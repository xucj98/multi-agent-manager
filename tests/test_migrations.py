from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from multi_agent_manager import migrations, task_state


class MigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".local" / "tasks").mkdir(parents=True)
        (self.root / ".local" / "service").mkdir()
        self.record = self.root / ".local" / "tasks" / "task.json"
        self.record.write_text('{"id":"kept","jobs":[{"status":"stopped"}]}\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_old_records_are_detected_and_migrated_without_rewriting_them(self):
        self.assertEqual(migrations.read_data_version(self.root), "0.1.0")
        result = migrations.migrate_data(self.root)
        self.assertEqual(result["from"], "0.1.0")
        self.assertEqual(result["to"], "0.2.3")
        self.assertEqual(result["steps"], [
            {"from": "0.1.0", "to": "0.2.0"},
            {"from": "0.2.0", "to": "0.2.1"},
            {"from": "0.2.1", "to": "0.2.2"},
            {"from": "0.2.2", "to": "0.2.3"},
        ])
        self.assertEqual(migrations.read_data_version(self.root), "0.2.3")
        old_task = json.loads(self.record.read_text())
        self.assertEqual(old_task, {"id": "kept", "jobs": [{"status": "stopped"}]})
        self.assertEqual(task_state.reminder_count(old_task), 0)
        self.assertEqual(migrations.migrate_data(self.root)["steps"], [])

    def test_failed_step_does_not_record_destination_and_retry_continues(self):
        original = migrations.MIGRATIONS[("0.1.0", "0.2.0")]
        calls = []

        def fail_once(root: Path) -> None:
            calls.append(root)
            if len(calls) == 1:
                raise migrations.MigrationError("fixture interruption")
            original(root)

        with mock.patch.dict(migrations.MIGRATIONS, {("0.1.0", "0.2.0"): fail_once}):
            with self.assertRaisesRegex(migrations.MigrationError, "interruption"):
                migrations.migrate_data(self.root)
            self.assertFalse((self.root / ".local" / migrations.VERSION_FILE).exists())
            result = migrations.migrate_data(self.root)
        self.assertTrue(result["changed"])
        self.assertEqual(migrations.read_data_version(self.root), "0.2.3")

    def test_020_to_021_is_an_explicit_noop_receipt(self):
        version_file = self.root / ".local" / migrations.VERSION_FILE
        version_file.write_text('{"version":"0.2.0","history":[]}\n', encoding="utf-8")
        before = self.record.read_bytes()
        result = migrations.migrate_data(self.root, "0.2.1")
        self.assertEqual(result["steps"], [{"from": "0.2.0", "to": "0.2.1"}])
        self.assertEqual(migrations.read_data_version(self.root), "0.2.1")
        self.assertEqual(self.record.read_bytes(), before)

    def test_021_to_022_is_an_explicit_noop_receipt(self):
        migrations.write_data_version(self.root, "0.2.1")
        before = self.record.read_bytes()
        result = migrations.migrate_data(self.root, "0.2.2")
        self.assertEqual(result["from"], "0.2.1")
        self.assertEqual(result["steps"], [{"from": "0.2.1", "to": "0.2.2"}])
        self.assertEqual(migrations.read_data_version(self.root), "0.2.2")
        self.assertEqual(self.record.read_bytes(), before)
        self.assertEqual(migrations.migrate_data(self.root, "0.2.2")["steps"], [])

    def test_interrupted_latest_step_keeps_021_receipt_and_retries_only_that_step(self):
        original = migrations.MIGRATIONS[("0.2.2", "0.2.3")]
        with mock.patch.dict(migrations.MIGRATIONS, {
            ("0.2.2", "0.2.3"): mock.Mock(side_effect=migrations.MigrationError("latest step interruption"))
        }):
            with self.assertRaisesRegex(migrations.MigrationError, "interruption"):
                migrations.migrate_data(self.root)
        self.assertEqual(migrations.read_data_version(self.root), "0.2.2")
        with mock.patch.dict(migrations.MIGRATIONS, {
            ("0.2.2", "0.2.3"): mock.Mock(wraps=original)
        }):
            result = migrations.migrate_data(self.root)
        self.assertEqual(result["steps"], [{"from": "0.2.2", "to": "0.2.3"}])
        self.assertEqual(migrations.read_data_version(self.root), "0.2.3")

    def test_backup_copies_only_local_and_never_overwrites_existing_backup(self):
        (self.root / "outside.txt").write_text("outside", encoding="utf-8")
        destination = self.root / "backup"
        result = migrations.backup_local(self.root, destination)
        self.assertEqual(result, destination)
        self.assertEqual((destination / "tasks" / "task.json").read_text(), self.record.read_text())
        self.assertFalse((destination / "outside.txt").exists())
        with self.assertRaisesRegex(migrations.MigrationError, "already exists"):
            migrations.backup_local(self.root, destination)


if __name__ == "__main__":
    unittest.main()
