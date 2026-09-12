from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
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


class InstallerScriptTests(unittest.TestCase):
    source_root = Path(__file__).resolve().parents[1]

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.primary = self.project / "mam-state"
        self.primary.mkdir()
        self._write_checkout_files(self.primary)
        self._git("init", self.primary)
        self._git("config", self.primary, "user.email", "tests@example.invalid")
        self._git("config", self.primary, "user.name", "MAM tests")
        self._git("add", self.primary, ".")
        self._git("commit", self.primary, "-m", "fixture")
        self.checkout = self.project / "installer-checkout"
        self._git("worktree", self.primary, "add", "-b", "fixture-installer", str(self.checkout), "HEAD")
        branch = subprocess.check_output(["git", "-C", str(self.primary), "branch", "--show-current"], text=True).strip()
        (self.project / ".mam").mkdir()
        (self.project / ".mam" / "env.json").write_text(
            json.dumps({"MAM_ROOT": str(self.primary), "PROJECT_ROOT": str(self.project), "MAM_BRANCH": branch}),
            encoding="utf-8",
        )
        self.home = self.root / "home"
        self.home.mkdir()
        (self.home / ".bashrc").write_text(
            "export KEEP_THIS=1\n"
            "# >>> MAM Codex App Server trace >>>\n"
            "if [[ \":$PATH:\" != *\":$HOME/.local/bin:\"* ]]; then\n"
            "    export PATH=\"$HOME/.local/bin:$PATH\"\n"
            "fi\n"
            "export RUST_LOG=\"off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info\"\n"
            "export LOG_FORMAT=json\n"
            "# <<< MAM Codex App Server trace <<<\n"
            "[[ -z \"$PS1\" ]] && return\n"
            "export AFTER_RETURN=1\n",
            encoding="utf-8",
        )
        (self.home / ".profile").write_text("export LOGIN_KEEP=1\n", encoding="utf-8")
        self.pipx_home = self.home / "pipx"
        self.venv = self.pipx_home / "venvs" / "multi-agent-manager"
        subprocess.run([sys.executable, "-m", "venv", str(self.venv)], check=True)
        installed_python = self.venv / "bin" / "python"
        site_packages = Path(
            subprocess.check_output([str(installed_python), "-c", "import site; print(site.getsitepackages()[0])"], text=True).strip()
        )
        os.symlink(self.checkout / "multi_agent_manager", site_packages / "multi_agent_manager")
        self.fake_bin = self.root / "fake-bin"
        self.fake_bin.mkdir()
        self.log = self.root / "commands.log"
        self.state = self.root / "service-state"
        self.state.write_text("stopped\n", encoding="utf-8")
        self._write_fake_mam()
        self._write_fake_pipx()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _git(*arguments: str | Path) -> None:
        if arguments[0] == "init":
            _, repository = arguments
            subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
            return
        command, repository, *rest = arguments
        subprocess.run(["git", "-C", str(repository), str(command), *(str(item) for item in rest)], check=True, stdout=subprocess.DEVNULL)

    def _write_checkout_files(self, root: Path) -> None:
        (root / "scripts").mkdir()
        (root / "multi_agent_manager").mkdir()
        (root / "tests").mkdir()
        for relative in (
            "scripts/install.sh",
            "multi_agent_manager/__init__.py",
            "multi_agent_manager/job_runtime.py",
            "multi_agent_manager/wake_compat.py",
            "multi_agent_manager/liveprobe.py",
            "multi_agent_manager/wake_runtime.py",
            "multi_agent_manager/cli.py",
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.source_root / relative, target)
        (root / "pyproject.toml").write_text("[project]\nname = 'fixture'\nversion = '0'\n", encoding="utf-8")
        # Git does not retain an empty directory, while the installer requires
        # a tests directory before it will run its suite.
        (root / "tests" / "test_placeholder.py").write_text("# fixture\n", encoding="utf-8")

    def _write_fake_mam(self) -> None:
        self.fake_mam = self.root / "fake-mam"
        self.fake_mam.write_text(
            r'''#!/usr/bin/env bash
set -euo pipefail
{
    printf 'cwd=%s thread=%s args=' "$PWD" "${CODEX_THREAD_ID:-}"
    printf '%s ' "$@"
    printf '\n'
} >> "$FAKE_LOG"
if [[ "${1:-}" == --help ]]; then
    exit 0
fi
if [[ "${1:-}" != service ]]; then
    exit 64
fi
if [[ "$PWD" != "$FAKE_EXPECT_PROJECT" ]]; then
    printf 'wrong project context\n' >&2
    exit 65
fi
if [[ -n "${CODEX_THREAD_ID:-}" ]]; then
    printf 'installer thread leaked into service command\n' >&2
    exit 66
fi
state="$(cat "$FAKE_STATE")"
emit_status() {
    case "$1" in
        stopped)
            printf '%s\n' '{"running":false,"healthy":false,"manager":null,"pending":{"count":0,"events":[]},"status":"disabled"}'
            ;;
        healthy)
            printf '{"running":true,"healthy":true,"manager":"%s","pending":{"count":0,"events":[]},"status":"healthy"}\n' "$FAKE_MANAGER"
            ;;
        awaiting_manager)
            printf '%s\n' '{"running":true,"healthy":true,"manager":null,"pending":{"count":0,"events":[]},"status":"awaiting_manager"}'
            ;;
        missing_manager)
            printf '%s\n' '{"running":false,"healthy":false,"manager":null,"pending":{"count":0,"events":[]},"status":"error","error":"existing bound tasks have no determinable Manager; run mam service start --manager AGENT-ID"}'
            ;;
        invalid)
            printf '%s\n' 'not-json'
            ;;
        *)
            printf '%s\n' '{"running":false,"healthy":false,"manager":null,"pending":{"count":0,"events":[]},"status":"error","error":"launcher path missing; TOKEN=do-not-log"}'
            ;;
    esac
}
case "${2:-}" in
    status)
        emit_status "$state"
        ;;
    stop)
        if [[ "$state" != healthy && "$state" != awaiting_manager ]]; then
            printf 'stop requested without a running service\n' >&2
            exit 67
        fi
        printf 'stopped\n' > "$FAKE_STATE"
        emit_status stopped
        ;;
    start)
        if [[ "${FAKE_START_FAIL:-}" == 1 ]]; then
            printf 'launcher path missing; TOKEN=do-not-log\n' >&2
            exit 68
        fi
        if [[ "$state" != stopped ]]; then
            printf 'duplicate service start\n' >&2
            exit 69
        fi
        printf '%s\n' "${FAKE_START_STATE:-healthy}" > "$FAKE_STATE"
        emit_status "${FAKE_START_STATE:-healthy}"
        ;;
    *)
        exit 64
        ;;
esac
''',
            encoding="utf-8",
        )
        self.fake_mam.chmod(0o755)

    def _write_fake_pipx(self) -> None:
        path = self.fake_bin / "pipx"
        path.write_text(
            r'''#!/usr/bin/env bash
set -euo pipefail
printf 'pipx args=' >> "$FAKE_LOG"
printf '%s ' "$@" >> "$FAKE_LOG"
printf '\n' >> "$FAKE_LOG"
if [[ "${1:-}" == environment && "${2:-}" == --value && "${3:-}" == PIPX_HOME ]]; then
    printf '%s\n' "$PIPX_HOME"
    exit 0
fi
if [[ "${1:-}" == install ]]; then
    if [[ "${FAKE_PIPX_FAIL:-}" == 1 ]]; then
        printf 'simulated pipx failure\n' >&2
        exit 71
    fi
    mkdir -p "$PIPX_BIN_DIR"
    cp "$FAKE_MAM" "$PIPX_BIN_DIR/mam"
    chmod 755 "$PIPX_BIN_DIR/mam"
    exit 0
fi
exit 72
''',
            encoding="utf-8",
        )
        path.chmod(0o755)

    @staticmethod
    def _probe_stubs() -> str:
        return r'''
ensure_runtime_logging() {
    TARGET_SOCKET=/tmp/fake-app-server.sock
    TARGET_LOG_PATH=/tmp/fake-app-server.log
    printf 'trace socket=%s log=%s\n' "$TARGET_SOCKET" "$TARGET_LOG_PATH" >> "$FAKE_LOG"
}
run_wait_compatibility() {
    printf 'wait python=%s socket=%s log=%s\n' "$INSTALLED_PYTHON" "$WAIT_SOCKET" "$WAIT_LOG_PATH" >> "$FAKE_LOG"
    if [[ "${FAKE_WAIT_COMPAT_FAIL:-}" == 1 ]]; then
        incomplete 'simulated optional wait compatibility failure'
        return 1
    fi
    printf 'MAM optional wait: live App Server trace compatibility PASS\n'
}
run_lightweight_probe() {
    printf 'lightweight python=%s\n' "$INSTALLED_PYTHON" >> "$FAKE_LOG"
    COMPATIBILITY_JSON="$INSTALL_TMP/compatibility.json"
    printf '%s\n' '{"socket_path":"/tmp/fake-app-server.sock","capabilities":{"model_requests":0},"diagnostics":{}}' > "$COMPATIBILITY_JSON"
    printf 'MAM proactive wakeup: non-model App Server API compatibility PASS\n'
}
run_live_delivery_probe() {
    printf 'liveprobe python=%s\n' "$INSTALLED_PYTHON" >> "$FAKE_LOG"
    if [[ "${FAKE_LIVEPROBE_FAIL:-}" == 1 ]]; then
        incomplete 'simulated isolated delivery failure'
        return 1
    fi
    printf 'MAM proactive wakeup: isolated real delivery PASS (6 model turns)\n'
}
'''

    def _fixture_environment(self, overrides: dict[str, str]) -> dict[str, str]:
        environment = dict(os.environ)
        # Test defaults must not inherit the real installer's optional Manager
        # selection.  Individual tests supply it explicitly when exercising
        # the final service-start path.
        environment.pop("MAM_SERVICE_MANAGER", None)
        environment.update({
            "HOME": str(self.home),
            "PIPX_HOME": str(self.pipx_home),
            "PATH": f"{self.fake_bin}:{os.environ['PATH']}",
            "FAKE_LOG": str(self.log),
            "FAKE_STATE": str(self.state),
            "FAKE_MAM": str(self.fake_mam),
            "FAKE_EXPECT_PROJECT": str(self.project),
            "FAKE_MANAGER": MANAGER,
        })
        environment.update(overrides)
        return environment

    def run_installer(self, *, probe_stubs: bool = True, **overrides: str) -> subprocess.CompletedProcess[str]:
        environment = self._fixture_environment(overrides)
        command = 'source "$1"\nrun_tests() { :; }\n'
        if probe_stubs:
            command += self._probe_stubs()
        command += "main\n"
        return subprocess.run(
            ["bash", "-c", command, "bash", str(self.checkout / "scripts" / "install.sh")],
            cwd=self.checkout,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def run_checkout_tests(self, **overrides: str) -> subprocess.CompletedProcess[str]:
        """Run the installer's pre-pipx test phase against the fixture checkout."""

        environment = self._fixture_environment(overrides)
        command = 'source "$1"\nCHECKOUT_ROOT="$2"\nchoose_source_python\nrun_tests\n'
        return subprocess.run(
            ["bash", "-c", command, "bash", str(self.checkout / "scripts" / "install.sh"), str(self.checkout)],
            cwd=self.checkout,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def service_commands(self) -> list[str]:
        if not self.log.exists():
            return []
        return [
            line.partition("args=")[2].strip()
            for line in self.log.read_text().splitlines()
            if line.startswith("cwd=") and "args=service " in line
        ]

    def test_installer_fixture_does_not_inherit_manager_control_value(self):
        with mock.patch.dict(os.environ, {"MAM_SERVICE_MANAGER": MANAGER}):
            result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.service_commands(), ["service status", "service start", "service status"])

    def test_checkout_tests_remove_manager_control_value(self):
        (self.checkout / "tests" / "test_manager_environment.py").write_text(
            "import os\n"
            "import unittest\n"
            "\n"
            "class ManagerEnvironmentTests(unittest.TestCase):\n"
            "    def test_manager_selection_is_not_a_test_input(self):\n"
            "        self.assertNotIn('MAM_SERVICE_MANAGER', os.environ)\n",
            encoding="utf-8",
        )
        result = self.run_checkout_tests(MAM_SERVICE_MANAGER=MANAGER)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_install_upgrade_failure_does_not_touch_probes_or_scheduler(self):
        result = self.run_installer(FAKE_PIPX_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pipx could not install", result.stdout)
        self.assertEqual(self.service_commands(), [])
        self.assertNotIn("liveprobe", self.log.read_text())

    def test_same_repository_sibling_checkout_is_installed_and_path_persists(self):
        self.assertNotEqual(self.primary, self.checkout)
        result = self.run_installer(CODEX_THREAD_ID="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("scheduler healthy", result.stdout)
        log = self.log.read_text()
        self.assertIn(f"pipx args=install --force {self.checkout}", log)
        self.assertIn(f"wait python={self.venv / 'bin' / 'python'}", log)
        self.assertIn(f"lightweight python={self.venv / 'bin' / 'python'}", log)
        self.assertIn(f"liveprobe python={self.venv / 'bin' / 'python'}", log)
        self.assertLess(log.index("wait python"), log.index("lightweight"))
        self.assertLess(log.index("lightweight"), log.index("liveprobe"))
        self.assertLess(log.index("liveprobe"), log.index("args=service status"))
        self.assertEqual(self.service_commands(), ["service status", "service start", "service status"])
        self.assertNotIn("aaaaaaaa", log)
        bashrc = (self.home / ".bashrc").read_text()
        self.assertIn("export KEEP_THIS=1", bashrc)
        self.assertEqual(bashrc.count("# >>> MAM Codex App Server trace >>>"), 1)
        self.assertIn('export RUST_LOG="off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info"', bashrc)
        self.assertIn("export LOG_FORMAT=json", bashrc)
        self.assertEqual(bashrc.count("# >>> MAM PATH >>>"), 1)
        self.assertLess(bashrc.index("# >>> MAM PATH >>>"), bashrc.index('[[ -z "$PS1" ]] && return'))
        self.assertTrue(list(self.home.glob(".bashrc.mam-path.*.bak")))
        interactive = subprocess.run(
            ["bash", "--noprofile", "--rcfile", str(self.home / ".bashrc"), "-ic", "command -v mam"],
            env={**os.environ, "HOME": str(self.home), "PATH": "/usr/bin:/bin"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(interactive.returncode, 0, interactive.stderr)
        self.assertEqual(interactive.stdout.strip(), str(self.home / ".local" / "bin" / "mam"))
        login = subprocess.run(
            ["bash", "--norc", "-lc", "command -v mam"],
            env={**os.environ, "HOME": str(self.home), "PATH": "/usr/bin:/bin"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(login.returncode, 0, login.stderr)
        self.assertEqual(login.stdout.strip().splitlines()[-1], str(self.home / ".local" / "bin" / "mam"))
        again = self.run_installer()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual((self.home / ".bashrc").read_text().count("# >>> MAM PATH >>>"), 1)

    def test_checkout_test_environment_reaches_current_source_in_detached_daemon(self):
        """A fresh checkout must outrank an older package for the daemon child.

        The test interpreter deliberately has an old ``multi_agent_manager``
        in its site-packages.  The checkout has no editable environment.  The
        fixture test starts the real detached fresh-project daemon, whose cwd
        is the separate MAM state root just like ``_spawn_service`` uses.
        """

        self.assertFalse((self.checkout / ".venv").exists())
        source_environment = self.root / "old-installed-python"
        subprocess.run([sys.executable, "-m", "venv", str(source_environment)], check=True)
        source_python = source_environment / "bin" / "python"
        site_packages = Path(
            subprocess.check_output([str(source_python), "-c", "import site; print(site.getsitepackages()[0])"], text=True).strip()
        )
        stale_package = site_packages / "multi_agent_manager"
        stale_package.mkdir()
        (stale_package / "__init__.py").write_text('"""Old installed package fixture."""\n', encoding="utf-8")
        stale_marker = self.root / "old-package-daemon-ran"
        (stale_package / "wake_runtime.py").write_text(
            "from pathlib import Path\n"
            "import os\n"
            "Path(os.environ['MAM_STALE_DAEMON_MARKER']).write_text('old package ran\\n', encoding='utf-8')\n"
            "raise SystemExit(91)\n",
            encoding="utf-8",
        )
        daemon_root = self.root / "daemon-state"
        daemon_projects = self.root / "daemon-projects"
        daemon_root.mkdir()
        daemon_projects.mkdir()
        (self.checkout / "tests" / "test_detached_source_import.py").write_text(
            "from pathlib import Path\n"
            "import os\n"
            "import time\n"
            "import unittest\n"
            "\n"
            "from multi_agent_manager import cli, job_runtime, wake_runtime\n"
            "\n"
            "\n"
            "class DetachedSourceImportTests(unittest.TestCase):\n"
            "    def test_daemon_uses_checkout_runtime_after_cwd_changes(self):\n"
            "        checkout = Path(os.environ['MAM_CHECKOUT_ROOT']).resolve()\n"
            "        self.assertEqual(Path(wake_runtime.__file__).resolve(), checkout / 'multi_agent_manager' / 'wake_runtime.py')\n"
            "        config = cli.ProjectConfig(Path(os.environ['MAM_TEST_DAEMON_ROOT']), Path(os.environ['MAM_TEST_DAEMON_PROJECTS']), 'project/daemon')\n"
            "        store = cli.Store(config)\n"
            "        started = False\n"
            "        try:\n"
            "            result = wake_runtime.start_service(config)\n"
            "            started = True\n"
            "            self.assertEqual(result['status'], 'awaiting_manager')\n"
            "            self.assertTrue(result['healthy'])\n"
            "            self.assertFalse(Path(os.environ['MAM_STALE_DAEMON_MARKER']).exists())\n"
            "        finally:\n"
            "            if started:\n"
            "                wake_runtime.stop_service(config)\n"
            "                deadline = time.monotonic() + 5.0\n"
            "                while time.monotonic() < deadline:\n"
            "                    state = wake_runtime._load_state(store)\n"
            "                    observed = job_runtime.probe_process('local', state['pid'], state['identity'])\n"
            "                    if observed['status'] == 'stopped':\n"
            "                        break\n"
            "                    time.sleep(0.05)\n"
            "                else:\n"
            "                    self.fail('fresh detached daemon did not stop')\n",
            encoding="utf-8",
        )
        result = self.run_checkout_tests(
            PATH=f"{source_python.parent}:{self.fake_bin}:{os.environ['PATH']}",
            PYTHONPATH="",
            MAM_CHECKOUT_ROOT=str(self.checkout),
            MAM_TEST_DAEMON_ROOT=str(daemon_root),
            MAM_TEST_DAEMON_PROJECTS=str(daemon_projects),
            MAM_STALE_DAEMON_MARKER=str(stale_marker),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(stale_marker.exists())

    def test_fresh_project_still_requires_live_app_server_before_service_status(self):
        missing = self.root / "missing.sock"
        result = self.run_installer(probe_stubs=False, MAM_APP_SERVER_SOCKET=str(missing), FAKE_START_STATE="awaiting_manager")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no standalone fallback was launched", result.stdout + result.stderr)
        self.assertEqual(self.service_commands(), [])

    def test_optional_wait_compatibility_failure_happens_before_wake_or_scheduler(self):
        result = self.run_installer(FAKE_WAIT_COMPAT_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated optional wait compatibility failure", result.stdout)
        log = self.log.read_text()
        self.assertIn("wait python", log)
        self.assertNotIn("lightweight", log)
        self.assertNotIn("liveprobe", log)
        self.assertEqual(self.service_commands(), [])

    def test_live_delivery_failure_happens_before_existing_scheduler_stop(self):
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer(FAKE_LIVEPROBE_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated isolated delivery failure", result.stdout)
        self.assertEqual(self.service_commands(), [])
        self.assertEqual(self.state.read_text().strip(), "healthy")

    def test_upgrade_stops_then_restarts_only_the_existing_project_singleton(self):
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.service_commands(), ["service status", "service stop", "service start", "service status"])
        self.assertEqual(self.state.read_text().strip(), "healthy")

    def test_fresh_bootstrap_is_awaiting_manager_without_capturing_installer_thread(self):
        result = self.run_installer(
            CODEX_THREAD_ID="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", FAKE_START_STATE="awaiting_manager"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("awaiting first Manager binding", result.stdout)
        self.assertEqual(self.service_commands(), ["service status", "service start", "service status"])
        self.assertNotIn("aaaaaaaa", self.log.read_text())
        self.assertEqual(self.state.read_text().strip(), "awaiting_manager")

    def test_installed_launcher_uses_project_context_and_explicit_manager_only(self):
        result = self.run_installer(MAM_SERVICE_MANAGER=MANAGER)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = self.log.read_text()
        self.assertIn(f"cwd={self.project} thread= args=service start --manager {MANAGER}", log)
        self.assertNotIn("CODEX_THREAD_ID", log)

    def test_bound_project_without_manager_is_nonzero_with_remediation(self):
        result = self.run_installer(FAKE_START_STATE="missing_manager")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bound tasks have no persisted Manager", result.stdout)
        self.assertIn("mam service start --manager AGENT-ID", result.stdout)

    def test_start_failure_retains_specific_reason_and_redacts_secret(self):
        result = self.run_installer(FAKE_START_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mam service start failed", result.stdout)
        self.assertIn("launcher path missing", result.stdout)
        self.assertIn("TOKEN=<redacted>", result.stdout)
        self.assertNotIn("TOKEN=do-not-log", result.stdout + result.stderr)

    def test_unrecognized_trace_block_stops_install_without_mutating_user_content(self):
        path = self.home / ".bashrc"
        content = path.read_text().replace("export LOG_FORMAT=json", "export LOG_FORMAT=custom")
        path.write_text(content, encoding="utf-8")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized MAM trace block", result.stderr)
        self.assertEqual(path.read_text(), content)
        self.assertEqual(self.service_commands(), [])

    def test_installer_does_not_implement_a_background_shell_supervisor(self):
        source = (self.source_root / "scripts" / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn("nohup", source)
        self.assertNotIn("setsid", source)
        self.assertNotIn("disown", source)
        for line in source.splitlines():
            code = line.split("#", 1)[0]
            self.assertIsNone(re.search(r"(?<![>&])&(?![&0-9])", code), line)


if __name__ == "__main__":
    unittest.main()
