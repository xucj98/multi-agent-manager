from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class ReleaseFixtureTests(unittest.TestCase):
    def test_installer_uses_private_endpoint_only_when_controlled_mode_is_explicit(self):
        from scripts import test_integration

        runtime = mock.Mock()
        runtime.env = {"MAM_INTEGRATION_RUNTIME": "controlled", "MAM_APP_SERVER_SOCKET": "/tmp/fixture.sock"}
        instances = [(Path("/tmp/fixture"), {"fixture": {"worker": "fixture-worker"}})]
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(test_integration.installer_runtime_environment([runtime], instances))
        with mock.patch.dict(os.environ, {"MAM_INTEGRATION_RUNTIME": "controlled"}, clear=True):
            self.assertEqual(
                test_integration.installer_runtime_environment([runtime], instances),
                {**runtime.env, "CODEX_THREAD_ID": "fixture-worker"},
            )

    def test_controlled_archive_install_isolated_from_default_socket_and_not_real_delivery(self):
        from scripts import test_integration

        with tempfile.TemporaryDirectory(prefix="mam controlled archive ") as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "scripts").mkdir(parents=True)
            (source / "scripts" / "install.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            archive = root / "candidate.tar.gz"
            with tarfile.open(archive, "w:gz") as package:
                package.add(source, arcname="candidate")

            instance = root / "instance"
            instance.mkdir()
            install_root = root / "isolated-install"
            log = root / "integration.log"
            endpoint = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            socket_path = root / "controlled.sock"
            endpoint.bind(str(socket_path))
            seen = {}

            def fake_pipx_install(_source, env, _log):
                bin_dir = Path(env["PIPX_BIN_DIR"])
                bin_dir.mkdir(parents=True, exist_ok=True)
                launcher = bin_dir / "mam"
                launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                launcher.chmod(0o755)

            def fake_run(argv, *, cwd, env, log):
                seen.update({"socket": env.get("MAM_APP_SERVER_SOCKET"), "thread": env.get("CODEX_THREAD_ID")})
                return subprocess.CompletedProcess(argv, 0, "", "")

            try:
                with mock.patch.object(test_integration, "pipx_install", side_effect=fake_pipx_install), \
                     mock.patch.object(test_integration, "run", side_effect=fake_run):
                    launcher, delivery = test_integration.install_candidate(
                        [(instance, {"fixture": {"worker": "fixture-worker"}})],
                        archive, install_root, log,
                        runtime_env={
                            "MAM_INTEGRATION_RUNTIME": "controlled",
                            "MAM_APP_SERVER_SOCKET": str(socket_path),
                            "CODEX_THREAD_ID": "fixture-worker",
                        },
                    )
            finally:
                endpoint.close()

            self.assertTrue(launcher.is_file())
            self.assertEqual(seen, {"socket": str(socket_path), "thread": "fixture-worker"})
            self.assertEqual(delivery["status"], "failed")
            self.assertIn("no real Codex delivery was exercised", delivery["error"])
            self.assertTrue(delivery["controlled_migration_allowed"])

    def test_controlled_install_failure_requires_persisted_live_delivery_evidence(self):
        from scripts import test_integration

        with tempfile.TemporaryDirectory(prefix="mam install evidence ") as temporary:
            home = Path(temporary)
            evidence_root = home / ".local" / "share" / "multi-agent-manager" / "install-evidence"
            evidence_root.mkdir(parents=True)
            failed = evidence_root / "20261001T000000Z-0.2.1.compatibility-failed.json"
            failed.write_text(json.dumps({
                "status": "failed",
                "stages": [{"name": "live_delivery", "status": "failed"}],
            }), encoding="utf-8")
            accepted = test_integration.controlled_compatibility_failure(home, "0.2.1")
            self.assertIsNotNone(accepted)
            failed.write_text(json.dumps({
                "status": "failed",
                "stages": [{"name": "non_model", "status": "failed"}],
            }), encoding="utf-8")
            self.assertIsNone(test_integration.controlled_compatibility_failure(home, "0.2.1"))

    def test_install_evidence_is_copied_before_private_home_cleanup(self):
        from scripts import test_integration

        with tempfile.TemporaryDirectory(prefix="mam retained evidence ") as temporary:
            root = Path(temporary)
            source = root / "install" / "home" / ".local" / "share" / "multi-agent-manager" / "install-evidence"
            source.mkdir(parents=True)
            (source / "20261001T000000Z-0.2.1.compatibility.json").write_text("{}", encoding="utf-8")
            (source / "20261001T000000Z-0.2.1.json").write_text("{}", encoding="utf-8")
            results = root / "results"
            try:
                raise RuntimeError("simulated install failure")
            except RuntimeError:
                retained = test_integration.retain_install_evidence(root / "install", results)
            self.assertEqual(len(retained), 2)
            shutil.rmtree(root / "install")
            self.assertTrue((results / "install-evidence" / "20261001T000000Z-0.2.1.json").is_file())

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
        from scripts import test_integration

        with tempfile.TemporaryDirectory(prefix="mam release integration ") as temporary:
            root = Path(temporary) / "run"
            with mock.patch.object(test_integration, "run_full_unit_suite", side_effect=AssertionError("preflight ran the full suite")):
                code, outcome = test_integration.integration(root, "0.0.1", "0.2.1", False)
            self.assertNotEqual(code, 0)
            self.assertIn("only the complete", outcome["error"])
            self.assertTrue((root / "integration-results" / "result.json").is_file())
            self.assertFalse((root / "mam-test").exists())

    def test_published_missing_tag_does_not_allocate_resources(self):
        from scripts import test_integration

        if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-dir"], check=False, capture_output=True).returncode:
            self.skipTest("published-ref preflight requires the source checkout Git repository")
        with tempfile.TemporaryDirectory(prefix="mam release missing tag ") as temporary:
            root = Path(temporary) / "run"
            with mock.patch.object(test_integration, "run_full_unit_suite", side_effect=AssertionError("preflight ran the full suite")):
                code, outcome = test_integration.integration(root, "0.1.0", "0.2.1", False, published=True)
            self.assertNotEqual(code, 0)
            self.assertFalse((root / "mam-test").exists())
            evidence = json.loads((root / "integration-results" / "result.json").read_text(encoding="utf-8"))
            self.assertIn("published source tag", evidence["error"])
            self.assertIn("published source tag", outcome["error"])

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
            'RELEASE_VERSION = "0.2.1"\nRELEASE_TAG = "v0.2.1"\nRELEASE_COMMIT = "$Format:%H$"\n',
                encoding="utf-8",
            )
            (repository / "pyproject.toml").write_text('[project]\nname = "multi-agent-manager"\nversion = "0.2.1"\n', encoding="utf-8")
            git("add", ".")
            git("commit", "-q", "-m", "release")
            git("tag", "-a", "v0.2.1", "-m", "published")
            tag_object = git("rev-parse", "refs/tags/v0.2.1")
            expected = git("rev-parse", "refs/tags/v0.2.1^{commit}")
            with mock.patch.object(test_integration, "root_dir", return_value=repository):
                archive, selected = test_integration.build_archive(Path(temporary), Path(temporary) / "archive.log", "0.2.1", published=True)
            self.assertNotEqual(tag_object, expected)
            self.assertEqual(selected, expected)
            with tarfile.open(archive, "r:gz") as package_archive:
                member = next(item for item in package_archive.getmembers() if item.name.endswith("multi_agent_manager/release.py"))
                self.assertIn(expected, package_archive.extractfile(member).read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
