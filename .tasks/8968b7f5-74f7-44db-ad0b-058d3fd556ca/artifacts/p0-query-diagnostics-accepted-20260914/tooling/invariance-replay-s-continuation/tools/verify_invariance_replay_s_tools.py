#!/usr/bin/env python3
"""Verify a frozen task-private invariance/replay S-tool deployment."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import traceback
from pathlib import Path


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
        raise FileExistsError(f"refusing to overwrite deployment receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def checked_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve(strict=True)
    root_resolved = root.resolve(strict=True)
    if root_resolved not in path.parents and path != root_resolved:
        raise ValueError(f"manifest path escapes declared root: {relative!r}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--tools-root", required=True, type=Path)
    parser.add_argument("--frozen-tools-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = {"schema_version": 1, "kind": "invariance_replay_s_tool_deployment", "status": "failed", "passed": False}
    try:
        manifest_path = args.manifest.resolve(strict=True)
        tools_root = args.tools_root.resolve(strict=True)
        frozen_root = args.frozen_tools_root.resolve(strict=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("kind") != "c2_invariance_replay_s_continuation_tools_manifest":
            raise ValueError("unexpected manifest kind")
        verified_files = []
        for item in manifest.get("runtime_tools", []):
            if not isinstance(item, dict) or not isinstance(item.get("relative_path"), str) or not isinstance(item.get("sha256"), str):
                raise TypeError("malformed runtime tool manifest entry")
            path = checked_path(tools_root, item["relative_path"])
            actual = sha256(path)
            if actual != item["sha256"]:
                raise ValueError(f"runtime tool hash mismatch: {item['relative_path']}")
            verified_files.append(ref(path))
        verified_frozen = []
        for item in manifest.get("frozen_dependencies", []):
            if not isinstance(item, dict) or not isinstance(item.get("relative_path"), str) or not isinstance(item.get("sha256"), str):
                raise TypeError("malformed frozen dependency manifest entry")
            path = checked_path(frozen_root, item["relative_path"])
            actual = sha256(path)
            if actual != item["sha256"]:
                raise ValueError(f"frozen dependency hash mismatch: {item['relative_path']}")
            verified_frozen.append(ref(path))
        if not verified_files or not verified_frozen:
            raise ValueError("manifest must list runtime tools and frozen dependencies")
        receipt.update({
            "status": "passed",
            "passed": True,
            "manifest": ref(manifest_path),
            "tools_root": str(tools_root),
            "frozen_tools_root": str(frozen_root),
            "verified_runtime_tools": verified_files,
            "verified_frozen_dependencies": verified_frozen,
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
