from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest import mock

from multi_agent_manager import job_runtime, wake_compat


MANAGER = "01a081fe-d6c2-74f2-a73d-68584e9d915b"


def _take(connection: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        part = connection.recv(size - len(chunks))
        if not part:
            raise ConnectionError("peer closed")
        chunks.extend(part)
    return bytes(chunks)


def _read_frame(connection: socket.socket) -> tuple[int, bytes]:
    first, second = _take(connection, 2)
    size = second & 0x7F
    if size == 126:
        size = int.from_bytes(_take(connection, 2), "big")
    elif size == 127:
        size = int.from_bytes(_take(connection, 8), "big")
    mask = _take(connection, 4) if second & 0x80 else None
    payload = _take(connection, size)
    if mask is not None:
        payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return first & 0x0F, payload


def _send_text(connection: socket.socket, message: dict) -> None:
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    header = bytes((0x81, len(payload))) if len(payload) < 126 else bytes((0x81, 126)) + len(payload).to_bytes(2, "big")
    connection.sendall(header + payload)


class AppServerFixture:
    """A Unix/WebSocket server that rejects only unknown thread operations."""

    def __init__(self, *, rejection: str = "thread not found") -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.path = Path(self._temporary.name) / "control.sock"
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(self.path))
        self.listener.listen()
        self.listener.settimeout(0.05)
        self.stop = threading.Event()
        self.error: BaseException | None = None
        self.requests: list[dict] = []
        self.rejection = rejection
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        while not self.stop.is_set():
            try:
                connection, _ = self.listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            try:
                with connection:
                    self._handle(connection)
            except ConnectionError:
                continue
            except BaseException as exc:  # surface server assertions to the test
                self.error = exc
                return

    def _handle(self, connection: socket.socket) -> None:
        request = bytearray()
        while b"\r\n\r\n" not in request:
            request.extend(_take(connection, 1))
        headers = {}
        for line in request.decode("ascii").split("\r\n")[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.lower()] = value.strip()
        key = headers["sec-websocket-key"]
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        connection.sendall(
            (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode("ascii")
        )
        opcode, payload = _read_frame(connection)
        if opcode != 1:
            raise AssertionError("initialize was not a text frame")
        initialize = json.loads(payload)
        self.requests.append(initialize)
        if initialize.get("method") != "initialize" or not isinstance(initialize.get("id"), int):
            raise AssertionError("expected initialize request")
        _send_text(connection, {"id": initialize["id"], "result": {}})
        opcode, payload = _read_frame(connection)
        initialized = json.loads(payload)
        self.requests.append(initialized)
        if opcode != 1 or initialized.get("method") != "initialized" or "id" in initialized:
            raise AssertionError("expected initialized notification")
        while True:
            opcode, payload = _read_frame(connection)
            if opcode != 1:
                raise AssertionError("request was not a text frame")
            request = json.loads(payload)
            self.requests.append(request)
            if not isinstance(request.get("id"), int) or not isinstance(request.get("method"), str):
                raise AssertionError("expected JSON-RPC request")
            _send_text(connection, {"id": request["id"], "error": {"message": self.rejection}})

    def close(self) -> None:
        self.stop.set()
        self.listener.close()
        self.thread.join(timeout=2)
        self._temporary.cleanup()
        if self.error is not None:
            raise self.error

    def __enter__(self) -> "AppServerFixture":
        return self

    def __exit__(self, *_args) -> None:
        self.close()


class WakeCompatibilityTests(unittest.TestCase):
    def test_unknown_thread_rpc_sequence_uses_no_model_request(self):
        with AppServerFixture() as fixture, mock.patch.dict(
            os.environ, {"MAM_APP_SERVER_SOCKET": str(fixture.path)}, clear=False
        ):
            result = wake_compat.require_compatible()
        self.assertEqual(result["socket_path"], str(fixture.path))
        self.assertEqual(result["capabilities"]["model_requests"], 0)
        self.assertEqual(result["capabilities"]["managed_agent_delivery"], "not-validated-by-lightweight-check")
        self.assertEqual(
            [request["method"] for request in fixture.requests],
            ["initialize", "initialized", "thread/read", "thread/resume", "thread/turns/list", "turn/start"],
        )
        requests = fixture.requests[2:]
        thread_ids = [request["params"]["threadId"] for request in requests]
        self.assertEqual(len(set(thread_ids)), 1)
        self.assertRegex(thread_ids[0], r"^[0-9a-f-]{36}$")
        self.assertEqual(requests[0]["params"], {"threadId": thread_ids[0], "includeTurns": False})
        self.assertEqual(requests[1]["params"], {"threadId": thread_ids[0], "excludeTurns": True})
        self.assertEqual(
            requests[2]["params"],
            {"threadId": thread_ids[0], "limit": 1, "sortDirection": "desc", "itemsView": "notLoaded"},
        )
        self.assertEqual(
            requests[3]["params"],
            {"threadId": thread_ids[0], "input": [{"type": "text", "text": "MAM compatibility probe; unknown thread only."}]},
        )
        self.assertNotIn("model", requests[3]["params"])
        self.assertNotIn("effort", requests[3]["params"])

    def test_unsupported_rpc_rejection_is_not_compatible(self):
        with AppServerFixture(rejection="method not found") as fixture, mock.patch.dict(
            os.environ, {"MAM_APP_SERVER_SOCKET": str(fixture.path)}, clear=False
        ):
            with self.assertRaisesRegex(wake_compat.CompatibilityError, "did not reject thread/read"):
                wake_compat.require_compatible()

    def test_known_empty_thread_rejections_are_distinguished_from_unsupported_methods(self):
        for detail in (
            "App Server request thread/read failed: thread not loaded: id",
            "App Server request thread/resume failed: no rollout found for thread id id",
            "App Server request turn/start failed: thread not found: id",
        ):
            self.assertTrue(wake_compat._unknown_thread_rejection(detail), detail)
        self.assertFalse(wake_compat._unknown_thread_rejection("App Server request thread/read failed: method not found"))

    def test_socket_unavailable_is_a_bounded_actionable_failure(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"MAM_APP_SERVER_SOCKET": str(Path(directory) / "missing.sock")}, clear=False
        ):
            with self.assertRaisesRegex(wake_compat.CompatibilityError, "control socket is unavailable"):
                wake_compat.require_compatible()

    def test_control_socket_environment_rejects_line_breaks(self):
        with mock.patch.dict(os.environ, {"MAM_APP_SERVER_SOCKET": "/tmp/control\nnext"}, clear=False):
            with self.assertRaisesRegex(wake_compat.CompatibilityError, "single-line absolute path"):
                wake_compat.configured_socket_path()

    def test_transport_error_does_not_echo_remote_secret(self):
        with AppServerFixture() as fixture, mock.patch.object(
            job_runtime.AppServerEventStream,
            "connect",
            side_effect=job_runtime.AppServerEventError("TOKEN=do-not-log"),
        ), mock.patch.dict(os.environ, {"MAM_APP_SERVER_SOCKET": str(fixture.path)}, clear=False):
            with self.assertRaises(wake_compat.CompatibilityError) as captured:
                wake_compat.require_compatible()
        self.assertIn("event stream is unavailable", str(captured.exception))
        self.assertNotIn("TOKEN", str(captured.exception))

    def test_socket_replacement_during_probe_is_rejected(self):
        with mock.patch.object(
            wake_compat, "configured_socket_path", return_value=Path("/tmp/mam-control.sock")
        ), mock.patch.object(
            wake_compat, "_socket_identity", side_effect=[{"device": 1, "inode": 2}, {"device": 1, "inode": 3}]
        ), mock.patch.object(wake_compat, "_api_rejection_probe", return_value=("thread/read",)):
            with self.assertRaisesRegex(wake_compat.CompatibilityError, "changed during validation"):
                wake_compat.require_compatible()

    def test_compatible_json_cli_output_is_machine_readable(self):
        mapping = {"socket_path": "/tmp/control.sock", "capabilities": {"model_requests": 0}, "diagnostics": {}}
        stream = io.StringIO()
        with mock.patch.object(wake_compat, "require_compatible", return_value=mapping), contextlib.redirect_stdout(stream):
            self.assertEqual(wake_compat._main(["--json"]), 0)
        self.assertEqual(json.loads(stream.getvalue()), mapping)

    def test_healthy_service_status_is_accepted(self):
        result = wake_compat.service_readiness(
            {"running": True, "healthy": True, "manager": MANAGER, "pending": {"count": 0, "events": []}, "status": "healthy"}
        )
        self.assertEqual(result, {"status": "healthy", "running": True, "pending": 0, "manager": MANAGER})

    def test_fresh_project_awaiting_manager_is_an_acknowledged_idle_state(self):
        result = wake_compat.service_readiness(
            {"running": True, "healthy": True, "manager": None, "pending": {"count": 0, "events": []}, "status": "awaiting_manager"}
        )
        self.assertEqual(result["status"], "awaiting_manager")
        self.assertIsNone(result["manager"])

    def test_bound_project_missing_manager_has_explicit_remediation(self):
        with self.assertRaisesRegex(wake_compat.CompatibilityError, "mam service start --manager AGENT-ID"):
            wake_compat.service_readiness(
                {
                    "running": False,
                    "healthy": False,
                    "manager": None,
                    "pending": {"count": 0, "events": []},
                    "status": "error",
                    "error": "existing bound tasks have no determinable Manager; run mam service start --manager AGENT-ID",
                }
            )

    def test_unrelated_service_error_keeps_useful_category_and_redacts_assignment_secret(self):
        with self.assertRaises(wake_compat.CompatibilityError) as captured:
            wake_compat.service_readiness(
                {
                    "running": False,
                    "healthy": False,
                    "manager": None,
                    "pending": {"count": 0, "events": []},
                    "status": "error",
                    "error": "launcher path missing; TOKEN=do-not-log",
                }
            )
        self.assertIn("launcher path missing", str(captured.exception))
        self.assertIn("TOKEN=<redacted>", str(captured.exception))

    def test_module_failure_is_stdout_and_nonzero(self):
        stream = io.StringIO()
        with mock.patch.object(wake_compat, "require_compatible", side_effect=wake_compat.CompatibilityError("socket unavailable")), contextlib.redirect_stdout(stream):
            result = wake_compat._main([])
        self.assertEqual(result, 1)
        self.assertIn("MAM proactive wakeup compatibility: FAIL", stream.getvalue())
        self.assertIn("socket unavailable", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
