from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from multi_agent_manager import cli, migrations, wake_runtime


class UpgradeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        self.root = self.project / "mam"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "MAM tests")
        (self.root / "code.txt").write_text("old\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "old")
        self.git("branch", "-M", "instance")
        self.old = self.git("rev-parse", "HEAD")
        self.git("checkout", "-qb", "release")
        (self.root / "release.txt").write_text("release\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "release")
        self.target = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "instance")
        self.config = cli.ProjectConfig(self.root, self.project, "instance")
        self.store = cli.Store(self.config)
        self.state = wake_runtime._default_state(self.config)
        wake_runtime._save_state(self.store, self.state)
        (self.root / ".local" / "keep.txt").write_text("kept\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()

    def upgrade(self):
        with mock.patch.object(wake_runtime, "source_commit", return_value=self.target):
            return wake_runtime.service_upgrade(self.config)

    def test_upgrade_merges_into_instance_and_preserves_local_data(self):
        self.state["message_channel"] = "tool"
        wake_runtime._write_json(wake_runtime._service_path(self.store, "state.json"), self.state)
        result = self.upgrade()
        self.assertEqual(result["status"], "upgraded")
        self.assertEqual(result["data_version"], "0.2.3")
        self.assertEqual(result["adaptation"], "docs/upgrades/0.2.3.md")
        self.assertEqual(self.git("branch", "--show-current"), "instance")
        self.assertEqual(self.git("rev-parse", "HEAD"), self.target)
        self.assertEqual((self.root / ".local" / "keep.txt").read_text(), "kept\n")
        self.assertTrue((Path(result["backup"]) / "service" / "state.json").is_file())
        self.assertEqual(json.loads((Path(result["backup"]) / "service" / "state.json").read_text())["message_channel"], "tool")
        self.assertEqual(json.loads(wake_runtime._service_path(self.store, "state.json").read_text())["message_channel"], "user")
        self.assertEqual(result["message_channel"], "user")
        again = self.upgrade()
        self.assertEqual(again["status"], "up-to-date")
        self.assertEqual(again["migrations"]["steps"], [])

    def test_running_daemon_is_rejected_before_backup_or_merge(self):
        self.state["pid"] = 123
        self.state["identity"] = {"host": "local"}
        wake_runtime._save_state(self.store, self.state)
        with mock.patch.object(wake_runtime, "_probe_service_process", return_value=(True, None)):
            with self.assertRaisesRegex(wake_runtime.WakeRuntimeError, "still running"):
                self.upgrade()
        self.assertEqual(self.git("rev-parse", "HEAD"), self.old)
        self.assertEqual(list(self.root.glob(".local.backup-*")), [])

    def test_missing_target_and_origin_fails_before_backup_or_data_write(self):
        missing = "f" * 40
        with mock.patch.object(wake_runtime, "source_commit", return_value=missing):
            with self.assertRaisesRegex(wake_runtime.WakeRuntimeError, "no configured origin"):
                wake_runtime.service_upgrade(self.config)
        self.assertEqual(migrations.read_data_version(self.root), "0.1.0")
        self.assertEqual(list(self.root.glob(".local.backup-*")), [])

    def test_missing_local_target_is_fetched_from_configured_origin(self):
        origin = self.project / "origin.git"
        subprocess.run(["git", "clone", "--bare", str(self.root), str(origin)], check=True, capture_output=True)
        self.git("remote", "add", "origin", str(origin))
        self.git("branch", "-D", "release")
        self.git("reflog", "expire", "--expire=now", "--all")
        self.git("gc", "--prune=now")
        with mock.patch.object(wake_runtime, "source_commit", return_value=self.target):
            result = wake_runtime.service_upgrade(self.config)
        self.assertEqual(result["data_version"], "0.2.3")
        self.assertEqual(self.git("rev-parse", "HEAD"), self.target)

    def test_git_conflict_keeps_baseline_version_and_can_be_resolved_then_retried(self):
        self.git("checkout", "-q", "release")
        (self.root / "code.txt").write_text("release changed\n", encoding="utf-8")
        self.git("add", "code.txt")
        self.git("commit", "-qm", "release changes old file")
        self.target = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "instance")
        (self.root / "code.txt").write_text("instance changed\n", encoding="utf-8")
        self.git("add", "code.txt")
        self.git("commit", "-qm", "instance changes old file")
        with self.assertRaisesRegex(wake_runtime.WakeRuntimeError, "resolve conflicts and retry"):
            self.upgrade()
        self.assertEqual(migrations.read_data_version(self.root), "0.1.0")
        self.assertTrue(list(self.root.glob(".local.backup-*")))
        (self.root / "code.txt").write_text("resolved\n", encoding="utf-8")
        self.git("add", "code.txt")
        self.git("commit", "-qm", "resolve upgrade conflict")
        self.assertEqual(self.upgrade()["data_version"], "0.2.3")

    def test_status_distinguishes_current_program_old_daemon_and_data_version(self):
        result = wake_runtime.service_status(self.config)
        self.assertEqual(result["program_version"], "0.2.3")
        self.assertIsNone(result["daemon_version"])
        self.assertEqual(result["data_version"], "0.1.0")


if __name__ == "__main__":
    unittest.main()
