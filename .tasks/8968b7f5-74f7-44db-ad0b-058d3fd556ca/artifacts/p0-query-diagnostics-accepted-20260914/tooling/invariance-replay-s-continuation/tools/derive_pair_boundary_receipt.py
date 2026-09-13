#!/usr/bin/env python3
"""Derive an immutable boundary-analysis receipt from an existing J pair."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite derived receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def identity(value: Any) -> dict[str, Any]:
    array = np.asarray(value)
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(b"\0")
    digest.update(repr(tuple(array.shape)).encode("ascii"))
    digest.update(b"\0")
    digest.update(np.ascontiguousarray(array).tobytes())
    return {
        "dtype": array.dtype.str,
        "shape": list(array.shape),
        "sha256": digest.hexdigest(),
        "nonfinite": bool(np.issubdtype(array.dtype, np.inexact) and not np.isfinite(array).all()),
    }


def same_value(left: Any, right: Any, path: str) -> str | None:
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        a, b = np.asarray(left), np.asarray(right)
        if a.dtype != b.dtype or a.shape != b.shape:
            return f"{path}: dtype/shape {a.dtype}/{a.shape} != {b.dtype}/{b.shape}"
        if not np.array_equal(a, b, equal_nan=True):
            return f"{path}: array values differ"
        return None
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left) != set(right):
            return f"{path}: keys differ"
        for key in sorted(left, key=str):
            mismatch = same_value(left[key], right[key], f"{path}.{key}")
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return f"{path}: list length differs"
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            mismatch = same_value(a, b, f"{path}[{index}]")
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(left, tuple) and isinstance(right, tuple):
        return same_value(list(left), list(right), path)
    if isinstance(left, float) and isinstance(right, float) and np.isnan(left) and np.isnan(right):
        return None
    return None if left == right else f"{path}: {left!r} != {right!r}"


def materialize(value: Any, arrays: Mapping[str, np.ndarray]) -> Any:
    if isinstance(value, Mapping):
        if set(value) == {"array_ref"} and isinstance(value["array_ref"], Mapping):
            key = value["array_ref"].get("key")
            if not isinstance(key, str) or key not in arrays:
                raise ValueError(f"missing array bundle key {key!r}")
            return np.array(arrays[key], copy=True)
        if set(value) == {"bytes_ref"}:
            raw = materialize(value["bytes_ref"], arrays)
            return np.asarray(raw, dtype=np.uint8).tobytes()
        return {str(key): materialize(item, arrays) for key, item in value.items()}
    if isinstance(value, list):
        return [materialize(item, arrays) for item in value]
    return value


def load_record(path: Path) -> tuple[dict[str, Any], dict[str, np.ndarray], Path]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "recorded":
        raise ValueError(f"derivation requires a recorded diagnostic, got {data.get('status')!r}")
    bundle = data.get("array_bundle")
    if not isinstance(bundle, Mapping) or not isinstance(bundle.get("file"), str):
        raise ValueError("record lacks an array bundle")
    array_path = path.parent.parent / bundle["file"]
    with np.load(array_path, allow_pickle=False) as loaded:
        arrays = {name: np.array(loaded[name], copy=True) for name in loaded.files}
    return data, arrays, array_path


def comparison(left: Any, right: Any, path: str) -> dict[str, Any]:
    difference = same_value(left, right, path)
    return {"equal": difference is None, "difference": difference}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-receipt", required=True, type=Path)
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--backend-source", required=True, type=Path)
    parser.add_argument("--task-revision", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "query_diagnostic_pair_boundary_derivation",
        "status": "failed",
        "passed": False,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    try:
        pair_path = args.pair_receipt.resolve(strict=True)
        record_path = args.record.resolve(strict=True)
        backend_source = args.backend_source.resolve(strict=True)
        pair = json.loads(pair_path.read_text(encoding="utf-8"))
        data, arrays, array_path = load_record(record_path)
        policy = materialize(data.get("policy"), arrays)
        scheduler = materialize(data.get("scheduler"), arrays)
        if not isinstance(policy, Mapping) or not isinstance(scheduler, Mapping):
            raise ValueError("record has no policy/scheduler mapping")
        outputs = policy.get("outputs")
        if not isinstance(outputs, Mapping):
            raise ValueError("record has no policy outputs")
        after_transform = outputs.get("after_output_transform")
        if not isinstance(after_transform, Mapping) or "actions" not in after_transform:
            raise ValueError("record has no policy after_output_transform.actions")
        action_dispatch = scheduler.get("action_dispatch")
        if not isinstance(action_dispatch, Mapping):
            raise ValueError("record has no action dispatch")
        post_wire = action_dispatch.get("policy_actions_after_output_transform")
        execute_request = action_dispatch.get("execute_request")
        execute_actions = execute_request.get("actions") if isinstance(execute_request, Mapping) else None
        execute = execute_actions.get("arms") if isinstance(execute_actions, Mapping) else None
        saved_policy_actions = np.asarray(after_transform["actions"])
        backend_actions = np.asarray(saved_policy_actions, dtype=np.float32)
        post_wire_array = np.asarray(post_wire)
        execute_array = np.asarray(execute)
        h50 = comparison(backend_actions, post_wire_array, "scheduler.action_dispatch.policy_actions_after_output_transform")
        k30 = comparison(backend_actions[:30], execute_array, "scheduler.action_dispatch.execute_request.actions.arms")
        if saved_policy_actions.shape != (50, 14):
            raise ValueError(f"expected saved policy H50 actions, got {saved_policy_actions.shape}")
        if post_wire_array.shape != (50, 14) or execute_array.shape != (30, 14):
            raise ValueError("record does not contain the frozen H50/K30 action layout")
        source_text = backend_source.read_text(encoding="utf-8")
        cast_statement = 'output["actions"] = np.asarray(result["actions"], dtype=np.float32)'
        if cast_statement not in source_text:
            raise ValueError("frozen OpenPiBackend actions-boundary cast was not found")
        original_comparisons = pair.get("comparisons")
        if not isinstance(original_comparisons, Mapping):
            raise ValueError("old pair receipt has no comparisons mapping")
        required_invariance = (
            "logging_off_vs_logging_on",
            "logging_off_final_rng_vs_logging_on",
            "logging_on_sidecar_input_vs_saved_pre_transport_input",
            "logging_on_sidecar_rng_before_vs_saved",
            "logging_on_sidecar_rng_after_vs_saved",
            "logging_on_final_rng_vs_saved",
            "logging_off_final_rng_vs_saved",
        )
        missing = [key for key in required_invariance if key not in original_comparisons]
        if missing:
            raise ValueError(f"old pair receipt is missing invariance checks: {missing}")
        invariant_checks = {key: original_comparisons[key] for key in required_invariance}
        invariance_passed = all(
            isinstance(value, Mapping) and value.get("equal") is True for value in invariant_checks.values()
        )
        ordinary = pair.get("ordinary_output")
        if not isinstance(ordinary, Mapping) or not isinstance(ordinary.get("actions"), Mapping):
            raise ValueError("old pair receipt lacks ordinary actions identity")
        replay_action = ordinary["actions"]
        replay_equal = replay_action == identity(backend_actions)
        legacy = {
            "receipt": ref(pair_path),
            "status": pair.get("status"),
            "passed": pair.get("passed"),
            "started_at": pair.get("started_at"),
            "finished_at": pair.get("finished_at"),
            "script": pair.get("script"),
            "record": pair.get("record"),
            "rng": pair.get("rng"),
            "ordinary_output": ordinary,
            "comparisons": original_comparisons,
            "error": pair.get("error"),
        }
        receipt.update({
            "status": "passed" if invariance_passed and replay_equal else "failed",
            "passed": invariance_passed and replay_equal,
            "manager_task_revision": args.task_revision,
            "legacy_pair": legacy,
            "record": {"json": ref(record_path), "array_bundle": ref(array_path)},
            "backend_actions_boundary": {
                "source": ref(backend_source),
                "statement": cast_statement,
                "policy_after_output_transform_actions": identity(saved_policy_actions),
                "policy_to_backend_actions": {
                    "operation": "np.asarray(policy_after_output_transform.actions, dtype=np.float32)",
                    "identity": identity(backend_actions),
                },
                "post_wire_h50": {"identity": identity(post_wire_array), "comparison": h50},
                "execute_k30": {"identity": identity(execute_array), "comparison": k30},
            },
            "logging_invariance": {
                "passed": invariance_passed,
                "scope": "The original pair loaded one backend and invoked it twice from the same restored starting key; it compares ordinary output strictly while excluding timing and the diagnostic sidecar, plus final key and sidecar input/key alignment.",
                "ordinary_output_fields": ordinary.get("keys"),
                "comparisons": invariant_checks,
            },
            "cross_process_saved_replay": {
                "passed": replay_equal,
                "scope": "Saved policy after_output_transform.actions are compared at the frozen OpenPiBackend output boundary after only the explicit float32 actions conversion. This is an additional replay check, not evidence that logging changed the same-process invocation.",
                "expected_backend_actions": identity(backend_actions),
                "observed_ordinary_actions": replay_action,
                "comparison": {
                    "equal": replay_equal,
                    "difference": None if replay_equal else "saved policy actions after the frozen backend float32 conversion have a different identity from the persisted direct pair ordinary actions",
                },
                "unavailable": [
                    "The old pair receipt persisted only action identity, not the direct off/on ordinary arrays; max_abs and RMSE cannot be reconstructed offline.",
                    "The old recursive saved-output comparison stopped at the actions dtype mismatch, so later saved-output fields were not evaluated and are unavailable rather than passed.",
                ],
            },
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        })
        atomic_json(args.output, receipt)
        print(json.dumps({"passed": receipt["passed"], "output": str(args.output)}, sort_keys=True))
        return 0
    except BaseException as exc:
        receipt.update({
            "status": "failed",
            "passed": False,
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
        })
        try:
            atomic_json(args.output, receipt)
        except BaseException:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
