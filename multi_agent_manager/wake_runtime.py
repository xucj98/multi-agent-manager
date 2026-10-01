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

from . import job_runtime, task_state
from .cli import ProjectConfig, Store, safe_path
try:
    from .migrations import MigrationError, backup_local, migrate_data, read_data_version, write_data_version
    from .release import RELEASE_TAG
    from .version import DATA_VERSION, info as program_info, source_commit
except ImportError:  # A source-only 0.1.0 fixture may omit release helpers.
    class MigrationError(RuntimeError):
        pass

    DATA_VERSION = "0.1.0"
    RELEASE_TAG = "v0.1.0"
    def read_data_version(root):
        return "0.1.0"

    def backup_local(root, destination=None):
        raise MigrationError("release migration helpers are unavailable")

    def migrate_data(root, target=DATA_VERSION):
        return {"from": DATA_VERSION, "to": target, "steps": [], "changed": False}

    def write_data_version(root, version, *, from_version=None):
        return None

    def program_info():
        return {"version": "0.1.0", "commit": None, "data_version": DATA_VERSION}

    def source_commit():
        return None


ADAPTATION_DOCUMENT = "docs/upgrades/0.2.0.md"


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
_NATIVE_V2_DIRECT_INPUT_REJECTION = (
    "App Server request turn/start failed: direct app-server input is not allowed for multi-agent v2 sub-agents"
)
_NATIVE_V2_DIRECT_INPUT_FAILURE = "unsupported_multi_agent_v2_direct_input"
_MANAGER_NATIVE_FOLLOWUP = "manager_native_followup"
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


@contextlib.contextmanager
def task_rebind_lock(store: Store, task: str):
    """Serialize a task handoff with every scheduler delivery edge.

    Keep this lock order aligned with :meth:`WakeScheduler.run_once`: service
    startup/cycle coordination comes before the global binding registry and
    then the individual task.
    """

    with _service_start_lock(store), store.lock("service-cycle"), store.lock("bindings"), store.lock(task):
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
        "message_channel": "tool",
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
        # ``version`` above is the service-state schema.  This field records
        # the code that owns the running daemon and intentionally remains
        # absent/unknown for old daemon state files.
        "daemon_version": None,
        "daemon_commit": None,
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


def _route_messages(state: dict[str, Any], manager: str) -> None:
    for event in state.get("events", {}).values():
        if not isinstance(event, dict) or event.get("kind") != "message" or event.get("recipient") == manager:
            continue
        event["recipient"] = manager
        if event.get("delivery") not in {"pending", "rejected", "blocked"}:
            continue
        event["delivery"] = "pending"
        event["next_attempt_at"] = 0.0
        event.pop("block_kind", None)
        event.pop("last_error", None)
        for key in tuple(event):
            if key.startswith("interruption_"):
                event.pop(key, None)


def rebind_manager(store: Store, note: str) -> dict[str, Any]:
    """Transfer a project Manager after proving the old owner has stopped."""
    from . import cli, identity
    if not isinstance(note, str) or not note.strip():
        raise WakeRuntimeError("--note must describe the Manager handoff")
    try:
        caller = identity.read(cli.caller_agent())
    except (cli.Error, identity.IdentityError) as exc:
        raise WakeRuntimeError(str(exc)) from exc
    if caller.path != "/root" or caller.tree_root != caller.agent:
        raise WakeRuntimeError("Manager takeover requires a native root thread")
    with _service_start_lock(store), store.lock("service-cycle"), store.lock("bindings"), store.lock("service-manager"):
        if caller.agent in _active_bindings(store):
            raise WakeRuntimeError("a bound executor cannot become Manager")
        previous = _manager_record(store)
        old = previous["manager"] if previous else None
        if old == caller.agent:
            return {"manager": old, "unchanged": True}
        if old is not None:
            try:
                states = cli.agent_observations([old])
                cli._rebind_quiescent(old, cli.agent_state(old, states), role="current Manager")
            except Exception as exc:
                raise WakeRuntimeError(str(exc)) from exc
        record = {"manager": caller.agent, "source": "service rebind-manager", "recorded_at": _timestamp(),
                  "handoffs": list(previous.get("handoffs", [])) if previous else []}
        record["handoffs"].append({"from_agent": old, "to_agent": caller.agent, "at": _timestamp(), "note": note})
        state = _load_state(store)
        _write_json(_service_path(store, "manager.json"), record)
        _route_messages(state, caller.agent)
        if old is not None:
            for signature, event in list(state.get("events", {}).items()):
                if isinstance(event, Mapping) and event.get("recipient") == old:
                    scheduler_event = state["events"].pop(signature)
                    state.setdefault("history", []).append({**scheduler_event, "resolved_at": _timestamp(),
                                                               "resolution": "Manager identity changed"})
            state["history"] = state["history"][-HISTORY_LIMIT:]
        state["manager"] = caller.agent
        _save_state(store, state)
    return {"manager": caller.agent, "previous_manager": old, "unchanged": False}


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
    try:
        data_version = read_data_version(store.root)
    except MigrationError as exc:
        data_version = None
        data_error = str(exc)
    else:
        data_error = None
    result = {
        "status": status,
        "program_version": program_info()["version"],
        "daemon_version": state.get("daemon_version"),
        "data_version": data_version,
        "message_channel": state.get("message_channel", "tool"),
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
    if data_error:
        result["data_version_error"] = data_error
    if state.get("diagnostics"):
        result["diagnostics"] = list(state["diagnostics"])
    return result


def service_status(config: ProjectConfig) -> dict[str, Any]:
    """Return JSON-serializable service state without creating a daemon."""

    store = Store(config)
    with store.lock("service-state"):
        state = _load_state(store)
        return _status_mapping(store, state)


def set_message_channel(config: ProjectConfig, value: str) -> dict[str, Any]:
    if value not in {"tool", "user"}:
        raise WakeRuntimeError("message-channel must be tool or user")
    store = Store(config)
    with _service_start_lock(store), store.lock("service-cycle"):
        state = _load_state(store)
        state["message_channel"] = value
        _save_state(store, state)
        return {"message_channel": value}


def enqueue_message(store: Store, *, sender: str, sender_path: str, sender_tree: str,
                    message: str, defer: bool, task: str | None) -> dict[str, Any]:
    if not message.strip():
        raise WakeRuntimeError("--message must contain text")
    with _service_start_lock(store), store.lock("service-cycle"):
        manager = recorded_manager(store)
        if manager is None:
            raise WakeRuntimeError("this project has no recorded Manager")
        state = _load_state(store)
        message_id = str(uuid.uuid4())
        state.setdefault("events", {})[message_id] = {
            "signature": message_id, "kind": "message", "recipient": manager,
            "sender": sender, "sender_path": sender_path, "sender_tree": sender_tree,
            "task": task, "message": message, "defer": defer,
            "created_at": _timestamp(), "delivery": "pending", "attempts": 0,
            "next_attempt_at": 0.0,
        }
        _save_state(store, state)
        alive, error = _probe_service_process(state) if state.get("pid") is not None else (False, None)
        service = "running" if state.get("enabled") and alive else "disabled" if not state.get("enabled") else "unavailable"
        result = {"id": message_id, "status": "queued", "service": service}
        if error and service == "unavailable":
            result["service_error"] = error
        return result


_DAEMON_BOOTSTRAP = """\
import runpy
import sys

package_parent = sys.argv.pop(1)
sys.path.insert(0, package_parent)
runpy.run_module("multi_agent_manager.wake_runtime", run_name="__main__", alter_sys=True)
"""


def _caller_package_parent() -> str:
    """Return the resolved parent that supplied this running runtime module.

    ``MAM_ROOT`` is a project-state checkout and is deliberately not used as a
    code root.  It may be a different worktree from the installation or the
    current source checkout that called ``start_service``.
    """

    package = Path(__file__).resolve().parent
    if package.name != "multi_agent_manager" or not (package / "__init__.py").is_file():
        raise WakeRuntimeError("cannot resolve the current multi_agent_manager package for detached service startup")
    return str(package.parent)


def _spawn_service(config: ProjectConfig, token: str, log_path: Path) -> subprocess.Popen[bytes]:
    environment = os.environ.copy()
    # The detached scheduler is not a Manager action and must never capture
    # the caller's thread identity or Python import path through an inherited
    # environment.  ``-I -S`` below also enforces this in the child.
    environment.pop("CODEX_THREAD_ID", None)
    environment.pop("PYTHONPATH", None)
    command = [
        sys.executable,
        "-I",
        "-S",
        "-c",
        _DAEMON_BOOTSTRAP,
        _caller_package_parent(),
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
        # A new empty instance starts at the current data format.  Existing
        # task records deliberately retain the 0.1.0 default until upgrade.
        if not (store.root / ".local" / "data-version.json").exists() and not any(
            (store.root / ".local" / "tasks").glob("*.json")
        ):
            write_data_version(store.root, DATA_VERSION)
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
            "daemon_version": program_info()["version"],
            "daemon_commit": source_commit(),
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


def _merge_release(store: Store, target: str) -> dict[str, Any]:
    """Merge the installed release commit into the configured MAM branch."""

    current_branch = _git_output(store.root, "branch", "--show-current")
    if current_branch != store.branch:
        raise WakeRuntimeError(
            f"MAM_ROOT is on branch {current_branch or '<detached>'}; check out configured MAM_BRANCH {store.branch} and retry"
        )
    merge = subprocess.run(
        ["git", "-C", str(store.root), "merge", "--no-edit", target],
        capture_output=True,
        text=True,
        check=False,
    )
    if merge.returncode:
        detail = " ".join((merge.stdout + " " + merge.stderr).split())[:1200]
        raise WakeRuntimeError(
            f"Git merge of release {target} into {store.branch} failed; resolve conflicts and retry"
            + (f": {detail}" if detail else "")
        )
    return {"branch": store.branch, "commit": target, "output": " ".join(merge.stdout.split())}


def _ensure_release_commit(store: Store, target: str) -> None:
    """Ensure an installed release commit is available without changing remotes."""

    verify = subprocess.run(
        ["git", "-C", str(store.root), "cat-file", "-e", f"{target}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode == 0:
        return
    origin = subprocess.run(
        ["git", "-C", str(store.root), "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False,
    )
    if origin.returncode or not origin.stdout.strip():
        raise WakeRuntimeError(
            f"installed release commit {target} is unavailable and MAM_ROOT has no configured origin"
        )
    fetched = subprocess.run(
        ["git", "-C", str(store.root), "fetch", "--no-tags", "origin", target],
        capture_output=True,
        text=True,
        check=False,
    )
    if fetched.returncode:
        detail = " ".join((fetched.stdout + " " + fetched.stderr).split())[:800]
        raise WakeRuntimeError(
            f"could not fetch installed release commit {target} from configured origin"
            + (f": {detail}" if detail else "")
        )
    verify = subprocess.run(
        ["git", "-C", str(store.root), "cat-file", "-e", f"{target}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode:
        raise WakeRuntimeError(f"configured origin did not provide installed release commit {target}")


def _git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise WakeRuntimeError("git command failed: " + " ".join(args))
    return result.stdout.strip()


def service_upgrade(config: ProjectConfig) -> dict[str, Any]:
    """Upgrade one stopped instance to the installed program's release."""

    store = Store(config)
    with _service_start_lock(store), store.lock("service-upgrade"):
        state = _load_state(store)
        alive, process_error = _probe_service_process(state) if state.get("pid") is not None else (False, None)
        if alive:
            raise WakeRuntimeError("service daemon is still running; run mam service stop and retry")
        if process_error and state.get("pid") is not None and process_error != "service process is no longer running":
            raise WakeRuntimeError(f"cannot verify service daemon is stopped: {process_error}")
        target = source_commit()
        if not target or len(target) != 40 or any(char not in "0123456789abcdef" for char in target):
            raise WakeRuntimeError("installed program has no fixed release commit metadata; use a tagged source archive")
        current_data = read_data_version(store.root)
        try:
            _ensure_release_commit(store, target)
        except WakeRuntimeError:
            # Fetch/metadata failures happen before backup or migration, so a
            # retry cannot mistake a partially prepared instance for success.
            raise
        backup = backup_local(store.root)
        try:
            merge = _merge_release(store, target)
            migrations = migrate_data(store.root, DATA_VERSION)
        except (MigrationError, WakeRuntimeError) as exc:
            raise WakeRuntimeError(f"service upgrade incomplete; backup retained at {backup}: {exc}") from exc
        return {
            "status": "upgraded" if current_data != DATA_VERSION else "up-to-date",
            "program_version": program_info()["version"],
            "target_commit": target,
            "target_tag": RELEASE_TAG,
            "data_version": read_data_version(store.root),
            "backup": str(backup),
            "merge": merge,
            "migrations": migrations,
            "adaptation": ADAPTATION_DOCUMENT,
            "daemon_running": False,
        }


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

    def _refresh_task_states(
        self, tasks: list[dict[str, Any]], states: Mapping[str, Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        """Persist lifecycle states from the latest executor and job observations."""
        for task in tasks:
            task_id = task.get("id")
            if not isinstance(task_id, str):
                continue
            agent = task.get("agent")
            observation = states.get(agent) if _valid_agent(agent) else None
            with self.store.lock(task_id):
                fresh = self.store.read(task_id)
                updated, _, _ = task_state.refresh_state(fresh, observation)
                if updated != fresh:
                    self.store.write(updated)
        return self._load_tasks()

    @staticmethod
    def _job_stopped(job: Mapping[str, Any]) -> bool:
        probe = job.get("probe")
        return job_runtime.job_status(job.get("status")) == "exited" or (isinstance(probe, Mapping)
            and job_runtime.job_status(probe.get("status")) == "exited")

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
                observation = {**observation, "status": job_runtime.job_status(observation["status"])}
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
                    if observation.get("status") in {"running", "exited"}:
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

    def _review_graph(self, tasks: list[dict[str, Any]], states: Mapping[str, Mapping[str, Any]]) -> tuple[set[str], list[dict[str, str]]]:
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
        adjacent: dict[str, set[str]] = {task_id: set() for task_id in by_id}
        for reviewer, source in edges.items():
            adjacent[reviewer].add(source)
            adjacent[source].add(reviewer)
        blocked: set[str] = set()
        visited: set[str] = set()
        for root in adjacent:
            if root in visited:
                continue
            component = {root}
            frontier = [root]
            while frontier:
                current = frontier.pop()
                for neighbor in adjacent[current] - component:
                    component.add(neighbor)
                    frontier.append(neighbor)
            visited.update(component)
            for task_id in component:
                task = by_id[task_id]
                agent = task.get("agent")
                agent_status = states.get(agent, {}).get("status") if _valid_agent(agent) else None
                jobs = self._unarchived_jobs(task)
                if (_valid_agent(agent) and agent_status not in {"idle", "notLoaded"}) or any(
                    not self._job_stopped(job) for job in jobs
                ):
                    blocked.update(component)
                    break
        return blocked, diagnostics

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

    def _executor_path(self, task: Mapping[str, Any]) -> str | None:
        known = task.get("identity")
        if not isinstance(known, Mapping) or known.get("tree_root") != self.manager:
            return None
        path = known.get("path")
        if not isinstance(path, str) or not path.startswith("/root/") or any(
            segment in ("", ".", "..") for segment in path.split("/")[1:]
        ):
            return None
        return path

    @staticmethod
    def _executor_stopped_job_event(event: Mapping[str, Any]) -> bool:
        """Return whether a stopped-job event was directed to its executor.

        A task without an executor can route a stopped job to the Manager.
        That is already a Manager delivery and must never be promoted again.
        """

        executor = event.get("executor")
        return (
            event.get("kind") == "job_stopped"
            and _valid_agent(executor)
            and event.get("recipient") == executor
            and isinstance(event.get("task"), str)
            and isinstance(event.get("task_title"), str)
            and isinstance(event.get("job"), str)
            and isinstance(event.get("note"), str)
        )

    @staticmethod
    def _native_v2_direct_input_rejection(detail: Any) -> bool:
        """Recognize only the known explicit native-v2 input prohibition.

        A broad App Server RPC failure can be transient or can have a future
        supported recovery path, so it deliberately remains on the ordinary
        explicit-rejection retry path.
        """

        return detail == _NATIVE_V2_DIRECT_INPUT_REJECTION

    @classmethod
    def _native_v2_blocked_source(cls, event: Mapping[str, Any]) -> bool:
        return (
            cls._executor_stopped_job_event(event)
            and event.get("delivery") == "blocked"
            and event.get("failure_kind") == _NATIVE_V2_DIRECT_INPUT_FAILURE
            and event.get("block_kind") == _NATIVE_V2_DIRECT_INPUT_FAILURE
            and cls._native_v2_direct_input_rejection(event.get("last_error"))
        )

    @staticmethod
    def _block_native_v2_direct_input(event: dict[str, Any], detail: str) -> None:
        """Persist a known unsupported executor delivery without a retry timer."""

        event.update({
            "delivery": "blocked",
            "failure_kind": _NATIVE_V2_DIRECT_INPUT_FAILURE,
            "block_kind": _NATIVE_V2_DIRECT_INPUT_FAILURE,
            "last_error": detail,
            "next_attempt_at": None,
        })
        if not event.get("blocked_at"):
            event["blocked_at"] = _timestamp()

    def _manager_native_followup_event(self, source: Mapping[str, Any]) -> dict[str, Any] | None:
        """Build one durable Manager escalation for a blocked executor event."""

        if self.manager is None:
            return None
        return self._make_event(
            _MANAGER_NATIVE_FOLLOWUP,
            self.manager,
            task=source["task"],
            task_title=source["task_title"],
            job=source["job"],
            note=source["note"],
            executor=source["executor"],
            **({"executor_path": source["executor_path"]} if source.get("executor_path") else {}),
            source_event=source["signature"],
            error=source["last_error"],
            action="use_native_followup_task",
        )

    def _task_pending_event(self, task: Mapping[str, Any], task_id: str, title: str) -> dict[str, Any] | None:
        if self.manager is None:
            return None
        executor = task.get("agent") if _valid_agent(task.get("agent")) else None
        identity = {"kind": "task_pending", "recipient": self.manager, "task": task_id}
        if executor:
            identity["executor"] = executor
        path = self._executor_path(task)
        event = {"signature": _event_signature(identity), **identity, "task_title": title,
                 "automatic": True, "expected_status": "pending", "reminder_tasks": [task_id],
                 "reminder_number": task_state.reminder_count(task) + 1}
        if path:
            event["executor_path"] = path
        return event

    @staticmethod
    def _pending_group(
        task_id: str,
        tasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        """Return a task and its directly linked review group, if complete."""
        by_id = {task.get("id"): task for task in tasks if isinstance(task.get("id"), str)}
        task = by_id.get(task_id)
        if task is None:
            return None
        link = task.get("review")
        root_id = link.get("task") if isinstance(link, Mapping) else task_id
        if not isinstance(root_id, str) or root_id not in by_id:
            return None
        group = [by_id[root_id]]
        group.extend(
            review for review in tasks
            if isinstance(review.get("review"), Mapping)
            and review["review"].get("task") == root_id
            and review.get("status") != "archived"
        )
        if all(member.get("id") != task_id for member in group):
            return None
        return group

    @staticmethod
    def _dormant_observation(observation: Mapping[str, Any] | None) -> bool:
        return (
            isinstance(observation, Mapping)
            and observation.get("status") in {"idle", "notLoaded"}
            and not observation.get("error")
        )

    def _native_v2_manager_escalations(
        self,
        state: Mapping[str, Any],
        desired: dict[str, dict[str, Any]],
        diagnostics: list[dict[str, str]],
    ) -> None:
        """Add one Manager event for each still-current blocked child wake.

        The source event itself remains durable and blocked.  The escalation's
        signature contains that source signature, so an unchanged condition is
        retained across cycles and daemon restarts instead of creating another
        Manager turn.  A changed job, archive, or rebind removes the source
        from ``desired`` and therefore also retires its escalation.
        """

        manager = self.manager
        events = state.get("events")
        if not isinstance(events, Mapping):
            return
        for source in events.values():
            if not isinstance(source, Mapping) or not self._native_v2_blocked_source(source):
                continue
            source_signature = source.get("signature")
            if not isinstance(source_signature, str) or source_signature not in desired:
                continue
            task = source["task"]
            executor = source["executor"]
            if not _valid_agent(manager):
                diagnostics.append({
                    "kind": "native_v2_wake_manager_missing",
                    "task": task,
                    "message": f"executor {executor} cannot receive direct native-v2 input and no Manager is available",
                })
                continue
            if manager == source.get("recipient"):
                # The direct recipient already is the Manager.  Escalating it
                # back to itself would recurse through the same unsupported
                # delivery mechanism.
                diagnostics.append({
                    "kind": "native_v2_wake_manager_recipient",
                    "task": task,
                    "message": f"direct native-v2 input to Manager/executor {executor} is blocked; no self-escalation was created",
                })
                continue
            escalation = self._manager_native_followup_event(source)
            if escalation is None:
                continue
            with self.store.lock(task):
                current_task = self.store.read(task)
            count = task_state.reminder_count(current_task)
            if count >= task_state.REMINDER_LIMIT:
                continue
            escalation.update({
                "automatic": True,
                "expected_status": "working",
                "reminder_tasks": [task],
                "reminder_number": count + 1,
            })
            desired[escalation["signature"]] = escalation
            diagnostics.append({
                "kind": "native_v2_wake_blocked",
                "task": task,
                "message": (
                    f"direct input to executor {executor} was explicitly rejected for JOB-ID {source['job']}; "
                    "Manager native follow-up is required"
                ),
            })

    def _desired_events(
        self, tasks: list[dict[str, Any]], states: Mapping[str, Mapping[str, Any]]
    ) -> tuple[dict[str, dict[str, Any]], set[str], list[dict[str, str]]]:
        desired: dict[str, dict[str, Any]] = {}
        inconclusive: set[str] = set()
        _, diagnostics = self._review_graph(tasks, states)
        for task in tasks:
            task_id, title = task.get("id"), task.get("title")
            if not isinstance(task_id, str) or not isinstance(title, str):
                diagnostics.append({"kind": "invalid_task", "task": str(task_id), "message": "task record lacks id or title"})
                continue
            agent = task.get("agent") if _valid_agent(task.get("agent")) else None
            agent_status = states.get(agent, {}).get("status") if agent else None
            if agent and (
                agent_status not in {"active", "idle", "notLoaded"}
                or states.get(agent, {}).get("error")
            ):
                diagnostics.append({
                    "kind": "unknown_executor",
                    "task": task_id,
                    "message": f"task executor {agent} is {agent_status or 'unknown'}",
                })
            jobs = self._unarchived_jobs(task)
            stopped = [job for job in jobs if self._job_stopped(job)]
            if stopped:
                count = task_state.reminder_count(task)
                if count >= task_state.REMINDER_LIMIT:
                    continue
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
                        **({"executor_path": self._executor_path(task)} if agent and self._executor_path(task) else {}),
                    )
                    event.update({
                        "automatic": True,
                        "expected_status": "working",
                        "reminder_tasks": [task_id],
                        "reminder_number": count + 1,
                    })
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
            if task.get("status") != "pending":
                continue
            if self.manager is None:
                diagnostics.append({"kind": "missing_manager", "task": task_id, "message": "pending task has no recorded Manager"})
                continue
            group = self._pending_group(task_id, tasks)
            if not group or any(member.get("status") != "pending" or self._unarchived_jobs(member) for member in group):
                continue
            if any(
                _valid_agent(member.get("agent"))
                and not self._dormant_observation(states.get(member["agent"]))
                for member in group
            ):
                continue
            if task_state.reminder_count(task) >= task_state.REMINDER_LIMIT:
                continue
            event = self._task_pending_event(task, task_id, title)
            if event is not None:
                desired[event["signature"]] = event
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
        for signature in list(events):
            existing = events.get(signature)
            if not isinstance(existing, dict) or existing.get("kind") == "message":
                continue
            if existing.get("block_kind") == "interrupted_turn":
                existing.update({"delivery": "pending", "next_attempt_at": 0.0})
                existing.pop("block_kind", None)
                existing.pop("interruption_turn_id", None)
            delivery = existing.get("delivery")
            if delivery not in {"attempting", "accepted", "ambiguous", "uncertain", "rejected", "blocked"}:
                self._resolve_event(state, signature, reason="condition changed or resolved")
            elif signature not in desired:
                currentness, detail = self._event_is_current(existing)
                if currentness == _EVENT_STALE:
                    self._resolve_event(state, signature, reason=detail or "condition changed or resolved")
                elif currentness == _EVENT_UNVERIFIABLE:
                    self._retain_unverifiable_event(existing, detail)
        for signature, current in desired.items():
            existing = events.get(signature)
            if isinstance(existing, dict):
                existing.update(dict(current))
                if "executor_path" not in current:
                    existing.pop("executor_path", None)
                existing.pop("last_condition_error", None)

    def _block_persisted_native_v2_rejections(self, state: Mapping[str, Any]) -> None:
        """Upgrade a prior exact RPC rejection before its retry deadline.

        Existing service state can outlive an installed scheduler process.  On
        upgrade, do not make one more known-invalid child ``turn/start`` just
        because the old code saved it as a generic explicit rejection.
        """

        events = state.get("events")
        if not isinstance(events, Mapping):
            return
        for event in events.values():
            if (
                isinstance(event, dict)
                and self._executor_stopped_job_event(event)
                and event.get("delivery") == "rejected"
                and event.get("failure_kind") == "explicit_rpc_rejection"
                and self._native_v2_direct_input_rejection(event.get("last_error"))
            ):
                self._block_native_v2_direct_input(event, event["last_error"])

    def _source_suppressed_now(self, task_id: str) -> bool:
        tasks = self._load_tasks()
        agents = {task["agent"] for task in tasks if _valid_agent(task.get("agent"))}
        suppressed, _ = self._review_graph(tasks, self._agent_states(agents))
        return task_id in suppressed

    def _event_is_current(self, event: Mapping[str, Any]) -> tuple[str, str | None]:
        """Classify an event without turning an unavailable read into resolution."""

        if event.get("kind") == "message":
            return (_EVENT_CURRENT, None) if event.get("recipient") == self.manager else (_EVENT_STALE, "Manager changed")
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
            if event.get("automatic") and task.get("status") != "working":
                return _EVENT_STALE, "task is no longer working"
            recipient = task.get("agent") if _valid_agent(task.get("agent")) else self.manager
            count = task_state.reminder_count(task)
            if count >= task_state.REMINDER_LIMIT:
                return _EVENT_STALE, "task reminder limit reached"
            if isinstance(event, dict):
                event["reminder_number"] = count + 1
            if recipient != event.get("recipient"):
                return _EVENT_STALE, "event recipient changed"
            job = next((item for item in self._unarchived_jobs(task) if item.get("id") == event.get("job")), None)
            if job and self._job_stopped(job) and job.get("note") == event.get("note") and task.get("title") == event.get("task_title"):
                return _EVENT_CURRENT, None
            return _EVENT_STALE, "stopped job condition changed"
        if kind == "task_pending":
            if self.manager != event.get("recipient"):
                return _EVENT_STALE, "task pending recipient changed"
            if event.get("executor") != task.get("agent"):
                return _EVENT_STALE, "task executor changed"
            tasks = self._load_tasks()
            group = self._pending_group(task_id, tasks)
            if not group:
                return _EVENT_STALE, "task pending group is no longer available"
            if any(member.get("status") != "pending" or self._unarchived_jobs(member) for member in group):
                return _EVENT_STALE, "task or associated review is no longer pending"
            agents = {member["agent"] for member in group if _valid_agent(member.get("agent"))}
            observations = self._agent_states(agents)
            for agent in agents:
                observation = observations.get(agent)
                if observation is None or observation.get("status") in {None, "unknown"} or observation.get("error"):
                    return _EVENT_UNVERIFIABLE, f"task group executor {agent} state is unavailable"
                if not self._dormant_observation(observation):
                    return _EVENT_STALE, f"task group executor {agent} is active"
            if task_state.reminder_count(task) >= task_state.REMINDER_LIMIT:
                return _EVENT_STALE, "task reminder limit reached"
            return _EVENT_CURRENT, None
        if kind == "task_unbound":
            return _EVENT_STALE, "legacy unbound-task reminder was replaced by task-pending"
        if kind == _MANAGER_NATIVE_FOLLOWUP:
            executor = event.get("executor")
            if (
                not _valid_agent(executor)
                or self.manager != event.get("recipient")
                or executor == event.get("recipient")
                or event.get("action") != "use_native_followup_task"
            ):
                return _EVENT_STALE, "native-v2 Manager escalation recipient changed"
            job = next((item for item in self._unarchived_jobs(task) if item.get("id") == event.get("job")), None)
            if (
                task.get("agent") == executor
                and job
                and self._job_stopped(job)
                and job.get("note") == event.get("note")
                and task.get("title") == event.get("task_title")
            ):
                count = task_state.reminder_count(task)
                if count >= task_state.REMINDER_LIMIT:
                    return _EVENT_STALE, "task reminder limit reached"
                if isinstance(event, dict):
                    event["reminder_number"] = count + 1
                return _EVENT_CURRENT, None
            return _EVENT_STALE, "native-v2 Manager escalation source condition changed"
        if kind == "task_ready":
            executor = task.get("agent")
            if (
                executor != event.get("executor")
                or self.manager != event.get("recipient")
                or self._unarchived_jobs(task)
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
        entries: list[str] = []
        seen_auto: set[tuple[str, str]] = set()
        seen_auto_entries: set[tuple[str, str, str]] = set()
        for event in events:
            kind = event.get("kind")
            task_id = event.get("task")
            automatic = bool(event.get("automatic")) or kind in {
                "job_stopped", "task_ready", "task_unbound", "task_pending", _MANAGER_NATIVE_FOLLOWUP,
            }
            if kind in {"job_stopped", _MANAGER_NATIVE_FOLLOWUP}:
                unique = (str(kind), str(task_id))
                if unique in seen_auto:
                    continue
                seen_auto.add(unique)
                if _valid_agent(event.get("executor")) and event.get("recipient") == event.get("executor"):
                    source = event.get("executor_path") or f"task: {task_id}"
                    body = "There are exited jobs. Check the results and archive them."
                else:
                    source = event.get("executor_path") or f"task: {task_id}"
                    body = "There are exited jobs. Ask the executor to check the results and archive them."
                message_type = "job exited"
            elif kind in {"task_pending", "task_ready", "task_unbound"}:
                unique = (str(kind), str(task_id))
                if unique in seen_auto:
                    continue
                seen_auto.add(unique)
                source = event.get("executor_path") or f"task: {task_id}"
                body = "Check the task and any published report; start or continue the work, request review, block or archive the task."
                message_type = "task pending"
            elif kind == "message":
                sender = event.get("sender_path") if event.get("sender_tree") == event.get("recipient") else None
                source = sender or f"agent: {event['sender']}"
                body = event["message"]
                message_type = "message"
            else:
                continue
            if automatic and event.get("reminder_number") == task_state.REMINDER_LIMIT:
                body += f"\nFinal reminder ({task_state.REMINDER_LIMIT}/{task_state.REMINDER_LIMIT}) for this round."
            entry = f"[{message_type} | {source}]\n{body}"
            if automatic:
                key = (message_type, str(source), body)
                if key in seen_auto_entries:
                    continue
                seen_auto_entries.add(key)
            entries.append(entry)
        if not entries:
            return ""
        return "[MAM MESSAGE]\n\n" + "\n\n".join(entries)

    @staticmethod
    def _turn_boundary(turn: Mapping[str, Any] | None) -> tuple[bool, str | None, str | None]:
        if turn is None:
            return True, None, None
        turn_id, status = turn.get("id"), turn.get("status")
        return True, turn_id if isinstance(turn_id, str) else None, status if isinstance(status, str) else None

    @staticmethod
    def _terminal_turn(status: str | None) -> bool:
        return isinstance(status, str) and status.lower() in {"completed", "failed"}

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
                if self._executor_stopped_job_event(event) and self._native_v2_direct_input_rejection(detail):
                    # This exact server acknowledgement is a capability
                    # boundary for native v2 children, not a transient RPC
                    # failure.  Preserve the source and let the Manager's
                    # ordinary thread receive one native-followup escalation.
                    self._block_native_v2_direct_input(event, detail)
                    continue
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
        retry: list[dict[str, Any]] = []
        for event in events:
            if event.get("delivery") != "uncertain":
                retry.append(event)
                continue
            event.update({
                "delivery": "ambiguous",
                "next_attempt_at": None,
                "last_error": "turn/start acknowledgement was lost; delivery cannot be confirmed without risking a duplicate",
                "ambiguity_at": _timestamp(),
            })
        return retry

    def _rearm_accepted(self, state: dict[str, Any], states: Mapping[str, Mapping[str, Any]]) -> None:
        groups: dict[str, list[dict[str, Any]]] = {}
        for event in state.get("events", {}).values():
            if not isinstance(event, dict) or event.get("delivery") != "accepted" or event.get("kind") == "message":
                continue
            recipient = event.get("recipient")
            if _valid_agent(recipient) and self._eligible_recipient(states.get(recipient, {}).get("status")):
                groups.setdefault(recipient, []).append(event)
        for recipient, events in groups.items():
            stream = None
            try:
                stream = self.stream_factory(self.socket_path)
                latest = stream.latest_turn(recipient)
            except Exception as exc:
                for event in events:
                    event["last_condition_error"] = f"cannot verify recipient turn completion: {exc}"
                continue
            finally:
                if stream is not None:
                    with contextlib.suppress(Exception):
                        stream.close()
            _, latest_id, status = self._turn_boundary(latest)
            for event in events:
                accepted_id = event.get("accepted_turn_id")
                detail = None
                if not isinstance(accepted_id, str) or not accepted_id:
                    detail = "accepted turn ID is missing; completion cannot be verified safely"
                elif accepted_id == event.get("before_turn_id"):
                    detail = "accepted turn ID matches the pre-delivery turn; completion cannot be verified safely"
                elif latest_id != accepted_id:
                    detail = f"latest turn {latest_id or 'unknown'} does not match accepted turn {accepted_id}"
                elif self._terminal_turn(status):
                    self._resolve_event(state, event["signature"], reason="accepted reminder turn completed")
                    continue
                else:
                    turn_error = event.pop("turn_completion_error", None)
                    if turn_error and event.get("last_condition_error") == turn_error:
                        event.pop("last_condition_error", None)
                    continue
                event["turn_completion_error"] = detail
                event["last_condition_error"] = detail
                state.setdefault("diagnostics", []).append({
                    "kind": "accepted_turn_unverified",
                    "task": str(event.get("task")),
                    "message": detail,
                })

    def _deliver(
        self, state: dict[str, Any], auto_candidates: Mapping[str, Mapping[str, Any]] | None = None
    ) -> None:
        now = self.clock()
        groups: dict[str, list[dict[str, Any]]] = {}
        transient: dict[str, list[Mapping[str, Any]]] = {}
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
        for event in (auto_candidates or {}).values():
            recipient = event.get("recipient")
            if _valid_agent(recipient) and event.get("automatic"):
                transient.setdefault(recipient, []).append(event)
        for recipient in set(groups) | set(transient):
            candidates = groups.get(recipient, [])
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
            recipient_observation = self._agent_states({recipient}).get(recipient, {})
            recipient_state = recipient_observation.get("status")
            if recipient_observation.get("error") or (
                recipient_state != "active" and not self._eligible_recipient(recipient_state)
            ):
                for event in current:
                    event["last_recipient_state"] = recipient_state or "unknown"
                continue
            if recipient_state == "active":
                current = [event for event in current if event.get("kind") == "message" and not event.get("defer")]
            else:
                # Both idle and notLoaded enter the targeted resume/recheck below.
                current_signatures = {event.get("signature") for event in current}
                for candidate in transient.get(recipient, []):
                    signature = candidate.get("signature")
                    if not isinstance(signature, str) or signature in current_signatures:
                        continue
                    prior = state.setdefault("events", {}).get(signature)
                    if isinstance(prior, Mapping):
                        continue
                    currentness, detail = self._event_is_current(candidate)
                    if currentness == _EVENT_CURRENT:
                        current.append(dict(candidate))
                        current_signatures.add(signature)
                    elif currentness == _EVENT_UNVERIFIABLE:
                        state.setdefault("diagnostics", []).append({
                            "kind": "reminder_condition_unverifiable",
                            "task": str(candidate.get("task")),
                            "message": detail or "reminder condition could not be verified",
                        })
            if not current:
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
                if resumed_state not in {"idle", "active"}:
                    if resumed_state == "notLoaded":
                        self._preflight_failure(current, "recipient remains notLoaded after thread/resume recheck")
                        continue
                    for event in current:
                        event["delivery"] = "pending"
                        event["last_recipient_state"] = resumed_state or "unknown"
                    continue
                if resumed_state == "active":
                    current = [event for event in current if event.get("kind") == "message" and not event.get("defer")]
                    if not current:
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
                if before_turn_status == "inProgress":
                    current = [event for event in current if event.get("kind") == "message" and not event.get("defer")]
                    if not current:
                        continue
                elif resumed_state == "active" and not self._terminal_turn(before_turn_status):
                    self._preflight_failure(current, "active recipient has no verifiable current turn")
                    continue
                payload = self._payload(current)
                if not payload:
                    continue
                channel = state.get("message_channel", "tool")
                in_progress = before_turn_status == "inProgress"
                if channel == "user" and in_progress and (
                    not isinstance(before_turn_id, str) or
                    (hasattr(stream, "start_turn") and not hasattr(stream, "steer_turn"))
                ):
                    self._preflight_failure(current, "active user-channel delivery requires a verified turn and turn/steer")
                    continue
                # Persist the attempt and its exact before-turn boundary
                # before the RPC.  A missing response can then be reconciled
                # after a crash/restart without pretending exactly-once.
                for event in current:
                    if event.get("automatic") and event.get("signature") not in state.setdefault("events", {}):
                        event.update({"created_at": _timestamp(), "attempts": 0})
                        state["events"][event["signature"]] = event
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
                    if channel == "user" and in_progress:
                        response = stream.steer_turn(recipient, before_turn_id, payload)
                    else:
                        response = stream.start_turn(recipient, payload, message_channel=channel)
                elif channel == "user" and in_progress:
                    response = stream.request("turn/steer", {"threadId": recipient, "expectedTurnId": before_turn_id,
                                                              "input": [{"type": "text", "text": payload}]})
                else:
                    params = {"threadId": recipient, "input": [{"type": "text", "text": payload}]} if channel == "user" else {
                        "threadId": recipient, "input": [],
                        "toolOutput": {"name": "message", "namespace": "mam", "output": payload},
                    }
                    response = stream.request("turn/start", params)
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
                turn = response.get("turn") if isinstance(response, Mapping) else None
                accepted_turn = turn.get("id") if isinstance(turn, Mapping) else None
                for event in current:
                    event.update({
                        "delivery": "accepted",
                        "accepted_at": _timestamp(),
                        "accepted_turn_id": accepted_turn if isinstance(accepted_turn, str) and accepted_turn else None,
                        "acknowledgement": "turn/start RPC response",
                        "last_error": None,
                    })
                    if not isinstance(accepted_turn, str) or not accepted_turn:
                        detail = "turn/start was acknowledged without a turn ID; completion cannot be verified safely"
                        event["turn_completion_error"] = detail
                        event["last_condition_error"] = detail
                        state.setdefault("diagnostics", []).append({
                            "kind": "accepted_turn_unverified",
                            "task": str(event.get("task")),
                            "message": detail,
                        })
                    else:
                        event.pop("last_condition_error", None)
                    event.pop("failure_kind", None)
                    if event.get("kind") == "message":
                        self._resolve_event(state, event["signature"], reason="message accepted")
                self._record_automatic_reminders(current)
                counters = state.setdefault("counters", {})
                counters["accepted"] = int(counters.get("accepted", 0)) + len(current)
            finally:
                if stream is not None:
                    with contextlib.suppress(Exception):
                        stream.close()
                _save_state(self.store, state)

    def _record_automatic_reminders(self, events: list[Mapping[str, Any]]) -> None:
        expected: dict[str, str] = {}
        for event in events:
            if not event.get("automatic"):
                continue
            status = event.get("expected_status")
            task_ids = event.get("reminder_tasks")
            if not isinstance(status, str) or not isinstance(task_ids, list):
                continue
            for task_id in task_ids:
                if isinstance(task_id, str):
                    expected.setdefault(task_id, status)
        for task_id, status in expected.items():
            with self.store.lock(task_id):
                task = self.store.read(task_id)
                updated, accepted = task_state.record_reminder(task, status)
                if accepted:
                    self.store.write(updated)

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
            _route_messages(state, manager)
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
            tasks = self._refresh_task_states(tasks, states)
            desired, inconclusive, diagnostics = self._desired_events(tasks, states)
            self._block_persisted_native_v2_rejections(state)
            self._native_v2_manager_escalations(state, desired, diagnostics)
            state["diagnostics"] = diagnostics
            state["healthy"] = True
            state["error"] = None
            self._reconcile_events(state, desired, inconclusive)
            self._recover_attempts_without_reply(state)
            self._rearm_accepted(state, states)
            _save_state(self.store, state)
            self._deliver(state, desired)
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
