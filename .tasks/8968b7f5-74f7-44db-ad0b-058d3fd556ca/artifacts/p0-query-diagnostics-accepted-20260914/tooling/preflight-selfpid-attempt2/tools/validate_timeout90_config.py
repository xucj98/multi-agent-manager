#!/usr/bin/env python3
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
