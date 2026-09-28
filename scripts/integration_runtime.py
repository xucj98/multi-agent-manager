#!/usr/bin/env python3
"""Runtime helpers for the release integration lifecycle.

The endpoint in this module is a local, deterministic App Server-shaped
fixture.  It is deliberately never connected to the user's Codex socket.
The MAM daemon still runs as a detached child process and performs its normal
service and scheduler RPCs against this endpoint.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import threading
import time
from typing import Any, Mapping


class RuntimeIntegrationError(RuntimeError):
    """The controlled runtime did not observe the expected lifecycle."""


def _take(connection: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise OSError("App Server fixture connection closed")
        data.extend(chunk)
    return bytes(data)


def _read_frame(connection: socket.socket) -> tuple[int, bytes]:
    first, second = _take(connection, 2)
    size = second & 0x7F
    if size == 126:
        size = int.from_bytes(_take(connection, 2), "big")
    elif size == 127:
        size = int.from_bytes(_take(connection, 8), "big")
    if size > 16 * 1024 * 1024:
        raise OSError("App Server fixture frame is too large")
    mask = _take(connection, 4) if second & 0x80 else None
    payload = _take(connection, size)
    if mask:
        payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return first & 0x0F, payload


def _send_frame(connection: socket.socket, opcode: int, payload: bytes) -> None:
    size = len(payload)
    if size < 126:
        header = bytes((0x80 | opcode, size))
    elif size < 65536:
        header = bytes((0x80 | opcode, 126)) + size.to_bytes(2, "big")
    else:
        header = bytes((0x80 | opcode, 127)) + size.to_bytes(8, "big")
    connection.sendall(header + payload)


class ControlledCodexEndpoint:
    """A private Unix-socket App Server fixture used by real daemon children.

    Only the declared fixture manager and worker are accepted as known
    threads.  Compatibility probes use random IDs and receive explicit
    unknown-thread errors, while all requests and accepted messages are
    retained for lifecycle assertions.
    """

    def __init__(self, *, manager: str, worker: str) -> None:
        self.manager = manager
        self.worker = worker
        self._temporary = tempfile.TemporaryDirectory(prefix="mam-runtime-")
        self.path = str(Path(self._temporary.name) / "app-server.sock")
        self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener.bind(self.path)
        self._listener.listen(8)
        self._listener.settimeout(0.2)
        self._closed = threading.Event()
        self._lock = threading.Lock()
        self._connections: set[socket.socket] = set()
        self._threads: list[threading.Thread] = []
        self._server_errors: list[str] = []
        self._requests: list[dict[str, Any]] = []
        self._notifications: list[dict[str, Any]] = []
        self._statuses: dict[str, str] = {manager: "idle", worker: "idle"}
        self._latest_turn: dict[str, dict[str, str]] = {
            manager: {"id": "fixture-manager-turn", "status": "completed"},
            worker: {"id": "fixture-worker-turn", "status": "completed"},
        }
        self._turn_counter = 0
        self._thread = threading.Thread(target=self._serve, name="mam-controlled-codex", daemon=True)
        self._thread.start()

    @property
    def requests(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self._requests]

    @property
    def notifications(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self._notifications]

    @property
    def errors(self) -> list[str]:
        with self._lock:
            return list(self._server_errors)

    def _serve(self) -> None:
        while not self._closed.is_set():
            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            connection.settimeout(3.0)
            with self._lock:
                self._connections.add(connection)
            thread = threading.Thread(target=self._connection, args=(connection,), daemon=True)
            self._threads.append(thread)
            thread.start()

    def _connection(self, connection: socket.socket) -> None:
        try:
            self._upgrade(connection)
            while not self._closed.is_set():
                opcode, payload = _read_frame(connection)
                if opcode == 0x8:
                    return
                if opcode == 0x9:
                    _send_frame(connection, 0xA, payload)
                    continue
                if opcode != 0x1:
                    raise OSError(f"unexpected WebSocket opcode {opcode}")
                message = json.loads(payload.decode("utf-8"))
                if isinstance(message, Mapping):
                    self._handle(connection, dict(message))
        except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            if not self._closed.is_set():
                with self._lock:
                    self._server_errors.append(str(exc))
        finally:
            with self._lock:
                self._connections.discard(connection)
            try:
                connection.close()
            except OSError:
                pass

    @staticmethod
    def _upgrade(connection: socket.socket) -> None:
        data = bytearray()
        while b"\r\n\r\n" not in data:
            data.extend(connection.recv(4096))
            if len(data) > 32768:
                raise OSError("App Server fixture WebSocket header is too large")
        header = bytes(data).split(b"\r\n\r\n", 1)[0].decode("ascii")
        headers = {
            line.split(":", 1)[0].strip().lower(): line.split(":", 1)[1].strip()
            for line in header.split("\r\n")[1:]
            if ":" in line
        }
        key = headers.get("sec-websocket-key")
        if not key:
            raise OSError("App Server fixture request omitted WebSocket key")
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        connection.sendall(
            f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n".encode()
        )

    def _record(self, message: dict[str, Any]) -> None:
        with self._lock:
            self._requests.append(message)

    def _reply(self, connection: socket.socket, request_id: Any, result: Any = None, error: str | None = None) -> None:
        response: dict[str, Any] = {"id": request_id}
        if error is None:
            response["result"] = result if result is not None else {}
        else:
            response["error"] = {"code": -32000, "message": error}
        _send_frame(connection, 0x1, json.dumps(response, separators=(",", ":")).encode("utf-8"))

    def _known(self, thread_id: Any) -> bool:
        return isinstance(thread_id, str) and thread_id in {self.manager, self.worker}

    def _snapshot(self, thread_id: str) -> dict[str, Any]:
        return {"thread": {"id": thread_id, "status": {"type": self._statuses[thread_id]}}}

    @staticmethod
    def _message(params: Mapping[str, Any]) -> str:
        tool = params.get("toolOutput")
        if isinstance(tool, Mapping) and isinstance(tool.get("output"), str):
            return tool["output"]
        inputs = params.get("input")
        if isinstance(inputs, list):
            return "\n".join(item.get("text", "") for item in inputs if isinstance(item, Mapping) and isinstance(item.get("text"), str))
        return ""

    def _handle(self, connection: socket.socket, request: dict[str, Any]) -> None:
        method = request.get("method")
        params = request.get("params")
        params = params if isinstance(params, Mapping) else {}
        if isinstance(method, str):
            self._record({"method": method, "params": dict(params), "id": request.get("id")})
        if "id" not in request:
            return
        request_id = request.get("id")
        if method == "initialize":
            self._reply(connection, request_id, {"serverInfo": {"name": "mam-controlled-codex", "version": "fixture"}})
            return
        thread_id = params.get("threadId")
        if method in {"thread/read", "thread/resume", "thread/turns/list", "turn/start", "turn/steer"} and not self._known(thread_id):
            self._reply(connection, request_id, error="unknown thread")
            return
        if method in {"thread/read", "thread/resume"}:
            self._reply(connection, request_id, self._snapshot(thread_id))
            return
        if method == "thread/turns/list":
            self._reply(connection, request_id, {"data": [dict(self._latest_turn[thread_id])]})
            return
        if method in {"turn/start", "turn/steer"}:
            self._turn_counter += 1
            turn_id = f"fixture-turn-{self._turn_counter}"
            message = self._message(params)
            delivery = {
                "thread_id": thread_id,
                "method": method,
                "message": message,
                "params": dict(params),
                "turn_id": turn_id,
                "received_at": time.time(),
            }
            with self._lock:
                self._notifications.append(delivery)
            self._statuses[thread_id] = "active"
            self._latest_turn[thread_id] = {"id": turn_id, "status": "inProgress"}
            def complete_turn() -> None:
                if self._closed.is_set():
                    return
                self._statuses[thread_id] = "idle"
                self._latest_turn[thread_id] = {"id": turn_id, "status": "completed"}
            threading.Timer(0.15, complete_turn).start()
            self._reply(connection, request_id, {"turn": {"id": turn_id, "status": "inProgress"}})
            return
        self._reply(connection, request_id, error=f"unsupported method: {method}")

    def close(self) -> None:
        if self._closed.is_set():
            return
        self._closed.set()
        try:
            self._listener.close()
        except OSError:
            pass
        with self._lock:
            connections = list(self._connections)
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                connection.close()
            except OSError:
                pass
        self._thread.join(timeout=2)
        for thread in self._threads:
            thread.join(timeout=1)
        self._temporary.cleanup()


class RuntimeHarness:
    """Own one instance's endpoint and every daemon started through it."""

    def __init__(self, instance: Path, metadata: Mapping[str, Any], log: Path) -> None:
        self.instance = Path(instance).resolve()
        self.metadata = dict(metadata)
        fixture = self.metadata.get("fixture")
        if not isinstance(fixture, Mapping):
            raise ValueError("runtime metadata must include a fixture mapping")
        self.fixture = dict(fixture)
        for key in ("manager", "worker", "task"):
            if not isinstance(self.fixture.get(key), str) or not self.fixture[key]:
                raise ValueError(f"runtime fixture is missing {key}")
        self.log = Path(log)
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.endpoint = ControlledCodexEndpoint(manager=self.fixture["manager"], worker=self.fixture["worker"])
        self.env = {**os.environ, "MAM_APP_SERVER_SOCKET": self.endpoint.path, "MAM_INTEGRATION_RUNTIME": "controlled"}
        self._owned: dict[int, dict[str, Any]] = {}
        self._launchers: list[Path] = []
        self._closed = False
        self._endpoint_closed = False
        self.last_cleanup: dict[str, Any] | None = None

    @property
    def notifications(self) -> list[dict[str, Any]]:
        return self.endpoint.notifications

    @property
    def requests(self) -> list[dict[str, Any]]:
        return self.endpoint.requests

    def _run(self, launcher: Path, args: list[str]) -> dict[str, Any]:
        command = [str(launcher), *args]
        result = subprocess.run(command, cwd=self.instance, env=self.env, capture_output=True, text=True, timeout=20)
        with self.log.open("a", encoding="utf-8") as stream:
            stream.write("$ " + " ".join(command) + "\n")
            stream.write(result.stdout)
            stream.write(result.stderr)
            stream.write(f"[exit {result.returncode}]\n")
        if result.returncode:
            raise RuntimeIntegrationError(f"{' '.join(command)} failed: {result.stderr[-1200:]}")
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeIntegrationError(f"{' '.join(command)} returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise RuntimeIntegrationError(f"{' '.join(command)} returned a non-object")
        return value

    @property
    def mam_root(self) -> Path:
        value = self.metadata.get("mam_root")
        return Path(value).resolve() if isinstance(value, str) else self.instance / "multi-agent-manager"

    def _service_state(self) -> dict[str, Any]:
        path = self.mam_root / ".local" / "service" / "state.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeIntegrationError(f"cannot read service state {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeIntegrationError("service state is not an object")
        return value

    def _alive(self, pid: int, identity: Mapping[str, Any] | None = None) -> bool:
        try:
            from multi_agent_manager.job_runtime import probe_process
            observed = probe_process("local", pid, dict(identity) if isinstance(identity, Mapping) else None)
            return observed.get("status") == "running"
        except Exception:
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            return True

    def status(self, launcher: Path) -> dict[str, Any]:
        return self._run(Path(launcher), ["service", "status"])

    def start(self, launcher: Path) -> dict[str, Any]:
        launcher = Path(launcher).resolve()
        before = self._service_state() if (self.mam_root / ".local" / "service" / "state.json").is_file() else {}
        prior_pid = before.get("pid")
        if isinstance(prior_pid, int) and before.get("enabled") and self._alive(prior_pid, before.get("identity")):
            raise RuntimeIntegrationError(f"refusing to attach to an existing daemon PID {prior_pid}")
        result = self._run(launcher, ["service", "start", "--manager", self.fixture["manager"]])
        state = self._service_state()
        pid = state.get("pid")
        identity = state.get("identity")
        if not isinstance(pid, int) or not isinstance(identity, Mapping) or not self._alive(pid, identity):
            raise RuntimeIntegrationError("service start did not leave a live daemon with an identity")
        if pid in self._owned:
            raise RuntimeIntegrationError(f"service start reused an owned daemon PID {pid}")
        if prior_pid == pid and prior_pid is not None:
            raise RuntimeIntegrationError("service restart did not produce an independent daemon PID")
        if not result.get("running"):
            raise RuntimeIntegrationError(f"service start did not report running: {result}")
        self._owned[pid] = {"launcher": str(launcher), "identity": dict(identity)}
        self._launchers.append(launcher)
        return {"launcher": str(launcher), "status": result, "state": state, "pid": pid, "identity": dict(identity)}

    def stop(self, launcher: Path) -> dict[str, Any]:
        result = self._run(Path(launcher).resolve(), ["service", "stop"])
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            state = self._service_state()
            pid = state.get("pid")
            if not state.get("enabled") and (not isinstance(pid, int) or not self._alive(pid, state.get("identity"))):
                return {"status": result, "state": state, "stopped": True}
            time.sleep(0.05)
        raise RuntimeIntegrationError("service stop returned before its daemon exited")

    def wait_for_job_state(self, job_id: str, expected: str, *, timeout: float = 60.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        task_dir = self.mam_root / ".local" / "tasks"
        while time.monotonic() < deadline:
            for path in task_dir.glob("*.json"):
                try:
                    task = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                for job in task.get("jobs", []) if isinstance(task, Mapping) and isinstance(task.get("jobs"), list) else []:
                    if isinstance(job, Mapping) and job.get("id") == job_id and job.get("status") == expected:
                        return dict(job)
            time.sleep(0.05)
        raise RuntimeIntegrationError(f"JOB-ID {job_id} did not reach status {expected}")

    def verify_notification(self, job_id: str, expected: str = "exited", *, timeout: float = 60.0) -> dict[str, Any]:
        if expected != "exited":
            raise ValueError("controlled notification verification currently expects exited jobs")
        deadline = time.monotonic() + timeout
        recipient = self.fixture["worker"]
        while time.monotonic() < deadline:
            matches = [
                item for item in self.endpoint.notifications
                if item.get("thread_id") == recipient and job_id in str(item.get("message", ""))
                and "exited" in str(item.get("message", ""))
            ]
            try:
                state = self._service_state()
            except RuntimeIntegrationError:
                state = {}
            events = state.get("events", {}) if isinstance(state, Mapping) else {}
            histories = state.get("history", []) if isinstance(state, Mapping) else []
            event_matches = [
                dict(item) for item in events.values() if isinstance(item, Mapping)
                and item.get("kind") == "job_stopped" and item.get("job") == job_id
                and item.get("recipient") == recipient and item.get("delivery") == "accepted"
            ] if isinstance(events, Mapping) else []
            if matches and event_matches:
                return {
                    "job": job_id,
                    "expected": expected,
                    "recipient": recipient,
                    "message": matches[0]["message"],
                    "notification": matches[0],
                    "event": event_matches[0],
                    "pending": list(events.values()) if isinstance(events, Mapping) else [],
                    "history": list(histories) if isinstance(histories, list) else [],
                    "requests": self.requests,
                }
            time.sleep(0.05)
        raise RuntimeIntegrationError(
            f"no accepted controlled notification for JOB-ID {job_id}; "
            f"notifications={self.endpoint.notifications!r}, service={state!r}"
        )

    def _force_stop(self, pid: int, identity: Mapping[str, Any] | None) -> bool:
        if not self._alive(pid, identity):
            return True
        for signum, wait in ((signal.SIGTERM, 2.0), (signal.SIGKILL, 1.0)):
            try:
                os.kill(pid, signum)
            except ProcessLookupError:
                return True
            deadline = time.monotonic() + wait
            while time.monotonic() < deadline:
                if not self._alive(pid, identity):
                    return True
                time.sleep(0.05)
        return not self._alive(pid, identity)

    def close(self) -> dict[str, Any]:
        if self._closed:
            return {"ok": True, "daemons": [], "endpoint": "closed"}
        cleanup: list[dict[str, Any]] = []
        for pid, info in list(self._owned.items()):
            stop_result = None
            try:
                state = self._service_state()
            except (RuntimeIntegrationError, OSError):
                state = None
            current = isinstance(state, Mapping) and state.get("pid") == pid and state.get("identity") == info.get("identity")
            if current:
                try:
                    stop_result = self._run(Path(info["launcher"]), ["service", "stop"])
                except (RuntimeIntegrationError, OSError) as exc:
                    stop_result = {"error": str(exc)}
            # A successful service command is only a request.  The owned
            # process identity is the source of truth for cleanup success.
            stopped = self._force_stop(pid, info.get("identity"))
            cleanup.append({"pid": pid, "stopped": stopped, "stop_result": stop_result})
        if not self._endpoint_closed:
            self.endpoint.close()
            self._endpoint_closed = True
        result = {
            "ok": all(item["stopped"] for item in cleanup),
            "daemons": cleanup,
            "endpoint": "closed",
            "requests": len(self.requests),
            "notifications": len(self.notifications),
        }
        self.last_cleanup = result
        if not result["ok"]:
            raise RuntimeIntegrationError(f"failed to clean up controlled daemons: {result}")
        self._closed = True
        return result


__all__ = ["ControlledCodexEndpoint", "RuntimeHarness", "RuntimeIntegrationError"]
