"""Event-driven implementation for the unified :command:`mam wait` command.

The waiter subscribes only to the calling Codex thread and the agents bound to
this MAM project.  It evaluates the registered task and job state before it
blocks, then uses App Server lifecycle notifications plus bounded local process
probes.  It never starts a model turn or changes a registered job.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, Mapping

from . import job_runtime


WAIT_SECONDS = 3600.0
# These are local control/log checks, not model or agent polling.  Lifecycle
# updates arrive through the subscribed App Server connection.
CONTROL_CHECK_SECONDS = 1.0
STATE_REFRESH_SECONDS = 5.0
JOB_REFRESH_SECONDS = 5.0
JOB_PROBE_TIMEOUT_SECONDS = 3.0
_AGENT_STATUSES = {"active", "idle", "notLoaded", "systemError"}
_MESSAGE_METHODS = {"turn/steer", "turn/start"}
_USER_TEXT_KIND = "user.text"
MAX_SESSION_RECORD_BYTES = 16 * 1024 * 1024
# The initial backwards scan occurs once while a native-message watcher is
# created.  It is large enough to include one maximum-size journal row on each
# side of the timestamp boundary; a rare missing boundary falls back to offset
# zero rather than risk skipping an invocation-time input.
SESSION_LOOKBACK_BYTES = 2 * MAX_SESSION_RECORD_BYTES


class WaitRuntimeError(RuntimeError):
    """A wait cannot safely continue with the observed runtime state."""


@dataclass(frozen=True)
class ThreadState:
    agent: str
    status: str
    turn_id: str | None


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    agent: str | None
    jobs: tuple[dict[str, Any], ...]
    review_source: str | None


@dataclass(frozen=True)
class JobTarget:
    task: Task
    job: dict[str, Any]


@dataclass(frozen=True)
class AgentTarget:
    task: Task
    agent: str
    turn_id: str


@dataclass(frozen=True)
class Targets:
    active_agents: tuple[AgentTarget, ...]
    jobs: tuple[JobTarget, ...]
    inactive_tasks: tuple[Task, ...]
    pending_active: bool


@dataclass(frozen=True)
class TraceMessage:
    turn_id: str
    method: str


@dataclass(frozen=True)
class SessionMessage:
    """One text input observed in the local Codex session journal."""

    turn_id: str
    message_id: str


def _timestamp(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except ValueError:
        return None


def _thread_state(agent: str, result: Any) -> ThreadState:
    if not isinstance(result, Mapping) or not isinstance(result.get("thread"), Mapping):
        raise WaitRuntimeError(f"thread/resume for {agent} returned no thread snapshot")
    thread = result["thread"]
    if thread.get("id") != agent:
        raise WaitRuntimeError(f"thread/resume for {agent} returned another thread")
    raw_status = thread.get("status")
    status = raw_status.get("type") if isinstance(raw_status, Mapping) else raw_status
    if status not in _AGENT_STATUSES:
        raise WaitRuntimeError(f"thread/resume for {agent} returned an unknown status")
    turns = thread.get("turns")
    if not isinstance(turns, list):
        raise WaitRuntimeError(f"thread/resume for {agent} returned no turns snapshot")
    active = [turn.get("id") for turn in turns if isinstance(turn, Mapping) and turn.get("status") == "inProgress"]
    if any(not isinstance(turn_id, str) or not turn_id for turn_id in active):
        raise WaitRuntimeError(f"thread/resume for {agent} returned an invalid active turn")
    if len(active) > 1:
        raise WaitRuntimeError(f"thread/resume for {agent} returned multiple active turns")
    if status == "active" and not active:
        raise WaitRuntimeError(f"thread/resume for {agent} cannot identify its active turn")
    if status != "active" and active:
        raise WaitRuntimeError(f"thread/resume for {agent} returned an active turn with inactive status")
    return ThreadState(agent=agent, status=status, turn_id=active[0] if active else None)


class TraceMessages:
    """Tail new App Server request-trace spans without retaining message text."""

    def __init__(self, path: str | os.PathLike[str], *, started_at: float | None = None) -> None:
        self.path = Path(path)
        self._handle = None
        self._device_inode: tuple[int, int] | None = None
        self._partial = ""
        self._seen: set[tuple[str, str, str, str, str]] = set()
        self._seen_order: list[tuple[str, str, str, str, str]] = []
        if started_at is not None and (not isinstance(started_at, (int, float)) or isinstance(started_at, bool)):
            raise ValueError("trace start time must be numeric")
        self._started_at = time.time() if started_at is None else float(started_at)
        self._open(at_end=True)

    def _open(self, *, at_end: bool) -> None:
        try:
            handle = self.path.open("r", encoding="utf-8", errors="replace")
            stat = os.fstat(handle.fileno())
        except OSError as exc:
            raise WaitRuntimeError(f"cannot read App Server request trace: {exc}") from exc
        if at_end:
            handle.seek(0, os.SEEK_END)
        if self._handle is not None:
            self._handle.close()
        self._handle = handle
        self._device_inode = (stat.st_dev, stat.st_ino)
        self._partial = ""

    def _refresh_handle(self) -> None:
        if self._handle is None:
            self._open(at_end=False)
            return
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            # Keep the old descriptor through the short rename/create window.
            # A real App Server restart also breaks the subscribed connection
            # and returns an explicit wait error.
            return
        except OSError as exc:
            raise WaitRuntimeError(f"cannot stat App Server request trace: {exc}") from exc
        current = (stat.st_dev, stat.st_ino)
        if current != self._device_inode:
            self._open(at_end=False)
        elif stat.st_size < self._handle.tell():
            self._handle.seek(0)
            self._partial = ""

    def _remember(self, key: tuple[str, str, str, str, str]) -> bool:
        if key in self._seen:
            return False
        self._seen.add(key)
        self._seen_order.append(key)
        if len(self._seen_order) > 4096:
            stale = self._seen_order.pop(0)
            self._seen.discard(stale)
        return True

    @staticmethod
    def _spans(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        spans: list[Mapping[str, Any]] = []
        span = row.get("span")
        if isinstance(span, Mapping):
            spans.append(span)
        ancestors = row.get("spans")
        if isinstance(ancestors, list):
            spans.extend(item for item in ancestors if isinstance(item, Mapping))
        return spans

    def poll(self) -> list[TraceMessage]:
        self._refresh_handle()
        if self._handle is None:
            return []
        try:
            text = self._handle.read()
        except OSError as exc:
            raise WaitRuntimeError(f"cannot read App Server request trace: {exc}") from exc
        if not text:
            return []
        lines = (self._partial + text).split("\n")
        self._partial = lines.pop()
        signals: list[TraceMessage] = []
        for line in lines:
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                # The App Server log can contain unrelated diagnostics.  They
                # have no request span and cannot wake a waiter.
                continue
            if not isinstance(row, Mapping):
                continue
            when = _timestamp(row.get("timestamp"))
            # The initial descriptor tails from EOF, but an old buffered row
            # can still be appended after a later wait starts.  Apply this
            # invocation's timestamp floor to every increment, including the
            # first one, so it cannot wake the newer wait.
            if when is None or when < self._started_at:
                continue
            for span in self._spans(row):
                method = span.get("rpc.method")
                if method not in _MESSAGE_METHODS:
                    continue
                turn_id = span.get("turn.id")
                # Tracing records the turn id late in the request span, so
                # earlier rows for the same request legitimately omit it.
                if turn_id is None:
                    continue
                if not isinstance(turn_id, str) or not turn_id:
                    raise WaitRuntimeError("App Server request trace has an invalid turn id")
                key = (
                    str(span.get("rpc.transport", "")),
                    str(span.get("app_server.connection_id", "")),
                    str(span.get("rpc.request_id", "")),
                    str(method),
                    turn_id,
                )
                if self._remember(key):
                    signals.append(TraceMessage(turn_id=turn_id, method=method))
        return signals

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


class SessionMessages:
    """Tail current-thread text inputs from Codex's local session journal.

    Manager ``send_input`` currently reaches a running agent through this
    in-process journal path rather than a traced ``turn/steer`` RPC.  The
    watcher retains only message and turn identifiers; it never returns or
    persists message text.
    """

    def __init__(
        self, path: str | os.PathLike[str], *, started_at: float | None = None, include_started_at: bool = False
    ) -> None:
        self.path = Path(path)
        if started_at is not None and (not isinstance(started_at, (int, float)) or isinstance(started_at, bool)):
            raise ValueError("session journal start time must be numeric")
        if not isinstance(include_started_at, bool):
            raise ValueError("session journal lookup window must be boolean")
        self._started_at = time.time() if started_at is None else float(started_at)
        self._handle = None
        self._device_inode: tuple[int, int] | None = None
        self._partial = b""
        self._seen: set[tuple[str, str]] = set()
        self._seen_order: list[tuple[str, str]] = []
        offset = self._lookup_start_offset() if include_started_at else None
        self._open(at_end=offset is None, offset=offset)

    @classmethod
    def from_environment(
        cls, agent: str, *, environment: Mapping[str, str] | None = None, started_at: float | None = None
    ) -> "SessionMessages":
        """Open the unique current-session journal for ``CODEX_THREAD_ID``."""

        # Take the invocation boundary before journal discovery.  A native
        # input can arrive between identifying the file and opening it.
        boundary = time.time() if started_at is None else started_at
        env = os.environ if environment is None else environment
        home, session_id = env.get("CODEX_HOME"), env.get("CODEX_SESSION_ID")
        if not isinstance(home, str) or not home:
            raise WaitRuntimeError("CODEX_HOME is required to observe native messages")
        if not isinstance(session_id, str) or not session_id:
            raise WaitRuntimeError("CODEX_SESSION_ID is required to observe native messages")
        root = Path(home) / "sessions"
        if not Path(home).is_absolute() or not root.is_dir() or root.is_symlink():
            raise WaitRuntimeError("CODEX_HOME has no readable Codex sessions directory")
        if not isinstance(agent, str) or not agent:
            raise WaitRuntimeError("native message watcher has an invalid AGENT-ID")

        matches: list[Path] = []
        try:
            candidates = sorted(root.glob(f"**/*-{agent}.jsonl"))
        except OSError as exc:
            raise WaitRuntimeError(f"cannot locate Codex session journal: {exc}") from exc
        for candidate in candidates:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            try:
                with candidate.open("rb") as handle:
                    header = handle.readline(MAX_SESSION_RECORD_BYTES + 1)
            except OSError as exc:
                raise WaitRuntimeError(f"cannot read Codex session journal: {exc}") from exc
            if len(header) > MAX_SESSION_RECORD_BYTES:
                raise WaitRuntimeError("Codex session journal header is too large")
            try:
                row = json.loads(header)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise WaitRuntimeError("Codex session journal has an invalid header") from exc
            if not isinstance(row, Mapping):
                raise WaitRuntimeError("Codex session journal header is not an object")
            payload = row.get("payload")
            if (row.get("type") == "session_meta" and isinstance(payload, Mapping)
                    and payload.get("id") == agent and payload.get("session_id") == session_id):
                matches.append(candidate)
        if len(matches) != 1:
            raise WaitRuntimeError("cannot identify one current Codex session journal for CODEX_THREAD_ID")
        return cls(matches[0], started_at=boundary, include_started_at=True)

    def _lookup_start_offset(self) -> int:
        """Find a bounded pre-invocation journal boundary once at startup.

        The normal poll path only consumes bytes appended after this offset.
        If the bounded tail has no safely older timestamp, begin at zero so a
        message written during discovery cannot be lost to an EOF seek.
        """

        try:
            with self.path.open("rb") as handle:
                size = os.fstat(handle.fileno()).st_size
                lower = max(0, size - SESSION_LOOKBACK_BYTES)
                handle.seek(lower)
                tail = handle.read(SESSION_LOOKBACK_BYTES)
        except OSError as exc:
            raise WaitRuntimeError(f"cannot read Codex session journal: {exc}") from exc

        offset = lower
        if lower:
            newline = tail.find(b"\n")
            if newline < 0:
                return 0
            offset += newline + 1
            tail = tail[newline + 1:]

        rows: list[tuple[int, bytes]] = []
        for row in tail.splitlines(keepends=True):
            end = offset + len(row)
            if row.endswith(b"\n"):
                rows.append((end, row[:-1]))
            offset = end

        for end, row in reversed(rows):
            if len(row) > MAX_SESSION_RECORD_BYTES:
                continue
            try:
                value = json.loads(row)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(value, Mapping) and (when := _timestamp(value.get("timestamp"))) is not None and when < self._started_at:
                return end
        return 0

    def _open(self, *, at_end: bool, offset: int | None = None) -> None:
        try:
            handle = self.path.open("rb")
            stat = os.fstat(handle.fileno())
        except OSError as exc:
            raise WaitRuntimeError(f"cannot read Codex session journal: {exc}") from exc
        if offset is not None:
            handle.seek(offset)
        elif at_end:
            handle.seek(0, os.SEEK_END)
        if self._handle is not None:
            self._handle.close()
        self._handle = handle
        self._device_inode = (stat.st_dev, stat.st_ino)
        self._partial = b""

    def _refresh_handle(self) -> None:
        if self._handle is None:
            raise WaitRuntimeError("Codex session journal was closed while waiting")
        try:
            stat = self.path.stat()
        except OSError as exc:
            raise WaitRuntimeError(f"cannot stat Codex session journal: {exc}") from exc
        if (stat.st_dev, stat.st_ino) != self._device_inode:
            raise WaitRuntimeError("Codex session journal rotated while waiting")
        if stat.st_size < self._handle.tell():
            raise WaitRuntimeError("Codex session journal was truncated while waiting")

    def _remember(self, key: tuple[str, str]) -> bool:
        if key in self._seen:
            return False
        self._seen.add(key)
        self._seen_order.append(key)
        if len(self._seen_order) > 4096:
            stale = self._seen_order.pop(0)
            self._seen.discard(stale)
        return True

    def _message(self, row: Mapping[str, Any]) -> SessionMessage | None:
        if row.get("type") != "response_item":
            return None
        payload = row.get("payload")
        if not isinstance(payload, Mapping) or payload.get("type") != "message" or payload.get("role") != "user":
            return None
        when = _timestamp(row.get("timestamp"))
        if when is None:
            raise WaitRuntimeError("Codex session journal user message has an invalid timestamp")
        if when < self._started_at:
            return None
        metadata = payload.get("internal_chat_message_metadata_passthrough")
        if not isinstance(metadata, Mapping):
            raise WaitRuntimeError("Codex session journal user message has no turn metadata")
        turn_id, message_id = metadata.get("turn_id"), payload.get("id")
        kinds = metadata.get("content_item_kinds")
        if not isinstance(turn_id, str) or not turn_id or not isinstance(message_id, str) or not message_id:
            raise WaitRuntimeError("Codex session journal user message has invalid identifiers")
        if not isinstance(kinds, list) or not all(isinstance(kind, str) for kind in kinds):
            raise WaitRuntimeError("Codex session journal user message has invalid content metadata")
        if _USER_TEXT_KIND not in kinds:
            return None
        key = (turn_id, message_id)
        return SessionMessage(turn_id, message_id) if self._remember(key) else None

    def poll(self) -> list[SessionMessage]:
        self._refresh_handle()
        assert self._handle is not None
        try:
            chunk = self._handle.read(MAX_SESSION_RECORD_BYTES + 1)
        except OSError as exc:
            raise WaitRuntimeError(f"cannot read Codex session journal: {exc}") from exc
        if not chunk:
            return []
        lines = (self._partial + chunk).split(b"\n")
        self._partial = lines.pop()
        if len(self._partial) > MAX_SESSION_RECORD_BYTES:
            raise WaitRuntimeError("Codex session journal record is too large")
        messages: list[SessionMessage] = []
        for line in lines:
            if not line:
                continue
            if len(line) > MAX_SESSION_RECORD_BYTES:
                raise WaitRuntimeError("Codex session journal record is too large")
            try:
                row = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise WaitRuntimeError("Codex session journal has an invalid record") from exc
            if not isinstance(row, Mapping):
                raise WaitRuntimeError("Codex session journal record is not an object")
            message = self._message(row)
            if message is not None:
                messages.append(message)
        return messages

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


class UnifiedWait:
    """Own one unified wait and return one compact, actionable exit result."""

    def __init__(
        self,
        store: Any,
        caller: str,
        *,
        socket_path: str,
        log_path: str,
        begin_wait: Callable[[str, str | None, str], dict[str, Any]],
        cancelled: Callable[[dict[str, Any]], bool],
        finish_wait: Callable[[dict[str, Any]], None],
        active_wait_states: Callable[[], Mapping[str, str]],
        process_probe: Callable[..., Mapping[str, Any]] = job_runtime.probe_process,
        stream_factory: Callable[[str], Any] = job_runtime.AppServerEventStream.connect,
        trace_factory: Callable[[str], TraceMessages] = TraceMessages,
        trace: Any | None = None,
        messages: Any | None = None,
        message_floor_ms: int | None = None,
        clock: Callable[[], float] = time.monotonic,
        control_check_seconds: float = CONTROL_CHECK_SECONDS,
        state_refresh_seconds: float = STATE_REFRESH_SECONDS,
        job_refresh_seconds: float = JOB_REFRESH_SECONDS,
    ) -> None:
        self.store = store
        self.caller = caller
        self.socket_path = socket_path
        self.log_path = log_path
        self.begin_wait = begin_wait
        self.cancelled = cancelled
        self.finish_wait = finish_wait
        self.active_wait_states = active_wait_states
        self.process_probe = process_probe
        self.stream_factory = stream_factory
        self.trace_factory = trace_factory
        self.trace = trace
        self.messages = messages
        if message_floor_ms is not None and (not isinstance(message_floor_ms, int) or isinstance(message_floor_ms, bool)):
            raise ValueError("message timestamp floor must be an integer")
        self.message_floor_ms = int(time.time() * 1000) if message_floor_ms is None else message_floor_ms
        self.clock = clock
        self.control_check_seconds = self._positive_interval(control_check_seconds, "control check")
        self.state_refresh_seconds = self._positive_interval(state_refresh_seconds, "state refresh")
        self.job_refresh_seconds = self._positive_interval(job_refresh_seconds, "job refresh")
        self.stream: Any = None
        self.states: dict[str, ThreadState] = {}
        self.tasks: tuple[Task, ...] = ()
        self.by_agent: dict[str, Task] = {}
        self.watched_turns: dict[tuple[str, str], AgentTarget] = {}
        self.caller_turn: str | None = None
        self._native_item_seen: set[tuple[str, str]] = set()
        self._native_item_order: list[tuple[str, str]] = []

    @staticmethod
    def _positive_interval(value: float, label: str) -> float:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} interval must be positive")
        return float(value)

    def _result(self, reason: str, message: str, agent: str) -> dict[str, Any]:
        return {"status": reason, "reason": reason, "message": message, "agent": agent}

    def _error(self, detail: str) -> dict[str, Any]:
        return self._result("error", detail, self.caller)

    def _message_result(self) -> dict[str, Any]:
        return self._result("message", "received new message", self.caller)

    def _cancelled_result(self) -> dict[str, Any]:
        return self._result("cancelled", "manual mam wait stop", self.caller)

    def _timeout_result(self) -> dict[str, Any]:
        result = self._result("timeout", "fixed 3600-second wait elapsed", self.caller)
        result["timeout_seconds"] = int(WAIT_SECONDS)
        return result

    def _load_tasks(self) -> None:
        try:
            records = self.store.all()
        except Exception as exc:
            raise WaitRuntimeError(f"cannot read registered MAM tasks: {exc}") from exc
        if not isinstance(records, list):
            raise WaitRuntimeError("registered MAM tasks are unavailable")
        tasks: list[Task] = []
        bindings: dict[str, Task] = {}
        for data in records:
            if not isinstance(data, Mapping) or data.get("status") == "archived":
                continue
            task_id, title, agent, jobs = data.get("id"), data.get("title"), data.get("agent"), data.get("jobs")
            if not isinstance(task_id, str) or not task_id or not isinstance(title, str) or not isinstance(jobs, list):
                raise WaitRuntimeError("registered MAM task has invalid wait fields")
            if agent is not None and (not isinstance(agent, str) or not agent):
                raise WaitRuntimeError(f"registered MAM task {task_id} has an invalid agent")
            if not all(isinstance(job, Mapping) for job in jobs):
                raise WaitRuntimeError(f"registered MAM task {task_id} has an invalid job")
            review = data.get("review")
            review_source: str | None = None
            if review is not None:
                if not isinstance(review, Mapping):
                    raise WaitRuntimeError(f"registered MAM task {task_id} has an invalid review link")
                source = review.get("task")
                if not isinstance(source, str) or not source:
                    raise WaitRuntimeError(f"registered MAM task {task_id} has an invalid review source")
                review_source = source
            task = Task(task_id, title, agent, tuple(dict(job) for job in jobs), review_source)
            if agent:
                if agent in bindings:
                    raise WaitRuntimeError(f"AGENT-ID is bound to multiple nonarchived MAM tasks: {agent}")
                bindings[agent] = task
            tasks.append(task)
        self.tasks = tuple(sorted(tasks, key=lambda task: task.id))
        self.by_agent = bindings

    def _subscribe(self, agent: str) -> None:
        if agent in self.states:
            return
        try:
            self.states[agent] = _thread_state(agent, self.stream.resume(agent))
        except job_runtime.AppServerEventError as exc:
            raise WaitRuntimeError(str(exc)) from exc

    def _role(self) -> tuple[str, Task | None]:
        bound = self.by_agent.get(self.caller)
        return ("executor", bound) if bound is not None else ("manager", None)

    def _managed_agents(self) -> set[str]:
        return {self.caller, *self.by_agent}

    def _current_wait_states(self) -> Mapping[str, str]:
        try:
            states = self.active_wait_states()
        except Exception as exc:
            raise WaitRuntimeError(f"cannot inspect current MAM waits: {exc}") from exc
        if not isinstance(states, Mapping):
            raise WaitRuntimeError("current MAM waits are unavailable")
        for agent, state in states.items():
            if not isinstance(agent, str) or state not in {"running", "unknown"}:
                raise WaitRuntimeError("current MAM wait has an invalid state")
        return states

    def _owner_active(self, task: Task, wait_states: Mapping[str, str]) -> bool:
        assert task.agent is not None
        wait_state = wait_states.get(task.agent)
        if wait_state == "unknown":
            raise WaitRuntimeError(f"cannot verify active wait identity for agent: {task.agent}")
        if wait_state == "running":
            return True
        state = self.states.get(task.agent)
        if state is None:
            raise WaitRuntimeError(f"cannot resolve registered agent: {task.agent}")
        if state.status == "active":
            return True
        if state.status == "idle":
            return False
        raise WaitRuntimeError(f"cannot resolve current status for registered agent: {task.agent}")

    def _delegated_sources(self) -> set[str]:
        """Return local source tasks with an unarchived review owner.

        Only links among the current MAM records participate.  Detecting a
        local cycle is safer than recursively delegating responsibility.
        """

        by_id = {task.id: task for task in self.tasks}
        edges = {
            task.id: task.review_source
            for task in self.tasks
            if task.review_source is not None and task.review_source in by_id
        }
        for root in edges:
            seen: set[str] = set()
            current = root
            while current in edges:
                if current in seen:
                    raise WaitRuntimeError("unarchived review links contain a cycle")
                seen.add(current)
                current = edges[current]
        return set(edges.values())

    @staticmethod
    def _unarchived_jobs(task: Task) -> tuple[JobTarget, ...]:
        return tuple(JobTarget(task, job) for job in task.jobs if job.get("status") != "archived")

    def _targets(self, role: str, bound: Task | None) -> Targets:
        if role == "executor":
            if bound is None:
                raise WaitRuntimeError("executor wait has no bound task")
            return Targets((), self._unarchived_jobs(bound), (), False)

        wait_states = self._current_wait_states()
        delegated_sources = self._delegated_sources()
        active_agents: list[AgentTarget] = []
        jobs: list[JobTarget] = []
        inactive_tasks: list[Task] = []
        pending_active = False
        for task in self.tasks:
            if task.agent is None:
                # An unbound task has no executor completion to report, but a
                # stopped process remains concrete work for the manager.
                jobs.extend(self._unarchived_jobs(task))
                continue
            if self._owner_active(task, wait_states):
                state = self.states[task.agent]
                if state.status == "active" and state.turn_id:
                    active_agents.append(AgentTarget(task, task.agent, state.turn_id))
                else:
                    # A verified waiter can briefly precede its lifecycle
                    # notification.  Keep ownership with it without guessing
                    # an agent turn or claiming its jobs.
                    pending_active = True
                continue
            jobs.extend(self._unarchived_jobs(task))
            if task.id not in delegated_sources:
                inactive_tasks.append(task)
        return Targets(tuple(active_agents), tuple(jobs), tuple(inactive_tasks), pending_active)

    def _remember_targets(self, targets: Targets) -> None:
        self.watched_turns = {(target.agent, target.turn_id): target for target in targets.active_agents}

    def _refresh(self, *, require_caller_turn: bool) -> tuple[str, Task | None, Targets]:
        self._load_tasks()
        self._subscribe(self.caller)
        role, bound = self._role()
        if role == "manager":
            for agent in sorted(self.by_agent):
                self._subscribe(agent)
        caller = self.states[self.caller]
        if require_caller_turn and (caller.status != "active" or not caller.turn_id):
            raise WaitRuntimeError("CODEX_THREAD_ID resolves to no active current turn")
        targets = self._targets(role, bound)
        self._remember_targets(targets)
        return role, bound, targets

    @staticmethod
    def _stored_stopped(target: JobTarget) -> bool:
        probe = target.job.get("probe")
        return target.job.get("status") == "stopped" or isinstance(probe, Mapping) and probe.get("status") == "stopped"

    @staticmethod
    def _job_fields(target: JobTarget) -> tuple[str, str]:
        job_id, note = target.job.get("id"), target.job.get("note")
        if not isinstance(job_id, str) or not job_id or not isinstance(note, str):
            raise WaitRuntimeError(f"registered job for task {target.task.id} has no id or note")
        return job_id, note

    def _job_result(self, target: JobTarget) -> dict[str, Any]:
        job_id, note = self._job_fields(target)
        agent = target.task.agent or self.caller
        result = self._result("job_stopped", "registered job stopped; process exit does not prove experimental success", agent)
        result.update({"task": target.task.id, "task_title": target.task.title, "job": job_id, "note": note})
        if agent != self.caller:
            result["waiter"] = self.caller
        return result

    def _agent_result(self, task: Task) -> dict[str, Any]:
        if not task.agent:
            raise WaitRuntimeError(f"inactive task has no bound agent: {task.id}")
        result = self._result("agent_completed", "subagent completed its turn", task.agent)
        result.update({"task": task.id, "task_title": task.title})
        if task.agent != self.caller:
            result["waiter"] = self.caller
        return result

    def _probe_jobs(self, targets: tuple[JobTarget, ...], deadline: float | None) -> dict[str, Any] | None:
        for target in targets:
            job_id, _ = self._job_fields(target)
            timeout = JOB_PROBE_TIMEOUT_SECONDS
            if deadline is not None:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    return None
                timeout = min(timeout, remaining)
            try:
                observation = self.process_probe(
                    target.job.get("host"), target.job.get("pid"), target.job.get("identity"), timeout
                )
            except Exception as exc:
                raise WaitRuntimeError(f"cannot probe registered JOB-ID {job_id}: {exc}") from exc
            if not isinstance(observation, Mapping) or not isinstance(observation.get("status"), str):
                raise WaitRuntimeError(f"registered JOB-ID {job_id} probe returned an invalid status")
            status = observation["status"]
            if status == "stopped":
                return self._job_result(target)
            if status != "running":
                detail = observation.get("error")
                suffix = f": {detail}" if isinstance(detail, str) and detail else ""
                raise WaitRuntimeError(f"cannot determine state for registered JOB-ID {job_id}{suffix}")
        return None

    def _reconcile(self, targets: Targets, *, probe_jobs: bool, deadline: float | None) -> dict[str, Any] | None:
        stopped = next((target for target in targets.jobs if self._stored_stopped(target)), None)
        if stopped is not None:
            return self._job_result(stopped)
        # A stopped source job must remain visible even while an active review
        # suppresses the source task completion trigger.  Probe before any
        # inactive-task return for the same reason.
        if targets.jobs and (probe_jobs or targets.inactive_tasks):
            result = self._probe_jobs(targets.jobs, deadline)
            if result is not None:
                return result
        if targets.inactive_tasks:
            return self._agent_result(targets.inactive_tasks[0])
        if not targets.active_agents and not targets.jobs and not targets.pending_active:
            return self._result("empty", "no active subagents or unarchived jobs", self.caller)
        return None

    def _event(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, Mapping):
            raise WaitRuntimeError("App Server event is not an object")
        method, params = message.get("method"), message.get("params")
        if method not in {"turn/started", "turn/completed", "thread/status/changed", "item/started", "item/completed"}:
            return None
        if not isinstance(params, Mapping):
            raise WaitRuntimeError(f"App Server {method} event has invalid params")
        if method in {"item/started", "item/completed"}:
            return self._native_item_event(method, params)
        agent = params.get("threadId")
        if not isinstance(agent, str) or agent not in self._managed_agents():
            return None
        previous = self.states.get(agent)
        if previous is None:
            # The shared control stream can notify a bound agent before this
            # wait has subscribed and snapshotted it (an executor normally
            # subscribes only to itself).  Its current state is reconciled on
            # the next refresh, so this unrelated notification must not abort
            # the caller's wait.
            return None
        if method == "thread/status/changed":
            raw_status = params.get("status")
            status = raw_status.get("type") if isinstance(raw_status, Mapping) else raw_status
            if status not in _AGENT_STATUSES:
                raise WaitRuntimeError(f"App Server status event has an unknown status for {agent}")
            # Keep the last active turn through the idle notification so the
            # following turn/completed notification still has its exact map.
            self.states[agent] = ThreadState(agent, status, previous.turn_id)
            return None

        turn = params.get("turn")
        turn_id = turn.get("id") if isinstance(turn, Mapping) else None
        if not isinstance(turn_id, str) or not turn_id:
            raise WaitRuntimeError(f"App Server {method} event has no turn id for {agent}")
        if method == "turn/started":
            self.states[agent] = ThreadState(agent, "active", turn_id)
            role, bound = self._role()
            self._remember_targets(self._targets(role, bound))
            return None

        target = self.watched_turns.pop((agent, turn_id), None)
        if previous.turn_id == turn_id:
            self.states[agent] = ThreadState(agent, "idle", None)
        if target is None:
            return None
        return self._agent_result(target.task)

    def _native_item_event(self, method: str, params: Mapping[str, Any]) -> dict[str, Any] | None:
        """Recognize native manager input emitted as an observed UserMessage item."""

        agent = params.get("threadId")
        if agent != self.caller:
            return None
        turn_id = params.get("turnId")
        if not isinstance(turn_id, str) or not turn_id:
            raise WaitRuntimeError(f"App Server {method} native message has no turn id")
        if turn_id != self.caller_turn:
            return None
        item = params.get("item")
        if not isinstance(item, Mapping):
            raise WaitRuntimeError(f"App Server {method} native message has no item")
        if item.get("type") != "userMessage":
            return None
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise WaitRuntimeError(f"App Server {method} native message has no item id")
        observed_at = params.get("startedAtMs")
        if observed_at is None:
            observed_at = params.get("completedAtMs")
        if not isinstance(observed_at, int) or isinstance(observed_at, bool):
            raise WaitRuntimeError(f"App Server {method} native message has no timestamp")
        if observed_at < self.message_floor_ms:
            return None
        key = (turn_id, item_id)
        if key in self._native_item_seen:
            return None
        self._native_item_seen.add(key)
        self._native_item_order.append(key)
        if len(self._native_item_order) > 4096:
            stale = self._native_item_order.pop(0)
            self._native_item_seen.discard(stale)
        return self._message_result()

    def _drain_events(self) -> dict[str, Any] | None:
        while True:
            event = self.stream.poll(0)
            if event is None:
                return None
            result = self._event(event)
            if result is not None:
                return result

    @staticmethod
    def _matching_message(trace: TraceMessages, turn_id: str) -> bool:
        return any(signal.turn_id == turn_id for signal in trace.poll())

    @staticmethod
    def _matching_session_message(messages: Any | None, turn_id: str) -> bool:
        return messages is not None and any(signal.turn_id == turn_id for signal in messages.poll())

    def _current_turn(self) -> str:
        state = self.states.get(self.caller)
        if state is None or state.status != "active" or not state.turn_id:
            raise WaitRuntimeError("CODEX_THREAD_ID resolves to no active current turn")
        return state.turn_id

    def _refresh_after_registration(
        self, record: dict[str, Any], caller_turn: str, deadline: float
    ) -> tuple[str, Task | None, Targets, dict[str, Any] | None]:
        if self.cancelled(record):
            return "", None, Targets((), (), (), False), self._cancelled_result()
        role, bound, targets = self._refresh(require_caller_turn=True)
        if self._current_turn() != caller_turn:
            raise WaitRuntimeError("current caller turn changed while registering mam wait")
        if self._matching_session_message(self.messages, caller_turn):
            return role, bound, targets, self._message_result()
        result = self._drain_events()
        if result is None:
            result = self._reconcile(targets, probe_jobs=True, deadline=deadline)
        return role, bound, targets, result

    def run(self) -> dict[str, Any]:
        record: dict[str, Any] | None = None
        trace: TraceMessages | None = None
        try:
            deadline = self.clock() + WAIT_SECONDS
            try:
                trace = self.trace if self.trace is not None else self.trace_factory(self.log_path)
                self.stream = self.stream_factory(self.socket_path)
            except job_runtime.AppServerEventError as exc:
                raise WaitRuntimeError(str(exc)) from exc
            except (OSError, TimeoutError) as exc:
                raise WaitRuntimeError(f"App Server event subscription failed: {exc}") from exc

            role, bound, targets = self._refresh(require_caller_turn=True)
            caller_turn = self._current_turn()
            self.caller_turn = caller_turn
            if self._matching_session_message(self.messages, caller_turn):
                return self._message_result()
            if self._matching_message(trace, caller_turn):
                return self._message_result()
            result = self._drain_events()
            if result is not None:
                return result
            result = self._reconcile(targets, probe_jobs=True, deadline=deadline)
            if result is not None:
                return result
            if self.clock() >= deadline:
                return self._timeout_result()

            record = self.begin_wait(role, bound.id if bound else None, caller_turn)
            if not isinstance(record, Mapping) or record.get("turn_id") != caller_turn:
                raise WaitRuntimeError("wait registration did not retain the current caller turn")
            role, bound, targets, result = self._refresh_after_registration(record, caller_turn, deadline)
            if result is not None:
                return result

            next_control = self.clock() + self.control_check_seconds
            next_state = self.clock() + self.state_refresh_seconds
            next_job = self.clock() + self.job_refresh_seconds
            while True:
                if self.cancelled(record):
                    return self._cancelled_result()
                now = self.clock()
                if now >= deadline:
                    return self._timeout_result()
                if self._matching_session_message(self.messages, caller_turn):
                    return self._message_result()
                if self._matching_message(trace, caller_turn):
                    return self._message_result()
                result = self._drain_events()
                if result is not None:
                    return result

                now = self.clock()
                if now >= next_state:
                    role, bound, targets = self._refresh(require_caller_turn=True)
                    if self._current_turn() != caller_turn:
                        raise WaitRuntimeError("current caller turn changed while waiting")
                    result = self._drain_events()
                    if result is not None:
                        return result
                    result = self._reconcile(targets, probe_jobs=False, deadline=deadline)
                    if result is not None:
                        return result
                    next_state = now + self.state_refresh_seconds
                if now >= next_job:
                    result = self._reconcile(targets, probe_jobs=True, deadline=deadline)
                    if result is not None:
                        return result
                    next_job = now + self.job_refresh_seconds
                if now >= next_control:
                    next_control = now + self.control_check_seconds

                wait_for = min(next_control, next_state, next_job, deadline) - self.clock()
                event = self.stream.poll(max(0.0, wait_for))
                if event is not None:
                    result = self._event(event)
                    if result is not None:
                        return result
        except (WaitRuntimeError, job_runtime.AppServerEventError) as exc:
            return self._error(str(exc))
        finally:
            if record is not None:
                self.finish_wait(record)
            if trace is not None:
                trace.close()
            if self.messages is not None:
                self.messages.close()
            if self.stream is not None:
                self.stream.close()


def wait(
    store: Any,
    caller: str,
    *,
    socket_path: str,
    log_path: str,
    begin_wait: Callable[[str, str | None, str], dict[str, Any]],
    cancelled: Callable[[dict[str, Any]], bool],
    finish_wait: Callable[[dict[str, Any]], None],
    active_wait_states: Callable[[], Mapping[str, str]],
    process_probe: Callable[..., Mapping[str, Any]],
    trace: Any | None = None,
    messages: Any | None = None,
    message_floor_ms: int | None = None,
) -> dict[str, Any]:
    """Run one unified wait with the concrete MAM storage callbacks."""

    return UnifiedWait(
        store,
        caller,
        socket_path=socket_path,
        log_path=log_path,
        begin_wait=begin_wait,
        cancelled=cancelled,
        finish_wait=finish_wait,
        active_wait_states=active_wait_states,
        process_probe=process_probe,
        trace=trace,
        messages=messages,
        message_floor_ms=message_floor_ms,
    ).run()
