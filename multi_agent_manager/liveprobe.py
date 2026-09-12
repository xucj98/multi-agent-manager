"""Bounded real-delivery acceptance for the MAM installer.

This module is intentionally separate from :mod:`wake_compat`.  The latter is
safe to run at scheduler startup and reconnection because it never touches a
registered thread.  This module is an installer-only, Manager-authorized
acceptance run: it creates a disposable MAM project and dedicated persisted
Codex threads, then proves the real detached scheduler delivers both a stopped
job wakeup and a Manager-ready wakeup.

It never reads or writes the caller's MAM project.  The fixture root must be a
new directory supplied by the installer, and cleanup is restricted to marker-
owned paths, task IDs, job IDs, processes, and thread IDs created in that run.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from types import SimpleNamespace
from typing import Any

from . import cli, job_runtime


MODEL = "gpt-5.6-terra"
EFFORT = "max"
MAX_MODEL_TURNS = 3
DEFAULT_TIMEOUT_SECONDS = 180.0
POLL_SECONDS = 0.5
_MARKER = ".mam-liveprobe.json"
_MARKER_KIND = "multi-agent-manager live delivery fixture v1"


class LiveProbeError(RuntimeError):
    """The authorized isolated delivery acceptance could not prove behavior."""


def _redact(value: Any, *, limit: int = 700) -> str:
    """Keep useful operational details while never copying likely secrets."""

    text = " ".join(str(value).split())[:limit]
    return re.sub(r"(?i)\b(token|secret|password|api[_-]?key)\s*=\s*[^\s,;]+", r"\1=<redacted>", text)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LiveProbeError(f"{label} returned no JSON object")
    return value


def _socket_path(compatibility: Mapping[str, Any]) -> str:
    path = compatibility.get("socket_path")
    if not isinstance(path, str) or not path or not Path(path).is_absolute():
        raise LiveProbeError("lightweight compatibility result has no absolute App Server socket path")
    return path


def _safe_root(value: str | os.PathLike[str]) -> Path:
    root = Path(value)
    if not root.is_absolute():
        raise LiveProbeError("live delivery fixture root must be an absolute path")
    if root.exists():
        if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
            raise LiveProbeError("live delivery fixture root must be a new empty regular directory")
    else:
        root.mkdir(mode=0o700, parents=True)
    marker = root / _MARKER
    marker.write_text(json.dumps({"kind": _MARKER_KIND}) + "\n", encoding="utf-8")
    try:
        os.chmod(root, 0o700)
    except OSError:
        pass
    return root.resolve(strict=True)


def _remove_owned_root(root: Path) -> None:
    """Remove only a root carrying the exact marker this process created."""

    marker = root / _MARKER
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise LiveProbeError("refusing to remove a live delivery fixture without its ownership marker") from exc
    if data != {"kind": _MARKER_KIND}:
        raise LiveProbeError("refusing to remove a live delivery fixture with an unexpected ownership marker")
    shutil.rmtree(root)


@contextlib.contextmanager
def _without_thread_id() -> Any:
    """Do not accidentally register the installer caller as fixture Manager."""

    present = "CODEX_THREAD_ID" in os.environ
    previous = os.environ.pop("CODEX_THREAD_ID", None)
    try:
        yield
    finally:
        if present and previous is not None:
            os.environ["CODEX_THREAD_ID"] = previous


def _thread_status(result: Any) -> str:
    data = _mapping(result, "App Server thread/read")
    thread = _mapping(data.get("thread"), "App Server thread/read")
    raw = thread.get("status")
    status = raw.get("type") if isinstance(raw, Mapping) else raw
    if not isinstance(status, str) or not status:
        raise LiveProbeError("App Server thread/read returned no thread status")
    return status


def _turns(result: Any) -> list[Mapping[str, Any]]:
    data = _mapping(result, "App Server thread/turns/list")
    rows = data.get("data")
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        raise LiveProbeError("App Server thread/turns/list returned no valid turn page")
    return list(rows)


def _turn_text(turn: Mapping[str, Any]) -> str:
    """Return every textual field in a turn without assuming protocol variants."""

    values: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, Mapping):
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(turn)
    return "\n".join(values)


def _status_is_terminal(status: str) -> bool:
    return status in {"idle", "notLoaded"}


def _status_is_interrupted(status: str) -> bool:
    return status.lower() in {"interrupted", "cancelled", "canceled", "paused", "suspended"}


def _is_unmaterialized_thread_error(error: Exception) -> bool:
    """Recognize a persisted thread that has never received a user turn.

    The current App Server deliberately keeps a normal persisted ``thread/start``
    thread out of its rollout store until a first user turn.  It reports this
    state as either ``not materialized yet`` on history reads or ``no rollout
    found`` on archive.  This is useful fixture evidence: an idle executor that
    must not receive a scheduler turn remains unmaterialized.
    """

    detail = str(error).lower()
    return "not materialized yet" in detail or "no rollout found for thread id" in detail


def _is_history_not_ready_error(error: Exception) -> bool:
    """Return whether a just-started persisted turn has not reached history yet."""

    return "list_turns is not supported yet" in str(error).lower()


def _load_runtime() -> Any:
    try:
        from . import wake_runtime
    except ImportError as exc:
        raise LiveProbeError("multi_agent_manager.wake_runtime is required for live delivery acceptance") from exc
    return wake_runtime


class _LiveFixture:
    """Own and clean one entirely isolated MAM/App Server acceptance fixture."""

    def __init__(
        self,
        compatibility: Mapping[str, Any],
        root: Path,
        *,
        timeout_seconds: float,
        runtime_module: Any,
        stream_factory: Callable[[str | None], Any],
        process_factory: Callable[..., subprocess.Popen[bytes]],
        clock: Callable[[], float],
        sleeper: Callable[[float], None],
    ) -> None:
        self.compatibility = dict(compatibility)
        self.socket_path = _socket_path(compatibility)
        self.root = root
        self.timeout_seconds = timeout_seconds
        self.runtime = runtime_module
        self.stream_factory = stream_factory
        self.process_factory = process_factory
        self.clock = clock
        self.sleeper = sleeper
        self.config = cli.ProjectConfig(root / "mam-state", root / "project", "liveprobe/state")
        self.store = cli.Store(self.config)
        self.stream: Any | None = None
        self.tasks: dict[str, str] = {}
        self.threads: dict[str, str] = {}
        self.jobs: list[tuple[str, str]] = []
        self.blockers: list[subprocess.Popen[bytes]] = []
        self.materialized_roles: set[str] = set()
        self.unmaterialized_roles: set[str] = set()
        self.started_service = False
        self.service_start_attempted = False
        self.stage = "prepare fixture"
        self.evidence: dict[str, Any] = {
            "status": "running",
            "model": MODEL,
            "effort": EFFORT,
            "model_turn_limit": MAX_MODEL_TURNS,
            "calls": {"thread_start": 0, "direct_turn_start": 0},
            "checks": {
                "fixture_tasks_registered_before_threads": False,
                "executor_bound_before_first_model_turn": False,
                "job_delivery": False,
                "manager_delivery": False,
                "manager_is_fixture_only": False,
                "turn_budget": False,
                "quiet_window_no_duplicate_starts": False,
                "idle_executors_received_no_turn": False,
            },
            "resources": {"tasks": {}, "threads": {}, "jobs": {}, "turns": {}},
            "cleanup": {
                "service": "not_started",
                "jobs": "not_started",
                "tasks": "not_started",
                "threads": "not_started",
                "thread_archive": {},
            },
        }

    def _deadline(self) -> float:
        return self.clock() + self.timeout_seconds

    def _expired(self, deadline: float, waiting_for: str) -> None:
        if self.clock() >= deadline:
            raise LiveProbeError(f"timed out waiting for {waiting_for}")

    def _request(self, method: str, params: Mapping[str, Any]) -> Any:
        if self.stream is None:
            raise LiveProbeError("live delivery probe has no App Server control stream")
        try:
            return self.stream.request(method, dict(params))
        except Exception as exc:
            raise LiveProbeError(f"App Server {method} failed: {_redact(exc)}") from exc

    def _create_tasks(self) -> None:
        self.stage = "register fixture tasks"
        titles = {
            "job": "MAM liveprobe stopped-job delivery",
            "idle": "MAM liveprobe no-job Manager delivery",
            "archived": "MAM liveprobe archived-job Manager delivery",
        }
        with _without_thread_id():
            for role, title in titles.items():
                try:
                    result = cli.create(self.store, SimpleNamespace(title=title, review=None))
                except Exception as exc:
                    raise LiveProbeError(f"cannot register fixture {role} task: {_redact(exc)}") from exc
                task_id = result.get("id") if isinstance(result, Mapping) else None
                if not isinstance(task_id, str) or not task_id:
                    raise LiveProbeError(f"fixture {role} task creation returned no TASK-ID")
                self.tasks[role] = task_id
                self.evidence["resources"]["tasks"][role] = task_id
        self.evidence["checks"]["fixture_tasks_registered_before_threads"] = True

    def _connect(self) -> None:
        self.stage = "connect fixture App Server stream"
        try:
            self.stream = self.stream_factory(self.socket_path)
        except Exception as exc:
            raise LiveProbeError(f"cannot connect to the live App Server for fixture threads: {_redact(exc)}") from exc

    def _create_thread(self, role: str) -> str:
        result = self._request(
            "thread/start",
            {
                "cwd": str(self.root / "project"),
                # The App Server supports turn history and archive cleanup for
                # ordinary persisted threads.  Every ID is recorded below and
                # only those IDs are ever archived during cleanup.
                "ephemeral": False,
                "model": MODEL,
                "effort": EFFORT,
                "sandbox": "read-only",
                "approvalPolicy": "never",
                "developerInstructions": (
                    "MAM installer acceptance fixture. Reply with the requested short marker only; "
                    "do not use tools, files, network, or create agents."
                ),
            },
        )
        response = _mapping(result, "App Server thread/start")
        thread = _mapping(response.get("thread"), "App Server thread/start")
        thread_id = thread.get("id")
        if not isinstance(thread_id, str) or not thread_id:
            raise LiveProbeError(f"fixture {role} thread/start returned no thread id")
        self.evidence["calls"]["thread_start"] += 1
        self.evidence["resources"]["threads"][role] = thread_id
        return thread_id

    def _create_and_bind_threads(self) -> None:
        self.stage = "create and bind dedicated fixture threads"
        for role in ("manager", "job_executor", "idle_executor", "archived_executor"):
            self.threads[role] = self._create_thread(role)
        bindings = {
            "job": "job_executor",
            "idle": "idle_executor",
            "archived": "archived_executor",
        }
        with _without_thread_id():
            for task_role, thread_role in bindings.items():
                try:
                    cli.bind(self.store, SimpleNamespace(task=self.tasks[task_role], agent=self.threads[thread_role]))
                except Exception as exc:
                    raise LiveProbeError(f"cannot bind fixture {task_role} executor: {_redact(exc)}") from exc
        self.evidence["checks"]["executor_bound_before_first_model_turn"] = True
        self.evidence["checks"]["manager_is_fixture_only"] = True

    def _spawn_blocker(self) -> subprocess.Popen[bytes]:
        try:
            process = self.process_factory(
                [sys.executable, "-u", "-c", "import sys; sys.stdin.buffer.read()"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise LiveProbeError(f"cannot start fixture short job: {_redact(exc)}") from exc
        if not isinstance(getattr(process, "pid", None), int) or process.pid <= 0:
            raise LiveProbeError("fixture short job returned no positive PID")
        self.blockers.append(process)
        return process

    def _release_blocker(self, process: subprocess.Popen[bytes]) -> None:
        handle = process.stdin
        if handle is not None and not handle.closed:
            handle.close()
        deadline = self.clock() + min(10.0, self.timeout_seconds)
        while process.poll() is None and self.clock() < deadline:
            self.sleeper(min(POLL_SECONDS, max(0.0, deadline - self.clock())))
        if process.poll() is None:
            # This is a process created solely by this fixture.  Stop it only
            # during fixture cleanup; no production or registered user job is
            # ever signalled here.
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    def _register_jobs(self) -> tuple[str, str]:
        self.stage = "register fixture jobs"
        job_process = self._spawn_blocker()
        try:
            job = cli.job_add(
                self.store,
                SimpleNamespace(
                    task=self.tasks["job"], host="local", pid=job_process.pid, note="liveprobe-short-job-stop"
                ),
            )
        except Exception as exc:
            raise LiveProbeError(f"cannot register fixture stopped-job probe: {_redact(exc)}") from exc
        job_id = job.get("id") if isinstance(job, Mapping) else None
        if not isinstance(job_id, str) or not job_id:
            raise LiveProbeError("fixture stopped-job registration returned no JOB-ID")
        self.jobs.append((self.tasks["job"], job_id))
        self.evidence["resources"]["jobs"]["stopped"] = job_id

        archived_process = self._spawn_blocker()
        try:
            archived = cli.job_add(
                self.store,
                SimpleNamespace(
                    task=self.tasks["archived"], host="local", pid=archived_process.pid, note="liveprobe-archived-job"
                ),
            )
            archived_id = archived.get("id") if isinstance(archived, Mapping) else None
            if not isinstance(archived_id, str) or not archived_id:
                raise LiveProbeError("fixture archived-job registration returned no JOB-ID")
            cli.job_archive(self.store, SimpleNamespace(job=archived_id, note="liveprobe fixture archived before delivery"))
        except LiveProbeError:
            raise
        except Exception as exc:
            raise LiveProbeError(f"cannot archive fixture archived-job probe: {_redact(exc)}") from exc
        self.evidence["resources"]["jobs"]["archived_before_delivery"] = archived_id
        self._release_blocker(archived_process)
        return job_id, "liveprobe-short-job-stop"

    def _start_service(self) -> None:
        self.stage = "start isolated fixture scheduler"
        # A runtime failure can occur after it has spawned a detached child but
        # before it returns its status mapping.  Cleanup may safely issue this
        # fixture's project-local stop even when no child was ultimately made.
        self.service_start_attempted = True
        try:
            # This deliberately uses the settled public two-argument runtime
            # API.  Parent and detached child repeat the lightweight check;
            # it has no model work and must not be bypassed or certified.
            result = self.runtime.start_service(self.config, manager=self.threads["manager"])
        except Exception as exc:
            raise LiveProbeError(f"cannot start isolated fixture scheduler: {_redact(exc)}") from exc
        status = _mapping(result, "fixture service start")
        if status.get("manager") != self.threads["manager"]:
            raise LiveProbeError("fixture service start did not persist the dedicated fixture Manager")
        self.started_service = True

    def _wait_for_service(self) -> None:
        self.stage = "fixture scheduler readiness"
        deadline = self._deadline()
        while True:
            try:
                status = _mapping(self.runtime.service_status(self.config), "fixture service status")
            except Exception as exc:
                raise LiveProbeError(f"cannot read isolated fixture scheduler status: {_redact(exc)}") from exc
            if status.get("manager") != self.threads["manager"]:
                raise LiveProbeError("fixture scheduler status changed to a non-fixture Manager")
            if status.get("running") is True and status.get("healthy") is True:
                return
            if status.get("status") in {"error", "disabled"} or status.get("error"):
                raise LiveProbeError(f"isolated fixture scheduler is unhealthy: {_redact(status.get('error') or status)}")
            self._expired(deadline, "isolated fixture scheduler readiness")
            self.sleeper(POLL_SECONDS)

    def _read_status(self, thread_id: str) -> str:
        result = self._request("thread/read", {"threadId": thread_id, "includeTurns": False})
        return _thread_status(result)

    def _resume_if_not_loaded(self, thread_id: str, status: str) -> str:
        if status != "notLoaded":
            return status
        self._request("thread/resume", {"threadId": thread_id, "excludeTurns": True})
        return self._read_status(thread_id)

    def _thread_turns(self, thread_id: str) -> list[Mapping[str, Any]]:
        result = self._request(
            "thread/turns/list",
            {"threadId": thread_id, "limit": 16, "sortDirection": "desc", "itemsView": "full"},
        )
        return _turns(result)

    def _turn_count(self) -> int:
        count = 0
        for role in self.materialized_roles:
            try:
                count += len(self._thread_turns(self.threads[role]))
            except LiveProbeError as exc:
                # A turn/start acknowledgement can precede materialization of
                # its history by a short interval.  Waiting for that interval
                # does not send a retry turn or consume another model call.
                if not _is_history_not_ready_error(exc):
                    raise
        return count

    def _enforce_turn_limit(self) -> None:
        count = self._turn_count()
        if count > MAX_MODEL_TURNS:
            raise LiveProbeError(
                f"fixture observed {count} model turns, exceeding the fixed acceptance limit of {MAX_MODEL_TURNS}"
            )

    def _wait_for_turn_text(self, role: str, expected: list[str], minimum_turns: int, label: str) -> Mapping[str, Any]:
        deadline = self._deadline()
        thread_id = self.threads[role]
        while True:
            self._enforce_turn_limit()
            status = self._resume_if_not_loaded(thread_id, self._read_status(thread_id))
            if _status_is_interrupted(status):
                raise LiveProbeError(f"fixture {label} thread entered {status}; it was not restarted")
            if _status_is_terminal(status):
                try:
                    turns = self._thread_turns(thread_id)
                except LiveProbeError as exc:
                    if _is_unmaterialized_thread_error(exc):
                        self.unmaterialized_roles.add(role)
                        self._expired(deadline, label)
                        self.sleeper(POLL_SECONDS)
                        continue
                    if _is_history_not_ready_error(exc):
                        self._expired(deadline, label)
                        self.sleeper(POLL_SECONDS)
                        continue
                    raise
                self.materialized_roles.add(role)
                if len(turns) >= minimum_turns:
                    for turn in turns:
                        text = _turn_text(turn)
                        if all(item in text for item in expected) and turn.get("status") == "completed":
                            return turn
            self._expired(deadline, label)
            self.sleeper(POLL_SECONDS)

    def _start_initial_executor_turn(self) -> None:
        self.stage = "start fixture executor baseline turn"
        if not self.evidence["checks"]["executor_bound_before_first_model_turn"]:
            raise LiveProbeError("fixture executor was not bound before its first model turn")
        result = self._request(
            "turn/start",
            {
                "threadId": self.threads["job_executor"],
                "input": [{"type": "text", "text": "Reply exactly PROBE_EXECUTOR_READY."}],
                "model": MODEL,
                "effort": EFFORT,
            },
        )
        response = _mapping(result, "App Server turn/start")
        turn = response.get("turn")
        if not isinstance(turn, Mapping):
            raise LiveProbeError("fixture executor baseline turn/start returned no turn")
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            raise LiveProbeError("fixture executor baseline turn/start returned no turn id")
        self.evidence["calls"]["direct_turn_start"] += 1
        self.evidence["resources"]["turns"]["executor_baseline_started"] = turn_id
        self.materialized_roles.add("job_executor")
        completed = self._wait_for_turn_text(
            "job_executor", ["PROBE_EXECUTOR_READY"], 1, "fixture executor baseline turn completion"
        )
        completed_id = completed.get("id")
        if completed_id != turn_id:
            raise LiveProbeError("fixture executor baseline completed under an unexpected turn id")
        self.evidence["resources"]["turns"]["executor_baseline_completed"] = turn_id

    def _wait_for_manager_delivery(self) -> None:
        self.stage = "verify fixture Manager delivery"
        manager_payloads = [
            (
                f"Executor AGENT-ID {self.threads['idle_executor']} has no unarchived jobs for "
                f"TASK-ID {self.tasks['idle']}: MAM liveprobe no-job Manager delivery."
            ),
            (
                f"Executor AGENT-ID {self.threads['archived_executor']} has no unarchived jobs for "
                f"TASK-ID {self.tasks['archived']}: MAM liveprobe archived-job Manager delivery."
            ),
        ]
        manager_turn = self._wait_for_turn_text("manager", manager_payloads, 1, "Manager-ready scheduler turn")
        manager_turn_id = manager_turn.get("id")
        if not isinstance(manager_turn_id, str) or not manager_turn_id:
            raise LiveProbeError("Manager-ready scheduler delivery returned no turn id")
        self.evidence["resources"]["turns"]["manager_ready_delivery"] = manager_turn_id
        self.evidence["checks"]["manager_delivery"] = True

    def _verify_idle_executors_received_no_turn(self) -> None:
        self.stage = "verify fixture idle executors received no scheduler turn"
        for role in ("idle_executor", "archived_executor"):
            deadline = self._deadline()
            while True:
                try:
                    self._thread_turns(self.threads[role])
                except LiveProbeError as exc:
                    if _is_unmaterialized_thread_error(exc):
                        self.unmaterialized_roles.add(role)
                        break
                    if _is_history_not_ready_error(exc):
                        self._expired(deadline, f"fixture {role} history state")
                        self.sleeper(POLL_SECONDS)
                        continue
                    raise
                raise LiveProbeError(f"fixture {role} unexpectedly materialized a turn history")
        self.evidence["checks"]["idle_executors_received_no_turn"] = True

    def _wait_for_stopped_job_delivery(self, job_id: str, note: str) -> None:
        self.stage = "verify stopped-job scheduler delivery"
        job_payload = (
            f"Stopped registered job: JOB-ID {job_id} ({note}); "
            f"TASK-ID {self.tasks['job']}: MAM liveprobe stopped-job delivery."
        )
        job_turn = self._wait_for_turn_text("job_executor", [job_payload], 2, "stopped-job scheduler turn")
        job_turn_id = job_turn.get("id")
        if not isinstance(job_turn_id, str) or not job_turn_id:
            raise LiveProbeError("stopped-job scheduler delivery returned no turn id")
        self.evidence["resources"]["turns"]["stopped_job_delivery"] = job_turn_id
        self.evidence["checks"]["job_delivery"] = True

        counts = {
            "manager": len(self._thread_turns(self.threads["manager"])),
            "job_executor": len(self._thread_turns(self.threads["job_executor"])),
            "idle_executor": 0,
            "archived_executor": 0,
        }
        if counts != {"manager": 1, "job_executor": 2, "idle_executor": 0, "archived_executor": 0}:
            raise LiveProbeError(f"fixture model turn distribution is unexpected: {counts}")
        # The fixture changes no records after the two deliveries.  Two fresh
        # scheduler intervals must therefore leave the exact turn distribution
        # unchanged, proving it did not start duplicate work for a quiet task.
        for _ in range(2):
            self.sleeper(POLL_SECONDS)
            self._enforce_turn_limit()
            observed = {
                "manager": len(self._thread_turns(self.threads["manager"])),
                "job_executor": len(self._thread_turns(self.threads["job_executor"])),
                "idle_executor": 0,
                "archived_executor": 0,
            }
            if observed != counts:
                raise LiveProbeError(f"fixture quiet window started unexpected additional turns: {observed}")
        self.evidence["checks"]["turn_budget"] = True
        self.evidence["checks"]["quiet_window_no_duplicate_starts"] = True
        self.evidence["model_turns"] = sum(counts.values())

    def run(self) -> dict[str, Any]:
        self._create_tasks()
        self._connect()
        self._create_and_bind_threads()
        job_id, note = self._register_jobs()
        self._start_service()
        self._wait_for_service()
        self._start_initial_executor_turn()
        self._wait_for_manager_delivery()
        self._verify_idle_executors_received_no_turn()
        # Releasing EOF makes this fixture-owned, already-registered local
        # process finish.  The detached scheduler must later observe the stop
        # itself; this module does not refresh the job record on its behalf.
        self._release_blocker(self.blockers[0])
        self._wait_for_stopped_job_delivery(job_id, note)
        self.evidence["status"] = "passed"
        return self.evidence

    def _interrupt_active_thread(self, thread_id: str) -> None:
        try:
            status = self._read_status(thread_id)
            if status != "active":
                return
            turns = self._thread_turns(thread_id)
            active = next((turn for turn in turns if turn.get("status") == "inProgress"), None)
            turn_id = active.get("id") if isinstance(active, Mapping) else None
            if isinstance(turn_id, str) and turn_id:
                self._request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
        except Exception:
            # Cleanup continues for the other dedicated threads and records the
            # aggregate error below.  It never guesses an unrelated turn id.
            raise

    def cleanup(self) -> list[str]:
        errors: list[str] = []
        if self.service_start_attempted:
            try:
                self.runtime.stop_service(self.config)
                deadline = self.clock() + min(15.0, self.timeout_seconds)
                while self.clock() < deadline:
                    status = _mapping(self.runtime.service_status(self.config), "fixture service cleanup status")
                    if status.get("running") is False:
                        break
                    self.sleeper(POLL_SECONDS)
                else:
                    raise LiveProbeError("fixture scheduler did not stop after its own stop request")
                self.evidence["cleanup"]["service"] = "stopped"
            except Exception as exc:
                errors.append(f"service cleanup: {_redact(exc)}")
                self.evidence["cleanup"]["service"] = "failed"
        else:
            self.evidence["cleanup"]["service"] = "not_started"

        for process in list(self.blockers):
            try:
                self._release_blocker(process)
            except Exception as exc:
                errors.append(f"fixture process cleanup: {_redact(exc)}")

        try:
            for task_id, job_id in self.jobs:
                cli.job_archive(self.store, SimpleNamespace(job=job_id, note="liveprobe fixture cleanup"))
            self.evidence["cleanup"]["jobs"] = "archived"
        except Exception as exc:
            errors.append(f"job cleanup: {_redact(exc)}")
            self.evidence["cleanup"]["jobs"] = "failed"

        try:
            with _without_thread_id():
                for task_id in self.tasks.values():
                    cli.archive(self.store, SimpleNamespace(task=task_id, note="liveprobe fixture cleanup"))
            self.evidence["cleanup"]["tasks"] = "archived"
        except Exception as exc:
            errors.append(f"task cleanup: {_redact(exc)}")
            self.evidence["cleanup"]["tasks"] = "failed"

        if self.stream is not None:
            thread_errors = False
            try:
                for role, thread_id in reversed(list(self.threads.items())):
                    try:
                        if role not in self.unmaterialized_roles:
                            self._interrupt_active_thread(thread_id)
                        try:
                            self._request("thread/archive", {"threadId": thread_id})
                        except LiveProbeError as exc:
                            if role in self.unmaterialized_roles and _is_unmaterialized_thread_error(exc):
                                self.evidence["cleanup"]["thread_archive"][role] = "not_materialized_no_rollout"
                                continue
                            raise
                        self.evidence["cleanup"]["thread_archive"][role] = "archived"
                    except Exception as exc:
                        thread_errors = True
                        detail = _redact(exc)
                        self.evidence["cleanup"]["thread_archive"][role] = f"failed: {detail}"
                        errors.append(f"thread cleanup ({role}): {detail}")
                self.evidence["cleanup"]["threads"] = "partial" if thread_errors else "archived_or_not_materialized"
            finally:
                try:
                    self.stream.close()
                except Exception as exc:
                    errors.append(f"control stream cleanup: {_redact(exc)}")
                self.stream = None
        else:
            self.evidence["cleanup"]["threads"] = "not_created"
        return errors


def _write_evidence(path: str | os.PathLike[str] | None, value: Mapping[str, Any]) -> None:
    if path is None:
        return
    target = Path(path)
    if not target.is_absolute():
        raise LiveProbeError("live delivery evidence path must be absolute")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, target)


def run_live_delivery(
    compatibility: Mapping[str, Any],
    root: str | os.PathLike[str],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    evidence_path: str | os.PathLike[str] | None = None,
    runtime_module: Any | None = None,
    stream_factory: Callable[[str | None], Any] = job_runtime.AppServerEventStream.connect,
    process_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Run exactly one bounded, isolated real scheduler acceptance fixture.

    ``compatibility`` must be the mapping just returned by the lightweight
    installer check, which supplies the App Server socket used to create only
    the fixture threads.  The fixture invokes the unchanged runtime lifecycle
    API, so its parent and detached child independently repeat their normal
    non-model compatibility checks.  It never calls install and never creates
    a compatibility bypass or a persisted PASS certificate.
    """

    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise LiveProbeError("live delivery timeout must be a positive number")
    root_path = _safe_root(root)
    fixture: _LiveFixture | None = None
    failure: LiveProbeError | None = None
    evidence: dict[str, Any] = {
        "status": "failed",
        "model": MODEL,
        "effort": EFFORT,
        "model_turn_limit": MAX_MODEL_TURNS,
        "stage": "prepare fixture",
    }
    try:
        fixture = _LiveFixture(
            _mapping(compatibility, "lightweight compatibility"),
            root_path,
            timeout_seconds=float(timeout_seconds),
            runtime_module=runtime_module or _load_runtime(),
            stream_factory=stream_factory,
            process_factory=process_factory,
            clock=clock,
            sleeper=sleeper,
        )
        evidence = fixture.run()
    except LiveProbeError as exc:
        failure = exc
        if fixture is not None:
            evidence = dict(fixture.evidence)
            evidence.update({"status": "failed", "stage": fixture.stage, "error": _redact(exc)})
        else:
            evidence.update({"error": _redact(exc)})
    except Exception as exc:
        failure = LiveProbeError(f"live delivery fixture failed unexpectedly: {_redact(exc)}")
        if fixture is not None:
            evidence = dict(fixture.evidence)
            evidence.update({"status": "failed", "stage": fixture.stage, "error": _redact(exc)})
        else:
            evidence.update({"error": _redact(exc)})
    finally:
        cleanup_errors: list[str] = []
        if fixture is not None:
            cleanup_errors = fixture.cleanup()
            evidence = dict(fixture.evidence) | {key: value for key, value in evidence.items() if key in {"status", "stage", "error"}}
        if cleanup_errors:
            evidence["cleanup_errors"] = cleanup_errors
            if failure is None:
                failure = LiveProbeError("live delivery fixture cleanup failed: " + "; ".join(cleanup_errors))
                evidence.update({"status": "failed", "stage": "cleanup", "error": _redact(failure)})
        try:
            _remove_owned_root(root_path)
        except Exception as exc:
            detail = f"fixture filesystem cleanup: {_redact(exc)}"
            evidence.setdefault("cleanup_errors", []).append(detail)
            if failure is None:
                failure = LiveProbeError(detail)
                evidence.update({"status": "failed", "stage": "cleanup", "error": detail})
        _write_evidence(evidence_path, evidence)
    if failure is not None:
        raise failure
    return evidence


def _load_compatibility(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    source = Path(path)
    try:
        if source.stat().st_size > 1024 * 1024:
            raise LiveProbeError("lightweight compatibility result is unexpectedly large")
        value = json.loads(source.read_text(encoding="utf-8"))
    except LiveProbeError:
        raise
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise LiveProbeError("cannot read the completed lightweight compatibility result") from exc
    return _mapping(value, "lightweight compatibility")


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="run one isolated real MAM wake delivery acceptance")
    parser.add_argument("--compatibility", required=True, metavar="PATH", help="JSON result from wake_compat --json")
    parser.add_argument("--root", required=True, metavar="PATH", help="new empty fixture directory below installer temporary root")
    parser.add_argument("--evidence", required=True, metavar="PATH", help="bounded JSON evidence output path")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, metavar="SECONDS")
    args = parser.parse_args(argv)
    try:
        result = run_live_delivery(
            _load_compatibility(args.compatibility),
            args.root,
            timeout_seconds=args.timeout,
            evidence_path=args.evidence,
        )
    except LiveProbeError as exc:
        print("MAM isolated live delivery: FAIL")
        print(_redact(exc))
        return 1
    print("MAM isolated live delivery: PASS")
    print(f"model turns: {result.get('model_turns', '?')}/{MAX_MODEL_TURNS}")
    print("checks: stopped-job executor delivery and fixture-Manager ready delivery")
    return 0


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
