from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
import multi_agent_manager
import subprocess
import sys
import types
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from multi_agent_manager import cli
from multi_agent_manager import job_runtime
from multi_agent_manager import wait_runtime


CALLER = "00000000-0000-0000-0000-000000000001"
AGENT = "00000000-0000-0000-0000-000000000002"
REVIEWER = "00000000-0000-0000-0000-000000000003"
OTHER = "00000000-0000-0000-0000-000000000004"
TASK = "10000000-0000-0000-0000-000000000001"
REVIEW_TASK = "10000000-0000-0000-0000-000000000002"
OTHER_TASK = "10000000-0000-0000-0000-000000000003"


def snapshot(agent, status="active", turn=None):
    turns = [] if turn is None else [{"id": turn, "status": "inProgress"}]
    return {"thread": {"id": agent, "status": {"type": status}, "turns": turns}}


def job(job_id="job-1", note="registered work", status="running", probe=None):
    return {
        "id": job_id,
        "note": note,
        "status": status,
        "host": "local",
        "pid": 10,
        "identity": {"host": "local", "boot_id": "test", "start_ticks": 10},
        "probe": probe,
    }


def task(task_id=TASK, title="worker task", agent=AGENT, jobs=(), status="working", review=None):
    data = {
        "id": task_id,
        "title": title,
        "agent": agent,
        "status": status,
        "jobs": list(jobs),
    }
    if review is not None:
        data["review"] = review
    return data


def event(method, agent, *, turn=None, status=None):
    params = {"threadId": agent}
    if turn is not None:
        params["turn"] = {"id": turn}
    if status is not None:
        params["status"] = {"type": status}
    return {"method": method, "params": params}


def native_message_event(agent, turn, item_id, *, observed_at=1, method="item/started"):
    params = {
        "threadId": agent,
        "turnId": turn,
        "item": {"type": "userMessage", "id": item_id},
        "startedAtMs": observed_at,
    }
    return {"method": method, "params": params}


class FakeStore:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def all(self):
        self.calls += 1
        return self.rows(self.calls) if callable(self.rows) else self.rows


class FakeStream:
    def __init__(self, snapshots, *, queued=(), events=(), clock=None, on_resume=None):
        self.snapshots = dict(snapshots)
        self.queued = list(queued)
        self.events = list(events)
        self.clock = clock
        self.on_resume = on_resume
        self.resumed = []
        self.closed = False

    def resume(self, agent):
        self.resumed.append(agent)
        if self.on_resume is not None:
            self.queued.extend(self.on_resume(agent))
        value = self.snapshots[agent]
        if isinstance(value, BaseException):
            raise value
        return value

    def poll(self, timeout):
        if self.queued:
            value = self.queued.pop(0)
        elif timeout and self.events:
            value = self.events.pop(0)
        else:
            if timeout and self.clock is not None:
                self.clock[0] += timeout
            return None
        if isinstance(value, BaseException):
            raise value
        return value

    def close(self):
        self.closed = True


class FakeTrace:
    def __init__(self, polls=()):
        self.polls = list(polls)
        self.closed = False

    def poll(self):
        return self.polls.pop(0) if self.polls else []

    def close(self):
        self.closed = True


class FakeSessionMessages:
    def __init__(self, polls=()):
        self.polls = list(polls)
        self.closed = False

    def poll(self):
        return self.polls.pop(0) if self.polls else []

    def close(self):
        self.closed = True


class WaitRuntimeTests(unittest.TestCase):
    def run_wait(
        self,
        rows,
        snapshots,
        *,
        queued=(),
        events=(),
        on_resume=None,
        signals=(),
        session_signals=(),
        probe=None,
        wait_states=lambda: {},
        clock=None,
        control=1.0,
        state_refresh=5.0,
        job_refresh=5.0,
        cancelled=None,
    ):
        store = FakeStore(rows)
        stream = FakeStream(snapshots, queued=queued, events=events, clock=clock, on_resume=on_resume)
        trace = FakeTrace(signals)
        messages = FakeSessionMessages(session_signals)
        record, finished = {}, []

        def begin(role, bound_task, turn_id):
            value = {"agent": CALLER, "token": "wait-token", "role": role, "task": bound_task, "turn_id": turn_id}
            record.update(value)
            return value

        runner = wait_runtime.UnifiedWait(
            store,
            CALLER,
            socket_path="fake.sock",
            log_path="fake.log",
            begin_wait=begin,
            cancelled=cancelled or (lambda current: False),
            finish_wait=lambda current: finished.append(dict(current)),
            active_wait_states=wait_states,
            process_probe=probe or (lambda *args: {"status": "running"}),
            stream_factory=lambda path: stream,
            trace_factory=lambda path: trace,
            messages=messages,
            message_floor_ms=0,
            clock=(lambda: clock[0]) if clock is not None else wait_runtime.time.monotonic,
            control_check_seconds=control,
            state_refresh_seconds=state_refresh,
            job_refresh_seconds=job_refresh,
        )
        return runner.run(), stream, trace, record, finished, store

    def assert_exit(self, result, reason, message):
        self.assertEqual(result["status"], reason)
        self.assertEqual(result["reason"], reason)
        self.assertEqual(result["message"], message)

    def test_executor_scope_ignores_unrelated_tasks_and_returns_empty(self):
        rows = [task(agent=CALLER), task(OTHER_TASK, "unrelated", OTHER, [job("other-job", status="stopped")])]
        result, stream, _, record, finished, _ = self.run_wait(
            rows,
            {CALLER: snapshot(CALLER, turn="caller-turn"), OTHER: snapshot(OTHER, turn="other-turn")},
        )
        self.assert_exit(result, "empty", "no active subagents or unarchived jobs")
        self.assertEqual(result["agent"], CALLER)
        self.assertEqual(stream.resumed, [CALLER])
        self.assertEqual(record, {})
        self.assertEqual(finished, [])

    def test_manager_scope_never_subscribes_unregistered_threads(self):
        result, stream, _, record, finished, _ = self.run_wait(
            [],
            {CALLER: snapshot(CALLER, turn="caller-turn"), OTHER: snapshot(OTHER, turn="other-turn")},
        )
        self.assert_exit(result, "empty", "no active subagents or unarchived jobs")
        self.assertEqual(stream.resumed, [CALLER])
        self.assertEqual(record, {})
        self.assertEqual(finished, [])

    def test_manager_current_inactive_task_returns_completion_before_wait(self):
        result, _, _, record, finished, _ = self.run_wait(
            [task()],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, "idle")},
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual(result["agent"], AGENT)
        self.assertEqual(result["task"], TASK)
        self.assertEqual(result["task_title"], "worker task")
        self.assertEqual(record, {})
        self.assertEqual(finished, [])

    def test_manager_excludes_stopped_job_owned_by_active_agent(self):
        result, _, _, _, finished, _ = self.run_wait(
            [task(jobs=[job("owned-job", "keep owner", status="stopped")])],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, turn="worker-turn")},
            queued=[event("turn/completed", AGENT, turn="worker-turn")],
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertNotEqual(result["reason"], "job_stopped")
        self.assertEqual(result["agent"], AGENT)
        self.assertEqual(len(finished), 0)

    def test_verified_active_wait_owner_keeps_its_stopped_job_out_of_manager_scope(self):
        probes = []

        result, _, _, _, finished, _ = self.run_wait(
            [task(jobs=[job("owned-job", "owner handles it", status="stopped")])],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, "idle")},
            wait_states=lambda: {AGENT: "running"},
            events=[
                event("turn/started", AGENT, turn="wait-turn"),
                event("turn/completed", AGENT, turn="wait-turn"),
            ],
            probe=lambda *args: probes.append(args) or {"status": "stopped"},
            control=10.0,
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual(result["agent"], AGENT)
        self.assertEqual(probes, [])
        self.assertEqual(len(finished), 1)

    def test_manager_returns_stopped_job_for_inactive_owner_with_note(self):
        result, _, _, record, finished, _ = self.run_wait(
            [task(jobs=[job("done-job", "save artifacts", status="stopped")])],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, "idle")},
        )
        self.assert_exit(result, "job_stopped", "registered job stopped; process exit does not prove experimental success")
        self.assertEqual((result["agent"], result["waiter"]), (AGENT, CALLER))
        self.assertEqual((result["task"], result["task_title"], result["job"], result["note"]),
                         (TASK, "worker task", "done-job", "save artifacts"))
        self.assertEqual(record, {})
        self.assertEqual(finished, [])

    def test_review_delegates_source_to_active_reviewer(self):
        source = task(jobs=[])
        reviewer = task(REVIEW_TASK, "review task", REVIEWER, review={"task": TASK})
        result, stream, _, _, _, _ = self.run_wait(
            [source, reviewer],
            {
                CALLER: snapshot(CALLER, turn="caller-turn"),
                AGENT: snapshot(AGENT, "idle"),
                REVIEWER: snapshot(REVIEWER, turn="review-turn"),
            },
            queued=[event("turn/completed", REVIEWER, turn="review-turn")],
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual((result["agent"], result["task"]), (REVIEWER, REVIEW_TASK))
        self.assertEqual(set(stream.resumed), {CALLER, AGENT, REVIEWER})

    def test_inactive_reviewer_is_current_pending_work(self):
        source = task()
        reviewer = task(REVIEW_TASK, "review task", REVIEWER, review={"task": TASK})
        result, _, _, _, _, _ = self.run_wait(
            [source, reviewer],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, "idle"), REVIEWER: snapshot(REVIEWER, "idle")},
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual((result["agent"], result["task"], result["task_title"]),
                         (REVIEWER, REVIEW_TASK, "review task"))

    def test_archived_review_exposes_source_inactive_task_again(self):
        archived_review = task(REVIEW_TASK, "old review", REVIEWER, status="archived", review={"task": TASK})
        result, _, _, _, _, _ = self.run_wait(
            [task(), archived_review],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, "idle")},
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual((result["agent"], result["task"]), (AGENT, TASK))

    def test_review_does_not_hide_stopped_source_job(self):
        source = task(jobs=[job("source-job", "inspect source result", status="stopped")])
        reviewer = task(REVIEW_TASK, "review task", REVIEWER, review={"task": TASK})
        result, _, _, _, _, _ = self.run_wait(
            [source, reviewer],
            {
                CALLER: snapshot(CALLER, turn="caller-turn"),
                AGENT: snapshot(AGENT, "idle"),
                REVIEWER: snapshot(REVIEWER, turn="review-turn"),
            },
        )
        self.assert_exit(result, "job_stopped", "registered job stopped; process exit does not prove experimental success")
        self.assertEqual((result["agent"], result["task"], result["job"], result["note"]),
                         (AGENT, TASK, "source-job", "inspect source result"))

    def test_subscription_race_preserves_completion_queued_during_resume(self):
        completion = event("turn/completed", AGENT, turn="worker-turn")
        result, stream, _, _, _, _ = self.run_wait(
            [task()],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, turn="worker-turn")},
            on_resume=lambda agent_id: [completion] if agent_id == AGENT else [],
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual((result["agent"], result["task"]), (AGENT, TASK))
        self.assertEqual(stream.resumed, [CALLER, AGENT])

    def test_dynamic_task_registration_is_reconciled_without_global_scope(self):
        initial = task(TASK, "first task", AGENT)
        added = task(OTHER_TASK, "new task", OTHER)

        def rows(call):
            return [initial] if call < 3 else [initial, added]

        clock = [0.0]
        result, stream, _, _, finished, store = self.run_wait(
            rows,
            {
                CALLER: snapshot(CALLER, turn="caller-turn"),
                AGENT: snapshot(AGENT, turn="first-turn"),
                OTHER: snapshot(OTHER, "idle"),
            },
            clock=clock,
            control=10.0,
            state_refresh=1.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual((result["agent"], result["task"]), (OTHER, OTHER_TASK))
        self.assertIn(OTHER, stream.resumed)
        self.assertGreaterEqual(store.calls, 3)
        self.assertEqual(len(finished), 1)

    def test_active_to_inactive_handoff_returns_completion_and_never_probes_while_active(self):
        probes = []

        def probe(*args):
            probes.append(args)
            return {"status": "stopped"}

        result, _, _, _, finished, _ = self.run_wait(
            [task(jobs=[job("job-after-turn")])],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, turn="worker-turn")},
            events=[
                event("thread/status/changed", AGENT, status="idle"),
                event("turn/completed", AGENT, turn="worker-turn"),
            ],
            probe=probe,
            control=10.0,
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "agent_completed", "subagent completed its turn")
        self.assertEqual(probes, [])
        self.assertEqual(len(finished), 1)

    def test_targeted_user_steer_wakes_only_matching_current_wait(self):
        signals = [
            [],
            [wait_runtime.TraceMessage("stale-turn", "turn/steer")],
            [wait_runtime.TraceMessage("caller-turn", "turn/steer")],
        ]
        clock = [0.0]
        result, _, trace, record, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            signals=signals,
            clock=clock,
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "message", "received new message")
        self.assertEqual(result["agent"], CALLER)
        self.assertEqual(record["turn_id"], "caller-turn")
        self.assertTrue(trace.closed)
        self.assertEqual(len(finished), 1)

    def test_native_manager_input_turn_start_wakes_matching_wait(self):
        result, _, _, _, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            signals=[[], [wait_runtime.TraceMessage("caller-turn", "turn/start")]],
            clock=[0.0],
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "message", "received new message")
        self.assertEqual(result["agent"], CALLER)
        self.assertEqual(len(finished), 1)

    def test_native_manager_input_item_wakes_only_matching_current_wait(self):
        result, _, _, _, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            events=[
                native_message_event(OTHER, "caller-turn", "wrong-agent"),
                native_message_event(CALLER, "stale-turn", "wrong-turn"),
                native_message_event(CALLER, "caller-turn", "old", observed_at=-1),
                native_message_event(CALLER, "caller-turn", "current"),
            ],
            clock=[0.0],
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "message", "received new message")
        self.assertEqual(result["agent"], CALLER)
        self.assertEqual(len(finished), 1)

    def test_executor_ignores_other_bound_agent_lifecycle_before_its_snapshot(self):
        result, stream, _, _, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()]), task(OTHER_TASK, "other task", OTHER)],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            events=[
                event("turn/started", OTHER, turn="other-turn"),
                native_message_event(CALLER, "caller-turn", "native-input"),
            ],
            clock=[0.0],
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "message", "received new message")
        self.assertEqual(result["agent"], CALLER)
        self.assertEqual(stream.resumed, [CALLER])
        self.assertEqual(len(finished), 1)

    def test_native_session_message_wakes_only_matching_current_wait(self):
        result, _, _, record, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            session_signals=[
                [],
                [wait_runtime.SessionMessage("stale-turn", "stale")],
                [wait_runtime.SessionMessage("caller-turn", "current")],
            ],
            clock=[0.0],
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(result, "message", "received new message")
        self.assertEqual((result["agent"], record["turn_id"]), (CALLER, "caller-turn"))
        self.assertEqual(len(finished), 1)

    def test_manual_stop_is_distinct_and_cleans_only_its_wait(self):
        calls = []

        def cancelled(record):
            calls.append(record["token"])
            return len(calls) >= 2

        result, _, _, _, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            cancelled=cancelled,
        )
        self.assert_exit(result, "cancelled", "manual mam wait stop")
        self.assertEqual(result["agent"], CALLER)
        self.assertEqual(len(finished), 1)

    def test_timeout_has_fixed_one_hour_reason_and_field(self):
        clock = [0.0]
        result, _, _, _, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            clock=clock,
            control=4000.0,
            state_refresh=4000.0,
            job_refresh=4000.0,
        )
        self.assert_exit(result, "timeout", "fixed 3600-second wait elapsed")
        self.assertEqual((result["agent"], result["timeout_seconds"]), (CALLER, 3600))
        self.assertEqual(len(finished), 1)

    def test_initial_reconciliation_cannot_reset_the_fixed_timeout(self):
        clock = [0.0]

        def slow_probe(*_):
            clock[0] += wait_runtime.WAIT_SECONDS
            return {"status": "running"}

        result, _, _, record, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            clock=clock,
            probe=slow_probe,
        )
        self.assert_exit(result, "timeout", "fixed 3600-second wait elapsed")
        self.assertEqual(record, {})
        self.assertEqual(finished, [])

    def test_unknown_status_and_unknown_probe_are_explicit_errors(self):
        bad_agent, _, _, _, _, _ = self.run_wait(
            [task()],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, "systemError")},
        )
        self.assert_exit(bad_agent, "error", bad_agent["message"])
        self.assertIn(AGENT, bad_agent["message"])

        bad_job, _, _, _, _, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job("offline-job")])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            probe=lambda *args: {"status": "unknown", "error": "host offline"},
        )
        self.assert_exit(bad_job, "error", bad_job["message"])
        self.assertIn("offline-job", bad_job["message"])

    def test_unresolvable_caller_and_notification_disconnect_are_explicit_errors(self):
        caller_error, _, _, _, _, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, "systemError")},
        )
        self.assert_exit(caller_error, "error", caller_error["message"])
        self.assertIn("no active current turn", caller_error["message"])

        disconnected, _, _, _, finished, _ = self.run_wait(
            [task(agent=CALLER, jobs=[job()])],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
            events=[job_runtime.AppServerEventError("socket closed")],
            clock=[0.0],
            state_refresh=10.0,
            job_refresh=10.0,
        )
        self.assert_exit(disconnected, "error", disconnected["message"])
        self.assertIn("socket closed", disconnected["message"])
        self.assertEqual(len(finished), 1)

    def test_ambiguous_binding_and_review_cycle_fail_explicitly(self):
        ambiguous, _, _, _, _, _ = self.run_wait(
            [task(TASK, "one", AGENT), task(OTHER_TASK, "two", AGENT)],
            {CALLER: snapshot(CALLER, turn="caller-turn")},
        )
        self.assert_exit(ambiguous, "error", ambiguous["message"])
        self.assertIn("multiple nonarchived", ambiguous["message"])

        left = task(TASK, "left", AGENT, review={"task": REVIEW_TASK})
        right = task(REVIEW_TASK, "right", REVIEWER, review={"task": TASK})
        cycle, _, _, _, _, _ = self.run_wait(
            [left, right],
            {CALLER: snapshot(CALLER, turn="caller-turn"), AGENT: snapshot(AGENT, "idle"), REVIEWER: snapshot(REVIEWER, "idle")},
        )
        self.assert_exit(cycle, "error", cycle["message"])
        self.assertIn("review links contain a cycle", cycle["message"])


class TraceMessagesTests(unittest.TestCase):
    def test_initial_timestamp_floor_rejects_a_late_old_same_turn_span(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app-server.log"
            path.touch()
            trace = wait_runtime.TraceMessages(path)
            old = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
            stale = {"timestamp": old, "span": {"rpc.transport": "unix_socket", "rpc.method": "turn/steer",
                      "turn.id": "same-turn", "rpc.request_id": "stale", "app_server.connection_id": "1"}}
            with path.open("a") as handle:
                handle.write(json.dumps(stale) + "\n")
            self.assertEqual(trace.poll(), [])
            trace.close()

    def test_trace_is_targeted_deduplicated_stale_safe_and_handles_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app-server.log"
            stale = {"span": {"rpc.transport": "in-process", "rpc.method": "turn/steer", "turn.id": "stale",
                              "rpc.request_id": "1", "app_server.connection_id": "1"}}
            path.write_text(json.dumps(stale) + "\n")
            trace = wait_runtime.TraceMessages(path)
            self.assertEqual(trace.poll(), [])

            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            native = {"timestamp": now, "span": {"rpc.transport": "in-process", "rpc.method": "turn/start",
                      "turn.id": "current", "rpc.request_id": "2", "app_server.connection_id": "3"}}
            with path.open("a") as handle:
                handle.write(json.dumps(native) + "\n" + json.dumps(native) + "\n")
            self.assertEqual(trace.poll(), [wait_runtime.TraceMessage("current", "turn/start")])
            self.assertEqual(trace.poll(), [])

            rotated = path.with_suffix(".old")
            path.replace(rotated)
            later = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            steer = {"timestamp": later, "span": {"rpc.transport": "unix_socket", "rpc.method": "turn/steer",
                     "turn.id": "new-current", "rpc.request_id": "4", "app_server.connection_id": "5"}}
            path.write_text(json.dumps(steer) + "\n")
            self.assertEqual(trace.poll(), [wait_runtime.TraceMessage("new-current", "turn/steer")])
            trace.close()


class SessionMessagesTests(unittest.TestCase):
    @staticmethod
    def row(timestamp, turn, message_id, kinds):
        return {
            "timestamp": timestamp,
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "id": message_id,
                "internal_chat_message_metadata_passthrough": {
                    "turn_id": turn,
                    "content_item_kinds": kinds,
                },
            },
        }

    def test_session_messages_are_targeted_stale_safe_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout-current.jsonl"
            path.touch()
            watcher = wait_runtime.SessionMessages(path)
            old = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
            current = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
            rows = [
                self.row(old, "current-turn", "late-old", ["user.text"]),
                self.row(current, "other-turn", "wrong-turn", ["user.text"]),
                self.row(current, "current-turn", "environment", ["environments.environment_context"]),
                self.row(current, "current-turn", "current", ["user.text"]),
                self.row(current, "current-turn", "current", ["user.text"]),
            ]
            with path.open("a") as handle:
                handle.write("".join(json.dumps(row) + "\n" for row in rows))
            self.assertEqual(
                watcher.poll(),
                [wait_runtime.SessionMessage("other-turn", "wrong-turn"), wait_runtime.SessionMessage("current-turn", "current")],
            )
            self.assertEqual(watcher.poll(), [])
            watcher.close()

    def test_session_messages_require_the_current_session_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex"
            path = home / "sessions" / "2026" / "09" / "12" / f"rollout-{CALLER}.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"type": "session_meta", "payload": {"id": CALLER, "session_id": "session"}}) + "\n")
            watcher = wait_runtime.SessionMessages.from_environment(
                CALLER, environment={"CODEX_HOME": str(home), "CODEX_SESSION_ID": "session"}
            )
            self.assertEqual(watcher.path, path)
            watcher.close()

    def test_session_lookup_window_captures_input_written_between_discovery_and_open(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "codex"
            path = home / "sessions" / "2026" / "09" / "12" / f"rollout-{CALLER}.jsonl"
            path.parent.mkdir(parents=True)
            started_at = datetime.now(timezone.utc).timestamp()
            old = datetime.fromtimestamp(started_at - 60, timezone.utc).isoformat().replace("+00:00", "Z")
            current = datetime.fromtimestamp(started_at + 1, timezone.utc).isoformat().replace("+00:00", "Z")
            header = {"type": "session_meta", "payload": {"id": CALLER, "session_id": "session"}}
            path.write_text(json.dumps(header) + "\n" + json.dumps(self.row(old, "old-turn", "old", ["user.text"])) + "\n")
            original_open = wait_runtime.SessionMessages._open
            opened = False

            def append_during_lookup_window(instance, **kwargs):
                nonlocal opened
                if not opened:
                    opened = True
                    with path.open("a") as handle:
                        handle.write(json.dumps(self.row(current, "caller-turn", "during-open", ["user.text"])) + "\n")
                return original_open(instance, **kwargs)

            with patch.object(wait_runtime.SessionMessages, "_open", new=append_during_lookup_window):
                watcher = wait_runtime.SessionMessages.from_environment(
                    CALLER,
                    environment={"CODEX_HOME": str(home), "CODEX_SESSION_ID": "session"},
                    started_at=started_at,
                )
            self.assertTrue(opened)
            self.assertEqual(watcher.poll(), [wait_runtime.SessionMessage("caller-turn", "during-open")])
            watcher.close()


class CliWaitOutputTests(unittest.TestCase):
    def test_trace_boundary_captures_input_written_during_compatibility(self):
        with tempfile.TemporaryDirectory() as directory:
            trace_path = Path(directory) / "app-server.log"
            trace_path.touch()
            calls = []

            def configured_paths():
                calls.append("paths")
                return Path("/tmp/app-server.sock"), trace_path

            def require_compatible():
                calls.append("compatibility")
                now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                message = {"timestamp": now, "span": {"rpc.transport": "in-process", "rpc.method": "turn/start",
                           "turn.id": "caller-turn", "rpc.request_id": "during-compat",
                           "app_server.connection_id": "connection"}}
                with trace_path.open("a") as handle:
                    handle.write(json.dumps(message) + "\n")
                return {"socket_path": "/tmp/app-server.sock", "log_path": str(trace_path)}

            module = types.SimpleNamespace(configured_paths=configured_paths, require_compatible=require_compatible)
            expected = {"status": "message", "reason": "message", "message": "received new message", "agent": CALLER}

            def fake_wait(*_args, **kwargs):
                calls.append("wait")
                self.assertEqual(kwargs["trace"].poll(), [wait_runtime.TraceMessage("caller-turn", "turn/start")])
                return expected

            with patch.dict(sys.modules, {"multi_agent_manager.wait_compat": module}), \
                    patch.object(multi_agent_manager, "wait_compat", module, create=True), \
                    patch.object(cli, "wait_caller", return_value=CALLER), \
                    patch.object(cli, "wait_session_messages", return_value=FakeSessionMessages()), \
                    patch.object(wait_runtime, "wait", side_effect=fake_wait):
                self.assertEqual(cli.wait_unified(object(), object()), expected)
            self.assertEqual(calls, ["paths", "compatibility", "wait"])

    def test_session_boundary_captures_native_input_written_during_compatibility(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace_path = root / "app-server.log"
            trace_path.touch()
            journal = root / "codex" / "sessions" / "2026" / "09" / "12" / f"rollout-{CALLER}.jsonl"
            journal.parent.mkdir(parents=True)
            journal.write_text(json.dumps({
                "type": "session_meta", "payload": {"id": CALLER, "session_id": "session"},
            }) + "\n")
            calls = []

            def configured_paths():
                calls.append("paths")
                return Path("/tmp/app-server.sock"), trace_path

            def require_compatible():
                calls.append("compatibility")
                now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                row = SessionMessagesTests.row(now, "caller-turn", "native-message", ["user.text"])
                with journal.open("a") as handle:
                    handle.write(json.dumps(row) + "\n")
                return {"socket_path": "/tmp/app-server.sock", "log_path": str(trace_path)}

            module = types.SimpleNamespace(configured_paths=configured_paths, require_compatible=require_compatible)
            expected = {"status": "message", "reason": "message", "message": "received new message", "agent": CALLER}

            def fake_wait(*_args, **kwargs):
                calls.append("wait")
                self.assertEqual(kwargs["messages"].poll(), [wait_runtime.SessionMessage("caller-turn", "native-message")])
                return expected

            with patch.dict(sys.modules, {"multi_agent_manager.wait_compat": module}), \
                    patch.object(multi_agent_manager, "wait_compat", module, create=True), \
                    patch.object(cli, "wait_caller", return_value=CALLER), \
                    patch.dict(cli.os.environ, {"CODEX_HOME": str(root / "codex"), "CODEX_SESSION_ID": "session"}, clear=True), \
                    patch.object(wait_runtime, "wait", side_effect=fake_wait):
                self.assertEqual(cli.wait_unified(object(), object()), expected)
            self.assertEqual(calls, ["paths", "compatibility", "wait"])

    def test_default_wait_accepts_no_wait_options_or_jobs_subcommand(self):
        parsed = cli.parser().parse_args(["wait"])
        self.assertIs(parsed.func, cli.wait_unified)
        for argv in (["wait", "jobs"], ["wait", "--timeout", "1"], ["wait", "--agent", CALLER]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                cli.parser().parse_args(argv)

    def test_wait_caller_requires_a_canonical_thread_id(self):
        for value in (None, "", "not-a-thread", "A0000000-0000-0000-0000-000000000001"):
            environment = {} if value is None else {"CODEX_THREAD_ID": value}
            with self.subTest(value=value), patch.dict(cli.os.environ, environment, clear=True):
                with self.assertRaisesRegex(cli.Error, "CODEX_THREAD_ID"):
                    cli.wait_caller()
        with patch.dict(cli.os.environ, {"CODEX_THREAD_ID": CALLER}, clear=True):
            self.assertEqual(cli.wait_caller(), CALLER)

    def test_compatibility_gate_is_called_without_arguments_and_supplies_runtime_paths(self):
        require = Mock(return_value={"socket_path": "/tmp/app.sock", "log_path": "/tmp/app.log"})
        module = types.SimpleNamespace(require_compatible=require)
        with patch.dict(sys.modules, {"multi_agent_manager.wait_compat": module}), \
                patch.object(multi_agent_manager, "wait_compat", module, create=True):
            self.assertEqual(cli.wait_compatibility(), {"socket_path": "/tmp/app.sock", "log_path": "/tmp/app.log"})
        require.assert_called_once_with()

    def test_python_module_entry_invokes_cli_main(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "multi_agent_manager.cli", "wait", "--help"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wait for this agent's MAM work", result.stdout)

    def test_cli_json_retains_reason_and_required_identifiers_for_each_exit(self):
        cases = [
            {
                "status": "timeout", "reason": "timeout", "message": "fixed 3600-second wait elapsed",
                "agent": CALLER, "timeout_seconds": 3600,
            },
            {
                "status": "job_stopped", "reason": "job_stopped",
                "message": "registered job stopped; process exit does not prove experimental success",
                "agent": AGENT, "task": TASK, "task_title": "worker task", "job": "job-1", "note": "saved",
            },
            {
                "status": "agent_completed", "reason": "agent_completed", "message": "subagent completed its turn",
                "agent": AGENT, "task": TASK, "task_title": "worker task",
            },
            {"status": "cancelled", "reason": "cancelled", "message": "manual mam wait stop", "agent": CALLER},
            {"status": "message", "reason": "message", "message": "received new message", "agent": CALLER},
        ]
        for expected in cases:
            with self.subTest(reason=expected["reason"]), \
                    patch.object(cli, "project_config", return_value=object()), \
                    patch.object(cli, "Store", return_value=object()), \
                    patch.object(cli, "wait_unified", return_value=expected), \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(cli.main(["wait"]), 0)
            self.assertEqual(json.loads(output.getvalue()), expected)


if __name__ == "__main__":
    unittest.main()
