"""Run the bounded MAM/Codex compatibility acceptance and save JSON evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any

from . import liveprobe, wake_compat
from .version import info as program_info


def _write(path: Path, value: dict[str, Any]) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise OSError(f"output path is not a regular file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _stage(name: str, status: str, started: float, *, error: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "status": status, "elapsed_seconds": round(time.monotonic() - started, 3)}
    if error:
        result["error"] = " ".join(error.split())[:800]
    return result


def _counts(evidence: dict[str, Any] | None) -> dict[str, Any]:
    resources = evidence.get("resources", {}) if isinstance(evidence, dict) else {}
    threads = resources.get("threads", {}) if isinstance(resources, dict) else {}
    turns = resources.get("turns", {}) if isinstance(resources, dict) else {}
    calls = evidence.get("calls", {}) if isinstance(evidence, dict) else {}
    checks = evidence.get("checks", {}) if isinstance(evidence, dict) else {}
    sessions = len(threads) if isinstance(threads, dict) else 0
    turn_ids = {value for value in turns.values() if isinstance(value, str) and value}
    direct = calls.get("direct_turn_start", 0) if isinstance(calls, dict) else 0
    model_turns = evidence.get("model_turns") if isinstance(evidence, dict) else None
    observed_turns = len(turn_ids) if turn_ids else (model_turns if isinstance(model_turns, int) else direct)
    usage = evidence.get("token_usage") if isinstance(evidence, dict) else None
    if not isinstance(usage, dict):
        usage = {key: None for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens")}
    input_tokens = usage.get("input_tokens")
    cached_tokens = usage.get("cached_input_tokens")
    if isinstance(input_tokens, int) and isinstance(cached_tokens, int) and cached_tokens > input_tokens:
        input_tokens = cached_tokens = None
    return {
        "sessions": sessions,
        "turns": observed_turns,
        "compactions": calls.get("compact_start", 0) if isinstance(calls, dict) else 0,
        "tests": sum(value is True for value in checks.values()) if isinstance(checks, dict) else 0,
        "model_requests": None,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": usage.get("reasoning_tokens"),
    }


def run(output: str | os.PathLike[str]) -> dict[str, Any]:
    target = Path(output).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    target = target.absolute()
    started = time.monotonic()
    metadata = program_info()
    result: dict[str, Any] = {
        "status": "failed",
        "version": metadata.get("version"),
        "commit": metadata.get("commit"),
        "model": liveprobe.MODEL,
        "effort": liveprobe.EFFORT,
        "elapsed_seconds": 0.0,
        "stages": [],
        "counts": _counts(None),
        "live_delivery": None,
    }
    root: Path | None = None
    compatibility: dict[str, Any] | None = None
    try:
        stage_started = time.monotonic()
        try:
            compatibility = wake_compat.require_compatible()
        except Exception as exc:
            result["stages"].append(_stage("non_model", "failed", stage_started, error=str(exc)))
            result["error"] = " ".join(str(exc).split())[:800]
            return result
        result["stages"].append(_stage("non_model", "passed", stage_started))

        stage_started = time.monotonic()
        parent = Path(tempfile.mkdtemp(prefix="mam-compatibility-"))
        root = parent / "liveprobe"
        evidence_path = parent / "liveprobe.json"
        try:
            delivery = liveprobe.run_live_delivery(
                compatibility,
                root,
                timeout_seconds=liveprobe.DEFAULT_TIMEOUT_SECONDS,
                evidence_path=evidence_path,
            )
        except Exception as exc:
            result["stages"].append(_stage("live_delivery", "failed", stage_started, error=str(exc)))
            result["error"] = " ".join(str(exc).split())[:800]
            if evidence_path.is_file():
                try:
                    result["live_delivery"] = json.loads(evidence_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, ValueError):
                    pass
        else:
            result["stages"].append(_stage("live_delivery", "passed", stage_started))
            result["live_delivery"] = delivery
            result["status"] = "passed"
        result["counts"] = _counts(result.get("live_delivery"))
        return result
    finally:
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        delivery = result.get("live_delivery")
        preserve_fixture = isinstance(delivery, dict) and (
            bool(delivery.get("cleanup_errors")) or isinstance(delivery.get("cleanup_root"), str)
        )
        if root is not None and not preserve_fixture:
            shutil.rmtree(root.parent, ignore_errors=True)
        try:
            _write(target, result)
        except OSError as exc:
            # A result that could not be persisted is never a successful check.
            result["status"] = "failed"
            result["error"] = f"cannot write compatibility output: {exc}"
            raise


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="run the MAM/Codex compatibility check")
    parser.add_argument("--output", default="mam-compatibility.json", metavar="FILE")
    args = parser.parse_args(argv)
    try:
        result = run(args.output)
    except OSError as exc:
        print(f"MAM Codex compatibility: FAIL\n{exc}")
        return 1
    print(f"MAM Codex compatibility: {'PASS' if result.get('status') == 'passed' else 'FAIL'}")
    return 0 if result.get("status") == "passed" else 1


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
