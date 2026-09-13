#!/usr/bin/env python3
"""Require two complete, recorded selected-query diagnostics from one v2 smoke."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import traceback
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def atomic_json(path: Path, value: dict) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite smoke acceptance receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"non-object JSONL row in {path}")
            rows.append(value)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", required=True, choices=("full_t_plus_1", "serial_lag30"))
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--diagnostic-dir", required=True, type=Path)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--validator", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = {"schema_version": 1, "kind": "timeout90_selected_query_smoke_acceptance", "variant": args.variant, "status": "failed", "passed": False}
    try:
        config = args.config.resolve(strict=True)
        diagnostic_dir = args.diagnostic_dir.resolve(strict=True)
        result_dir = args.result_dir.resolve(strict=True)
        validator = args.validator.resolve(strict=True)
        yaml_payload = yaml.safe_load(config.read_text(encoding="utf-8"))
        params = yaml_payload.get("params") if isinstance(yaml_payload, dict) else None
        trace = params.get("diagnostic_trace") if isinstance(params, dict) else None
        if not isinstance(trace, dict) or Path(trace.get("directory", "")).resolve(strict=False) != diagnostic_dir:
            raise ValueError("result validation config does not point to this isolated diagnostic directory")
        if params.get("policy_first_infer_timeout") != 90.0:
            raise ValueError("result validation config lacks policy_first_infer_timeout=90.0")
        records = sorted((diagnostic_dir / "records").glob("*.json"))
        if len(records) != 2:
            raise ValueError(f"expected exactly two selected-query records, found {len(records)}")
        identities = []
        validator_results = []
        for record in records:
            process = subprocess.run([os.fspath(Path(os.sys.executable)), os.fspath(validator), os.fspath(record)], text=True, capture_output=True, check=False)
            if process.returncode != 0:
                raise RuntimeError(f"validate_query_diagnostic failed for {record}: {process.stderr.strip()}")
            validated = json.loads(process.stdout)
            if validated.get("status") != "recorded":
                raise ValueError(f"{record} validated as {validated.get('status')!r}, not recorded")
            data = json.loads(record.read_text(encoding="utf-8"))
            query = data.get("query")
            if not isinstance(query, dict):
                raise TypeError(f"{record} has no query identity")
            if data.get("status") != "recorded" or query.get("query_id") != 1:
                raise ValueError(f"{record} is not a recorded query-1 diagnostic")
            bundle = data.get("array_bundle")
            if not isinstance(bundle, dict) or not isinstance(bundle.get("file"), str):
                raise ValueError(f"{record} has no array bundle")
            array_path = record.parent.parent / bundle["file"]
            identities.append({
                "record": ref(record),
                "array_bundle": ref(array_path),
                "episode_id": query.get("episode_id"),
                "env_seed": query.get("env_seed"),
                "query_id": query.get("query_id"),
                "record_id": query.get("record_id"),
            })
            validator_results.append(validated)
        pairs = {(item["episode_id"], item["env_seed"], item["query_id"]) for item in identities}
        if pairs != {(0, 100000, 1), (1, 100001, 1)}:
            raise ValueError(f"unexpected recorded query identities: {sorted(pairs)!r}")
        summary_path = result_dir / "diagnostics_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        benchmark = summary.get("benchmark")
        if not isinstance(benchmark, dict) or benchmark.get("status") != "completed" or benchmark.get("target_episodes") != 2:
            raise ValueError(f"benchmark did not complete the two-episode smoke: {benchmark!r}")
        if summary.get("episode_count") != 2:
            raise ValueError("benchmark summary does not contain both accepted terminal episodes")
        process_events_path = result_dir / "processes.jsonl"
        process_events = read_jsonl(process_events_path)
        scheduler_exits = [row for row in process_events if row.get("event") == "exit" and row.get("role") == "scheduler"]
        if len(scheduler_exits) != 2 or any(row.get("returncode") != 0 for row in scheduler_exits):
            raise ValueError(f"scheduler exits are not two clean terminal exits: {scheduler_exits!r}")
        scheduler_logs = sorted((result_dir / "processes").glob("*-scheduler.stdout.log"))
        marker = "First policy inference uses 90.0s RPC budget."
        if len(scheduler_logs) != 2 or any(marker not in path.read_text(encoding="utf-8", errors="replace") for path in scheduler_logs):
            raise ValueError("each scheduler process did not log the configured 90-second first-call budget")
        result_scheduler = result_dir / "scheduler.yaml"
        result_yaml = yaml.safe_load(result_scheduler.read_text(encoding="utf-8"))
        result_params = result_yaml.get("params") if isinstance(result_yaml, dict) else None
        if not isinstance(result_params, dict) or result_params.get("policy_first_infer_timeout") != 90.0:
            raise ValueError("result leaf did not retain the 90-second first-infer scheduler config")
        receipt.update({
            "status": "passed",
            "passed": True,
            "config": ref(config),
            "result_scheduler_config": ref(result_scheduler),
            "result_summary": ref(summary_path),
            "process_events": ref(process_events_path),
            "scheduler_logs": [ref(path) for path in scheduler_logs],
            "records": identities,
            "validator_results": validator_results,
            "scheduler_first_infer_log_marker": marker,
            "subsequent_policy_rpc_seconds": 30.0,
        })
        atomic_json(args.output, receipt)
        print(json.dumps({"passed": True, "output": str(args.output)}, sort_keys=True))
        return 0
    except BaseException as exc:
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        try:
            atomic_json(args.output, receipt)
        except BaseException:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
