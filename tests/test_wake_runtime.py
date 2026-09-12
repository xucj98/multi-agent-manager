from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

from multi_agent_manager import job_runtime, wake_runtime
from multi_agent_manager import cli


MANAGER = "00000000-0000-4000-8000-000000000001"
EXECUTOR = "00000000-0000-4000-8000-000000000002"
EXECUTOR_TWO = "00000000-0000-4000-8000-000000000003"
REVIEWER = "00000000-0000-4000-8000-000000000004"
TASK_ONE = "10000000-0000-4000-8000-000000000001"
TASK_TWO = "10000000-0000-4000-8000-000000000002"
TASK_THREE = "10000000-0000-4000-8000-000000000003"


class Clock:
    def __init__(self, value: float = 1000.0):
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeStream:
    def __init__(self, agent_statuses, calls, turns, resumed_statuses, resume_failures, *, failure=None, resumes=None):
        self.agent_statuses = agent_statuses
        self.calls = calls
        self.turns = turns
        self.resumed_statuses = resumed_statuses
        self.resume_failures = resume_failures
        self.failure = failure
        self.resumes = resumes
        self.closed = False

    def resume(self, agent):
        if self.resumes is not None:
            self.resumes.append(agent)
        if agent in self.resume_failures:
            raise self.resume_failures[agent]
        return {"thread": {"id": agent, "status": {"type": self.agent_statuses[agent]}, "turns": []}}

    def read(self, agent):
        return {"thread": {"id": agent, "status": {"type": self.resumed_statuses.get(agent, self.agent_statuses[agent])}, "turns": []}}

    def latest_turn(self, agent):
        return self.turns.get(agent)

    def start_turn(self, agent, text):
        if self.failure is not None:
            failure, self.failure = self.failure, None
            if isinstance(failure, AcceptedThenLost):
                self.calls.append((agent, text))
                self.turns[agent] = {"id": failure.turn_id, "status": "completed"}
                raise failure.error
            raise failure
        self.calls.append((agent, text))
        self.turns[agent] = {"id": f"accepted-{len(self.calls)}", "status": "inProgress"}
        return {"turn": {"id": "started"}}

    def close(self):
        self.closed = True


class AcceptedThenLost:
    def __init__(self, error, turn_id="turn-after-lost-reply"):
        self.error = error
        self.turn_id = turn_id


_ISOLATED_SOURCE_DAEMON_SCRIPT = """\
import contextlib
import sys
import time
from pathlib import Path

source_root = Path(sys.argv[1]).resolve()
mam_root = Path(sys.argv[2]).resolve()
project_root = Path(sys.argv[3]).resolve()
shadow_marker = Path(sys.argv[4]).resolve()
sys.path.insert(0, str(source_root))

from multi_agent_manager import cli, job_runtime, wake_runtime

if Path(wake_runtime.__file__).resolve().parent.parent != source_root:
    raise RuntimeError("isolated source runner imported a different wake runtime")

config = cli.ProjectConfig(mam_root, project_root, "project/isolated-source")
store = cli.Store(config)
try:
    result = wake_runtime.start_service(config)
    if result.get("status") != "awaiting_manager" or not result.get("ready_at") or not result.get("running"):
        raise RuntimeError(f"detached source daemon did not become ready: {result}")
    if shadow_marker.exists():
        raise RuntimeError("detached daemon executed the shadow MAM_ROOT package")
finally:
    with contextlib.suppress(Exception):
        wake_runtime.stop_service(config)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        state = wake_runtime._load_state(store)
        pid = state.get("pid")
        identity = state.get("identity")
        if not isinstance(pid, int) or not isinstance(identity, dict):
            break
        if job_runtime.probe_process("local", pid, identity).get("status") == "stopped":
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("isolated source daemon did not stop")

if shadow_marker.exists():
    raise RuntimeError("detached daemon executed the shadow MAM_ROOT package")
"""


class WakeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.mam_root = root / "mam"
        self.project_root = root / "projects"
        self.mam_root.mkdir()
        self.project_root.mkdir()
        self.config = cli.ProjectConfig(self.mam_root, self.project_root, "project/test")
        self.store = cli.Store(self.config)
        self.clock = Clock()
        self.statuses = {MANAGER: "idle", EXECUTOR: "idle", EXECUTOR_TWO: "idle", REVIEWER: "idle"}
        self.processes = {}
        self.process_calls = []
        self.starts = []
        self.stream_connections = 0
        self.resumes = []
        self.turns = {}
        self.resumed_statuses = {}
        self.resume_failures = {}
        self.stream_failure = None
        wake_runtime._record_manager(self.store, MANAGER, source="test")

    def tearDown(self):
        self.temporary.cleanup()

    def task(self, task_id, *, title=None, agent=EXECUTOR, jobs=(), review=None, status="working"):
        data = {
            "id": task_id,
            "title": title or f"task {task_id[-1]}",
            "agent": agent,
            "status": status,
            "created_at": "test",
            "workspace": str(self.project_root / "workspace" / task_id),
            "repos": {},
            "jobs": list(jobs),
            "report": None,
            "review": review,
            "archive": None,
            "error": None,
        }
        self.store.write(data)
        return data

    @staticmethod
    def job(job_id, *, status="running", note=None, pid=42, probe=None):
        return {
            "id": job_id,
            "note": note or job_id,
            "host": "local",
            "pid": pid,
            "identity": {"host": "local", "boot_id": "boot", "start_ticks": pid},
            "status": status,
            "checked_at": "before",
            "started_at": None,
            "probe": probe or {"status": status, "checked_at": "before", "error": None},
            "archive": None,
        }

    def compatibility(self):
        return {"socket_path": "/tmp/fake-app-server.sock", "capabilities": {"delivery": "validated"}, "diagnostics": {}}

    def agent_probe(self, agents, socket_path):
        self.assertEqual(socket_path, "/tmp/fake-app-server.sock")
        return {agent: {"status": self.statuses.get(agent, "unknown"), "error": None} for agent in agents}

    def process_probe(self, host, pid, identity):
        self.process_calls.append((host, pid, identity))
        value = self.processes.get(pid, "running")
        if isinstance(value, Exception):
            raise value
        return {"status": value, "checked_at": f"check-{len(self.process_calls)}", "identity": identity, "error": None if value != "unknown" else "SSH unavailable"}

    def stream_factory(self, _socket_path):
        self.stream_connections += 1
        failure, self.stream_failure = self.stream_failure, None
        return FakeStream(
            self.statuses,
            self.starts,
            self.turns,
            self.resumed_statuses,
            self.resume_failures,
            failure=failure,
            resumes=self.resumes,
        )

    def scheduler(self, **kwargs):
        process_probe = kwargs.pop("process_probe", self.process_probe)
        agent_probe = kwargs.pop("agent_probe", self.agent_probe)
        return wake_runtime.WakeScheduler(
            self.store,
            compatibility=self.compatibility,
            agent_probe=agent_probe,
            process_probe=process_probe,
            stream_factory=self.stream_factory,
            clock=self.clock,
            job_probe_seconds=kwargs.pop("job_probe_seconds", 30.0),
            **kwargs,
        )

    def state(self):
        return wake_runtime._load_state(self.store)

    @staticmethod
    def _write_shadow_wake_runtime(mam_root, marker):
        package = mam_root / "multi_agent_manager"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "wake_runtime.py").write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('shadowed', encoding='utf-8')\n"
            "raise SystemExit(97)\n",
            encoding="utf-8",
        )

    def test_routing_matrix_mixed_jobs_and_empty_task(self):
        self.task(TASK_ONE, title="stopped and running", jobs=[self.job("stopped", status="stopped", note="formal eval"), self.job("running", pid=43)])
        self.task(TASK_TWO, title="running only", agent=EXECUTOR_TWO, jobs=[self.job("only-running", pid=44)])
        self.task(TASK_THREE, title="ready for acceptance", agent=REVIEWER)

        self.scheduler().run_once()

        by_recipient = {recipient: text for recipient, text in self.starts}
        self.assertIn(EXECUTOR, by_recipient)
        self.assertIn("JOB-ID stopped (formal eval)", by_recipient[EXECUTOR])
        self.assertIn(MANAGER, by_recipient)
        self.assertIn(f"AGENT-ID {REVIEWER}", by_recipient[MANAGER])
        self.assertNotIn("running only", "\n".join(by_recipient.values()))
        self.assertEqual(len(self.process_calls), 2, "stopped jobs are never re-probed")

    def test_busy_executor_retains_stopped_job_until_idle(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.statuses[EXECUTOR] = "active"
        scheduler = self.scheduler()
        scheduler.run_once()
        self.assertEqual(self.starts, [])
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "pending")
        self.statuses[EXECUTOR] = "idle"
        scheduler.run_once()
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(self.starts[0][0], EXECUTOR)

    def test_not_loaded_stopped_owner_is_targetedly_resumed_then_started(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.statuses[EXECUTOR] = "notLoaded"
        self.resumed_statuses[EXECUTOR] = "idle"
        self.scheduler().run_once()
        self.assertEqual(self.starts[0][0], EXECUTOR)
        self.assertEqual(self.stream_connections, 1)

    def test_not_loaded_no_job_executor_exposes_manager_work(self):
        self.task(TASK_ONE)
        self.statuses[EXECUTOR] = "notLoaded"
        self.scheduler().run_once()
        self.assertEqual(self.starts[0][0], MANAGER)
        self.assertIn(f"AGENT-ID {EXECUTOR}", self.starts[0][1])

    def test_not_loaded_deleted_thread_stays_visible_without_creating_a_replacement(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.statuses[EXECUTOR] = "notLoaded"
        self.resume_failures[EXECUTOR] = job_runtime.AppServerEventError("thread missing")
        self.scheduler().run_once()
        self.assertEqual(self.starts, [])
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "blocked")
        self.assertIn("thread missing", event["last_error"])

    def test_running_only_job_never_wakes_manager_after_executor_ends(self):
        self.task(TASK_ONE, jobs=[self.job("still-running")])
        self.statuses[EXECUTOR] = "idle"
        self.scheduler().run_once()
        self.assertEqual(self.starts, [])
        self.assertFalse(self.state()["events"])

    def test_review_suppression_and_reexposure(self):
        self.task(TASK_ONE, title="source", agent=EXECUTOR)
        self.task(TASK_TWO, title="review", agent=REVIEWER, review={"task": TASK_ONE, "commits": {}})
        self.statuses[REVIEWER] = "active"
        scheduler = self.scheduler()
        scheduler.run_once()
        self.assertEqual(self.starts, [])
        review = self.store.read(TASK_TWO)
        review["status"] = "archived"
        self.store.write(review)
        scheduler.run_once()
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(self.starts[0][0], MANAGER)
        self.assertIn(f"TASK-ID {TASK_ONE}", self.starts[0][1])

    def test_uncertain_delivery_survives_restart_and_retries_with_backoff(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.stream_failure = job_runtime.AppServerEventError("connection closed after request")
        self.scheduler().run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "uncertain")
        self.assertEqual(self.starts, [])
        self.clock.advance(5)
        self.scheduler().run_once()  # a new scheduler object models a daemon restart
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "accepted")
        self.assertEqual(len(self.starts), 1)

    def test_crash_after_persisted_attempt_recovers_as_uncertain_before_retry(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.stream_failure = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.scheduler().run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "attempting")
        self.scheduler().run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "uncertain")
        self.assertEqual(self.starts, [])
        self.clock.advance(5)
        self.scheduler().run_once()
        self.assertEqual(next(iter(self.state()["events"].values()))["delivery"], "accepted")

    def test_accepted_turn_with_lost_reply_becomes_ambiguous_not_a_second_model_turn(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.stream_failure = AcceptedThenLost(job_runtime.AppServerEventError("connection closed after accepted turn/start"))
        self.scheduler().run_once()
        first = next(iter(self.state()["events"].values()))
        self.assertEqual(first["delivery"], "uncertain")
        self.assertEqual(first["failure_kind"], "response_loss_or_transport")
        self.assertEqual(len(self.starts), 1)
        self.clock.advance(5)
        self.scheduler().run_once()  # daemon restart after the recipient completed its new turn
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "ambiguous")
        self.assertIsNone(event["next_attempt_at"])
        self.assertEqual(len(self.starts), 1)

    def test_transient_unknown_probe_never_becomes_stopped(self):
        self.task(TASK_ONE, jobs=[self.job("remote", pid=51)])
        self.processes[51] = "unknown"
        scheduler = self.scheduler()
        scheduler.run_once()
        self.assertEqual(self.store.read(TASK_ONE)["jobs"][0]["status"], "running")
        self.assertEqual(self.starts, [])
        self.clock.advance(30)
        self.processes[51] = "stopped"
        scheduler.run_once()
        self.assertEqual(self.store.read(TASK_ONE)["jobs"][0]["status"], "stopped")
        self.assertEqual(self.starts[0][0], EXECUTOR)

    def test_no_repeated_turn_start_or_global_job_scan_for_unchanged_state(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.task(TASK_TWO, agent=EXECUTOR_TWO, jobs=[self.job("running", pid=71)])
        scheduler = self.scheduler()
        scheduler.run_once()
        scheduler.run_once()
        self.assertEqual([recipient for recipient, _ in self.starts], [EXECUTOR])
        self.assertEqual([pid for _, pid, _ in self.process_calls], [71])

    def test_quiet_monitoring_never_resumes_historical_threads(self):
        self.task(TASK_ONE, agent=EXECUTOR, jobs=[self.job("running", pid=81)])
        self.task(TASK_TWO, agent=EXECUTOR_TWO, status="archived")
        self.scheduler().run_once()
        self.assertEqual(self.stream_connections, 0)
        self.assertEqual(self.starts, [])

    def test_interrupted_latest_turn_requires_explicit_action(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.turns[EXECUTOR] = {"id": "interrupted-turn", "status": "interrupted"}
        self.scheduler().run_once()
        self.assertEqual(self.starts, [])
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "blocked")
        self.assertIsNone(event["next_attempt_at"])

    def test_interrupted_event_recovers_only_after_new_completed_turn_and_idle_recipient(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.turns[EXECUTOR] = {"id": "interrupted-turn", "status": "interrupted"}
        scheduler = self.scheduler()

        scheduler.run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["block_kind"], "interrupted_turn")
        self.assertEqual(event["interruption_turn_id"], "interrupted-turn")

        scheduler.run_once()  # An unchanged interrupted boundary remains blocked.
        self.assertEqual(self.starts, [])
        self.assertEqual(self.resumes, [EXECUTOR], "interruption re-observation must not resume the recipient")
        self.assertEqual(next(iter(self.state()["events"].values()))["delivery"], "blocked")

        self.turns[EXECUTOR] = {"id": "user-recovered-turn", "status": "completed"}
        self.statuses[EXECUTOR] = "active"
        scheduler.run_once()
        self.assertEqual(self.starts, [])
        self.assertEqual(next(iter(self.state()["events"].values()))["delivery"], "blocked")

        self.statuses[EXECUTOR] = "idle"
        scheduler.run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "accepted")
        self.assertEqual(event["interruption_recovery_turn_id"], "user-recovered-turn")
        self.assertEqual([recipient for recipient, _ in self.starts], [EXECUTOR])

        scheduler.run_once()
        self.assertEqual([recipient for recipient, _ in self.starts], [EXECUTOR])

    def test_accepted_task_ready_survives_unknown_source_without_duplicate_manager_turn(self):
        self.task(TASK_ONE)
        scheduler = self.scheduler()

        scheduler.run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "accepted")
        self.assertEqual([recipient for recipient, _ in self.starts], [MANAGER])

        self.statuses[EXECUTOR] = "unknown"
        scheduler.run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "accepted")
        self.assertIn("source thread metadata", event["last_condition_error"])

        self.statuses[EXECUTOR] = "idle"
        scheduler.run_once()
        self.assertEqual([recipient for recipient, _ in self.starts], [MANAGER])

    def test_task_ready_pre_send_unknown_source_retains_pending_event(self):
        self.task(TASK_ONE)
        self.statuses[MANAGER] = "active"
        probes = []

        def staged_probe(agents, socket_path):
            self.assertEqual(socket_path, "/tmp/fake-app-server.sock")
            probes.append(tuple(agents))
            if len(probes) == 1:
                return {
                    agent: {"status": "idle" if agent == EXECUTOR else "active", "error": None}
                    for agent in agents
                }
            if len(probes) == 2:
                return {agent: {"status": "unknown", "error": "temporary source query failure"} for agent in agents}
            return {agent: {"status": self.statuses.get(agent, "unknown"), "error": None} for agent in agents}

        scheduler = self.scheduler(agent_probe=staged_probe)
        scheduler.run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "pending")
        self.assertIn("temporary source query failure", event["last_condition_error"])
        self.assertEqual(self.starts, [])

        self.statuses[MANAGER] = "idle"
        scheduler.run_once()
        self.assertEqual([recipient for recipient, _ in self.starts], [MANAGER])
        scheduler.run_once()
        self.assertEqual([recipient for recipient, _ in self.starts], [MANAGER])

    def _accepted_task_ready(self):
        self.task(TASK_ONE)
        scheduler = self.scheduler()
        scheduler.run_once()
        self.assertEqual(next(iter(self.state()["events"].values()))["delivery"], "accepted")
        return scheduler

    def test_archived_task_invalidates_accepted_task_ready_event(self):
        scheduler = self._accepted_task_ready()
        task = self.store.read(TASK_ONE)
        task["status"] = "archived"
        self.store.write(task)

        scheduler.run_once()
        self.assertFalse(self.state()["events"])
        self.assertEqual([recipient for recipient, _ in self.starts], [MANAGER])

    def test_review_suppression_invalidates_accepted_task_ready_event(self):
        scheduler = self._accepted_task_ready()
        self.task(TASK_TWO, agent=REVIEWER, review={"task": TASK_ONE, "commits": {}})
        self.statuses[REVIEWER] = "active"

        scheduler.run_once()
        self.assertFalse(self.state()["events"])
        self.assertEqual([recipient for recipient, _ in self.starts], [MANAGER])

    def test_agent_reassignment_invalidates_accepted_task_ready_event(self):
        scheduler = self._accepted_task_ready()
        task = self.store.read(TASK_ONE)
        task["agent"] = EXECUTOR_TWO
        self.store.write(task)
        self.statuses[EXECUTOR_TWO] = "active"

        scheduler.run_once()
        self.assertFalse(self.state()["events"])
        self.assertEqual([recipient for recipient, _ in self.starts], [MANAGER])

    def test_explicit_rpc_rejection_retries_without_response_loss_ambiguity(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.stream_failure = job_runtime.AppServerRpcError("turn/start explicitly rejected")
        scheduler = self.scheduler()

        scheduler.run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "rejected")
        self.assertEqual(event["failure_kind"], "explicit_rpc_rejection")
        self.assertTrue(scheduler.compatibility_ready)
        self.assertEqual(self.starts, [])

        self.turns[EXECUTOR] = {"id": "unrelated-completed-turn", "status": "completed"}
        self.clock.advance(5)
        self.statuses[EXECUTOR] = "active"
        scheduler.run_once()
        self.assertEqual(next(iter(self.state()["events"].values()))["delivery"], "rejected")
        self.assertEqual(self.starts, [])

        self.statuses[EXECUTOR] = "idle"
        scheduler.run_once()
        event = next(iter(self.state()["events"].values()))
        self.assertEqual(event["delivery"], "accepted")
        self.assertNotIn("failure_kind", event)
        self.assertEqual([recipient for recipient, _ in self.starts], [EXECUTOR])

    def test_task_mutation_under_store_lock_wins_over_stale_probe(self):
        self.task(TASK_ONE, jobs=[self.job("race", pid=61)])
        self.statuses[EXECUTOR] = "active"

        def archive_during_probe(_host, _pid, _identity):
            data = self.store.read(TASK_ONE)
            data["jobs"][0]["status"] = "archived"
            self.store.write(data)
            return {"status": "stopped", "checked_at": "race", "identity": _identity, "error": None}

        self.scheduler(process_probe=archive_during_probe).run_once()
        self.assertEqual(self.starts, [])
        self.assertEqual(self.store.read(TASK_ONE)["jobs"][0]["status"], "archived")

    def test_review_cycle_and_unknown_executor_are_visible_without_turn_start(self):
        self.task(TASK_ONE, agent=EXECUTOR, review={"task": TASK_TWO, "commits": {}})
        self.task(TASK_TWO, agent=REVIEWER, review={"task": TASK_ONE, "commits": {}})
        self.statuses[EXECUTOR] = "systemError"
        self.statuses[REVIEWER] = "systemError"
        self.scheduler().run_once()
        diagnostics = self.state()["diagnostics"]
        self.assertTrue(any(item["kind"] == "review_cycle" for item in diagnostics))
        self.assertTrue(any(item["kind"] == "unknown_executor" for item in diagnostics))
        self.assertEqual(self.starts, [])

    def test_multiple_projects_keep_pending_state_isolated(self):
        self.task(TASK_ONE, jobs=[self.job("stopped", status="stopped")])
        self.scheduler().run_once()
        other_root = Path(self.temporary.name) / "other-mam"
        other_projects = Path(self.temporary.name) / "other-projects"
        other_root.mkdir()
        other_projects.mkdir()
        other = cli.Store(cli.ProjectConfig(other_root, other_projects, "project/other"))
        wake_runtime._record_manager(other, MANAGER, source="test")
        other_task = {
            "id": TASK_TWO,
            "title": "other",
            "agent": EXECUTOR_TWO,
            "status": "working",
            "created_at": "test",
            "workspace": str(other_projects / "workspace" / TASK_TWO),
            "repos": {}, "jobs": [], "report": None, "review": None, "archive": None, "error": None,
        }
        other.write(other_task)
        starts = []
        scheduler = wake_runtime.WakeScheduler(
            other,
            compatibility=self.compatibility,
            agent_probe=self.agent_probe,
            process_probe=self.process_probe,
            stream_factory=lambda path: FakeStream(self.statuses, starts, self.turns, self.resumed_statuses, self.resume_failures),
            clock=self.clock,
        )
        scheduler.run_once()
        self.assertNotEqual(wake_runtime._service_directory(self.store), wake_runtime._service_directory(other))
        self.assertEqual(len(self.state()["events"]), 1)
        self.assertEqual(len(wake_runtime._load_state(other)["events"]), 1)

    def test_fresh_project_awaits_manager_then_first_manager_action_registers_it(self):
        fresh_root = Path(self.temporary.name) / "fresh-mam"
        fresh_projects = Path(self.temporary.name) / "fresh-projects"
        fresh_root.mkdir()
        fresh_projects.mkdir()
        config = cli.ProjectConfig(fresh_root, fresh_projects, "project/fresh")
        identity = {"host": "local", "boot_id": "boot", "start_ticks": 77}
        process = types.SimpleNamespace(pid=77)

        def process_probe(_host, _pid, _identity=None):
            return {"status": "running", "identity": identity, "error": None}

        with mock.patch.object(wake_runtime, "_spawn_service", return_value=process), \
             mock.patch.object(wake_runtime, "_await_daemon_ready", side_effect=lambda store, _token, _pid: wake_runtime._load_state(store)), \
             mock.patch.object(job_runtime, "probe_process", side_effect=process_probe):
            result = wake_runtime.start_service(config)
        self.assertEqual(result["status"], "awaiting_manager")
        self.assertTrue(result["running"])
        fresh_store = cli.Store(config)
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": MANAGER}, clear=False):
            created = cli.create(fresh_store, types.SimpleNamespace(title="first task", review=None))
        self.assertEqual(wake_runtime.recorded_manager(fresh_store), MANAGER)
        self.assertTrue(Path(created["task_file"]).exists())

    def test_fresh_daemon_process_confirms_readiness_and_stops_without_app_server_delivery(self):
        daemon_root = Path(self.temporary.name) / "daemon-mam"
        daemon_projects = Path(self.temporary.name) / "daemon-projects"
        daemon_root.mkdir()
        daemon_projects.mkdir()
        shadow_marker = daemon_root / "shadowed-from-mam-root"
        self._write_shadow_wake_runtime(daemon_root, shadow_marker)
        config = cli.ProjectConfig(daemon_root, daemon_projects, "project/daemon")
        store = cli.Store(config)
        started = False
        try:
            result = wake_runtime.start_service(config)
            started = True
            self.assertEqual(result["status"], "awaiting_manager")
            self.assertTrue(result["running"])
            self.assertTrue(result["healthy"])
            self.assertTrue(result["ready_at"])
            self.assertFalse(shadow_marker.exists())

            stopped = wake_runtime.stop_service(config)
            self.assertEqual(stopped["status"], "disabled")
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                state = wake_runtime._load_state(store)
                observed = job_runtime.probe_process("local", state["pid"], state["identity"])
                if observed["status"] == "stopped":
                    break
                time.sleep(0.05)
            else:
                self.fail("fresh detached daemon did not stop after service stop")
        finally:
            if started:
                wake_runtime.stop_service(config)

    def test_isolated_source_checkout_daemon_ignores_mam_root_shadow_and_pythonpath(self):
        daemon_root = Path(self.temporary.name) / "isolated-source-mam"
        daemon_projects = Path(self.temporary.name) / "isolated-source-projects"
        daemon_root.mkdir()
        daemon_projects.mkdir()
        shadow_marker = daemon_root / "shadowed-from-mam-root"
        self._write_shadow_wake_runtime(daemon_root, shadow_marker)
        source_root = Path(wake_runtime.__file__).resolve().parent.parent
        self.assertTrue((source_root / "multi_agent_manager" / "wake_runtime.py").is_file())

        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(daemon_root)
        environment["CODEX_THREAD_ID"] = EXECUTOR
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                "-c",
                _ISOLATED_SOURCE_DAEMON_SCRIPT,
                str(source_root),
                str(daemon_root),
                str(daemon_projects),
                str(shadow_marker),
            ],
            cwd=daemon_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"isolated source daemon failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertFalse(shadow_marker.exists())

    def test_existing_bound_project_without_manager_fails_instead_of_guessing(self):
        # Remove the manager record made by setUp and leave a real executor binding.
        wake_runtime._service_path(self.store, "manager.json").unlink()
        self.task(TASK_ONE)
        with self.assertRaisesRegex(wake_runtime.WakeRuntimeError, "mam service start --manager"):
            wake_runtime.start_service(self.config)

    def test_live_bound_project_without_manager_fails_instead_of_reusing_stale_daemon_state(self):
        wake_runtime._service_path(self.store, "manager.json").unlink()
        self.task(TASK_ONE)
        state = wake_runtime._load_state(self.store)
        state.update({
            "enabled": True,
            "mode": "active",
            "pid": 78,
            "identity": {"host": "local", "boot_id": "live", "start_ticks": 78},
            "token": "live-without-manager",
            "ready_at": "ready",
            "healthy": True,
        })
        wake_runtime._save_state(self.store, state)

        with mock.patch.object(
            job_runtime,
            "probe_process",
            return_value={"status": "running", "identity": state["identity"], "error": None},
        ), mock.patch.object(wake_runtime, "_spawn_service") as spawn:
            with self.assertRaisesRegex(wake_runtime.WakeRuntimeError, "mam service start --manager"):
                wake_runtime.start_service(self.config)

        spawn.assert_not_called()
        self.assertEqual(wake_runtime._load_state(self.store)["mode"], "error")

    def test_live_awaiting_service_becomes_pending_until_its_first_active_cycle(self):
        identity = {"host": "local", "boot_id": "awaiting", "start_ticks": 79}
        state = wake_runtime._load_state(self.store)
        state.update({
            "enabled": True,
            "mode": "awaiting_manager",
            "pid": 79,
            "identity": identity,
            "token": "awaiting-service",
            "ready_at": "ready",
            "healthy": True,
        })
        wake_runtime._save_state(self.store, state)

        with mock.patch.object(wake_runtime, "_compatibility", self.compatibility), \
             mock.patch.object(job_runtime, "probe_process", return_value={"status": "running", "identity": identity, "error": None}):
            result = wake_runtime.start_service(self.config)

        self.assertEqual(result["mode"], "active")
        self.assertEqual(result["status"], "pending")
        self.assertFalse(result["healthy"])

    def test_startup_compatibility_failure_is_visible_in_service_status(self):
        with mock.patch.object(wake_runtime, "_compatibility", side_effect=wake_runtime.WakeRuntimeError("control socket unavailable")), \
             mock.patch.object(wake_runtime, "_spawn_service") as spawn:
            with self.assertRaisesRegex(wake_runtime.WakeRuntimeError, "control socket unavailable"):
                wake_runtime.start_service(self.config)

        spawn.assert_not_called()
        status = wake_runtime.service_status(self.config)
        self.assertEqual(status["status"], "error")
        self.assertIn("control socket unavailable", status["error"])

    def test_start_waits_for_child_identity_readiness_and_reports_starting_as_pending(self):
        identity = {"host": "local", "boot_id": "boot", "start_ticks": 89}
        ready = threading.Event()
        child_errors = []

        def process_probe(_host, _pid, _identity=None):
            return {"status": "running", "identity": identity, "error": None}

        def spawn(_config, _token, _log):
            def mark_ready():
                for _ in range(100):
                    state = wake_runtime._load_state(self.store)
                    if state.get("pid") == 89 and state.get("identity") == identity:
                        with self.store.lock("service-state"):
                            state = wake_runtime._load_state(self.store)
                            state["ready_at"] = "child-verified"
                            wake_runtime._save_state(self.store, state)
                        ready.set()
                        return
                    time.sleep(0.001)
                child_errors.append("test child never observed the persisted service identity")

            threading.Thread(target=mark_ready, daemon=True).start()
            return types.SimpleNamespace(pid=89)

        with mock.patch.object(wake_runtime, "_compatibility", self.compatibility), \
             mock.patch.object(wake_runtime, "_spawn_service", side_effect=spawn), \
             mock.patch.object(job_runtime, "probe_process", side_effect=process_probe):
            result = wake_runtime.start_service(self.config)

        self.assertTrue(ready.is_set())
        self.assertFalse(child_errors)
        self.assertTrue(result["running"])
        self.assertFalse(result["healthy"])
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["ready_at"], "child-verified")

    def test_unverifiable_existing_service_never_spawns_a_second_daemon(self):
        state = wake_runtime._load_state(self.store)
        state.update({
            "enabled": True,
            "mode": "active",
            "pid": 90,
            "identity": {"host": "local", "boot_id": "prior", "start_ticks": 90},
            "token": "prior-service",
        })
        wake_runtime._save_state(self.store, state)

        with mock.patch.object(
            job_runtime,
            "probe_process",
            return_value={"status": "unknown", "identity": None, "error": "temporary /proc failure"},
        ), mock.patch.object(wake_runtime, "_spawn_service") as spawn:
            with self.assertRaisesRegex(wake_runtime.WakeRuntimeError, "refusing to start another"):
                wake_runtime.start_service(self.config)

        spawn.assert_not_called()
        saved = wake_runtime._load_state(self.store)
        self.assertEqual(saved["mode"], "error")
        self.assertIn("temporary /proc failure", saved["error"])
        self.assertEqual(wake_runtime.service_status(self.config)["status"], "error")

    def test_concurrent_starts_share_one_detached_daemon(self):
        starts = []
        identity = {"host": "local", "boot_id": "boot", "start_ticks": 88}

        def spawn(_config, _token, _log):
            starts.append(1)
            return types.SimpleNamespace(pid=88)

        def process_probe(_host, _pid, _identity=None):
            return {"status": "running", "identity": identity, "error": None}

        with mock.patch.object(wake_runtime, "_compatibility", self.compatibility), \
             mock.patch.object(wake_runtime, "_spawn_service", side_effect=spawn), \
             mock.patch.object(wake_runtime, "_await_daemon_ready", side_effect=lambda store, _token, _pid: wake_runtime._load_state(store)), \
             mock.patch.object(job_runtime, "probe_process", side_effect=process_probe):
            threads = [threading.Thread(target=lambda: wake_runtime.start_service(self.config)) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertEqual(starts, [1])


if __name__ == "__main__":
    unittest.main()
