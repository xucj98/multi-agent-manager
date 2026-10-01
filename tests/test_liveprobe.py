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
}
THREAD_IDS = {
    "manager": "20000000-0000-4000-8000-000000000001",
    "job_executor": "20000000-0000-4000-8000-000000000002",
}
JOB_ID = "30000000-0000-4000-8000-000000000001"
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
        self.manager_delivery_ready = False
        self.job_delivery_added = False
        self.history_unsupported: set[str] = set()
        self.active_reads_remaining: dict[str, int] = {}
        self.active_after_turn_start: dict[str, int] = {}
        self.completion_polls_remaining: dict[str, int] = {}
        self.subscribed_threads: set[str] = set()
        self.resume_failures: dict[str, list[str]] = {}
        self.resume_calls: dict[str, int] = {}
        self.completed_turn_ids: set[str] = set()
        self.events: list[dict] = []
        self.manager_delivery_input_override: str | None = None
        self.manager_delivery_reply_override: str | None = None
        self.manager_baseline_reply_override: str | None = None
        self.failed_turn_ids: set[str] = set()
        self.history_omitted_turn_ids: set[str] = set()

    def _all_roles_have_baseline(self):
        return all(f"turn-{role}-baseline" in self.completed_turn_ids for role in liveprobe._ROLE_ORDER)

    def _append_turn(self, thread_id, turn_id, text, *, assistant_text=None):
        items = [{"id": f"input-{turn_id}", "type": "userMessage", "content": [{"type": "text", "text": text}]}]
        if turn_id.endswith("-baseline"):
            role = next(role for role, value in THREAD_IDS.items() if value == thread_id)
            marker = liveprobe._BASELINE_MARKERS[role]
            items.extend([
                {"id": f"call-{turn_id}", "type": "custom_tool_call", "name": "exec", "call_id": f"call-{turn_id}", "input": f'text("{marker}");'},
                {"id": f"output-{turn_id}", "type": "custom_tool_call_output", "call_id": f"call-{turn_id}", "output": [{"type": "input_text", "text": marker}]},
            ])
        if assistant_text is not None:
            items.append({"id": f"answer-{turn_id}", "type": "agentMessage", "text": assistant_text})
        self.turns[thread_id].append({"id": turn_id, "status": "inProgress", "items": items})
        self.events.append({"method": "turn/completed", "params": {"threadId": thread_id, "turn": {"id": turn_id}}})

    def _complete_turn(self, thread_id, turn_id):
        for turn in self.turns[thread_id]:
            if turn["id"] == turn_id:
                turn["status"] = "failed" if turn_id in self.failed_turn_ids else "completed"
                self.completed_turn_ids.add(turn_id)
                return
        raise AssertionError(f"completion event referenced unknown turn {turn_id}")

    def _add_manager_delivery_after_baselines(self):
        if self.manager_delivery_added or not self.state.get("running") or not self.manager_delivery_ready or not self._all_roles_have_baseline():
            return
        self.manager_delivery_added = True
        notification = (
            "[MAM MESSAGE]\n\n"
            "[task pending | /root/liveprobe/job_executor]\n"
            "Check the task and any published report; start or continue the work, request review, block or archive the task."
        )
        self._append_turn(
            THREAD_IDS["manager"],
            "turn-manager-delivery",
            self.manager_delivery_input_override or notification,
            assistant_text=self.manager_delivery_reply_override or "PROBE_MANAGER_BASELINE_READY",
        )

    def _add_job_delivery_if_released(self):
        if self.job_delivery_added or self.state.get("stopped_pid") not in self.state["released_processes"]:
            return
        self.job_delivery_added = True
        self._append_turn(
            THREAD_IDS["job_executor"],
            "turn-job-delivery",
            (
                "[MAM MESSAGE]\n\n"
                "[job exited | /root/liveprobe/job_executor]\n"
                "There are exited jobs. Check the results and archive them."
            ),
            assistant_text="PROBE_JOB_EXECUTOR_BASELINE_READY",
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
            if self.state["tasks_created"] != ["job"]:
                raise AssertionError("fixture threads were created before all tasks were registered")
            if params.get("ephemeral") is not False:
                raise AssertionError("fixture threads must be persisted")
            if params.get("model") != "gpt-6-sol" or params.get("config", {}).get("model_reasoning_effort") != "high":
                raise AssertionError("fixture thread did not select gpt-6-sol/high")
            role = liveprobe._ROLE_ORDER[self.thread_starts]
            self.thread_starts += 1
            return {"thread": {"id": THREAD_IDS[role], "status": {"type": "idle"}}}

        thread_id = params.get("threadId")
        if method == "thread/read":
            return self._thread_snapshot(thread_id, include_turns=params.get("includeTurns") is True)
        if method == "thread/resume":
            self.resume_calls[thread_id] = self.resume_calls.get(thread_id, 0) + 1
            failures = self.resume_failures.get(thread_id, [])
            if failures:
                raise RuntimeError(failures.pop(0))
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
            return {"data": [
                turn for turn in reversed(self.turns[thread_id])
                if turn["id"] not in self.history_omitted_turn_ids
            ]}
        if method == "turn/start":
            role = liveprobe._ROLE_ORDER[self.direct_baseline_starts]
            if thread_id != THREAD_IDS[role]:
                raise AssertionError("direct baseline turns must use the four dedicated roles in order")
            if params.get("model") != "gpt-6-sol" or params.get("effort") != "high":
                raise AssertionError("baseline turn did not select gpt-6-sol/high")
            marker = liveprobe._BASELINE_MARKERS[role]
            if params.get("input") != [{"type": "text", "text": liveprobe._baseline_prompt(role)}]:
                raise AssertionError("baseline turn did not request its harmless tool call")
            turn_id = f"turn-{role}-baseline"
            self.direct_baseline_starts += 1
            reply = self.manager_baseline_reply_override if role == "manager" else None
            self._append_turn(thread_id, turn_id, liveprobe._baseline_prompt(role), assistant_text=reply or marker)
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
            "sleeps": [],
        }
        self.runtime = FakeRuntime(self.state)
        self.stream = FakeStream(self.state)
        self.task_roles = iter(("job",))
        self.job_roles = iter((JOB_ID,))
        self.processes = 0

    def tearDown(self):
        self.temporary.cleanup()

    def _create(self, _store, _args):
        role = next(self.task_roles)
        self.state["tasks_created"].append(role)
        return {"id": TASK_IDS[role]}

    def _job_add(self, _store, args):
        job_id = next(self.job_roles)
        self.state["job_adds"].append((args.task, args.pid, args.note, job_id))
        if job_id == JOB_ID:
            self.state["stopped_pid"] = args.pid
        return {"id": job_id}

    def _job_archive(self, _store, args):
        self.state["job_archives"].append((args.job, args.note))
        if args.job == JOB_ID:
            self.stream.manager_delivery_ready = True
        return {"id": args.job}

    def _archive(self, _store, args):
        self.state["task_archives"].append((args.task, args.note))
        return {"task": args.task}

    def _process_factory(self, *_args, **_kwargs):
        pid = 4000 + self.processes
        self.processes += 1
        return FakeProcess(self.state, pid)

    def _run_fixture(self, root, *, timeout_seconds=2, **kwargs):
        def prepare_binding(fixture, task_role, thread_role):
            self.state["binds"].append((fixture.tasks[task_role], fixture.threads[thread_role]))

        with mock.patch.object(liveprobe.cli, "create", side_effect=self._create), mock.patch.object(
            liveprobe._LiveFixture, "_prepare_binding", autospec=True, side_effect=prepare_binding
        ), mock.patch.object(liveprobe.cli, "job_add", side_effect=self._job_add), mock.patch.object(
            liveprobe.cli, "job_archive", side_effect=self._job_archive
        ), mock.patch.object(liveprobe.cli, "archive", side_effect=self._archive):
            return liveprobe.run_live_delivery(
                {"socket_path": SOCKET, "capabilities": {"model_requests": 0}, "diagnostics": {}},
                root,
                runtime_module=self.runtime,
                stream_factory=lambda _socket: self.stream,
                process_factory=self._process_factory,
                timeout_seconds=timeout_seconds,
                sleeper=lambda seconds: self.state["sleeps"].append(seconds),
                **kwargs,
            )

    def test_fixture_materializes_all_roles_before_service_and_cleans_its_own_resources(self):
        root = self.base / "fixture"
        evidence_path = self.base / "evidence.json"
        result = self._run_fixture(root, evidence_path=evidence_path)

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["model_turns"], 4)
        self.assertEqual(result["cleanup"]["threads"], "archived")
        self.assertEqual(result["delivery_inputs"]["manager_delivery"]["item_type"], "userMessage")
        self.assertTrue(result["delivery_inputs"]["manager_delivery"]["matched"])
        self.assertEqual(result["delivery_inputs"]["manager_delivery"]["status"], "completed")
        self.assertEqual(result["delivery_inputs"]["manager_delivery"]["thread_id"], THREAD_IDS["manager"])
        self.assertEqual(
            result["delivery_inputs"]["manager_delivery"]["turn_id"],
            result["resources"]["turns"]["manager_ready_delivery"],
        )
        self.assertIn(
            "[task pending | /root/liveprobe/job_executor]",
            result["delivery_inputs"]["manager_delivery"]["text"],
        )
        self.assertEqual(result["delivery_inputs"]["exited_job_delivery"]["item_type"], "userMessage")
        self.assertEqual(result["delivery_inputs"]["exited_job_delivery"]["thread_id"], THREAD_IDS["job_executor"])
        self.assertEqual(
            result["delivery_inputs"]["exited_job_delivery"]["turn_id"],
            result["resources"]["turns"]["exited_job_delivery"],
        )
        self.assertEqual(result["delivery_inputs"]["exited_job_delivery"]["status"], "completed")
        self.assertIn(
            "[job exited | /root/liveprobe/job_executor]",
            result["delivery_inputs"]["exited_job_delivery"]["text"],
        )
        self.assertIn(
            "There are exited jobs. Check the results and archive them.",
            result["delivery_inputs"]["exited_job_delivery"]["text"],
        )
        self.assertNotIn(JOB_ID, result["delivery_inputs"]["exited_job_delivery"]["text"])
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
                "service_stopped_after_delivery": True,
                "baseline_custom_tool_calls": True,
                "job_archived_before_manager_delivery": True,
            },
        )
        self.assertFalse(root.exists())
        self.assertEqual(json.loads(evidence_path.read_text())["status"], "passed")
        self.assertEqual(self.state["tasks_created"], ["job"])
        self.assertEqual(
            self.state["binds"],
            [
                (TASK_IDS["job"], THREAD_IDS["job_executor"]),
            ],
        )
        self.assertEqual(self.state["job_adds"][0][0], TASK_IDS["job"])
        self.assertEqual(self.state["job_adds"][0][2], "liveprobe-short-job-exit")
        self.assertIn(self.state["stopped_pid"], self.state["released_processes"])
        self.assertEqual(self.state["runtime_config"].mam_root, root / "mam-state")
        self.assertEqual(self.state["manager"], THREAD_IDS["manager"])
        self.assertEqual(
            self.state["job_archives"],
            [(JOB_ID, "liveprobe fixture worker completed"), (JOB_ID, "liveprobe fixture cleanup")],
        )
        self.assertEqual([task for task, _ in self.state["task_archives"]], list(TASK_IDS.values()))

        methods = [method for method, _ in self.state["requests"]]
        self.assertEqual(methods.count("thread/start"), 2)
        self.assertEqual(methods.count("turn/start"), 2)
        direct = [params for method, params in self.state["requests"] if method == "turn/start"]
        self.assertEqual([params["threadId"] for params in direct], [THREAD_IDS[role] for role in liveprobe._ROLE_ORDER])
        for role, params in zip(liveprobe._ROLE_ORDER, direct):
            self.assertEqual(params["model"], liveprobe.MODEL)
            self.assertEqual(params["effort"], liveprobe.EFFORT)
            self.assertEqual(
                params["input"], [{"type": "text", "text": liveprobe._baseline_prompt(role)}]
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
        self.assertEqual(len(direct_starts), 2)
        self.assertTrue(all(index < service_start for index in direct_starts))
        self.assertIn(("service-stop", THREAD_IDS["manager"]), self.state["timeline"])
        self.assertTrue(self.stream.closed)
        self.assertEqual(result["resources"]["threads"], THREAD_IDS)
        self.assertEqual(result["resources"]["jobs"], {"exited": JOB_ID})
        self.assertEqual(
            result["turn_counts"]["before_job_stop"],
            {"manager": 1, "job_executor": 1},
        )
        self.assertEqual(
            result["turn_counts"]["after_job_stop"],
            {"manager": 2, "job_executor": 2},
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
        self.assertEqual(result["calls"]["direct_turn_start"], 2)

    def test_assistant_and_baseline_echo_cannot_replace_current_inbound_delivery(self):
        root = self.base / "fixture-assistant-only"
        evidence_path = self.base / "assistant-only.json"
        notification = (
            "[MAM MESSAGE]\n\n"
            "[task pending | /root/liveprobe/job_executor]\n"
            "Check the task and any published report; start or continue the work, request review, block or archive the task."
        )
        self.stream.manager_delivery_input_override = "unrelated user message"
        self.stream.manager_delivery_reply_override = notification
        self.stream.manager_baseline_reply_override = notification
        with self.assertRaisesRegex(liveprobe.LiveProbeError, "without matching inbound delivery"):
            self._run_fixture(root, evidence_path=evidence_path)
        evidence = json.loads(evidence_path.read_text())
        self.assertFalse(evidence["checks"]["manager_delivery"])
        receipt = evidence["delivery_inputs"]["manager_delivery"]
        self.assertFalse(receipt["matched"])
        self.assertEqual(receipt["status"], "completed")
        self.assertEqual(receipt["inbound_items"][0]["text"], "unrelated user message")
        self.assertEqual(evidence["cleanup"]["threads"], "archived")

    def test_wrong_executor_path_does_not_count_as_manager_delivery(self):
        root = self.base / "fixture-wrong-path"
        evidence_path = self.base / "wrong-path.json"
        self.stream.manager_delivery_input_override = (
            "[MAM MESSAGE]\n\n"
            "[task pending | /root/liveprobe/other_executor]\n"
            "Check the task and any published report; start or continue the work, request review, block or archive the task."
        )
        with self.assertRaisesRegex(liveprobe.LiveProbeError, "without matching inbound delivery"):
            self._run_fixture(root, evidence_path=evidence_path)
        evidence = json.loads(evidence_path.read_text())
        receipt = evidence["delivery_inputs"]["manager_delivery"]
        self.assertEqual(receipt["thread_id"], THREAD_IDS["manager"])
        self.assertEqual(receipt["turn_id"], "turn-manager-delivery")
        self.assertEqual(receipt["status"], "completed")
        self.assertFalse(receipt["matched"])
        self.assertEqual(receipt["inbound_items"][0]["item_type"], "userMessage")
        self.assertIn("[task pending | /root/liveprobe/other_executor]", receipt["inbound_items"][0]["text"])
        self.assertEqual(evidence["cleanup"]["threads"], "archived")

    def test_missing_corresponding_turn_records_observed_turns(self):
        root = self.base / "fixture-missing-turn"
        evidence_path = self.base / "missing-turn.json"
        self.stream.history_omitted_turn_ids.add("turn-manager-delivery")
        with self.assertRaisesRegex(liveprobe.LiveProbeError, "without matching inbound delivery"):
            self._run_fixture(root, evidence_path=evidence_path)
        receipt = json.loads(evidence_path.read_text())["delivery_inputs"]["manager_delivery"]
        self.assertEqual(receipt["thread_id"], THREAD_IDS["manager"])
        self.assertEqual(receipt["turn_id"], "turn-manager-delivery")
        self.assertFalse(receipt["matched"])
        self.assertEqual(receipt["observed_turns"][0]["id"], "turn-manager-baseline")
        self.assertNotIn("status", receipt)
        self.assertNotIn("inbound_items", receipt)

    def test_wrong_job_executor_path_or_message_type_is_not_matching_inbound_delivery(self):
        expected = [
            "[MAM MESSAGE]",
            "[job exited | /root/liveprobe/job_executor]",
            "There are exited jobs. Check the results and archive them.",
        ]
        wrong_executor = {
            "status": "completed",
            "items": [{"type": "userMessage", "content": [{
                "type": "text", "text": "[MAM MESSAGE]\n\n[job exited | /root/liveprobe/other_executor]\n"
                "There are exited jobs. Check the results and archive them.",
            }]}],
        }
        self.assertIsNone(liveprobe._delivery_input(wrong_executor, expected))
        wrong_type = {
            "status": "completed",
            "items": [{"type": "userMessage", "content": [{
                "type": "text", "text": "[MAM MESSAGE]\n\n[task pending | /root/liveprobe/job_executor]\n"
                "There are exited jobs. Check the results and archive them.",
            }]}],
        }
        self.assertIsNone(liveprobe._delivery_input(wrong_type, expected))

    def test_failed_turn_does_not_count_as_delivery(self):
        root = self.base / "fixture-failed-manager-turn"
        evidence_path = self.base / "failed-turn.json"
        self.stream.failed_turn_ids.add("turn-manager-delivery")
        with self.assertRaisesRegex(liveprobe.LiveProbeError, "without matching inbound delivery"):
            self._run_fixture(root, evidence_path=evidence_path)
        receipt = json.loads(evidence_path.read_text())["delivery_inputs"]["manager_delivery"]
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse(receipt["matched"])
        self.assertEqual(receipt["inbound_items"][0]["item_type"], "userMessage")

    def test_matching_mam_function_call_output_is_valid_inbound_delivery(self):
        expected = [
            "[MAM MESSAGE]", "[job exited | /root/liveprobe/job_executor]",
            "There are exited jobs. Check the results and archive them.",
        ]
        payload = (
            "[MAM MESSAGE]\n\n[job exited | /root/liveprobe/job_executor]\n"
            "There are exited jobs. Check the results and archive them."
        )
        turn = {"status": "completed", "items": [{
            "type": "functionCallOutput", "name": "message", "namespace": "mam",
            "output": [{"type": "input_text", "text": payload}],
        }]}
        self.assertEqual(liveprobe._delivery_input(turn, expected), {"item_type": "functionCallOutput", "text": payload})
        turn["items"][0]["namespace"] = "unrelated"
        self.assertIsNone(liveprobe._delivery_input(turn, expected))

    def test_empty_rollout_resume_retries_without_replaying_turn(self):
        root = self.base / "fixture-empty-rollout-retry"
        self.stream.resume_failures[THREAD_IDS["manager"]] = [
            "failed to read session metadata /tmp/rollout.jsonl: rollout at /tmp/rollout.jsonl is empty",
            "failed to read session metadata /tmp/rollout.jsonl: rollout at /tmp/rollout.jsonl is empty",
        ]
        result = self._run_fixture(root)

        self.assertEqual(result["status"], "passed")
        self.assertEqual(self.stream.resume_calls[THREAD_IDS["manager"]], 3)
        self.assertEqual(
            result["resume_persistence"]["manager"],
            {"attempts": 3, "retry_delays": [0.05, 0.1], "result": "subscribed_after_retry"},
        )
        self.assertEqual(self.state["sleeps"][:2], [0.05, 0.1])
        self.assertEqual(
            [method for method, _ in self.state["requests"]].count("turn/start"),
            2,
        )

    def test_empty_rollout_resume_timeout_keeps_last_error_and_is_bounded(self):
        root = self.base / "fixture-empty-rollout-timeout"
        evidence_path = self.base / "empty-rollout-timeout.json"
        self.stream.resume_failures[THREAD_IDS["manager"]] = [
            "failed to read session metadata /tmp/rollout.jsonl: rollout at /tmp/rollout.jsonl is empty"
        ]
        with self.assertRaisesRegex(liveprobe.LiveProbeError, r"rollout at /tmp/rollout\.jsonl is empty"):
            self._run_fixture(root, evidence_path=evidence_path, timeout_seconds=0.01)

        evidence = json.loads(evidence_path.read_text())
        self.assertEqual(
            evidence["resume_persistence"]["manager"],
            {"attempts": 1, "retry_delays": [], "result": "failed_timeout"},
        )
        self.assertEqual(self.stream.resume_calls[THREAD_IDS["manager"]], 1)
        self.assertEqual(
            [method for method, _ in self.state["requests"]].count("turn/start"),
            1,
        )

    def test_empty_rollout_resume_stops_after_bounded_retry_limit(self):
        root = self.base / "fixture-empty-rollout-retry-limit"
        evidence_path = self.base / "empty-rollout-retry-limit.json"
        empty_error = "failed to read session metadata /tmp/rollout.jsonl: rollout at /tmp/rollout.jsonl is empty"
        self.stream.resume_failures[THREAD_IDS["manager"]] = [empty_error] * 6
        with self.assertRaisesRegex(liveprobe.LiveProbeError, r"rollout at /tmp/rollout\.jsonl is empty"):
            self._run_fixture(root, evidence_path=evidence_path)

        evidence = json.loads(evidence_path.read_text())
        self.assertEqual(
            evidence["resume_persistence"]["manager"],
            {
                "attempts": 6,
                "retry_delays": [0.05, 0.1, 0.2, 0.4, 0.8],
                "result": "failed_retry_limit",
            },
        )
        self.assertEqual(self.stream.resume_calls[THREAD_IDS["manager"]], 6)
        self.assertEqual(self.state["sleeps"][:5], [0.05, 0.1, 0.2, 0.4, 0.8])
        self.assertEqual(
            [method for method, _ in self.state["requests"]].count("turn/start"),
            1,
        )

    def test_unrelated_resume_error_is_not_retried(self):
        root = self.base / "fixture-empty-rollout-unrelated-error"
        evidence_path = self.base / "empty-rollout-unrelated-error.json"
        self.stream.resume_failures[THREAD_IDS["manager"]] = [
            "failed to read session metadata /tmp/rollout.jsonl: rollout at /tmp/rollout.jsonl is malformed"
        ]
        with self.assertRaisesRegex(liveprobe.LiveProbeError, "rollout.jsonl is malformed"):
            self._run_fixture(root, evidence_path=evidence_path)

        evidence = json.loads(evidence_path.read_text())
        self.assertEqual(
            evidence["resume_persistence"]["manager"],
            {"attempts": 1, "retry_delays": [], "result": "failed_unrelated_error"},
        )
        self.assertEqual(self.stream.resume_calls[THREAD_IDS["manager"]], 1)
        self.assertEqual(self.state["sleeps"], [])

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
