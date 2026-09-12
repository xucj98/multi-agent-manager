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
MAX_MODEL_TURNS = 6
DEFAULT_TIMEOUT_SECONDS = 180.0
POLL_SECONDS = 0.5
_MARKER = ".mam-liveprobe.json"
_MARKER_KIND = "multi-agent-manager live delivery fixture v1"
_ROLE_ORDER = ("manager", "job_executor", "idle_executor", "archived_executor")
_BASELINE_MARKERS = {
    "manager": "PROBE_MANAGER_BASELINE_READY",
    "job_executor": "PROBE_JOB_EXECUTOR_BASELINE_READY",
    "idle_executor": "PROBE_IDLE_EXECUTOR_BASELINE_READY",
    "archived_executor": "PROBE_ARCHIVED_EXECUTOR_BASELINE_READY",
}


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


def _included_turns(result: Any) -> list[Mapping[str, Any]]:
    """Read the optional turn list returned by ``thread/read(includeTurns=true)``."""

    data = _mapping(result, "App Server thread/read(includeTurns=true)")
    thread = _mapping(data.get("thread"), "App Server thread/read(includeTurns=true)")
    rows = thread.get("turns")
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        raise LiveProbeError("App Server thread/read(includeTurns=true) returned no valid turns")
    return list(rows)


def _turn_summaries(turns: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Keep receipt history compact and limited to fixture-owned metadata."""

    summaries: list[dict[str, Any]] = []
    for turn in turns:
        item: dict[str, Any] = {}
        for key in ("id", "status", "completedAt", "createdAt"):
            value = turn.get(key)
            if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                item[key] = value
        summaries.append(item)
    return summaries


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


def _status_is_interrupted(status: str) -> bool:
    return status.lower() in {"interrupted", "cancelled", "canceled", "paused", "suspended"}


def _is_paged_history_unsupported(error: Exception) -> bool:
    """Recognize the explicit current-App-Server pagination limitation."""

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
        # Only direct baseline turn IDs are known before their history is
        # available.  Cleanup may interrupt one of these IDs if it is still
        # active; it never guesses an ID for a scheduler-started turn.
        self.active_direct_turns: dict[str, str] = {}
        self.started_service = False
        self.service_start_attempted = False
        self.deadline = self.clock() + self.timeout_seconds
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
                "all_roles_baselined_before_service": False,
                "baseline_history_read_after_idle": False,
                "job_delivery": False,
                "manager_delivery": False,
                "manager_is_fixture_only": False,
                "turn_budget": False,
                "quiet_window_no_duplicate_starts": False,
                "idle_executors_received_no_turn": False,
            },
            "resources": {"tasks": {}, "threads": {}, "jobs": {}, "turns": {}},
            "history": {},
            "turn_counts": {},
            "cleanup": {
                "service": "not_started",
                "jobs": "not_started",
                "tasks": "not_started",
                "threads": "not_started",
                "thread_interrupt": {},
                "thread_archive": {},
            },
        }

    def _deadline(self) -> float:
        return self.deadline

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
        for role in _ROLE_ORDER:
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

    def _read_thread(self, thread_id: str, *, include_turns: bool) -> Mapping[str, Any]:
        return _mapping(
            self._request("thread/read", {"threadId": thread_id, "includeTurns": include_turns}),
            "App Server thread/read",
        )

    def _read_status(self, thread_id: str) -> str:
        return _thread_status(self._read_thread(thread_id, include_turns=False))

    def _resume_if_not_loaded(self, thread_id: str, status: str) -> str:
        if status != "notLoaded":
            return status
        self._request("thread/resume", {"threadId": thread_id, "excludeTurns": True})
        return self._read_status(thread_id)

    def _wait_for_idle(self, role: str, label: str, *, deadline: float | None = None) -> None:
        """Wait on metadata only; paging an active baseline is not valid evidence."""

        deadline = self._deadline() if deadline is None else deadline
        thread_id = self.threads[role]
        while True:
            status = self._resume_if_not_loaded(thread_id, self._read_status(thread_id))
            if status == "idle":
                return
            if _status_is_interrupted(status):
                raise LiveProbeError(f"fixture {label} thread entered {status}; it was not restarted")
            if status != "active":
                raise LiveProbeError(f"fixture {label} thread returned unexpected status {status!r}")
            self._expired(deadline, label)
            self.sleeper(min(POLL_SECONDS, max(0.0, deadline - self.clock())))

    def _thread_turns(self, thread_id: str) -> list[Mapping[str, Any]]:
        result = self._request(
            "thread/turns/list",
            {"threadId": thread_id, "limit": 16, "sortDirection": "desc", "itemsView": "full"},
        )
        return _turns(result)

    def _history_key(self, role: str, phase: str) -> str:
        return f"{role}:{phase}"

    def _record_paged_history(self, role: str, phase: str, turns: list[Mapping[str, Any]]) -> None:
        self.evidence["history"][self._history_key(role, phase)] = {
            "status_before_paged_history": "idle",
            "thread_turns_list": {"result": "ok", "count": len(turns), "turns": _turn_summaries(turns)},
        }

    def _compare_include_turns_after_paging_failure(
        self, role: str, phase: str, page_error: LiveProbeError
    ) -> str:
        """Record the required same-thread API comparison before failing once."""

        record: dict[str, Any] = {
            "status_before_paged_history": "idle",
            "thread_turns_list": {"result": "unsupported", "error": _redact(page_error)},
        }
        try:
            turns = _included_turns(self._read_thread(self.threads[role], include_turns=True))
        except LiveProbeError as exc:
            detail = _redact(exc)
            record["thread_read_include_turns"] = {"result": "failed", "error": detail}
            comparison = f"failed: {detail}"
        else:
            record["thread_read_include_turns"] = {
                "result": "ok",
                "count": len(turns),
                "turns": _turn_summaries(turns),
            }
            comparison = f"returned {len(turns)} turns"
        self.evidence["history"][self._history_key(role, phase)] = record
        return comparison

    def _thread_turns_after_idle(self, role: str, phase: str) -> list[Mapping[str, Any]]:
        """Page only after metadata is idle, or produce the one required comparison."""

        try:
            return self._thread_turns(self.threads[role])
        except LiveProbeError as exc:
            if not _is_paged_history_unsupported(exc):
                raise
            comparison = self._compare_include_turns_after_paging_failure(role, phase, exc)
            raise LiveProbeError(
                f"fixture {role} was idle but thread/turns/list is unsupported during {phase}; "
                f"thread/read(includeTurns=true) {comparison}"
            ) from exc

    def _wait_for_turn_text(
        self, role: str, expected: list[str], minimum_turns: int, label: str, phase: str
    ) -> Mapping[str, Any]:
        deadline = self._deadline()
        while True:
            self._wait_for_idle(role, label, deadline=deadline)
            turns = self._thread_turns_after_idle(role, phase)
            if len(turns) >= minimum_turns:
                for turn in turns:
                    text = _turn_text(turn)
                    if all(item in text for item in expected) and turn.get("status") == "completed":
                        self._record_paged_history(role, phase, turns)
                        return turn
            self._expired(deadline, label)
            self.sleeper(min(POLL_SECONDS, max(0.0, deadline - self.clock())))

    def _start_baseline_turn(self, role: str) -> None:
        self.stage = f"start fixture {role} baseline turn"
        if role != "manager" and not self.evidence["checks"]["executor_bound_before_first_model_turn"]:
            raise LiveProbeError("fixture executor was not bound before its first model turn")
        marker = _BASELINE_MARKERS[role]
        result = self._request(
            "turn/start",
            {
                "threadId": self.threads[role],
                "input": [{"type": "text", "text": f"Reply exactly {marker}."}],
                "model": MODEL,
                "effort": EFFORT,
            },
        )
        response = _mapping(result, "App Server turn/start")
        turn = response.get("turn")
        if not isinstance(turn, Mapping):
            raise LiveProbeError(f"fixture {role} baseline turn/start returned no turn")
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            raise LiveProbeError(f"fixture {role} baseline turn/start returned no turn id")
        self.evidence["calls"]["direct_turn_start"] += 1
        if self.evidence["calls"]["direct_turn_start"] > len(_ROLE_ORDER):
            raise LiveProbeError("fixture attempted more direct baseline turns than its fixed role set")
        self.active_direct_turns[role] = turn_id
        self.evidence["resources"]["turns"][f"{role}_baseline_started"] = turn_id
        self._wait_for_idle(role, f"fixture {role} baseline completion")
        turns = self._thread_turns_after_idle(role, "baseline")
        completed = next((item for item in turns if item.get("id") == turn_id), None)
        if not isinstance(completed, Mapping) or completed.get("status") != "completed":
            raise LiveProbeError(f"fixture {role} baseline did not complete under its acknowledged turn id")
        if marker not in _turn_text(completed):
            raise LiveProbeError(f"fixture {role} baseline history lacks its requested marker")
        self._record_paged_history(role, "baseline", turns)
        self.active_direct_turns.pop(role, None)
        self.evidence["resources"]["turns"][f"{role}_baseline_completed"] = turn_id

    def _start_all_baseline_turns(self) -> None:
        self.stage = "materialize all dedicated fixture roles"
        for role in _ROLE_ORDER:
            self._start_baseline_turn(role)
        self.evidence["checks"]["all_roles_baselined_before_service"] = True
        self.evidence["checks"]["baseline_history_read_after_idle"] = True

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
        manager_turn = self._wait_for_turn_text(
            "manager", manager_payloads, 2, "Manager-ready scheduler turn", "manager_delivery"
        )
        manager_turn_id = manager_turn.get("id")
        if not isinstance(manager_turn_id, str) or not manager_turn_id:
            raise LiveProbeError("Manager-ready scheduler delivery returned no turn id")
        self.evidence["resources"]["turns"]["manager_ready_delivery"] = manager_turn_id
        self.evidence["checks"]["manager_delivery"] = True

    def _turn_counts_after_idle(self, phase: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        deadline = self._deadline()
        for role in _ROLE_ORDER:
            self._wait_for_idle(role, f"fixture {role} {phase} count", deadline=deadline)
            turns = self._thread_turns_after_idle(role, phase)
            self._record_paged_history(role, phase, turns)
            counts[role] = len(turns)
        self.evidence["turn_counts"][phase] = counts
        return counts

    def _verify_baseline_only_executors(self) -> None:
        self.stage = "verify fixture executors received no pre-stop scheduler turn"
        expected = {"manager": 2, "job_executor": 1, "idle_executor": 1, "archived_executor": 1}
        counts = self._turn_counts_after_idle("before_job_stop")
        if counts != expected:
            raise LiveProbeError(f"fixture pre-stop turn distribution is unexpected: {counts}")
        self.evidence["checks"]["idle_executors_received_no_turn"] = True

    def _wait_for_stopped_job_delivery(self, job_id: str, note: str) -> dict[str, int]:
        self.stage = "verify stopped-job scheduler delivery"
        job_payload = (
            f"Stopped registered job: JOB-ID {job_id} ({note}); "
            f"TASK-ID {self.tasks['job']}: MAM liveprobe stopped-job delivery."
        )
        job_turn = self._wait_for_turn_text(
            "job_executor", [job_payload], 2, "stopped-job scheduler turn", "stopped_job_delivery"
        )
        job_turn_id = job_turn.get("id")
        if not isinstance(job_turn_id, str) or not job_turn_id:
            raise LiveProbeError("stopped-job scheduler delivery returned no turn id")
        self.evidence["resources"]["turns"]["stopped_job_delivery"] = job_turn_id
        self.evidence["checks"]["job_delivery"] = True
        counts = self._turn_counts_after_idle("after_job_stop")
        expected = {"manager": 2, "job_executor": 2, "idle_executor": 1, "archived_executor": 1}
        if counts != expected:
            raise LiveProbeError(f"fixture model turn distribution is unexpected: {counts}")
        observed = sum(counts.values())
        if observed > MAX_MODEL_TURNS:
            raise LiveProbeError(
                f"fixture observed {observed} model turns, exceeding the fixed acceptance limit of {MAX_MODEL_TURNS}"
            )
        if observed != MAX_MODEL_TURNS:
            raise LiveProbeError(f"fixture did not produce the required {MAX_MODEL_TURNS}-turn acceptance distribution: {counts}")
        self.evidence["checks"]["turn_budget"] = True
        self.evidence["model_turns"] = observed
        return counts

    def _scheduler_interval(self) -> float:
        raw = getattr(self.runtime, "POLL_SECONDS", POLL_SECONDS)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or raw <= 0:
            raw = POLL_SECONDS
        return min(max(float(raw), POLL_SECONDS), 30.0) + POLL_SECONDS

    def _verify_quiet_window(self, expected: Mapping[str, int]) -> None:
        self.stage = "verify unchanged fixture quiet window"
        # Check across two actual daemon polling windows.  No fixture records
        # change after the stopped job has been delivered, so another start is
        # an observable duplicate rather than a timing assumption.
        for index in range(1, 3):
            deadline = self._deadline()
            self.sleeper(min(self._scheduler_interval(), max(0.0, deadline - self.clock())))
            self._expired(deadline, "fixture quiet window")
            observed = self._turn_counts_after_idle(f"quiet_window_{index}")
            if observed != dict(expected):
                raise LiveProbeError(f"fixture quiet window started unexpected additional turns: {observed}")
        self.evidence["checks"]["quiet_window_no_duplicate_starts"] = True

    def run(self) -> dict[str, Any]:
        self._create_tasks()
        self._connect()
        self._create_and_bind_threads()
        self._start_all_baseline_turns()
        job_id, note = self._register_jobs()
        self._start_service()
        self._wait_for_service()
        self._wait_for_manager_delivery()
        self._verify_baseline_only_executors()
        # Releasing EOF makes this fixture-owned, already-registered local
        # process finish.  The detached scheduler must later observe the stop
        # itself; this module does not refresh the job record on its behalf.
        self._release_blocker(self.blockers[0])
        counts = self._wait_for_stopped_job_delivery(job_id, note)
        self._verify_quiet_window(counts)
        self.evidence["status"] = "passed"
        return self.evidence

    def _interrupt_known_direct_turn(self, role: str, thread_id: str) -> None:
        """Interrupt only a direct baseline turn whose ID this fixture recorded."""

        status = self._read_status(thread_id)
        if status != "active":
            self.evidence["cleanup"]["thread_interrupt"][role] = "not_needed"
            return
        turn_id = self.active_direct_turns.get(role)
        if not turn_id:
            # A scheduler delivery may be active, but it did not reply on this
            # stream with an ID we can safely target.  Archive still remains
            # limited to this fixture-owned thread and its result is recorded.
            self.evidence["cleanup"]["thread_interrupt"][role] = "not_attempted_unknown_active_turn"
            return
        self._request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
        self.evidence["cleanup"]["thread_interrupt"][role] = "interrupted_known_direct_baseline"

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
                        self._interrupt_known_direct_turn(role, thread_id)
                        self._request("thread/archive", {"threadId": thread_id})
                        self.evidence["cleanup"]["thread_archive"][role] = "archived"
                    except Exception as exc:
                        thread_errors = True
                        detail = _redact(exc)
                        self.evidence["cleanup"]["thread_archive"][role] = f"failed: {detail}"
                        errors.append(f"thread cleanup ({role}): {detail}")
                self.evidence["cleanup"]["threads"] = "partial" if thread_errors else "archived"
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
