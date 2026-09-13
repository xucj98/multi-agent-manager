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
    for field in ("source_root", "manager", "child", "branch"):
        if not isinstance(marker.get(field), str) or not marker[field]:
            raise FixtureError(f"fixture ownership marker lacks {field}")
    if marker["branch"] != BRANCH:
        raise FixtureError("fixture ownership marker has an unexpected branch")
    _canonical_agent(marker["manager"], field="fixture Manager")
    _canonical_agent(marker["child"], field="fixture child")
    return root, marker


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
    _assert_source(source)
    if escalation.get("source_event") != source.get("signature") or escalation.get("action") != "use_native_followup_task":
        raise FixtureError("Manager escalation is not tied to the blocked source")
    _assert_no_extra_manager_event(events, task, manager, escalation)
    counters = state.get("counters")
    if not isinstance(counters, Mapping):
        raise FixtureError("fixture service state has no counters")
    return task_record, fixture_job, state, source, escalation


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
    baseline = _absolute_path(value, field="--baseline")
    if not _is_within(baseline, root / "receipts"):
        raise FixtureError("baseline must be inside FIXTURE_ROOT/receipts")
    return _regular_json(baseline, label="baseline receipt")


def _checkpoint_payload(
    *, phase: str, task: str, job: str, manager: str, child: str, state: Mapping[str, Any], source: Mapping[str, Any], escalation: Mapping[str, Any]
) -> dict[str, Any]:
    counters = state.get("counters")
    assert isinstance(counters, Mapping)
    return {
        "kind": "native-v2-fallback-checkpoint",
        "phase": phase,
        "checked_at": _now(),
        "task": task,
        "job": job,
        "manager": manager,
        "child": child,
        "service_pid": state.get("pid"),
        "service_cycles": _integer(counters.get("cycles"), field="service cycles"),
        "turn_start_attempts": _integer(counters.get("turn_start_attempts"), field="turn-start attempts"),
        "source_signature": source.get("signature"),
        "source_attempts": _integer(source.get("attempts"), field="source attempts"),
        "escalation_signature": escalation.get("signature"),
        "escalation_attempts": _integer(escalation.get("attempts"), field="escalation attempts"),
        "escalation_delivery": escalation.get("delivery"),
        "escalation_accepted_at": escalation.get("accepted_at"),
    }


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
    mam = source / ".venv" / "bin" / "mam"
    if mam.is_symlink() or not mam.is_file() or not os.access(mam, os.X_OK):
        raise FixtureError("source worktree has no executable .venv/bin/mam")
    if not (source / "multi_agent_manager" / "wake_runtime.py").is_file():
        raise FixtureError("source worktree has no wake_runtime source")
    manager = _canonical_agent(args.manager, field="--manager")
    child = _canonical_agent(args.child, field="--child")
    if manager == child:
        raise FixtureError("fixture Manager and child must be distinct")

    root.mkdir(mode=0o700)
    marker = {
        "kind": MARKER_KIND,
        "root": str(root),
        "source_root": str(source),
        "manager": manager,
        "child": child,
        "branch": BRANCH,
        "created_at": _now(),
    }
    _write_new_json(root / MARKER_NAME, marker, label="fixture ownership marker")
    state, project, receipts = root / "state", root / "project", root / "receipts"
    for directory in (state, project, receipts):
        directory.mkdir(mode=0o700)
    try:
        subprocess.run(
            ["git", "init", f"--initial-branch={BRANCH}", str(state)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(["git", "-C", str(state), "config", "user.name", "MAM native-v2 fixture"], check=True)
        subprocess.run(
            ["git", "-C", str(state), "config", "user.email", "mam-native-v2-fixture@invalid"], check=True
        )
        (state / "README.fixture.md").write_text(
            "# Isolated native-v2 fallback fixture\n\nThis Git root is owned only by its marker.\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(state), "add", "README.fixture.md"], check=True)
        subprocess.run(["git", "-C", str(state), "commit", "-m", "Initialize native-v2 fallback fixture"], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FixtureError("could not initialize the isolated fixture Git state") from exc
    config_dir = project / ".mam"
    config_dir.mkdir(mode=0o700)
    _write_new_json(
        config_dir / "env.json",
        {"MAM_ROOT": str(state), "PROJECT_ROOT": str(project), "MAM_BRANCH": BRANCH},
        label="fixture project configuration",
    )
    (project / "README.fixture.md").write_text(
        "Run only the source-worktree .venv/bin/mam from this project directory.\n", encoding="utf-8"
    )
    _write_new_json(
        receipts / "prepare.json",
        {
            "kind": "native-v2-fallback-prepare",
            "prepared_at": _now(),
            "root": str(root),
            "source_mam": str(mam),
            "manager": manager,
            "child": child,
            "side_effects": ["new isolated fixture directory", "new isolated fixture Git state", "new fixture project config"],
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
                "source_mam": str(mam),
                "next": "Root Manager must manually create/publish/bind the fixture task, then explicitly delegate its existing native child.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
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
        if not args.baseline:
            raise FixtureError("restarted assertion requires --baseline blocked.json")
        baseline = _load_baseline(root, args.baseline)
        for field in ("task", "job", "manager", "child", "source_signature", "escalation_signature"):
            if baseline.get(field) != payload.get(field):
                raise FixtureError(f"restart baseline has a different {field}")
        if payload["service_pid"] == baseline.get("service_pid"):
            raise FixtureError("fixture scheduler PID did not change across the requested restart")
        if payload["service_cycles"] <= _integer(baseline.get("service_cycles"), field="baseline service cycles"):
            raise FixtureError("fixture scheduler did not complete a cycle after restart")
        for field in ("source_attempts", "escalation_attempts", "turn_start_attempts"):
            if payload[field] != _integer(baseline.get(field), field=f"baseline {field}"):
                raise FixtureError("fixture scheduler retried child input or delivered Manager work during active-root restart")
        if escalation.get("delivery") != "pending" or escalation.get("accepted_at") is not None:
            raise FixtureError("Manager escalation was delivered during the active-root restart checkpoint")
    elif phase == "delivered":
        if not args.baseline:
            raise FixtureError("delivered assertion requires --baseline restarted.json")
        baseline = _load_baseline(root, args.baseline)
        if escalation.get("delivery") != "accepted" or _integer(escalation.get("attempts"), field="escalation attempts") != 1:
            raise FixtureError("idle root did not receive exactly one accepted fallback escalation")
        if not isinstance(escalation.get("accepted_at"), str) or not escalation["accepted_at"]:
            raise FixtureError("accepted fallback escalation has no acknowledgement timestamp")
        expected_turn_starts = _integer(baseline.get("turn_start_attempts"), field="baseline turn-start attempts") + 1
        if payload["turn_start_attempts"] != expected_turn_starts:
            raise FixtureError("fixture did not have exactly one additional Manager turn/start after root became idle")
        attestation = (args.manager_attestation or "").strip()
        if "[MAM Message]" not in attestation or args.task not in attestation or args.job not in attestation:
            raise FixtureError("--manager-attestation must record the received [MAM Message] with this TASK-ID and JOB-ID")
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
    if fixture_job.get("status") != "archived":
        raise FixtureError("fixture job was not archived by the native child")
    report = root / "state" / ".tasks" / args.task / "report.md"
    if report.is_symlink() or not report.is_file() or not report.read_text(encoding="utf-8").strip():
        raise FixtureError("fixture child did not leave a non-empty fixture report")
    state = _service_state(root)
    active = _events(state)
    if _matching_source(active, args.task, args.job, child) or _matching_escalation(active, args.task, args.job, manager, child):
        raise FixtureError("archived fixture job still has an active blocked source or escalation")
    history = _history(state)
    source_history = _matching_source(history, args.task, args.job, child)
    escalation_history = _matching_escalation(history, args.task, args.job, manager, child)
    source = _one(source_history, label="archived source history")
    escalation = _one(escalation_history, label="archived escalation history")
    if source.get("resolution") is None or escalation.get("resolution") is None:
        raise FixtureError("archived source/escalation history lacks a stale resolution")
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
    prepare.add_argument("--source-root", required=True, help="source worktree whose .venv/bin/mam will run the fixture")
    prepare.add_argument("--manager", required=True, help="existing root Manager AGENT-ID")
    prepare.add_argument("--child", required=True, help="existing native child AGENT-ID")
    prepare.add_argument("--confirm", required=True, help="must equal CREATE_NATIVE_V2_FIXTURE")
    prepare.set_defaults(func=command_prepare)

    delegation = subcommands.add_parser("record-delegation", help="record a root's already-sent native delegation")
    delegation.add_argument("--root", required=True)
    delegation.add_argument("--task", required=True)
    delegation.add_argument("--manager", required=True)
    delegation.add_argument("--child", required=True)
    delegation.add_argument("--attestation", required=True)
    delegation.add_argument("--receipt", required=True)
    delegation.set_defaults(func=command_record_delegation)

    assertion = subcommands.add_parser("assert", help="assert blocked/restarted/delivered state from fixture files")
    assertion.add_argument("--root", required=True)
    assertion.add_argument("--task", required=True)
    assertion.add_argument("--job", required=True)
    assertion.add_argument("--manager", required=True)
    assertion.add_argument("--child", required=True)
    assertion.add_argument("--phase", required=True, choices=("blocked", "restarted", "delivered"))
    assertion.add_argument("--baseline", help="blocked or restarted receipt for comparison")
    assertion.add_argument("--manager-attestation", help="required only for delivered after the root saw the message")
    assertion.add_argument("--receipt", required=True)
    assertion.set_defaults(func=command_assert)

    archived = subcommands.add_parser("assert-archived", help="assert source/escalation stale after native child archives the job")
    archived.add_argument("--root", required=True)
    archived.add_argument("--task", required=True)
    archived.add_argument("--job", required=True)
    archived.add_argument("--manager", required=True)
    archived.add_argument("--child", required=True)
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
