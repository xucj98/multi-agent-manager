from __future__ import annotations

from contextlib import ExitStack
import io
import os
from pathlib import Path
import pty
import select
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

    def test_noninteractive_restart_refusal_never_calls_kill(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "kill-called"
            body = r'''
discover_app_server() {
    TARGET_PID=123; TARGET_START_TICKS=10; TARGET_EXECUTABLE=/opt/codex
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
    TARGET_SOCKET="$1"; TARGET_RECORD="$TARGET_PID:$TARGET_START_TICKS:$TARGET_EXECUTABLE:$TARGET_SOCKET"
}
confirm_restart() { return 0; }
send_term() { : > "$KILL_MARKER"; }
if restart_app_server /tmp/control.sock; then exit 0; else exit 7; fi
'''
            result = self.run_sourced(body, env={"KILL_MARKER": str(marker)})
            self.assertEqual(result.returncode, 7)
            self.assertFalse(marker.exists())
            self.assertIn("target changed before restart", result.stderr)

    def test_restart_confirmation_accepts_only_exact_yes(self):
        accepted_code, accepted_output = self.run_confirmation_in_pty(b"yes\n")
        rejected_code, rejected_output = self.run_confirmation_in_pty(b"YES\n")
        self.assertEqual(accepted_code, 0, accepted_output)
        self.assertEqual(rejected_code, 9, rejected_output)
        self.assertIn("Restart declined", rejected_output)


if __name__ == "__main__":
    unittest.main()
