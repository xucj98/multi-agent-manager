"""Small, task-private helpers for a bounded first-query diagnosis.

The helpers deliberately retain arrays only when a caller asks for a full
snapshot.  Their hashes are stable across processes and are safe to compare
without loading the NPZ archive again.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = 1


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_json(path: str | Path, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(value) + b"\n"
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(destination)


def atomic_write_pickle(path: str | Path, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(destination)


def load_pickle(path: str | Path) -> Any:
    with Path(path).open("rb") as handle:
        return pickle.load(handle)


def _array(value: Any) -> np.ndarray | None:
    if isinstance(value, np.ndarray):
        return np.asarray(value)
    if isinstance(value, np.generic):
        return np.asarray(value)
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        try:
            return np.asarray(value)
        except (TypeError, ValueError):
            return None
    return None


def array_fingerprint(value: Any) -> dict[str, Any]:
    array = _array(value)
    if array is None:
        raise TypeError(f"cannot fingerprint non-array {type(value).__name__}")
    if array.dtype.hasobject:
        raise TypeError("object arrays are not reproducible diagnostic inputs")
    contiguous = np.ascontiguousarray(array)
    header = canonical_json({"dtype": contiguous.dtype.str, "shape": list(contiguous.shape), "order": "C"})
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\0")
    digest.update(contiguous.tobytes(order="C"))
    return {
        "kind": "array",
        "dtype": contiguous.dtype.str,
        "shape": list(contiguous.shape),
        "nbytes": int(contiguous.nbytes),
        "sha256": digest.hexdigest(),
        "nonfinite": bool(np.issubdtype(contiguous.dtype, np.inexact) and not np.isfinite(contiguous).all()),
    }


def _scalar_descriptor(value: Any) -> dict[str, Any]:
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, bytes):
        return {
            "kind": "bytes",
            "length": len(value),
            "sha256": sha256_bytes(value),
        }
    if value is None or isinstance(value, (str, bool, int, float)):
        try:
            encoded = canonical_json(value)
        except ValueError as exc:
            raise TypeError(f"non-finite scalar cannot be recorded: {value!r}") from exc
        descriptor: dict[str, Any] = {
            "kind": type(value).__name__ if value is not None else "none",
            "sha256": sha256_bytes(encoded),
        }
        # Retain language input itself for the single bounded query. This is
        # useful when a hash differs and does not expand camera storage.
        if isinstance(value, str):
            descriptor["value"] = value
            descriptor["length"] = len(value)
        elif value is None or isinstance(value, (bool, int, float)):
            descriptor["value"] = value
        return descriptor
    raise TypeError(f"unsupported diagnostic leaf type {type(value).__name__}")


def describe_tree(
    value: Any,
    *,
    directory: str | Path | None = None,
    stem: str | None = None,
    retain_arrays: bool = False,
) -> dict[str, Any]:
    """Describe a nested policy-wire value and optionally retain all arrays.

    The returned flat leaf list makes cross-process first-difference reporting
    deterministic.  When retention is enabled, only this selected snapshot is
    emitted as an NPZ bundle.
    """

    leaves: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {}

    def visit(item: Any, path: str) -> None:
        array = _array(item)
        if array is not None:
            descriptor = array_fingerprint(array)
            descriptor["path"] = path
            if retain_arrays:
                key = f"array_{len(arrays):04d}"
                arrays[key] = np.array(array, copy=True)
                descriptor["array_key"] = key
            leaves.append(descriptor)
            return
        if isinstance(item, Mapping):
            for key in sorted(item, key=lambda candidate: str(candidate)):
                child = str(key) if not path else f"{path}/{key}"
                visit(item[key], child)
            return
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for index, child_value in enumerate(item):
                child = str(index) if not path else f"{path}/{index}"
                visit(child_value, child)
            return
        descriptor = _scalar_descriptor(item)
        descriptor["path"] = path
        leaves.append(descriptor)

    visit(value, "$")
    leaves.sort(key=lambda record: str(record["path"]))
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "leaf_count": len(leaves),
        "leaves": leaves,
        "tree_sha256": sha256_bytes(canonical_json(leaves)),
    }
    if retain_arrays:
        if directory is None or not stem:
            raise ValueError("directory and stem are required when retain_arrays=True")
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        archive = root / f"{stem}.npz"
        with tempfile.NamedTemporaryFile(dir=root, prefix=f".{archive.name}.", suffix=".npz", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            np.savez_compressed(temporary, **arrays)
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
        result["array_bundle"] = {
            "path": str(archive),
            "sha256": sha256_file(archive),
            "array_count": len(arrays),
            "uncompressed_array_bytes": int(sum(array.nbytes for array in arrays.values())),
        }
    return result


def first_difference(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    left_leaves = {str(item["path"]): item for item in left.get("leaves", []) if isinstance(item, Mapping)}
    right_leaves = {str(item["path"]): item for item in right.get("leaves", []) if isinstance(item, Mapping)}
    for path in sorted(set(left_leaves) | set(right_leaves)):
        lhs, rhs = left_leaves.get(path), right_leaves.get(path)
        if lhs != rhs:
            return {"equal": False, "path": path, "left": lhs, "right": rhs}
    return {"equal": True}


def file_identity(path: str | Path) -> dict[str, Any]:
    item = Path(path).resolve()
    return {"path": str(item), "sha256": sha256_file(item)}


def key_data(key: Any) -> np.ndarray:
    """Return JAX key data without assuming an old- or new-style key object."""

    import jax

    try:
        return np.asarray(jax.random.key_data(key), dtype=np.uint32)
    except (AttributeError, TypeError, ValueError):
        return np.asarray(key, dtype=np.uint32)


def key_descriptor(key: Any) -> dict[str, Any]:
    data = key_data(key)
    return {"algorithm": "threefry2x32", "key_data": array_fingerprint(data), "values": data.tolist()}
