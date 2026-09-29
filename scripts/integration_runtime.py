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


def _notification_input_type(notification: Mapping[str, Any]) -> str | None:
    """Classify the App Server input shape used for a delivered message."""

    if notification.get("method") != "turn/start":
        return None
    params = notification.get("params")
    if not isinstance(params, Mapping):
        return None
    tool = params.get("toolOutput")
    if isinstance(tool, Mapping):
        if tool.get("name") == "message" and tool.get("namespace") == "mam":
            return "tool"
        return None
    inputs = params.get("input")
    if isinstance(inputs, list) and inputs and all(
        isinstance(item, Mapping) and item.get("type") == "text" and isinstance(item.get("text"), str)
        for item in inputs
    ):
        return "user"
    return None


def validate_job_notification(
    notification: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    job_id: str,
    task_id: str,
    recipient: str,
    executor_path: str | None,
    expected_input_type: str,
    current_turn_id: str,
    allow_task_fallback: bool = False,
) -> dict[str, Any]:
    """Validate one exact job delivery against its durable scheduler event."""

    if expected_input_type not in {"tool", "user"}:
        raise ValueError("expected_input_type must be tool or user")
    if (
        event.get("kind") != "job_stopped"
        or event.get("job") != job_id
        or event.get("task") != task_id
        or event.get("executor") != recipient
    ):
        raise RuntimeIntegrationError("accepted scheduler event does not identify the fixture task and stopped job")
    if event.get("delivery") != "accepted" or event.get("recipient") != recipient:
        raise RuntimeIntegrationError("scheduler event was not accepted for the fixture executor")
    if executor_path is None:
        if not allow_task_fallback:
            raise RuntimeIntegrationError("scheduler event has no fixture executor path")
        if event.get("executor_path") is not None:
            raise RuntimeIntegrationError("scheduler event path does not match the legacy fixture record")
        executor_locator = f"task: {task_id}"
    else:
        if event.get("executor_path") != executor_path:
            raise RuntimeIntegrationError("scheduler event does not identify the fixture executor path")
        executor_locator = executor_path
    if notification.get("thread_id") != recipient:
        raise RuntimeIntegrationError("job notification was delivered to the wrong fixture thread")
    if _notification_input_type(notification) != expected_input_type:
        raise RuntimeIntegrationError("job notification used the wrong App Server input type")
    turn_id = notification.get("turn_id")
    if not isinstance(turn_id, str) or not turn_id or turn_id != current_turn_id:
        raise RuntimeIntegrationError("job notification does not belong to the current fixture turn")
    if event.get("accepted_turn_id") != turn_id:
        raise RuntimeIntegrationError("accepted scheduler event refers to a different turn")
    expected_message = (
        "[MAM MESSAGE]\n\n[job exited | " + executor_locator + "]\n"
        "There are exited jobs. Check the results and archive them."
    )
    message = notification.get("message")
    if isinstance(message, str) and job_id in message:
        raise RuntimeIntegrationError("job notification unexpectedly exposes a JOB-ID")
    if not isinstance(message, str) or expected_message not in message:
        raise RuntimeIntegrationError("job notification does not match the fixture executor message")
    return {
        "job": job_id,
        "recipient": recipient,
        "executor_path": executor_path,
        "executor_locator": executor_locator,
        "input_type": expected_input_type,
        "turn_id": turn_id,
        "message": message,
        "notification": dict(notification),
        "event": dict(event),
    }


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
        self._turns: dict[str, dict[str, dict[str, str]]] = {
            thread_id: {turn["id"]: dict(turn)} for thread_id, turn in self._latest_turn.items()
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

    def current_turn(self, thread_id: str) -> dict[str, str] | None:
        with self._lock:
            value = self._latest_turn.get(thread_id)
            return dict(value) if value is not None else None

    def turn_state(self, thread_id: str, turn_id: str) -> dict[str, str] | None:
        with self._lock:
            value = self._turns.get(thread_id, {}).get(turn_id)
            return dict(value) if value is not None else None

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
                turn_state = {"id": turn_id, "status": "inProgress"}
                self._turns.setdefault(thread_id, {})[turn_id] = turn_state
                self._latest_turn[thread_id] = dict(turn_state)
            def complete_turn() -> None:
                if self._closed.is_set():
                    return
                with self._lock:
                    turn_state = {"id": turn_id, "status": "completed"}
                    self._turns.setdefault(thread_id, {})[turn_id] = turn_state
                    if self._latest_turn.get(thread_id, {}).get("id") == turn_id:
                        self._statuses[thread_id] = "idle"
                        self._latest_turn[thread_id] = dict(turn_state)
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

    def _fixture_executor_path(self) -> str | None:
        task_path = self.mam_root / ".local" / "tasks" / f"{self.fixture['task']}.json"
        try:
            task = json.loads(task_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeIntegrationError(f"cannot read fixture task identity {task_path}: {exc}") from exc
        identity = task.get("identity") if isinstance(task, Mapping) else None
        if (
            not isinstance(task, Mapping)
            or task.get("agent") != self.fixture["worker"]
        ):
            raise RuntimeIntegrationError("fixture task does not identify its registered executor")
        if identity is None and self.metadata.get("version") == "0.1.0":
            return None
        path = identity.get("path") if isinstance(identity, Mapping) else None
        if (
            not isinstance(identity, Mapping)
            or identity.get("tree_root") != self.fixture["manager"]
            or not isinstance(path, str)
            or not path.startswith("/root/")
            or any(segment in ("", ".", "..") for segment in path.split("/")[1:])
        ):
            raise RuntimeIntegrationError("fixture task has no unique native executor path")
        return path

    def verify_notification(
        self,
        job_id: str,
        expected: str = "exited",
        *,
        expected_input_type: str = "tool",
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        if expected != "exited":
            raise ValueError("controlled notification verification currently expects exited jobs")
        deadline = time.monotonic() + timeout
        recipient = self.fixture["worker"]
        executor_path = self._fixture_executor_path()
        allow_task_fallback = executor_path is None and self.metadata.get("version") == "0.1.0"
        executor_locator = executor_path or f"task: {self.fixture['task']}"
        state: dict[str, Any] = {}
        events: Mapping[str, Any] = {}
        histories: list[Any] = []
        rejected: set[str] = set()
        while time.monotonic() < deadline:
            try:
                state = self._service_state()
            except RuntimeIntegrationError:
                time.sleep(0.05)
                continue
            events = state.get("events", {}) if isinstance(state, Mapping) else {}
            histories = state.get("history", []) if isinstance(state, Mapping) else []
            event_matches = [
                dict(item) for item in events.values() if isinstance(item, Mapping)
                and item.get("kind") == "job_stopped" and item.get("job") == job_id
                and item.get("recipient") == recipient and item.get("delivery") == "accepted"
                and item.get("executor_path") == executor_path
            ] if isinstance(events, Mapping) else []
            for event in event_matches:
                accepted_turn_id = event.get("accepted_turn_id")
                if not isinstance(accepted_turn_id, str):
                    continue
                completed_turn = self.endpoint.turn_state(recipient, accepted_turn_id)
                if completed_turn and completed_turn.get("status") == "completed":
                    for notification in self.endpoint.notifications:
                        if notification.get("turn_id") != accepted_turn_id:
                            continue
                        try:
                            evidence = validate_job_notification(
                                notification,
                                event,
                                job_id=job_id,
                                task_id=self.fixture["task"],
                                recipient=recipient,
                                executor_path=executor_path,
                                allow_task_fallback=allow_task_fallback,
                                expected_input_type=expected_input_type,
                                current_turn_id=accepted_turn_id,
                            )
                        except RuntimeIntegrationError as exc:
                            rejected.add(str(exc))
                            continue
                        evidence.update({
                            "expected": expected,
                            "pending": list(events.values()) if isinstance(events, Mapping) else [],
                            "history": list(histories) if isinstance(histories, list) else [],
                            "requests": self.requests,
                        })
                        return evidence
            time.sleep(0.05)
        event_diagnostics = [
            {
                key: item.get(key)
                for key in ("kind", "task", "job", "executor", "recipient", "executor_path", "delivery", "accepted_turn_id")
            }
            for item in events.values() if isinstance(item, Mapping)
            and item.get("kind") == "job_stopped" and item.get("job") == job_id
        ] if isinstance(events, Mapping) else []
        notification_diagnostics = [
            {
                "thread_id": item.get("thread_id"),
                "method": item.get("method"),
                "turn_id": item.get("turn_id"),
                "input_type": _notification_input_type(item),
                "message": item.get("message"),
            }
            for item in self.endpoint.notifications if item.get("thread_id") == recipient
        ]
        raise RuntimeIntegrationError(
            f"no accepted controlled notification for fixture job {job_id}; "
            f"recipient={recipient}, executor_locator={executor_locator!r}, expected_input_type={expected_input_type!r}, "
            f"latest_turn={self.endpoint.current_turn(recipient)!r}, rejected={sorted(rejected)!r}; "
            f"events={event_diagnostics!r}, notifications={notification_diagnostics!r}, "
            f"counters={state.get('counters') if isinstance(state, Mapping) else None!r}"
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


__all__ = ["ControlledCodexEndpoint", "RuntimeHarness", "RuntimeIntegrationError", "validate_job_notification"]
