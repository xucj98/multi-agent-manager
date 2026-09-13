#!/usr/bin/env python3
"""Exercise the preflight PID parser with a real self command and residual PID."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any


def process_table() -> str:
    return subprocess.run(
        ["ps", "-eo", "pid=,args="],
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def command_for_pid(table: str, pid: int) -> str | None:
    for line in table.splitlines():
        fields = line.strip().split(maxsplit=1)
        if fields and fields[0].isdigit() and int(fields[0]) == pid:
            return fields[1] if len(fields) == 2 else ""
    return None


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite CPU-check receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def load_preflight(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("preflight_selfpid_attempt2", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "c2_timeout90_v2_preflight_self_pid_cpu_check",
        "status": "failed",
        "passed": False,
    }
    residual: subprocess.Popen[str] | None = None
    try:
        module = load_preflight(args.preflight.resolve(strict=True))
        self_pid = os.getpid()
        initial = process_table()
        self_args = command_for_pid(initial, self_pid)
        if self_args is None or module.RUN not in self_args:
            raise AssertionError(
                "test process command line does not contain RUN; invoke this check with exec -a"
            )
        residual = subprocess.Popen(
            ["bash", "-c", 'exec -a "$1" sleep 30', "_", f"{module.RUN}/preflight-residual-cpu-check"],
            text=True,
        )
        observed = ""
        residual_args: str | None = None
        for _ in range(80):
            observed = process_table()
            residual_args = command_for_pid(observed, residual.pid)
            if residual_args is not None and module.RUN in residual_args:
                break
            time.sleep(0.05)
        if residual_args is None or module.RUN not in residual_args:
            raise AssertionError("real residual child command line was not visible in ps output")
        owned = module.task_owned_processes(observed, self_pid=self_pid)
        owned_pids = [int(item["pid"]) for item in owned]
        if self_pid in owned_pids:
            raise AssertionError("the current PID was not excluded")
        if residual.pid not in owned_pids:
            raise AssertionError("an other PID with RUN in its command line was not rejected")
        receipt.update(
            {
                "status": "passed",
                "passed": True,
                "self_pid": self_pid,
                "self_command_contains_run": True,
                "self_pid_ignored": True,
                "residual_pid": residual.pid,
                "residual_command_contains_run": True,
                "residual_pid_rejected": True,
                "matched_other_pids": owned_pids,
                "preflight": str(args.preflight.resolve(strict=True)),
            }
        )
        write_once(args.output, receipt)
        print(json.dumps({"passed": True, "output": str(args.output)}, sort_keys=True))
        return 0
    except BaseException as exc:
        receipt["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        try:
            write_once(args.output, receipt)
        except BaseException:
            pass
        raise
    finally:
        if residual is not None and residual.poll() is None:
            residual.terminate()
            try:
                residual.wait(timeout=5)
            except subprocess.TimeoutExpired:
                residual.kill()
                residual.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
