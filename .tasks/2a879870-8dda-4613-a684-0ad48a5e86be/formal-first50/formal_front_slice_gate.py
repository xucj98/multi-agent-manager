#!/usr/bin/env python3
"""Check a completed front slice without requiring a live run to stop at exactly N rows."""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from typing import Any

INFRA_PATTERNS = (
    r"Traceback",
    r"FileNotFoundError",
    r"ConnectionResetError",
    r"AttributeError",
    r"ErrorIncompatibleDriver",
    r"Your GPU driver does not support Vulkan",
    r"worker closed the RPC stream",
    r"\bEOFError\b",
)


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def categories(records: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(collections.Counter(
        str((record.get("diagnostics") or {}).get("primary_failure_reason", "missing_reason"))
        for record in records if record.get("result") != "Success"
    ).items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--worker-log", type=Path, required=True)
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        raise SystemExit("--count must be positive")

    run_dir, baseline_dir = args.run_dir.resolve(), args.baseline_dir.resolve()
    completed_all = rows(run_dir / "episode_diagnostics.jsonl")
    preflight_all = rows(run_dir / "seed_preflight.jsonl")
    videos_all = rows(run_dir / "video_checks.jsonl")
    completed = completed_all[:args.count]
    expected_episodes = list(range(args.count))
    expected_seeds = [100000 + episode for episode in expected_episodes]
    preflight = {item.get("episode_id"): item for item in preflight_all if item.get("episode_id") in expected_episodes}
    videos = {item.get("episode_id"): item for item in videos_all if item.get("episode_id") in expected_episodes}
    worker_text = args.worker_log.read_text(encoding="utf-8", errors="replace") if args.worker_log.is_file() else ""
    matches = {pattern: len(re.findall(pattern, worker_text)) for pattern in INFRA_PATTERNS}
    matches = {pattern: count for pattern, count in matches.items() if count}

    completed_shape_ok = (
        len(completed_all) >= args.count
        and [item.get("episode_id") for item in completed] == expected_episodes
        and [item.get("seed") for item in completed] == expected_seeds
    )
    preflight_ok = all(
        (item := preflight.get(episode)) is not None
        and item.get("seed") == 100000 + episode
        and item.get("accepted") is True
        and (item.get("response") or {}).get("status") == "ok"
        for episode in expected_episodes
    )
    diagnostics_ok = all(
        item.get("error") in (None, "")
        and not ((item.get("diagnostics") or {}).get("runtime_error"))
        and ((item.get("diagnostics") or {}).get("episode_status") or {}).get("terminal") is True
        for item in completed
    )
    video_ok = all(
        (item := videos.get(episode)) is not None
        and item.get("enabled") is (episode < 5)
        and item.get("ok") is True
        for episode in expected_episodes
    )

    baseline_all = rows(baseline_dir / "episode_diagnostics.jsonl")
    baseline = baseline_all[:args.count]
    current_success = sum(item.get("result") == "Success" for item in completed)
    baseline_success = sum(item.get("result") == "Success" for item in baseline)
    output = {
        "kind": "formal_front_completed_slice_gate",
        "run_dir": str(run_dir),
        "baseline_dir": str(baseline_dir),
        "requested_completed_slice": args.count,
        "available": {
            "completed_rows": len(completed_all),
            "preflight_rows": len(preflight_all),
            "video_rows": len(videos_all),
        },
        "slice": {
            "episode_ids": [item.get("episode_id") for item in completed],
            "seeds": [item.get("seed") for item in completed],
            "success": current_success,
            "failure_categories": categories(completed),
        },
        "baseline_same_slice": {
            "available_completed_rows": len(baseline_all),
            "success": baseline_success,
            "failure_categories": categories(baseline),
            "success_delta": current_success - baseline_success,
        },
        "checks": {
            "completed_shape": completed_shape_ok,
            "accepted_preflight": preflight_ok,
            "terminal_without_runtime_error": diagnostics_ok,
            "video_protocol": video_ok,
            "worker_infrastructure_matches": matches,
        },
        "healthy_infrastructure_slice": completed_shape_ok and preflight_ok and diagnostics_ok and video_ok and not matches,
        "note": "Checks the first N completed diagnostics records and matching IDs; it intentionally permits later live rows to already exist.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if output["healthy_infrastructure_slice"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
