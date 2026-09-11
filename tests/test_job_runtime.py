from __future__ import annotations

import base64
import hashlib
import json
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


from multi_agent_manager import job_runtime as runtime


def _take(connection: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise AssertionError("peer closed the connection")
        data.extend(chunk)
    return bytes(data)


def _read_frame(connection: socket.socket) -> tuple[int, bytes]:
    first, second = _take(connection, 2)
    size = second & 0x7F
    if size == 126:
        size = int.from_bytes(_take(connection, 2), "big")
    elif size == 127:
        size = int.from_bytes(_take(connection, 8), "big")
    mask = _take(connection, 4) if second & 0x80 else None
    payload = _take(connection, size)
    if mask:
        payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return first & 0x0F, payload


def _send_frame(connection: socket.socket, opcode: int, payload: bytes, final: bool = True) -> None:
    prefix = 0x80 if final else 0
    size = len(payload)
    if size < 126:
        header = bytes((prefix | opcode, size))
    elif size < 65536:
        header = bytes((prefix | opcode, 126)) + size.to_bytes(2, "big")
    else:
        header = bytes((prefix | opcode, 127)) + size.to_bytes(8, "big")
    connection.sendall(header + payload)


class AppServerFixture:
    def __init__(self, handler) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name) / "app-server.sock")
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(1)
        self.handler = handler
        self.errors: list[BaseException] = []
        self.thread = threading.Thread(target=self._serve, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.listener.close()
        self.thread.join(timeout=1)
        self.directory.cleanup()
        if self.errors:
            raise self.errors[0]

    def _serve(self) -> None:
        try:
            connection, _ = self.listener.accept()
            with connection:
                connection.settimeout(1)
                data = bytearray()
                while b"\r\n\r\n" not in data:
                    data.extend(connection.recv(4096))
                header = bytes(data).split(b"\r\n\r\n", 1)[0].decode("ascii")
                headers = dict(line.split(":", 1) for line in header.split("\r\n")[1:] if ":" in line)
                key = headers["Sec-WebSocket-Key"].strip()
                accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
                connection.sendall(
                    f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode()
                )
                self.handler(self, connection)
        except BaseException as exc:
            self.errors.append(exc)

    @staticmethod
    def read_json(connection: socket.socket) -> dict:
        opcode, payload = _read_frame(connection)
        if opcode != 1:
            raise AssertionError(f"expected text frame, received {opcode}")
        return json.loads(payload)

    @staticmethod
    def send_json(connection: socket.socket, message: dict) -> None:
        _send_frame(connection, 1, json.dumps(message, separators=(",", ":")).encode())


class ProcessProbeTests(unittest.TestCase):
    def test_local_lifecycle_and_identity_mismatch(self) -> None:
        processes = [subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"]) for _ in range(2)]
        try:
            running = [runtime.probe_process("localhost", process.pid) for process in processes]
            self.assertEqual([result["status"] for result in running], ["running", "running"])
            self.assertTrue(all(result["identity"] for result in running))
            changed = dict(running[0]["identity"])
            changed["start_ticks"] += 1
            self.assertEqual(runtime.probe_process("localhost", processes[0].pid, changed)["status"], "stopped")
        finally:
            for process in processes:
                process.terminate()
                process.wait(timeout=3)
        self.assertEqual(runtime.probe_process("localhost", processes[0].pid)["status"], "stopped")

    def test_zombie_is_stopped(self) -> None:
        process = subprocess.Popen([sys.executable, "-c", "pass"])
        try:
            result = {"status": "running"}
            deadline = time.monotonic() + 1
            while result["status"] == "running" and time.monotonic() < deadline:
                time.sleep(0.01)
                result = runtime.probe_process("localhost", process.pid)
            self.assertEqual(result["status"], "stopped")
            self.assertIn("zombie", result["error"])
        finally:
            process.wait(timeout=3)

    def test_remote_timeout_is_unknown_and_host_is_not_injected(self) -> None:
        with mock.patch.object(runtime.subprocess, "run", side_effect=subprocess.TimeoutExpired("ssh", 1)) as run:
            result = runtime.probe_process("wuwen-1", 123)
        self.assertEqual(result["status"], "unknown")
        command = run.call_args.args[0]
        self.assertEqual(command[0], "ssh")
        self.assertEqual(command[5:7], ["--", "wuwen-1"])
        self.assertIn("python3 -c", command[-1])
        self.assertTrue(command[-1].endswith(" 123"))
        with mock.patch.object(runtime.subprocess, "run") as run:
            invalid = runtime.probe_process("wuwen-1; echo unsafe", 123)
        self.assertEqual(invalid["status"], "unknown")
        run.assert_not_called()

    def test_remote_missing_and_unreadable_processes_are_distinguished(self) -> None:
        responses = [
            subprocess.CompletedProcess(["ssh"], 4, stdout="", stderr=""),
            subprocess.CompletedProcess(["ssh"], 5, stdout="", stderr="permission denied"),
        ]
        with mock.patch.object(runtime.subprocess, "run", side_effect=responses):
            missing = runtime.probe_process("wuwen-1", 123)
            unreadable = runtime.probe_process("wuwen-1", 124)
        self.assertEqual(missing["status"], "stopped")
        self.assertEqual(missing["error"], "process not found")
        self.assertEqual(unreadable["status"], "unknown")
        self.assertIn("cannot be accessed", unreadable["error"])


class AgentProbeTests(unittest.TestCase):
    def test_batch_query_handles_ping_and_fragmented_response(self) -> None:
        def handler(fixture: AppServerFixture, connection: socket.socket) -> None:
            initialize = fixture.read_json(connection)
            self.assertEqual(initialize["method"], "initialize")
            fixture.send_json(connection, {"id": initialize["id"], "result": {}})
            self.assertEqual(fixture.read_json(connection)["method"], "initialized")
            first = fixture.read_json(connection)
            self.assertEqual(first["params"], {"threadId": "active-agent", "includeTurns": False})
            _send_frame(connection, 9, b"check")
            self.assertEqual(_read_frame(connection), (10, b"check"))
            response = json.dumps({"id": first["id"], "result": {"thread": {"status": {"type": "active"}}}}).encode()
            _send_frame(connection, 1, response[:12], final=False)
            _send_frame(connection, 0, response[12:])
            second = fixture.read_json(connection)
            self.assertEqual(second["params"], {"threadId": "idle-agent", "includeTurns": False})
            fixture.send_json(connection, {"id": second["id"], "result": {"thread": {"status": {"type": "idle"}}}})
            third = fixture.read_json(connection)
            self.assertEqual(third["params"], {"threadId": "not-loaded-agent", "includeTurns": False})
            fixture.send_json(connection, {"id": third["id"], "result": {"thread": {"status": {"type": "notLoaded"}}}})

        with AppServerFixture(handler) as fixture:
            result = runtime.probe_agents(["active-agent", "idle-agent", "not-loaded-agent"], fixture.path)
        self.assertEqual(result["active-agent"]["status"], "active")
        self.assertEqual(result["idle-agent"]["status"], "idle")
        self.assertEqual(result["not-loaded-agent"]["status"], "notLoaded")
        self.assertIsNone(result["active-agent"]["error"])

    def test_rpc_error_is_limited_to_its_agent(self) -> None:
        def handler(fixture: AppServerFixture, connection: socket.socket) -> None:
            initialize = fixture.read_json(connection)
            fixture.send_json(connection, {"id": initialize["id"], "result": {}})
            fixture.read_json(connection)
            failed = fixture.read_json(connection)
            fixture.send_json(connection, {"id": failed["id"], "error": {"code": -1, "message": "thread missing"}})
            good = fixture.read_json(connection)
            fixture.send_json(connection, {"id": good["id"], "result": {"thread": {"status": {"type": "systemError"}}}})

        with AppServerFixture(handler) as fixture:
            result = runtime.probe_agents(["missing", "broken"], fixture.path)
        self.assertEqual(result["missing"]["status"], "unknown")
        self.assertIn("thread missing", result["missing"]["error"])
        self.assertEqual(result["broken"]["status"], "systemError")

    def test_timeout_marks_all_agents_unknown(self) -> None:
        def handler(fixture: AppServerFixture, connection: socket.socket) -> None:
            fixture.read_json(connection)
            time.sleep(0.15)

        with mock.patch.object(runtime, "APP_SERVER_TIMEOUT_SECONDS", 0.03):
            with AppServerFixture(handler) as fixture:
                result = runtime.probe_agents(["first", "second"], fixture.path)
        self.assertEqual({value["status"] for value in result.values()}, {"unknown"})
        self.assertTrue(all("timed out" in value["error"].lower() for value in result.values()))


class EventStreamTests(unittest.TestCase):
    def test_resume_preserves_notification_received_before_its_snapshot(self) -> None:
        def handler(fixture: AppServerFixture, connection: socket.socket) -> None:
            initialize = fixture.read_json(connection)
            self.assertEqual(initialize["method"], "initialize")
            fixture.send_json(connection, {"id": initialize["id"], "result": {}})
            self.assertEqual(fixture.read_json(connection)["method"], "initialized")
            resume = fixture.read_json(connection)
            self.assertEqual(resume["method"], "thread/resume")
            fixture.send_json(connection, {
                "method": "turn/completed",
                "params": {"threadId": "agent", "turn": {"id": "turn-1"}},
            })
            fixture.send_json(connection, {
                "id": resume["id"],
                "result": {"thread": {"id": "agent", "status": {"type": "active"}, "turns": []}},
            })

        with AppServerFixture(handler) as fixture:
            stream = runtime.AppServerEventStream.connect(fixture.path)
            try:
                snapshot = stream.resume("agent")
                queued = stream.poll(0)
            finally:
                stream.close()
        self.assertEqual(snapshot["thread"]["id"], "agent")
        self.assertEqual(queued, {
            "method": "turn/completed",
            "params": {"threadId": "agent", "turn": {"id": "turn-1"}},
        })


if __name__ == "__main__":
    unittest.main()
