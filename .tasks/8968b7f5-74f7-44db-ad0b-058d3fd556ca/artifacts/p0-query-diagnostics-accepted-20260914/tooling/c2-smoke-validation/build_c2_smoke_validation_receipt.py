"""Write a task-owned receipt for the C2 cuRobo smoke validation copy."""

from __future__ import annotations

import argparse
import datetime as datetime
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from query_diagnostic_curobo_provenance import verify_curobo_extension_origin


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {"path": str(path), "bytes": stat.st_size, "sha256": _sha256(path)}


def _git_state(path: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return {"root": str(path), "commit": commit, "clean": not dirty}


def _last_smoke_json(text: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "render_shape" in parsed and "pose_distance_max" in parsed:
            return parsed
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--records-root", type=Path, required=True)
    parser.add_argument("--original-script", type=Path, required=True)
    parser.add_argument("--validation-script", type=Path, required=True)
    parser.add_argument("--provenance-script", type=Path, required=True)
    parser.add_argument("--diff", type=Path, required=True)
    parser.add_argument("--command-file", type=Path, required=True)
    parser.add_argument("--smoke-log", type=Path, required=True)
    parser.add_argument("--exit-status", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    smoke_log = args.smoke_log.read_text(encoding="utf-8", errors="replace")
    parsed_output = _last_smoke_json(smoke_log)
    provenance: dict[str, Any] | None = None
    provenance_error: dict[str, str] | None = None
    try:
        from curobo.curobolib import geom_cu

        provenance = verify_curobo_extension_origin(geom_cu.__file__)
    except Exception as exc:  # Receipt must preserve, rather than erase, a check failure.
        provenance_error = {"type": type(exc).__name__, "message": str(exc)}

    sources = {
        name: _git_state(args.run_root / name)
        for name in ("RMBench", "robot-bridge", "openpi")
    }
    passed = args.exit_status == 0 and parsed_output is not None and provenance_error is None
    receipt = {
        "kind": "c2_query_diagnostic_curobo_smoke_validation",
        "schema_version": 1,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "passed": passed,
        "validation_copy": {
            "original": _file(args.original_script),
            "validation": _file(args.validation_script),
            "provenance_helper": _file(args.provenance_script),
            "minimal_diff": _file(args.diff),
            "command_file": _file(args.command_file),
        },
        "environment": {
            "CUDA_VISIBLE_DEVICES": "6",
            "SAPIEN_RENDER_DEVICE": "cuda:0",
            "VK_ICD_FILENAMES": "/etc/vulkan/icd.d/nvidia_icd.json",
        },
        "actual_smoke": {
            "exit_status": args.exit_status,
            "log": _file(args.smoke_log),
            "output": parsed_output,
        },
        "provenance": provenance,
        "provenance_error": provenance_error,
        "source": sources,
    }
    temporary = args.output.with_name(f".{args.output.name}.tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({"output": str(args.output), "passed": passed}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
