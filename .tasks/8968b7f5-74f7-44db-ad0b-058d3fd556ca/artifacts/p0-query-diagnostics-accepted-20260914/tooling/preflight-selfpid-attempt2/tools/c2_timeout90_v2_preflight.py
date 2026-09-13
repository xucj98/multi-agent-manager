#!/usr/bin/env python3
"""Read-only C2 GPU6 preflight for the one timeout-90 recovery pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import traceback
from pathlib import Path

TASK_ID = '8968b7f5-74f7-44db-ad0b-058d3fd556ca'
C_ROOT = '/mnt/public/xcj/Projects/state-vla'
RUN = '/mnt/public/xcj/Projects/state-vla/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/c2-query-diagnostic'
RECORDS = '/mnt/public/xcj/Projects/state-vla/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/records'
GROUP = 'query_diagnostic_c2_20260914_timeout90_v2'
EXPECTED = {
    "RMBench": "f401f5279c95451eb424ac98b831bab5552b2120",
    "robot-bridge": "e147f600dc4329f330a6e2eb0335150b5b3093a3",
    "openpi": "bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6",
}
V1_FAILURE_RECEIPT = "681a5b4b5dc29069d69d1821190cb52e961be4f7009152b27b148533d8a67ad2"
DEPLOYMENT_RECEIPT = "c2-query-diagnostic-timeout90-v2-preflight-selfpid-attempt2-deployment-receipt.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite preflight receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def command(*args: str) -> str:
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout


def task_owned_processes(ps_output: str, *, self_pid: int) -> list[dict[str, object]]:
    """Return other process rows whose command line contains this task run path."""
    owned: list[dict[str, object]] = []
    for line in ps_output.splitlines():
        fields = line.strip().split(maxsplit=1)
        if not fields:
            continue
        try:
            pid = int(fields[0])
        except ValueError as exc:
            raise ValueError(f"could not parse process PID from ps output: {line!r}") from exc
        args = fields[1] if len(fields) == 2 else ""
        if RUN in args and pid != self_pid:
            owned.append({"pid": pid, "args": args})
    return owned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = {"schema_version": 1, "kind": "c2_timeout90_v2_preflight", "status": "failed", "passed": False}
    try:
        deployment_path = Path(RECORDS) / DEPLOYMENT_RECEIPT
        deployment = json.loads(deployment_path.read_text(encoding="utf-8"))
        if deployment.get("status") != "passed" or deployment.get("passed") is not True:
            raise RuntimeError("the frozen v2 deployment receipt is not passed")
        source = {}
        for name, commit in EXPECTED.items():
            root = Path(RUN) / name
            head = command("git", "-C", str(root), "rev-parse", "HEAD").strip()
            dirty = command("git", "-C", str(root), "status", "--porcelain")
            if head != commit or dirty:
                raise RuntimeError(f"unexpected source state for {name}: {head} dirty={bool(dirty)}")
            source[name] = {"root": str(root), "commit": head, "clean": True}
        v1_receipt = Path(RECORDS) / "c2-query-diagnostic-full_t_plus_1-failure-receipt.json"
        if sha256(v1_receipt) != V1_FAILURE_RECEIPT:
            raise RuntimeError("v1 failure receipt hash changed")
        gpu_lines = command("nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits").splitlines()
        gpu6 = next((line for line in gpu_lines if line.split(",", 1)[0].strip() == "6"), None)
        if gpu6 is None:
            raise RuntimeError("GPU6 was not reported")
        values = [item.strip() for item in gpu6.split(",")]
        used, total, util = (int(values[1]), int(values[2]), int(values[3]))
        if used > 256 or util > 5:
            raise RuntimeError(f"GPU6 is not idle enough: {gpu6}")
        ports = subprocess.run(["ss", "-ltn"], text=True, capture_output=True, check=False).stdout
        if any(f":{port}" in ports for port in (19460, 19462)):
            raise RuntimeError("C2 policy or robot port is already listening")
        ps = subprocess.run(["ps", "-eo", "pid=,args="], text=True, capture_output=True, check=True).stdout
        owned = task_owned_processes(ps, self_pid=os.getpid())
        if owned:
            raise RuntimeError(f"task-owned C2 process remains: {owned!r}")
        new_paths = []
        for variant, spec in {"full_t_plus_1": {"checkpoint_parent": "/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0", "checkpoint_alias": "CheckpointFull", "result_run": "query_diagnostic_full_t_plus_1_smoke_20260914_timeout90_v2"}, "serial_lag30": {"checkpoint_parent": "/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0", "checkpoint_alias": "CheckpointSerial", "result_run": "query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2"}}.items():
            result = Path(RUN) / "RMBench" / "eval_result" / GROUP / spec["result_run"]
            diagnostic = Path(RECORDS) / "diagnostics-timeout90-v2" / variant
            pairing = Path(RECORDS) / "pairs-timeout90-v2" / variant
            for item in (result, diagnostic, pairing):
                if item.exists() or item.is_symlink():
                    raise RuntimeError(f"new v2 output already exists: {item}")
                new_paths.append(str(item))
        receipt.update({
            "status": "passed", "passed": True, "task_id": TASK_ID, "gpu6": {"raw": gpu6, "memory_used_mib": used, "memory_total_mib": total, "utilization_percent": util},
            "ports_listening": {"19460": False, "19462": False}, "task_owned_processes": [], "source": source,
            "deployment_receipt": {"path": str(deployment_path), "sha256": sha256(deployment_path)},
            "v1_failure_receipt": {"path": str(v1_receipt), "sha256": V1_FAILURE_RECEIPT}, "new_outputs_absent": new_paths,
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
