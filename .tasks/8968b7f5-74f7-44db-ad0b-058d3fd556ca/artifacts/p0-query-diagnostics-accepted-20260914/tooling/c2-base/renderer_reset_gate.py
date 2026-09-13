#!/usr/bin/env python3
"""Run the fixed 40-reset renderer lifecycle gate through the bridge proxy.

This is deliberately narrower than an evaluation runner: it starts the
existing RMBench worker through ``RMBenchSimulationController``, issues forty
fixed reset requests, and writes one gate receipt outside ``eval_result``.
It never starts a policy server or records rollout results.
"""

from __future__ import annotations

import argparse
import datetime as datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable


SEED_START = 100000
RESET_COUNT = 40
SYSTEM_ICD = Path("/etc/vulkan/icd.d/nvidia_icd.json")
TASK = "put_back_block"
TASK_CONFIG = "demo_clean_eval"
INFRA_MARKERS = (
    "ErrorIncompatibleDriver",
    "Your GPU driver does not support Vulkan",
    "Traceback (most recent call last)",
    "ConnectionResetError",
    "EOFError",
    "Segmentation fault",
    "core dumped",
)


class GateError(RuntimeError):
    """A gate precondition or reset did not satisfy the fixed contract."""


def _git_state(root: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    clean = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if commit.returncode or clean.returncode or not commit.stdout.strip():
        raise GateError(f"cannot record git state for {root}")
    if clean.stdout:
        raise GateError(f"source tree is dirty: {root}")
    return {"root": str(root), "commit": commit.stdout.strip(), "clean": True}


def _require_renderer_reuse(rmbench_root: Path) -> None:
    source = rmbench_root / "envs" / "_base_task.py"
    text = source.read_text(encoding="utf-8")
    if "_PROCESS_RENDERER = None" not in text or "self.renderer = _PROCESS_RENDERER" not in text:
        raise GateError("RMBench source does not contain the approved process renderer reuse")


def _outside_eval_result(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if "eval_result" in resolved.parts:
        raise GateError(f"{label} must not be written under eval_result")
    return resolved


def _load_controller(bridge_root: Path) -> Callable[[dict[str, Any]], Any]:
    bridge = str(bridge_root)
    if bridge not in sys.path:
        sys.path.insert(0, bridge)
    from robot_bridge.robot.controllers.rmbench_simulation import RMBenchSimulationController

    return RMBenchSimulationController


def run_gate(
    *,
    rmbench_root: Path,
    bridge_root: Path,
    worker_python: Path,
    device: int,
    output: Path,
    worker_log: Path,
    startup_timeout: float = 120.0,
    rpc_timeout: float = 660.0,
    system_icd: Path = SYSTEM_ICD,
    environment: dict[str, str] | None = None,
    controller_factory: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Execute the fixed contract and return the persisted receipt.

    ``controller_factory`` and ``environment`` are test seams. Production uses
    the bridge proxy and ``os.environ`` unchanged apart from the fixed-device
    mapping required by the renderer worker.
    """

    rmbench_root = rmbench_root.expanduser().resolve()
    bridge_root = bridge_root.expanduser().resolve()
    # Virtualenv ``bin/python`` is normally a symlink.  Resolving it selects
    # the base interpreter and loses the virtualenv's site-packages.
    worker_python = Path(os.path.abspath(worker_python.expanduser()))
    output = _outside_eval_result(output, "output")
    worker_log = _outside_eval_result(worker_log, "worker log")
    system_icd = system_icd.expanduser().resolve()
    if not rmbench_root.is_dir() or not bridge_root.is_dir() or not worker_python.is_file():
        raise GateError("rmbench root, bridge root, or worker Python does not exist")
    if not system_icd.is_file():
        raise GateError(f"system Vulkan ICD is unavailable: {system_icd}")
    if output.exists() or worker_log.exists():
        raise GateError("gate output and worker log must be fresh paths")
    if output == worker_log:
        raise GateError("gate output and worker log must differ")

    _require_renderer_reuse(rmbench_root)
    source = {"rmbench": _git_state(rmbench_root), "robot_bridge": _git_state(bridge_root)}
    runtime_env = os.environ if environment is None else environment
    runtime_env["CUDA_VISIBLE_DEVICES"] = str(device)
    runtime_env["SAPIEN_RENDER_DEVICE"] = "cuda:0"
    runtime_env["VK_ICD_FILENAMES"] = str(system_icd)
    output.parent.mkdir(parents=True, exist_ok=True)
    worker_log.parent.mkdir(parents=True, exist_ok=True)

    factory = controller_factory or _load_controller(bridge_root)
    controller = None
    worker_metadata: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = []
    failure: dict[str, str] | None = None
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        controller = factory({
            "rmbench_root": str(rmbench_root),
            "worker_python": str(worker_python),
            "worker_log_path": str(worker_log),
            "startup_timeout": startup_timeout,
            "rpc_timeout": rpc_timeout,
        })
        worker_metadata = controller.get_metadata()
        if not isinstance(worker_metadata, dict):
            raise GateError("worker proxy did not return metadata")
        for episode_id in range(RESET_COUNT):
            seed = SEED_START + episode_id
            started = time.monotonic()
            response = controller.reset(
                task=TASK,
                config={"task_config": TASK_CONFIG, "overrides": {"instruction_type": "unseen", "test_num": 100}},
                seed=seed,
                episode_id=episode_id,
                video={"enabled": False},
            )
            status = response.get("episode_status") if isinstance(response, dict) else None
            accepted = bool(response.get("accepted")) if isinstance(response, dict) else False
            rows.append({
                "episode_id": episode_id,
                "seed": seed,
                "accepted": accepted,
                "elapsed_s": round(time.monotonic() - started, 3),
                "status": status,
            })
            if not accepted:
                raise GateError(f"seed {seed} was not accepted")
            if not isinstance(status, dict) or status.get("state") != "ready" or status.get("terminal") is not False:
                raise GateError(f"seed {seed} did not reach a ready nonterminal state")
    except Exception as exc:  # Preserve the original failure in the receipt.
        failure = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        if controller is not None:
            try:
                controller.shutdown()
            except Exception as exc:  # A shutdown failure also invalidates the gate.
                if failure is None:
                    failure = {"type": type(exc).__name__, "message": f"worker shutdown failed: {exc}"}

    worker_text = worker_log.read_text(encoding="utf-8", errors="replace") if worker_log.exists() else ""
    marker_counts = {marker: worker_text.count(marker) for marker in INFRA_MARKERS}
    expected_seeds = list(range(SEED_START, SEED_START + RESET_COUNT))
    accepted = [row["accepted"] for row in rows]
    passed = (
        failure is None
        and len(rows) == RESET_COUNT
        and [row["episode_id"] for row in rows] == list(range(RESET_COUNT))
        and [row["seed"] for row in rows] == expected_seeds
        and all(accepted)
        and not any(marker_counts.values())
    )
    receipt = {
        "kind": "rmbench_renderer_reset_gate",
        "schema_version": 1,
        "requested_count": RESET_COUNT,
        "completed_count": len(rows),
        "seed_sequence": f"{SEED_START}..{SEED_START + RESET_COUNT - 1}",
        "task": {"name": TASK, "config": TASK_CONFIG, "video": False},
        "device": {
            "cuda_visible_devices": runtime_env["CUDA_VISIBLE_DEVICES"],
            "sapien_render_device": runtime_env["SAPIEN_RENDER_DEVICE"],
            "vulkan_icd": runtime_env["VK_ICD_FILENAMES"],
        },
        "source": source,
        "worker_proxy": "RMBenchSimulationController",
        "worker_metadata": worker_metadata,
        "worker_log": str(worker_log),
        "worker_infra_markers": marker_counts,
        "rows": rows,
        "error": failure,
        "passed": passed,
        "started_at": started_at,
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return receipt


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="fixed 40-reset RMBench renderer lifecycle gate")
    parser.add_argument("--rmbench-root", type=Path, default=Path.cwd())
    parser.add_argument("--bridge-root", type=Path, required=True)
    parser.add_argument("--worker-python", type=Path, required=True)
    parser.add_argument("--device", type=int, required=True, help="physical GPU exposed as cuda:0 to the worker")
    parser.add_argument("--output", type=Path, required=True, help="fresh gate receipt outside eval_result")
    parser.add_argument("--worker-log", type=Path, required=True, help="fresh worker stderr log outside eval_result")
    parser.add_argument("--startup-timeout", type=float, default=120.0)
    parser.add_argument("--rpc-timeout", type=float, default=660.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    receipt = run_gate(
        rmbench_root=args.rmbench_root,
        bridge_root=args.bridge_root,
        worker_python=args.worker_python,
        device=args.device,
        output=args.output,
        worker_log=args.worker_log,
        startup_timeout=args.startup_timeout,
        rpc_timeout=args.rpc_timeout,
    )
    print(json.dumps({"output": str(args.output), "passed": receipt["passed"], "completed_count": receipt["completed_count"]}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
