from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


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
            status = subprocess.run(
                [metadata["mam"], "service", "status"],
                cwd=instance,
                env={**os.environ, "CODEX_THREAD_ID": fixture["worker"]},
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(json.loads(status.stdout)["status"], "disabled")

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

    def test_published_missing_tag_does_not_allocate_resources(self):
        if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-dir"], check=False, capture_output=True).returncode:
            self.skipTest("published-ref preflight requires the source checkout Git repository")
        with tempfile.TemporaryDirectory(prefix="mam release missing tag ") as temporary:
            root = Path(temporary) / "run"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "test_integration.py"), "--root", str(root), "--to", "0.2.0"],
                cwd=ROOT, check=False, capture_output=True, text=True, timeout=10,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "mam-test").exists())
            evidence = json.loads((root / "integration-results" / "result.json").read_text(encoding="utf-8"))
            self.assertIn("published source tag", evidence["error"])

    def test_build_archive_uses_commit_for_annotated_tag(self):
        from scripts import test_integration

        with tempfile.TemporaryDirectory(prefix="mam release annotated tag ") as temporary:
            repository = Path(temporary) / "repo"
            repository.mkdir()
            def git(*args: str) -> str:
                return subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, text=True).stdout.strip()

            git("init", "-q")
            git("config", "user.name", "integration test")
            git("config", "user.email", "integration@example.invalid")
            (repository / ".gitattributes").write_text("multi_agent_manager/release.py export-subst\n", encoding="utf-8")
            package = repository / "multi_agent_manager"
            package.mkdir()
            (package / "release.py").write_text(
                'RELEASE_VERSION = "0.2.0"\nRELEASE_TAG = "v0.2.0"\nRELEASE_COMMIT = "$Format:%H$"\n',
                encoding="utf-8",
            )
            (repository / "pyproject.toml").write_text('[project]\nname = "multi-agent-manager"\nversion = "0.2.0"\n', encoding="utf-8")
            git("add", ".")
            git("commit", "-q", "-m", "release")
            git("tag", "-a", "v0.2.0", "-m", "published")
            tag_object = git("rev-parse", "refs/tags/v0.2.0")
            expected = git("rev-parse", "refs/tags/v0.2.0^{commit}")
            with mock.patch.object(test_integration, "root_dir", return_value=repository):
                archive, selected = test_integration.build_archive(Path(temporary), Path(temporary) / "archive.log", "0.2.0", published=True)
            self.assertNotEqual(tag_object, expected)
            self.assertEqual(selected, expected)
            with tarfile.open(archive, "r:gz") as package_archive:
                member = next(item for item in package_archive.getmembers() if item.name.endswith("multi_agent_manager/release.py"))
                self.assertIn(expected, package_archive.extractfile(member).read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
