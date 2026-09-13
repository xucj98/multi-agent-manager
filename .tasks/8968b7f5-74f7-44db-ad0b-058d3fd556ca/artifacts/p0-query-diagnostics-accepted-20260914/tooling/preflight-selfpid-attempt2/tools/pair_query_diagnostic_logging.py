#!/usr/bin/env python3
"""Compare actual OpenPI inference with selected-query logging disabled and enabled.

The checker consumes one completed diagnostic record.  It materializes the
recorded scheduler input, restores the recorded state_before_split on the
already loaded Policy, then invokes the actual checkpoint twice: once without
the selected-query envelope and once with the saved envelope.  It does not
start a robot, scheduler, WebSocket server, or a new environment reset.
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

import jax
import numpy as np

from robot_bridge.policy.backends.openpi import OpenPiBackend
from robot_bridge.scheduler.query_diagnostic import CONTEXT_KEY, OUTPUT_KEY, validate_record


SCRIPT_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_TIMING_KEYS = {"policy_timing"}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(encoded)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _strict_record(path: Path) -> tuple[dict[str, Any], dict[str, np.ndarray], Path]:
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
    if isinstance(left, float) or isinstance(right, float):
        if isinstance(left, float) and isinstance(right, float) and np.isnan(left) and np.isnan(right):
            return None
    return None if left == right else f"{path}: {left!r} != {right!r}"


def _ordinary_output(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): item for key, item in value.items() if key not in _TIMING_KEYS and key != OUTPUT_KEY}


def _restore_key(rng: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
    algorithm = rng.get("algorithm")
    key_data = rng.get("key_data")
    if not isinstance(algorithm, str) or not algorithm or algorithm == "jax_key_data_unavailable":
        raise ValueError(f"unsupported recorded JAX key algorithm {algorithm!r}")
    if not isinstance(key_data, np.ndarray):
        raise TypeError("recorded rng key_data was not materialized as an ndarray")
    key = jax.random.wrap_key_data(np.array(key_data, copy=True), impl=algorithm)
    check = jax.random.key_data(key)
    if not np.array_equal(check, key_data):
        raise ValueError("restored JAX key does not reproduce recorded key_data")
    return key, {"algorithm": algorithm, "key_data": _array_identity(key_data)}


def _rng_identity(policy: Any) -> dict[str, Any]:
    key = policy._rng  # Task-owned checker: explicit restoration is required for the paired invocation.
    data = np.asarray(jax.random.key_data(key))
    return {"algorithm": str(jax.random.key_impl(key)), "key_data": _array_identity(data)}


def _recorded_output(policy: Mapping[str, Any], arrays: Mapping[str, np.ndarray]) -> Mapping[str, Any]:
    outputs = policy.get("outputs")
    if not isinstance(outputs, Mapping):
        raise ValueError("record has no policy outputs")
    result = _materialize(outputs.get("after_output_transform"), arrays)
    if not isinstance(result, Mapping):
        raise ValueError("record has no materialized transformed policy output")
    return result


def _run(args: argparse.Namespace) -> dict[str, Any]:
    record_path = args.record.resolve(strict=True)
    checkpoint = args.checkpoint.resolve(strict=True)
    data, arrays, array_path = _strict_record(record_path)
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
    expected_output = _recorded_output(policy_data, arrays)

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

    ordinary_off = _ordinary_output(logging_off)
    ordinary_on = _ordinary_output(logging_on)
    expected_ordinary = _ordinary_output(expected_output)
    comparisons = {
        "logging_off_vs_logging_on": _same_value(ordinary_off, ordinary_on),
        "logging_on_vs_saved_recorded_output": _same_value(ordinary_on, expected_ordinary),
        "logging_off_vs_saved_recorded_output": _same_value(ordinary_off, expected_ordinary),
        "logging_on_sidecar_input_vs_saved_pre_transport_input": _same_value(
            on_sidecar.get("inputs", {}).get("before_policy_input_transform") if isinstance(on_sidecar.get("inputs"), Mapping) else None,
            input_before_transport,
        ),
        "logging_on_sidecar_rng_before_vs_saved": _same_value(
            _materialize(on_before, arrays), _materialize(rng["state_before_split"], arrays)
        ),
        "logging_off_final_rng_vs_logging_on": _same_value(logging_off_rng, logging_on_rng),
        "logging_on_final_rng_vs_saved": _same_value(logging_on_rng, expected_after_identity),
        "logging_off_final_rng_vs_saved": _same_value(logging_off_rng, expected_after_identity),
        "logging_on_sidecar_rng_after_vs_saved": _same_value(
            _materialize(on_after, arrays), _materialize(expected_after, arrays)
        ),
    }
    passed = all(value is None for value in comparisons.values())
    return {
        "schema_version": 1,
        "kind": "actual_model_logging_off_on_pair",
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
        "rng": {
            "state_before_split": before_identity,
            "saved_state_after_split": expected_after_identity,
            "logging_off_final": logging_off_rng,
            "logging_on_final": logging_on_rng,
        },
        "ordinary_output": {
            "keys": sorted(ordinary_on),
            "actions": _array_identity(ordinary_on["actions"]) if "actions" in ordinary_on else None,
            "state": _array_identity(ordinary_on["state"]) if "state" in ordinary_on else None,
        },
        "comparisons": {key: {"equal": value is None, "difference": value} for key, value in comparisons.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "actual_model_logging_off_on_pair",
        "status": "failed",
        "passed": False,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": {"path": str(Path(__file__).resolve()), "sha256": SCRIPT_SHA256},
    }
    try:
        receipt.update(_run(args))
        receipt["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        _atomic_json(args.output, receipt)
        if not receipt["passed"]:
            raise RuntimeError("logging off/on pair comparison failed")
        print(json.dumps({"passed": True, "output": str(args.output)}, sort_keys=True))
        return 0
    except BaseException as exc:  # Preserve the first observed failure as an auditable task artifact.
        receipt.update(
            {
                "status": "failed",
                "passed": False,
                "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
            }
        )
        _atomic_json(args.output, receipt)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
