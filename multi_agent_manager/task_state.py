"""Task lifecycle state and per-task automatic reminder accounting."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REMINDER_LIMIT = 3
REMINDER_COUNT_FIELD = "wake_reminder_count"
TASK_STATES = {"pending", "working", "blocked", "archived"}


def _status(value: Any) -> str | None:
    return value if isinstance(value, str) and value in TASK_STATES else None


def _unarchived_jobs(task: Mapping[str, Any]) -> bool:
    jobs = task.get("jobs")
    return isinstance(jobs, list) and any(
        isinstance(job, Mapping) and job.get("status") != "archived" for job in jobs
    )


def refresh_state(task: Mapping[str, Any], executor_observation: Mapping[str, Any] | None
                  ) -> tuple[dict[str, Any], str | None, str]:
    """Return a refreshed task and its before/after state.

    Callers hold the task lock when persisting the returned record. Unknown
    executor state keeps the saved state unless an unarchived job proves work
    is active. Unknown is never interpreted as idle.
    """
    updated = dict(task)
    old = _status(task.get("status"))
    current = old or ("pending" if not task.get("agent") else "working")
    if current == "archived":
        new = "archived"
    elif _unarchived_jobs(task):
        new = "working"
    else:
        observed = executor_observation.get("status") if isinstance(executor_observation, Mapping) else None
        if observed == "active":
            new = "working"
        elif current == "blocked":
            new = "blocked"
        elif not task.get("agent"):
            new = "pending"
        elif observed == "idle":
            new = "pending"
        else:
            new = current
    updated["status"] = new
    if task.get("status") != new:
        updated[REMINDER_COUNT_FIELD] = 0
    return updated, old, new


def reminder_count(task: Mapping[str, Any]) -> int:
    value = task.get(REMINDER_COUNT_FIELD, 0)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def record_reminder(task: Mapping[str, Any], expected_status: str) -> tuple[dict[str, Any], bool]:
    """Return an incremented copy only for an accepted reminder state."""
    updated = dict(task)
    if _status(task.get("status")) != expected_status or expected_status == "archived":
        return updated, False
    count = reminder_count(task)
    if count >= REMINDER_LIMIT:
        return updated, False
    updated[REMINDER_COUNT_FIELD] = count + 1
    return updated, True


def set_blocked(task: Mapping[str, Any], note: str) -> dict[str, Any]:
    """Return a blocked task copy; callers enforce Manager permission/state."""
    updated = dict(task)
    if task.get("status") != "blocked":
        updated[REMINDER_COUNT_FIELD] = 0
    updated["status"] = "blocked"
    updated["block_note"] = note
    return updated
