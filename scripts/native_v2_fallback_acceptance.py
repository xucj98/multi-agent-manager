#!/usr/bin/env python3
"""Prepare and verify, but never autonomously run, a native-v2 fallback fixture.

The fallback crosses a parent-native ``collaboration.followup_task`` boundary,
which a standalone process must not impersonate.  This helper therefore keeps
the live steps intentionally manual: it creates an owned, isolated MAM state
root and verifies durable evidence after each human-controlled phase.  It does
not connect to App Server or invoke ``mam`` itself.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from collections.abc import Mapping
from typing import Any


MARKER_NAME = ".mam-native-v2-fallback-fixture.json"
MARKER_KIND = "multi-agent-manager native-v2 fallback fixture v1"
BRANCH = "fixture-native-v2"
EXACT_REJECTION = (
    "App Server request turn/start failed: direct app-server input is not allowed for multi-agent v2 sub-agents"
)
FAILURE_KIND = "unsupported_multi_agent_v2_direct_input"
MANAGER_EVENT = "manager_native_followup"
CHILD_ARCHIVE_NOTE = "native-v2 fallback fixture handled"
CONTROLLED_CLI = "from multi_agent_manager.cli import main; raise SystemExit(main())"
SOURCE_IDENTITY_FIELDS = (
    "source_root",
    "source_python",
    "source_python_resolved",
    "source_cli",
    "source_git_toplevel",
    "source_commit",
    "source_clean",
    "source_git_status",
    "source_modules",
)


class FixtureError(RuntimeError):
    """The requested fixture operation is unsafe or its evidence is incomplete."""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _absolute_path(value: str, *, field: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise FixtureError(f"{field} must be an absolute path")
    return path


def _canonical_agent(value: str, *, field: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise FixtureError(f"{field} must be a canonical AGENT-ID") from exc
    if str(parsed) != value:
        raise FixtureError(f"{field} must be a canonical AGENT-ID")
    return value


def _required_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise FixtureError(f"{field} must be a non-empty string")
    return value


def _regular_json(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise FixtureError(f"{label} is not a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise FixtureError(f"{label} is not a JSON object: {path}")
    return value


def _write_new_json(path: Path, value: Mapping[str, Any], *, label: str) -> None:
    if not path.is_absolute():
        raise FixtureError(f"{label} path must be absolute")
    if path.exists() or path.is_symlink():
        raise FixtureError(f"refusing to overwrite {label}: {path}")
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise FixtureError(f"{label} parent is not an owned directory: {path.parent}")
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise FixtureError(f"temporary {label} path already exists: {temporary}")
    try:
        payload = json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return True


def _prepare_fixture_git_isolation(root: Path) -> Path:
    """Create the only Git configuration, template, and hook paths we permit."""

    isolation = root / "git-isolation"
    isolation.mkdir(mode=0o700)
    template = isolation / "template"
    hooks = isolation / "hooks"
    template.mkdir(mode=0o700)
    hooks.mkdir(mode=0o700)
    with (isolation / "global.config").open("x", encoding="utf-8"):
        pass
    return isolation


def _fixture_git_paths(isolation: Path) -> tuple[Path, Path, Path]:
    global_config = isolation / "global.config"
    template = isolation / "template"
    hooks = isolation / "hooks"
    if (
        isolation.is_symlink()
        or not isolation.is_dir()
        or global_config.is_symlink()
        or not global_config.is_file()
        or template.is_symlink()
        or not template.is_dir()
        or hooks.is_symlink()
        or not hooks.is_dir()
    ):
        raise FixtureError("fixture Git isolation paths are no longer regular owned paths")
    return global_config, template, hooks


def _fixture_git_env(isolation: Path) -> dict[str, str]:
    """Drop every caller-supplied GIT_* value before running fixture Git."""

    global_config, template, _hooks = _fixture_git_paths(isolation)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_TEMPLATE_DIR": str(template),
        }
    )
    return environment


def _run_fixture_git(isolation: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run Git with fixture-owned configuration and no inherited Git context."""

    _global_config, template, hooks = _fixture_git_paths(isolation)
    return subprocess.run(
        [
            "git",
            "-c",
            f"core.hooksPath={hooks}",
            "-c",
            f"init.templateDir={template}",
            *arguments,
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_fixture_git_env(isolation),
    )


def _source_identity(source: Path, python: Path, git_isolation: Path) -> dict[str, Any]:
    """Resolve the exact source package and commit under isolated interpreters."""

    try:
        top_level = _run_fixture_git(
            git_isolation, ["-C", str(source), "rev-parse", "--show-toplevel"]
        ).stdout.strip()
        source_commit = _run_fixture_git(
            git_isolation, ["-C", str(source), "rev-parse", "--verify", "HEAD^{commit}"]
        ).stdout.strip()
        source_git_status = _run_fixture_git(
            git_isolation,
            [
                "-C",
                str(source),
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--ignore-submodules=none",
            ],
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FixtureError("could not verify the source worktree with isolated Git") from exc
    if top_level != str(source):
        raise FixtureError("isolated Git did not resolve the source worktree as its exact top-level")
    if not source_commit:
        raise FixtureError("isolated Git did not resolve an exact source HEAD commit")
    if source_git_status:
        raise FixtureError("source worktree is not clean under isolated Git")

    query = (
        "import json\n"
        "import multi_agent_manager\n"
        "import multi_agent_manager.cli\n"
        "import multi_agent_manager.wake_runtime\n"
        "print(json.dumps({\n"
        "  'multi_agent_manager': multi_agent_manager.__file__,\n"
        "  'multi_agent_manager.cli': multi_agent_manager.cli.__file__,\n"
        "  'multi_agent_manager.wake_runtime': multi_agent_manager.wake_runtime.__file__,\n"
        "}, sort_keys=True))\n"
    )
    try:
        imported = subprocess.run(
            [str(python), "-I", "-c", query],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        raw_paths = json.loads(imported.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise FixtureError("source isolated Python could not import the MAM CLI and wake runtime") from exc
    if not isinstance(raw_paths, Mapping):
        raise FixtureError("source isolated Python returned invalid module paths")

    package = source / "multi_agent_manager"
    if package.is_symlink() or not package.is_dir():
        raise FixtureError("source worktree has no regular multi_agent_manager package")
    package_root = package.resolve(strict=True)
    module_paths: dict[str, str] = {}
    for module in ("multi_agent_manager", "multi_agent_manager.cli", "multi_agent_manager.wake_runtime"):
        raw_path = _required_string(raw_paths.get(module), field=f"resolved {module}.__file__")
        try:
            resolved = Path(raw_path).resolve(strict=True)
        except OSError as exc:
            raise FixtureError(f"resolved {module}.__file__ does not exist") from exc
        if not resolved.is_file() or not _is_within(resolved, package_root):
            raise FixtureError(f"resolved {module}.__file__ is outside SOURCE_ROOT/multi_agent_manager")
        module_paths[module] = str(resolved)

    return {
        "source_root": str(source),
        "source_python": str(python),
        "source_python_resolved": str(python.resolve(strict=True)),
        "source_cli": [str(python), "-I", "-c", CONTROLLED_CLI],
        "source_git_toplevel": top_level,
        "source_commit": source_commit,
        "source_clean": True,
        "source_git_status": source_git_status,
        "source_modules": module_paths,
    }


def _fixture_root_for_prepare(value: str) -> Path:
    root = _absolute_path(value, field="--root")
    if root.exists() or root.is_symlink():
        raise FixtureError("fixture root must not exist before prepare")
    parent = root.parent
    if parent.is_symlink() or not parent.is_dir():
        raise FixtureError("fixture root parent must be an existing non-symlink directory")
    return root


def _load_fixture(value: str) -> tuple[Path, dict[str, Any]]:
    root = _absolute_path(value, field="--root")
    if root.is_symlink() or not root.is_dir():
        raise FixtureError("fixture root is not a regular directory")
    marker = _regular_json(root / MARKER_NAME, label="fixture ownership marker")
    if marker.get("kind") != MARKER_KIND or marker.get("root") != str(root):
        raise FixtureError("fixture ownership marker does not match this root")
    for field in ("source_root", "source_python", "manager", "child", "branch"):
        if not isinstance(marker.get(field), str) or not marker[field]:
            raise FixtureError(f"fixture ownership marker lacks {field}")
    if marker["branch"] != BRANCH:
        raise FixtureError("fixture ownership marker has an unexpected branch")
    _canonical_agent(marker["manager"], field="fixture Manager")
    _canonical_agent(marker["child"], field="fixture child")
    return root, marker


def _fixture_source(marker: Mapping[str, Any]) -> tuple[Path, Path]:
    source = _absolute_path(_required_string(marker.get("source_root"), field="fixture source root"), field="fixture source root")
    if source.is_symlink() or not source.is_dir():
        raise FixtureError("fixture source worktree is no longer a regular directory")
    source = source.resolve(strict=True)
    python = _absolute_path(_required_string(marker.get("source_python"), field="fixture source Python"), field="fixture source Python")
    if python != source / ".venv" / "bin" / "python":
        raise FixtureError("fixture ownership marker has an unexpected source Python path")
    if not python.is_file() or not os.access(python, os.X_OK):
        raise FixtureError("fixture source Python is no longer executable")
    return source, python


def _prepare_source_identity(root: Path, marker: Mapping[str, Any]) -> dict[str, Any]:
    prepare = _regular_json(root / "receipts" / "prepare.json", label="prepare receipt")
    if prepare.get("kind") != "native-v2-fallback-prepare" or prepare.get("root") != str(root):
        raise FixtureError("prepare receipt does not belong to this fixture")
    source, python = _fixture_source(marker)
    if prepare.get("source_root") != str(source) or prepare.get("source_python") != str(python):
        raise FixtureError("prepare receipt does not match the fixture source marker")
    return prepare


def _assert_source_identity_matches_prepare(current: Mapping[str, Any], prepare: Mapping[str, Any]) -> None:
    for field in SOURCE_IDENTITY_FIELDS:
        if current.get(field) != prepare.get(field):
            raise FixtureError(f"source identity drifted from prepare receipt: {field}")


def _require_fixture_identities(marker: Mapping[str, Any], args: argparse.Namespace) -> tuple[str, str]:
    manager = _canonical_agent(args.manager, field="--manager")
    child = _canonical_agent(args.child, field="--child")
    if manager == child:
        raise FixtureError("fixture Manager and child must be distinct")
    if marker.get("manager") != manager or marker.get("child") != child:
        raise FixtureError("provided Manager/child do not match the fixture ownership marker")
    return manager, child


def _task_record(root: Path, task: str) -> dict[str, Any]:
    try:
        canonical = str(uuid.UUID(task))
    except ValueError as exc:
        raise FixtureError("--task must be a canonical TASK-ID") from exc
    if canonical != task:
        raise FixtureError("--task must be a canonical TASK-ID")
    return _regular_json(root / "state" / ".local" / "tasks" / f"{task}.json", label="fixture task record")


def _service_state(root: Path) -> dict[str, Any]:
    return _regular_json(root / "state" / ".local" / "service" / "state.json", label="fixture service state")


def _events(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    events = state.get("events")
    if not isinstance(events, Mapping):
        raise FixtureError("fixture service state has no event mapping")
    result: list[dict[str, Any]] = []
    for signature, event in events.items():
        if not isinstance(signature, str) or not isinstance(event, Mapping):
            raise FixtureError("fixture service state has an invalid event")
        row = dict(event)
        if row.get("signature") != signature:
            raise FixtureError("fixture event signature does not match its state key")
        result.append(row)
    return result


def _history(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    history = state.get("history")
    if not isinstance(history, list) or not all(isinstance(item, Mapping) for item in history):
        raise FixtureError("fixture service state has an invalid history")
    return [dict(item) for item in history]


def _integer(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FixtureError(f"fixture state has invalid {field}")
    return value


def _matching_source(events: list[dict[str, Any]], task: str, job: str, child: str) -> list[dict[str, Any]]:
    return [
        event
        for event in events
        if event.get("kind") == "job_stopped"
        and event.get("task") == task
        and event.get("job") == job
        and event.get("executor") == child
        and event.get("recipient") == child
    ]


def _matching_escalation(
    events: list[dict[str, Any]], task: str, job: str, manager: str, child: str
) -> list[dict[str, Any]]:
    return [
        event
        for event in events
        if event.get("kind") == MANAGER_EVENT
        and event.get("task") == task
        and event.get("job") == job
        and event.get("executor") == child
        and event.get("recipient") == manager
    ]


def _one(events: list[dict[str, Any]], *, label: str) -> dict[str, Any]:
    if len(events) != 1:
        raise FixtureError(f"expected exactly one {label}; found {len(events)}")
    return events[0]


def _assert_source(source: Mapping[str, Any]) -> None:
    if source.get("delivery") != "blocked":
        raise FixtureError("native-v2 source was not persisted as blocked")
    if source.get("failure_kind") != FAILURE_KIND or source.get("block_kind") != FAILURE_KIND:
        raise FixtureError("native-v2 source has the wrong failure/block kind")
    if source.get("last_error") != EXACT_REJECTION:
        raise FixtureError("native-v2 source does not contain the exact direct-input rejection")
    if source.get("next_attempt_at") is not None:
        raise FixtureError("native-v2 source still has a retry deadline")
    if _integer(source.get("attempts"), field="source attempts") != 1:
        raise FixtureError("native-v2 source was retried after the precise rejection")


def _assert_source_event(source: Mapping[str, Any], *, task: str, job: str, child: str) -> None:
    if (
        source.get("kind") != "job_stopped"
        or source.get("task") != task
        or source.get("job") != job
        or source.get("executor") != child
        or source.get("recipient") != child
    ):
        raise FixtureError("native-v2 source does not identify the declared fixture task, job, and child")
    _required_string(source.get("signature"), field="native-v2 source signature")
    _assert_source(source)


def _assert_escalation_event(
    escalation: Mapping[str, Any], *, task: str, job: str, manager: str, child: str
) -> None:
    if (
        escalation.get("kind") != MANAGER_EVENT
        or escalation.get("task") != task
        or escalation.get("job") != job
        or escalation.get("executor") != child
        or escalation.get("recipient") != manager
    ):
        raise FixtureError("Manager escalation does not identify the declared fixture task, job, Manager, and child")
    _required_string(escalation.get("signature"), field="Manager escalation signature")


def _assert_escalation(source: Mapping[str, Any], escalation: Mapping[str, Any]) -> None:
    source_signature = _required_string(source.get("signature"), field="native-v2 source signature")
    if escalation.get("source_event") != source_signature:
        raise FixtureError("Manager escalation is not tied to the blocked source signature")
    if escalation.get("error") != EXACT_REJECTION:
        raise FixtureError("Manager escalation does not contain the exact direct-input rejection")
    if escalation.get("action") != "use_native_followup_task":
        raise FixtureError("Manager escalation has the wrong fallback action")


def _assert_no_extra_manager_event(events: list[dict[str, Any]], task: str, manager: str, escalation: Mapping[str, Any]) -> None:
    manager_events = [event for event in events if event.get("task") == task and event.get("recipient") == manager]
    if len(manager_events) != 1 or manager_events[0].get("signature") != escalation.get("signature"):
        raise FixtureError("fixture has an extra or missing Manager event for this task")


def _fixture_job(task_record: Mapping[str, Any], job: str) -> dict[str, Any]:
    jobs = task_record.get("jobs")
    if not isinstance(jobs, list):
        raise FixtureError("fixture task record has no job list")
    matching = [item for item in jobs if isinstance(item, Mapping) and item.get("id") == job]
    return _one([dict(item) for item in matching], label="fixture job")


def _running_fixture_context(
    root: Path, task: str, job: str, manager: str, child: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    task_record = _task_record(root, task)
    if task_record.get("agent") != child:
        raise FixtureError("fixture task is not bound to the declared native child")
    fixture_job = _fixture_job(task_record, job)
    if fixture_job.get("status") != "stopped":
        raise FixtureError("fixture job is not recorded as stopped before fallback verification")
    state = _service_state(root)
    if state.get("manager") != manager or state.get("mode") != "active" or state.get("enabled") is not True:
        raise FixtureError("fixture service is not running for the declared Manager")
    if state.get("healthy") is not True:
        raise FixtureError("fixture service is not healthy")
    events = _events(state)
    source = _one(_matching_source(events, task, job, child), label="blocked native-v2 source")
    escalation = _one(_matching_escalation(events, task, job, manager, child), label="Manager native-followup escalation")
    _assert_source_event(source, task=task, job=job, child=child)
    _assert_escalation_event(escalation, task=task, job=job, manager=manager, child=child)
    _assert_escalation(source, escalation)
    _assert_no_extra_manager_event(events, task, manager, escalation)
    counters = state.get("counters")
    if not isinstance(counters, Mapping):
        raise FixtureError("fixture service state has no counters")
    return task_record, fixture_job, state, source, escalation


def _service_process_identity(
    state: Mapping[str, Any],
    *,
    field: str = "fixture service",
    pid_field: str = "pid",
    identity_field: str = "identity",
) -> tuple[int, dict[str, Any]]:
    pid = state.get(pid_field)
    identity = state.get(identity_field)
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise FixtureError(f"{field} has no valid PID")
    if not isinstance(identity, Mapping) or not identity:
        raise FixtureError(f"{field} has no persisted process identity")
    return pid, dict(identity)


def _service_status_observation(value: str, *, manager: str) -> tuple[dict[str, Any], int]:
    try:
        status = json.loads(value)
    except json.JSONDecodeError as exc:
        raise FixtureError("--service-status is not valid JSON") from exc
    if not isinstance(status, Mapping):
        raise FixtureError("--service-status is not a JSON object")
    if status.get("running") is not False:
        raise FixtureError("--service-status does not show the fixture scheduler stopped")
    if status.get("mode") != "disabled":
        raise FixtureError("--service-status does not show the fixture scheduler disabled")
    if status.get("status") != "disabled" or status.get("manager") != manager:
        raise FixtureError("--service-status does not belong to the disabled fixture service")
    counters = status.get("counters")
    if not isinstance(counters, Mapping):
        raise FixtureError("--service-status has no counter mapping")
    return dict(status), _integer(counters.get("cycles"), field="stopped service-status cycles")


def _receipt_path(root: Path, value: str) -> Path:
    receipt = _absolute_path(value, field="--receipt")
    receipts = root / "receipts"
    if not _is_within(receipt, receipts) or receipt.parent != receipts:
        raise FixtureError("receipt must be a new direct file under FIXTURE_ROOT/receipts")
    return receipt


def _write_receipt(root: Path, value: str, payload: Mapping[str, Any]) -> None:
    receipt = _receipt_path(root, value)
    _write_new_json(receipt, payload, label="fixture receipt")


def _load_baseline(root: Path, value: str) -> dict[str, Any]:
    return _load_fixture_receipt(root, value, label="baseline receipt", field="--baseline")


def _load_fixture_receipt(root: Path, value: str, *, label: str, field: str) -> dict[str, Any]:
    baseline = _absolute_path(value, field=field)
    receipts = root / "receipts"
    if not _is_within(baseline, receipts) or baseline.parent != receipts:
        raise FixtureError(f"{label} must be a direct file inside FIXTURE_ROOT/receipts")
    return _regular_json(baseline, label=label)


def _checkpoint_payload(
    *, phase: str, task: str, job: str, manager: str, child: str, state: Mapping[str, Any], source: Mapping[str, Any], escalation: Mapping[str, Any]
) -> dict[str, Any]:
    counters = state.get("counters")
    assert isinstance(counters, Mapping)
    service_pid, service_identity = _service_process_identity(state)
    return {
        "kind": "native-v2-fallback-checkpoint",
        "phase": phase,
        "checked_at": _now(),
        "task": task,
        "job": job,
        "manager": manager,
        "child": child,
        "service_pid": service_pid,
        "service_identity": service_identity,
        "service_cycles": _integer(counters.get("cycles"), field="service cycles"),
        "turn_start_attempts": _integer(counters.get("turn_start_attempts"), field="turn-start attempts"),
        "source_signature": _required_string(source.get("signature"), field="native-v2 source signature"),
        "source_delivery": source.get("delivery"),
        "source_attempts": _integer(source.get("attempts"), field="source attempts"),
        "source_failure_kind": source.get("failure_kind"),
        "source_block_kind": source.get("block_kind"),
        "source_error": source.get("last_error"),
        "source_next_attempt_at": source.get("next_attempt_at"),
        "escalation_signature": _required_string(escalation.get("signature"), field="Manager escalation signature"),
        "escalation_source_event": escalation.get("source_event"),
        "escalation_error": escalation.get("error"),
        "escalation_action": escalation.get("action"),
        "escalation_delivery": escalation.get("delivery"),
        "escalation_attempts": _integer(escalation.get("attempts"), field="escalation attempts"),
        "escalation_accepted_at": escalation.get("accepted_at"),
    }


def _assert_checkpoint_receipt(
    receipt: Mapping[str, Any],
    *,
    phase: str,
    task: str,
    job: str,
    manager: str,
    child: str,
    escalation_delivery: str,
    escalation_attempts: int,
) -> None:
    if receipt.get("kind") != "native-v2-fallback-checkpoint" or receipt.get("phase") != phase:
        raise FixtureError(f"baseline is not a {phase} native-v2 fallback checkpoint")
    for field, expected in (("task", task), ("job", job), ("manager", manager), ("child", child)):
        if receipt.get(field) != expected:
            raise FixtureError(f"baseline has a different {field}")
    source_signature = _required_string(receipt.get("source_signature"), field="baseline source signature")
    escalation_signature = _required_string(receipt.get("escalation_signature"), field="baseline escalation signature")
    if source_signature == escalation_signature:
        raise FixtureError("baseline source and escalation signatures must differ")
    if (
        receipt.get("source_delivery") != "blocked"
        or _integer(receipt.get("source_attempts"), field="baseline source attempts") != 1
        or receipt.get("source_failure_kind") != FAILURE_KIND
        or receipt.get("source_block_kind") != FAILURE_KIND
        or receipt.get("source_error") != EXACT_REJECTION
        or receipt.get("source_next_attempt_at") is not None
    ):
        raise FixtureError("baseline does not preserve the exact blocked source")
    if (
        receipt.get("escalation_source_event") != source_signature
        or receipt.get("escalation_error") != EXACT_REJECTION
        or receipt.get("escalation_action") != "use_native_followup_task"
        or receipt.get("escalation_delivery") != escalation_delivery
        or _integer(receipt.get("escalation_attempts"), field="baseline escalation attempts") != escalation_attempts
    ):
        raise FixtureError("baseline does not preserve the exact Manager escalation")
    accepted_at = receipt.get("escalation_accepted_at")
    if escalation_delivery == "accepted":
        if not isinstance(accepted_at, str) or not accepted_at:
            raise FixtureError("accepted baseline has no Manager acknowledgement timestamp")
    elif accepted_at is not None:
        raise FixtureError("pending baseline unexpectedly has a Manager acknowledgement timestamp")
    _integer(receipt.get("service_cycles"), field="baseline service cycles")
    _integer(receipt.get("turn_start_attempts"), field="baseline turn-start attempts")
    _service_process_identity(
        receipt,
        field="baseline service",
        pid_field="service_pid",
        identity_field="service_identity",
    )


_STOPPED_BLOCKED_FIELDS = (
    "task",
    "job",
    "manager",
    "child",
    "service_pid",
    "service_identity",
    "service_cycles",
    "turn_start_attempts",
    "source_signature",
    "source_delivery",
    "source_attempts",
    "source_failure_kind",
    "source_block_kind",
    "source_error",
    "source_next_attempt_at",
    "escalation_signature",
    "escalation_source_event",
    "escalation_error",
    "escalation_action",
    "escalation_delivery",
    "escalation_attempts",
    "escalation_accepted_at",
)


def _assert_stopped_receipt(
    receipt: Mapping[str, Any],
    *,
    blocked: Mapping[str, Any],
    task: str,
    job: str,
    manager: str,
    child: str,
) -> None:
    if receipt.get("kind") != "native-v2-fallback-stopped" or receipt.get("phase") != "stopped":
        raise FixtureError("stopped baseline is not a native-v2 fallback stopped receipt")
    for field, expected in (("task", task), ("job", job), ("manager", manager), ("child", child)):
        if receipt.get(field) != expected:
            raise FixtureError(f"stopped baseline has a different {field}")
    stopped_blocked = receipt.get("blocked_checkpoint")
    if not isinstance(stopped_blocked, Mapping):
        raise FixtureError("stopped baseline has no blocked checkpoint binding")
    for field in _STOPPED_BLOCKED_FIELDS:
        if stopped_blocked.get(field) != blocked.get(field):
            raise FixtureError(f"stopped baseline is not bound to blocked checkpoint {field}")
    stopped_pid, stopped_identity = _service_process_identity(
        receipt,
        field="stopped fixture service",
        pid_field="stopped_service_pid",
        identity_field="stopped_service_identity",
    )
    if (
        stopped_pid != stopped_blocked.get("service_pid")
        or stopped_identity != stopped_blocked.get("service_identity")
    ):
        raise FixtureError("stopped baseline does not preserve the blocked daemon PID and identity")
    status = receipt.get("service_status")
    if (
        not isinstance(status, Mapping)
        or status.get("status") != "disabled"
        or status.get("running") is not False
        or status.get("mode") != "disabled"
        or status.get("manager") != manager
    ):
        raise FixtureError("stopped baseline has no disabled running:false service observation")
    status_counters = status.get("counters")
    if not isinstance(status_counters, Mapping):
        raise FixtureError("stopped baseline service observation has no counter mapping")
    stopped_cycles = _integer(receipt.get("stopped_cycles"), field="stopped service cycles")
    if stopped_cycles < _integer(stopped_blocked.get("service_cycles"), field="blocked service cycles"):
        raise FixtureError("stopped baseline cycle predates its blocked checkpoint")
    if _integer(status_counters.get("cycles"), field="stopped service-status cycles") != stopped_cycles:
        raise FixtureError("stopped baseline counter does not match its service-status observation")
    if _integer(receipt.get("stopped_turn_start_attempts"), field="stopped turn-start attempts") != stopped_blocked.get(
        "turn_start_attempts"
    ):
        raise FixtureError("stopped baseline changed the blocked daemon turn-start count")
    if receipt.get("state_enabled") is not False or receipt.get("state_mode") != "disabled":
        raise FixtureError("stopped baseline has no disabled fixture state observation")


def _record_stopped_payload(
    *,
    task: str,
    job: str,
    manager: str,
    child: str,
    blocked: Mapping[str, Any],
    state: Mapping[str, Any],
    service_status: Mapping[str, Any],
) -> dict[str, Any]:
    counters = state.get("counters")
    if not isinstance(counters, Mapping):
        raise FixtureError("fixture service state has no counters")
    service_pid, service_identity = _service_process_identity(state)
    status_counters = service_status.get("counters")
    if not isinstance(status_counters, Mapping) or dict(status_counters) != dict(counters):
        raise FixtureError("stopped service-status counters do not match fixture service state")
    stopped_cycles = _integer(counters.get("cycles"), field="stopped service cycles")
    if _integer(status_counters.get("cycles"), field="stopped service-status cycles") != stopped_cycles:
        raise FixtureError("stopped service-status cycle does not match fixture service state")
    if service_pid != blocked.get("service_pid") or service_identity != blocked.get("service_identity"):
        raise FixtureError("stopped fixture service PID or identity drifted from blocked checkpoint")
    turn_start_attempts = _integer(counters.get("turn_start_attempts"), field="stopped turn-start attempts")
    if turn_start_attempts != blocked.get("turn_start_attempts"):
        raise FixtureError("stopped fixture service changed the blocked turn-start count")
    return {
        "kind": "native-v2-fallback-stopped",
        "phase": "stopped",
        "recorded_at": _now(),
        "task": task,
        "job": job,
        "manager": manager,
        "child": child,
        "blocked_checkpoint": {field: blocked.get(field) for field in _STOPPED_BLOCKED_FIELDS},
        "stopped_service_pid": service_pid,
        "stopped_service_identity": service_identity,
        "stopped_cycles": stopped_cycles,
        "stopped_turn_start_attempts": turn_start_attempts,
        "state_enabled": state.get("enabled"),
        "state_mode": state.get("mode"),
        "service_status": {
            "status": service_status.get("status"),
            "running": service_status.get("running"),
            "healthy": service_status.get("healthy"),
            "manager": service_status.get("manager"),
            "mode": service_status.get("mode"),
            "counters": dict(status_counters),
        },
    }


def _assert_checkpoint_event_snapshot(
    source: Mapping[str, Any], escalation: Mapping[str, Any], receipt: Mapping[str, Any]
) -> None:
    source_fields = {
        "signature": "source_signature",
        "delivery": "source_delivery",
        "attempts": "source_attempts",
        "failure_kind": "source_failure_kind",
        "block_kind": "source_block_kind",
        "last_error": "source_error",
        "next_attempt_at": "source_next_attempt_at",
    }
    escalation_fields = {
        "signature": "escalation_signature",
        "source_event": "escalation_source_event",
        "error": "escalation_error",
        "action": "escalation_action",
        "delivery": "escalation_delivery",
        "attempts": "escalation_attempts",
        "accepted_at": "escalation_accepted_at",
    }
    for event, fields, label in (
        (source, source_fields, "source"),
        (escalation, escalation_fields, "Manager escalation"),
    ):
        for event_field, receipt_field in fields.items():
            if event.get(event_field) != receipt.get(receipt_field):
                raise FixtureError(f"{label} no longer matches the delivered checkpoint {receipt_field}")


def _assert_source_checkpoint_snapshot(source: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    for event_field, receipt_field in {
        "signature": "source_signature",
        "delivery": "source_delivery",
        "attempts": "source_attempts",
        "failure_kind": "source_failure_kind",
        "block_kind": "source_block_kind",
        "last_error": "source_error",
        "next_attempt_at": "source_next_attempt_at",
    }.items():
        if source.get(event_field) != receipt.get(receipt_field):
            raise FixtureError(f"source no longer matches the delivered checkpoint {receipt_field}")


def _assert_escalation_identity_snapshot(escalation: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    for event_field, receipt_field in {
        "signature": "escalation_signature",
        "source_event": "escalation_source_event",
        "error": "escalation_error",
        "action": "escalation_action",
    }.items():
        if escalation.get(event_field) != receipt.get(receipt_field):
            raise FixtureError(f"Manager escalation no longer matches the delivered checkpoint {receipt_field}")


def command_plan(_args: argparse.Namespace) -> int:
    print(
        "\n".join(
            (
                "This helper is a gated fixture preparer and durable-state verifier.",
                "It never invokes mam, connects to App Server, creates a Codex thread, or sends follow-up.",
                "Read docs/native-v2-fallback-acceptance.zh-CN.md before prepare.",
                "Use prepare only with a new absolute fixture root and CREATE_NATIVE_V2_FIXTURE.",
                "Keep the root Manager active through blocked and restarted checkpoints.",
                "Only after the root receives the one idle-time fallback may it use parent-native followup_task.",
            )
        )
    )
    return 0


def command_prepare(args: argparse.Namespace) -> int:
    if args.confirm != "CREATE_NATIVE_V2_FIXTURE":
        raise FixtureError("prepare requires --confirm CREATE_NATIVE_V2_FIXTURE")
    root = _fixture_root_for_prepare(args.root)
    source = _absolute_path(args.source_root, field="--source-root")
    if source.is_symlink() or not source.is_dir():
        raise FixtureError("--source-root must be an existing non-symlink MAM worktree")
    source = source.resolve(strict=True)
    if _is_within(root, source) or _is_within(source, root):
        raise FixtureError("fixture root and source worktree must not contain one another")
    python = source / ".venv" / "bin" / "python"
    if not python.is_file() or not os.access(python, os.X_OK):
        raise FixtureError("source worktree has no executable .venv/bin/python")
    manager = _canonical_agent(args.manager, field="--manager")
    child = _canonical_agent(args.child, field="--child")
    if manager == child:
        raise FixtureError("fixture Manager and child must be distinct")

    root.mkdir(mode=0o700)
    marker = {
        "kind": MARKER_KIND,
        "root": str(root),
        "source_root": str(source),
        "source_python": str(python),
        "manager": manager,
        "child": child,
        "branch": BRANCH,
        "created_at": _now(),
    }
    _write_new_json(root / MARKER_NAME, marker, label="fixture ownership marker")
    state, project, receipts = root / "state", root / "project", root / "receipts"
    for directory in (state, project, receipts):
        directory.mkdir(mode=0o700)
    git_isolation = _prepare_fixture_git_isolation(root)
    try:
        source_identity = _source_identity(source, python, git_isolation)
        _run_fixture_git(git_isolation, ["init", f"--initial-branch={BRANCH}", str(state)])
        _run_fixture_git(git_isolation, ["-C", str(state), "config", "user.name", "MAM native-v2 fixture"])
        _run_fixture_git(git_isolation, ["-C", str(state), "config", "user.email", "mam-native-v2-fixture@invalid"])
        (state / "README.fixture.md").write_text(
            "# Isolated native-v2 fallback fixture\n\nThis Git root is owned only by its marker.\n",
            encoding="utf-8",
        )
        _run_fixture_git(git_isolation, ["-C", str(state), "add", "README.fixture.md"])
        _run_fixture_git(
            git_isolation,
            ["-C", str(state), "commit", "--no-verify", "-m", "Initialize native-v2 fallback fixture"],
        )
        fixture_top_level = _run_fixture_git(
            git_isolation, ["-C", str(state), "rev-parse", "--show-toplevel"]
        ).stdout.strip()
        fixture_git_dir = _run_fixture_git(
            git_isolation, ["-C", str(state), "rev-parse", "--absolute-git-dir"]
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FixtureError("could not initialize or verify the isolated fixture Git state") from exc
    expected_fixture_git_dir = str((state / ".git").resolve(strict=True))
    if fixture_top_level != str(state.resolve(strict=True)) or fixture_git_dir != expected_fixture_git_dir:
        raise FixtureError("isolated Git did not create the fixture state repository in its owned directory")
    config_dir = project / ".mam"
    config_dir.mkdir(mode=0o700)
    _write_new_json(
        config_dir / "env.json",
        {"MAM_ROOT": str(state), "PROJECT_ROOT": str(project), "MAM_BRANCH": BRANCH},
        label="fixture project configuration",
    )
    (project / "README.fixture.md").write_text(
        "Run only SOURCE_ROOT/.venv/bin/python -I -c " + CONTROLLED_CLI + " from this project directory.\n",
        encoding="utf-8",
    )
    _write_new_json(
        receipts / "prepare.json",
        {
            "kind": "native-v2-fallback-prepare",
            "prepared_at": _now(),
            "root": str(root),
            **source_identity,
            "fixture_git_toplevel": fixture_top_level,
            "fixture_git_dir": fixture_git_dir,
            "manager": manager,
            "child": child,
            "side_effects": [
                "new isolated fixture directory",
                "new isolated fixture Git state",
                "new fixture project config",
            ],
            "not_done": ["no MAM task", "no scheduler", "no App Server connection", "no Codex thread or follow-up"],
        },
        label="prepare receipt",
    )
    print(
        json.dumps(
            {
                "fixture_root": str(root),
                "project": str(project),
                "state": str(state),
                "receipts": str(receipts),
                **source_identity,
                "next": "Root Manager must manually create/publish/bind the fixture task, then explicitly delegate its existing native child.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_verify_source(args: argparse.Namespace) -> int:
    """Recheck that the editable source has not drifted since fixture prepare."""

    root, marker = _load_fixture(args.root)
    source, python = _fixture_source(marker)
    prepare = _prepare_source_identity(root, marker)
    current = _source_identity(source, python, root / "git-isolation")
    _assert_source_identity_matches_prepare(current, prepare)
    payload = {
        "kind": "native-v2-fallback-source-verification",
        "phase": args.phase,
        "verified_at": _now(),
        "root": str(root),
        "prepare_receipt": "prepare.json",
        "manager": marker["manager"],
        "child": marker["child"],
        **current,
    }
    _write_receipt(root, args.receipt, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_record_stopped(args: argparse.Namespace) -> int:
    """Freeze the verified stopped service counter before the fixture restart."""

    root, marker = _load_fixture(args.root)
    manager, child = _require_fixture_identities(marker, args)
    blocked = _load_baseline(root, args.baseline)
    _assert_checkpoint_receipt(
        blocked,
        phase="blocked",
        task=args.task,
        job=args.job,
        manager=manager,
        child=child,
        escalation_delivery="pending",
        escalation_attempts=0,
    )
    task_record = _task_record(root, args.task)
    if task_record.get("agent") != child:
        raise FixtureError("fixture task is not bound to the declared native child")
    fixture_job = _fixture_job(task_record, args.job)
    if fixture_job.get("status") != "stopped":
        raise FixtureError("fixture job is not recorded as stopped before restart verification")
    state = _service_state(root)
    if state.get("manager") != manager or state.get("mode") != "disabled" or state.get("enabled") is not False:
        raise FixtureError("fixture service state is not disabled after the requested stop")
    status, _status_cycles = _service_status_observation(args.service_status, manager=manager)
    events = _events(state)
    source = _one(_matching_source(events, args.task, args.job, child), label="blocked native-v2 source")
    escalation = _one(
        _matching_escalation(events, args.task, args.job, manager, child),
        label="Manager native-followup escalation",
    )
    _assert_source_event(source, task=args.task, job=args.job, child=child)
    _assert_escalation_event(escalation, task=args.task, job=args.job, manager=manager, child=child)
    _assert_escalation(source, escalation)
    _assert_no_extra_manager_event(events, args.task, manager, escalation)
    _assert_checkpoint_event_snapshot(source, escalation, blocked)
    payload = _record_stopped_payload(
        task=args.task,
        job=args.job,
        manager=manager,
        child=child,
        blocked=blocked,
        state=state,
        service_status=status,
    )
    _write_receipt(root, args.receipt, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_record_delegation(args: argparse.Namespace) -> int:
    root, marker = _load_fixture(args.root)
    manager, child = _require_fixture_identities(marker, args)
    task_record = _task_record(root, args.task)
    if task_record.get("agent") != child:
        raise FixtureError("fixture task is not bound to the declared native child")
    attestation = args.attestation.strip()
    if "collaboration.followup_task" not in attestation:
        raise FixtureError("delegation attestation must name collaboration.followup_task")
    _write_receipt(
        root,
        args.receipt,
        {
            "kind": "native-v2-fallback-delegation",
            "recorded_at": _now(),
            "task": args.task,
            "manager": manager,
            "child": child,
            "attestation": attestation,
        },
    )
    print("delegation receipt recorded; this command did not send a message")
    return 0


def _fixture_job_archive(fixture_job: Mapping[str, Any]) -> tuple[str, str]:
    if fixture_job.get("status") != "archived":
        raise FixtureError("fixture job is not archived")
    archive = fixture_job.get("archive")
    if not isinstance(archive, Mapping):
        raise FixtureError("archived fixture job has no archive record")
    if archive.get("note") != CHILD_ARCHIVE_NOTE:
        raise FixtureError("fixture job archive note is not the controlled native-v2 fallback note")
    archived_at = _required_string(archive.get("at"), field="fixture job archive timestamp")
    return CHILD_ARCHIVE_NOTE, archived_at


def command_record_child_archive(args: argparse.Namespace) -> int:
    """Record the native child's already-completed, controlled fixture archive."""

    root, marker = _load_fixture(args.root)
    manager, child = _require_fixture_identities(marker, args)
    task_record = _task_record(root, args.task)
    if task_record.get("agent") != child:
        raise FixtureError("fixture task is not bound to the declared native child")
    fixture_job = _fixture_job(task_record, args.job)
    archive_note, archived_at = _fixture_job_archive(fixture_job)
    attestation = args.attestation.strip()
    if (
        "collaboration.followup_task" not in attestation
        or "mam job archive" not in attestation
        or args.task not in attestation
        or args.job not in attestation
        or archive_note not in attestation
    ):
        raise FixtureError(
            "child archive attestation must name collaboration.followup_task, mam job archive, this TASK-ID/JOB-ID, and the controlled note"
        )
    _write_receipt(
        root,
        args.receipt,
        {
            "kind": "native-v2-fallback-child-archive",
            "recorded_at": _now(),
            "task": args.task,
            "job": args.job,
            "manager": manager,
            "child": child,
            "job_status": fixture_job.get("status"),
            "job_archive_note": archive_note,
            "job_archived_at": archived_at,
            "attestation": attestation,
        },
    )
    print("child archive receipt recorded; this command did not archive a job or send a message")
    return 0


def _assert_child_archive_receipt(
    receipt: Mapping[str, Any],
    *,
    task: str,
    job: str,
    manager: str,
    child: str,
    fixture_job: Mapping[str, Any],
) -> None:
    if receipt.get("kind") != "native-v2-fallback-child-archive":
        raise FixtureError("child archive receipt has the wrong kind")
    for field, expected in (("task", task), ("job", job), ("manager", manager), ("child", child)):
        if receipt.get(field) != expected:
            raise FixtureError(f"child archive receipt has a different {field}")
    archive_note, archived_at = _fixture_job_archive(fixture_job)
    if (
        receipt.get("job_status") != "archived"
        or receipt.get("job_archive_note") != archive_note
        or receipt.get("job_archived_at") != archived_at
    ):
        raise FixtureError("child archive receipt does not match the fixture job archive state")
    attestation = _required_string(receipt.get("attestation"), field="child archive attestation")
    if (
        "collaboration.followup_task" not in attestation
        or "mam job archive" not in attestation
        or task not in attestation
        or job not in attestation
        or archive_note not in attestation
    ):
        raise FixtureError("child archive receipt lacks the explicit native follow-up and mam job archive attestation")


def command_assert(args: argparse.Namespace) -> int:
    root, marker = _load_fixture(args.root)
    manager, child = _require_fixture_identities(marker, args)
    task_record, fixture_job, state, source, escalation = _running_fixture_context(
        root, args.task, args.job, manager, child
    )
    del task_record, fixture_job
    counters = state["counters"]
    assert isinstance(counters, Mapping)
    phase = args.phase
    payload = _checkpoint_payload(
        phase=phase,
        task=args.task,
        job=args.job,
        manager=manager,
        child=child,
        state=state,
        source=source,
        escalation=escalation,
    )
    if phase == "blocked":
        if escalation.get("delivery") != "pending" or _integer(escalation.get("attempts"), field="escalation attempts") != 0:
            raise FixtureError("Manager escalation was delivered while the root Manager should still be active")
        if escalation.get("accepted_at") is not None or escalation.get("last_recipient_state") != "active":
            raise FixtureError("blocked checkpoint lacks evidence that the active root was not interrupted")
        if _integer(counters.get("turn_start_attempts"), field="turn-start attempts") != 1:
            raise FixtureError("blocked checkpoint observed more than the one rejected child turn/start")
    elif phase == "restarted":
        if not args.baseline or not args.stopped_baseline:
            raise FixtureError("restarted assertion requires --baseline blocked.json and --stopped-baseline stopped.json")
        baseline = _load_baseline(root, args.baseline)
        _assert_checkpoint_receipt(
            baseline,
            phase="blocked",
            task=args.task,
            job=args.job,
            manager=manager,
            child=child,
            escalation_delivery="pending",
            escalation_attempts=0,
        )
        stopped = _load_fixture_receipt(
            root,
            args.stopped_baseline,
            label="stopped baseline receipt",
            field="--stopped-baseline",
        )
        _assert_stopped_receipt(
            stopped,
            blocked=baseline,
            task=args.task,
            job=args.job,
            manager=manager,
            child=child,
        )
        _assert_checkpoint_event_snapshot(source, escalation, baseline)
        if payload["service_pid"] == stopped.get("stopped_service_pid"):
            raise FixtureError("fixture scheduler PID did not change from the stopped daemon")
        required_cycles = _integer(stopped.get("stopped_cycles"), field="stopped service cycles") + 2
        if payload["service_cycles"] < required_cycles:
            raise FixtureError("fixture scheduler did not complete two post-restart cycles")
        for field in ("source_attempts", "escalation_attempts", "turn_start_attempts"):
            if payload[field] != _integer(baseline.get(field), field=f"baseline {field}"):
                raise FixtureError("fixture scheduler retried child input or delivered Manager work during active-root restart")
        if (
            escalation.get("delivery") != "pending"
            or escalation.get("accepted_at") is not None
            or escalation.get("last_recipient_state") != "active"
        ):
            raise FixtureError("Manager escalation was delivered during the active-root restart checkpoint")
        payload["blocked_checkpoint"] = {field: baseline.get(field) for field in _STOPPED_BLOCKED_FIELDS}
        payload["stopped_checkpoint"] = {
            "service_pid": stopped.get("stopped_service_pid"),
            "service_identity": stopped.get("stopped_service_identity"),
            "service_cycles": stopped.get("stopped_cycles"),
            "turn_start_attempts": stopped.get("stopped_turn_start_attempts"),
            "service_status": stopped.get("service_status"),
        }
    elif phase == "delivered":
        if not args.baseline:
            raise FixtureError("delivered assertion requires --baseline restarted.json")
        baseline = _load_baseline(root, args.baseline)
        _assert_checkpoint_receipt(
            baseline,
            phase="restarted",
            task=args.task,
            job=args.job,
            manager=manager,
            child=child,
            escalation_delivery="pending",
            escalation_attempts=0,
        )
        _assert_source_checkpoint_snapshot(source, baseline)
        _assert_escalation_identity_snapshot(escalation, baseline)
        if escalation.get("delivery") != "accepted" or _integer(escalation.get("attempts"), field="escalation attempts") != 1:
            raise FixtureError("idle root did not receive exactly one accepted fallback escalation")
        if not isinstance(escalation.get("accepted_at"), str) or not escalation["accepted_at"]:
            raise FixtureError("accepted fallback escalation has no acknowledgement timestamp")
        expected_turn_starts = _integer(baseline.get("turn_start_attempts"), field="baseline turn-start attempts") + 1
        if payload["turn_start_attempts"] != expected_turn_starts:
            raise FixtureError("fixture did not have exactly one additional Manager turn/start after root became idle")
        attestation = (args.manager_attestation or "").strip()
        if (
            "[MAM Message]" not in attestation
            or args.task not in attestation
            or args.job not in attestation
            or EXACT_REJECTION not in attestation
        ):
            raise FixtureError(
                "--manager-attestation must record the received [MAM Message] with this TASK-ID, JOB-ID, and exact rejection"
            )
        payload["manager_attestation"] = attestation
    else:
        raise FixtureError(f"unsupported running-service assertion phase: {phase}")
    _write_receipt(root, args.receipt, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_assert_archived(args: argparse.Namespace) -> int:
    root, marker = _load_fixture(args.root)
    manager, child = _require_fixture_identities(marker, args)
    task_record = _task_record(root, args.task)
    fixture_job = _fixture_job(task_record, args.job)
    if task_record.get("agent") != child:
        raise FixtureError("fixture task is not bound to the declared native child")
    _fixture_job_archive(fixture_job)
    baseline = _load_baseline(root, args.baseline)
    _assert_checkpoint_receipt(
        baseline,
        phase="delivered",
        task=args.task,
        job=args.job,
        manager=manager,
        child=child,
        escalation_delivery="accepted",
        escalation_attempts=1,
    )
    child_archive_receipt = _load_fixture_receipt(
        root,
        args.child_archive_receipt,
        label="child archive receipt",
        field="--child-archive-receipt",
    )
    _assert_child_archive_receipt(
        child_archive_receipt,
        task=args.task,
        job=args.job,
        manager=manager,
        child=child,
        fixture_job=fixture_job,
    )
    state = _service_state(root)
    active = _events(state)
    source_signature = baseline["source_signature"]
    escalation_signature = baseline["escalation_signature"]
    active_signatures = {event["signature"] for event in active}
    if source_signature in active_signatures or escalation_signature in active_signatures:
        raise FixtureError("archived fixture job still has an active baseline source or escalation")
    history = _history(state)
    source = _one(
        [event for event in history if event.get("signature") == source_signature],
        label="baseline source history",
    )
    escalation = _one(
        [event for event in history if event.get("signature") == escalation_signature],
        label="baseline escalation history",
    )
    _assert_source_event(source, task=args.task, job=args.job, child=child)
    _assert_escalation_event(escalation, task=args.task, job=args.job, manager=manager, child=child)
    _assert_escalation(source, escalation)
    _assert_checkpoint_event_snapshot(source, escalation, baseline)
    if (
        source.get("resolution") != "condition changed or resolved"
        or escalation.get("resolution") != "condition changed or resolved"
    ):
        raise FixtureError("archived source/escalation history lacks the runtime condition-changed resolution")
    payload = {
        "kind": "native-v2-fallback-checkpoint",
        "phase": "archived",
        "checked_at": _now(),
        "task": args.task,
        "job": args.job,
        "manager": manager,
        "child": child,
        "task_status": task_record.get("status"),
        "job_status": fixture_job.get("status"),
        "source_signature": source_signature,
        "escalation_signature": escalation_signature,
        "source_error": source.get("last_error"),
        "source_attempts": source.get("attempts"),
        "escalation_source_event": escalation.get("source_event"),
        "escalation_error": escalation.get("error"),
        "escalation_action": escalation.get("action"),
        "escalation_delivery": escalation.get("delivery"),
        "escalation_attempts": escalation.get("attempts"),
        "escalation_accepted_at": escalation.get("accepted_at"),
        "job_archive_note": CHILD_ARCHIVE_NOTE,
        "job_archived_at": fixture_job["archive"]["at"],
        "source_history_resolution": source.get("resolution"),
        "escalation_history_resolution": escalation.get("resolution"),
    }
    _write_receipt(root, args.receipt, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_cleanup(args: argparse.Namespace) -> int:
    if args.confirm != "REMOVE_NATIVE_V2_FIXTURE":
        raise FixtureError("cleanup requires --confirm REMOVE_NATIVE_V2_FIXTURE")
    root, _marker = _load_fixture(args.root)
    task_record = _task_record(root, args.task)
    fixture_job = _fixture_job(task_record, args.job)
    if task_record.get("status") != "archived" or fixture_job.get("status") != "archived":
        raise FixtureError("cleanup requires the fixture task and fixture job to be archived")
    probe = fixture_job.get("probe")
    if not isinstance(probe, Mapping) or probe.get("status") != "stopped":
        raise FixtureError("cleanup requires a previously observed stopped fixture process")
    state = _service_state(root)
    if state.get("enabled") is not False or state.get("mode") != "disabled":
        raise FixtureError("cleanup requires the fixture scheduler to be stopped")
    evidence = _absolute_path(args.external_evidence, field="--external-evidence")
    if _is_within(evidence, root) or evidence.is_symlink() or not evidence.is_file():
        raise FixtureError("cleanup requires an existing evidence file outside the fixture root")
    shutil.rmtree(root)
    print(f"removed owned fixture root: {root}")
    return 0


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="prepare/check an isolated native-v2 fallback fixture; it never sends Codex input"
    )
    subcommands = command.add_subparsers(dest="command", required=True)
    subcommands.add_parser("plan", help="print the no-side-effect execution boundary").set_defaults(func=command_plan)

    prepare = subcommands.add_parser("prepare", help="create only a new marker-owned fixture project/state")
    prepare.add_argument("--root", required=True, help="new, absolute fixture root")
    prepare.add_argument(
        "--source-root",
        required=True,
        help=f"source worktree whose .venv/bin/python -I -c {CONTROLLED_CLI} will run the fixture",
    )
    prepare.add_argument("--manager", required=True, help="existing root Manager AGENT-ID")
    prepare.add_argument("--child", required=True, help="existing native child AGENT-ID")
    prepare.add_argument("--confirm", required=True, help="must equal CREATE_NATIVE_V2_FIXTURE")
    prepare.set_defaults(func=command_prepare)

    verify_source = subcommands.add_parser(
        "verify-source",
        help="recheck the clean source identity against prepare before start or after stop",
    )
    verify_source.add_argument("--root", required=True)
    verify_source.add_argument("--phase", required=True, choices=("before-start", "after-stop"))
    verify_source.add_argument("--receipt", required=True)
    verify_source.set_defaults(func=command_verify_source)

    stopped = subcommands.add_parser(
        "record-stopped",
        help="freeze a verified stopped fixture-service counter before restart",
    )
    stopped.add_argument("--root", required=True)
    stopped.add_argument("--task", required=True)
    stopped.add_argument("--job", required=True)
    stopped.add_argument("--manager", required=True)
    stopped.add_argument("--child", required=True)
    stopped.add_argument("--baseline", required=True, help="blocked.json checkpoint to bind source and old daemon")
    stopped.add_argument("--service-status", required=True, help="JSON emitted by the stopped fixture service status command")
    stopped.add_argument("--receipt", required=True)
    stopped.set_defaults(func=command_record_stopped)

    delegation = subcommands.add_parser("record-delegation", help="record a root's already-sent native delegation")
    delegation.add_argument("--root", required=True)
    delegation.add_argument("--task", required=True)
    delegation.add_argument("--manager", required=True)
    delegation.add_argument("--child", required=True)
    delegation.add_argument("--attestation", required=True)
    delegation.add_argument("--receipt", required=True)
    delegation.set_defaults(func=command_record_delegation)

    child_archive = subcommands.add_parser(
        "record-child-archive",
        help="record the child-owned fixture job archive after a real native follow-up",
    )
    child_archive.add_argument("--root", required=True)
    child_archive.add_argument("--task", required=True)
    child_archive.add_argument("--job", required=True)
    child_archive.add_argument("--manager", required=True)
    child_archive.add_argument("--child", required=True)
    child_archive.add_argument("--attestation", required=True)
    child_archive.add_argument("--receipt", required=True)
    child_archive.set_defaults(func=command_record_child_archive)

    assertion = subcommands.add_parser("assert", help="assert blocked/restarted/delivered state from fixture files")
    assertion.add_argument("--root", required=True)
    assertion.add_argument("--task", required=True)
    assertion.add_argument("--job", required=True)
    assertion.add_argument("--manager", required=True)
    assertion.add_argument("--child", required=True)
    assertion.add_argument("--phase", required=True, choices=("blocked", "restarted", "delivered"))
    assertion.add_argument("--baseline", help="blocked or restarted receipt for comparison")
    assertion.add_argument("--stopped-baseline", help="stopped.json receipt required for restarted comparison")
    assertion.add_argument("--manager-attestation", help="required only for delivered after the root saw the message")
    assertion.add_argument("--receipt", required=True)
    assertion.set_defaults(func=command_assert)

    archived = subcommands.add_parser("assert-archived", help="assert source/escalation stale after native child archives the job")
    archived.add_argument("--root", required=True)
    archived.add_argument("--task", required=True)
    archived.add_argument("--job", required=True)
    archived.add_argument("--manager", required=True)
    archived.add_argument("--child", required=True)
    archived.add_argument("--baseline", required=True, help="delivered.json checkpoint to bind history evidence")
    archived.add_argument("--child-archive-receipt", required=True, help="child-archive.json controlled attestation")
    archived.add_argument("--receipt", required=True)
    archived.set_defaults(func=command_assert_archived)

    cleanup = subcommands.add_parser("cleanup", help="remove only a stopped, archived, marker-owned fixture")
    cleanup.add_argument("--root", required=True)
    cleanup.add_argument("--task", required=True)
    cleanup.add_argument("--job", required=True)
    cleanup.add_argument("--external-evidence", required=True)
    cleanup.add_argument("--confirm", required=True, help="must equal REMOVE_NATIVE_V2_FIXTURE")
    cleanup.set_defaults(func=command_cleanup)
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except FixtureError as exc:
        print(f"native-v2 fallback fixture: FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
