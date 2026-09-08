"""Read-only probes for registered processes and Codex App Server threads."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shlex
import socket
import subprocess
from datetime import datetime, timezone
from typing import Any, Mapping


PROCESS_TIMEOUT_SECONDS = 3.0
APP_SERVER_TIMEOUT_SECONDS = 3.0
DEFAULT_SOCKET_PATH = "/root/.codex/app-server-control/app-server-control.sock"
_IDENTITY_KEYS = ("host", "boot_id", "start_ticks")
_SAFE_REMOTE_HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:@-]*\Z")
_REMOTE_PROC_SCRIPT = """
import os
import sys

pid = int(sys.argv[1])
try:
    os.kill(pid, 0)
except ProcessLookupError:
    raise SystemExit(4)
except OSError:
    raise SystemExit(5)
try:
    with open('/proc/sys/kernel/random/boot_id', encoding='ascii') as handle:
        boot_id = handle.read().strip()
except OSError:
    raise SystemExit(5)
try:
    with open(f'/proc/{pid}/stat', encoding='utf-8') as handle:
        stat = handle.read()
except FileNotFoundError:
    raise SystemExit(4)
except OSError:
    raise SystemExit(5)
if not boot_id:
    raise SystemExit(5)
print(boot_id)
print(stat, end='')
"""
_AGENT_STATUSES = {"active", "idle", "notLoaded", "systemError"}


class _ProbeError(RuntimeError):
    """A transport or protocol failure that must not imply a stopped target."""


class _RpcError(_ProbeError):
    """An App Server response carrying a JSON-RPC error."""


def _checked_at() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _process_result(
    status: str, checked_at: str, identity: dict[str, Any] | None = None, error: str | None = None
) -> dict[str, Any]:
    return {"status": status, "identity": identity, "checked_at": checked_at, "error": error}


def _agent_result(status: str, checked_at: str, error: str | None = None) -> dict[str, str | None]:
    return {"status": status, "checked_at": checked_at, "error": error}


def _is_local_host(host: str) -> bool:
    return host.lower() in {"local", "localhost", "127.0.0.1", "::1", socket.gethostname().lower(), socket.getfqdn().lower()}


def _valid_identity(identity: Mapping[str, Any]) -> bool:
    return set(_IDENTITY_KEYS).issubset(identity) and isinstance(identity["start_ticks"], int)


def _same_identity(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> bool:
    return all(expected[key] == observed[key] for key in _IDENTITY_KEYS)


def _parse_proc_stat(stat: str) -> tuple[str, int]:
    close_paren = stat.rfind(")")
    fields = stat[close_paren + 1 :].split() if close_paren >= 0 else []
    if len(fields) <= 19 or not fields[19].isdigit():
        raise _ProbeError("invalid /proc stat response")
    return fields[0], int(fields[19])


def _read_local_process(host: str, pid: int) -> tuple[dict[str, Any], str] | None:
    try:
        with open("/proc/sys/kernel/random/boot_id", encoding="ascii") as handle:
            boot_id = handle.read().strip()
    except OSError as exc:
        raise _ProbeError(f"cannot read boot identity: {exc}") from exc
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
            state, start_ticks = _parse_proc_stat(handle.read())
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _ProbeError(f"cannot read process: {exc}") from exc
    if not boot_id:
        raise _ProbeError("empty boot identity")
    return {"host": host, "boot_id": boot_id, "start_ticks": start_ticks}, state


def _read_remote_process(host: str, pid: int) -> tuple[dict[str, Any], str] | None:
    if not _SAFE_REMOTE_HOST.fullmatch(host):
        raise _ProbeError("invalid remote host")
    remote_command = f"python3 -c {shlex.quote(_REMOTE_PROC_SCRIPT)} {pid}"
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={int(PROCESS_TIMEOUT_SECONDS)}",
        "--",
        host,
        remote_command,
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise _ProbeError("SSH query timed out") from exc
    except OSError as exc:
        raise _ProbeError(f"cannot run SSH: {exc}") from exc
    if completed.returncode == 4:
        return None
    if completed.returncode == 5:
        raise _ProbeError("remote process cannot be accessed")
    if completed.returncode != 0:
        detail = completed.stderr.strip().replace("\n", " ")
        raise _ProbeError(f"SSH query failed ({completed.returncode}): {detail or 'no detail'}")
    boot_id, separator, stat = completed.stdout.partition("\n")
    if not separator or not boot_id.strip():
        raise _ProbeError("invalid SSH process response")
    state, start_ticks = _parse_proc_stat(stat)
    return {"host": host, "boot_id": boot_id.strip(), "start_ticks": start_ticks}, state


def probe_process(host: str, pid: int, identity: dict | None = None) -> dict:
    """Return the current state of a local or SSH-reachable registered process."""

    checked_at = _checked_at()
    if not isinstance(host, str) or not host:
        return _process_result("unknown", checked_at, error="host must be a non-empty string")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return _process_result("unknown", checked_at, error="pid must be a positive integer")
    if identity is not None and (not isinstance(identity, Mapping) or not _valid_identity(identity)):
        return _process_result("unknown", checked_at, error="invalid registered process identity")
    try:
        current = _read_local_process(host, pid) if _is_local_host(host) else _read_remote_process(host, pid)
    except _ProbeError as exc:
        return _process_result("unknown", checked_at, error=str(exc))
    if current is None:
        return _process_result("stopped", checked_at, error="process not found")
    observed, state = current
    if state == "Z":
        return _process_result("stopped", checked_at, observed, "process is a zombie")
    if identity is not None and not _same_identity(identity, observed):
        return _process_result("stopped", checked_at, observed, "process identity changed")
    return _process_result("running", checked_at, observed)


class _WebSocket:
    """The small client-only WebSocket subset needed by the local control socket."""

    def __init__(self, connection: socket.socket, buffered: bytes = b"") -> None:
        self.connection = connection
        self.buffer = bytearray(buffered)

    @classmethod
    def connect(cls, path: str) -> "_WebSocket":
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(APP_SERVER_TIMEOUT_SECONDS)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            "GET / HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        try:
            connection.connect(path)
            connection.sendall(request)
            header, buffered = cls._read_header(connection)
            lines = header.decode("iso-8859-1").split("\r\n")
            headers = {key.strip().lower(): value.strip() for key, value in (line.split(":", 1) for line in lines[1:] if ":" in line)}
            accepted = headers.get("sec-websocket-accept")
            expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            if not lines[0].endswith(" 101 Switching Protocols") or accepted != expected:
                raise _ProbeError("WebSocket upgrade rejected")
            return cls(connection, buffered)
        except BaseException:
            connection.close()
            raise

    @staticmethod
    def _read_header(connection: socket.socket) -> tuple[bytes, bytes]:
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = connection.recv(4096)
            if not chunk:
                raise _ProbeError("connection closed during WebSocket upgrade")
            data.extend(chunk)
            if len(data) > 32768:
                raise _ProbeError("WebSocket upgrade response is too large")
        header, buffered = bytes(data).split(b"\r\n\r\n", 1)
        return header, buffered

    def _take(self, size: int) -> bytes:
        while len(self.buffer) < size:
            chunk = self.connection.recv(4096)
            if not chunk:
                raise _ProbeError("WebSocket connection closed")
            self.buffer.extend(chunk)
        value = bytes(self.buffer[:size])
        del self.buffer[:size]
        return value

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        length = len(payload)
        if length < 126:
            header = bytes((0x80 | opcode, 0x80 | length))
        elif length < 65536:
            header = bytes((0x80 | opcode, 0x80 | 126)) + length.to_bytes(2, "big")
        else:
            header = bytes((0x80 | opcode, 0x80 | 127)) + length.to_bytes(8, "big")
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.connection.sendall(header + mask + masked)

    def send_text(self, message: str) -> None:
        self._send_frame(0x1, message.encode("utf-8"))

    def _read_frame(self) -> tuple[bool, int, bytes]:
        first, second = self._take(2)
        if first & 0x70:
            raise _ProbeError("unsupported WebSocket extension")
        size = second & 0x7F
        if size == 126:
            size = int.from_bytes(self._take(2), "big")
        elif size == 127:
            size = int.from_bytes(self._take(8), "big")
        if size > 4 * 1024 * 1024:
            raise _ProbeError("WebSocket frame is too large")
        mask = self._take(4) if second & 0x80 else None
        payload = self._take(size)
        if mask is not None:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return bool(first & 0x80), first & 0x0F, payload

    def receive_text(self) -> str:
        fragments: bytearray | None = None
        while True:
            final, opcode, payload = self._read_frame()
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x8:
                raise _ProbeError("WebSocket connection closed by server")
            if opcode == 0x1:
                if fragments is not None:
                    raise _ProbeError("unexpected WebSocket text frame")
                fragments = bytearray(payload)
            elif opcode == 0x0 and fragments is not None:
                fragments.extend(payload)
            else:
                raise _ProbeError("unexpected WebSocket frame")
            if final:
                if fragments is None:
                    raise _ProbeError("unexpected WebSocket continuation")
                return bytes(fragments).decode("utf-8")

    def close(self) -> None:
        self.connection.close()


def _rpc(websocket: _WebSocket, request_id: int, method: str, params: dict[str, Any]) -> Any:
    websocket.send_text(json.dumps({"method": method, "id": request_id, "params": params}, separators=(",", ":")))
    while True:
        try:
            message = json.loads(websocket.receive_text())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _ProbeError("invalid JSON-RPC response") from exc
        if not isinstance(message, Mapping) or message.get("id") != request_id:
            continue
        if "error" in message:
            error = message["error"]
            detail = error.get("message") if isinstance(error, Mapping) else str(error)
            raise _RpcError(str(detail or "unspecified server error"))
        if "result" not in message:
            raise _ProbeError("JSON-RPC response has no result")
        return message["result"]


def _thread_status(result: Any) -> str:
    if not isinstance(result, Mapping) or not isinstance(result.get("thread"), Mapping):
        raise _ProbeError("thread/read response has no thread")
    status = result["thread"].get("status")
    value = status.get("type") if isinstance(status, Mapping) else status
    if value not in _AGENT_STATUSES:
        raise _ProbeError("thread/read returned an unknown status")
    return value


def probe_agents(agent_ids: list[str], socket_path: str | None = None) -> dict[str, dict]:
    """Read each supplied thread once through one existing App Server connection."""

    agent_ids = list(dict.fromkeys(agent_ids))
    checked_at = _checked_at()
    if not agent_ids:
        return {}
    if not all(isinstance(agent_id, str) for agent_id in agent_ids):
        raise TypeError("agent_ids must contain strings")
    results: dict[str, dict] = {}
    websocket: _WebSocket | None = None
    try:
        websocket = _WebSocket.connect(socket_path or DEFAULT_SOCKET_PATH)
        _rpc(
            websocket,
            1,
            "initialize",
            {"clientInfo": {"name": "multi-agent-manager", "title": "Multi-agent manager", "version": "1.0"}},
        )
        websocket.send_text(json.dumps({"method": "initialized", "params": {}}, separators=(",", ":")))
        for request_id, agent_id in enumerate(agent_ids, start=2):
            try:
                results[agent_id] = _agent_result(
                    _thread_status(_rpc(websocket, request_id, "thread/read", {"threadId": agent_id, "includeTurns": False})),
                    checked_at,
                )
            except _RpcError as exc:
                results[agent_id] = _agent_result("unknown", checked_at, f"thread/read failed: {exc}")
    except (OSError, TimeoutError, _ProbeError) as exc:
        error = f"App Server query failed: {exc}"
        for agent_id in agent_ids:
            results.setdefault(agent_id, _agent_result("unknown", checked_at, error))
    finally:
        if websocket is not None:
            websocket.close()
    return results
