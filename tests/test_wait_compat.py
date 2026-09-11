from __future__ import annotations

import base64
from contextlib import ExitStack
import io
import json
import os
from pathlib import Path
import pty
import select
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from multi_agent_manager import wait_compat


class WaitCompatibilityTests(unittest.TestCase):
    socket_path = Path("/tmp/mam-app-server.sock")
    log_path = Path("/tmp/mam-app-server.log")

    def passing_probes(self, *, cli_version: str | None = "codex-cli 0.154.0", behavior=None):
        stack = ExitStack()
        stack.enter_context(mock.patch.object(wait_compat, "_configured_paths", return_value=(self.socket_path, self.log_path)))
        stack.enter_context(mock.patch.object(wait_compat, "_socket_identity", return_value={"device": 1, "inode": 2}))
        stack.enter_context(
            mock.patch.object(wait_compat, "_log_identity", return_value={"device": 3, "inode": 4, "format": "json-request-span"})
        )
        stack.enter_context(
            mock.patch.object(
                wait_compat,
                "_live_control_probe",
                return_value={"response_keys": ["platformOs", "userAgent"], "user_agent_digest": "server-fingerprint"},
            )
        )
        stack.enter_context(
            mock.patch.object(
                wait_compat,
                "_behavior_probe",
                return_value=behavior
                or {
                    "thread_started": True,
                    "safe_steer_rejected": True,
                    "trace_request": True,
                    "trace_turn_mapping": True,
                },
            )
        )
        stack.enter_context(mock.patch.object(wait_compat, "_diagnostic_cli_version", return_value=cli_version))
        return stack

    def test_changed_or_unknown_versions_pass_when_behavior_passes(self):
        for version in ("codex-cli 99.0.0", "not-a-version", None):
            with self.subTest(version=version), self.passing_probes(cli_version=version):
                result = wait_compat.require_compatible()
                self.assertEqual(result["diagnostics"]["cli_version"], version)
                self.assertTrue(result["fingerprint"].startswith("sha256:"))

    def test_server_cli_version_difference_is_diagnostic_only(self):
        with self.passing_probes(cli_version="codex-cli 1.0.0"):
            result = wait_compat.require_compatible()
        self.assertEqual(result["capabilities"]["live_control_socket"], "validated")
        self.assertEqual(result["capabilities"]["native_message_wake"], "not-certified")

    def test_cli_version_does_not_change_the_behavioral_fingerprint(self):
        with self.passing_probes(cli_version="codex-cli 0.154.0"):
            before = wait_compat.require_compatible()
        with self.passing_probes(cli_version="codex-cli 99.0.0"):
            after = wait_compat.require_compatible()
        self.assertNotEqual(before["diagnostics"]["cli_version"], after["diagnostics"]["cli_version"])
        self.assertEqual(before["fingerprint"], after["fingerprint"])

    def test_every_call_revalidates_instead_of_accepting_a_stale_certificate(self):
        behavior = mock.Mock(
            side_effect=[
                {
                    "thread_started": True,
                    "safe_steer_rejected": True,
                    "trace_request": True,
                    "trace_turn_mapping": True,
                },
                wait_compat._CompatibilityFailure("event delivery failed"),
            ]
        )
        with self.passing_probes() as probes:
            probes.enter_context(mock.patch.object(wait_compat, "_behavior_probe", behavior))
            wait_compat.require_compatible()
            with self.assertRaisesRegex(RuntimeError, "event delivery failed"):
                wait_compat.require_compatible()
        self.assertEqual(behavior.call_count, 2)

    def test_restart_or_configuration_change_revalidates_and_changes_fingerprint(self):
        socket_identities = mock.Mock(side_effect=[{"device": 1, "inode": 2}, {"device": 1, "inode": 2}, {"device": 1, "inode": 9}, {"device": 1, "inode": 9}])
        behavior = mock.Mock(
            return_value={
                "thread_started": True,
                "safe_steer_rejected": True,
                "trace_request": True,
                "trace_turn_mapping": True,
            }
        )
        with self.passing_probes() as probes:
            probes.enter_context(mock.patch.object(wait_compat, "_socket_identity", socket_identities))
            probes.enter_context(mock.patch.object(wait_compat, "_behavior_probe", behavior))
            first = wait_compat.require_compatible()
            second = wait_compat.require_compatible()
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(behavior.call_count, 2)

    def test_disconnected_running_runtime_is_an_actionable_error(self):
        with self.passing_probes() as probes:
            probes.enter_context(
                mock.patch.object(
                    wait_compat,
                    "_live_control_probe",
                    side_effect=wait_compat._CompatibilityFailure("the running Codex App Server control connection is disconnected"),
                )
            )
            with self.assertRaisesRegex(RuntimeError, "control connection is disconnected"):
                wait_compat.require_compatible()

    def test_missing_event_delivery_is_rejected(self):
        with self.assertRaisesRegex(wait_compat._CompatibilityFailure, "event delivery"):
            wait_compat._validate_behavior(
                {
                    "thread_started": False,
                    "safe_steer_rejected": True,
                    "trace_request": True,
                    "trace_turn_mapping": True,
                }
            )

    def test_missing_trace_request_is_rejected(self):
        with self.assertRaisesRegex(wait_compat._CompatibilityFailure, "turn/steer was not recorded"):
            wait_compat._validate_behavior(
                {
                    "thread_started": True,
                    "safe_steer_rejected": True,
                    "trace_request": False,
                    "trace_turn_mapping": True,
                }
            )

    def test_missing_turn_mapping_is_rejected(self):
        with self.assertRaisesRegex(wait_compat._CompatibilityFailure, "mapped to turn.id"):
            wait_compat._validate_behavior(
                {
                    "thread_started": True,
                    "safe_steer_rejected": True,
                    "trace_request": True,
                    "trace_turn_mapping": False,
                }
            )

    def test_failed_no_model_behavior_is_rejected(self):
        with self.assertRaisesRegex(wait_compat._CompatibilityFailure, "safety check"):
            wait_compat._validate_behavior(
                {
                    "thread_started": True,
                    "safe_steer_rejected": False,
                    "trace_request": True,
                    "trace_turn_mapping": True,
                }
            )

    def test_stop_closes_pipes_after_an_already_exited_process(self):
        process = subprocess.Popen(
            [sys.executable, "-c", "pass"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        process.wait(timeout=5)
        wait_compat._stop(process)
        self.assertTrue(process.stdin.closed)
        self.assertTrue(process.stdout.closed)

    def test_stop_closes_pipes_after_termination_timeout(self):
        process = mock.Mock()
        process.poll.return_value = None
        process.stdin = io.BytesIO()
        process.stdout = io.BytesIO()
        process.wait.side_effect = [subprocess.TimeoutExpired(["codex"], 5), None]

        wait_compat._stop(process)

        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertTrue(process.stdin.closed)
        self.assertTrue(process.stdout.closed)

    def test_stop_closes_pipes_when_termination_errors(self):
        process = mock.Mock()
        process.poll.return_value = None
        process.stdin = io.BytesIO()
        process.stdout = io.BytesIO()
        process.terminate.side_effect = OSError("process disappeared")

        with self.assertRaisesRegex(OSError, "process disappeared"):
            wait_compat._stop(process)

        self.assertTrue(process.stdin.closed)
        self.assertTrue(process.stdout.closed)


class InstallerScriptTests(unittest.TestCase):
    script = Path(__file__).resolve().parents[1] / "scripts" / "install.sh"

    def run_sourced(self, body: str, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        command = f'source "$1"\n{body}'
        return subprocess.run(
            ["bash", "-c", command, "bash", str(self.script)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **(env or {})},
            check=False,
        )

    def run_confirmation_in_pty(self, response: bytes) -> tuple[int, str]:
        command = 'source "$1"\nif confirm_restart 123 /opt/codex /tmp/control.sock; then exit 0; else exit 9; fi'
        master, slave = pty.openpty()
        process = subprocess.Popen(
            ["bash", "-c", command, "bash", str(self.script)],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
        )
        os.close(slave)
        try:
            os.write(master, response)
            chunks: list[bytes] = []
            deadline = time.monotonic() + 5
            while process.poll() is None and time.monotonic() < deadline:
                readable, _, _ = select.select([master], [], [], 0.1)
                if readable:
                    try:
                        chunks.append(os.read(master, 4096))
                    except OSError:
                        break
            process.wait(timeout=5)
            while True:
                readable, _, _ = select.select([master], [], [], 0)
                if not readable:
                    break
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            return process.returncode, b"".join(chunks).decode(errors="replace")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)

    @staticmethod
    def encoded_record(value: object) -> str:
        return base64.b64encode(
            json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).decode("ascii")

    def test_bashrc_update_is_minimal_idempotent_and_reversible(self):
        legacy_rust_log = 'export RUST_LOG="off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info"\n'
        original = legacy_rust_log + "export LOG_FORMAT=json\nexport KEEP_ME=1\n[ -z \"$PS1\" ] && return\nalias ll='ls -alF'\n"
        with tempfile.TemporaryDirectory() as directory:
            bashrc = Path(directory) / ".bashrc"
            bashrc.write_text(original, encoding="utf-8")
            bashrc.chmod(0o640)
            environment = {"MAM_INSTALL_BASHRC": str(bashrc)}

            first = self.run_sourced("update_bashrc", env=environment)
            self.assertEqual(first.returncode, 0, first.stderr)
            updated = bashrc.read_text(encoding="utf-8")
            self.assertEqual(updated.count("# >>> MAM Codex App Server trace >>>"), 1)
            self.assertLess(updated.index("# >>> MAM Codex App Server trace >>>"), updated.index('[ -z "$PS1" ] && return'))
            self.assertEqual(updated.count(legacy_rust_log), 1)
            self.assertGreater(updated.index(legacy_rust_log), updated.index("# >>> MAM Codex App Server trace >>>"))
            self.assertNotIn("export LOG_FORMAT=json\nexport KEEP_ME", updated)
            self.assertIn("export KEEP_ME=1", updated)
            self.assertIn("alias ll='ls -alF'", updated)
            self.assertEqual(bashrc.stat().st_mode & 0o777, 0o640)
            backups = list(Path(directory).glob(".bashrc.mam-install.*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), original)
            self.assertIn("Rollback: cp -p", first.stdout)

            second = self.run_sourced("update_bashrc", env=environment)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(bashrc.read_text(encoding="utf-8"), updated)
            self.assertEqual(len(list(Path(directory).glob(".bashrc.mam-install.*.bak"))), 1)
            self.assertIn("already up to date", second.stdout)

    def test_incomplete_markers_leave_bashrc_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            bashrc = Path(directory) / ".bashrc"
            original = "keep=1\n# >>> MAM Codex App Server trace >>>\n"
            bashrc.write_text(original, encoding="utf-8")
            result = self.run_sourced(
                "if update_bashrc; then exit 0; else exit 7; fi", env={"MAM_INSTALL_BASHRC": str(bashrc)}
            )
            self.assertEqual(result.returncode, 7)
            self.assertEqual(bashrc.read_text(encoding="utf-8"), original)
            self.assertIn("incomplete MAM trace markers", result.stderr)

    def test_runtime_logging_missing_environment_returns_one(self):
        environment = {**os.environ, "RUST_LOG": "off", "LOG_FORMAT": "text"}
        process = subprocess.Popen(["/bin/sleep", "5"], env=environment)
        try:
            result = self.run_sourced(
                'if runtime_logging_ready "$CHECK_PID"; then exit 0; else status=$?; printf "status=%s\\n" "$status"; printf "%s\\n" "$RUNTIME_ENV_ERROR" >&2; exit "$status"; fi',
                env={"CHECK_PID": str(process.pid)},
            )
        finally:
            process.terminate()
            process.wait(timeout=5)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("status=1", result.stdout)
        self.assertIn("does not have the required JSON trace logging environment", result.stderr)

    def test_runtime_logging_unreadable_pid_returns_two(self):
        result = self.run_sourced(
            'if runtime_logging_ready 99999999; then exit 0; else status=$?; printf "status=%s\\n" "$status"; printf "%s\\n" "$RUNTIME_ENV_ERROR" >&2; exit "$status"; fi'
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("status=2", result.stdout)
        self.assertIn("cannot inspect the listener environment", result.stderr)

    def test_ensure_runtime_logging_restarts_only_for_missing_trace_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "restart-called"
            body = r'''
discover_app_server() { TARGET_PID=123; TARGET_LOG_PATH=/tmp/app-server.log; TARGET_SOCKET="$1"; TARGET_RECORD=old; }
log_is_regular() { return 0; }
runtime_logging_ready() { RUNTIME_ENV_ERROR='trace logging is missing'; return "${RUNTIME_STATUS}"; }
restart_app_server() { : > "$RESTART_MARKER"; }
if ensure_runtime_logging /tmp/control.sock; then exit 0; else exit $?; fi
'''
            missing = self.run_sourced(body, env={"RUNTIME_STATUS": "1", "RESTART_MARKER": str(marker)})
            self.assertEqual(missing.returncode, 0, missing.stderr)
            self.assertTrue(marker.exists())
            marker.unlink()

            unreadable = self.run_sourced(body, env={"RUNTIME_STATUS": "2", "RESTART_MARKER": str(marker)})
            self.assertEqual(unreadable.returncode, 1, unreadable.stderr)
            self.assertFalse(marker.exists())
            self.assertIn("trace logging is missing", unreadable.stderr)

    def test_existing_startup_lock_is_released_after_use(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app-server-startup.lock").touch()
            socket = root / "app-server-control.sock"
            result = self.run_sourced(
                'if acquire_startup_lock "$LOCK_SOCKET"; then release_startup_lock; [[ -z "$STARTUP_LOCK_FD" ]]; else exit $?; fi',
                env={"LOCK_SOCKET": str(socket)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_noninteractive_restart_refusal_never_calls_kill(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "kill-called"
            body = r'''
discover_app_server() {
    TARGET_PID=123; TARGET_START_TICKS=10; TARGET_EXECUTABLE=/opt/codex
    TARGET_PARENT_PID=122; TARGET_PARENT_START_TICKS=9; TARGET_PARENT_EXECUTABLE=/usr/bin/node
    TARGET_LOG_PATH=/tmp/app-server.log; TARGET_LAUNCH_PLAN=plan
    TARGET_SOCKET="$1"; TARGET_RECORD="$TARGET_PID:$TARGET_START_TICKS:$TARGET_EXECUTABLE:$TARGET_SOCKET"
}
send_term() { : > "$KILL_MARKER"; }
if restart_app_server /tmp/control.sock; then exit 0; else exit 7; fi
'''
            result = self.run_sourced(body, env={"KILL_MARKER": str(marker)})
            self.assertEqual(result.returncode, 7)
            self.assertFalse(marker.exists())
            self.assertIn("No terminal confirmation is available", result.stderr)
            self.assertIn("no process was stopped", result.stderr)

    def test_changed_target_after_confirmation_never_calls_kill(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "kill-called"
            body = r'''
calls=0
discover_app_server() {
    calls=$((calls + 1))
    TARGET_PID=123; TARGET_START_TICKS=10; TARGET_EXECUTABLE=/opt/codex
    if ((calls > 1)); then TARGET_START_TICKS=11; fi
    TARGET_PARENT_PID=122; TARGET_PARENT_START_TICKS=9; TARGET_PARENT_EXECUTABLE=/usr/bin/node
    TARGET_LOG_PATH=/tmp/app-server.log; TARGET_LAUNCH_PLAN=plan
    TARGET_SOCKET="$1"; TARGET_RECORD="$TARGET_PID:$TARGET_START_TICKS:$TARGET_EXECUTABLE:$TARGET_SOCKET"
}
confirm_restart() { return 0; }
acquire_startup_lock() { return 0; }
release_startup_lock() { :; }
validate_discovered_runtime() { RESTART_ERROR='the replacement has no trace environment'; return 1; }
send_term() { : > "$KILL_MARKER"; }
if restart_app_server /tmp/control.sock; then exit 0; else exit 7; fi
'''
            result = self.run_sourced(body, env={"KILL_MARKER": str(marker)})
            self.assertEqual(result.returncode, 7)
            self.assertFalse(marker.exists())
            self.assertIn("no process was stopped", result.stderr)

    def test_concurrent_valid_replacement_never_signals_or_launches(self):
        with tempfile.TemporaryDirectory() as directory:
            killed = Path(directory) / "kill-called"
            launched = Path(directory) / "launch-called"
            body = r'''
calls=0
discover_app_server() {
    calls=$((calls + 1))
    TARGET_PID=123; TARGET_START_TICKS=10; TARGET_EXECUTABLE=/opt/codex
    TARGET_PARENT_PID=122; TARGET_PARENT_START_TICKS=9; TARGET_PARENT_EXECUTABLE=/usr/bin/node
    TARGET_LOG_PATH=/tmp/app-server.log; TARGET_LAUNCH_PLAN=plan; TARGET_SOCKET="$1"
    if ((calls == 1)); then TARGET_RECORD=old; else TARGET_PID=456; TARGET_START_TICKS=20; TARGET_RECORD=replacement; fi
}
confirm_restart() { return 0; }
acquire_startup_lock() { return 0; }
release_startup_lock() { :; }
validate_discovered_runtime() { return 0; }
send_term() { : > "$KILL_MARKER"; }
launch_same_style() { : > "$LAUNCH_MARKER"; return 1; }
if restart_app_server /tmp/control.sock; then exit 0; else exit 7; fi
'''
            result = self.run_sourced(body, env={"KILL_MARKER": str(killed), "LAUNCH_MARKER": str(launched)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(killed.exists())
            self.assertFalse(launched.exists())
            self.assertIn("concurrent verified App Server replacement", result.stdout)

    def test_restart_orders_revalidation_stop_relaunch_and_unlock(self):
        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / "events"
            body = r'''
calls=0
discover_app_server() {
    calls=$((calls + 1)); printf 'discover%s\n' "$calls" >> "$EVENTS"
    TARGET_PID=123; TARGET_START_TICKS=10; TARGET_EXECUTABLE=/opt/codex
    TARGET_PARENT_PID=122; TARGET_PARENT_START_TICKS=9; TARGET_PARENT_EXECUTABLE=/usr/bin/node
    TARGET_LOG_PATH=/tmp/app-server.log; TARGET_LAUNCH_PLAN=plan; TARGET_SOCKET="$1"; TARGET_RECORD=old
}
confirm_restart() { printf 'confirm\n' >> "$EVENTS"; }
acquire_startup_lock() { printf 'lock\n' >> "$EVENTS"; }
release_startup_lock() { printf 'unlock\n' >> "$EVENTS"; }
send_term() { printf 'term\n' >> "$EVENTS"; }
wait_for_target_departure() { printf 'departed\n' >> "$EVENTS"; TARGET_LAUNCH_PLAN=cleared-by-discovery; RESTART_OUTCOME=departed; }
launch_same_style() { [[ "$1" == plan ]] || return 1; printf 'launch\n' >> "$EVENTS"; LAUNCHED_WRAPPER_PID=456; LAUNCHED_WRAPPER_START_TICKS=20; }
wait_for_replacement() { printf 'replacement\n' >> "$EVENTS"; TARGET_PID=789; TARGET_SOCKET="$1"; RESTART_OUTCOME=relaunched; }
if restart_app_server /tmp/control.sock; then exit 0; else exit 7; fi
'''
            result = self.run_sourced(body, env={"EVENTS": str(events)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                events.read_text(encoding="utf-8").splitlines(),
                ["discover1", "confirm", "lock", "discover2", "term", "departed", "launch", "replacement", "unlock"],
            )

    def test_launch_same_style_replays_wrapper_command_and_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cwd = root / "cwd"
            cwd.mkdir()
            socket = root / "app-server-control.sock"
            log_path = root / "app-server.log"
            log_path.write_text("", encoding="utf-8")
            wrapper = root / "codex"
            wrapper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            wrapper.chmod(0o755)
            capture = root / "capture.json"
            node = root / "node"
            node.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys, time\n"
                "from pathlib import Path\n"
                "Path(os.environ['CAPTURE_FILE']).write_text(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), "
                "'environment': {key: os.environ.get(key) for key in ('KEEP', 'RUST_LOG', 'LOG_FORMAT')}}), encoding='utf-8')\n"
                "print('fake npm wrapper started', flush=True)\n"
                "time.sleep(0.2)\n",
                encoding="utf-8",
            )
            node.chmod(0o755)
            log_stat = log_path.stat()
            plan = {
                "socket": str(socket),
                "log_path": str(log_path),
                "parent": {
                    "pid": 12,
                    "start_ticks": 34,
                    "executable": str(node),
                    "argv": ["node", str(wrapper), "app-server", "--listen", "unix://"],
                    "cwd": str(cwd),
                    "environment": {
                        "CAPTURE_FILE": str(capture),
                        "KEEP": "preserved",
                        "PATH": os.environ["PATH"],
                        "RUST_LOG": "old-trace",
                        "LOG_FORMAT": "text",
                    },
                    "stdin": "/dev/null",
                    "stdout": str(log_path),
                    "stderr": str(log_path),
                    "log_identity": {"device": log_stat.st_dev, "inode": log_stat.st_ino},
                },
            }
            result = self.run_sourced(
                'if launch_same_style "$LAUNCH_PLAN"; then printf "launched=%s:%s\\n" "$LAUNCHED_WRAPPER_PID" "$LAUNCHED_WRAPPER_START_TICKS"; else exit $?; fi',
                env={"LAUNCH_PLAN": self.encoded_record(plan)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            deadline = time.monotonic() + 5
            while not capture.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(capture.exists(), log_path.read_text(encoding="utf-8"))
            captured = json.loads(capture.read_text(encoding="utf-8"))
            self.assertEqual(captured["argv"], [str(wrapper), "app-server", "--listen", "unix://"])
            self.assertEqual(captured["cwd"], str(cwd))
            self.assertEqual(captured["environment"]["KEEP"], "preserved")
            self.assertEqual(captured["environment"]["RUST_LOG"], "off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info")
            self.assertEqual(captured["environment"]["LOG_FORMAT"], "json")
            self.assertIn("fake npm wrapper started", log_path.read_text(encoding="utf-8"))

    def test_isolated_restart_recreates_the_captured_node_wrapper(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cwd = root / "cwd"
            cwd.mkdir()
            socket = root / "app-server-control.sock"
            log_path = root / "app-server.log"
            (root / "app-server-startup.lock").touch()
            listener = root / "fake-listener"
            listener.write_text(
                "#!/usr/bin/env python3\n"
                "import os, signal, socket, time\n"
                "path = os.environ['FAKE_SOCKET']\n"
                "try:\n    os.unlink(path)\nexcept FileNotFoundError:\n    pass\n"
                "server = socket.socket(socket.AF_UNIX)\n"
                "server.bind(path)\n"
                "server.listen(1)\n"
                "running = True\n"
                "def stop(_signal, _frame):\n    global running\n    running = False\n"
                "signal.signal(signal.SIGTERM, stop)\n"
                "while running:\n    time.sleep(0.02)\n"
                "server.close()\n"
                "try:\n    os.unlink(path)\nexcept FileNotFoundError:\n    pass\n",
                encoding="utf-8",
            )
            listener.chmod(0o755)
            wrapper = root / "codex"
            wrapper.write_text(
                "const { spawn } = require('child_process');\n"
                "const child = spawn(process.env.FAKE_LISTENER, process.argv.slice(2), { env: process.env, stdio: 'inherit' });\n"
                "child.on('exit', code => process.exit(code === null ? 1 : code));\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            environment = {
                "PATH": os.environ["PATH"],
                "HOME": os.environ.get("HOME", str(root)),
                "FAKE_LISTENER": str(listener),
                "FAKE_SOCKET": str(socket),
                "KEEP": "preserved",
                "RUST_LOG": "old-trace",
                "LOG_FORMAT": "text",
            }
            initial = None
            replacement_parent = None
            try:
                with log_path.open("ab") as log_handle:
                    initial = subprocess.Popen(
                        [node, str(wrapper), "app-server", "--listen", "unix://"],
                        cwd=cwd,
                        env=environment,
                        stdin=subprocess.DEVNULL,
                        stdout=log_handle,
                        stderr=log_handle,
                        start_new_session=True,
                    )
                deadline = time.monotonic() + 5
                while not socket.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(socket.exists(), log_path.read_text(encoding="utf-8"))
                body = r'''
confirm_restart() { return 0; }
if restart_app_server "$FAKE_SOCKET"; then
    if runtime_logging_ready "$TARGET_PID"; then
        printf 'replacement=%s parent=%s\n' "$TARGET_PID" "$TARGET_PARENT_PID"
        send_term "$TARGET_PID" "$TARGET_START_TICKS" "$TARGET_EXECUTABLE" "$TARGET_SOCKET"
    else
        exit $?
    fi
else
    exit $?
fi
'''
                result = self.run_sourced(body, env={"FAKE_SOCKET": str(socket)})
                self.assertEqual(result.returncode, 0, result.stderr + log_path.read_text(encoding="utf-8"))
                line = next(line for line in result.stdout.splitlines() if line.startswith("replacement="))
                replacement_parent = int(line.split(" parent=", 1)[1])
                self.assertNotEqual(replacement_parent, initial.pid)
                self.assertIn("Verified replacement listener", result.stdout)
                deadline = time.monotonic() + 5
                while socket.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertFalse(socket.exists())
            finally:
                for process_group in (initial.pid if initial is not None else None, replacement_parent):
                    if process_group is None:
                        continue
                    try:
                        os.killpg(process_group, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                if initial is not None:
                    initial.wait(timeout=5)

    def test_replacement_match_preserves_captured_environment_except_trace_values(self):
        old = {
            "listener": {"pid": 123, "parent_pid": 122, "socket": "/tmp/app-server-control.sock"},
            "launch": {
                "socket": "/tmp/app-server-control.sock",
                "log_path": "/tmp/app-server.log",
                "parent": {
                    "pid": 122,
                    "start_ticks": 10,
                    "executable": "/usr/bin/node",
                    "argv": ["node", "/opt/codex", "app-server", "--listen", "unix://"],
                    "cwd": "/tmp",
                    "environment": {"KEEP": "unchanged", "RUST_LOG": "old", "LOG_FORMAT": "text"},
                    "stdin": "/dev/null",
                    "stdout": "/tmp/app-server.log",
                    "stderr": "/tmp/app-server.log",
                    "log_identity": {"device": 1, "inode": 2},
                },
            },
        }
        current = json.loads(json.dumps(old))
        current["listener"]["pid"] = 789
        current["listener"]["parent_pid"] = 456
        current["launch"]["parent"]["pid"] = 456
        current["launch"]["parent"]["start_ticks"] = 20
        current["launch"]["parent"]["environment"].update(
            {
                "RUST_LOG": "off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info",
                "LOG_FORMAT": "json",
            }
        )
        body = 'if replacement_matches_launch "$OLD_RECORD" "$CURRENT_RECORD" 456 20; then exit 0; else status=$?; printf "%s\\n" "$MATCH_ERROR" >&2; exit "$status"; fi'
        passing = self.run_sourced(
            body,
            env={"OLD_RECORD": self.encoded_record(old), "CURRENT_RECORD": self.encoded_record(current)},
        )
        self.assertEqual(passing.returncode, 0, passing.stderr)

        current["launch"]["parent"]["environment"]["KEEP"] = "changed"
        rejected = self.run_sourced(
            body,
            env={"OLD_RECORD": self.encoded_record(old), "CURRENT_RECORD": self.encoded_record(current)},
        )
        self.assertEqual(rejected.returncode, 1, rejected.stderr)
        self.assertIn("environment differs", rejected.stderr)

    def test_restart_confirmation_accepts_only_exact_yes(self):
        accepted_code, accepted_output = self.run_confirmation_in_pty(b"yes\n")
        rejected_code, rejected_output = self.run_confirmation_in_pty(b"YES\n")
        self.assertEqual(accepted_code, 0, accepted_output)
        self.assertEqual(rejected_code, 9, rejected_output)
        self.assertIn("Restart declined", rejected_output)


if __name__ == "__main__":
    unittest.main()
