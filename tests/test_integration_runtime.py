from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from multi_agent_manager import job_runtime
from scripts.integration_runtime import RuntimeHarness, RuntimeIntegrationError, validate_job_notification


ROOT = Path(__file__).resolve().parents[1]


class IntegrationRuntimeTests(unittest.TestCase):
    @staticmethod
    def _delivery(input_type: str = "user", *, recipient: str = "worker-thread", turn_id: str = "turn-current", locator: str = "/root/fixture-worker") -> dict:
        message = f"[MAM MESSAGE]\n\n[job exited | {locator}]\nThere are exited jobs. Check the results and archive them."
        params = {"threadId": recipient}
        if input_type == "tool":
            params.update({"input": [], "toolOutput": {"name": "message", "namespace": "mam", "output": message}})
        else:
            params["input"] = [{"type": "text", "text": message}]
        return {"thread_id": recipient, "method": "turn/start", "message": message, "params": params, "turn_id": turn_id}

    @staticmethod
    def _event(*, recipient: str = "worker-thread", path: str | None = "/root/fixture-worker", turn_id: str = "turn-current") -> dict:
        event = {
            "kind": "job_stopped", "job": "fixture-job-id", "task": "fixture-task-id",
            "executor": recipient, "delivery": "accepted",
            "recipient": recipient, "accepted_turn_id": turn_id,
        }
        if path is not None:
            event["executor_path"] = path
        return event

    def test_notification_matches_fixture_thread_path_input_and_current_turn(self) -> None:
        for input_type in ("user",):
            with self.subTest(input_type=input_type):
                result = validate_job_notification(
                    self._delivery(input_type), self._event(), job_id="fixture-job-id",
                    task_id="fixture-task-id",
                    recipient="worker-thread", executor_path="/root/fixture-worker",
                    expected_input_type=input_type, current_turn_id="turn-current",
                )
                self.assertEqual(result["input_type"], input_type)
                self.assertEqual(result["turn_id"], "turn-current")
                self.assertEqual(result["executor_path"], "/root/fixture-worker")
                self.assertNotIn("fixture-job-id", result["message"])

    def test_notification_rejects_wrong_thread_executor_path_and_old_turn(self) -> None:
        valid_delivery = self._delivery()
        valid_event = self._event()
        invalid_cases = (
            (self._delivery(recipient="other-thread"), valid_event, "wrong fixture thread"),
            (valid_delivery, self._event(path="/root/other-worker"), "fixture executor path"),
            (self._delivery(turn_id="turn-old"), valid_event, "current fixture turn"),
        )
        for delivery, event, message in invalid_cases:
            with self.subTest(message=message), self.assertRaisesRegex(RuntimeIntegrationError, message):
                validate_job_notification(
                    delivery, event, job_id="fixture-job-id", recipient="worker-thread",
                    task_id="fixture-task-id",
                    executor_path="/root/fixture-worker", expected_input_type="user",
                    current_turn_id="turn-current",
                )

    def test_notification_rejects_wrong_input_type_and_job_id_echo(self) -> None:
        with self.assertRaisesRegex(RuntimeIntegrationError, "input type"):
            validate_job_notification(
                self._delivery("tool"), self._event(), job_id="fixture-job-id",
                task_id="fixture-task-id",
                recipient="worker-thread", executor_path="/root/fixture-worker",
                expected_input_type="user", current_turn_id="turn-current",
            )

    def test_later_turn_does_not_erase_completed_accepted_turn(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mam-integration-turn-history-") as temporary:
            instance = Path(temporary) / "instance"
            instance.mkdir()
            metadata = {"mam_root": str(instance / "multi-agent-manager"), "fixture": {
                "manager": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "worker": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                "task": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            }}
            harness = RuntimeHarness(instance, metadata, Path(temporary) / "turns.log")
            stream = job_runtime.AppServerEventStream.connect(harness.endpoint.path)
            try:
                first = stream.start_turn(metadata["fixture"]["worker"], "first controlled turn")
                first_id = first["turn"]["id"]
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    state = harness.endpoint.turn_state(metadata["fixture"]["worker"], first_id)
                    if state and state.get("status") == "completed":
                        break
                    time.sleep(0.01)
                self.assertEqual(state, {"id": first_id, "status": "completed"})
                second = stream.start_turn(metadata["fixture"]["worker"], "later controlled turn")
                second_id = second["turn"]["id"]
                self.assertNotEqual(first_id, second_id)
                self.assertEqual(harness.endpoint.current_turn(metadata["fixture"]["worker"])["id"], second_id)
                self.assertEqual(
                    harness.endpoint.turn_state(metadata["fixture"]["worker"], first_id),
                    {"id": first_id, "status": "completed"},
                )
            finally:
                stream.close()
                harness.close()
        delivery = self._delivery()
        delivery["message"] += " fixture-job-id"
        delivery["params"]["input"][0]["text"] = delivery["message"]
        with self.assertRaisesRegex(RuntimeIntegrationError, "JOB-ID"):
            validate_job_notification(
                delivery, self._event(), job_id="fixture-job-id", recipient="worker-thread",
                task_id="fixture-task-id",
                executor_path="/root/fixture-worker", expected_input_type="user",
                current_turn_id="turn-current",
            )

    def test_legacy_task_without_identity_uses_exact_task_locator_fallback(self) -> None:
        delivery = self._delivery(locator="task: fixture-task-id")
        result = validate_job_notification(
            delivery, self._event(path=None),
            job_id="fixture-job-id", task_id="fixture-task-id", recipient="worker-thread",
            executor_path=None, allow_task_fallback=True, expected_input_type="user",
            current_turn_id="turn-current",
        )
        self.assertIsNone(result["executor_path"])
        self.assertEqual(result["executor_locator"], "task: fixture-task-id")

        duplicate = self._delivery(locator="task: fixture-task-id")
        duplicate["message"] += "\n\n" + duplicate["message"].split("\n\n", 1)[1]
        duplicate["params"]["input"][0]["text"] = duplicate["message"]
        with self.assertRaisesRegex(RuntimeIntegrationError, "does not match"):
            validate_job_notification(
                duplicate, self._event(path=None),
                job_id="fixture-job-id", task_id="fixture-task-id", recipient="worker-thread",
                executor_path=None, allow_task_fallback=True, expected_input_type="user",
                current_turn_id="turn-current",
            )

        with self.assertRaisesRegex(RuntimeIntegrationError, "no fixture executor path"):
            validate_job_notification(
                self._delivery(locator="task: fixture-task-id"), self._event(path=None),
                job_id="fixture-job-id", task_id="fixture-task-id", recipient="worker-thread",
                executor_path=None, expected_input_type="user", current_turn_id="turn-current",
            )

        with self.assertRaisesRegex(RuntimeIntegrationError, "path does not match"):
            validate_job_notification(
                self._delivery(locator="task: fixture-task-id"), self._event(),
                job_id="fixture-job-id", task_id="fixture-task-id", recipient="worker-thread",
                executor_path=None, allow_task_fallback=True, expected_input_type="user",
                current_turn_id="turn-current",
            )

    def test_missing_identity_is_only_allowed_for_archived_010_fixture(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mam-integration-missing-identity-") as temporary:
            instance = Path(temporary) / "instance"
            task_dir = instance / "multi-agent-manager" / ".local" / "tasks"
            task_dir.mkdir(parents=True)
            worker = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
            manager = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
            task_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
            (task_dir / f"{task_id}.json").write_text(
                json.dumps({"id": task_id, "agent": worker}), encoding="utf-8"
            )
            metadata = {"version": "0.2.1", "mam_root": str(task_dir.parents[1]), "fixture": {
                "manager": manager, "worker": worker, "task": task_id,
            }}
            harness = RuntimeHarness(instance, metadata, Path(temporary) / "missing-identity.log")
            try:
                with self.assertRaisesRegex(RuntimeIntegrationError, "unique native executor path"):
                    harness._fixture_executor_path()
            finally:
                harness.close()

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
                if not new_launcher.is_file():
                    # A source archive has no checkout venv.  Point a temporary
                    # launcher at the archived package so this test still
                    # exercises a real new daemon process.
                    new_launcher = Path(temporary) / "candidate-mam"
                    new_launcher.write_text(
                        f"#!{sys.executable}\n"
                        f"import sys\nsys.path.insert(0, {str(ROOT)!r})\n"
                        "from multi_agent_manager.cli import main\n"
                        "raise SystemExit(main())\n",
                        encoding="utf-8",
                    )
                    new_launcher.chmod(0o755)
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
                self.assertEqual(evidence["input_type"], "user")
                self.assertEqual(evidence["event"]["accepted_turn_id"], evidence["turn_id"])
                self.assertIsNone(evidence["executor_path"])
                self.assertEqual(evidence["executor_locator"], f"task: {metadata['fixture']['task']}")
                self.assertNotIn(exiting_job, evidence["message"])
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

    def test_close_does_not_mask_a_live_owned_pid_and_can_retry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mam-integration-cleanup-") as temporary:
            instance = Path(temporary) / "instance"
            instance.mkdir()
            metadata = {"mam_root": str(instance / "multi-agent-manager"), "fixture": {
                "manager": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "worker": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                "task": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            }}
            harness = RuntimeHarness(instance, metadata, Path(temporary) / "cleanup.log")
            identity = {"host": "local", "boot_id": "fixture", "start_ticks": 123}
            harness._owned[123] = {"launcher": "/tmp/owned-mam", "identity": identity}
            try:
                with mock.patch.object(harness, "_service_state", return_value={"pid": 123, "identity": identity}), \
                     mock.patch.object(harness, "_run", return_value={"status": "disabled"}), \
                     mock.patch.object(harness, "_force_stop", return_value=False):
                    with self.assertRaises(RuntimeIntegrationError):
                        harness.close()
                self.assertFalse(harness._closed)
                self.assertFalse(harness.last_cleanup["ok"])
                self.assertFalse(harness.last_cleanup["daemons"][0]["stopped"])

                with mock.patch.object(harness, "_service_state", return_value={"pid": 123, "identity": identity}), \
                     mock.patch.object(harness, "_run", return_value={"status": "disabled"}), \
                     mock.patch.object(harness, "_force_stop", return_value=True):
                    retry = harness.close()
                self.assertTrue(retry["ok"])
                self.assertTrue(retry["daemons"][0]["stopped"])
                self.assertTrue(harness._closed)
                self.assertTrue(harness.close()["ok"])
            finally:
                if not harness._closed:
                    with mock.patch.object(harness, "_force_stop", return_value=True):
                        harness.close()


if __name__ == "__main__":
    unittest.main()
