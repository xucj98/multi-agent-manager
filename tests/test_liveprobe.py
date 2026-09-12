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
    def __init__(self, state, pid):
        self.state = state
        self.pid = pid
        self.closed = False

    def close(self):
        self.closed = True
        self.state["released_processes"].add(self.pid)


class FakeProcess:
    def __init__(self, state, pid):
        self.state = state
        self.pid = pid
        self.stdin = FakeStdin(state, pid)

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
        self.state["timeline"].append(("service-start", manager))
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
        self.state["timeline"].append(("service-stop", self.state.get("manager")))
        self.state["running"] = False
        return {
            "running": False,
            "healthy": False,
            "manager": self.state.get("manager"),
            "pending": {"count": 0, "events": []},
        }


class FakeStream:
    def __init__(self, state):
        self.state = state
        self.closed = False
        self.turns = {thread_id: [] for thread_id in THREAD_IDS.values()}
        self.thread_starts = 0
        self.direct_baseline_starts = 0
        self.manager_delivery_added = False
        self.job_delivery_added = False
        self.history_unsupported: set[str] = set()
        self.active_reads_remaining: dict[str, int] = {}
        self.active_after_turn_start: dict[str, int] = {}
        self.completion_polls_remaining: dict[str, int] = {}
        self.subscribed_threads: set[str] = set()
        self.completed_turn_ids: set[str] = set()
        self.events: list[dict] = []

    def _all_roles_have_baseline(self):
        return all(f"turn-{role}-baseline" in self.completed_turn_ids for role in liveprobe._ROLE_ORDER)

    def _append_turn(self, thread_id, turn_id, text):
        self.turns[thread_id].append({"id": turn_id, "status": "inProgress", "input": {"text": text}})
        self.events.append({"method": "turn/completed", "params": {"threadId": thread_id, "turn": {"id": turn_id}}})

    def _complete_turn(self, thread_id, turn_id):
        for turn in self.turns[thread_id]:
            if turn["id"] == turn_id:
                turn["status"] = "completed"
                self.completed_turn_ids.add(turn_id)
                return
        raise AssertionError(f"completion event referenced unknown turn {turn_id}")

    def _add_manager_delivery_after_baselines(self):
        if self.manager_delivery_added or not self.state.get("running") or not self._all_roles_have_baseline():
            return
        self.manager_delivery_added = True
        self._append_turn(
            THREAD_IDS["manager"],
            "turn-manager-delivery",
            (
                f"Executor AGENT-ID {THREAD_IDS['idle_executor']} has no unarchived jobs for "
                f"TASK-ID {TASK_IDS['idle']}: MAM liveprobe no-job Manager delivery.\n"
                f"Executor AGENT-ID {THREAD_IDS['archived_executor']} has no unarchived jobs for "
                f"TASK-ID {TASK_IDS['archived']}: MAM liveprobe archived-job Manager delivery."
            ),
        )

    def _add_job_delivery_if_released(self):
        if self.job_delivery_added or self.state.get("stopped_pid") not in self.state["released_processes"]:
            return
        self.job_delivery_added = True
        self._append_turn(
            THREAD_IDS["job_executor"],
            "turn-job-delivery",
            (
                f"Stopped registered job: JOB-ID {JOB_ID} (liveprobe-short-job-stop); "
                f"TASK-ID {TASK_IDS['job']}: MAM liveprobe stopped-job delivery."
            ),
        )

    def _maybe_schedule_deliveries(self):
        self._add_manager_delivery_after_baselines()
        self._add_job_delivery_if_released()

    def _thread_snapshot(self, thread_id, *, include_turns):
        remaining = self.active_reads_remaining.get(thread_id, 0)
        if remaining:
            self.active_reads_remaining[thread_id] = remaining - 1
            self.state["metadata_statuses"].append((thread_id, "active"))
            return {"thread": {"id": thread_id, "status": {"type": "active"}}}
        self.state["metadata_statuses"].append((thread_id, "idle"))
        thread = {"id": thread_id, "status": {"type": "idle"}}
        if include_turns:
            thread["turns"] = list(reversed(self.turns[thread_id]))
        return {"thread": thread}

    def request(self, method, params):
        params = dict(params)
        self.state["requests"].append((method, params))
        self.state["timeline"].append((method, params.get("threadId")))
        if method == "thread/start":
            if self.state["tasks_created"] != ["job", "idle", "archived"]:
                raise AssertionError("fixture threads were created before all tasks were registered")
            if params.get("ephemeral") is not False:
                raise AssertionError("fixture threads must be persisted")
            if params.get("model") != liveprobe.MODEL or params.get("effort") != liveprobe.EFFORT:
                raise AssertionError("fixture thread did not select gpt-5.6-terra/max")
            role = liveprobe._ROLE_ORDER[self.thread_starts]
            self.thread_starts += 1
            return {"thread": {"id": THREAD_IDS[role], "status": {"type": "idle"}}}

        thread_id = params.get("threadId")
        if method == "thread/read":
            return self._thread_snapshot(thread_id, include_turns=params.get("includeTurns") is True)
        if method == "thread/resume":
            self.subscribed_threads.add(thread_id)
            return self._thread_snapshot(thread_id, include_turns=False)
        if method == "thread/turns/list":
            if self.active_reads_remaining.get(thread_id, 0):
                raise AssertionError("paged history was requested before metadata became idle")
            if thread_id not in self.subscribed_threads:
                raise AssertionError("paged history was requested before completion-event subscription")
            if any(turn["status"] == "inProgress" for turn in self.turns[thread_id]):
                raise AssertionError("paged history was requested before turn/completed")
            if thread_id in self.history_unsupported:
                raise RuntimeError("list_turns is not supported yet")
            return {"data": list(reversed(self.turns[thread_id]))}
        if method == "turn/start":
            role = liveprobe._ROLE_ORDER[self.direct_baseline_starts]
            if thread_id != THREAD_IDS[role]:
                raise AssertionError("direct baseline turns must use the four dedicated roles in order")
            if params.get("model") != liveprobe.MODEL or params.get("effort") != liveprobe.EFFORT:
                raise AssertionError("baseline turn did not select gpt-5.6-terra/max")
            marker = liveprobe._BASELINE_MARKERS[role]
            if params.get("input") != [{"type": "text", "text": f"Reply exactly {marker}."}]:
                raise AssertionError("baseline turn did not use its deterministic marker")
            turn_id = f"turn-{role}-baseline"
            self.direct_baseline_starts += 1
            self._append_turn(thread_id, turn_id, f"Reply exactly {marker}.")
            self.active_reads_remaining[thread_id] = self.active_after_turn_start.get(thread_id, 0)
            return {"turn": {"id": turn_id}}
        if method in {"thread/archive", "turn/interrupt"}:
            return {}
        raise AssertionError(f"unexpected App Server request: {method}")

    def poll(self, timeout):
        self._maybe_schedule_deliveries()
        if not self.events:
            return None
        event = self.events[0]
        turn_id = event["params"]["turn"]["id"]
        remaining = self.completion_polls_remaining.get(turn_id, 0)
        if remaining:
            self.completion_polls_remaining[turn_id] = remaining - 1
            return None
        self.events.pop(0)
        self._complete_turn(event["params"]["threadId"], turn_id)
        return event

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
            "timeline": [],
            "metadata_statuses": [],
            "operations": [],
            "released_processes": set(),
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
        self.processes = 0

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
        if job_id == JOB_ID:
            self.state["stopped_pid"] = args.pid
        return {"id": job_id}

    def _job_archive(self, _store, args):
        self.state["job_archives"].append((args.job, args.note))
        return {"id": args.job}

    def _archive(self, _store, args):
        self.state["task_archives"].append((args.task, args.note))
        return {"task": args.task}

    def _process_factory(self, *_args, **_kwargs):
        pid = 4000 + self.processes
        self.processes += 1
        return FakeProcess(self.state, pid)

    def _run_fixture(self, root, **kwargs):
        with mock.patch.object(liveprobe.cli, "create", side_effect=self._create), mock.patch.object(
            liveprobe.cli, "bind", side_effect=self._bind
        ), mock.patch.object(liveprobe.cli, "job_add", side_effect=self._job_add), mock.patch.object(
            liveprobe.cli, "job_archive", side_effect=self._job_archive
        ), mock.patch.object(liveprobe.cli, "archive", side_effect=self._archive):
            return liveprobe.run_live_delivery(
                {"socket_path": SOCKET, "capabilities": {"model_requests": 0}, "diagnostics": {}},
                root,
                runtime_module=self.runtime,
                stream_factory=lambda _socket: self.stream,
                process_factory=self._process_factory,
                timeout_seconds=2,
                sleeper=lambda _seconds: None,
                **kwargs,
            )

    def test_fixture_materializes_all_roles_before_service_and_cleans_its_own_resources(self):
        root = self.base / "fixture"
        evidence_path = self.base / "evidence.json"
        result = self._run_fixture(root, evidence_path=evidence_path)

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["model_turns"], 6)
        self.assertEqual(result["cleanup"]["threads"], "archived")
        self.assertEqual(
            result["checks"],
            {
                "fixture_tasks_registered_before_threads": True,
                "executor_bound_before_first_model_turn": True,
                "all_roles_baselined_before_service": True,
                "baseline_history_read_after_idle": True,
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
        self.assertIn(self.state["stopped_pid"], self.state["released_processes"])
        self.assertEqual(self.state["runtime_config"].mam_root, root / "mam-state")
        self.assertEqual(self.state["manager"], THREAD_IDS["manager"])
        self.assertEqual(
            self.state["job_archives"],
            [(ARCHIVED_JOB_ID, "liveprobe fixture archived before delivery"), (JOB_ID, "liveprobe fixture cleanup")],
        )
        self.assertEqual([task for task, _ in self.state["task_archives"]], list(TASK_IDS.values()))

        methods = [method for method, _ in self.state["requests"]]
        self.assertEqual(methods.count("thread/start"), 4)
        self.assertEqual(methods.count("turn/start"), 4)
        direct = [params for method, params in self.state["requests"] if method == "turn/start"]
        self.assertEqual([params["threadId"] for params in direct], [THREAD_IDS[role] for role in liveprobe._ROLE_ORDER])
        for role, params in zip(liveprobe._ROLE_ORDER, direct):
            self.assertEqual(params["model"], liveprobe.MODEL)
            self.assertEqual(params["effort"], liveprobe.EFFORT)
            self.assertEqual(
                params["input"], [{"type": "text", "text": f"Reply exactly {liveprobe._BASELINE_MARKERS[role]}."}]
            )
            start_index = next(
                index
                for index, (method, request) in enumerate(self.state["requests"])
                if method == "turn/start" and request["threadId"] == THREAD_IDS[role]
            )
            resume_index = next(
                index
                for index, (method, request) in enumerate(self.state["requests"])
                if index > start_index and method == "thread/resume" and request["threadId"] == THREAD_IDS[role]
            )
            history_index = next(
                index
                for index, (method, request) in enumerate(self.state["requests"])
                if index > resume_index and method == "thread/turns/list" and request["threadId"] == THREAD_IDS[role]
            )
            self.assertLess(start_index, resume_index)
            self.assertLess(resume_index, history_index)

        service_start = self.state["timeline"].index(("service-start", THREAD_IDS["manager"]))
        direct_starts = [index for index, event in enumerate(self.state["timeline"]) if event[0] == "turn/start"]
        self.assertEqual(len(direct_starts), 4)
        self.assertTrue(all(index < service_start for index in direct_starts))
        self.assertIn(("service-stop", THREAD_IDS["manager"]), self.state["timeline"])
        self.assertTrue(self.stream.closed)
        self.assertEqual(result["resources"]["threads"], THREAD_IDS)
        self.assertEqual(result["resources"]["jobs"], {"stopped": JOB_ID, "archived_before_delivery": ARCHIVED_JOB_ID})
        self.assertEqual(
            result["turn_counts"]["before_job_stop"],
            {"manager": 2, "job_executor": 1, "idle_executor": 1, "archived_executor": 1},
        )
        self.assertEqual(
            result["turn_counts"]["after_job_stop"],
            {"manager": 2, "job_executor": 2, "idle_executor": 1, "archived_executor": 1},
        )
        self.assertEqual(
            result["cleanup"]["thread_archive"],
            {role: "archived" for role in reversed(liveprobe._ROLE_ORDER)},
        )
        self.assertEqual(
            result["cleanup"]["thread_interrupt"],
            {role: "not_needed" for role in reversed(liveprobe._ROLE_ORDER)},
        )
        for role in liveprobe._ROLE_ORDER:
            baseline = result["history"][f"{role}:baseline"]
            self.assertEqual(baseline["status_before_paged_history"], "idle")
            self.assertEqual(baseline["thread_turns_list"]["result"], "ok")

    def test_active_baseline_waits_for_metadata_idle_before_paged_history(self):
        root = self.base / "fixture-active-baseline"
        self.stream.active_after_turn_start[THREAD_IDS["manager"]] = 1
        result = self._run_fixture(root)
        self.assertEqual(result["status"], "passed")
        self.assertIn((THREAD_IDS["manager"], "active"), self.state["metadata_statuses"])
        self.assertEqual(result["calls"]["direct_turn_start"], 4)

    def test_idle_metadata_does_not_replace_the_baseline_completion_event(self):
        root = self.base / "fixture-completion-event"
        self.stream.completion_polls_remaining["turn-manager-baseline"] = 1
        result = self._run_fixture(root)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["completion_events"]["manager:baseline"]["turn_id"], "turn-manager-baseline")

    def test_idle_paging_unsupported_compares_include_turns_on_same_fixture_without_extra_baseline(self):
        root = self.base / "fixture-history-unsupported"
        evidence_path = self.base / "history-unsupported.json"
        self.stream.history_unsupported.add(THREAD_IDS["manager"])
        with self.assertRaisesRegex(liveprobe.LiveProbeError, r"thread/read\(includeTurns=true\) returned 1 turns"):
            self._run_fixture(root, evidence_path=evidence_path)

        self.assertFalse(root.exists())
        methods = [method for method, _ in self.state["requests"]]
        self.assertEqual(methods.count("turn/start"), 1)
        include_reads = [
            params
            for method, params in self.state["requests"]
            if method == "thread/read" and params.get("includeTurns") is True
        ]
        self.assertEqual(include_reads, [{"threadId": THREAD_IDS["manager"], "includeTurns": True}])
        evidence = json.loads(evidence_path.read_text())
        comparison = evidence["history"]["manager:baseline"]
        self.assertEqual(comparison["status_before_paged_history"], "idle")
        self.assertEqual(comparison["thread_turns_list"]["result"], "unsupported")
        self.assertEqual(comparison["thread_read_include_turns"]["result"], "ok")
        self.assertEqual(comparison["thread_read_include_turns"]["count"], 1)

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
