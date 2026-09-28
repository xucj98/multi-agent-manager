from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseFixtureTests(unittest.TestCase):
    def test_create_old_fixture_uses_archived_writer_and_refuses_reuse(self):
        with tempfile.TemporaryDirectory(prefix="mam release fixture ") as temporary:
            instance = Path(temporary) / "mam-test"
            command = [sys.executable, str(ROOT / "scripts" / "create_mam_test.py"), "--version", "0.1.0", "--root", str(instance)]
            created = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True, timeout=30)
            self.assertEqual(created.returncode, 0, created.stderr)
            metadata = json.loads(created.stdout)
            self.assertEqual(metadata["version"], "0.1.0")
            self.assertTrue(Path(metadata["mam"]).is_file())
            fixture = metadata["fixture"]
            self.assertTrue((instance / "multi-agent-manager" / ".tasks" / fixture["task"] / "files" / "fixture.txt").is_file())
            self.assertTrue((instance / "multi-agent-manager" / ".local" / "service" / "state.json").is_file())

            reused = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(reused.returncode, 0)
            self.assertIn("already exists", reused.stderr)

    def test_integration_argument_validation_does_not_allocate_resources(self):
        with tempfile.TemporaryDirectory(prefix="mam release integration ") as temporary:
            root = Path(temporary) / "run"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "test_integration.py"), "--root", str(root), "--from", "0.0.1"],
                cwd=ROOT, check=False, capture_output=True, text=True, timeout=10,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((root / "integration-results" / "result.json").is_file())
            self.assertFalse((root / "mam-test").exists())


if __name__ == "__main__":
    unittest.main()
