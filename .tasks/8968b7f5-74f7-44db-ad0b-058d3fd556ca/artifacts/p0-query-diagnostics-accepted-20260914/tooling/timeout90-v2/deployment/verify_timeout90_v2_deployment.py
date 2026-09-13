#!/usr/bin/env python3
"""Verify the task-private C2 timeout-90 v2 deployment before any GPU work."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


TASK_ID = "8968b7f5-74f7-44db-ad0b-058d3fd556ca"
MANIFEST_KIND = "c2_query_diagnostic_timeout90_v2_deployment_manifest"
TOOLS_MANIFEST_KIND = "frozen_c2_query_diagnostic_timeout90_v2_tools"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regular_file(path: Path) -> os.stat_result:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"required deployment file is absent: {path}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise RuntimeError(f"deployment file must not be a symlink: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"deployment path is not a regular file: {path}")
    return info


def ref(path: Path) -> dict[str, Any]:
    info = regular_file(path)
    return {"path": str(path), "bytes": info.st_size, "sha256": sha256(path)}


def json_object(path: Path, label: str) -> dict[str, Any]:
    regular_file(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a JSON object: {path}")
    return value


def absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def under(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} is outside its declared root: {path}") from exc


def check_digest(path: Path, expected: dict[str, Any], label: str) -> dict[str, Any]:
    actual = ref(path)
    expected_bytes = expected.get("bytes")
    expected_sha = expected.get("sha256")
    if not isinstance(expected_bytes, int) or expected_bytes < 0:
        raise TypeError(f"{label} has invalid expected bytes")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise TypeError(f"{label} has invalid expected sha256")
    if actual["bytes"] != expected_bytes or actual["sha256"] != expected_sha:
        raise RuntimeError(
            f"{label} digest mismatch: expected bytes={expected_bytes} sha256={expected_sha}, "
            f"got bytes={actual['bytes']} sha256={actual['sha256']}"
        )
    return actual


def assert_exact_tree(root: Path, expected_files: set[Path], label: str) -> None:
    root = absolute(root)
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"{label} root is not a real directory: {root}")
    expected_dirs = {root}
    for file_path in expected_files:
        under(file_path, root, label)
        current = file_path.parent
        while current != root:
            expected_dirs.add(current)
            current = current.parent
    actual_files: set[Path] = set()
    actual_dirs: set[Path] = {root}
    for raw_dir, dirs, files in os.walk(root, topdown=True, followlinks=False):
        directory = absolute(Path(raw_dir))
        if directory.is_symlink():
            raise RuntimeError(f"{label} contains a symlinked directory: {directory}")
        actual_dirs.add(directory)
        for name in dirs:
            candidate = directory / name
            if candidate.is_symlink():
                raise RuntimeError(f"{label} contains a symlinked directory: {candidate}")
        for name in files:
            candidate = directory / name
            regular_file(candidate)
            actual_files.add(candidate)
    if actual_files != expected_files:
        unexpected = sorted(str(path) for path in actual_files - expected_files)
        missing = sorted(str(path) for path in expected_files - actual_files)
        raise RuntimeError(f"{label} file set differs; missing={missing!r} unexpected={unexpected!r}")
    if actual_dirs != expected_dirs:
        unexpected = sorted(str(path) for path in actual_dirs - expected_dirs)
        missing = sorted(str(path) for path in expected_dirs - actual_dirs)
        raise RuntimeError(f"{label} directory set differs; missing={missing!r} unexpected={unexpected!r}")


def validate_manifest(payload: dict[str, Any], manifest_path: Path, verifier_path: Path) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    if payload.get("schema_version") != 1 or payload.get("kind") != MANIFEST_KIND:
        raise ValueError("unexpected deployment manifest schema or kind")
    if payload.get("task_id") != TASK_ID:
        raise ValueError("deployment manifest task id differs from this verifier")
    roots_raw = payload.get("remote_roots")
    if not isinstance(roots_raw, dict):
        raise TypeError("deployment manifest has no remote_roots object")
    required_roots = ("records", "tools", "manifests", "deployment")
    if set(roots_raw) != set(required_roots):
        raise ValueError(f"deployment manifest roots differ: {sorted(roots_raw)!r}")
    roots = {name: absolute(Path(value)) for name, value in roots_raw.items() if isinstance(value, str)}
    if set(roots) != set(required_roots):
        raise TypeError("deployment manifest roots must be absolute strings")
    for name in ("tools", "manifests", "deployment"):
        under(roots[name], roots["records"], f"{name} root")
    expected_manifest_path = payload.get("deployment_manifest_remote_path")
    if not isinstance(expected_manifest_path, str) or absolute(Path(expected_manifest_path)) != manifest_path:
        raise ValueError("deployment manifest was not executed from its declared remote path")
    expected_receipt_path = payload.get("receipt_path")
    if not isinstance(expected_receipt_path, str):
        raise TypeError("deployment manifest has no receipt_path")
    receipt_path = absolute(Path(expected_receipt_path))
    under(receipt_path, roots["records"], "receipt path")
    verifier = payload.get("verifier")
    if not isinstance(verifier, dict):
        raise TypeError("deployment manifest has no verifier object")
    expected_verifier_path = verifier.get("remote_path")
    if not isinstance(expected_verifier_path, str) or absolute(Path(expected_verifier_path)) != verifier_path:
        raise ValueError("verifier was not executed from its declared remote path")
    under(verifier_path, roots["deployment"], "verifier path")
    check_digest(verifier_path, verifier, "deployment verifier")
    frozen = payload.get("frozen_tools_manifest")
    if not isinstance(frozen, dict):
        raise TypeError("deployment manifest has no frozen_tools_manifest object")
    expected_frozen_path = frozen.get("remote_path")
    if not isinstance(expected_frozen_path, str):
        raise TypeError("frozen tools manifest has no remote_path")
    frozen_path = absolute(Path(expected_frozen_path))
    under(frozen_path, roots["tools"], "frozen tools manifest")
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise TypeError("deployment manifest has no files list")
    seen_paths: set[Path] = set()
    seen_logical: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise TypeError(f"deployment file entry {index} is not an object")
        category = item.get("category")
        logical_path = item.get("logical_path")
        remote_path = item.get("remote_path")
        if category not in {"runtime_tool", "manifest"}:
            raise ValueError(f"deployment file entry {index} has unsupported category")
        if not isinstance(logical_path, str) or not logical_path:
            raise TypeError(f"deployment file entry {index} has invalid logical_path")
        if not isinstance(remote_path, str):
            raise TypeError(f"deployment file entry {index} has invalid remote_path")
        actual_path = absolute(Path(remote_path))
        required_root = roots["tools"] if category == "runtime_tool" else roots["manifests"]
        under(actual_path, required_root, f"deployment file entry {index}")
        if actual_path in seen_paths or logical_path in seen_logical:
            raise ValueError(f"duplicate deployment file entry {index}")
        seen_paths.add(actual_path)
        seen_logical.add(logical_path)
        normalized.append({**item, "_path": actual_path})
    if frozen_path not in seen_paths:
        raise ValueError("frozen tools manifest is not itself a tracked deployment file")
    return normalized, roots


def validate_tools_manifest(
    payload: dict[str, Any],
    frozen_path: Path,
    deployment_files: list[dict[str, Any]],
) -> None:
    frozen = payload["frozen_tools_manifest"]
    check_digest(frozen_path, frozen, "frozen tools manifest")
    tools = json_object(frozen_path, "frozen tools manifest")
    if tools.get("schema_version") != 1 or tools.get("kind") != TOOLS_MANIFEST_KIND:
        raise ValueError("unexpected frozen tools manifest schema or kind")
    if tools.get("task_id") != TASK_ID:
        raise ValueError("frozen tools manifest task id differs")
    if tools.get("manager_task_revision") != payload.get("manager_task_revision"):
        raise ValueError("frozen tools manifest task revision differs")
    if tools.get("source_identity") != payload.get("source_identity"):
        raise ValueError("frozen tools manifest source identity differs")
    listed = tools.get("runtime_tools")
    if not isinstance(listed, list):
        raise TypeError("frozen tools manifest has no runtime_tools list")
    expected = []
    for item in deployment_files:
        if item["category"] != "runtime_tool":
            continue
        path = item["_path"]
        if path == frozen_path:
            continue
        expected.append(
            {
                "name": path.name,
                "expected_remote_path": str(path),
                "sha256": item.get("sha256"),
            }
        )
    actual = []
    for item in listed:
        if not isinstance(item, dict):
            raise TypeError("frozen tools manifest runtime_tools has a non-object entry")
        actual.append(
            {
                "name": item.get("name"),
                "expected_remote_path": item.get("expected_remote_path"),
                "sha256": item.get("sha256"),
            }
        )
    if sorted(actual, key=lambda item: str(item["name"])) != sorted(expected, key=lambda item: str(item["name"])):
        raise ValueError("frozen tools manifest runtime_tools differs from deployment file set")


def write_once(path: Path, payload: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite deployment receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest_path = absolute(args.manifest)
    verifier_path = absolute(Path(__file__))
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "c2_query_diagnostic_timeout90_v2_deployment_receipt",
        "task_id": TASK_ID,
        "status": "failed",
        "passed": False,
    }
    output_path = absolute(args.output)
    try:
        regular_file(manifest_path)
        regular_file(verifier_path)
        payload = json_object(manifest_path, "deployment manifest")
        files, roots = validate_manifest(payload, manifest_path, verifier_path)
        expected_output = absolute(Path(payload["receipt_path"]))
        if output_path != expected_output:
            raise ValueError(f"output differs from the declared receipt path: {output_path}")
        assert_exact_tree(
            roots["deployment"],
            {manifest_path, verifier_path},
            "deployment verifier tree",
        )
        tool_files = {item["_path"] for item in files if item["category"] == "runtime_tool"}
        manifest_files = {item["_path"] for item in files if item["category"] == "manifest"}
        assert_exact_tree(roots["tools"], tool_files, "runtime tools tree")
        assert_exact_tree(roots["manifests"], manifest_files, "runtime manifests tree")
        verified_files = []
        for item in files:
            actual = check_digest(item["_path"], item, f"{item['category']} {item['logical_path']}")
            verified_files.append(
                {
                    "category": item["category"],
                    "logical_path": item["logical_path"],
                    **actual,
                }
            )
        frozen_path = absolute(Path(payload["frozen_tools_manifest"]["remote_path"]))
        validate_tools_manifest(payload, frozen_path, files)
        receipt.update(
            {
                "status": "passed",
                "passed": True,
                "verified_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "deployment_manifest": ref(manifest_path),
                "verifier": ref(verifier_path),
                "frozen_tools_manifest": ref(frozen_path),
                "remote_roots": {name: str(path) for name, path in roots.items()},
                "source_identity": payload["source_identity"],
                "manager_task_revision": payload["manager_task_revision"],
                "verified_file_count": len(verified_files),
                "verified_files": verified_files,
                "no_source_tree_or_checkpoint_write": True,
            }
        )
        write_once(output_path, receipt)
        print(json.dumps({"passed": True, "output": str(output_path)}, sort_keys=True))
        return 0
    except BaseException as exc:
        receipt["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        try:
            write_once(output_path, receipt)
        except BaseException:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
