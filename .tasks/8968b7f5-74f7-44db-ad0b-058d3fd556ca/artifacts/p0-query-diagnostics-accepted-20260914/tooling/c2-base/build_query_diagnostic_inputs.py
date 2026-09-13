#!/usr/bin/env python3
"""Build immutable input and checkpoint evidence for one C2 diagnostic smoke.

This task-owned helper never writes beneath a source worktree or checkpoint.  It
hashes every regular file in the selected checkpoint, emits the audit format
consumed by ``robot_bridge.benchmark.runner``, and writes the narrow scheduler
configuration that enables exactly the selected diagnostic queries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


MIB = 1024 * 1024


VARIANTS = {
    "full_t_plus_1": {
        "checkpoint_alias": "CheckpointFull",
        "train_config": "pi05_rmbench_put_back_block_full_t_plus_1",
        "memory_config_id": "put_back_block_full_t_plus_1",
        "representation": "joint_dense",
    },
    "serial_lag30": {
        "checkpoint_alias": "CheckpointSerial",
        "train_config": "pi05_rmbench_put_back_block_serial_lag30",
        "memory_config_id": "put_back_block_serial_lag30",
        "representation": "serial_token",
    },
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(MIB), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest_rows(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda row: row["path"])
    return hashlib.sha256(_stable_json(ordered)).hexdigest()


def _file_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        if path.is_symlink():
            raise RuntimeError(f"checkpoint evidence refuses a symlinked file: {path}")
        before = path.stat()
        digest = _sha256_file(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ino,
        ):
            raise RuntimeError(f"checkpoint changed while hashing: {path}")
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": before.st_size,
                "sha256": digest,
            }
        )
    if not rows:
        raise RuntimeError(f"checkpoint subtree has no regular files: {root}")
    return rows


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _scheduler_yaml(directory: Path) -> str:
    return "\n".join(
        (
            "scheduler: openpi_simulation",
            "params:",
            "  move_steps: 30",
            "  debug_iterations: 0",
            "  diagnostic_trace:",
            f"    directory: {json.dumps(str(directory))}",
            "    episode_ids: [0, 1]",
            "    query_ids: [1]",
            "    max_records: 2",
            "    max_array_bytes: 67108864",
            "",
        )
    )


def _manifest(
    *,
    variant: str,
    checkpoint_alias: str,
    audit_sha256: str,
    params_assets_digest: str,
    metadata_digest: str,
    source_commits: dict[str, str],
) -> dict[str, Any]:
    info = VARIANTS[variant]
    checkpoint_id = f"query_diagnostic_{variant}_checkpoint"
    profile_id = f"query_diagnostic_{variant}_profile"
    run_id = f"query_diagnostic_{variant}"
    return {
        "schema_version": 1,
        "purpose": "C2 selected-query diagnostic technical smoke; no success-rate or mechanism claim",
        "stage": {
            "status": "inputs_ready",
            "scope": "Existing frozen 20k checkpoint; two accepted episodes only; diagnostic query 1 only.",
        },
        "source_identity": source_commits,
        "path_aliases": {
            "RMBench": "isolated task RMBench worktree",
            checkpoint_alias: "read-only frozen checkpoint parent",
            "TaskRecords": "task-owned diagnostic inputs, manifests, and outputs",
        },
        "run_profiles": {
            profile_id: {
                "config": "RMBench/policy/pi05/deploy_policy.yml",
                "fixed": {
                    "task_name": "put_back_block",
                    "task_config": "demo_clean_eval",
                    "seed": 0,
                    "test_num": 100,
                    "instruction_type": "unseen",
                    "eval_video_count": 5,
                    "eval_video_log": True,
                    "eval_video_key_state_overlay": True,
                    "pi0_step": 30,
                    "policy_name": "pi05",
                },
            }
        },
        "checkpoints": [
            {
                "id": checkpoint_id,
                "component": "Pi0.5",
                "role": "simulation",
                "path": f"{checkpoint_alias}/20000",
                "input_ready": True,
                "metadata": {
                    "path": f"{checkpoint_alias}/20000/metadata",
                    "hash": metadata_digest,
                    "status": "ready",
                },
                "tree_hash": {
                    "status": "ready",
                    "digest": params_assets_digest,
                    "method": "json_rows",
                    "evidence": "runner_input_audit.json",
                    "evidence_sha256": audit_sha256,
                    "entry_id": checkpoint_id,
                },
                "weight_content_manifest": "TaskRecords/manifests/" + variant + "/weight_content_manifest.json",
            }
        ],
        "simulation_runs": [
            {
                "id": run_id,
                "profile": profile_id,
                "checkpoint_ref": checkpoint_id,
                "config_source": "TaskRecords/manifests/" + variant,
                "task_overrides": {},
                "overrides": {
                    "evaluation_kind": "technical_query_diagnostic_smoke",
                    "train_config_name": info["train_config"],
                    "memory_config_id": info["memory_config_id"],
                    "memory_representation": info["representation"],
                },
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--records-root", required=True, type=Path)
    parser.add_argument("--rmbench-commit", required=True)
    parser.add_argument("--bridge-commit", required=True)
    parser.add_argument("--openpi-commit", required=True)
    args = parser.parse_args()

    checkpoint = args.checkpoint.resolve(strict=True)
    if checkpoint.name != "20000":
        raise RuntimeError(f"only a completed 20000 checkpoint is allowed, got {checkpoint}")
    for name in ("params", "assets", "metadata"):
        if not (checkpoint / name).is_dir():
            raise RuntimeError(f"checkpoint missing required {name}/ directory: {checkpoint}")
    if not (checkpoint / "_CHECKPOINT_METADATA").is_file():
        raise RuntimeError(f"checkpoint has no _CHECKPOINT_METADATA: {checkpoint}")

    records_root = args.records_root.resolve()
    output = records_root / "manifests" / args.variant
    source_commits = {
        "rmbench": args.rmbench_commit,
        "robot_bridge": args.bridge_commit,
        "openpi": args.openpi_commit,
    }

    all_rows = _file_rows(checkpoint)
    params_assets = [
        row for row in all_rows if row["path"].split("/", 1)[0] in {"params", "assets"}
    ]
    metadata_rows = _file_rows(checkpoint / "metadata")
    if not params_assets:
        raise RuntimeError("checkpoint has no params/assets files")
    weight_manifest = {
        "schema_version": 1,
        "kind": "checkpoint_weight_content_manifest",
        "checkpoint": str(checkpoint),
        "file_scope": "all regular files below the completed checkpoint directory",
        "hash_method": "sha256(json_rows_sorted_by_path)",
        "files": all_rows,
        "aggregate_sha256": _digest_rows(all_rows),
        "source_identity": source_commits,
        "planned_execution": {
            "task_name": "put_back_block",
            "task_config": "demo_clean_eval",
            "action_horizon": 50,
            "execution_rows": 30,
            "episode_ids": [0, 1],
            "env_seeds": [100000, 100001],
            "query_ids": [1],
            "max_records": 2,
            "max_array_bytes": 64 * MIB,
        },
        "result_link": {"status": "pending", "run_result_directory": None},
    }
    audit = {
        "schema_version": 1,
        "purpose": "Runner verification subset derived from the complete weight-content manifest.",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "checkpoints": [
            {
                "id": f"query_diagnostic_{args.variant}_checkpoint",
                "params_assets": params_assets,
                "metadata": metadata_rows,
                "weight_content_manifest": "weight_content_manifest.json",
                "weight_content_aggregate_sha256": weight_manifest["aggregate_sha256"],
            }
        ],
    }
    _atomic_json(output / "weight_content_manifest.json", weight_manifest)
    _atomic_json(output / "runner_input_audit.json", audit)
    audit_sha256 = _sha256_file(output / "runner_input_audit.json")
    alias = VARIANTS[args.variant]["checkpoint_alias"]
    manifest = _manifest(
        variant=args.variant,
        checkpoint_alias=alias,
        audit_sha256=audit_sha256,
        params_assets_digest=_digest_rows(params_assets),
        metadata_digest=_digest_rows(metadata_rows),
        source_commits=source_commits,
    )
    _atomic_json(output / "runner_input_manifest.json", manifest)
    diagnostics = records_root / "diagnostics" / args.variant
    _atomic_text(output / "scheduler_config.yaml", _scheduler_yaml(diagnostics))
    _atomic_json(
        output / "input_summary.json",
        {
            "variant": args.variant,
            "checkpoint": str(checkpoint),
            "checkpoint_file_count": len(all_rows),
            "checkpoint_total_bytes": sum(row["size"] for row in all_rows),
            "weight_content_aggregate_sha256": weight_manifest["aggregate_sha256"],
            "params_assets_digest": _digest_rows(params_assets),
            "metadata_digest": _digest_rows(metadata_rows),
            "runner_input_audit_sha256": audit_sha256,
            "runner_input_manifest_sha256": _sha256_file(output / "runner_input_manifest.json"),
            "scheduler_config_sha256": _sha256_file(output / "scheduler_config.yaml"),
            "diagnostic_directory": str(diagnostics),
        },
    )
    print(json.dumps(json.loads((output / "input_summary.json").read_text(encoding="utf-8")), sort_keys=True))


if __name__ == "__main__":
    main()
