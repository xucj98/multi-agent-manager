#!/usr/bin/env python3
"""Offline comparison of the two bounded first-query captures.

This reader consumes only task-private artifacts.  It never starts a model,
simulator, policy server, or scheduler.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from capture_common import atomic_write_json, canonical_json, sha256_bytes


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"{path} is not a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"{path}:{number} is not a JSON object")
            records.append(value)
    return records


def at(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def leaf_map(snapshot: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(snapshot, Mapping):
        return {}
    leaves = snapshot.get("leaves")
    if not isinstance(leaves, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for leaf in leaves:
        if isinstance(leaf, Mapping) and isinstance(leaf.get("path"), str):
            result[str(leaf["path"])] = dict(leaf)
    return result


def normalized_leaf(leaf: Mapping[str, Any]) -> dict[str, Any]:
    # archive-key names belong to each local NPZ bundle, not the data contract
    return {str(key): value for key, value in leaf.items() if key != "array_key"}


def load_snapshot_array(snapshot: Any, path: str) -> np.ndarray | None:
    if not isinstance(snapshot, Mapping):
        return None
    leaf = leaf_map(snapshot).get(path)
    bundle = snapshot.get("array_bundle")
    if not isinstance(leaf, Mapping) or leaf.get("kind") != "array" or not isinstance(bundle, Mapping):
        return None
    array_key, bundle_path = leaf.get("array_key"), bundle.get("path")
    if not isinstance(array_key, str) or not isinstance(bundle_path, str):
        return None
    source = Path(bundle_path)
    if not source.is_file():
        return None
    with np.load(source, allow_pickle=False) as archive:
        if array_key not in archive:
            return None
        return np.array(archive[array_key], copy=True)


def array_difference(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    result: dict[str, Any] = {
        "left_shape": list(left.shape),
        "right_shape": list(right.shape),
        "left_dtype": left.dtype.str,
        "right_dtype": right.dtype.str,
    }
    if left.shape != right.shape:
        result.update(equal=False, reason="shape_mismatch")
        return result
    try:
        equal = np.array_equal(left, right, equal_nan=True)
    except TypeError:
        equal = np.array_equal(left, right)
    result["equal"] = bool(equal)
    if equal:
        result["different_elements"] = 0
        return result
    different = np.not_equal(left, right)
    result["different_elements"] = int(np.count_nonzero(different))
    if np.issubdtype(left.dtype, np.inexact) and np.issubdtype(right.dtype, np.inexact):
        finite = np.isfinite(left) & np.isfinite(right)
        delta = np.abs(left.astype(np.float64) - right.astype(np.float64))
        result.update(
            finite_compared_elements=int(np.count_nonzero(finite)),
            max_abs=None if not np.any(finite) else float(np.max(delta[finite])),
            rmse=None if not np.any(finite) else float(np.sqrt(np.mean(np.square(delta[finite])))),
            nonfinite_left=int(np.count_nonzero(~np.isfinite(left))),
            nonfinite_right=int(np.count_nonzero(~np.isfinite(right))),
        )
    return result


def compare_snapshots(left: Any, right: Any) -> dict[str, Any]:
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return {
            "equal": False,
            "reason": "missing_or_malformed_snapshot",
            "baseline_type": None if left is None else type(left).__name__,
            "shadow_type": None if right is None else type(right).__name__,
        }
    left_leaves, right_leaves = leaf_map(left), leaf_map(right)
    for path in sorted(set(left_leaves) | set(right_leaves)):
        lhs, rhs = left_leaves.get(path), right_leaves.get(path)
        if lhs is None or rhs is None or normalized_leaf(lhs) != normalized_leaf(rhs):
            result: dict[str, Any] = {
                "equal": False,
                "first_unequal_path": path,
                "baseline": None if lhs is None else normalized_leaf(lhs),
                "shadow": None if rhs is None else normalized_leaf(rhs),
            }
            if (
                isinstance(lhs, Mapping)
                and isinstance(rhs, Mapping)
                and lhs.get("kind") == "array"
                and rhs.get("kind") == "array"
            ):
                left_array, right_array = load_snapshot_array(left, path), load_snapshot_array(right, path)
                if left_array is not None and right_array is not None:
                    result["array_difference"] = array_difference(left_array, right_array)
            return result
    return {
        "equal": True,
        "leaf_count": len(left_leaves),
        "baseline_tree_sha256": left.get("tree_sha256"),
        "shadow_tree_sha256": right.get("tree_sha256"),
    }


def compare_arrays(name: str, left: np.ndarray | None, right: np.ndarray | None) -> dict[str, Any]:
    if left is None or right is None:
        return {
            "name": name,
            "equal": False,
            "reason": "missing_array",
            "left_available": left is not None,
            "right_available": right is not None,
        }
    return {"name": name, **array_difference(left, right)}


def capture(root: Path, label: str) -> dict[str, Any]:
    location = root / "captures" / label
    required = {
        "index": location / "run_index.json",
        "scheduler": location / "scheduler" / "scheduler_trace.json",
        "policy": location / "policy" / "policy_trace.json",
        "runtime": location / "policy" / "policy_runtime.json",
        "samples": location / "policy" / "policy_samples.jsonl",
        "lifecycle": location / "policy" / "policy_lifecycle.jsonl",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"{label}: missing {missing}")
    policy = read_json(required["policy"])
    first = policy.get("first_query")
    full = first.get("full_capture_artifacts") if isinstance(first, Mapping) else None
    if not isinstance(first, Mapping) or not isinstance(full, Mapping):
        raise ValueError(f"{label}: no full first-query policy capture")
    return {
        "label": label,
        "location": str(location),
        "index": read_json(required["index"]),
        "scheduler": read_json(required["scheduler"]),
        "policy": policy,
        "runtime": read_json(required["runtime"]),
        "samples": read_jsonl(required["samples"]),
        "lifecycle": read_jsonl(required["lifecycle"]),
        "first": dict(first),
        "full": dict(full),
    }


def snapshot(item: Mapping[str, Any], name: str) -> Any:
    scheduler, full = item["scheduler"], item["full"]
    values = {
        "scheduler_pre_rpc": at(scheduler, "first_query_input", "snapshot"),
        "policy_pre_transform": full.get("before_policy_input_transform"),
        "policy_post_transform": full.get("after_policy_input_transform"),
        "implicit_noise": full.get("implicit_noise_derived_from_sampling_key"),
        "model_output_h50": full.get("model_outputs_before_output_transform"),
        "policy_output_h50": full.get("outputs_after_output_transform"),
        "queued_k30": at(scheduler, "queued_actions", "snapshot"),
    }
    return values[name]


def raw_policy_actions(item: Mapping[str, Any]) -> np.ndarray | None:
    return load_snapshot_array(snapshot(item, "policy_output_h50"), "$/actions")


def real_actions(item: Mapping[str, Any]) -> np.ndarray | None:
    """Recreate the frozen OpenPiBackend wire dtype before scheduler use.

    Policy.infer retains its transform output as float64.  The frozen backend
    immediately applies np.asarray(actions, dtype=np.float32) before the
    WebSocket response and scheduler queue.  Replays archive that latter,
    actual wire representation, so comparisons must use the same cast.
    """

    raw = raw_policy_actions(item)
    return None if raw is None else np.asarray(raw, dtype=np.float32)


def queued_actions(item: Mapping[str, Any]) -> np.ndarray | None:
    value = snapshot(item, "queued_k30")
    paths = [
        path
        for path, leaf in leaf_map(value).items()
        if leaf.get("kind") == "array"
    ]
    return load_snapshot_array(value, paths[0]) if len(paths) == 1 else None


def replay_actions(item: Mapping[str, Any], ordinal: int) -> np.ndarray | None:
    source = Path(str(item["location"])) / f"replay_{ordinal}_output.npz"
    if not source.is_file():
        return None
    with np.load(source, allow_pickle=False) as archive:
        return np.array(archive["actions"], copy=True) if "actions" in archive else None


def rng_comparison(baseline: Mapping[str, Any], shadow: Mapping[str, Any]) -> dict[str, Any]:
    base_rng, shadow_rng = at(baseline["first"], "rng"), at(shadow["first"], "rng")
    result: dict[str, Any] = {}
    for field in ("state_before_split", "sampling_key", "state_after_split_from_return", "state_after_split"):
        left = base_rng.get(field) if isinstance(base_rng, Mapping) else None
        right = shadow_rng.get(field) if isinstance(shadow_rng, Mapping) else None
        result[field] = {"equal": left == right, "baseline": left, "shadow": right}
    return result


def first_detail(value: Mapping[str, Any]) -> str:
    if value.get("equal") is True:
        return "equal"
    path = value.get("first_unequal_path")
    return f"difference at {path}" if isinstance(path, str) else str(value.get("reason", "different"))


def classify(cross: Mapping[str, Any], rng: Mapping[str, Any], replays: Mapping[str, Any]) -> dict[str, str]:
    for name, category in (
        ("scheduler_pre_rpc", "scheduler input divergence"),
        ("policy_pre_transform", "policy wire-input divergence"),
        ("policy_post_transform", "input-transform divergence"),
    ):
        value = cross[name]
        if value.get("equal") is not True:
            return {"classification": category, "detail": first_detail(value)}
    changed_keys = [name for name, value in rng.items() if value.get("equal") is not True]
    if changed_keys:
        return {"classification": "action PRNG divergence", "detail": ", ".join(changed_keys)}
    if cross["implicit_noise"].get("equal") is not True:
        return {"classification": "derived diffusion-noise divergence", "detail": first_detail(cross["implicit_noise"])}
    for name in ("model_output_h50", "policy_output_h50"):
        if cross[name].get("equal") is not True:
            return {
                "classification": "model/output divergence under matched observed input and key",
                "detail": first_detail(cross[name]),
            }
    for name, value in replays.items():
        if value.get("equal") is not True:
            return {"classification": "fixed-input/key replay divergence", "detail": f"{name}: {first_detail(value)}"}
    if cross["queued_k30"].get("equal") is not True:
        return {"classification": "queue construction divergence", "detail": first_detail(cross["queued_k30"])}
    return {
        "classification": "no divergence in bounded capture",
        "detail": "all retained inputs, keys, noise, model outputs, queues, and replays were equal",
    }


def markdown(analysis: Mapping[str, Any]) -> str:
    lines = [
        "# Bounded matched first-query diagnostic",
        "",
        "Scope: put_back_block, train seed 0, environment seed 100000. Each entrypoint made one real action query and two fixed-input replays.",
        "",
        "## Accounting",
        "",
    ]
    accounting = analysis["accounting"]
    lines += [
        f"- Baseline policy samples: {accounting['baseline_policy_samples']}",
        f"- Shadow policy samples: {accounting['shadow_policy_samples']}",
        f"- Planned normal samples: {accounting['planned_normal_action_samples']} / limit {accounting['global_limit']}",
        "- Replay comparisons use the frozen backend's float32 action-wire cast; raw Policy transform output is retained separately.",
        "",
        "## Earliest observed divergence",
        "",
        f"{analysis['diagnosis']['classification']}: {analysis['diagnosis']['detail']}",
        "",
        "## Cross-entrypoint sites",
        "",
        "| Site | Result |",
        "| --- | --- |",
    ]
    for name, result in analysis["cross_entrypoint"].items():
        lines.append(f"| {name} | {first_detail(result)} |")
    lines += ["", "## Same-input/key replays", "", "| Comparison | Result |", "| --- | --- |"]
    for name, result in analysis["replays"].items():
        if result.get("equal") is True:
            shown = "equal"
        else:
            shown = f"different ({result.get('different_elements', result.get('reason', 'unknown'))})"
        lines.append(f"| {name} | {shown} |")
    lines += [
        "",
        "See analysis.json for full structured evidence, hashes, first unequal leaves, numerical deltas, source identities, lifecycle records, and resource snapshots.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-root", required=True, type=Path)
    parser.add_argument("--baseline-label", default="matched_baseline")
    parser.add_argument("--shadow-label", default="matched_shadow")
    args = parser.parse_args()
    root = args.task_root.resolve()
    baseline, shadow = capture(root, args.baseline_label), capture(root, args.shadow_label)

    names = (
        "scheduler_pre_rpc",
        "policy_pre_transform",
        "policy_post_transform",
        "implicit_noise",
        "model_output_h50",
        "policy_output_h50",
        "queued_k30",
    )
    cross = {name: compare_snapshots(snapshot(baseline, name), snapshot(shadow, name)) for name in names}
    rng = rng_comparison(baseline, shadow)

    base_raw, shadow_raw = raw_policy_actions(baseline), raw_policy_actions(shadow)
    base_real, shadow_real = real_actions(baseline), real_actions(shadow)
    base_queue, shadow_queue = queued_actions(baseline), queued_actions(shadow)
    base_one, base_two = replay_actions(baseline, 1), replay_actions(baseline, 2)
    shadow_one, shadow_two = replay_actions(shadow, 1), replay_actions(shadow, 2)
    replays = {
        "baseline_real_vs_replay_1": compare_arrays("baseline_real_vs_replay_1", base_real, base_one),
        "baseline_replay_1_vs_replay_2": compare_arrays("baseline_replay_1_vs_replay_2", base_one, base_two),
        "shadow_cross_replay_1_vs_replay_2": compare_arrays("shadow_cross_replay_1_vs_replay_2", shadow_one, shadow_two),
        "baseline_replay_1_vs_shadow_cross_replay_1": compare_arrays(
            "baseline_replay_1_vs_shadow_cross_replay_1", base_one, shadow_one
        ),
        "baseline_replay_2_vs_shadow_cross_replay_2": compare_arrays(
            "baseline_replay_2_vs_shadow_cross_replay_2", base_two, shadow_two
        ),
        "baseline_real_h50_prefix_vs_queued_k30": compare_arrays(
            "baseline_real_h50_prefix_vs_queued_k30",
            None if base_real is None or base_queue is None else base_real[: len(base_queue)],
            base_queue,
        ),
        "shadow_real_h50_prefix_vs_queued_k30": compare_arrays(
            "shadow_real_h50_prefix_vs_queued_k30",
            None if shadow_real is None or shadow_queue is None else shadow_real[: len(shadow_queue)],
            shadow_queue,
        ),
    }
    analysis: dict[str, Any] = {
        "schema_version": 1,
        "scope": {
            "task_root": str(root),
            "baseline_label": args.baseline_label,
            "shadow_label": args.shadow_label,
            "purpose": "bounded_first_query_only",
        },
        "accounting": {
            "baseline_policy_samples": baseline["policy"].get("sample_count"),
            "shadow_policy_samples": shadow["policy"].get("sample_count"),
            "baseline_scheduler_action_samples": baseline["scheduler"].get("action_sample_count"),
            "shadow_scheduler_action_samples": shadow["scheduler"].get("action_sample_count"),
            "planned_normal_action_samples": 6,
            "global_limit": 8,
        },
        "source_identity": {
            "baseline": {
                "policy_imports": baseline["runtime"].get("imports"),
                "scheduler_source": at(baseline["scheduler"], "frozen_sources", "scheduler_module"),
                "run_inputs": baseline["index"].get("inputs"),
                "resources_before": baseline["index"].get("resources_before"),
                "resources_after": baseline["index"].get("resources_after"),
            },
            "shadow": {
                "policy_imports": shadow["runtime"].get("imports"),
                "scheduler_source": at(shadow["scheduler"], "frozen_sources", "scheduler_module"),
                "run_inputs": shadow["index"].get("inputs"),
                "resources_before": shadow["index"].get("resources_before"),
                "resources_after": shadow["index"].get("resources_after"),
            },
        },
        "wire_precision": {
            "frozen_backend_expression": "np.asarray(result['actions'], dtype=np.float32)",
            "baseline_policy_transform_dtype": None if base_raw is None else base_raw.dtype.str,
            "shadow_policy_transform_dtype": None if shadow_raw is None else shadow_raw.dtype.str,
            "baseline_wire_dtype": None if base_real is None else base_real.dtype.str,
            "shadow_wire_dtype": None if shadow_real is None else shadow_real.dtype.str,
        },
        "cross_entrypoint": cross,
        "rng": rng,
        "replays": replays,
        "lifecycle": {"baseline": baseline["lifecycle"], "shadow": shadow["lifecycle"]},
    }
    analysis["diagnosis"] = classify(cross, rng, replays)
    analysis["analysis_sha256"] = sha256_bytes(canonical_json(analysis))
    out = root / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out / "analysis.json", analysis)
    (out / "analysis.md").write_text(markdown(analysis), encoding="utf-8")
    print(out / "analysis.json")
    print(out / "analysis.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
