"""Read native Codex thread ancestry without changing a thread's state."""
from __future__ import annotations

from dataclasses import dataclass
import contextlib
import uuid

from . import job_runtime, wake_compat


class IdentityError(RuntimeError):
    pass


@dataclass(frozen=True)
class ThreadIdentity:
    agent: str
    path: str
    tree_root: str


def canonical(agent: str) -> str:
    try:
        if str(uuid.UUID(agent)) == agent:
            return agent
    except (ValueError, TypeError, AttributeError):
        pass
    raise IdentityError(f"invalid Codex thread ID: {agent}")


def _path(thread: dict, parent: str | None) -> str:
    source = thread.get("source")
    subagent = source.get("subAgent") if isinstance(source, dict) else None
    spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
    path = spawn.get("agent_path") if isinstance(spawn, dict) else None
    if parent is None:
        if path not in (None, "/root"):
            raise IdentityError("root thread has conflicting native agent path")
        return "/root"
    if not isinstance(path, str) or not path.startswith("/root/") or any(
        segment in ("", ".", "..") for segment in path.split("/")[1:]
    ):
        raise IdentityError("subagent thread has no valid native agent path")
    return path


def read(agent: str) -> ThreadIdentity:
    """Resolve the root through parentThreadId, never through sessionId."""
    agent = canonical(agent)
    stream = None
    try:
        stream = job_runtime.AppServerEventStream.connect(str(wake_compat.configured_socket_path()))
        current, seen, path, child_path = agent, set(), None, None
        while True:
            if current in seen:
                raise IdentityError("cycle in native thread ancestry")
            seen.add(current)
            result = stream.read(current)
            thread = result.get("thread") if isinstance(result, dict) else None
            if not isinstance(thread, dict) or thread.get("id") != current:
                raise IdentityError(f"thread/read returned no matching thread for {current}")
            parent = thread.get("parentThreadId")
            if parent is not None:
                parent = canonical(parent)
            observed = _path(thread, parent)
            if path is None:
                path = observed
            if child_path is not None and not child_path.startswith(observed + "/"):
                raise IdentityError("native agent path conflicts with parent ancestry")
            if parent is None:
                return ThreadIdentity(agent, path, current)
            child_path = observed
            current = parent
    except (job_runtime.AppServerEventError, OSError, ValueError) as exc:
        raise IdentityError(f"cannot verify native thread identity: {exc}") from exc
    finally:
        if stream is not None:
            with contextlib.suppress(Exception):
                stream.close()
