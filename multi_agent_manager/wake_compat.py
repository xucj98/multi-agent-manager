"""Non-model App Server compatibility checks for proactive MAM wakeups.

The scheduler calls :func:`require_compatible` at service startup and bounded
reconnection points.  Every request deliberately targets a new random,
unknown thread, so this check validates the event-stream RPC path without
creating a thread, changing a registered thread, or consuming a model turn.
The installer runs :mod:`multi_agent_manager.liveprobe` separately for real
managed-agent delivery acceptance.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid
from collections.abc import Callable, Mapping
from typing import Any

from . import job_runtime


DEFAULT_SOCKET_PATH = Path(job_runtime.DEFAULT_SOCKET_PATH)


class CompatibilityError(RuntimeError):
    """The local App Server cannot safely support the wake scheduler."""


def configured_socket_path() -> Path:
    """Return the absolute App Server control socket selected for this run."""

    raw = os.environ.get("MAM_APP_SERVER_SOCKET", str(DEFAULT_SOCKET_PATH))
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\n" in raw or "\r" in raw:
        raise CompatibilityError("the App Server control socket path must be a single-line absolute path")
    try:
        path = Path(raw)
    except (TypeError, ValueError) as exc:
        raise CompatibilityError("the App Server control socket path is invalid") from exc
    if not path.is_absolute():
        raise CompatibilityError("the App Server control socket path must be absolute")
    return path


def _socket_identity(path: Path) -> dict[str, int]:
    try:
        metadata = path.stat()
    except OSError as exc:
        raise CompatibilityError("the Codex App Server control socket is unavailable") from exc
    if not stat.S_ISSOCK(metadata.st_mode):
        raise CompatibilityError("the configured App Server control path is not a Unix socket")
    return {"device": metadata.st_dev, "inode": metadata.st_ino}


def _unknown_thread_rejection(detail: str) -> bool:
    """Return whether an App Server error specifically rejects a thread ID.

    An unsupported method must not look like a successful compatibility check,
    so a generic JSON-RPC error is insufficient.  The server's detail is never
    surfaced in the diagnostic because it is external, unbounded input.
    """

    # ``AppServerEventError`` prefixes the operation name (for example,
    # ``thread/read``).  Inspect only the remote detail so "method not found"
    # cannot accidentally satisfy the word "thread" through that prefix.
    remote = detail.rpartition(" failed: ")[2] or detail
    lowered = remote.lower()
    return "thread" in lowered and any(
        marker in lowered
        for marker in (
            "unknown",
            "not found",
            "not loaded",
            "no such",
            "no rollout found",
            "does not exist",
            "missing",
            "cannot find",
            "could not find",
        )
    )


def _expect_unknown_thread_rejection(
    operation: Callable[[], Any], *, method: str
) -> None:
    """Require one public event-stream operation to reject the random ID."""

    try:
        operation()
    except job_runtime.AppServerEventError as exc:
        if _unknown_thread_rejection(str(exc)):
            return
        raise CompatibilityError(
            f"the App Server did not reject {method} as an unknown thread through the expected RPC path"
        ) from exc
    except (OSError, TimeoutError) as exc:
        raise CompatibilityError(
            f"the App Server could not complete {method} through the event-stream RPC path"
        ) from exc
    except Exception as exc:
        raise CompatibilityError(
            f"the App Server could not complete {method} through the event-stream RPC path"
        ) from exc
    raise CompatibilityError(
        f"the App Server unexpectedly accepted {method} for an unknown thread; compatibility is unsafe"
    )


def _api_rejection_probe(socket_path: Path) -> tuple[str, ...]:
    """Exercise read, resume, latest-turn and turn-start without model work."""

    stream: Any | None = None
    unknown_thread = str(uuid.uuid4())
    try:
        stream = job_runtime.AppServerEventStream.connect(str(socket_path))
        operations = (
            ("thread/read", lambda: stream.read(unknown_thread)),
            ("thread/resume", lambda: stream.resume(unknown_thread)),
            ("thread/turns/list", lambda: stream.latest_turn(unknown_thread)),
            (
                "turn/start",
                lambda: stream.start_turn(unknown_thread, "MAM compatibility probe; unknown thread only."),
            ),
        )
        for method, operation in operations:
            _expect_unknown_thread_rejection(operation, method=method)
        return tuple(method for method, _ in operations)
    except CompatibilityError:
        raise
    except (OSError, TimeoutError) as exc:
        raise CompatibilityError("the Codex App Server event stream is unavailable or incompatible") from exc
    except Exception as exc:
        raise CompatibilityError("the Codex App Server event stream is unavailable or incompatible") from exc
    finally:
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass


def require_compatible() -> dict[str, Any]:
    """Validate the non-model event-stream behavior required by wakeups.

    No version allowlist or cached certificate is used.  A successful result
    confirms only the concrete unknown-thread RPC path; it does not claim to
    have observed a notification or a managed-agent delivery.
    """

    socket_path = configured_socket_path()
    before = _socket_identity(socket_path)
    methods = _api_rejection_probe(socket_path)
    after = _socket_identity(socket_path)
    if before != after:
        raise CompatibilityError("the Codex App Server control socket changed during validation")
    return {
        "socket_path": str(socket_path),
        "capabilities": {
            "control_socket": "validated",
            "thread_read": "validated-by-unknown-thread-rejection",
            "thread_resume": "validated-by-unknown-thread-rejection",
            "latest_turn": "validated-by-unknown-thread-rejection",
            "turn_start": "validated-by-unknown-thread-rejection",
            "event_stream_request_path": "validated-by-unknown-thread-rejection",
            "event_notifications": "not-observed-without-managed-thread",
            "model_requests": 0,
            "managed_agent_delivery": "not-validated-by-lightweight-check",
        },
        "diagnostics": {
            "socket_device": after["device"],
            "socket_inode": after["inode"],
            "probe_methods": list(methods),
            "probe_thread": "random unknown UUID (not persisted)",
        },
    }


def _redact_secrets(value: str) -> str:
    return re.sub(r"(?i)\b(token|secret|password|api[_-]?key)\s*=\s*[^\s,;]+", r"\1=<redacted>", value)


def _pending_count(value: Any) -> int:
    if not isinstance(value, Mapping):
        raise CompatibilityError("mam service status returned an invalid pending summary")
    count = value.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise CompatibilityError("mam service status returned an invalid pending count")
    if not isinstance(value.get("events"), list):
        raise CompatibilityError("mam service status returned invalid pending events")
    return count


def _status_error(status: Mapping[str, Any]) -> CompatibilityError:
    error = status.get("error")
    if (
        status.get("status") == "error"
        and status.get("manager") is None
        and isinstance(error, str)
        and "no determinable Manager" in error
    ):
        return CompatibilityError(
            "bound tasks have no persisted Manager; run mam service start --manager AGENT-ID"
        )
    if status.get("status") == "disabled":
        return CompatibilityError("the proactive wake service is disabled")
    if isinstance(error, str) and error:
        compact = _redact_secrets(" ".join(error.split())[:800])
        return CompatibilityError(f"the proactive wake service reported: {compact}")
    return CompatibilityError("the proactive wake service did not acknowledge readiness")


def service_readiness(status: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the JSON mapping returned by ``mam service status``."""

    if not isinstance(status, Mapping):
        raise CompatibilityError("mam service status returned no JSON object")
    running, healthy, lifecycle = status.get("running"), status.get("healthy"), status.get("status")
    if not isinstance(running, bool):
        raise CompatibilityError("mam service status omitted its running flag")
    if not isinstance(healthy, bool):
        raise CompatibilityError("mam service status omitted its healthy flag")
    if not isinstance(lifecycle, str):
        raise CompatibilityError("mam service status omitted its status")
    pending = _pending_count(status.get("pending"))

    if lifecycle == "awaiting_manager":
        if not running or not healthy:
            raise CompatibilityError("the awaiting_manager service is not running and healthy")
        if status.get("manager") is not None:
            raise CompatibilityError("awaiting_manager unexpectedly has a Manager binding")
        if pending:
            raise CompatibilityError("awaiting_manager unexpectedly has pending delivery work")
        return {"status": lifecycle, "running": running, "pending": pending, "manager": None}

    if lifecycle in {"healthy", "pending"}:
        manager = status.get("manager")
        if not running or not healthy:
            raise CompatibilityError("the wake service is not running and healthy")
        if not isinstance(manager, str) or not manager:
            raise CompatibilityError("the healthy wake service has no persisted Manager")
        if lifecycle == "healthy" and pending:
            raise CompatibilityError("healthy service status contradicts its pending summary")
        return {"status": lifecycle, "running": running, "pending": pending, "manager": manager}

    raise _status_error(status)


def load_service_status(path: str | os.PathLike[str]) -> Mapping[str, Any]:
    """Read one bounded status payload produced by the administrative CLI."""

    target = Path(path)
    try:
        if target.stat().st_size > 1024 * 1024:
            raise CompatibilityError("mam service status output is unexpectedly large")
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except CompatibilityError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatibilityError("mam service status did not return valid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise CompatibilityError("mam service status returned no JSON object")
    return parsed


def _print_json(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, sort_keys=True))


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="validate MAM proactive wakeup capabilities")
    parser.add_argument(
        "--service-status",
        metavar="PATH",
        help="validate a JSON payload produced by mam service status instead of probing the control socket",
    )
    parser.add_argument("--quiet", action="store_true", help="print only a short successful result")
    parser.add_argument("--json", action="store_true", help="print the validated result as one JSON object")
    args = parser.parse_args(argv)
    if args.quiet and args.json:
        parser.error("--quiet and --json cannot be used together")
    try:
        if args.service_status:
            result = service_readiness(load_service_status(args.service_status))
            if args.json:
                _print_json(result)
            elif args.quiet:
                print(result["status"])
            else:
                print("MAM proactive wakeup service: PASS")
                print(f"status: {result['status']}")
                print(f"pending: {result['pending']}")
        else:
            result = require_compatible()
            if args.json:
                _print_json(result)
            elif args.quiet:
                print("compatible")
            else:
                print("MAM proactive wakeup compatibility: PASS")
                print(f"socket: {result['socket_path']}")
                print("probe: unknown-thread RPC rejections only; model requests: 0")
    except CompatibilityError as exc:
        label = "service" if args.service_status else "compatibility"
        print(f"MAM proactive wakeup {label}: FAIL")
        print(str(exc))
        return 1
    return 0


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
