from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
