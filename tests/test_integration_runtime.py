from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from multi_agent_manager import job_runtime
from scripts.integration_runtime import RuntimeHarness


ROOT = Path(__file__).resolve().parents[1]


class IntegrationRuntimeTests(unittest.TestCase):
    def _create_old_instance(self, root: Path) -> dict:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "create_mam_test.py"), "--version", "0.1.0", "--root", str(root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=40,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertIsInstance(value, dict)
        return value

    @staticmethod
    def _register(launcher: str, instance: Path, metadata: dict, process: subprocess.Popen[bytes], env: dict[str, str]) -> str:
        result = subprocess.run(
            [launcher, "job", "add", metadata["fixture"]["task"], "--note", "controlled runtime job",
             "--host", "local", "--pid", str(process.pid)],
            cwd=instance,
            env={**env, "CODEX_THREAD_ID": metadata["fixture"]["worker"]},
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode:
            raise AssertionError(result.stderr)
        value = json.loads(result.stdout)
        return value["id"]

    def test_real_old_and_new_daemon_lifecycle_and_job_notification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mam-integration-runtime-") as temporary:
            root = Path(temporary) / "mam-test"
            metadata = self._create_old_instance(root)
            harness = RuntimeHarness(root, metadata, Path(temporary) / "runtime.log")
            jobs: list[subprocess.Popen[bytes]] = []
            try:
                for _ in range(2):
                    jobs.append(subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"]))
                running_job = self._register(metadata["mam"], root, metadata, jobs[0], harness.env)
                exiting_job = self._register(metadata["mam"], root, metadata, jobs[1], harness.env)

                old = harness.start(Path(metadata["mam"]))
                self.assertTrue(old["status"]["running"])
                self.assertIsInstance(old["pid"], int)
                self.assertTrue(harness.status(Path(metadata["mam"]))["running"])
                self.assertEqual(harness.wait_for_job_state(running_job, "running")["id"], running_job)
                self.assertEqual(harness.wait_for_job_state(exiting_job, "running")["id"], exiting_job)

                stopped = harness.stop(Path(metadata["mam"]))
                self.assertTrue(stopped["stopped"])
                self.assertFalse(harness.status(Path(metadata["mam"]))["running"])
                jobs[1].terminate()
                jobs[1].wait(timeout=5)

                new_launcher = Path(sys.executable).with_name("mam")
                if not new_launcher.is_file():
                    new_launcher = ROOT / ".venv" / "bin" / "mam"
                self.assertTrue(new_launcher.is_file())
                new = harness.start(new_launcher)
                self.assertTrue(new["status"]["running"])
                self.assertIsInstance(new["pid"], int)
                self.assertNotEqual(old["pid"], new["pid"])
                self.assertTrue(harness.status(new_launcher)["running"])
                self.assertEqual(harness.wait_for_job_state(running_job, "running")["id"], running_job)
                self.assertEqual(harness.wait_for_job_state(exiting_job, "exited", timeout=60)["id"], exiting_job)
                evidence = harness.verify_notification(exiting_job)
                self.assertEqual(evidence["recipient"], metadata["fixture"]["worker"])
                self.assertIn(exiting_job, evidence["message"])
                self.assertTrue(any(item.get("method") == "turn/start" for item in evidence["requests"]))
                self.assertTrue(evidence["event"]["delivery"] == "accepted")
                self.assertTrue(evidence["history"])
            finally:
                for process in jobs:
                    if process.poll() is None:
                        process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                harness.close()

    def test_endpoint_rejects_unknown_threads_and_never_uses_default_socket(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mam-integration-endpoint-") as temporary:
            instance = Path(temporary) / "instance"
            metadata = {"mam_root": str(instance / "multi-agent-manager"), "fixture": {
                "manager": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "worker": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                "task": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            }}
            instance.mkdir()
            (instance / "multi-agent-manager" / ".local" / "service").mkdir(parents=True)
            harness = RuntimeHarness(instance, metadata, Path(temporary) / "endpoint.log")
            try:
                self.assertTrue(Path(harness.env["MAM_APP_SERVER_SOCKET"]).is_socket())
                self.assertNotEqual(harness.env["MAM_APP_SERVER_SOCKET"], "/root/.codex/app-server-control/app-server-control.sock")
                stream = job_runtime.AppServerEventStream.connect(harness.endpoint.path)
                try:
                    with self.assertRaises(job_runtime.AppServerRpcError):
                        stream.read("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
                finally:
                    stream.close()
                self.assertTrue(any(item.get("method") == "thread/read" for item in harness.requests))
                self.assertEqual(harness.endpoint.errors, [])
            finally:
                harness.close()


if __name__ == "__main__":
    unittest.main()
