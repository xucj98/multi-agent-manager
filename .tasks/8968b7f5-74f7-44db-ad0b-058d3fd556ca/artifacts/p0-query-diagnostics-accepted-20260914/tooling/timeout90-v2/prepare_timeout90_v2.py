#!/usr/bin/env python3
"""Build the task-private timeout-90 C2 diagnostic artifacts from frozen v1 inputs.

This script only writes beneath its own local task directory. The resulting
``manifests/`` and ``tools/`` trees are copied unchanged to the C2 task records
area before execution.
"""

from __future__ import annotations

from pathlib import Path
import difflib
import hashlib
import json
import os
import shutil
import stat
import tempfile
from typing import Any


TASK_ID = "8968b7f5-74f7-44db-ad0b-058d3fd556ca"
C_ROOT = "/mnt/public/xcj/Projects/state-vla"
REMOTE_RECORDS = f"{C_ROOT}/workspace/{TASK_ID}/records"
REMOTE_RUN = f"{C_ROOT}/workspace/{TASK_ID}/c2-query-diagnostic"
TIMEOUT_GROUP = "query_diagnostic_c2_20260914_timeout90_v2"
V1_LAUNCHER_SHA256 = "61e3e8ce80bbe0f17fd8d1b56472038189b5be3931bca16b476c2d70b0c1d732"
V1_PAIR_SHA256 = "cdf577911a203994be50fd423b522e95cd5604f43c94e15b0ea247c18f8bce42"
V1_TOOLS_MANIFEST_SHA256 = "36d913b151db2fc624783d856266ae06f6b6493d8b89ee00b14af084d5e5a442"
V1_CONFIG_SHA256 = {
    "full_t_plus_1": "3ef7bf537b922ac740ede9c18d7e637482cf42e02682a64ec8e4298d4a836f47",
    "serial_lag30": "5621ad8ef70219c770c6ad6f907f71606489e0a558bf8dfe0475ae42b6de3d67",
}
V1_RUNNER_MANIFEST_SHA256 = {
    "full_t_plus_1": "7109aec53ea9f42bb64f4772b1bda3433dc04c889100c694385be5394bff9a41",
    "serial_lag30": "2cf5b99fb952a2ed244e8f1de77b515b09a19fe70341f33d8ed4e0db2ff738a3",
}
VARIANTS = {
    "full_t_plus_1": {
        "checkpoint_parent": f"{C_ROOT}/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0",
        "checkpoint_alias": "CheckpointFull",
        "result_run": "query_diagnostic_full_t_plus_1_smoke_20260914_timeout90_v2",
    },
    "serial_lag30": {
        "checkpoint_parent": f"{C_ROOT}/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0",
        "checkpoint_alias": "CheckpointSerial",
        "result_run": "query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2",
    },
}

ROOT = Path(__file__).resolve().parent
V1 = ROOT / "v1"
OUT_MANIFESTS = ROOT / "manifests"
OUT_TOOLS = ROOT / "tools"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def atomic_text(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def unified(before: str, after: str, before_name: str, after_name: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=before_name,
            tofile=after_name,
        )
    )


def nested_differences(before: Any, after: Any, path: str = "") -> list[str]:
    if type(before) is not type(after):
        return [path]
    if isinstance(before, dict):
        changed: list[str] = []
        for key in sorted(set(before) | set(after)):
            key_path = f"{path}.{key}" if path else str(key)
            if key not in before or key not in after:
                changed.append(key_path)
            else:
                changed.extend(nested_differences(before[key], after[key], key_path))
        return changed
    if isinstance(before, list):
        if len(before) != len(after):
            return [path]
        changed = []
        for index, (left, right) in enumerate(zip(before, after, strict=True)):
            changed.extend(nested_differences(left, right, f"{path}[{index}]"))
        return changed
    return [] if before == after else [path]


def config_validator_source() -> str:
    return r'''#!/usr/bin/env python3
"""Verify the frozen timeout-90 scheduler config without contacting a server."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import tempfile
import traceback
from pathlib import Path
from unittest.mock import Mock, call

import yaml

from robot_bridge.scheduler.base import SchedulerBase
from robot_bridge.scheduler.openpi_simulation import OpenPiSimulationScheduler
from robot_bridge.transport.websocket import WebSocketClient


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite timeout validation receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--expected-directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = {"schema_version": 1, "kind": "timeout90_scheduler_config_validation", "status": "failed", "passed": False}
    try:
        config = args.config.resolve(strict=True)
        expected_directory = args.expected_directory.resolve(strict=False)
        payload = yaml.safe_load(config.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("scheduler") != "openpi_simulation":
            raise ValueError("scheduler config does not select openpi_simulation")
        params = payload.get("params")
        if not isinstance(params, dict):
            raise TypeError("scheduler config has no params mapping")
        if params.get("policy_first_infer_timeout") != 90.0:
            raise ValueError("policy_first_infer_timeout must be exactly 90.0")
        if "policy_timeout" in params:
            raise ValueError("scheduler config must not override the normal policy timeout")
        trace = params.get("diagnostic_trace")
        if not isinstance(trace, dict):
            raise TypeError("scheduler config has no diagnostic_trace mapping")
        if Path(trace.get("directory", "")).resolve(strict=False) != expected_directory:
            raise ValueError("diagnostic_trace.directory differs from the v2 isolated directory")
        if trace.get("episode_ids") != [0, 1] or trace.get("query_ids") != [1]:
            raise ValueError("scheduler config changed the selected episode/query set")
        if trace.get("max_records") != 2 or trace.get("max_array_bytes") != 67108864:
            raise ValueError("scheduler config changed the diagnostic limits")
        if params.get("move_steps") != 30:
            raise ValueError("scheduler config changed move_steps")
        first_default = inspect.signature(SchedulerBase.__init__).parameters["policy_first_infer_timeout"].default
        simulation_default = inspect.signature(OpenPiSimulationScheduler.__init__).parameters["policy_first_infer_timeout"].default
        client_default = inspect.signature(WebSocketClient.__init__).parameters["timeout"].default
        if first_default != 30.0 or simulation_default != 30.0 or client_default != 30.0:
            raise ValueError("frozen bridge no longer has the expected 30-second normal timeout defaults")
        scheduler = object.__new__(SchedulerBase)
        scheduler._policy_first_infer_timeout = 90.0
        scheduler._first_policy_infer_pending = True
        scheduler._policy_client = Mock(call=Mock(side_effect=[{"status": "ok"}, {"status": "ok"}]))
        scheduler._call_policy_infer({"step": "first"})
        scheduler._call_policy_infer({"step": "later"})
        if scheduler._policy_client.call.call_args_list != [
            call({"cmd": "infer", "step": "first"}, timeout=90.0),
            call({"cmd": "infer", "step": "later"}),
        ]:
            raise ValueError("frozen scheduler does not restore the ordinary client timeout after its first call")
        source = Path(inspect.getsourcefile(SchedulerBase) or "").resolve(strict=True)
        receipt.update({
            "status": "passed",
            "passed": True,
            "config": {"path": str(config), "sha256": sha256(config)},
            "diagnostic_directory": str(expected_directory),
            "first_policy_rpc_seconds": 90.0,
            "subsequent_policy_rpc_seconds": 30.0,
            "first_policy_log_marker": "First policy inference uses 90.0s RPC budget.",
            "frozen_scheduler_source": {"path": str(source), "sha256": sha256(source)},
            "no_policy_or_robot_connection": True,
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
'''


def smoke_validator_source() -> str:
    return r'''#!/usr/bin/env python3
"""Require two complete, recorded selected-query diagnostics from one v2 smoke."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import traceback
from pathlib import Path

import yaml


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
        raise FileExistsError(f"refusing to overwrite smoke acceptance receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"non-object JSONL row in {path}")
            rows.append(value)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", required=True, choices=("full_t_plus_1", "serial_lag30"))
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--diagnostic-dir", required=True, type=Path)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--validator", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = {"schema_version": 1, "kind": "timeout90_selected_query_smoke_acceptance", "variant": args.variant, "status": "failed", "passed": False}
    try:
        config = args.config.resolve(strict=True)
        diagnostic_dir = args.diagnostic_dir.resolve(strict=True)
        result_dir = args.result_dir.resolve(strict=True)
        validator = args.validator.resolve(strict=True)
        yaml_payload = yaml.safe_load(config.read_text(encoding="utf-8"))
        params = yaml_payload.get("params") if isinstance(yaml_payload, dict) else None
        trace = params.get("diagnostic_trace") if isinstance(params, dict) else None
        if not isinstance(trace, dict) or Path(trace.get("directory", "")).resolve(strict=False) != diagnostic_dir:
            raise ValueError("result validation config does not point to this isolated diagnostic directory")
        if params.get("policy_first_infer_timeout") != 90.0:
            raise ValueError("result validation config lacks policy_first_infer_timeout=90.0")
        records = sorted((diagnostic_dir / "records").glob("*.json"))
        if len(records) != 2:
            raise ValueError(f"expected exactly two selected-query records, found {len(records)}")
        identities = []
        validator_results = []
        for record in records:
            process = subprocess.run([os.fspath(Path(os.sys.executable)), os.fspath(validator), os.fspath(record)], text=True, capture_output=True, check=False)
            if process.returncode != 0:
                raise RuntimeError(f"validate_query_diagnostic failed for {record}: {process.stderr.strip()}")
            validated = json.loads(process.stdout)
            if validated.get("status") != "recorded":
                raise ValueError(f"{record} validated as {validated.get('status')!r}, not recorded")
            data = json.loads(record.read_text(encoding="utf-8"))
            query = data.get("query")
            if not isinstance(query, dict):
                raise TypeError(f"{record} has no query identity")
            if data.get("status") != "recorded" or query.get("query_id") != 1:
                raise ValueError(f"{record} is not a recorded query-1 diagnostic")
            bundle = data.get("array_bundle")
            if not isinstance(bundle, dict) or not isinstance(bundle.get("file"), str):
                raise ValueError(f"{record} has no array bundle")
            array_path = record.parent.parent / bundle["file"]
            identities.append({
                "record": ref(record),
                "array_bundle": ref(array_path),
                "episode_id": query.get("episode_id"),
                "env_seed": query.get("env_seed"),
                "query_id": query.get("query_id"),
                "record_id": query.get("record_id"),
            })
            validator_results.append(validated)
        pairs = {(item["episode_id"], item["env_seed"], item["query_id"]) for item in identities}
        if pairs != {(0, 100000, 1), (1, 100001, 1)}:
            raise ValueError(f"unexpected recorded query identities: {sorted(pairs)!r}")
        summary_path = result_dir / "diagnostics_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        benchmark = summary.get("benchmark")
        if not isinstance(benchmark, dict) or benchmark.get("status") != "completed" or benchmark.get("target_episodes") != 2:
            raise ValueError(f"benchmark did not complete the two-episode smoke: {benchmark!r}")
        if summary.get("episode_count") != 2:
            raise ValueError("benchmark summary does not contain both accepted terminal episodes")
        process_events_path = result_dir / "processes.jsonl"
        process_events = read_jsonl(process_events_path)
        scheduler_exits = [row for row in process_events if row.get("event") == "exit" and row.get("role") == "scheduler"]
        if len(scheduler_exits) != 2 or any(row.get("returncode") != 0 for row in scheduler_exits):
            raise ValueError(f"scheduler exits are not two clean terminal exits: {scheduler_exits!r}")
        scheduler_logs = sorted((result_dir / "processes").glob("*-scheduler.stdout.log"))
        marker = "First policy inference uses 90.0s RPC budget."
        if len(scheduler_logs) != 2 or any(marker not in path.read_text(encoding="utf-8", errors="replace") for path in scheduler_logs):
            raise ValueError("each scheduler process did not log the configured 90-second first-call budget")
        result_scheduler = result_dir / "scheduler.yaml"
        result_yaml = yaml.safe_load(result_scheduler.read_text(encoding="utf-8"))
        result_params = result_yaml.get("params") if isinstance(result_yaml, dict) else None
        if not isinstance(result_params, dict) or result_params.get("policy_first_infer_timeout") != 90.0:
            raise ValueError("result leaf did not retain the 90-second first-infer scheduler config")
        receipt.update({
            "status": "passed",
            "passed": True,
            "config": ref(config),
            "result_scheduler_config": ref(result_scheduler),
            "result_summary": ref(summary_path),
            "process_events": ref(process_events_path),
            "scheduler_logs": [ref(path) for path in scheduler_logs],
            "records": identities,
            "validator_results": validator_results,
            "scheduler_first_infer_log_marker": marker,
            "subsequent_policy_rpc_seconds": 30.0,
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


if __name__ == "__main__":n    raise SystemExit(main())
'''.replace('if __name__ == "__main__":n', 'if __name__ == "__main__":\n')


def preflight_source() -> str:
    return f'''#!/usr/bin/env python3
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

TASK_ID = {TASK_ID!r}
C_ROOT = {C_ROOT!r}
RUN = {REMOTE_RUN!r}
RECORDS = {REMOTE_RECORDS!r}
GROUP = {TIMEOUT_GROUP!r}
EXPECTED = {{
    "RMBench": "f401f5279c95451eb424ac98b831bab5552b2120",
    "robot-bridge": "e147f600dc4329f330a6e2eb0335150b5b3093a3",
    "openpi": "bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6",
}}
V1_FAILURE_RECEIPT = "681a5b4b5dc29069d69d1821190cb52e961be4f7009152b27b148533d8a67ad2"
DEPLOYMENT_RECEIPT = "c2-query-diagnostic-timeout90-v2-deployment-receipt.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite preflight receipt: {{path}}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def command(*args: str) -> str:
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = {{"schema_version": 1, "kind": "c2_timeout90_v2_preflight", "status": "failed", "passed": False}}
    try:
        deployment_path = Path(RECORDS) / DEPLOYMENT_RECEIPT
        deployment = json.loads(deployment_path.read_text(encoding="utf-8"))
        if deployment.get("status") != "passed" or deployment.get("passed") is not True:
            raise RuntimeError("the frozen v2 deployment receipt is not passed")
        source = {{}}
        for name, commit in EXPECTED.items():
            root = Path(RUN) / name
            head = command("git", "-C", str(root), "rev-parse", "HEAD").strip()
            dirty = command("git", "-C", str(root), "status", "--porcelain")
            if head != commit or dirty:
                raise RuntimeError(f"unexpected source state for {{name}}: {{head}} dirty={{bool(dirty)}}")
            source[name] = {{"root": str(root), "commit": head, "clean": True}}
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
            raise RuntimeError(f"GPU6 is not idle enough: {{gpu6}}")
        ports = subprocess.run(["ss", "-ltn"], text=True, capture_output=True, check=False).stdout
        if any(f":{{port}}" in ports for port in (19460, 19462)):
            raise RuntimeError("C2 policy or robot port is already listening")
        ps = subprocess.run(["ps", "-eo", "pid=,args="], text=True, capture_output=True, check=True).stdout
        owned = [line for line in ps.splitlines() if RUN in line]
        if owned:
            raise RuntimeError(f"task-owned C2 process remains: {{owned!r}}")
        new_paths = []
        for variant, spec in {json.dumps(VARIANTS)}.items():
            result = Path(RUN) / "RMBench" / "eval_result" / GROUP / spec["result_run"]
            diagnostic = Path(RECORDS) / "diagnostics-timeout90-v2" / variant
            pairing = Path(RECORDS) / "pairs-timeout90-v2" / variant
            for item in (result, diagnostic, pairing):
                if item.exists() or item.is_symlink():
                    raise RuntimeError(f"new v2 output already exists: {{item}}")
                new_paths.append(str(item))
        receipt.update({{
            "status": "passed", "passed": True, "task_id": TASK_ID, "gpu6": {{"raw": gpu6, "memory_used_mib": used, "memory_total_mib": total, "utilization_percent": util}},
            "ports_listening": {{"19460": False, "19462": False}}, "task_owned_processes": [], "source": source,
            "deployment_receipt": {{"path": str(deployment_path), "sha256": sha256(deployment_path)}},
            "v1_failure_receipt": {{"path": str(v1_receipt), "sha256": V1_FAILURE_RECEIPT}}, "new_outputs_absent": new_paths,
        }})
        atomic_json(args.output, receipt)
        print(json.dumps({{"passed": True, "output": str(args.output)}}, sort_keys=True))
        return 0
    except BaseException as exc:
        receipt["error"] = {{"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}}
        try:
            atomic_json(args.output, receipt)
        except BaseException:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
'''


def status_writer_source() -> str:
    return r'''#!/usr/bin/env python3
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
'''


def launcher_v2(base: str) -> str:
    replacements = {
        "EXPERIMENT_GROUP=query_diagnostic_c2_20260914": f"EXPERIMENT_GROUP={TIMEOUT_GROUP}",
        "EXPECTED_RESULT_RUN=query_diagnostic_full_t_plus_1_smoke_20260914": f"EXPECTED_RESULT_RUN={VARIANTS['full_t_plus_1']['result_run']}",
        "EXPECTED_RESULT_RUN=query_diagnostic_serial_lag30_smoke_20260914": f"EXPECTED_RESULT_RUN={VARIANTS['serial_lag30']['result_run']}",
        'DIAGNOSTIC_DIR="$RECORDS/diagnostics/$VARIANT"': 'DIAGNOSTIC_DIR="$RECORDS/diagnostics-timeout90-v2/$VARIANT"',
        'MANIFEST="$RECORDS/manifests/$VARIANT/runner_input_manifest.json"': 'MANIFEST="$RECORDS/manifests-timeout90-v2/$VARIANT/runner_input_manifest.json"',
        'SCHEDULER_CONFIG="$RECORDS/manifests/$VARIANT/scheduler_config.yaml"': 'SCHEDULER_CONFIG="$RECORDS/manifests-timeout90-v2/$VARIANT/scheduler_config.yaml"',
        'RECORDS="$C_ROOT/workspace/$TASK_ID/records"\n': 'RECORDS="$C_ROOT/workspace/$TASK_ID/records"\nTOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2"\n',
    }
    result = base
    for before, after in replacements.items():
        if before not in result:
            raise RuntimeError(f"v1 launcher lacks expected fragment: {before!r}")
        result = result.replace(before, after, 1)
    anchor = 'export RB_OPENPI_POLICY_DIR="$CHECKPOINT_PARENT/20000"\n'
    validation = '''export RB_OPENPI_POLICY_DIR="$CHECKPOINT_PARENT/20000"
"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/validate_timeout90_config.py" \\
  --config "$SCHEDULER_CONFIG" \\
  --expected-directory "$DIAGNOSTIC_DIR" \\
  --output "$RECORDS/timeout90-v2-config-validation-${VARIANT}.json"
'''
    if anchor not in result:
        raise RuntimeError("v1 launcher lacks environment anchor")
    result = result.replace(anchor, validation, 1)
    marker = 'printf \'scheduler_config_sha256=%s\\n\' "$(sha256sum "$SCHEDULER_CONFIG" | awk \'{print $1}\')"\n'
    expanded = marker + "printf 'policy_first_infer_timeout=90.0\\n'\nprintf 'policy_subsequent_infer_timeout=30.0\\n'\n"
    if marker not in result:
        raise RuntimeError("v1 launcher lacks scheduler hash marker")
    result = result.replace(marker, expanded, 1)
    return result


def pair_wrapper_source() -> str:
    options = []
    for variant, spec in VARIANTS.items():
        options.append(
            f'''  {variant})
    CHECKPOINT_PARENT="{spec['checkpoint_parent']}"
    RECORD="$RECORDS/diagnostics-timeout90-v2/{variant}/records/episode-000000-query-000001-seq-000001.json"
    OUTPUT="$RECORDS/pairs-timeout90-v2/{variant}/episode-000000-query-000001-seq-000001.json"
    ;;'''
        )
    cases = "\n".join(options)
    return f'''#!/usr/bin/env bash
# Run exactly one authorized logging-off/on pair from the completed v2 episode-0 record.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 {{full_t_plus_1|serial_lag30}}" >&2
  exit 64
fi

VARIANT=$1
TASK_ID={TASK_ID}
C_ROOT={C_ROOT}
RUN="$C_ROOT/workspace/$TASK_ID/c2-query-diagnostic"
RECORDS="$C_ROOT/workspace/$TASK_ID/records"
TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2"
GPU=6

case "$VARIANT" in
{cases}
  *)
    echo "unsupported variant: $VARIANT" >&2
    exit 64
    ;;
esac

[[ -f "$RECORD" ]] || {{ echo "missing accepted v2 record: $RECORD" >&2; exit 66; }}
[[ ! -e "$OUTPUT" ]] || {{ echo "refusing to overwrite pair receipt: $OUTPUT" >&2; exit 73; }}
for spec in \
  "$RUN/RMBench:f401f5279c95451eb424ac98b831bab5552b2120" \
  "$RUN/robot-bridge:e147f600dc4329f330a6e2eb0335150b5b3093a3" \
  "$RUN/openpi:bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6"; do
  root=${{spec%%:*}}
  commit=${{spec##*:}}
  [[ "$(git -C "$root" rev-parse HEAD)" == "$commit" ]] || {{ echo "unexpected source commit: $root" >&2; exit 65; }}
  [[ -z "$(git -C "$root" status --porcelain)" ]] || {{ echo "source worktree is dirty: $root" >&2; exit 65; }}
done
if ss -ltn 2>/dev/null | grep -Eq ':(19460|19462)\\b'; then
  echo "C2 server port is unexpectedly listening before direct pair" >&2
  exit 75
fi

mkdir -p "$(dirname "$OUTPUT")"
export CUDA_VISIBLE_DEVICES=$GPU
export SAPIEN_RENDER_DEVICE=cuda:0
export VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.4
export PYTHONPATH="$RUN/robot-bridge:$RUN/openpi/packages/openpi-client/src${{PYTHONPATH:+:$PYTHONPATH}}"

exec "$RUN/openpi/.venv/bin/python" "$TOOLS/pair_query_diagnostic_logging.py" \
  --record "$RECORD" \
  --checkpoint "$CHECKPOINT_PARENT/20000" \
  --output "$OUTPUT"
'''


def pipeline_source() -> str:
    entries = []
    for variant, spec in VARIANTS.items():
        entries.extend(
            [
                f'PHASE="{variant}_smoke"',
                f'"$TOOLS/launch_query_diagnostic_smoke_timeout90_v2.sh" "{variant}" "{spec["result_run"]}"',
                f'PHASE="{variant}_acceptance"',
                f'''"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/validate_completed_diagnostic_smoke.py" \\
  --variant "{variant}" \\
  --config "$RECORDS/manifests-timeout90-v2/{variant}/scheduler_config.yaml" \\
  --diagnostic-dir "$RECORDS/diagnostics-timeout90-v2/{variant}" \\
  --result-dir "$RUN/RMBench/eval_result/{TIMEOUT_GROUP}/{spec["result_run"]}" \\
  --validator "$RUN/robot-bridge/scripts/validate_query_diagnostic.py" \\
  --output "$RECORDS/timeout90-v2-smoke-acceptance-{variant}.json"''',
                f'PHASE="{variant}_logging_off_on_pair"',
                f'"$TOOLS/run_query_diagnostic_pair_timeout90_v2.sh" "{variant}"',
            ]
        )
    body = "\n\n".join(entries)
    return f'''#!/usr/bin/env bash
# One bounded C2 recovery: preflight, J smoke/acceptance/pair, then S smoke/acceptance/pair.
set -euo pipefail

TASK_ID={TASK_ID}
C_ROOT={C_ROOT}
RUN="$C_ROOT/workspace/$TASK_ID/c2-query-diagnostic"
RECORDS="$C_ROOT/workspace/$TASK_ID/records"
TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2"
STATUS="$RECORDS/c2-query-diagnostic-timeout90-v2-pipeline-status.json"
OUTER_LOG="$RECORDS/c2-query-diagnostic-timeout90-v2-pipeline.log"
STARTED_AT="$(date -u --iso-8601=seconds)"
PHASE="preflight"

[[ ! -e "$STATUS" ]] || {{ echo "refusing to reuse timeout90 pipeline status: $STATUS" >&2; exit 73; }}
finish() {{
  code=$?
  "$RUN/robot-bridge/.venv/bin/python" "$TOOLS/write_timeout90_pipeline_status.py" \\
    --output "$STATUS" --phase "$PHASE" --exit-code "$code" --started-at "$STARTED_AT" --log "$OUTER_LOG" || true
  trap - EXIT
  exit "$code"
}}
trap finish EXIT

"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/c2_timeout90_v2_preflight.py" \\
  --output "$RECORDS/c2-query-diagnostic-timeout90-v2-preflight.json"

{body}

PHASE="completed"
'''


def main() -> None:
    if OUT_MANIFESTS.exists() or OUT_TOOLS.exists():
        raise RuntimeError("refusing to overwrite an existing v2 manifests or tools directory")
    if sha256(V1 / "tools" / "launch_query_diagnostic_smoke.sh") != V1_LAUNCHER_SHA256:
        raise RuntimeError("copied v1 launcher hash does not match the frozen receipt")
    if sha256(V1 / "tools" / "pair_query_diagnostic_logging.py") != V1_PAIR_SHA256:
        raise RuntimeError("copied v1 pair hash does not match the frozen receipt")
    if sha256(V1 / "tools" / "query_diagnostic_c2_tools_manifest.json") != V1_TOOLS_MANIFEST_SHA256:
        raise RuntimeError("copied v1 tools manifest hash does not match the frozen receipt")

    source_files: dict[str, Any] = {"tools": {}, "manifests": {}}
    config_diffs: dict[str, Any] = {}
    manifest_diffs: dict[str, Any] = {}
    for variant in VARIANTS:
        source_dir = V1 / "manifests" / variant
        if sha256(source_dir / "scheduler_config.yaml") != V1_CONFIG_SHA256[variant]:
            raise RuntimeError(f"v1 {variant} scheduler config hash changed")
        if sha256(source_dir / "runner_input_manifest.json") != V1_RUNNER_MANIFEST_SHA256[variant]:
            raise RuntimeError(f"v1 {variant} runner manifest hash changed")
        destination = OUT_MANIFESTS / variant
        destination.mkdir(parents=True)
        for filename in ("weight_content_manifest.json", "runner_input_audit.json"):
            shutil.copy2(source_dir / filename, destination / filename)
        base_config = (source_dir / "scheduler_config.yaml").read_text(encoding="utf-8")
        old_directory = f'{REMOTE_RECORDS}/diagnostics/{variant}'
        new_directory = f'{REMOTE_RECORDS}/diagnostics-timeout90-v2/{variant}'
        if "policy_first_infer_timeout" in base_config or old_directory not in base_config:
            raise RuntimeError(f"unexpected v1 config content for {variant}")
        new_config = base_config.replace(old_directory, new_directory, 1)
        anchor = "  debug_iterations: 0\n"
        if anchor not in new_config:
            raise RuntimeError(f"v1 config lacks insertion anchor for {variant}")
        new_config = new_config.replace(anchor, anchor + "  policy_first_infer_timeout: 90.0\n", 1)
        config_path = destination / "scheduler_config.yaml"
        atomic_text(config_path, new_config)
        diff_path = destination / "scheduler_config.v1-to-timeout90-v2.diff"
        atomic_text(diff_path, unified(base_config, new_config, f"v1/{variant}/scheduler_config.yaml", f"timeout90-v2/{variant}/scheduler_config.yaml"))
        config_diffs[variant] = {"v1": ref(source_dir / "scheduler_config.yaml"), "v2": ref(config_path), "diff": ref(diff_path)}

        base_manifest_text = (source_dir / "runner_input_manifest.json").read_text(encoding="utf-8")
        old_prefix = f"TaskRecords/manifests/{variant}"
        new_prefix = f"TaskRecords/manifests-timeout90-v2/{variant}"
        if base_manifest_text.count(old_prefix) != 2:
            raise RuntimeError(f"unexpected v1 manifest path count for {variant}")
        new_manifest_text = base_manifest_text.replace(old_prefix, new_prefix)
        old_manifest = json.loads(base_manifest_text)
        new_manifest = json.loads(new_manifest_text)
        changed = nested_differences(old_manifest, new_manifest)
        allowed = {
            "checkpoints[0].weight_content_manifest",
            "simulation_runs[0].config_source",
        }
        if set(changed) != allowed:
            raise RuntimeError(f"unexpected runner manifest changes for {variant}: {changed!r}")
        manifest_path = destination / "runner_input_manifest.json"
        atomic_text(manifest_path, new_manifest_text)
        manifest_diff = destination / "runner_input_manifest.v1-to-timeout90-v2.diff"
        atomic_text(manifest_diff, unified(base_manifest_text, new_manifest_text, f"v1/{variant}/runner_input_manifest.json", f"timeout90-v2/{variant}/runner_input_manifest.json"))
        manifest_diffs[variant] = {"v1": ref(source_dir / "runner_input_manifest.json"), "v2": ref(manifest_path), "diff": ref(manifest_diff), "changed_json_paths": changed}

        input_summary = json.loads((source_dir / "input_summary.json").read_text(encoding="utf-8"))
        input_summary["runner_input_manifest_sha256"] = sha256(manifest_path)
        input_summary["scheduler_config_sha256"] = sha256(config_path)
        input_summary["diagnostic_directory"] = new_directory
        input_summary_path = destination / "input_summary.json"
        atomic_json(input_summary_path, input_summary)
        source_files["manifests"][variant] = {
            "v1_input_summary": ref(source_dir / "input_summary.json"),
            "v2_input_summary": ref(input_summary_path),
            "v2_runner_input_audit": ref(destination / "runner_input_audit.json"),
            "v2_weight_content_manifest": ref(destination / "weight_content_manifest.json"),
        }

    base_launcher_path = V1 / "tools" / "launch_query_diagnostic_smoke.sh"
    base_launcher = base_launcher_path.read_text(encoding="utf-8")
    launcher_path = OUT_TOOLS / "launch_query_diagnostic_smoke_timeout90_v2.sh"
    v2_launcher = launcher_v2(base_launcher)
    atomic_text(launcher_path, v2_launcher, executable=True)
    launcher_diff_path = OUT_TOOLS / "launch_query_diagnostic_smoke.v1-to-timeout90-v2.diff"
    atomic_text(launcher_diff_path, unified(base_launcher, v2_launcher, "v1/launch_query_diagnostic_smoke.sh", "timeout90-v2/launch_query_diagnostic_smoke_timeout90_v2.sh"))

    shutil.copy2(V1 / "tools" / "pair_query_diagnostic_logging.py", OUT_TOOLS / "pair_query_diagnostic_logging.py")
    (OUT_TOOLS / "pair_query_diagnostic_logging.py").chmod((OUT_TOOLS / "pair_query_diagnostic_logging.py").stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    atomic_text(OUT_TOOLS / "validate_timeout90_config.py", config_validator_source(), executable=True)
    atomic_text(OUT_TOOLS / "validate_completed_diagnostic_smoke.py", smoke_validator_source(), executable=True)
    atomic_text(OUT_TOOLS / "c2_timeout90_v2_preflight.py", preflight_source(), executable=True)
    atomic_text(OUT_TOOLS / "write_timeout90_pipeline_status.py", status_writer_source(), executable=True)
    atomic_text(OUT_TOOLS / "run_query_diagnostic_pair_timeout90_v2.sh", pair_wrapper_source(), executable=True)
    atomic_text(OUT_TOOLS / "run_timeout90_v2_pipeline.sh", pipeline_source(), executable=True)

    runtime_tools = sorted(path for path in OUT_TOOLS.iterdir() if path.is_file() and path.name != "query_diagnostic_c2_timeout90_v2_tools_manifest.json")
    tools_manifest = {
        "schema_version": 1,
        "kind": "frozen_c2_query_diagnostic_timeout90_v2_tools",
        "task_id": TASK_ID,
        "manager_task_revision": "5223fb70aa219e92ad34d9c73aad1172e18fa207",
        "v1_sources": {
            "launcher": {"sha256": V1_LAUNCHER_SHA256},
            "pair": {"sha256": V1_PAIR_SHA256},
            "tools_manifest": {"sha256": V1_TOOLS_MANIFEST_SHA256},
            "scheduler_configs": V1_CONFIG_SHA256,
            "runner_input_manifests": V1_RUNNER_MANIFEST_SHA256,
        },
        "only_authorized_runtime_change": {
            "params.policy_first_infer_timeout": 90.0,
            "subsequent_policy_rpc_seconds": 30.0,
            "no_extra_infer_prewarm": True,
            "new_result_group": TIMEOUT_GROUP,
            "new_diagnostic_root": f"{REMOTE_RECORDS}/diagnostics-timeout90-v2",
            "new_manifest_root": f"{REMOTE_RECORDS}/manifests-timeout90-v2",
        },
        "source_identity": {
            "RMBench": "f401f5279c95451eb424ac98b831bab5552b2120",
            "robot_bridge": "e147f600dc4329f330a6e2eb0335150b5b3093a3",
            "openpi": "bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6",
        },
        "authorized_runs": {
            variant: {
                "result_run": spec["result_run"],
                "episodes": [0, 1],
                "env_seeds": [100000, 100001],
                "query_ids": [1],
                "horizon": 50,
                "move_steps": 30,
                "max_records": 2,
                "max_array_bytes": 67108864,
            }
            for variant, spec in VARIANTS.items()
        },
        "runtime_tools": [
            {"name": path.name, "sha256": sha256(path), "expected_remote_path": f"{REMOTE_RECORDS}/tools/query-diagnostic-c2-timeout90-v2/{path.name}"}
            for path in runtime_tools
        ],
    }
    tools_manifest_path = OUT_TOOLS / "query_diagnostic_c2_timeout90_v2_tools_manifest.json"
    atomic_json(tools_manifest_path, tools_manifest)

    preparation = {
        "schema_version": 1,
        "kind": "c2_timeout90_v2_local_preparation",
        "task_id": TASK_ID,
        "manager_task_revision": "5223fb70aa219e92ad34d9c73aad1172e18fa207",
        "preparer": ref(Path(__file__).resolve()),
        "v1_sources": source_files,
        "scheduler_config_diffs": config_diffs,
        "runner_manifest_diffs": manifest_diffs,
        "launcher": {"v1": ref(base_launcher_path), "v2": ref(launcher_path), "diff": ref(launcher_diff_path)},
        "tools_manifest": ref(tools_manifest_path),
        "frozen_pair_script": ref(OUT_TOOLS / "pair_query_diagnostic_logging.py"),
        "deployment": {
            "remote_tools_root": f"{REMOTE_RECORDS}/tools/query-diagnostic-c2-timeout90-v2",
            "remote_manifests_root": f"{REMOTE_RECORDS}/manifests-timeout90-v2",
            "v1_artifacts_preserved": True,
            "no_source_tree_or_checkpoint_write": True,
        },
    }
    atomic_json(ROOT / "timeout90_v2_preparation.json", preparation)
    print(json.dumps({"preparation": ref(ROOT / "timeout90_v2_preparation.json"), "tools_manifest": ref(tools_manifest_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
