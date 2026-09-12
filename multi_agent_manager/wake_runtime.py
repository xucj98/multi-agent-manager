"""Durable, project-local proactive wakeup scheduling.

The service deliberately keeps task discovery separate from delivery.  It
uses metadata-only App Server reads while monitoring and resumes exactly one
idle recipient immediately before starting a wakeup turn.  This avoids
hydrating historical threads merely to find work.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from typing import Any

from . import job_runtime
from .cli import ProjectConfig, Store, safe_path


SERVICE_VERSION = 1
POLL_SECONDS = 10.0
JOB_PROBE_SECONDS = 30.0
RETRY_BASE_SECONDS = 5.0
RETRY_MAX_SECONDS = 300.0
COMPATIBILITY_RETRY_SECONDS = 30.0
HISTORY_LIMIT = 256
STARTUP_TIMEOUT_SECONDS = 5.0
STARTUP_POLL_SECONDS = 0.05
_EVENT_CURRENT = "current"
_EVENT_STALE = "stale"
_EVENT_UNVERIFIABLE = "unverifiable"
_LOCAL_START_LOCKS: dict[str, threading.Lock] = {}
_LOCAL_START_LOCKS_GUARD = threading.Lock()
_DETACHED_CHILDREN: list[subprocess.Popen[bytes]] = []


class WakeRuntimeError(RuntimeError):
    """A configuration or durable wake-service failure."""


@contextlib.contextmanager
def _service_start_lock(store: Store):
    """Serialize same-process callers as well as separate daemon clients."""

    key = str(store.root)
    with _LOCAL_START_LOCKS_GUARD:
        lock = _LOCAL_START_LOCKS.setdefault(key, threading.Lock())
    with lock, store.lock("service-start"):
        yield


def _timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _valid_agent(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and not any(
        character in value for character in "\r\n\t"
    )


def _canonical_agent(value: Any) -> str | None:
    if not _valid_agent(value):
        return None
    try:
        return value if str(uuid.UUID(value)) == value else None
    except (ValueError, AttributeError):
        return None


def _service_directory(store: Store) -> Path:
    directory = safe_path(store.root / ".local" / "service")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _service_path(store: Store, name: str) -> Path:
    if name not in {"state.json", "manager.json", "service.log"}:
        raise WakeRuntimeError(f"unknown service state file: {name}")
    return safe_path(_service_directory(store) / name)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise WakeRuntimeError(f"service state is not a regular file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise WakeRuntimeError(f"invalid service state {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WakeRuntimeError(f"invalid service state {path}: expected an object")
    return data


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, encoding="utf-8", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _project(config: ProjectConfig) -> dict[str, str]:
    return {
        "mam_root": str(config.mam_root),
        "project_root": str(config.project_root),
        "branch": config.branch,
    }


def _default_state(config: ProjectConfig) -> dict[str, Any]:
    return {
        "version": SERVICE_VERSION,
        "project": _project(config),
        "enabled": False,
        "mode": "disabled",
        "manager": None,
        "pid": None,
        "identity": None,
        "token": None,
        "started_at": None,
        "ready_at": None,
        "stopped_at": None,
        "heartbeat_at": None,
        "healthy": False,
        "error": None,
        "compatibility": None,
        "events": {},
        "history": [],
        "job_schedule": {},
        "diagnostics": [],
        "counters": {"cycles": 0, "observed": 0, "queued": 0, "accepted": 0, "turn_start_attempts": 0},
    }


def _load_state(store: Store) -> dict[str, Any]:
    state = _read_json(_service_path(store, "state.json"))
    if state is None:
        return _default_state(store.config)
    if state.get("version") != SERVICE_VERSION or state.get("project") != _project(store.config):
        raise WakeRuntimeError("service state belongs to another MAM project or has an unsupported version")
    for key, value in _default_state(store.config).items():
        state.setdefault(key, value)
    if not isinstance(state.get("events"), dict) or not isinstance(state.get("history"), list):
        raise WakeRuntimeError("service state has invalid delivery bookkeeping")
    if not isinstance(state.get("job_schedule"), dict) or not isinstance(state.get("counters"), dict):
        raise WakeRuntimeError("service state has invalid scheduler bookkeeping")
    return state


def _save_state(store: Store, state: dict[str, Any]) -> None:
    state["version"] = SERVICE_VERSION
    state["project"] = _project(store.config)
    _write_json(_service_path(store, "state.json"), state)


def _manager_record(store: Store) -> dict[str, Any] | None:
    record = _read_json(_service_path(store, "manager.json"))
    if record is None:
        return None
    if not _valid_agent(record.get("manager")):
        raise WakeRuntimeError("recorded service manager is invalid")
    return record


def recorded_manager(store: Store) -> str | None:
    record = _manager_record(store)
    return record["manager"] if record else None


def _active_bindings(store: Store) -> set[str]:
    return {
        data["agent"]
        for data in store.all()
        if data.get("status") != "archived" and _valid_agent(data.get("agent"))
    }


def _has_bound_tasks(store: Store) -> bool:
    return bool(_active_bindings(store))


def _record_manager(store: Store, manager: str, *, source: str) -> str:
    if not _valid_agent(manager):
        raise WakeRuntimeError("manager must be a non-empty single-line AGENT-ID")
    with store.lock("service-manager"):
        existing = _manager_record(store)
        if existing and existing["manager"] != manager:
            raise WakeRuntimeError(
                "a different Manager is already recorded for this project; refusing to select another project manager"
            )
        if manager in _active_bindings(store):
            raise WakeRuntimeError("the requested Manager is bound to an active task")
        if not existing:
            _write_json(_service_path(store, "manager.json"), {"manager": manager, "source": source, "recorded_at": _timestamp()})
    return manager


def resolve_manager(store: Store, manager: str | None = None) -> str | None:
    """Resolve only an explicit or persisted project-local manager identity."""

    if manager is not None:
        return _record_manager(store, manager, source="explicit service start")
    existing = recorded_manager(store)
    if existing is not None:
        if existing in _active_bindings(store):
            raise WakeRuntimeError("recorded Manager is bound to an active task")
        return existing
    return None


def capture_manager_for_task(store: Store, *, excluded_agent: str | None = None) -> str | None:
    """Capture ``CODEX_THREAD_ID`` only for an unbound Manager action.

    ``task create`` and ``task bind`` call this helper.  A task executor (and
    the agent being bound) is deliberately never promoted to Manager.
    """

    caller = _canonical_agent(os.environ.get("CODEX_THREAD_ID"))
    if caller is None:
        return recorded_manager(store)
    if caller == excluded_agent or caller in _active_bindings(store):
        return recorded_manager(store)
    existing = recorded_manager(store)
    if existing is not None:
        return existing
    return _record_manager(store, caller, source="unbound Manager task create/bind")


def _compatibility() -> dict[str, Any]:
    try:
        from . import wake_compat
    except ImportError as exc:
        raise WakeRuntimeError("multi_agent_manager.wake_compat is required before service delivery can start") from exc
    try:
        result = wake_compat.require_compatible()
    except RuntimeError as exc:
        raise WakeRuntimeError(str(exc)) from exc
    if not isinstance(result, Mapping):
        raise WakeRuntimeError("wake compatibility check returned no mapping")
    socket_path = result.get("socket_path")
    if not isinstance(socket_path, str) or not socket_path or not Path(socket_path).is_absolute():
        raise WakeRuntimeError("wake compatibility check returned an invalid App Server socket path")
    return dict(result)


def _probe_service_process(state: Mapping[str, Any]) -> tuple[bool, str | None]:
    pid, identity = state.get("pid"), state.get("identity")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0 or not isinstance(identity, Mapping):
        return False, "service process identity is unavailable"
    try:
        observed = job_runtime.probe_process("local", pid, dict(identity))
    except Exception as exc:
        return False, f"cannot inspect service process: {exc}"
    if observed.get("status") == "running":
        return True, None
    if observed.get("status") == "unknown":
        return False, observed.get("error") or "cannot verify service process identity"
    return False, "service process is no longer running"


def _pending_events(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    events = state.get("events")
    if not isinstance(events, Mapping):
        return []
    return [
        {key: value for key, value in event.items() if key not in {"signature", "payload"}}
        for event in events.values()
        if isinstance(event, Mapping) and event.get("delivery") != "accepted"
    ]


def _status_mapping(store: Store, state: dict[str, Any]) -> dict[str, Any]:
    alive, process_error = _probe_service_process(state) if state.get("pid") is not None else (False, None)
    pending = _pending_events(state)
    if state.get("mode") == "awaiting_manager" and state.get("enabled") and alive:
        status = "awaiting_manager"
    elif state.get("error"):
        status = "error"
    elif not state.get("enabled"):
        status = "disabled"
    elif not alive:
        status = "error"
    elif pending or not state.get("ready_at") or not state.get("healthy"):
        status = "pending"
    else:
        status = "healthy"
    result = {
        "status": status,
        "running": alive,
        "healthy": bool(alive and state.get("healthy") and not state.get("error")),
        "manager": recorded_manager(store),
        "mode": state.get("mode"),
        "pending": {"count": len(pending), "events": pending},
        "counters": dict(state.get("counters") or {}),
        "heartbeat_at": state.get("heartbeat_at"),
        "ready_at": state.get("ready_at"),
    }
    error = state.get("error") or process_error
    if error:
        result["error"] = error
    if state.get("diagnostics"):
        result["diagnostics"] = list(state["diagnostics"])
    return result


def service_status(config: ProjectConfig) -> dict[str, Any]:
    """Return JSON-serializable service state without creating a daemon."""

    store = Store(config)
    with store.lock("service-state"):
        state = _load_state(store)
        return _status_mapping(store, state)


def _spawn_service(config: ProjectConfig, token: str, log_path: Path) -> subprocess.Popen[bytes]:
    environment = os.environ.copy()
    # The detached scheduler is not a Manager action and must never capture
    # the caller's thread identity through an inherited environment.
    environment.pop("CODEX_THREAD_ID", None)
    command = [
        sys.executable,
        "-m",
        "multi_agent_manager.wake_runtime",
        "--service",
        "--mam-root",
        str(config.mam_root),
        "--project-root",
        str(config.project_root),
        "--branch",
        config.branch,
        "--token",
        token,
    ]
    with log_path.open("ab") as log:
        return subprocess.Popen(
            command,
            cwd=config.mam_root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )


def _retain_detached_child(process: Any) -> None:
    """Keep local ``Popen`` wrappers alive until their detached child exits.

    The durable PID/identity record remains the source of truth.  Retaining a
    wrapper only prevents Python from emitting a misleading ResourceWarning
    while a deliberately detached child is still alive in a long-lived caller.
    """

    if not isinstance(process, subprocess.Popen):
        return
    live: list[subprocess.Popen[bytes]] = []
    for child in _DETACHED_CHILDREN:
        with contextlib.suppress(Exception):
            child.poll()
        if child.returncode is None:
            live.append(child)
    live.append(process)
    _DETACHED_CHILDREN[:] = live


def _await_daemon_ready(store: Store, token: str, pid: int) -> dict[str, Any]:
    """Wait until the child has verified its persisted project identity.

    The marker is intentionally written before the child enters its first
    scheduler cycle, which needs the parent's service-start lock.  It proves
    that a detached child, rather than only ``Popen``, has observed the exact
    token, PID and identity persisted by its parent.  A readiness timeout
    disables that attempted generation so a late child exits without delivery.
    """

    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while True:
        with store.lock("service-state"):
            state = _load_state(store)
        if state.get("token") != token or state.get("pid") != pid:
            raise WakeRuntimeError("detached service startup identity changed before readiness")
        if not state.get("enabled"):
            raise WakeRuntimeError(state.get("error") or "detached service stopped before readiness")
        if state.get("ready_at"):
            alive, detail = _probe_service_process(state)
            if alive:
                return state
            if detail == "service process is no longer running":
                break
        if time.monotonic() >= deadline:
            break
        time.sleep(STARTUP_POLL_SECONDS)

    message = "detached service did not signal verified startup readiness"
    with store.lock("service-state"):
        state = _load_state(store)
        if state.get("token") == token and state.get("pid") == pid:
            state.update({"enabled": False, "mode": "error", "healthy": False, "error": message, "stopped_at": _timestamp()})
            _save_state(store, state)
    raise WakeRuntimeError(message)


def _startup_compatibility(store: Store, state: dict[str, Any]) -> dict[str, Any]:
    """Run the installer-owned check and leave a durable status on failure."""

    try:
        return _compatibility()
    except Exception as exc:
        message = f"wake compatibility/reconnection failed: {exc}"
        state.update({"mode": "error", "healthy": False, "error": message})
        _save_state(store, state)
        raise WakeRuntimeError(message) from exc


def start_service(config: ProjectConfig, manager: str | None = None) -> dict[str, Any]:
    """Start one detached scheduler for ``config`` or return its live status.

    A fresh project with no bound task is allowed to run in
    ``awaiting_manager`` mode.  A project that already has task executors but
    lacks a trustworthy manager fails rather than guessing an arbitrary
    thread.
    """

    store = Store(config)
    with _service_start_lock(store):
        selected = resolve_manager(store, manager)
        state = _load_state(store)
        alive, process_error = _probe_service_process(state) if state.get("pid") is not None else (False, None)
        if alive:
            if not state.get("enabled"):
                raise WakeRuntimeError("the previous detached service is still stopping; wait for it before starting another")
            if selected is None:
                if _has_bound_tasks(store):
                    message = "existing bound tasks have no determinable Manager; run mam service start --manager AGENT-ID"
                    state.update({"mode": "error", "healthy": False, "error": message})
                    _save_state(store, state)
                    raise WakeRuntimeError(message)
                state.update({"manager": None, "mode": "awaiting_manager", "healthy": True, "error": None})
                _save_state(store, state)
                return _status_mapping(store, state)
            previous_mode = state.get("mode")
            compatibility = _startup_compatibility(store, state)
            state["manager"] = selected
            state["mode"] = "active"
            if previous_mode != "active":
                state["healthy"] = False
            state["error"] = None
            state["compatibility"] = _public_compatibility(compatibility)
            _save_state(store, state)
            return _status_mapping(store, state)

        # A PID that cannot be verified may still be a live scheduler.  Never
        # launch a second daemon merely because a local process inspection is
        # transiently unavailable or the saved identity is malformed.
        if state.get("pid") is not None and process_error != "service process is no longer running":
            message = f"cannot verify existing detached service identity: {process_error or 'unknown error'}; refusing to start another"
            state.update({"mode": "error", "healthy": False, "error": message})
            _save_state(store, state)
            raise WakeRuntimeError(message)

        if selected is None and _has_bound_tasks(store):
            state.update({
                "enabled": False,
                "mode": "error",
                "healthy": False,
                "error": "existing bound tasks have no determinable Manager; run mam service start --manager AGENT-ID",
                "stopped_at": _timestamp(),
            })
            _save_state(store, state)
            raise WakeRuntimeError(state["error"])

        compatibility = None
        if selected is not None:
            # Do this once at service startup.  The daemon repeats it only
            # when a control connection needs to be re-established.
            compatibility = _startup_compatibility(store, state)

        token = str(uuid.uuid4())
        state.update({
            "enabled": True,
            "mode": "active" if selected is not None else "awaiting_manager",
            "manager": selected,
            "pid": None,
            "identity": None,
            "token": token,
            "started_at": _timestamp(),
            "ready_at": None,
            "stopped_at": None,
            "heartbeat_at": None,
            "healthy": False,
            "error": None,
            "compatibility": _public_compatibility(compatibility),
        })
        _save_state(store, state)
        try:
            process = _spawn_service(config, token, _service_path(store, "service.log"))
        except OSError as exc:
            state.update({"enabled": False, "mode": "error", "healthy": False, "error": f"cannot start detached service: {exc}"})
            _save_state(store, state)
            raise WakeRuntimeError(state["error"]) from exc
        _retain_detached_child(process)
        observed = job_runtime.probe_process("local", process.pid)
        state["pid"] = process.pid
        state["identity"] = observed.get("identity") if observed.get("status") == "running" else None
        if state["identity"] is None:
            state.update({
                "enabled": False,
                "mode": "error",
                "healthy": False,
                "error": f"cannot confirm detached service identity: {observed.get('error') or observed}",
            })
        _save_state(store, state)
        if state["identity"] is None:
            raise WakeRuntimeError(state["error"])
        return _status_mapping(store, _await_daemon_ready(store, token, process.pid))


def stop_service(config: ProjectConfig) -> dict[str, Any]:
    """Request a graceful stop of this project's scheduler only."""

    store = Store(config)
    with _service_start_lock(store):
        state = _load_state(store)
        alive, _ = _probe_service_process(state) if state.get("enabled") else (False, None)
        state.update({"enabled": False, "mode": "disabled", "healthy": False, "error": None, "stopped_at": _timestamp()})
        _save_state(store, state)
        if alive and isinstance(state.get("pid"), int):
            try:
                os.kill(state["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass
            except OSError as exc:
                state["error"] = f"cannot signal detached service: {exc}"
                _save_state(store, state)
                raise WakeRuntimeError(state["error"]) from exc
        return _status_mapping(store, state)


def _public_compatibility(result: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {key: result[key] for key in ("capabilities", "diagnostics") if key in result}


def _status_from_snapshot(snapshot: Any, agent: str) -> str | None:
    thread = snapshot.get("thread") if isinstance(snapshot, Mapping) else None
    if not isinstance(thread, Mapping) or thread.get("id") != agent:
        return None
    raw = thread.get("status")
    status = raw.get("type") if isinstance(raw, Mapping) else raw
    return status if isinstance(status, str) else None


def _event_signature(data: Mapping[str, Any]) -> str:
    encoded = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _retry_after(clock: float, attempts: int) -> float:
    return clock + min(RETRY_MAX_SECONDS, RETRY_BASE_SECONDS * (2 ** min(max(attempts - 1, 0), 8)))


class WakeScheduler:
    """One durable scheduler loop, parameterized for deterministic tests."""

    def __init__(
        self,
        store: Store,
        *,
        compatibility: Callable[[], Mapping[str, Any]] | None = None,
        process_probe: Callable[[str, int, dict[str, Any] | None], Mapping[str, Any]] | None = None,
        agent_probe: Callable[[list[str], str | None], Mapping[str, Mapping[str, Any]]] | None = None,
        stream_factory: Callable[[str | None], Any] = job_runtime.AppServerEventStream.connect,
        clock: Callable[[], float] = time.time,
        job_probe_seconds: float = JOB_PROBE_SECONDS,
    ) -> None:
        self.store = store
        self.compatibility = compatibility or _compatibility
        self.process_probe = process_probe or job_runtime.probe_process
        self.agent_probe = agent_probe or (lambda agents, socket_path: job_runtime.probe_agents(agents, socket_path))
        self.stream_factory = stream_factory
        self.clock = clock
        self.job_probe_seconds = job_probe_seconds
        self.manager: str | None = None
        self.socket_path: str | None = None
        self.compatibility_ready = False
        self.next_compatibility_retry = 0.0

    def _load_tasks(self) -> list[dict[str, Any]]:
        tasks: list[dict[str, Any]] = []
        for listed in self.store.all():
            task_id = listed.get("id")
            if not isinstance(task_id, str):
                continue
            with self.store.lock(task_id):
                data = self.store.read(task_id)
            if data.get("status") != "archived":
                tasks.append(data)
        return tasks

    @staticmethod
    def _unarchived_jobs(task: Mapping[str, Any]) -> list[dict[str, Any]]:
        jobs = task.get("jobs")
        return [job for job in jobs if isinstance(job, dict) and job.get("status") != "archived"] if isinstance(jobs, list) else []

    @staticmethod
    def _job_stopped(job: Mapping[str, Any]) -> bool:
        probe = job.get("probe")
        return job.get("status") == "stopped" or isinstance(probe, Mapping) and probe.get("status") == "stopped"

    def _probe_jobs(self, state: dict[str, Any], tasks: list[dict[str, Any]]) -> None:
        schedule = state.setdefault("job_schedule", {})
        now = self.clock()
        live_keys: set[str] = set()
        for task in tasks:
            task_id = task.get("id")
            if not isinstance(task_id, str):
                continue
            for job in self._unarchived_jobs(task):
                job_id = job.get("id")
                if not isinstance(job_id, str):
                    continue
                key = f"{task_id}:{job_id}"
                live_keys.add(key)
                if self._job_stopped(job):
                    schedule.pop(key, None)
                    continue
                try:
                    due = float(schedule.get(key, 0.0))
                except (TypeError, ValueError):
                    due = 0.0
                if due > now:
                    continue
                schedule[key] = now + self.job_probe_seconds
                try:
                    observation = self.process_probe(job.get("host"), job.get("pid"), job.get("identity"))
                except Exception as exc:
                    observation = {"status": "unknown", "checked_at": _timestamp(), "error": str(exc)}
                if not isinstance(observation, Mapping) or not isinstance(observation.get("status"), str):
                    observation = {"status": "unknown", "checked_at": _timestamp(), "error": "invalid process probe result"}
                # Re-read while holding the task lock.  A concurrent archive or
                # replacement wins over this stale observation.
                with self.store.lock(task_id):
                    fresh = self.store.read(task_id)
                    if fresh.get("status") == "archived":
                        continue
                    current = next((item for item in self._unarchived_jobs(fresh) if item.get("id") == job_id), None)
                    if current is None:
                        continue
                    current["probe"] = dict(observation)
                    if observation.get("status") in {"running", "stopped"}:
                        current["status"] = observation["status"]
                        if observation.get("checked_at") is not None:
                            current["checked_at"] = observation["checked_at"]
                    identity = observation.get("identity")
                    if not current.get("started_at") and isinstance(identity, Mapping) and identity.get("started_at"):
                        current["started_at"] = identity["started_at"]
                    self.store.write(fresh)
        for key in list(schedule):
            if key not in live_keys:
                schedule.pop(key, None)

    @staticmethod
    def _review_graph(tasks: list[dict[str, Any]]) -> tuple[set[str], list[dict[str, str]]]:
        by_id = {task.get("id"): task for task in tasks if isinstance(task.get("id"), str)}
        edges: dict[str, str] = {}
        diagnostics: list[dict[str, str]] = []
        for task in tasks:
            review = task.get("review")
            if not isinstance(review, Mapping):
                continue
            source = review.get("task")
            task_id = task.get("id")
            if not isinstance(source, str) or source not in by_id:
                diagnostics.append({"kind": "unknown_review_source", "task": str(task_id), "message": "review source is not an active local task"})
            else:
                edges[str(task_id)] = source
        cycles: set[str] = set()
        for root in edges:
            seen: list[str] = []
            current = root
            while current in edges:
                if current in seen:
                    cycles.update(seen[seen.index(current) :])
                    break
                seen.append(current)
                current = edges[current]
        if cycles:
            diagnostics.append({"kind": "review_cycle", "task": ",".join(sorted(cycles)), "message": "unarchived review links contain a cycle"})
        suppressed = {source for reviewer, source in edges.items() if reviewer not in cycles and source not in cycles}
        return suppressed, diagnostics

    def _agent_states(self, agents: set[str]) -> dict[str, dict[str, Any]]:
        if not agents:
            return {}
        try:
            result = self.agent_probe(sorted(agents), self.socket_path)
        except Exception as exc:
            return {agent: {"status": "unknown", "error": str(exc)} for agent in agents}
        if not isinstance(result, Mapping):
            return {agent: {"status": "unknown", "error": "invalid App Server agent probe result"} for agent in agents}
        states: dict[str, dict[str, Any]] = {}
        for agent in agents:
            entry = result.get(agent)
            states[agent] = dict(entry) if isinstance(entry, Mapping) else {"status": "unknown", "error": "agent state unavailable"}
        return states

    def _make_event(self, kind: str, recipient: str, **fields: Any) -> dict[str, Any]:
        payload = {"kind": kind, "recipient": recipient, **fields}
        return {"signature": _event_signature(payload), **payload}

    def _task_ready_event(self, task: Mapping[str, Any], task_id: str, title: str, executor: str) -> dict[str, Any] | None:
        if self.manager is None:
            return None
        report = task.get("report") if isinstance(task.get("report"), Mapping) else {}
        return self._make_event(
            "task_ready",
            self.manager,
            task=task_id,
            task_title=title,
            executor=executor,
            task_status=task.get("status"),
            report_revision=report.get("revision"),
        )

    def _desired_events(
        self, tasks: list[dict[str, Any]], states: Mapping[str, Mapping[str, Any]]
    ) -> tuple[dict[str, dict[str, Any]], set[str], list[dict[str, str]]]:
        desired: dict[str, dict[str, Any]] = {}
        inconclusive: set[str] = set()
        suppressed, diagnostics = self._review_graph(tasks)
        for task in tasks:
            task_id, title = task.get("id"), task.get("title")
            if not isinstance(task_id, str) or not isinstance(title, str):
                diagnostics.append({"kind": "invalid_task", "task": str(task_id), "message": "task record lacks id or title"})
                continue
            agent = task.get("agent") if _valid_agent(task.get("agent")) else None
            jobs = self._unarchived_jobs(task)
            stopped = [job for job in jobs if self._job_stopped(job)]
            if stopped:
                for job in stopped:
                    job_id, note = job.get("id"), job.get("note")
                    if not isinstance(job_id, str) or not isinstance(note, str):
                        diagnostics.append({"kind": "invalid_job", "task": task_id, "message": "stopped job lacks id or note"})
                        continue
                    recipient = agent or self.manager
                    if recipient is None:
                        diagnostics.append({"kind": "missing_executor", "task": task_id, "message": "stopped job has no executor or Manager"})
                        continue
                    event = self._make_event(
                        "job_stopped",
                        recipient,
                        task=task_id,
                        task_title=title,
                        job=job_id,
                        note=note,
                        executor=agent,
                    )
                    desired[event["signature"]] = event
                continue
            if jobs:
                for job in jobs:
                    probe = job.get("probe")
                    if isinstance(probe, Mapping) and probe.get("status") == "unknown":
                        diagnostics.append({"kind": "unknown_job", "task": task_id, "message": f"JOB-ID {job.get('id')} state is unknown"})
                # A running or uncertain job is monitoring work, never an
                # implicit Manager-ready signal.
                continue
            if agent is None:
                if self.manager is None:
                    diagnostics.append({"kind": "missing_executor", "task": task_id, "message": "task has no executor or Manager"})
                else:
                    event = self._make_event("task_unbound", self.manager, task=task_id, task_title=title)
                    desired[event["signature"]] = event
                continue
            agent_state = states.get(agent, {}).get("status")
            if agent_state in {"idle", "notLoaded"}:
                if task_id not in suppressed:
                    event = self._task_ready_event(task, task_id, title, agent)
                    if event is None:
                        diagnostics.append({"kind": "missing_manager", "task": task_id, "message": "ready executor has no recorded Manager"})
                    else:
                        desired[event["signature"]] = event
            elif agent_state != "active":
                if task_id not in suppressed:
                    event = self._task_ready_event(task, task_id, title, agent)
                    if event is None:
                        diagnostics.append({"kind": "missing_manager", "task": task_id, "message": "unverifiable executor has no recorded Manager"})
                    else:
                        # A failed or unknown source metadata read says nothing
                        # about whether an already accepted Manager signal was
                        # resolved.  Preserve an exact existing signature, but
                        # never create a new signal without a positive idle
                        # observation.
                        inconclusive.add(event["signature"])
                diagnostics.append(
                    {"kind": "unknown_executor", "task": task_id, "message": f"executor {agent} is {agent_state or 'unknown'}"}
                )
        return desired, inconclusive, diagnostics

    def _resolve_event(self, state: dict[str, Any], signature: str, *, reason: str) -> None:
        event = state.setdefault("events", {}).pop(signature, None)
        if not isinstance(event, Mapping):
            return
        history = state.setdefault("history", [])
        history.append({**dict(event), "resolved_at": _timestamp(), "resolution": reason})
        if len(history) > HISTORY_LIMIT:
            del history[:-HISTORY_LIMIT]

    def _reconcile_events(
        self, state: dict[str, Any], desired: Mapping[str, Mapping[str, Any]], inconclusive: set[str]
    ) -> None:
        events = state.setdefault("events", {})
        counters = state.setdefault("counters", {})
        for signature in list(events):
            if signature in inconclusive:
                existing = events.get(signature)
                if isinstance(existing, dict):
                    existing["last_condition_checked_at"] = _timestamp()
                    existing["last_condition_error"] = "source thread metadata is unavailable"
            elif signature not in desired:
                self._resolve_event(state, signature, reason="condition changed or resolved")
        for signature, current in desired.items():
            existing = events.get(signature)
            if not isinstance(existing, dict):
                events[signature] = {
                    **dict(current),
                    "created_at": _timestamp(),
                    "last_observed_at": _timestamp(),
                    "observed_count": 1,
                    "delivery": "pending",
                    "attempts": 0,
                    "next_attempt_at": 0.0,
                    "last_error": None,
                    "accepted_at": None,
                }
                counters["queued"] = int(counters.get("queued", 0)) + 1
            else:
                existing.update(dict(current))
                existing["last_observed_at"] = _timestamp()
                existing["observed_count"] = int(existing.get("observed_count", 0)) + 1
                existing.pop("last_condition_error", None)
            counters["observed"] = int(counters.get("observed", 0)) + 1

    def _source_suppressed_now(self, task_id: str) -> bool:
        tasks = self._load_tasks()
        suppressed, _ = self._review_graph(tasks)
        return task_id in suppressed

    def _event_is_current(self, event: Mapping[str, Any]) -> tuple[str, str | None]:
        """Classify an event without turning an unavailable read into resolution."""

        task_id = event.get("task")
        if not isinstance(task_id, str):
            return _EVENT_STALE, "event has no valid TASK-ID"
        try:
            with self.store.lock(task_id):
                task = self.store.read(task_id)
        except Exception as exc:
            return _EVENT_UNVERIFIABLE, f"cannot read TASK-ID {task_id}: {exc}"
        if task.get("status") == "archived":
            return _EVENT_STALE, "task is archived"
        kind = event.get("kind")
        if kind == "job_stopped":
            recipient = task.get("agent") if _valid_agent(task.get("agent")) else self.manager
            if recipient != event.get("recipient"):
                return _EVENT_STALE, "event recipient changed"
            job = next((item for item in self._unarchived_jobs(task) if item.get("id") == event.get("job")), None)
            if job and self._job_stopped(job) and job.get("note") == event.get("note") and task.get("title") == event.get("task_title"):
                return _EVENT_CURRENT, None
            return _EVENT_STALE, "stopped job condition changed"
        if kind == "task_unbound":
            if (
                not _valid_agent(task.get("agent"))
                and not self._unarchived_jobs(task)
                and self.manager == event.get("recipient")
                and task.get("title") == event.get("task_title")
            ):
                return _EVENT_CURRENT, None
            return _EVENT_STALE, "unbound task condition changed"
        if kind == "task_ready":
            executor = task.get("agent")
            report = task.get("report") if isinstance(task.get("report"), Mapping) else {}
            if (
                executor != event.get("executor")
                or self.manager != event.get("recipient")
                or self._unarchived_jobs(task)
                or task.get("title") != event.get("task_title")
                or task.get("status") != event.get("task_status")
                or report.get("revision") != event.get("report_revision")
            ):
                return _EVENT_STALE, "task-ready condition changed"
            try:
                if self._source_suppressed_now(task_id):
                    return _EVENT_STALE, "source task is under active review"
            except Exception as exc:
                return _EVENT_UNVERIFIABLE, f"cannot read review state for TASK-ID {task_id}: {exc}"
            source = self._agent_states({executor}).get(executor, {})
            source_state = source.get("status")
            if source_state in {"idle", "notLoaded"}:
                return _EVENT_CURRENT, None
            if source_state == "active":
                return _EVENT_STALE, "executor is active"
            detail = source.get("error") if isinstance(source.get("error"), str) else None
            return _EVENT_UNVERIFIABLE, f"executor metadata is {source_state or 'unknown'}{f': {detail}' if detail else ''}"
        return _EVENT_STALE, "event kind is not recognized"

    @staticmethod
    def _retain_unverifiable_event(event: dict[str, Any], detail: str | None) -> None:
        event["last_condition_checked_at"] = _timestamp()
        event["last_condition_error"] = detail or "event condition could not be verified"

    @staticmethod
    def _payload(events: list[Mapping[str, Any]]) -> str:
        lines: list[str] = []
        for event in events:
            if event.get("kind") == "job_stopped":
                lines.append(
                    f"Stopped registered job: JOB-ID {event['job']} ({event['note']}); "
                    f"TASK-ID {event['task']}: {event['task_title']}."
                )
            elif event.get("kind") == "task_ready":
                lines.append(
                    f"Executor AGENT-ID {event['executor']} has no unarchived jobs for TASK-ID {event['task']}: {event['task_title']}."
                )
            elif event.get("kind") == "task_unbound":
                lines.append(f"TASK-ID {event['task']}: {event['task_title']} has no bound executor.")
        return "\n".join(lines)

    @staticmethod
    def _turn_boundary(turn: Mapping[str, Any] | None) -> tuple[bool, str | None, str | None]:
        if turn is None:
            return True, None, None
        turn_id, status = turn.get("id"), turn.get("status")
        return True, turn_id if isinstance(turn_id, str) else None, status if isinstance(status, str) else None

    @staticmethod
    def _interrupted_turn(status: str | None) -> bool:
        return isinstance(status, str) and status.lower() in {"interrupted", "cancelled", "canceled", "paused", "suspended"}

    @staticmethod
    def _completed_turn(status: str | None) -> bool:
        return isinstance(status, str) and status.lower() == "completed"

    def _block_for_interruption(
        self,
        events: list[dict[str, Any]],
        detail: str,
        *,
        latest: Mapping[str, Any] | None = None,
        recipient_status: str | None = None,
    ) -> None:
        """Persist a paused boundary until a later completed turn proves recovery."""

        _, turn_id, turn_status = self._turn_boundary(latest)
        turn_status = turn_status or recipient_status
        for event in events:
            event.update({
                "delivery": "blocked",
                "block_kind": "interrupted_turn",
                "interruption_turn_observed": True,
                "interruption_turn_id": turn_id,
                "interruption_turn_status": turn_status,
                "interruption_observed_at": _timestamp(),
                "last_error": detail,
                "next_attempt_at": None,
            })
            event.pop("failure_kind", None)

    def _reobserve_interrupted_events(
        self, state: dict[str, Any], states: Mapping[str, Mapping[str, Any]]
    ) -> None:
        """Re-enable only a visibly recovered interruption, without resuming it.

        These events intentionally have no ordinary retry deadline.  They are
        revisited only through a metadata-only newest-turn read after the
        normal bulk observation says the same recipient is idle or notLoaded.
        """

        groups: dict[str, list[dict[str, Any]]] = {}
        for event in state.get("events", {}).values():
            if not isinstance(event, dict) or event.get("delivery") != "blocked":
                continue
            if event.get("block_kind") != "interrupted_turn":
                continue
            recipient = event.get("recipient")
            if _valid_agent(recipient):
                groups.setdefault(recipient, []).append(event)
        for recipient, events in groups.items():
            recipient_state = states.get(recipient, {}).get("status")
            for event in events:
                event["last_recipient_state"] = recipient_state or "unknown"
            if not self._eligible_recipient(recipient_state):
                continue
            stream = None
            try:
                stream = self.stream_factory(self.socket_path)
                if not hasattr(stream, "latest_turn"):
                    raise WakeRuntimeError("App Server stream cannot inspect the recipient's latest turn")
                latest = stream.latest_turn(recipient)
            except Exception as exc:
                for event in events:
                    event["last_interruption_checked_at"] = _timestamp()
                    event["last_interruption_error"] = str(exc)
                continue
            finally:
                if stream is not None:
                    with contextlib.suppress(Exception):
                        stream.close()
            _, latest_id, latest_status = self._turn_boundary(latest)
            for event in events:
                event["last_interruption_checked_at"] = _timestamp()
                event["last_interruption_error"] = None
                if self._interrupted_turn(latest_status):
                    self._block_for_interruption(
                        [event],
                        f"recipient's newest turn is {latest_status}; waiting for explicit user or Manager action",
                        latest=latest,
                    )
                    continue
                if self._completed_turn(latest_status) and isinstance(latest_id, str) and latest_id != event.get("interruption_turn_id"):
                    event.update({
                        "delivery": "pending",
                        "next_attempt_at": 0.0,
                        "last_error": None,
                        "interruption_recovered_at": _timestamp(),
                        "interruption_recovery_turn_id": latest_id,
                        "interruption_recovery_turn_status": latest_status,
                    })
                    event.pop("block_kind", None)

    def _recover_attempts_without_reply(self, state: dict[str, Any]) -> None:
        """Convert a persisted in-flight attempt after daemon loss to uncertain.

        The before-turn boundary was fsynced before the RPC.  On the next
        targeted delivery path it is compared with the current newest turn;
        a changed boundary is ambiguous, not an excuse to start another turn.
        """

        now = self.clock()
        for event in state.get("events", {}).values():
            if not isinstance(event, dict) or event.get("delivery") != "attempting":
                continue
            event.update({
                "delivery": "uncertain",
                "failure_kind": "response_loss_or_daemon_exit",
                "last_error": "daemon ended before turn/start acknowledgement",
                "next_attempt_at": _retry_after(now, int(event.get("attempts", 1))),
            })

    def _delivery_failure(self, events: list[dict[str, Any]], error: Exception) -> None:
        now = self.clock()
        detail = str(error)
        for event in events:
            if isinstance(error, job_runtime.AppServerRpcError):
                # A JSON-RPC error is an acknowledged rejection.  It is safe
                # to retry later, and an unrelated later turn must not turn it
                # into a response-loss ambiguity.
                event.update({
                    "delivery": "rejected",
                    "failure_kind": "explicit_rpc_rejection",
                    "last_error": detail,
                    "next_attempt_at": _retry_after(now, int(event.get("attempts", 1))),
                    "last_attempt_at": _timestamp(),
                })
            else:
                event.update({
                    "delivery": "uncertain",
                    "failure_kind": "response_loss_or_transport",
                    "last_error": detail,
                    "next_attempt_at": _retry_after(now, int(event.get("attempts", 1))),
                    "last_attempt_at": _timestamp(),
                })

    def _preflight_failure(self, events: list[dict[str, Any]], detail: str) -> None:
        now = self.clock()
        for event in events:
            event.update({
                "delivery": "blocked",
                "last_error": detail,
                "next_attempt_at": _retry_after(now, int(event.get("attempts", 0) + 1)),
            })

    @staticmethod
    def _eligible_recipient(status: Any) -> bool:
        return status in {"idle", "notLoaded"}

    def _reconcile_uncertain_boundary(
        self, events: list[dict[str, Any]], latest: Mapping[str, Any] | None
    ) -> list[dict[str, Any]]:
        _, current_id, _ = self._turn_boundary(latest)
        retry: list[dict[str, Any]] = []
        for event in events:
            if event.get("delivery") != "uncertain":
                retry.append(event)
                continue
            if not event.get("before_turn_observed") or event.get("before_turn_id") != current_id:
                event.update({
                    "delivery": "ambiguous",
                    "next_attempt_at": None,
                    "last_error": "turn history changed after an unacknowledged turn/start; manual reconciliation is required",
                    "ambiguity_at": _timestamp(),
                })
                continue
            retry.append(event)
        return retry

    def _deliver(self, state: dict[str, Any]) -> None:
        now = self.clock()
        groups: dict[str, list[dict[str, Any]]] = {}
        for event in state.get("events", {}).values():
            if not isinstance(event, dict) or event.get("delivery") in {"accepted", "ambiguous"}:
                continue
            retry_at = event.get("next_attempt_at", 0.0)
            if retry_at is None:
                continue
            try:
                delayed = float(retry_at) > now
            except (TypeError, ValueError):
                delayed = False
            if delayed:
                continue
            recipient = event.get("recipient")
            if _valid_agent(recipient):
                groups.setdefault(recipient, []).append(event)
        for recipient, candidates in groups.items():
            current: list[dict[str, Any]] = []
            for event in candidates:
                currentness, detail = self._event_is_current(event)
                if currentness == _EVENT_CURRENT:
                    event.pop("last_condition_error", None)
                    current.append(event)
                elif currentness == _EVENT_STALE:
                    self._resolve_event(state, event["signature"], reason="stale before delivery")
                else:
                    self._retain_unverifiable_event(event, detail)
            if not current:
                continue
            recipient_state = self._agent_states({recipient}).get(recipient, {}).get("status")
            if not self._eligible_recipient(recipient_state):
                for event in current:
                    event["last_recipient_state"] = recipient_state or "unknown"
                continue
            stream = None
            sent = False
            try:
                stream = self.stream_factory(self.socket_path)
                snapshot = stream.resume(recipient)
                resumed_state = _status_from_snapshot(snapshot, recipient)
                if resumed_state == "notLoaded":
                    if not hasattr(stream, "read"):
                        self._preflight_failure(current, "thread/resume left recipient notLoaded and stream cannot recheck it")
                        continue
                    snapshot = stream.read(recipient)
                    resumed_state = _status_from_snapshot(snapshot, recipient)
                if resumed_state != "idle":
                    if resumed_state == "notLoaded":
                        self._preflight_failure(current, "recipient remains notLoaded after thread/resume recheck")
                        continue
                    if self._interrupted_turn(resumed_state):
                        latest = None
                        latest_error = None
                        if hasattr(stream, "latest_turn"):
                            try:
                                latest = stream.latest_turn(recipient)
                            except Exception as exc:
                                latest_error = str(exc)
                        detail = f"recipient status is {resumed_state}; waiting for explicit user or Manager action"
                        if latest_error:
                            detail = f"{detail}; newest turn metadata could not be read: {latest_error}"
                        self._block_for_interruption(
                            current,
                            detail,
                            latest=latest,
                            recipient_status=resumed_state,
                        )
                        continue
                    for event in current:
                        event["delivery"] = "pending"
                        event["last_recipient_state"] = resumed_state or "unknown"
                    continue
                # Conditions can change after the first recheck or while the
                # recipient is being resumed.  Do not start a stale turn.
                rechecked: list[dict[str, Any]] = []
                for event in current:
                    currentness, detail = self._event_is_current(event)
                    if currentness == _EVENT_CURRENT:
                        event.pop("last_condition_error", None)
                        rechecked.append(event)
                    elif currentness == _EVENT_STALE:
                        self._resolve_event(state, event["signature"], reason="stale immediately before turn/start")
                    else:
                        self._retain_unverifiable_event(event, detail)
                current = rechecked
                if not current:
                    continue
                if not hasattr(stream, "latest_turn"):
                    self._preflight_failure(current, "App Server stream cannot inspect the recipient's latest turn")
                    continue
                latest = stream.latest_turn(recipient)
                current = self._reconcile_uncertain_boundary(current, latest)
                if not current:
                    continue
                _, before_turn_id, before_turn_status = self._turn_boundary(latest)
                if self._interrupted_turn(before_turn_status):
                    self._block_for_interruption(
                        current,
                        f"recipient's newest turn is {before_turn_status}; waiting for explicit user or Manager action",
                        latest=latest,
                    )
                    continue
                payload = self._payload(current)
                if not payload:
                    continue
                # Persist the attempt and its exact before-turn boundary
                # before the RPC.  A missing response can then be reconciled
                # after a crash/restart without pretending exactly-once.
                for event in current:
                    event.update({
                        "delivery": "attempting",
                        "attempts": int(event.get("attempts", 0)) + 1,
                        "last_attempt_at": _timestamp(),
                        "before_turn_observed": True,
                        "before_turn_id": before_turn_id,
                        "before_turn_status": before_turn_status,
                    })
                counters = state.setdefault("counters", {})
                counters["turn_start_attempts"] = int(counters.get("turn_start_attempts", 0)) + 1
                _save_state(self.store, state)
                sent = True
                if hasattr(stream, "start_turn"):
                    stream.start_turn(recipient, payload)
                else:
                    stream.request("turn/start", {"threadId": recipient, "input": [{"type": "text", "text": payload}]})
            except Exception as exc:
                if sent:
                    self._delivery_failure(current, exc)
                else:
                    self._preflight_failure(current, str(exc))
                if sent and isinstance(exc, job_runtime.AppServerEventError) and not isinstance(exc, job_runtime.AppServerRpcError):
                    # A new delivery connection cannot be trusted after a
                    # transport/protocol error.  Re-run the installer-owned
                    # behavioral check on the bounded reconnection path.
                    self.compatibility_ready = False
                    self.next_compatibility_retry = self.clock() + COMPATIBILITY_RETRY_SECONDS
            else:
                for event in current:
                    event.update({
                        "delivery": "accepted",
                        "accepted_at": _timestamp(),
                        "acknowledgement": "turn/start RPC response",
                        "last_error": None,
                    })
                    event.pop("failure_kind", None)
                counters = state.setdefault("counters", {})
                counters["accepted"] = int(counters.get("accepted", 0)) + len(current)
            finally:
                if stream is not None:
                    with contextlib.suppress(Exception):
                        stream.close()
                _save_state(self.store, state)

    def _ensure_compatibility(self, state: dict[str, Any]) -> bool:
        if self.compatibility_ready:
            return True
        now = self.clock()
        if now < self.next_compatibility_retry:
            return False
        try:
            result = self.compatibility()
            socket_path = result.get("socket_path") if isinstance(result, Mapping) else None
            if not isinstance(socket_path, str) or not socket_path:
                raise WakeRuntimeError("wake compatibility check returned no socket path")
        except Exception as exc:
            state["healthy"] = False
            state["error"] = f"wake compatibility/reconnection failed: {exc}"
            self.next_compatibility_retry = now + COMPATIBILITY_RETRY_SECONDS
            return False
        self.socket_path = socket_path
        self.compatibility_ready = True
        self.next_compatibility_retry = 0.0
        state["compatibility"] = _public_compatibility(result)
        state["error"] = None
        return True

    def run_once(self) -> dict[str, Any]:
        """Reconcile durable state once; it never creates unrelated threads."""

        with _service_start_lock(self.store), self.store.lock("service-cycle"):
            state = _load_state(self.store)
            if state.get("token") and not state.get("enabled"):
                return state
            manager = recorded_manager(self.store)
            self.manager = manager
            counters = state.setdefault("counters", {})
            counters["cycles"] = int(counters.get("cycles", 0)) + 1
            state["heartbeat_at"] = _timestamp()
            state["manager"] = manager
            if manager is None:
                if _has_bound_tasks(self.store):
                    state.update({
                        "mode": "error",
                        "healthy": False,
                        "error": "existing bound tasks have no determinable Manager; run mam service start --manager AGENT-ID",
                    })
                else:
                    state.update({"mode": "awaiting_manager", "healthy": True, "error": None, "diagnostics": []})
                _save_state(self.store, state)
                return state
            state["mode"] = "active"
            if not self._ensure_compatibility(state):
                _save_state(self.store, state)
                return state
            tasks = self._load_tasks()
            self._probe_jobs(state, tasks)
            tasks = self._load_tasks()
            agents = {task["agent"] for task in tasks if _valid_agent(task.get("agent"))}
            agents.add(manager)
            states = self._agent_states(agents)
            if agents and all(states.get(agent, {}).get("status") == "unknown" for agent in agents):
                details = [str(states.get(agent, {}).get("error") or "unknown") for agent in agents]
                if any("App Server" in detail or "socket" in detail.lower() for detail in details):
                    self.compatibility_ready = False
                    self.next_compatibility_retry = self.clock() + COMPATIBILITY_RETRY_SECONDS
                    state["healthy"] = False
                    state["error"] = "App Server metadata query is unavailable; compatibility will be retried"
                    _save_state(self.store, state)
                    return state
            desired, inconclusive, diagnostics = self._desired_events(tasks, states)
            state["diagnostics"] = diagnostics
            state["healthy"] = True
            state["error"] = None
            self._reconcile_events(state, desired, inconclusive)
            self._recover_attempts_without_reply(state)
            self._reobserve_interrupted_events(state, states)
            _save_state(self.store, state)
            self._deliver(state)
            state["heartbeat_at"] = _timestamp()
            _save_state(self.store, state)
            return state


def _daemon(config: ProjectConfig, token: str) -> int:
    store = Store(config)
    # The parent writes the identity immediately after Popen.  Give that
    # atomic write a short chance before deciding this child is stale.
    deadline = time.monotonic() + 5.0
    while True:
        with store.lock("service-state"):
            state = _load_state(store)
        if state.get("token") == token:
            if state.get("pid") == os.getpid() and isinstance(state.get("identity"), Mapping):
                break
            if not state.get("enabled"):
                return 1
        if time.monotonic() >= deadline:
            return 2
        time.sleep(0.05)
    if state.get("pid") not in (None, os.getpid()):
        return 2
    stopped = threading.Event()

    def request_stop(_signum: int, _frame: Any) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    with store.lock("service-state"):
        state = _load_state(store)
        if state.get("token") != token or state.get("pid") != os.getpid() or not state.get("enabled"):
            return 1
        state["ready_at"] = _timestamp()
        if state.get("mode") == "awaiting_manager":
            state["healthy"] = True
            state["error"] = None
        _save_state(store, state)
    scheduler = WakeScheduler(store)
    try:
        while not stopped.is_set():
            with store.lock("service-state"):
                state = _load_state(store)
                if state.get("token") != token or not state.get("enabled"):
                    break
            scheduler.run_once()
            stopped.wait(POLL_SECONDS)
    except Exception as exc:
        with store.lock("service-state"):
            state = _load_state(store)
            if state.get("token") == token:
                state.update({"healthy": False, "error": f"scheduler failure: {exc}", "heartbeat_at": _timestamp()})
                _save_state(store, state)
        return 1
    finally:
        with store.lock("service-state"):
            state = _load_state(store)
            if state.get("token") == token:
                state.update({"enabled": False, "mode": "disabled", "healthy": False, "stopped_at": _timestamp()})
                _save_state(store, state)
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m multi_agent_manager.wake_runtime")
    parser.add_argument("--service", action="store_true")
    parser.add_argument("--mam-root")
    parser.add_argument("--project-root")
    parser.add_argument("--branch")
    parser.add_argument("--token")
    args = parser.parse_args(argv)
    if not args.service or not all((args.mam_root, args.project_root, args.branch, args.token)):
        parser.error("--service, --mam-root, --project-root, --branch and --token are required")
    config = ProjectConfig(Path(args.mam_root), Path(args.project_root), args.branch)
    return _daemon(config, args.token)


if __name__ == "__main__":
    raise SystemExit(_main())
