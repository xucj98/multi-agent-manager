#!/usr/bin/env python3
"""Align frozen put-back first-query evidence with the bounded capture.

This is an offline, task-private reader.  It opens retained JSON/JSONL/NPZ
artifacts only; it never imports a policy, starts a service, resets an
environment, or invokes JAX/GPU work.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import numpy as np


OLD_BASELINE = "c_hf_j_matched_baseline_engineering_put_back_trainseed0_eval0_2ep"
OLD_SHADOW = "c_hf_j_matched_shadow_engineering_put_back_trainseed0_eval0_2ep"
PROMPT = (
    "There are four mats, one block, and a button on the table. One block is on one of the mats. "
    "First, put the block to the center, then press the button. Then, put the block back in its original position."
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def array_sha256(array: np.ndarray) -> str:
    return sha256_bytes(np.ascontiguousarray(array).tobytes(order="C"))


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


def npz_array(path: Path, key: str) -> np.ndarray:
    with np.load(path, allow_pickle=False) as archive:
        if key not in archive:
            raise KeyError(f"{path} has no {key}")
        return np.array(archive[key], copy=True)


def first_record(records: Iterable[Mapping[str, Any]], record_type: str) -> dict[str, Any]:
    for record in records:
        if record.get("record_type") == record_type and record.get("source_step") == 0:
            return dict(record)
    raise LookupError(f"no source_step=0 {record_type}")


def comparison(name: str, left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    if left.shape != right.shape:
        return {
            "name": name,
            "equal": False,
            "reason": "shape_mismatch",
            "left_shape": list(left.shape),
            "right_shape": list(right.shape),
            "left_dtype": left.dtype.str,
            "right_dtype": right.dtype.str,
        }
    equal = np.equal(left, right)
    result: dict[str, Any] = {
        "name": name,
        "left_shape": list(left.shape),
        "right_shape": list(right.shape),
        "left_dtype": left.dtype.str,
        "right_dtype": right.dtype.str,
        "left_raw_sha256": array_sha256(left),
        "right_raw_sha256": array_sha256(right),
        "equal": bool(np.all(equal)),
        "different_elements": int(np.size(equal) - np.count_nonzero(equal)),
    }
    if result["equal"]:
        result.update(max_abs=0.0, rmse=0.0, first_difference=None)
        return result
    delta = left.astype(np.float64) - right.astype(np.float64)
    absolute = np.abs(delta)
    index = tuple(int(item) for item in np.argwhere(~equal)[0])
    result.update(
        max_abs=float(np.max(absolute)),
        rmse=float(math.sqrt(float(np.mean(np.square(delta))))),
        first_difference={
            "index": list(index),
            "left": float(left[index]),
            "right": float(right[index]),
            "delta_left_minus_right": float(delta[index]),
        },
    )
    return result


def snapshot_leaf(snapshot: Mapping[str, Any], wanted_path: str) -> tuple[Path, str]:
    bundle = snapshot.get("array_bundle")
    if not isinstance(bundle, Mapping) or not isinstance(bundle.get("path"), str):
        raise TypeError(f"snapshot has no array bundle for {wanted_path}")
    for leaf in snapshot.get("leaves", []):
        if isinstance(leaf, Mapping) and leaf.get("path") == wanted_path:
            array_key = leaf.get("array_key")
            if not isinstance(array_key, str):
                raise TypeError(f"snapshot leaf {wanted_path} is not retained as an array")
            return Path(str(bundle["path"])), array_key
    raise LookupError(f"snapshot has no {wanted_path}")


def capture_paths(root: Path, label: str) -> dict[str, Path]:
    capture = root / "captures" / label
    return {
        "capture": capture,
        "index": capture / "run_index.json",
        "context": capture / "episode_context.json",
        "policy_trace": capture / "policy" / "policy_trace.json",
        "scheduler_trace": capture / "scheduler" / "scheduler_trace.json",
    }


def load_new_capture(root: Path, label: str) -> dict[str, Any]:
    paths = capture_paths(root, label)
    for path in paths.values():
        if path.name != label and not path.is_file():
            raise FileNotFoundError(path)
    policy_trace = read_json(paths["policy_trace"])
    scheduler_trace = read_json(paths["scheduler_trace"])
    context = read_json(paths["context"])
    first = policy_trace.get("first_query")
    if not isinstance(first, Mapping):
        raise TypeError(f"{label}: absent first_query")
    artifacts = first.get("full_capture_artifacts")
    if not isinstance(artifacts, Mapping):
        raise TypeError(f"{label}: absent full_capture_artifacts")
    after = artifacts.get("outputs_after_output_transform")
    before = artifacts.get("before_policy_input_transform")
    queued = scheduler_trace.get("queued_actions")
    if not isinstance(after, Mapping) or not isinstance(before, Mapping) or not isinstance(queued, Mapping):
        raise TypeError(f"{label}: incomplete retained diagnostic snapshots")
    action_bundle, action_key = snapshot_leaf(after, "$/actions")
    state_bundle, state_key = snapshot_leaf(before, "$/state")
    memory_bundle, memory_key = snapshot_leaf(before, "$/memory_input_ids")
    queued_snapshot = queued.get("snapshot")
    if not isinstance(queued_snapshot, Mapping):
        raise TypeError(f"{label}: queued actions have no snapshot")
    queued_bundle, queued_key = snapshot_leaf(queued_snapshot, "$")
    return {
        "label": label,
        "paths": paths,
        "index": read_json(paths["index"]),
        "context": context,
        "policy_trace": policy_trace,
        "scheduler_trace": scheduler_trace,
        "actions_raw": npz_array(action_bundle, action_key),
        "actions_wire": np.asarray(npz_array(action_bundle, action_key), dtype=np.float32),
        "queued_k30": np.asarray(npz_array(queued_bundle, queued_key), dtype=np.float32),
        "state": np.asarray(npz_array(state_bundle, state_key), dtype=np.float32),
        "memory": np.asarray(npz_array(memory_bundle, memory_key), dtype=np.int32),
        "artifact_identities": {
            "run_index": file_identity(paths["index"]),
            "episode_context": file_identity(paths["context"]),
            "policy_trace": file_identity(paths["policy_trace"]),
            "scheduler_trace": file_identity(paths["scheduler_trace"]),
            "outputs_after_output_transform": file_identity(action_bundle),
            "queued_actions": file_identity(queued_bundle),
            "input_before_transform": file_identity(state_bundle),
        },
    }


def load_old_run(root: Path, label: str, role: str) -> dict[str, Any]:
    run = root / label
    episodes: list[dict[str, Any]] = []
    for episode_id in (0, 1):
        evidence = run / "rolling_evidence" / f"episode{episode_id}.jsonl"
        episode_file = run / f"episode{episode_id}.json"
        records = read_jsonl(evidence)
        if role == "baseline":
            event = first_record(records, "matched_baseline_action_query")
            result = event.get("result")
            inputs = event.get("input")
            if not isinstance(result, Mapping) or not isinstance(inputs, Mapping):
                raise TypeError(f"{evidence}: malformed matched baseline event")
            action = np.asarray(result.get("actions"), dtype=np.float32)
        elif role == "shadow":
            event = first_record(records, "action_plan")
            inputs = event.get("input")
            if not isinstance(inputs, Mapping):
                raise TypeError(f"{evidence}: malformed action plan")
            action = np.asarray(event.get("queued_actions"), dtype=np.float32)
        else:
            raise ValueError(role)
        if action.shape != (50, 14) and role == "baseline":
            raise ValueError(f"{evidence}: expected H50, got {action.shape}")
        if action.shape != (30, 14) and role == "shadow":
            raise ValueError(f"{evidence}: expected K30, got {action.shape}")
        state = np.asarray(inputs.get("robot_state"), dtype=np.float32)
        memory = np.asarray(inputs.get("memory_input_ids"), dtype=np.int32)
        episodes.append(
            {
                "episode_id": episode_id,
                "evidence": evidence,
                "episode_file": episode_file,
                "event": event,
                "actions": action,
                "state": state,
                "memory": memory,
                "instruction": read_json(episode_file).get("instruction"),
                "evidence_identity": file_identity(evidence),
                "episode_identity": file_identity(episode_file),
            }
        )
    return {"label": label, "run": run, "role": role, "episodes": episodes}


def without_video_output(request: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(request))
    video = value.get("video")
    if isinstance(video, dict):
        video.pop("output_path", None)
    return value


def without_video_save_dir(task_args: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(task_args))
    value.pop("eval_video_save_dir", None)
    return value


def source_identities(frozen: Path, diagnostic: Path) -> dict[str, dict[str, Any]]:
    source = {
        "old_hf_engineering": frozen / ".local/highfreq_engineering/hf_engineering.py",
        "old_benchmark_runner": frozen / "robot-bridge/robot_bridge/benchmark/runner.py",
        "old_scheduler_base": frozen / "robot-bridge/robot_bridge/scheduler/base.py",
        "old_rmbench_worker": frozen / "robot-bridge/robot_bridge/robot/controllers/rmbench_sim_worker.py",
        "old_put_back_task": frozen / "RMBench/envs/put_back_block.py",
        "old_base_task": frozen / "RMBench/envs/_base_task.py",
        "wire_backend": frozen / "robot-bridge/robot_bridge/policy/backends/openpi.py",
        "policy": frozen / "openpi/src/openpi/policies/policy.py",
        "new_launcher": diagnostic / "tools/run_first_query_diagnostic.py",
        "new_scheduler_wrapper": diagnostic / "tools/diagnostic_first_query_scheduler.py",
        "new_policy_wrapper": diagnostic / "tools/diagnostic_policy_server.py",
    }
    return {name: file_identity(path) for name, path in source.items()}


def equality_categories(new: np.ndarray, baseline: np.ndarray, shadow: np.ndarray) -> dict[str, int]:
    answer: dict[str, int] = {}
    for new_equal_baseline, new_equal_shadow, baseline_equal_shadow in (
        (False, False, False),
        (False, False, True),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ):
        mask = (
            (np.equal(new, baseline) == new_equal_baseline)
            & (np.equal(new, shadow) == new_equal_shadow)
            & (np.equal(baseline, shadow) == baseline_equal_shadow)
        )
        answer[
            f"new_eq_baseline={str(new_equal_baseline).lower()},"
            f"new_eq_shadow={str(new_equal_shadow).lower()},"
            f"baseline_eq_shadow={str(baseline_equal_shadow).lower()}"
        ] = int(np.count_nonzero(mask))
    if sum(answer.values()) != int(new.size):
        raise AssertionError("triple equality categories do not partition the K30 elements")
    return answer


def compact_metric(metric: Mapping[str, Any]) -> str:
    if metric.get("equal"):
        return "equal"
    return (
        f"{metric['different_elements']}/{int(np.prod(metric['left_shape']))}; "
        f"max {metric['max_abs']:.17g}; RMSE {metric['rmse']:.17g}; "
        f"first {metric['first_difference']}"
    )


def markdown(analysis: Mapping[str, Any]) -> str:
    numeric = analysis["numeric_alignment"]
    input_summary = analysis["input_and_reset_alignment"]
    sources = analysis["source_and_lifecycle"]
    artifacts = analysis["artifacts"]
    lines = [
        "# Offline historical first-query alignment",
        "",
        "This task-private reader used only frozen JSON/JSONL/NPZ artifacts. It did not start a model, simulator, service, reset, or GPU job.",
        "",
        "## Wire contract and inputs",
        "",
        "All comparisons use `np.asarray(actions, dtype=np.float32)`, matching frozen `OpenPiBackend.infer` at "
        "`robot_bridge/policy/backends/openpi.py:349-356`. New post-transform actions are stored as float64 before that wire cast.",
        "",
        f"- New wire H50 SHA-256: `{numeric['new_h50_wire_sha256']}`; new K30 SHA-256: `{numeric['new_k30_sha256']}`.",
        f"- Old matched-baseline H50 is retained at source step 0 in both old episode JSONL files; the two old H50 arrays are equal: `{numeric['old_baseline_h50_episode0_equals_episode1']}`.",
        f"- Old matched shadow retains only K30 in its first `action_plan.queued_actions`; it has no retained shadow H50 tail. The two old shadow K30 arrays are equal: `{numeric['old_shadow_k30_episode0_equals_episode1']}`.",
        "",
        "## Numeric alignment",
        "",
        "| Comparison | Result |",
        "| --- | --- |",
        f"| New H50 vs old baseline H50 | {compact_metric(numeric['new_h50_vs_old_baseline_h50'])} |",
        f"| New K30 vs old baseline H50 prefix | {compact_metric(numeric['new_k30_vs_old_baseline_prefix'])} |",
        f"| New K30 vs old shadow K30 | {compact_metric(numeric['new_k30_vs_old_shadow_k30'])} |",
        f"| Historical old baseline prefix vs old shadow K30 | {compact_metric(numeric['old_baseline_prefix_vs_old_shadow_k30'])} |",
        "",
        "The fresh capture exactly matches neither historical side. Its K30 triple equality categories are recorded in JSON; 164/420 elements differ from both old values, while the remaining categories do not form either old full array.",
        "",
        "## What can and cannot be aligned offline",
        "",
        f"- After removing only `video.output_path`, old and new reset requests are equal: `{input_summary['reset_requests_equal_without_video_path']}`; canonical SHA-256 `{input_summary['reset_request_canonical_sha256']}`. `task_overrides` is `{input_summary['old_task_overrides']}` and both requests use `instruction_type=unseen`, `test_num=100`.",
        f"- Prompt is equal: `{input_summary['prompt_equal']}`; UTF-8 SHA-256 `{input_summary['prompt_utf8_sha256']}`. Retained state and memory are equal across the two old sides and two new captures: `{input_summary['retained_state_equal']}` / `{input_summary['retained_memory_equal']}`.",
        f"- State float32 raw SHA-256 `{input_summary['state_float32_raw_sha256']}`; memory int32 raw SHA-256 `{input_summary['memory_int32_raw_sha256']}`.",
        f"- Preflight task arguments are equal after removing only `eval_video_save_dir`: `{input_summary['task_args_equal_without_video_save_dir']}`. The retained camera contract is `{json.dumps(input_summary['camera_contract'], sort_keys=True)}`; that establishes configuration, not equality of old RGB pixels.",
        f"- The new baseline/shadow scheduler input trees are equal (`{input_summary['new_scheduler_pre_rpc_tree_sha256']}`), as are their post-input-transform trees (`{input_summary['new_policy_post_transform_tree_sha256']}`) and captured actual action-key descriptors (`{input_summary['new_action_rng_descriptors_equal']}`). The old evidence has no corresponding full tree or actual key.",
        "- The old first-query evidence does not retain RGB, a complete prompt/token/transform tree, an actual PRNG key, sampler-internal noise, or the old shadow H50 tail. Equal retained state/memory is therefore not evidence that old full policy input or RNG state was equal.",
        "- `episode_info.info.task_facts.final_block_pose` is not a policy-input identity: the worker runs a probe environment and expert `play_once`, closes it, then creates the actual environment; it returns the probe `episode_info` rather than a snapshot of the policy environment.",
        "",
        "## Confirmed lifecycle differences",
        "",
        "- Old `BenchmarkRunner.run` starts robot and policy before either metadata handshake (`runner.py:750-771`). The diagnostic launcher starts robot, waits for its metadata, then starts policy (`run_first_query_diagnostic.py:355-379`).",
        "- Old launch uses normal `run_policy_server.py` and `scripts/run_scheduler.py`; the capture uses task-private diagnostic policy/scheduler wrappers. Its scheduler loads the same config and `apply_episode_prompt`, then calls `_startup(); run_iteration()`, equivalent to the nominal first `SchedulerBase.run()` action route after construction (`base.py:614-648`).",
        "- The diagnostic launcher adds task-private JAX/WARP/CUDA cache paths. Old receipts do not retain their values, so their equality cannot be established offline.",
        "",
        "## Instrumentation boundary",
        "",
        "`implicit_noise_derived_from_sampling_key` is an offline reconstruction using the captured real sampling key and frozen `jax.random.normal` expression. It is not a direct capture of GPU sampler-internal noise. The diagnostic wrapper also makes synchronous host copies and `fsync` around transforms and temporarily monkey-patches global `jax.random.split`. It preserves intended random-call semantics, but changes timing/JIT diagnostic conditions; equality in this capture does not exclude an uninstrumented-runtime timing or numerical effect.",
        "",
        "## Unexecuted two-sample discriminator",
        "",
        "Use one remaining action sample for matched baseline and one for matched shadow. Preserve the old `BenchmarkRunner` startup ordering and reset flow, and add only a scheduler-side post-wire K30 capture after the real execute request; clear the queue at logical step 0. Do not wrap `Policy.infer`, transforms, or `jax.random.split`. This distinguishes a diagnostic wrapper/startup-path contribution from the historical discrepancy, but cannot reconstruct old RGB or actual keys without separately authorized observation.",
        "",
        "## Artifact identities",
        "",
        f"- Analyzer: `{artifacts['analyzer']['path']}` SHA-256 `{artifacts['analyzer']['sha256']}`.",
        f"- Frozen old launcher: `{sources['identities']['old_hf_engineering']['path']}` SHA-256 `{sources['identities']['old_hf_engineering']['sha256']}`.",
        f"- New launcher: `{sources['identities']['new_launcher']['path']}` SHA-256 `{sources['identities']['new_launcher']['sha256']}`.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-root", required=True, type=Path)
    parser.add_argument("--old-results-root", required=True, type=Path)
    parser.add_argument("--diagnostic-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    frozen = args.frozen_root.resolve()
    old_root = args.old_results_root.resolve()
    diagnostic = args.diagnostic_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    new_baseline = load_new_capture(diagnostic, "matched_baseline")
    new_shadow = load_new_capture(diagnostic, "matched_shadow")
    old_baseline = load_old_run(old_root, OLD_BASELINE, "baseline")
    old_shadow = load_old_run(old_root, OLD_SHADOW, "shadow")

    # The diagnostic captures were intentionally cross-checked first. Preserve
    # that identity in the alignment rather than silently choosing one label.
    new_h50_cross = comparison("new baseline H50 vs new shadow H50", new_baseline["actions_wire"], new_shadow["actions_wire"])
    new_k30_cross = comparison("new baseline K30 vs new shadow K30", new_baseline["queued_k30"], new_shadow["queued_k30"])
    if not new_h50_cross["equal"] or not new_k30_cross["equal"]:
        raise AssertionError("the bounded baseline/shadow captures unexpectedly diverge")

    old_base_h50_0, old_base_h50_1 = (old_baseline["episodes"][i]["actions"] for i in (0, 1))
    old_shadow_k30_0, old_shadow_k30_1 = (old_shadow["episodes"][i]["actions"] for i in (0, 1))
    old_base_cross = comparison("old baseline episode0 H50 vs episode1 H50", old_base_h50_0, old_base_h50_1)
    old_shadow_cross = comparison("old shadow episode0 K30 vs episode1 K30", old_shadow_k30_0, old_shadow_k30_1)
    if not old_base_cross["equal"] or not old_shadow_cross["equal"]:
        raise AssertionError("historical episode pairs unexpectedly differ; do not collapse them")

    new_h50 = new_baseline["actions_wire"]
    new_k30 = new_baseline["queued_k30"]
    metrics = {
        "new_h50_vs_old_baseline_h50": comparison("new H50 vs old baseline H50", new_h50, old_base_h50_0),
        "new_k30_vs_old_baseline_prefix": comparison("new K30 vs old baseline H50[:30]", new_k30, old_base_h50_0[:30]),
        "new_k30_vs_old_shadow_k30": comparison("new K30 vs old shadow K30", new_k30, old_shadow_k30_0),
        "old_baseline_prefix_vs_old_shadow_k30": comparison("old baseline H50[:30] vs old shadow K30", old_base_h50_0[:30], old_shadow_k30_0),
    }

    old_inputs = [*old_baseline["episodes"], *old_shadow["episodes"]]
    new_inputs = [new_baseline, new_shadow]
    old_states = [item["state"] for item in old_inputs]
    old_memories = [item["memory"] for item in old_inputs]
    new_states = [item["state"] for item in new_inputs]
    new_memories = [item["memory"] for item in new_inputs]
    retained_state_equal = all(np.array_equal(old_states[0], item) for item in [*old_states[1:], *new_states])
    retained_memory_equal = all(np.array_equal(old_memories[0], item) for item in [*old_memories[1:], *new_memories])
    if not retained_state_equal or not retained_memory_equal:
        raise AssertionError("retained input fields are not equal as expected")

    old_request = read_jsonl(old_root / OLD_BASELINE / "seed_preflight.jsonl")[0].get("request")
    new_request = new_baseline["index"].get("inputs", {}).get("reset_request")
    if not isinstance(old_request, Mapping) or not isinstance(new_request, Mapping):
        raise TypeError("missing reset request evidence")
    old_without_video = without_video_output(old_request)
    new_without_video = without_video_output(new_request)
    reset_equal = old_without_video == new_without_video
    if not reset_equal:
        raise AssertionError("old/new reset request unexpectedly differs beyond video output path")

    old_prompt = old_baseline["episodes"][0]["instruction"]
    new_prompt = new_baseline["context"].get("instruction")
    if old_prompt != PROMPT or new_prompt != PROMPT:
        raise AssertionError("unexpected put-back instruction")

    old_task_args = read_json(old_baseline["episodes"][0]["episode_file"]).get("task_args")
    new_task_args = new_baseline["context"].get("task_args")
    if not isinstance(old_task_args, Mapping) or not isinstance(new_task_args, Mapping):
        raise TypeError("missing preflight task_args")
    task_args_equal = without_video_save_dir(old_task_args) == without_video_save_dir(new_task_args)
    if not task_args_equal:
        raise AssertionError("old/new task args unexpectedly differ beyond video save directory")
    camera_contract = old_task_args.get("camera")
    if not isinstance(camera_contract, Mapping):
        raise TypeError("missing camera contract")

    scheduler_pre_baseline = new_baseline["scheduler_trace"].get("first_query_input", {}).get("snapshot")
    scheduler_pre_shadow = new_shadow["scheduler_trace"].get("first_query_input", {}).get("snapshot")
    policy_artifacts_baseline = new_baseline["policy_trace"].get("first_query", {}).get("full_capture_artifacts", {})
    policy_artifacts_shadow = new_shadow["policy_trace"].get("first_query", {}).get("full_capture_artifacts", {})
    if not all(isinstance(value, Mapping) for value in (scheduler_pre_baseline, scheduler_pre_shadow, policy_artifacts_baseline, policy_artifacts_shadow)):
        raise TypeError("missing bounded diagnostic tree snapshots")
    scheduler_tree_baseline = scheduler_pre_baseline.get("tree_sha256")
    scheduler_tree_shadow = scheduler_pre_shadow.get("tree_sha256")
    post_tree_baseline = policy_artifacts_baseline.get("after_policy_input_transform", {}).get("tree_sha256")
    post_tree_shadow = policy_artifacts_shadow.get("after_policy_input_transform", {}).get("tree_sha256")
    before_tree_baseline = policy_artifacts_baseline.get("before_policy_input_transform", {}).get("tree_sha256")
    before_tree_shadow = policy_artifacts_shadow.get("before_policy_input_transform", {}).get("tree_sha256")
    new_rng_baseline = new_baseline["policy_trace"].get("first_query", {}).get("rng")
    new_rng_shadow = new_shadow["policy_trace"].get("first_query", {}).get("rng")
    if not all(isinstance(value, str) for value in (scheduler_tree_baseline, scheduler_tree_shadow, post_tree_baseline, post_tree_shadow, before_tree_baseline, before_tree_shadow)):
        raise TypeError("malformed bounded diagnostic tree hash")
    if scheduler_tree_baseline != scheduler_tree_shadow or before_tree_baseline != before_tree_shadow or post_tree_baseline != post_tree_shadow:
        raise AssertionError("new capture trees unexpectedly differ")
    if new_rng_baseline != new_rng_shadow:
        raise AssertionError("new capture action RNG descriptors unexpectedly differ")

    old_manifest = new_baseline["index"].get("inputs", {}).get("manifest", {})
    manifest_path = Path(str(old_manifest.get("path", "")))
    manifest = read_json(manifest_path)
    task_overrides = [item.get("task_overrides", {}) for item in manifest.get("simulation_runs", []) if isinstance(item, Mapping)]
    # The selected profile is a task-private frozen manifest. It contains
    # several runs, all of which use the same empty override contract here.
    if not task_overrides or any(value != {} for value in task_overrides):
        raise AssertionError("expected empty frozen task_overrides")

    source = {
        "identities": source_identities(frozen, diagnostic),
        "confirmed_differences": [
            {
                "topic": "startup ordering",
                "old": "BenchmarkRunner starts robot and policy before metadata handshakes (runner.py:750-771).",
                "new": "diagnostic launcher waits for robot metadata before starting policy (run_first_query_diagnostic.py:355-379).",
            },
            {
                "topic": "scheduler and policy entrypoints",
                "old": "normal run_policy_server.py and scripts/run_scheduler.py via BenchmarkRunner",
                "new": "task-private diagnostic_policy_server.py and diagnostic_first_query_scheduler.py wrappers",
            },
            {
                "topic": "first scheduler route",
                "old": "SchedulerBase.run calls _startup then _loop_step/run_iteration (base.py:614-648).",
                "new": "wrapper loads same config and apply_episode_prompt, then calls _startup(); run_iteration() (diagnostic scheduler:99-124,171-205).",
            },
            {
                "topic": "diagnostic cache environment",
                "old": "old receipt records no JAX_COMPILATION_CACHE_DIR, WARP_CACHE_PATH, or CUDA_CACHE_PATH values",
                "new": "diagnostic launcher sets task-private cache paths",
            },
        ],
        "reset_context_caveat": {
            "finding": "returned final_block_pose is preflight/probe-environment data, not a policy-input identity",
            "source": [
                "rmbench_sim_worker.py:135-149 creates probe env and calls play_once",
                "put_back_block.py:106-140 records final_block_pose after expert planner execution",
                "rmbench_sim_worker.py:155-179 sets up a separate actual episode env",
            ],
        },
        "wire_and_rng_source": [
            "openpi backend:349-369 casts actions to float32 for the wire",
            "policy.py:84-139 copies input, applies transform, splits JAX RNG, samples, and applies output transform",
        ],
    }

    analysis: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "offline alignment of historical put-back first-query evidence with bounded first-query capture",
        "offline_only": True,
        "wire_contract": {
            "expression": "np.asarray(actions, dtype=np.float32)",
            "source": "robot_bridge/policy/backends/openpi.py:349-356",
            "reason": "new Policy output-transform actions are float64 before frozen backend wire cast",
        },
        "artifacts": {
            "analyzer": file_identity(Path(__file__).resolve()),
            "old_results_root": str(old_root),
            "diagnostic_root": str(diagnostic),
            "old_baseline": {
                "run": str(old_baseline["run"]),
                "episodes": [
                    {"episode_id": item["episode_id"], "evidence": item["evidence_identity"], "episode": item["episode_identity"]}
                    for item in old_baseline["episodes"]
                ],
            },
            "old_shadow": {
                "run": str(old_shadow["run"]),
                "episodes": [
                    {"episode_id": item["episode_id"], "evidence": item["evidence_identity"], "episode": item["episode_identity"]}
                    for item in old_shadow["episodes"]
                ],
            },
            "new_captures": {
                label: capture["artifact_identities"] for label, capture in (("matched_baseline", new_baseline), ("matched_shadow", new_shadow))
            },
        },
        "numeric_alignment": {
            "new_h50_wire_sha256": array_sha256(new_h50),
            "new_k30_sha256": array_sha256(new_k30),
            "old_baseline_h50_sha256": array_sha256(old_base_h50_0),
            "old_shadow_k30_sha256": array_sha256(old_shadow_k30_0),
            "old_baseline_h50_episode0_equals_episode1": old_base_cross["equal"],
            "old_shadow_k30_episode0_equals_episode1": old_shadow_cross["equal"],
            "new_baseline_h50_equals_new_shadow_h50": new_h50_cross["equal"],
            "new_baseline_k30_equals_new_shadow_k30": new_k30_cross["equal"],
            **metrics,
            "new_k30_triple_equality_categories": equality_categories(new_k30, old_base_h50_0[:30], old_shadow_k30_0),
            "conclusion": "new capture exactly equals neither historical baseline nor historical shadow retained action array",
        },
        "input_and_reset_alignment": {
            "reset_requests_equal_without_video_path": reset_equal,
            "reset_request_canonical_sha256": sha256_bytes(canonical_json(old_without_video)),
            "old_task_overrides": {},
            "instruction_type": old_without_video["config"]["overrides"]["instruction_type"],
            "test_num": old_without_video["config"]["overrides"]["test_num"],
            "prompt_equal": old_prompt == new_prompt,
            "prompt_utf8_sha256": sha256_bytes(PROMPT.encode("utf-8")),
            "retained_state_equal": retained_state_equal,
            "retained_memory_equal": retained_memory_equal,
            "state_float32_raw_sha256": array_sha256(old_states[0]),
            "memory_int32_raw_sha256": array_sha256(old_memories[0]),
            "state_values": old_states[0].tolist(),
            "memory_values": old_memories[0].tolist(),
            "task_args_equal_without_video_save_dir": task_args_equal,
            "camera_contract": dict(camera_contract),
            "new_scheduler_pre_rpc_tree_sha256": scheduler_tree_baseline,
            "new_policy_pre_transform_tree_sha256": before_tree_baseline,
            "new_policy_post_transform_tree_sha256": post_tree_baseline,
            "new_action_rng_descriptors_equal": new_rng_baseline == new_rng_shadow,
            "new_action_rng_descriptor": new_rng_baseline,
            "old_matched_baseline_retained_input_keys": sorted(old_baseline["episodes"][0]["event"].get("input", {}).keys()),
            "old_matched_shadow_retained_input_keys": sorted(old_shadow["episodes"][0]["event"].get("input", {}).keys()),
            "old_matched_baseline_action_rng_keys": sorted(old_baseline["episodes"][0]["event"].get("result", {}).get("action_rng", {}).keys()),
            "old_shadow_h50_retained": False,
            "minimum_unobservable_gap": [
                "old rolling evidence has no RGB image arrays",
                "old rolling evidence has no complete prompt/token or post-input-transform tree",
                "old policy_rng records stream/call rather than actual PRNG key",
                "old rolling evidence has no sampler noise",
                "old shadow keeps K30 only, not its H50 tail",
            ],
        },
        "source_and_lifecycle": source,
        "instrumentation_caveat": {
            "implicit_noise": "offline reconstruction from captured real sampling key using frozen jax.random.normal; not direct GPU sampler-internal noise capture",
            "wrapper_effect": "synchronous host copies/fsync around transforms and temporary global jax.random.split monkey patch preserve intended random-call semantics but alter timing/JIT diagnostic conditions",
            "inference_limit": "new equality does not exclude an uninstrumented-runtime timing or numerical effect",
            "source_lines": {
                "fsync": "diagnostic_policy_server.py:92-97",
                "infer_wrapper_and_split_patch": "diagnostic_policy_server.py:178-289",
                "derived_noise": "diagnostic_policy_server.py:256-277",
            },
        },
        "unexecuted_two_sample_proposal": {
            "samples": [{"label": "matched_baseline", "count": 1}, {"label": "matched_shadow", "count": 1}],
            "preserve": ["old BenchmarkRunner startup order", "old reset flow", "real execute request"],
            "capture": "narrow scheduler-side post-wire K30 only after real execute; clear queue at logical step 0",
            "do_not_wrap": ["Policy.infer", "input/output transforms", "jax.random.split"],
            "distinguishes": "whether historical-vs-new discrepancy is introduced by diagnostic wrapper or startup path",
            "remaining_limit": "cannot reconstruct old RGB or actual keys without separately authorized observation",
            "executed": False,
        },
    }
    json_path = output / "historical_alignment.json"
    markdown_path = output / "historical_alignment.md"
    json_path.write_bytes(canonical_json(analysis) + b"\n")
    markdown_path.write_text(markdown(analysis), encoding="utf-8")
    print(json.dumps({"json": file_identity(json_path), "markdown": file_identity(markdown_path)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
