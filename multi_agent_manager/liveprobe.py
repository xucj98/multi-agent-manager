"""Bounded real-delivery acceptance for the MAM installer.

This module is intentionally separate from :mod:`wake_compat`.  The latter is
safe to run at scheduler startup and reconnection because it never touches a
registered thread.  This module is an installer-only, Manager-authorized
acceptance run: it creates a disposable MAM project and dedicated persisted
Codex threads, then proves the real detached scheduler delivers both an exited
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


MODEL = "gpt-6-sol"
EFFORT = "high"
MAX_MODEL_TURNS = 6
DEFAULT_TIMEOUT_SECONDS = 600.0
POLL_SECONDS = 0.5
# Codex acknowledges ``turn/start`` before the rollout JSONL is always visible
# to a following ``thread/resume``.  Keep this retry bounded and local to that
# post-turn persistence race; never replay the model turn itself.
RESUME_PERSISTENCE_RETRY_DELAYS = (0.05, 0.1, 0.2, 0.4, 0.8)
_MARKER = ".mam-liveprobe.json"
_MARKER_KIND = "multi-agent-manager live delivery fixture v1"
_ROLE_ORDER = ("manager", "job_executor")
_BASELINE_MARKERS = {
    "manager": "PROBE_MANAGER_BASELINE_READY",
    "job_executor": "PROBE_JOB_EXECUTOR_BASELINE_READY",
}
_FOLLOWUP_PROMPT = "Reply exactly PROBE_USER_AFTER_COMPACTION_READY."


def _baseline_prompt(role: str) -> str:
    # Normal MAM agents have performed real tools before receiving a wakeup.
    # Materialize that history without shell, filesystem, or network access.
    marker = _BASELINE_MARKERS[role]
    return (
        f'Call functions.exec once with exactly this JavaScript: text("{marker}"); '
        f"then reply exactly {marker}."
    )


class LiveProbeError(RuntimeError):
    """The authorized isolated delivery acceptance could not prove behavior."""


def _redact(value: Any, *, limit: int = 700) -> str:
    """Keep useful operational details while never copying likely secrets."""

    text = " ".join(str(value).split())[:limit]
    return re.sub(r"(?i)\b(token|secret|password|api[_-]?key)\s*=\s*[^\s,;]+", r"\1=<redacted>", text)


def _missing_rollout(error: Exception) -> bool:
    """Treat an App Server thread already absent from rollout storage as clean."""

    return "no rollout found" in str(error).lower()


def _empty_rollout_metadata(error: Exception) -> bool:
    """Match only the observed post-turn empty-rollout persistence race."""

    text = str(error).lower()
    if "failed to read session metadata" not in text:
        return False
    return re.search(r"rollout at .+ is empty(?:$|[.;])", text) is not None


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


@contextlib.contextmanager
def _as_thread(thread_id: str) -> Any:
    """Run a fixture CLI operation as its persisted native executor thread."""

    present = "CODEX_THREAD_ID" in os.environ
    previous = os.environ.get("CODEX_THREAD_ID")
    os.environ["CODEX_THREAD_ID"] = thread_id
    try:
        yield
    finally:
        if present and previous is not None:
            os.environ["CODEX_THREAD_ID"] = previous
        else:
            os.environ.pop("CODEX_THREAD_ID", None)


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


def _custom_tool_execution(turn: Mapping[str, Any], marker: str) -> dict[str, str] | None:
    """Prove a baseline through the recorded custom call and its matching output.

    Assistant text can repeat a requested marker without running a tool.  The
    App Server stores the call and output as response items; accept only an
    ``exec`` call whose ``call_id`` is present on a completed output containing
    the marker.
    """

    items = turn.get("items")
    if not isinstance(items, list):
        return None
    calls: dict[str, Mapping[str, Any]] = {}
    outputs: dict[str, Mapping[str, Any]] = {}

    def text(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, Mapping):
            return "\n".join(text(child) for child in value.values())
        if isinstance(value, list):
            return "\n".join(text(child) for child in value)
        return ""

    for item in items:
        if not isinstance(item, Mapping):
            continue
        kind = item.get("type")
        call_id = item.get("call_id") or item.get("callId")
        if not isinstance(call_id, str) or not call_id:
            continue
        if kind in {"custom_tool_call", "customToolCall", "functionCall"} and item.get("name") in {"exec", "functions.exec"}:
            calls[call_id] = item
        elif kind in {"custom_tool_call_output", "customToolCallOutput", "functionCallOutput"}:
            outputs[call_id] = item
    for call_id, call in calls.items():
        output = outputs.get(call_id)
        if output is None:
            continue
        call_input = text(call.get("input"))
        output_text = text(output.get("output"))
        output_status = output.get("status")
        if output_status in {"failed", "error", "incomplete"}:
            continue
        if (
            marker in call_input
            and marker in output_text
            and "script completed" in output_text.lower()
            and "script failed" not in output_text.lower()
        ):
            return {"call_id": call_id, "name": str(call.get("name")), "marker": marker}
    return None


def _rollout_token_usage(thread_id: str) -> dict[str, int] | None:
    """Read the final cumulative token_count snapshot for one fixture thread."""

    sessions = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions"
    if not sessions.is_dir() or sessions.is_symlink():
        return None
    candidates = [path for path in sessions.rglob(f"*{thread_id}*.jsonl") if path.is_file() and not path.is_symlink()]
    if not candidates:
        return None
    latest: dict[str, int] | None = None
    latest_mtime = -1.0
    for path in candidates:
        try:
            if path.stat().st_size > 128 * 1024 * 1024:
                continue
            snapshots: list[Mapping[str, Any]] = []
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                payload = row.get("payload") if isinstance(row, Mapping) else None
                info = payload.get("info") if isinstance(payload, Mapping) and payload.get("type") == "token_count" else None
                total = info.get("total_token_usage") if isinstance(info, Mapping) else None
                if isinstance(total, Mapping):
                    snapshots.append(total)
            if not snapshots:
                continue
            final = snapshots[-1]
            usage = {
                output: final[source]
                for output, source in {
                    "input_tokens": "input_tokens",
                    "cached_input_tokens": "cached_input_tokens",
                    "output_tokens": "output_tokens",
                    "reasoning_tokens": "reasoning_output_tokens",
                }.items()
                if isinstance(final.get(source), int) and not isinstance(final.get(source), bool)
            }
            mtime = path.stat().st_mtime
            if usage and mtime >= latest_mtime:
                latest, latest_mtime = usage, mtime
        except (OSError, UnicodeDecodeError):
            continue
    return latest


def _rollout_tool_execution(
    thread_id: str, marker: str, *, target_turn_id: str | None = None
) -> dict[str, str] | None:
    """Read one raw rollout turn when ``turns/list`` normalizes tools."""

    sessions = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions"
    if not sessions.is_dir() or sessions.is_symlink():
        return None
    for path in sessions.rglob(f"*{thread_id}*.jsonl"):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024 * 1024:
            continue
        try:
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        session = rows[0].get("payload") if rows and isinstance(rows[0], Mapping) else None
        if isinstance(session, Mapping) and session.get("id") not in {None, thread_id}:
            continue
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        current: str | None = None
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            payload = row.get("payload")
            if row.get("type") == "event_msg" and isinstance(payload, Mapping):
                kind = payload.get("type")
                if kind in {"task_started", "turn_context"}:
                    value = payload.get("turn_id")
                    current = value if isinstance(value, str) else current
                elif kind == "item_completed" and payload.get("thread_id") == thread_id:
                    value = payload.get("turn_id")
                    current = value if isinstance(value, str) else current
                continue
            if row.get("type") != "response_item" or not isinstance(payload, Mapping):
                continue
            metadata = payload.get("internal_chat_message_metadata_passthrough")
            item_turn = metadata.get("turn_id") if isinstance(metadata, Mapping) else None
            bucket = current or (item_turn if isinstance(item_turn, str) else None)
            if bucket:
                grouped.setdefault(bucket, []).append(payload)
        if target_turn_id:
            candidates = [grouped.get(target_turn_id, [])]
        elif len(grouped) == 1:
            candidates = list(grouped.values())
        else:
            candidates = []
        for items in candidates:
            execution = _custom_tool_execution({"items": items}, marker)
            if execution is not None:
                return {**execution, "source": "rollout"}
    return None


def _fixture_executor_path(role: str) -> str:
    return f"/root/liveprobe/{role}"


def _inbound_items(turn: Mapping[str, Any]) -> list[dict[str, str]]:
    """Extract inbound text from one fixture-owned scheduler turn."""

    inbound: list[dict[str, str]] = []
    items = turn.get("items")
    if not isinstance(items, list):
        return inbound
    for item in items:
        if not isinstance(item, Mapping):
            continue
        kind = item.get("type")
        if kind == "userMessage":
            content = item.get("content")
            if not isinstance(content, list):
                continue
            text = "".join(
                part["text"] for part in content
                if isinstance(part, Mapping) and part.get("type") == "text" and isinstance(part.get("text"), str)
            )
            inbound.append({"item_type": kind, "text": text})
        elif kind == "functionCallOutput":
            output = item.get("output")
            if isinstance(output, str):
                text = output
            elif isinstance(output, list):
                text = "".join(
                    part["text"] for part in output
                    if isinstance(part, Mapping) and part.get("type") == "input_text"
                    and isinstance(part.get("text"), str)
                )
            else:
                continue
            inbound.append({
                "item_type": kind, "text": text,
                "name": str(item.get("name", "")), "namespace": str(item.get("namespace", "")),
            })
    return inbound


def _delivery_input(turn: Mapping[str, Any], expected_lines: list[str]) -> dict[str, str] | None:
    """Match one inbound MAM message in the completed scheduler turn."""

    if turn.get("status") != "completed":
        return None
    for item in _inbound_items(turn):
        if item["item_type"] == "functionCallOutput" and (
            item["name"] != "message" or item["namespace"] != "mam"
        ):
            continue
        lines = item["text"].splitlines()
        if all(line in lines for line in expected_lines):
            return {"item_type": item["item_type"], "text": item["text"]}
    return None


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
        self._prepare_git_instance()
        self.store = cli.Store(self.config)
        self.stream: Any | None = None
        self.tasks: dict[str, str] = {}
        self.threads: dict[str, str] = {}
        self.jobs: list[tuple[str, str]] = []
        self.blockers: list[subprocess.Popen[bytes]] = []
        # Only direct turn IDs are known before their history is
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
            "token_usage": {
                "input_tokens": None,
                "cached_input_tokens": None,
                "output_tokens": None,
                "reasoning_tokens": None,
                "source": "unknown-until-finalized",
            },
            "calls": {"thread_start": 0, "direct_turn_start": 0, "compact_start": 0},
            "checks": {
                "fixture_tasks_registered_before_threads": False,
                "executor_bound_before_first_model_turn": False,
                "all_roles_baselined_before_service": False,
                "baseline_history_read_after_idle": False,
                "job_delivery": False,
                "manager_delivery": False,
                "manager_is_fixture_only": False,
                "turn_budget": False,
                "service_stopped_after_delivery": False,
                "baseline_custom_tool_calls": False,
                "job_archived_before_manager_delivery": False,
                "manager_compaction": False,
                "manager_user_followup": False,
            },
            "resources": {"tasks": {}, "threads": {}, "jobs": {}, "turns": {}},
            "history": {},
            "delivery_inputs": {},
            "completion_events": {},
            "resume_persistence": {},
            "turn_counts": {},
            "phase_elapsed_seconds": {},
            "cleanup": {
                "service": "not_started",
                "jobs": "not_started",
                "tasks": "not_started",
                "threads": "not_started",
                "thread_interrupt": {},
                "thread_archive": {},
            },
        }

    def _prepare_git_instance(self) -> None:
        """Create the disposable Git instance required by Store/task cleanup."""

        try:
            self.config.mam_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.config.project_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            subprocess.run(["git", "init", "--quiet", str(self.config.mam_root)], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "-C", str(self.config.mam_root), "config", "user.email", "liveprobe@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(self.config.mam_root), "config", "user.name", "MAM liveprobe"], check=True)
            (self.config.mam_root / "README").write_text("liveprobe fixture\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(self.config.mam_root), "add", "README"], check=True)
            subprocess.run(
                ["git", "-C", str(self.config.mam_root), "commit", "--quiet", "-m", "initialize liveprobe fixture"],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "-C", str(self.config.mam_root), "branch", "liveprobe/state"],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            subprocess.run(["git", "init", "--quiet", str(self.config.project_root)], check=True, stdout=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise LiveProbeError(f"cannot initialize isolated Git instance: {_redact(exc)}") from exc

    def _deadline(self) -> float:
        return self.deadline

    @contextlib.contextmanager
    def _timed_phase(self, phase: str) -> Any:
        started = self.clock()
        try:
            yield
        finally:
            self.evidence["phase_elapsed_seconds"][phase] = round(self.clock() - started, 3)

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
        titles = {"job": "MAM liveprobe exited-job and pending delivery"}
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
                "config": {"model_reasoning_effort": EFFORT},
                "sandbox": "read-only",
                "approvalPolicy": "never",
                "developerInstructions": (
                    "MAM installer acceptance fixture. Perform only the one harmless code execution "
                    "explicitly requested by the initial baseline, then reply with the requested marker. "
                    "Do not run shell commands, access files or network, or create agents. "
                    "On later MAM notifications, acknowledge briefly without using tools."
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
        bindings = {"job": "job_executor"}
        for task_role, thread_role in bindings.items():
            try:
                # App Server ``thread/start`` creates ordinary persisted
                # threads, not native subagents, so the product's ``task
                # start`` command correctly rejects them.  Prepare the
                # fixture's existing task records directly in its disposable
                # Store; native identity validation remains unchanged in CLI.
                self._prepare_binding(task_role, thread_role)
            except Exception as exc:
                raise LiveProbeError(f"cannot prepare fixture {task_role} executor: {_redact(exc)}") from exc
        self.evidence["checks"]["executor_bound_before_first_model_turn"] = True
        self.evidence["checks"]["manager_is_fixture_only"] = True

    def _prepare_binding(self, task_role: str, thread_role: str) -> None:
        task_id = self.tasks[task_role]
        agent = self.threads[thread_role]
        with self.store.lock(task_id):
            data = self.store.read(task_id, writable=True)
            data["agent"] = agent
            data["identity"] = {"path": _fixture_executor_path(thread_role), "tree_root": self.threads["manager"]}
            data["status"] = "working"
            self.store.write(data)

    def _commit_git_fixture_state(self) -> None:
        """Make the disposable Store clean before ``task archive`` preflight."""

        subprocess.run(
            ["git", "-C", str(self.config.mam_root), "add", "-A"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "-C", str(self.config.mam_root), "commit", "--quiet", "--allow-empty", "-m", "liveprobe fixture state"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

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

    def _register_jobs(self) -> str:
        self.stage = "register fixture jobs"
        job_process = self._spawn_blocker()
        try:
            job = cli.job_add(
                self.store,
                SimpleNamespace(
                    task=self.tasks["job"], host="local", pid=job_process.pid, note="liveprobe-short-job-exit"
                ),
            )
        except Exception as exc:
            raise LiveProbeError(f"cannot register fixture exited-job probe: {_redact(exc)}") from exc
        job_id = job.get("id") if isinstance(job, Mapping) else None
        if not isinstance(job_id, str) or not job_id:
            raise LiveProbeError("fixture exited-job registration returned no JOB-ID")
        self.jobs.append((self.tasks["job"], job_id))
        self.evidence["resources"]["jobs"]["exited"] = job_id

        return job_id

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

    def _subscribe_to_turn_events(self, role: str) -> None:
        """Subscribe immediately after an accepted baseline turn starts.

        A new persisted thread deliberately has no rollout to resume before its
        first user turn.  ``turn/start`` materializes that rollout, after which
        this metadata-only resume subscribes before the turn can be inspected.
        """

        record: dict[str, Any] = {"attempts": 0, "retry_delays": [], "result": "pending"}
        self.evidence["resume_persistence"][role] = record
        for retry_index, delay in enumerate((0.0, *RESUME_PERSISTENCE_RETRY_DELAYS)):
            record["attempts"] += 1
            try:
                result = self._request(
                    "thread/resume", {"threadId": self.threads[role], "excludeTurns": True}
                )
            except LiveProbeError as exc:
                if not _empty_rollout_metadata(exc):
                    record["result"] = "failed_unrelated_error"
                    raise
                if retry_index == len(RESUME_PERSISTENCE_RETRY_DELAYS):
                    record["result"] = "failed_retry_limit"
                    raise
                if self.clock() + RESUME_PERSISTENCE_RETRY_DELAYS[retry_index] > self._deadline():
                    record["result"] = "failed_timeout"
                    raise
                retry_delay = RESUME_PERSISTENCE_RETRY_DELAYS[retry_index]
                record["retry_delays"].append(retry_delay)
                self.sleeper(retry_delay)
            else:
                record["result"] = "subscribed_after_retry" if retry_index else "subscribed"
                break
        status = _thread_status(result)
        if _status_is_interrupted(status) or status not in {"active", "idle", "notLoaded"}:
            raise LiveProbeError(f"fixture {role} could not subscribe from its {status} state")

    def _event_completed_turn_id(self, event: Any, thread_id: str) -> str | None:
        if not isinstance(event, Mapping) or event.get("method") != "turn/completed":
            return None
        params = event.get("params")
        if not isinstance(params, Mapping) or params.get("threadId") != thread_id:
            return None
        turn = params.get("turn")
        turn_id = turn.get("id") if isinstance(turn, Mapping) else None
        return turn_id if isinstance(turn_id, str) and turn_id else None

    def _wait_for_completion_event(
        self, role: str, label: str, phase: str, *, expected_turn_id: str | None = None, deadline: float | None = None
    ) -> str:
        """Wait for the App Server's actual completion notification.

        Some App Server builds can publish idle metadata before a just-accepted
        turn is reflected as completed in paged history.  A subscription made
        immediately after ``turn/start`` gives this fixture a completion fact
        without polling history while that turn is still active.
        """

        deadline = self._deadline() if deadline is None else deadline
        poll = getattr(self.stream, "poll", None)
        if not callable(poll):
            raise LiveProbeError("App Server control stream cannot await turn/completed notifications")
        thread_id = self.threads[role]
        while True:
            try:
                event = poll(min(POLL_SECONDS, max(0.0, deadline - self.clock())))
            except Exception as exc:
                raise LiveProbeError(f"App Server turn/completed wait failed: {_redact(exc)}") from exc
            completed_id = self._event_completed_turn_id(event, thread_id)
            if completed_id is not None:
                if expected_turn_id is not None and completed_id != expected_turn_id:
                    raise LiveProbeError(
                        f"fixture {label} completed unexpected turn {completed_id}; expected {expected_turn_id}"
                    )
                self.evidence["completion_events"][self._history_key(role, phase)] = {
                    "method": "turn/completed",
                    "thread_id": thread_id,
                    "turn_id": completed_id,
                }
                return completed_id
            self._expired(deadline, label)

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

    def _wait_for_turn_delivery(
        self, role: str, expected: list[str], minimum_turns: int, label: str, phase: str,
        *, expected_turn_id: str | None = None,
    ) -> Mapping[str, Any]:
        deadline = self._deadline()
        completed_id = self._wait_for_completion_event(
            role, label, phase, expected_turn_id=expected_turn_id, deadline=deadline
        )
        self._wait_for_idle(role, label, deadline=deadline)
        turns = self._thread_turns_after_idle(role, phase)
        turn = next((item for item in turns if item.get("id") == completed_id), None)
        receipt: dict[str, Any] = {
            "thread_id": self.threads[role], "turn_id": completed_id,
            "matched": False, "observed_turns": _turn_summaries(turns),
        }
        if isinstance(turn, Mapping):
            receipt["status"] = turn.get("status")
            receipt["inbound_items"] = [
                {**item, "text": _redact(item["text"])} for item in _inbound_items(turn)
            ]
        self.evidence["delivery_inputs"][phase] = receipt
        if isinstance(turn, Mapping) and len(turns) >= minimum_turns:
            received = _delivery_input(turn, expected)
            if received is not None:
                receipt.update({**received, "text": _redact(received["text"]), "matched": True})
                self._record_paged_history(role, phase, turns)
                return turn
        raise LiveProbeError(f"fixture {label} completed turn {completed_id} without matching inbound delivery")

    def _start_baseline_turn(self, role: str) -> None:
        self.stage = f"start fixture {role} baseline turn"
        if role != "manager" and not self.evidence["checks"]["executor_bound_before_first_model_turn"]:
            raise LiveProbeError("fixture executor was not bound before its first model turn")
        marker = _BASELINE_MARKERS[role]
        result = self._request(
            "turn/start",
            {
                "threadId": self.threads[role],
                "input": [{"type": "text", "text": _baseline_prompt(role)}],
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
        self._subscribe_to_turn_events(role)
        self._wait_for_completion_event(
            role, f"fixture {role} baseline completion", "baseline", expected_turn_id=turn_id
        )
        self._wait_for_idle(role, f"fixture {role} baseline completion")
        turns = self._thread_turns_after_idle(role, "baseline")
        completed = next((item for item in turns if item.get("id") == turn_id), None)
        if not isinstance(completed, Mapping) or completed.get("status") != "completed":
            raise LiveProbeError(f"fixture {role} baseline did not complete under its acknowledged turn id")
        execution = _custom_tool_execution(completed, marker) or _rollout_tool_execution(
            self.threads[role], marker, target_turn_id=turn_id
        )
        if execution is None:
            raise LiveProbeError(f"fixture {role} baseline lacks a matching custom exec call/output")
        self.evidence.setdefault("baseline_tool_calls", {})[role] = execution
        self._record_paged_history(role, "baseline", turns)
        self.active_direct_turns.pop(role, None)
        self.evidence["resources"]["turns"][f"{role}_baseline_completed"] = turn_id

    def _start_all_baseline_turns(self) -> None:
        self.stage = "materialize all dedicated fixture roles"
        for role in _ROLE_ORDER:
            self._start_baseline_turn(role)
        self.evidence["checks"]["all_roles_baselined_before_service"] = True
        self.evidence["checks"]["baseline_history_read_after_idle"] = True
        self.evidence["checks"]["baseline_custom_tool_calls"] = True

    def _wait_for_manager_delivery(self) -> None:
        self.stage = "verify fixture Manager delivery"
        action = (
            "Check the task and any published report; start or continue the work, request review, "
            "block or archive the task."
        )
        manager_payloads = [
            "[MAM MESSAGE]",
            f"[task pending | {_fixture_executor_path('job_executor')}]",
            action,
        ]
        manager_turn = self._wait_for_turn_delivery(
            "manager", manager_payloads, 3, "Manager-ready scheduler turn", "manager_delivery"
        )
        manager_turn_id = manager_turn.get("id")
        if not isinstance(manager_turn_id, str) or not manager_turn_id:
            raise LiveProbeError("Manager-ready scheduler delivery returned no turn id")
        self.evidence["resources"]["turns"]["manager_ready_delivery"] = manager_turn_id
        self.evidence["checks"]["manager_delivery"] = True

    def _compact_manager(self) -> None:
        self.stage = "compact fixture Manager before scheduler delivery"
        self.evidence["calls"]["compact_start"] += 1
        self._request("thread/compact/start", {"threadId": self.threads["manager"]})
        turn_id = self._wait_for_completion_event(
            "manager", "fixture Manager compaction completion", "manager_compaction"
        )
        self._wait_for_idle("manager", "fixture Manager compaction completion")
        turns = self._thread_turns_after_idle("manager", "manager_compaction")
        turn = next((item for item in turns if item.get("id") == turn_id), None)
        self._record_paged_history("manager", "manager_compaction", turns)
        self.evidence["resources"]["turns"]["manager_compaction"] = turn_id
        if (
            not isinstance(turn, Mapping) or turn.get("status") != "completed"
            or not any(
                isinstance(item, Mapping) and item.get("type") == "contextCompaction"
                for item in turn.get("items", [])
            )
        ):
            raise LiveProbeError(f"fixture Manager compaction turn {turn_id} did not complete with contextCompaction")
        self.evidence["checks"]["manager_compaction"] = True

    def _start_manager_user_followup(self) -> None:
        self.stage = "verify ordinary fixture Manager input after compacted notification"
        response = _mapping(self._request(
            "turn/start", {
                "threadId": self.threads["manager"],
                "input": [{"type": "text", "text": _FOLLOWUP_PROMPT}],
                "model": MODEL, "effort": EFFORT,
            },
        ), "App Server turn/start")
        turn = _mapping(response.get("turn"), "fixture Manager user followup turn/start")
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            raise LiveProbeError("fixture Manager user followup turn/start returned no turn id")
        self.evidence["calls"]["direct_turn_start"] += 1
        self.active_direct_turns["manager"] = turn_id
        self.evidence["resources"]["turns"]["manager_user_followup"] = turn_id
        self._wait_for_turn_delivery(
            "manager", [_FOLLOWUP_PROMPT], 4, "ordinary user followup turn", "manager_user_followup",
            expected_turn_id=turn_id,
        )
        if self.evidence["delivery_inputs"]["manager_user_followup"]["item_type"] != "userMessage":
            raise LiveProbeError("fixture Manager user followup has no matching ordinary user input")
        self.active_direct_turns.pop("manager", None)
        self.evidence["checks"]["manager_user_followup"] = True

    def _stop_service_after_delivery(self) -> None:
        self.runtime.stop_service(self.config)
        deadline = self._deadline()
        while self.clock() < deadline:
            if self.runtime.service_status(self.config).get("running") is False:
                return
            self.sleeper(POLL_SECONDS)
        raise LiveProbeError("fixture scheduler did not stop after delivery")

    def _archive_exited_job(self) -> None:
        """Archive the delivered job so the same task becomes Manager-pending."""

        self.stage = "archive delivered fixture job"
        job_id = self.evidence["resources"]["jobs"].get("exited")
        if not isinstance(job_id, str):
            raise LiveProbeError("fixture exited-job delivery has no JOB-ID to archive")
        try:
            cli.job_archive(self.store, SimpleNamespace(job=job_id, note="liveprobe fixture worker completed"))
        except Exception as exc:
            raise LiveProbeError(f"cannot archive delivered fixture job: {_redact(exc)}") from exc
        self.evidence["checks"]["job_archived_before_manager_delivery"] = True

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
        self.stage = "verify fixture baseline turn distribution"
        counts = self._turn_counts_after_idle("before_job_stop")
        if any(counts[role] != 1 for role in _ROLE_ORDER):
            raise LiveProbeError(f"fixture pre-stop turn distribution is unexpected: {counts}")

    def _wait_for_exited_job_delivery(self) -> dict[str, int]:
        self.stage = "verify exited-job scheduler delivery"
        job_turn = self._wait_for_turn_delivery(
            "job_executor", [
                "[MAM MESSAGE]",
                f"[job exited | {_fixture_executor_path('job_executor')}]",
                "There are exited jobs. Check the results and archive them.",
            ],
            2, "exited-job scheduler turn", "exited_job_delivery"
        )
        job_turn_id = job_turn.get("id")
        if not isinstance(job_turn_id, str) or not job_turn_id:
            raise LiveProbeError("exited-job scheduler delivery returned no turn id")
        self.evidence["resources"]["turns"]["exited_job_delivery"] = job_turn_id
        self.evidence["checks"]["job_delivery"] = True
        # Pause the disposable scheduler between phases so accepted events do
        # not generate reminder turns while the worker archive is prepared.
        self._stop_service_after_delivery()
        self.evidence["checks"]["service_stopped_after_delivery"] = True
        with self._timed_phase("manager_compaction"):
            self._compact_manager()
        self._archive_exited_job()
        self._start_service()
        self._wait_for_service()
        with self._timed_phase("manager_delivery"):
            self._wait_for_manager_delivery()
        self._stop_service_after_delivery()
        with self._timed_phase("manager_user_followup"):
            self._start_manager_user_followup()
        counts = self._turn_counts_after_idle("after_job_stop")
        if counts["manager"] != 4 or counts["job_executor"] != 2:
            raise LiveProbeError(f"fixture model turn distribution is unexpected: {counts}")
        observed = sum(counts.values())
        if observed > MAX_MODEL_TURNS:
            raise LiveProbeError(
                f"fixture observed {observed} model turns, exceeding the acceptance limit of {MAX_MODEL_TURNS}"
            )
        self.evidence["checks"]["turn_budget"] = True
        self.evidence["model_turns"] = observed
        return counts

    def _collect_token_usage(self) -> None:
        by_thread: dict[str, dict[str, int]] = {}
        for role, thread_id in self.threads.items():
            usage = _rollout_token_usage(thread_id)
            if usage:
                by_thread[role] = usage
        if not by_thread:
            self.evidence["token_usage"]["source"] = "rollout-token-count-unavailable"
            return
        totals = {}
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"):
            values = [by_thread.get(role, {}).get(key) for role in self.threads]
            totals[key] = sum(values) if all(isinstance(value, int) and value >= 0 for value in values) else None
        self.evidence["token_usage"] = {**totals, "source": "Codex rollout token_count total_token_usage"}
        self.evidence["token_usage_by_thread"] = by_thread
        if self.evidence.get("calls", {}).get("compact_start", 0):
            # Rollout totals omit explicit compaction usage on current Codex.
            # Keep the observable subtotal without claiming a complete total.
            self.evidence["rollout_token_usage_excluding_compaction"] = self.evidence["token_usage"]
            self.evidence["token_usage"] = {
                **dict.fromkeys(totals), "source": "unavailable-including-explicit-compaction",
            }

    def run(self) -> dict[str, Any]:
        self._create_tasks()
        self._connect()
        self._create_and_bind_threads()
        self._start_all_baseline_turns()
        self._register_jobs()
        self._start_service()
        self._wait_for_service()
        self._verify_baseline_only_executors()
        # Releasing EOF makes this fixture-owned, already-registered local
        # process finish.  The detached scheduler must later observe the exit
        # itself; this module does not refresh the job record on its behalf.
        self._release_blocker(self.blockers[0])
        self._wait_for_exited_job_delivery()
        self._collect_token_usage()
        self.evidence["status"] = "passed"
        return self.evidence

    def _interrupt_known_direct_turn(self, role: str, thread_id: str) -> None:
        """Interrupt only a direct turn whose ID this fixture recorded."""

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
        self.evidence["cleanup"]["thread_interrupt"][role] = "interrupted_known_direct_turn"

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

        task_errors = False
        with _without_thread_id():
            for task_id in self.tasks.values():
                try:
                    self._commit_git_fixture_state()
                    cli.archive(self.store, SimpleNamespace(task=task_id, note="liveprobe fixture cleanup"))
                except Exception as exc:
                    task_errors = True
                    errors.append(f"task cleanup ({task_id}): {_redact(exc)}")
        self.evidence["cleanup"]["tasks"] = "partial" if task_errors else "archived"

        if self.stream is not None:
            thread_errors = False
            try:
                for role, thread_id in reversed(list(self.threads.items())):
                    try:
                        self._interrupt_known_direct_turn(role, thread_id)
                        self._request("thread/archive", {"threadId": thread_id})
                        self.evidence["cleanup"]["thread_archive"][role] = "archived"
                    except Exception as exc:
                        if _missing_rollout(exc):
                            # A failed task-start can leave a persisted thread
                            # id without a rollout record.  It is already
                            # absent from Codex storage and needs no archive
                            # retry or error escalation.
                            self.evidence["cleanup"]["thread_archive"][role] = "not_found"
                            continue
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
        "token_usage": {
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "reasoning_tokens": None,
            "source": "unknown-until-finalized",
        },
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
            try:
                fixture._collect_token_usage()
            except Exception:
                # Token accounting is diagnostic only; cleanup and pass/fail
                # evidence must remain authoritative when a rollout is partial.
                pass
            cleanup_errors = fixture.cleanup()
            evidence = dict(fixture.evidence) | {key: value for key, value in evidence.items() if key in {"status", "stage", "error"}}
        if cleanup_errors:
            evidence["cleanup_errors"] = cleanup_errors
            if failure is None:
                failure = LiveProbeError("live delivery fixture cleanup failed: " + "; ".join(cleanup_errors))
                evidence.update({"status": "failed", "stage": "cleanup", "error": _redact(failure)})
        if cleanup_errors:
            # Keep the owned root for diagnosis when service/process cleanup
            # was incomplete; deleting it could hide a live fixture process.
            evidence["cleanup_root"] = str(root_path)
        else:
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
    print("checks: exited-job delivery, successful compaction, Manager notification, and ordinary user followup")
    return 0


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
