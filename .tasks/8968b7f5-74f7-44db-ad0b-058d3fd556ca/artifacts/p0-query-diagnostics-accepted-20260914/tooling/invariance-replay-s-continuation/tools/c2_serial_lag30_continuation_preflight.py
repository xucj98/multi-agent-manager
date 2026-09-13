#!/usr/bin/env python3
"""Read-only preflight for the manager-approved S-only continuation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import traceback
from pathlib import Path

TASK_ID = "8968b7f5-74f7-44db-ad0b-058d3fd556ca"
C_ROOT = "/mnt/public/xcj/Projects/state-vla"
RUN = f"{C_ROOT}/workspace/{TASK_ID}/c2-query-diagnostic"
RECORDS = f"{C_ROOT}/workspace/{TASK_ID}/records"
GROUP = "query_diagnostic_c2_20260914_timeout90_v2"
EXPECTED = {
    "RMBench": "f401f5279c95451eb424ac98b831bab5552b2120",
    "robot-bridge": "e147f600dc4329f330a6e2eb0335150b5b3093a3",
    "openpi": "bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6",
}
EXPECTED_J = {
    "record": ("diagnostics-timeout90-v2/full_t_plus_1/records/episode-000000-query-000001-seq-000001.json", "9f7191f0fd1c87464b378450c89524dc25d4c066012228db3792f9bcc9d4b1fe"),
    "array_bundle": ("diagnostics-timeout90-v2/full_t_plus_1/arrays/episode-000000-query-000001-seq-000001.npz", "85cf69da786301ec412ee49b459370db9240cdd7811ad610b4ea505d4a0cb37c"),
    "acceptance": ("timeout90-v2-preflight-selfpid-attempt2-smoke-acceptance-full_t_plus_1.json", "35fc6e092c51910b49c522737c044246d76017cb1aaa942b949f681c6992c412"),
    "legacy_pair": ("pairs-timeout90-v2/full_t_plus_1/episode-000000-query-000001-seq-000001.json", "77e397f3574b09ee389d0aac4637923bf6b39a4feac8c556a067e5d8676af0b3"),
}
DEPLOYMENT_RECEIPT = ("c2-query-diagnostic-timeout90-v2-preflight-selfpid-attempt2-deployment-receipt.json", "0a2809fd871679bf425fbfc0d9aa443da0ac54b82ec6da9e1b73d9c1011f581d")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite S continuation preflight receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def command(*args: str) -> str:
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout


def task_owned_processes(ps_output: str, self_pid: int) -> list[dict[str, object]]:
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
    receipt: dict = {"schema_version": 1, "kind": "c2_serial_lag30_continuation_preflight", "status": "failed", "passed": False}
    try:
        source = {}
        for name, commit in EXPECTED.items():
            root = Path(RUN) / name
            head = command("git", "-C", str(root), "rev-parse", "HEAD").strip()
            dirty = command("git", "-C", str(root), "status", "--porcelain")
            if head != commit or dirty:
                raise RuntimeError(f"unexpected source state for {name}: {head} dirty={bool(dirty)}")
            source[name] = {"root": str(root), "commit": head, "clean": True}
        preserved_j = {}
        for name, (relative, expected_hash) in EXPECTED_J.items():
            path = Path(RECORDS) / relative
            actual = sha256(path)
            if actual != expected_hash:
                raise RuntimeError(f"preserved J {name} hash changed: {actual}")
            preserved_j[name] = {"path": str(path), "sha256": actual}
        deployment_path = Path(RECORDS) / DEPLOYMENT_RECEIPT[0]
        if sha256(deployment_path) != DEPLOYMENT_RECEIPT[1]:
            raise RuntimeError("attempt2 deployment receipt hash changed")
        deployment = json.loads(deployment_path.read_text(encoding="utf-8"))
        if deployment.get("passed") is not True or deployment.get("status") != "passed":
            raise RuntimeError("attempt2 deployment receipt is not passed")
        gpu_lines = command("nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits").splitlines()
        gpu6 = next((line for line in gpu_lines if line.split(",", 1)[0].strip() == "6"), None)
        if gpu6 is None:
            raise RuntimeError("GPU6 was not reported")
        fields = [item.strip() for item in gpu6.split(",")]
        used, total, utilization = (int(fields[1]), int(fields[2]), int(fields[3]))
        if used > 256 or utilization > 5:
            raise RuntimeError(f"GPU6 is not idle enough: {gpu6}")
        ports = subprocess.run(["ss", "-ltn"], text=True, capture_output=True, check=False).stdout
        if any(f":{port}" in ports for port in (19460, 19462)):
            raise RuntimeError("C2 policy or robot port is already listening")
        ps = command("ps", "-eo", "pid=,args=")
        owned = task_owned_processes(ps, os.getpid())
        if owned:
            raise RuntimeError(f"task-owned C2 process remains: {owned!r}")
        expected_absent = [
            Path(RUN) / "RMBench" / "eval_result" / GROUP / "query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2",
            Path(RECORDS) / "diagnostics-timeout90-v2/serial_lag30",
            Path(RECORDS) / "pairs-timeout90-v2-invariance-replay/serial_lag30",
            Path(RECORDS) / "timeout90-v2-preflight-selfpid-attempt2-config-validation-serial_lag30.json",
            Path(RECORDS) / "timeout90-v2-invariance-replay-s-smoke-acceptance-serial_lag30.json",
        ]
        for path in expected_absent:
            if path.exists() or path.is_symlink():
                raise RuntimeError(f"S continuation output already exists: {path}")
        receipt.update({
            "status": "passed",
            "passed": True,
            "task_id": TASK_ID,
            "source": source,
            "preserved_j": preserved_j,
            "deployment_receipt": {"path": str(deployment_path), "sha256": DEPLOYMENT_RECEIPT[1]},
            "gpu6": {"raw": gpu6, "memory_used_mib": used, "memory_total_mib": total, "utilization_percent": utilization},
            "ports_listening": {"19460": False, "19462": False},
            "task_owned_processes": [],
            "serial_outputs_absent": [str(path) for path in expected_absent],
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
