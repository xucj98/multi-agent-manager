from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from multi_agent_manager import liveprobe


TASK_IDS = {
    "job": "10000000-0000-4000-8000-000000000001",
    "idle": "10000000-0000-4000-8000-000000000002",
    "archived": "10000000-0000-4000-8000-000000000003",
}
THREAD_IDS = {
    "manager": "20000000-0000-4000-8000-000000000001",
    "job_executor": "20000000-0000-4000-8000-000000000002",
    "idle_executor": "20000000-0000-4000-8000-000000000003",
    "archived_executor": "20000000-0000-4000-8000-000000000004",
}
JOB_ID = "30000000-0000-4000-8000-000000000001"
ARCHIVED_JOB_ID = "30000000-0000-4000-8000-000000000002"
SOCKET = "/tmp/mam-liveprobe-test.sock"


class FakeStdin:
    def __init__(self, state):
        self.state = state
        self.closed = False

    def close(self):
        self.closed = True
        self.state["released"] = True


class FakeProcess:
    def __init__(self, state, pid):
        self.state = state
        self.pid = pid
        self.stdin = FakeStdin(state)

    def poll(self):
        return 0 if self.stdin.closed else None

    def terminate(self):
        self.stdin.close()

    def kill(self):
        self.stdin.close()

    def wait(self, timeout=None):
        self.stdin.close()
        return 0


class FakeRuntime:
    def __init__(self, state):
        self.state = state

    def start_service(self, config, manager=None):
        self.state["operations"].append(("service-start", manager))
        self.state["runtime_config"] = config
        self.state["manager"] = manager
        self.state["running"] = True
        return {
            "running": True,
            "healthy": True,
            "manager": manager,
            "pending": {"count": 0, "events": []},
            "status": "healthy",
        }

    def service_status(self, config):
        self.state["operations"].append(("service-status", self.state.get("running")))
        return {
            "running": bool(self.state.get("running")),
            "healthy": bool(self.state.get("running")),
            "manager": self.state.get("manager"),
            "pending": {"count": 0, "events": []},
            "status": "healthy" if self.state.get("running") else "disabled",
        }

    def stop_service(self, config):
        self.state["operations"].append(("service-stop", self.state.get("manager")))
        self.state["running"] = False
        return {"running": False, "healthy": False, "manager": self.state.get("manager"), "pending": {"count": 0, "events": []}}


class FakeStream:
    def __init__(self, state):
        self.state = state
        self.closed = False
        self.turns = {thread_id: [] for thread_id in THREAD_IDS.values()}
        self.thread_starts = 0
        self.manager_delivery_added = False
        self.job_delivery_added = False
        self.history_not_ready = set()

    def _add_manager_delivery_after_baseline(self):
        if self.manager_delivery_added or not self.turns[THREAD_IDS["job_executor"]]:
            return
        self.manager_delivery_added = True
        self.turns[THREAD_IDS["manager"]].append(
            {
                "id": "turn-manager-delivery",
                "status": "completed",
                "input": {
                    "text": (
                        f"Executor AGENT-ID {THREAD_IDS['idle_executor']} has no unarchived jobs for "
                        f"TASK-ID {TASK_IDS['idle']}: MAM liveprobe no-job Manager delivery.\n"
                        f"Executor AGENT-ID {THREAD_IDS['archived_executor']} has no unarchived jobs for "
                        f"TASK-ID {TASK_IDS['archived']}: MAM liveprobe archived-job Manager delivery."
                    )
                },
            }
        )

    def _add_job_delivery_if_released(self):
        if not self.state.get("released") or self.job_delivery_added:
            return
        self.job_delivery_added = True
        self.turns[THREAD_IDS["job_executor"]].append(
            {
                "id": "turn-job-delivery",
                "status": "completed",
                "input": {
                    "text": (
                        f"Stopped registered job: JOB-ID {JOB_ID} (liveprobe-short-job-stop); "
                        f"TASK-ID {TASK_IDS['job']}: MAM liveprobe stopped-job delivery."
                    )
                },
            }
        )

    def request(self, method, params):
        self.state["requests"].append((method, dict(params)))
        if method == "thread/start":
            if self.state["tasks_created"] != ["job", "idle", "archived"]:
                raise AssertionError("fixture threads were created before all tasks were registered")
            if params.get("ephemeral") is not False:
                raise AssertionError("fixture threads must be persisted")
            if params.get("model") != liveprobe.MODEL or params.get("effort") != liveprobe.EFFORT:
                raise AssertionError("fixture thread did not select gpt-5.6-terra/max")
            role = ("manager", "job_executor", "idle_executor", "archived_executor")[self.thread_starts]
            self.thread_starts += 1
            return {"thread": {"id": THREAD_IDS[role], "status": {"type": "idle"}}}
        thread_id = params.get("threadId")
        if method == "thread/read":
            return {"thread": {"id": thread_id, "status": {"type": "idle"}}}
        if method == "thread/resume":
            return {"thread": {"id": thread_id, "status": {"type": "idle"}}}
        if method == "thread/turns/list":
            if thread_id in self.history_not_ready:
                self.history_not_ready.remove(thread_id)
                raise RuntimeError("list_turns is not supported yet")
            if thread_id in {THREAD_IDS["idle_executor"], THREAD_IDS["archived_executor"]}:
                raise RuntimeError(f"thread {thread_id} is not materialized yet")
            if thread_id == THREAD_IDS["manager"]:
                self._add_manager_delivery_after_baseline()
            if thread_id == THREAD_IDS["job_executor"]:
                self._add_job_delivery_if_released()
            return {"data": list(reversed(self.turns[thread_id]))}
        if method == "turn/start":
            if thread_id != THREAD_IDS["job_executor"]:
                raise AssertionError("only the baseline executor turn is direct")
            if params.get("model") != liveprobe.MODEL or params.get("effort") != liveprobe.EFFORT:
                raise AssertionError("baseline turn did not select gpt-5.6-terra/max")
            self.turns[thread_id].append(
                {
                    "id": "turn-executor-baseline",
                    "status": "completed",
                    "input": {"text": "Reply exactly PROBE_EXECUTOR_READY."},
                    "output": {"text": "PROBE_EXECUTOR_READY"},
                }
            )
            return {"turn": {"id": "turn-executor-baseline"}}
        if method == "thread/archive" and thread_id in {THREAD_IDS["idle_executor"], THREAD_IDS["archived_executor"]}:
            raise RuntimeError(f"no rollout found for thread id {thread_id}")
        if method in {"thread/archive", "turn/interrupt"}:
            return {}
        raise AssertionError(f"unexpected App Server request: {method}")

    def close(self):
        self.closed = True
        self.state["operations"].append(("stream-close", None))


class LiveProbeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.state = {
            "tasks_created": [],
            "requests": [],
            "operations": [],
            "released": False,
            "running": False,
            "job_adds": [],
            "job_archives": [],
            "task_archives": [],
            "binds": [],
        }
        self.runtime = FakeRuntime(self.state)
        self.stream = FakeStream(self.state)
        self.task_roles = iter(("job", "idle", "archived"))
        self.job_roles = iter((JOB_ID, ARCHIVED_JOB_ID))

    def tearDown(self):
        self.temporary.cleanup()

    def _create(self, _store, _args):
        role = next(self.task_roles)
        self.state["tasks_created"].append(role)
        return {"id": TASK_IDS[role]}

    def _bind(self, _store, args):
        self.state["binds"].append((args.task, args.agent))
        return {"task": args.task, "agent": args.agent}

    def _job_add(self, _store, args):
        job_id = next(self.job_roles)
        self.state["job_adds"].append((args.task, args.pid, args.note, job_id))
        return {"id": job_id}

    def _job_archive(self, _store, args):
        self.state["job_archives"].append((args.job, args.note))
        return {"id": args.job}

    def _archive(self, _store, args):
        self.state["task_archives"].append((args.task, args.note))
        return {"task": args.task}

    def _process_factory(self, *_args, **_kwargs):
        return FakeProcess(self.state, 4000 + len(self.state["job_adds"]))

    def test_fixture_uses_real_contract_shape_and_cleans_its_own_resources(self):
        root = self.base / "fixture"
        evidence_path = self.base / "evidence.json"
        with mock.patch.object(liveprobe.cli, "create", side_effect=self._create), mock.patch.object(
            liveprobe.cli, "bind", side_effect=self._bind
        ), mock.patch.object(liveprobe.cli, "job_add", side_effect=self._job_add), mock.patch.object(
            liveprobe.cli, "job_archive", side_effect=self._job_archive
        ), mock.patch.object(liveprobe.cli, "archive", side_effect=self._archive):
            result = liveprobe.run_live_delivery(
                {"socket_path": SOCKET, "capabilities": {"model_requests": 0}, "diagnostics": {}},
                root,
                evidence_path=evidence_path,
                runtime_module=self.runtime,
                stream_factory=lambda _socket: self.stream,
                process_factory=self._process_factory,
                timeout_seconds=2,
                sleeper=lambda _seconds: None,
            )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["model_turns"], 3)
        self.assertEqual(result["cleanup"]["threads"], "archived_or_not_materialized")
        self.assertEqual(
            result["checks"],
            {
                "fixture_tasks_registered_before_threads": True,
                "executor_bound_before_first_model_turn": True,
                "job_delivery": True,
                "manager_delivery": True,
                "manager_is_fixture_only": True,
                "turn_budget": True,
                "quiet_window_no_duplicate_starts": True,
                "idle_executors_received_no_turn": True,
            },
        )
        self.assertFalse(root.exists())
        self.assertEqual(json.loads(evidence_path.read_text())["status"], "passed")
        self.assertEqual(self.state["tasks_created"], ["job", "idle", "archived"])
        self.assertEqual(
            self.state["binds"],
            [
                (TASK_IDS["job"], THREAD_IDS["job_executor"]),
                (TASK_IDS["idle"], THREAD_IDS["idle_executor"]),
                (TASK_IDS["archived"], THREAD_IDS["archived_executor"]),
            ],
        )
        self.assertEqual(self.state["job_adds"][0][0], TASK_IDS["job"])
        self.assertEqual(self.state["job_adds"][0][2], "liveprobe-short-job-stop")
        self.assertTrue(self.state["released"])
        self.assertEqual(self.state["runtime_config"].mam_root, self.base / "fixture" / "mam-state")
        self.assertEqual(self.state["manager"], THREAD_IDS["manager"])
        self.assertEqual(self.state["job_archives"], [(ARCHIVED_JOB_ID, "liveprobe fixture archived before delivery"), (JOB_ID, "liveprobe fixture cleanup")])
        self.assertEqual([task for task, _ in self.state["task_archives"]], list(TASK_IDS.values()))
        methods = [method for method, _ in self.state["requests"]]
        self.assertEqual(methods.count("thread/start"), 4)
        self.assertEqual(methods.count("turn/start"), 1)
        direct = next(params for method, params in self.state["requests"] if method == "turn/start")
        self.assertEqual(direct["threadId"], THREAD_IDS["job_executor"])
        self.assertEqual(direct["model"], liveprobe.MODEL)
        self.assertEqual(direct["effort"], liveprobe.EFFORT)
        self.assertIn(("service-start", THREAD_IDS["manager"]), self.state["operations"])
        self.assertIn(("service-stop", THREAD_IDS["manager"]), self.state["operations"])
        self.assertTrue(self.stream.closed)
        self.assertEqual(result["resources"]["threads"], THREAD_IDS)
        self.assertEqual(result["resources"]["jobs"], {"stopped": JOB_ID, "archived_before_delivery": ARCHIVED_JOB_ID})
        self.assertEqual(
            result["resources"]["turns"],
            {
                "executor_baseline_started": "turn-executor-baseline",
                "executor_baseline_completed": "turn-executor-baseline",
                "stopped_job_delivery": "turn-job-delivery",
                "manager_ready_delivery": "turn-manager-delivery",
            },
        )
        self.assertEqual(
            result["cleanup"]["thread_archive"],
            {
                "archived_executor": "not_materialized_no_rollout",
                "idle_executor": "not_materialized_no_rollout",
                "job_executor": "archived",
                "manager": "archived",
            },
        )

    def test_failure_writes_bounded_evidence_and_removes_marker_owned_root(self):
        root = self.base / "fixture-failure"
        evidence_path = self.base / "failure-evidence.json"
        with mock.patch.object(liveprobe.cli, "create", side_effect=RuntimeError("TOKEN=do-not-log")):
            with self.assertRaisesRegex(liveprobe.LiveProbeError, "cannot register fixture"):
                liveprobe.run_live_delivery(
                    {"socket_path": SOCKET},
                    root,
                    evidence_path=evidence_path,
                    runtime_module=self.runtime,
                    stream_factory=lambda _socket: self.stream,
                    process_factory=self._process_factory,
                )
        self.assertFalse(root.exists())
        evidence = json.loads(evidence_path.read_text())
        self.assertEqual(evidence["status"], "failed")
        self.assertNotIn("do-not-log", json.dumps(evidence))

    def test_history_materialization_delay_waits_without_a_second_direct_model_turn(self):
        root = self.base / "fixture-history-delay"
        self.stream.history_not_ready.add(THREAD_IDS["job_executor"])
        with mock.patch.object(liveprobe.cli, "create", side_effect=self._create), mock.patch.object(
            liveprobe.cli, "bind", side_effect=self._bind
        ), mock.patch.object(liveprobe.cli, "job_add", side_effect=self._job_add), mock.patch.object(
            liveprobe.cli, "job_archive", side_effect=self._job_archive
        ), mock.patch.object(liveprobe.cli, "archive", side_effect=self._archive):
            result = liveprobe.run_live_delivery(
                {"socket_path": SOCKET},
                root,
                runtime_module=self.runtime,
                stream_factory=lambda _socket: self.stream,
                process_factory=self._process_factory,
                timeout_seconds=2,
                sleeper=lambda _seconds: None,
            )
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["calls"]["direct_turn_start"], 1)

    def test_nonempty_or_symlink_fixture_root_is_refused_before_any_resource_creation(self):
        root = self.base / "not-empty"
        root.mkdir()
        (root / "user-file").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(liveprobe.LiveProbeError, "new empty regular directory"):
            liveprobe.run_live_delivery({"socket_path": SOCKET}, root, runtime_module=self.runtime)
        self.assertTrue((root / "user-file").exists())

    def test_cli_failure_is_nonzero_without_contacting_real_app_server(self):
        stream = io.StringIO()
        with mock.patch.object(liveprobe, "run_live_delivery", side_effect=liveprobe.LiveProbeError("fixture unavailable")), mock.patch(
            "sys.stdout", stream
        ):
            self.assertEqual(liveprobe._main(["--compatibility", "/missing", "--root", "/tmp/root", "--evidence", "/tmp/evidence"]), 1)
        self.assertIn("MAM isolated live delivery: FAIL", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
