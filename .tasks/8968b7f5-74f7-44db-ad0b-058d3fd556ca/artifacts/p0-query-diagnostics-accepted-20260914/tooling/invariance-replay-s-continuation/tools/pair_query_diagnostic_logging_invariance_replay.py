#!/usr/bin/env python3
"""Run one strict same-process logging pair and a separate saved-replay check.

The pair always uses one OpenPiBackend instance and restores the recorded key
before each direct inference.  Logging invariance compares the two ordinary
outputs, excluding only timing and the diagnostic sidecar.  Saved replay is a
separate check: only saved policy actions cross the frozen backend's explicit
float32 actions boundary; no other field is cast or compared approximately.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import numpy as np


SCRIPT_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_TIMING_KEYS = {"policy_timing"}
_DEFAULT_MAX_ORDINARY_ARRAY_BYTES = 8 * 1024 * 1024


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ref(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite pair receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(encoded)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _array_identity(value: Any) -> dict[str, Any]:
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


def _same_value(left: Any, right: Any, path: str = "output") -> str | None:
    """Require identical dtype, shape and values; never perform an approximate compare."""
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
            mismatch = _same_value(left[key], right[key], f"{path}.{key}")
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return f"{path}: list length differs"
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            mismatch = _same_value(a, b, f"{path}[{index}]")
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(left, tuple) and isinstance(right, tuple):
        return _same_value(list(left), list(right), path)
    if isinstance(left, float) and isinstance(right, float) and np.isnan(left) and np.isnan(right):
        return None
    return None if left == right else f"{path}: {left!r} != {right!r}"


def _comparison(left: Any, right: Any, path: str) -> dict[str, Any]:
    difference = _same_value(left, right, path)
    return {"equal": difference is None, "difference": difference}


def _field_comparisons(left: Any, right: Any, path: str) -> dict[str, dict[str, Any]]:
    """Compare every ordinary top-level field so an actions failure cannot hide another one."""
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return {"__root__": _comparison(left, right, path)}
    results: dict[str, dict[str, Any]] = {}
    for key in sorted(set(left) | set(right), key=str):
        child = f"{path}.{key}"
        if key not in left:
            results[str(key)] = {"equal": False, "difference": f"{child}: missing from actual output"}
        elif key not in right:
            results[str(key)] = {"equal": False, "difference": f"{child}: missing from saved output"}
        else:
            results[str(key)] = _comparison(left[key], right[key], child)
    return results


def _all_equal(comparisons: Mapping[str, Mapping[str, Any]]) -> bool:
    return all(item.get("equal") is True for item in comparisons.values())


def _ordinary_output(value: Mapping[str, Any], output_key: str) -> dict[str, Any]:
    return {
        str(key): item
        for key, item in value.items()
        if key not in _TIMING_KEYS and key != output_key
    }


def _materialize(value: Any, arrays: Mapping[str, np.ndarray]) -> Any:
    if isinstance(value, Mapping):
        if set(value) == {"array_ref"} and isinstance(value["array_ref"], Mapping):
            key = value["array_ref"].get("key")
            if not isinstance(key, str) or key not in arrays:
                raise ValueError(f"array descriptor references unavailable key {key!r}")
            return np.array(arrays[key], copy=True)
        if set(value) == {"bytes_ref"}:
            raw = _materialize(value["bytes_ref"], arrays)
            return np.asarray(raw, dtype=np.uint8).tobytes()
        return {str(key): _materialize(item, arrays) for key, item in value.items()}
    if isinstance(value, list):
        return [_materialize(item, arrays) for item in value]
    return value


def _strict_record(path: Path, validate_record: Any) -> tuple[dict[str, Any], dict[str, np.ndarray], Path]:
    validated = validate_record(path)
    if validated.get("status") != "recorded":
        raise ValueError(f"pairing requires a recorded diagnostic, got {validated.get('status')!r}")
    data = json.loads(path.read_text(encoding="utf-8"))
    bundle = data.get("array_bundle")
    if not isinstance(bundle, Mapping) or not isinstance(bundle.get("file"), str):
        raise ValueError("recorded diagnostic has no usable array bundle")
    array_path = path.parent.parent / bundle["file"]
    with np.load(array_path, allow_pickle=False) as loaded:
        arrays = {name: np.array(loaded[name], copy=True) for name in loaded.files}
    return data, arrays, array_path


def _restore_key(rng: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
    import jax

    algorithm = rng.get("algorithm")
    key_data = rng.get("key_data")
    if not isinstance(algorithm, str) or not algorithm or algorithm == "jax_key_data_unavailable":
        raise ValueError(f"unsupported recorded JAX key algorithm {algorithm!r}")
    if not isinstance(key_data, np.ndarray):
        raise TypeError("recorded rng key_data was not materialized as an ndarray")
    key = jax.random.wrap_key_data(np.array(key_data, copy=True), impl=algorithm)
    if not np.array_equal(jax.random.key_data(key), key_data):
        raise ValueError("restored JAX key does not reproduce recorded key_data")
    return key, {"algorithm": algorithm, "key_data": _array_identity(key_data)}


def _rng_identity(policy: Any) -> dict[str, Any]:
    import jax

    key = policy._rng
    data = np.asarray(jax.random.key_data(key))
    return {"algorithm": str(jax.random.key_impl(key)), "key_data": _array_identity(data)}


def _value_identity(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return {"kind": "array", **_array_identity(value)}
    if isinstance(value, Mapping):
        return {"kind": "mapping", "items": {str(key): _value_identity(item) for key, item in value.items()}}
    if isinstance(value, list):
        return {"kind": "list", "items": [_value_identity(item) for item in value]}
    if isinstance(value, tuple):
        return {"kind": "tuple", "items": [_value_identity(item) for item in value]}
    encoded = repr(value).encode("utf-8")
    return {"kind": "scalar", "type": type(value).__name__, "sha256": hashlib.sha256(encoded).hexdigest()}


def _collect_arrays(value: Any, path: str, collected: dict[str, np.ndarray], metadata: dict[str, Any]) -> None:
    if isinstance(value, np.ndarray):
        key = f"array_{len(collected):03d}"
        array = np.ascontiguousarray(value)
        collected[key] = array
        metadata[key] = {"field": path, **_array_identity(array), "nbytes": int(array.nbytes)}
        return
    if isinstance(value, Mapping):
        for name, item in value.items():
            _collect_arrays(item, f"{path}.{name}", collected, metadata)
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for index, item in enumerate(value):
            _collect_arrays(item, f"{path}[{index}]", collected, metadata)


def _write_ordinary_bundle(path: Path, logging_off: Mapping[str, Any], logging_on: Mapping[str, Any], max_bytes: int) -> dict[str, Any]:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite ordinary-output bundle: {path}")
    arrays: dict[str, np.ndarray] = {}
    metadata: dict[str, Any] = {}
    _collect_arrays(logging_off, "logging_off", arrays, metadata)
    _collect_arrays(logging_on, "logging_on", arrays, metadata)
    total = sum(int(array.nbytes) for array in arrays.values())
    if total > max_bytes:
        raise ValueError(f"ordinary output arrays total {total} bytes exceeds cap {max_bytes}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".npz", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        np.savez_compressed(temporary, **arrays)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"bundle": _ref(path), "uncompressed_array_bytes": total, "arrays": metadata}


def _run(args: argparse.Namespace) -> dict[str, Any]:
    import jax
    from robot_bridge.policy.backends.openpi import OpenPiBackend
    from robot_bridge.scheduler.query_diagnostic import CONTEXT_KEY, OUTPUT_KEY, validate_record

    record_path = args.record.resolve(strict=True)
    checkpoint = args.checkpoint.resolve(strict=True)
    data, arrays, array_path = _strict_record(record_path, validate_record)
    policy_data = data.get("policy")
    scheduler = data.get("scheduler")
    query = data.get("query")
    if not isinstance(policy_data, Mapping) or not isinstance(scheduler, Mapping) or not isinstance(query, Mapping):
        raise ValueError("record has no complete policy, scheduler, or query partition")
    input_before_transport = _materialize(scheduler.get("input_before_policy_transport"), arrays)
    if not isinstance(input_before_transport, Mapping):
        raise ValueError("saved input_before_policy_transport is not a mapping")
    if CONTEXT_KEY in input_before_transport:
        raise ValueError("saved pre-transport input unexpectedly already contains diagnostic context")
    rng = _materialize(policy_data.get("rng"), arrays)
    if not isinstance(rng, Mapping) or not isinstance(rng.get("state_before_split"), Mapping):
        raise ValueError("record has no materialized state_before_split")
    before_key, before_identity = _restore_key(rng["state_before_split"])
    expected_after = rng.get("state_after_split")
    if not isinstance(expected_after, Mapping):
        raise ValueError("record has no materialized state_after_split")
    _, expected_after_identity = _restore_key(expected_after)
    outputs = policy_data.get("outputs")
    if not isinstance(outputs, Mapping):
        raise ValueError("record has no policy outputs")
    expected_output = _materialize(outputs.get("after_output_transform"), arrays)
    if not isinstance(expected_output, Mapping):
        raise ValueError("record has no materialized transformed policy output")
    expected_ordinary = _ordinary_output(expected_output, OUTPUT_KEY)
    if "actions" not in expected_ordinary:
        raise ValueError("saved transformed policy output has no actions")
    expected_replay = dict(expected_ordinary)
    saved_policy_actions = np.asarray(expected_ordinary["actions"])
    expected_replay["actions"] = np.asarray(saved_policy_actions, dtype=np.float32)

    backend = OpenPiBackend({"policy_dir": str(checkpoint)})
    actual_policy_dir = Path(backend.get_metadata().get("policy_dir", "")).resolve(strict=True)
    if actual_policy_dir != checkpoint:
        raise ValueError(f"loaded policy path {actual_policy_dir} differs from requested checkpoint {checkpoint}")

    backend._policy._rng = before_key
    logging_off = backend.infer(copy.deepcopy(input_before_transport))
    logging_off_rng = _rng_identity(backend._policy)

    backend._policy._rng = jax.random.wrap_key_data(
        np.asarray(jax.random.key_data(before_key)), impl=before_identity["algorithm"]
    )
    logging_on_input = copy.deepcopy(input_before_transport)
    logging_on_input[CONTEXT_KEY] = copy.deepcopy(dict(query))
    logging_on = backend.infer(logging_on_input)
    logging_on_rng = _rng_identity(backend._policy)

    on_sidecar = logging_on.get(OUTPUT_KEY)
    if not isinstance(on_sidecar, Mapping) or on_sidecar.get("status") != "complete_policy_sidecar":
        raise ValueError("logging-on actual-model invocation did not produce a complete policy sidecar")
    on_rng = on_sidecar.get("rng")
    if not isinstance(on_rng, Mapping):
        raise ValueError("logging-on actual-model invocation has no RNG sidecar")
    on_before = on_rng.get("state_before_split")
    on_after = on_rng.get("state_after_split")
    if not isinstance(on_before, Mapping) or not isinstance(on_after, Mapping):
        raise ValueError("logging-on actual-model invocation has malformed RNG sidecar")

    ordinary_off = _ordinary_output(logging_off, OUTPUT_KEY)
    ordinary_on = _ordinary_output(logging_on, OUTPUT_KEY)
    invariance_checks = {
        "ordinary_output_logging_off_vs_logging_on": _comparison(ordinary_off, ordinary_on, "ordinary_output"),
        "final_rng_logging_off_vs_logging_on": _comparison(logging_off_rng, logging_on_rng, "final_rng"),
        "logging_on_sidecar_input_vs_saved_pre_transport_input": _comparison(
            on_sidecar.get("inputs", {}).get("before_policy_input_transform") if isinstance(on_sidecar.get("inputs"), Mapping) else None,
            input_before_transport,
            "sidecar.inputs.before_policy_input_transform",
        ),
        "logging_on_sidecar_rng_before_vs_saved": _comparison(
            _materialize(on_before, arrays), _materialize(rng["state_before_split"], arrays), "sidecar.rng.state_before_split"
        ),
        "logging_on_sidecar_rng_after_vs_saved": _comparison(
            _materialize(on_after, arrays), _materialize(expected_after, arrays), "sidecar.rng.state_after_split"
        ),
        "logging_on_final_rng_vs_saved": _comparison(logging_on_rng, expected_after_identity, "logging_on_final_rng"),
        "logging_off_final_rng_vs_saved": _comparison(logging_off_rng, expected_after_identity, "logging_off_final_rng"),
    }
    replay_checks = {
        "logging_off_vs_saved_backend_output": _field_comparisons(ordinary_off, expected_replay, "output"),
        "logging_on_vs_saved_backend_output": _field_comparisons(ordinary_on, expected_replay, "output"),
    }
    replay_passed = all(_all_equal(fields) for fields in replay_checks.values())
    invariance_passed = _all_equal(invariance_checks)
    ordinary_bundle = _write_ordinary_bundle(
        args.ordinary_output_npz, ordinary_off, ordinary_on, args.max_ordinary_array_bytes
    )
    passed = invariance_passed and replay_passed
    return {
        "schema_version": 2,
        "kind": "actual_model_logging_invariance_and_saved_replay_pair",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "script": {"path": str(Path(__file__).resolve()), "sha256": SCRIPT_SHA256},
        "record": {
            "path": str(record_path),
            "sha256": _sha256_file(record_path),
            "array_bundle": str(array_path),
            "array_bundle_sha256": _sha256_file(array_path),
            "record_id": query.get("record_id"),
            "episode_id": query.get("episode_id"),
            "query_id": query.get("query_id"),
        },
        "checkpoint": str(checkpoint),
        "input": {
            "source": "scheduler.input_before_policy_transport",
            "diagnostic_context_added_only_for_logging_on": True,
        },
        "backend_actions_boundary": {
            "operation": "np.asarray(saved_policy_after_output_transform.actions, dtype=np.float32)",
            "saved_policy_actions": _array_identity(saved_policy_actions),
            "expected_backend_actions": _array_identity(expected_replay["actions"]),
            "scope": "Only expected actions cross this explicit OpenPiBackend boundary; all other replay fields remain strict and uncast.",
        },
        "rng": {
            "state_before_split": before_identity,
            "saved_state_after_split": expected_after_identity,
            "logging_off_final": logging_off_rng,
            "logging_on_final": logging_on_rng,
        },
        "logging_invariance": {
            "passed": invariance_passed,
            "scope": "One loaded backend, same restored starting key, same ordinary pre-transport input, with diagnostic context added only to logging-on. Ordinary output excludes only timing and the diagnostic sidecar.",
            "ordinary_output_fields": sorted(ordinary_on),
            "comparisons": invariance_checks,
        },
        "cross_process_saved_replay": {
            "passed": replay_passed,
            "scope": "Additional saved-output replay check after only the explicit backend actions cast; it does not redefine same-process logging invariance.",
            "comparisons": replay_checks,
        },
        "ordinary_output": {
            "logging_off": _value_identity(ordinary_off),
            "logging_on": _value_identity(ordinary_on),
            "bundle": ordinary_bundle,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ordinary-output-npz", required=True, type=Path)
    parser.add_argument("--max-ordinary-array-bytes", type=int, default=_DEFAULT_MAX_ORDINARY_ARRAY_BYTES)
    args = parser.parse_args()
    if args.max_ordinary_array_bytes <= 0:
        raise ValueError("max ordinary array bytes must be positive")
    receipt: dict[str, Any] = {
        "schema_version": 2,
        "kind": "actual_model_logging_invariance_and_saved_replay_pair",
        "status": "failed",
        "passed": False,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": {"path": str(Path(__file__).resolve()), "sha256": SCRIPT_SHA256},
    }
    try:
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError(f"refusing to overwrite pair receipt: {args.output}")
        if args.ordinary_output_npz.exists() or args.ordinary_output_npz.is_symlink():
            raise FileExistsError(f"refusing to overwrite ordinary-output bundle: {args.ordinary_output_npz}")
        receipt.update(_run(args))
        receipt["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        _atomic_json(args.output, receipt)
        if not receipt["passed"]:
            raise RuntimeError("logging invariance and saved replay pair comparison failed")
        print(json.dumps({"passed": True, "output": str(args.output)}, sort_keys=True))
        return 0
    except BaseException as exc:
        receipt.update({
            "status": "failed",
            "passed": False,
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
        })
        try:
            _atomic_json(args.output, receipt)
        except BaseException:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
