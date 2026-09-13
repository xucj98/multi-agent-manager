#!/usr/bin/env python3
"""Write one non-overwriting terminal status receipt for the v2 pipeline."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--exit-code", required=True, type=int)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--log", required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError(f"refusing to overwrite pipeline status: {args.output}")
    payload = {
        "schema_version": 1,
        "kind": "c2_timeout90_v2_pipeline_status",
        "status": "completed" if args.exit_code == 0 else "failed",
        "exit_code": args.exit_code,
        "last_phase": args.phase,
        "started_at": args.started_at,
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "outer_log": args.log,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.output.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, args.output)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
