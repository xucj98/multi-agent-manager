"""Behavioral compatibility checks for MAM's event-driven waits.

The result is deliberately fresh: no version allowlist, cached approval, or
certificate is used.  A version is useful troubleshooting data, but only a
failed control, notification, or trace behavior probe blocks a wait.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
from collections.abc import Mapping
from typing import Any

from . import job_runtime


DEFAULT_SOCKET_PATH = Path(job_runtime.DEFAULT_SOCKET_PATH)
DEFAULT_LOG_PATH = DEFAULT_SOCKET_PATH.with_name("app-server.log")
PROBE_TIMEOUT_SECONDS = 15.0
LIVE_TRACE_SETTLE_SECONDS = 1.0
LOG_TAIL_BYTES = 512 * 1024
_CLIENT_INFO = {"name": "multi-agent-manager-wait-compat", "version": "1"}


class _CompatibilityFailure(RuntimeError):
    """A behavior required before MAM may block on a wait is unavailable."""


def _configured_paths() -> tuple[Path, Path]:
    socket_path = Path(os.environ.get("MAM_APP_SERVER_SOCKET", DEFAULT_SOCKET_PATH))
    log_path = Path(os.environ.get("MAM_APP_SERVER_LOG", socket_path.with_name("app-server.log")))
    if not socket_path.is_absolute() or not log_path.is_absolute():
        raise _CompatibilityFailure("the App Server socket and trace-log paths must be absolute")
    return socket_path, log_path


def _socket_identity(path: Path) -> dict[str, int]:
    try:
        current = path.stat()
    except OSError as exc:
        raise _CompatibilityFailure(f"the Codex App Server control socket is unavailable at {path}") from exc
    if not stat.S_ISSOCK(current.st_mode):
        raise _CompatibilityFailure(f"the configured App Server path is not a socket: {path}")
    return {"device": current.st_dev, "inode": current.st_ino}


def _tail(path: Path) -> bytes:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - LOG_TAIL_BYTES))
            data = handle.read()
    except OSError as exc:
        raise _CompatibilityFailure(f"the Codex App Server trace log is unavailable at {path}") from exc
    return data.split(b"\n", 1)[-1] if size > LOG_TAIL_BYTES else data


def _log_identity(path: Path) -> dict[str, int | str]:
    try:
        current = path.stat()
    except OSError as exc:
        raise _CompatibilityFailure(f"the Codex App Server trace log is unavailable at {path}") from exc
    if not stat.S_ISREG(current.st_mode):
        raise _CompatibilityFailure(f"the configured App Server trace path is not a regular file: {path}")

    has_structured_trace = False
    for line in _tail(path).splitlines():
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        span = row.get("span") if isinstance(row, Mapping) else None
        if isinstance(span, Mapping) and isinstance(span.get("rpc.method"), str):
            has_structured_trace = True
            break
    if not has_structured_trace:
        raise _CompatibilityFailure(
            "the App Server trace log has no structured request spans; configure JSON trace logging before waiting"
        )
    return {"device": current.st_dev, "inode": current.st_ino, "format": "json-request-span"}


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _handshake_trace_seen(path: Path, offset: int, client_name: str) -> bool:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(offset if size >= offset else 0)
            data = handle.read()
    except OSError as exc:
        raise _CompatibilityFailure(f"the Codex App Server trace log is unavailable at {path}") from exc
    for line in data.splitlines():
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        span = row.get("span") if isinstance(row, Mapping) else None
        if (
            isinstance(span, Mapping)
            and span.get("rpc.method") == "initialize"
            and span.get("app_server.client_name") == client_name
        ):
            return True
    return False


def _wait_for_handshake_trace(path: Path, offset: int, client_name: str) -> None:
    time.sleep(LIVE_TRACE_SETTLE_SECONDS)
    if _handshake_trace_seen(path, offset, client_name):
        return
    raise _CompatibilityFailure("the live control-socket handshake was not recorded in the App Server trace log")


def _live_control_probe(socket_path: Path, log_path: Path) -> dict[str, Any]:
    """Use only initialize/initialized on the app-managed control socket."""

    try:
        offset = log_path.stat().st_size
    except OSError as exc:
        raise _CompatibilityFailure(f"the Codex App Server trace log is unavailable at {log_path}") from exc
    client_info = dict(_CLIENT_INFO)
    client_info["name"] = f"{_CLIENT_INFO['name']}-{uuid.uuid4().hex}"
    websocket = None
    try:
        websocket = job_runtime._WebSocket.connect(str(socket_path))
        result = job_runtime._rpc(websocket, 1, "initialize", {"clientInfo": client_info})
        if not isinstance(result, Mapping):
            raise _CompatibilityFailure("the App Server initialize response is not an object")
        websocket.send_text(json.dumps({"method": "initialized", "params": {}}, separators=(",", ":")))
    except _CompatibilityFailure:
        raise
    except Exception as exc:
        raise _CompatibilityFailure("the running Codex App Server control connection is disconnected or incompatible") from exc
    finally:
        if websocket is not None:
            websocket.close()
    _wait_for_handshake_trace(log_path, offset, client_info["name"])

    user_agent = result.get("userAgent")
    return {
        "response_keys": sorted(str(key) for key in result),
        "user_agent_digest": _digest(user_agent) if isinstance(user_agent, str) else None,
        "trace_bound": True,
    }


class _JsonLinesClient:
    """A minimal JSON-RPC stdio client that retains server notifications."""

    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        if process.stdin is None or process.stdout is None:
            raise _CompatibilityFailure("the isolated App Server did not expose stdio")
        self.process = process
        self.stdin = process.stdin
        self.stdout_fd = process.stdout.fileno()
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.stdout_fd, selectors.EVENT_READ)
        self.buffer = bytearray()
        self.notifications: list[str] = []

    def close(self) -> None:
        self.selector.close()

    def notify(self, method: str, params: Mapping[str, Any]) -> None:
        self._send({"method": method, "params": params})

    def request(self, request_id: int, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self._send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + PROBE_TIMEOUT_SECONDS
        while True:
            message = self._receive(deadline)
            if message.get("id") == request_id:
                return message
            notification = message.get("method")
            if isinstance(notification, str):
                self.notifications.append(notification)

    def _send(self, message: Mapping[str, Any]) -> None:
        try:
            self.stdin.write(json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n")
            self.stdin.flush()
        except OSError as exc:
            raise _CompatibilityFailure("the isolated App Server closed its input") from exc

    def _receive(self, deadline: float) -> Mapping[str, Any]:
        while True:
            newline = self.buffer.find(b"\n")
            if newline >= 0:
                line = bytes(self.buffer[:newline])
                del self.buffer[: newline + 1]
                try:
                    message = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise _CompatibilityFailure("the isolated App Server emitted invalid JSON-RPC") from exc
                if not isinstance(message, Mapping):
                    raise _CompatibilityFailure("the isolated App Server emitted a non-object JSON-RPC message")
                return message

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _CompatibilityFailure("the isolated App Server behavior probe timed out")
            if not self.selector.select(remaining):
                continue
            try:
                chunk = os.read(self.stdout_fd, 65536)
            except OSError as exc:
                raise _CompatibilityFailure("the isolated App Server output could not be read") from exc
            if not chunk:
                raise _CompatibilityFailure("the isolated App Server stopped before replying")
            self.buffer.extend(chunk)


def _stop(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _trace_evidence(trace: bytes, expected_turn_id: str) -> dict[str, bool]:
    request_seen = False
    mapping_seen = False
    for line in trace.splitlines():
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(row, Mapping):
            continue
        fields = row.get("fields")
        span = row.get("span")
        if isinstance(fields, Mapping) and fields.get("message") == "app-server request: turn/steer":
            request_seen = True
        if (
            isinstance(span, Mapping)
            and span.get("rpc.method") == "turn/steer"
            and span.get("turn.id") == expected_turn_id
        ):
            mapping_seen = True
    return {"trace_request": request_seen, "trace_turn_mapping": mapping_seen}


def _validate_behavior(evidence: Mapping[str, bool]) -> None:
    if not evidence.get("thread_started"):
        raise _CompatibilityFailure("event delivery failed: the isolated App Server did not send thread/started")
    if not evidence.get("safe_steer_rejected"):
        raise _CompatibilityFailure("the isolated no-model turn/steer safety check did not return an error")
    if not evidence.get("trace_request"):
        raise _CompatibilityFailure("trace capability failed: turn/steer was not recorded by the isolated App Server")
    if not evidence.get("trace_turn_mapping"):
        raise _CompatibilityFailure("trace capability failed: turn/steer was not mapped to turn.id")


def _behavior_probe() -> dict[str, bool]:
    """Exercise notification delivery and trace mapping without a model request.

    The child gets a temporary cwd.  It creates only an ephemeral thread,
    then sends an empty steer request with an impossible turn id; that request
    must fail before a model turn can start.
    """

    codex = shutil.which("codex")
    if codex is None:
        raise _CompatibilityFailure("the codex executable is unavailable for the isolated behavior probe")

    with tempfile.TemporaryDirectory(prefix="mam-wait-compat-") as directory:
        root = Path(directory)
        cwd = root / "cwd"
        cwd.mkdir()
        env = os.environ.copy()
        env.update(
            {
                "RUST_LOG": "off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info",
                "LOG_FORMAT": "json",
            }
        )
        with tempfile.TemporaryFile(mode="w+b") as trace_file:
            process: subprocess.Popen[bytes] | None = None
            client: _JsonLinesClient | None = None
            trace = b""
            try:
                process = subprocess.Popen(
                    [codex, "app-server", "--listen", "stdio://"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=trace_file,
                    cwd=cwd,
                    env=env,
                )
                client = _JsonLinesClient(process)
                initialized = client.request(1, "initialize", {"clientInfo": _CLIENT_INFO})
                if "result" not in initialized:
                    raise _CompatibilityFailure("the isolated App Server rejected initialize")
                client.notify("initialized", {})

                started = client.request(2, "thread/start", {"cwd": str(cwd), "ephemeral": True})
                thread = started.get("result", {}).get("thread") if isinstance(started.get("result"), Mapping) else None
                thread_id = thread.get("id") if isinstance(thread, Mapping) else None
                if not isinstance(thread_id, str) or not thread_id:
                    raise _CompatibilityFailure("the isolated App Server did not create an ephemeral thread")

                expected_turn_id = str(uuid.uuid4())
                steered = client.request(
                    3,
                    "turn/steer",
                    {"threadId": thread_id, "expectedTurnId": expected_turn_id, "input": []},
                )
                evidence = {
                    "thread_started": "thread/started" in client.notifications,
                    "safe_steer_rejected": "error" in steered,
                }
            except _CompatibilityFailure:
                raise
            except (OSError, subprocess.SubprocessError) as exc:
                raise _CompatibilityFailure("the isolated App Server behavior probe could not run") from exc
            finally:
                if client is not None:
                    client.close()
                _stop(process)
                trace_file.seek(0)
                trace = trace_file.read()

    evidence.update(_trace_evidence(trace, expected_turn_id))
    _validate_behavior(evidence)
    return evidence


def _diagnostic_cli_version() -> str | None:
    codex = shutil.which("codex")
    if codex is None:
        return None
    try:
        completed = subprocess.run(
            [codex, "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode:
        return None
    line = completed.stdout.strip().splitlines()
    return line[0][:200] if line else None


def _fingerprint(
    socket_path: Path,
    log_path: Path,
    socket: Mapping[str, Any],
    log: Mapping[str, Any],
    live: Mapping[str, Any],
    behavior: Mapping[str, Any],
) -> str:
    """Identify the behavior that was just checked, without pinning a version.

    The CLI version deliberately stays out of this value.  It is useful in the
    returned diagnostics, but a version change is never a compatibility
    failure and should not look like one to a caller comparing results.
    """

    return "sha256:" + _digest(
        {
            "socket_path": str(socket_path),
            "log_path": str(log_path),
            "socket": dict(socket),
            "log": dict(log),
            "live": dict(live),
            "behavior": dict(behavior),
        }
    )


def require_compatible() -> dict[str, Any]:
    """Freshly validate the runtime prerequisites before MAM blocks on a wait.

    Versions are recorded only as diagnostics.  There is no persisted PASS:
    every call reconnects to the live App Server and reruns the isolated
    behavior probe.
    """

    try:
        socket_path, log_path = _configured_paths()
        socket_before = _socket_identity(socket_path)
        live = _live_control_probe(socket_path, log_path)
        socket = _socket_identity(socket_path)
        if socket != socket_before:
            raise _CompatibilityFailure("the Codex App Server restarted during validation; rerun the compatibility check")
        log = _log_identity(log_path)
        behavior = _behavior_probe()
        cli_version = _diagnostic_cli_version()
    except _CompatibilityFailure as exc:
        raise RuntimeError(
            f"MAM wait compatibility check failed: {exc}. "
            "Do not start or continue a MAM wait. Open or restart the Codex App yourself, "
            "then rerun bash scripts/install.sh from the MAM checkout."
        ) from None

    return {
        "socket_path": str(socket_path),
        "log_path": str(log_path),
        "fingerprint": _fingerprint(socket_path, log_path, socket, log, live, behavior),
        "capabilities": {
            "live_control_socket": "validated",
            "event_delivery": "validated",
            "trace_turn_mapping": "validated",
            "native_message_wake": "not-certified",
        },
        "diagnostics": {"cli_version": cli_version, "live_response_keys": live["response_keys"]},
    }


def main() -> int:
    try:
        result = require_compatible()
    except RuntimeError as exc:
        print(f"MAM wait compatibility: FAIL\n{exc}", file=os.sys.stderr)
        return 1
    print("MAM wait compatibility: PASS")
    print(f"socket: {result['socket_path']}")
    print(f"trace log: {result['log_path']}")
    print(f"fingerprint: {result['fingerprint']}")
    print("Native user-message/native-manager-send wake behavior is not certified by this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
