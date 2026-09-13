#!/usr/bin/env python3
"""Prepare the bounded task-private preflight self-PID repair attempt."""
from __future__ import annotations

import difflib
import hashlib
import json
import shutil
from pathlib import Path

TASK_ID = "8968b7f5-74f7-44db-ad0b-058d3fd556ca"
MANAGER_REVISION = "c13aa2c55aaec8da3e211696b22b4dc613feec27"
C_ROOT = Path("/mnt/public/xcj/Projects/state-vla")
RECORDS = C_ROOT / "workspace" / TASK_ID / "records"
SOURCE_ROOT = Path("/mnt/public/xcj/Projects/workspace") / TASK_ID / "c2-query-diagnostic-timeout90-v2"
ATTEMPT_ROOT = Path(__file__).resolve().parent
NEW_TOOLS_NAME = "query-diagnostic-c2-timeout90-v2-preflight-selfpid-attempt2"
NEW_DEPLOYMENT_NAME = "deployment-timeout90-v2-preflight-selfpid-attempt2"
ATTEMPT_PREFIX = "c2-query-diagnostic-timeout90-v2-preflight-selfpid-attempt2"
NEW_TOOLS_ROOT = RECORDS / "tools" / NEW_TOOLS_NAME
NEW_DEPLOYMENT_ROOT = RECORDS / NEW_DEPLOYMENT_NAME
MANIFESTS_ROOT = RECORDS / "manifests-timeout90-v2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": sha256(path)}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def regular_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected exactly one replacement, found {count}")
    return text.replace(old, new)


def main() -> int:
    if not SOURCE_ROOT.is_dir():
        raise FileNotFoundError(SOURCE_ROOT)
    tools = ATTEMPT_ROOT / "tools"
    local_validation = ATTEMPT_ROOT / "local-validation"
    deployment = ATTEMPT_ROOT / "deployment"
    tools.mkdir()
    local_validation.mkdir()
    deployment.mkdir()
    for source in regular_files(SOURCE_ROOT / "tools"):
        target = tools / source.relative_to(SOURCE_ROOT / "tools")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    old_tools_manifest = tools / "query_diagnostic_c2_timeout90_v2_tools_manifest.json"
    if not old_tools_manifest.exists():
        raise FileNotFoundError(old_tools_manifest)
    old_tools_manifest.unlink()

    preflight = tools / "c2_timeout90_v2_preflight.py"
    preflight_text = preflight.read_text(encoding="utf-8")
    preflight_text = replace_once(
        preflight_text,
        'DEPLOYMENT_RECEIPT = "c2-query-diagnostic-timeout90-v2-deployment-receipt.json"',
        f'DEPLOYMENT_RECEIPT = "{ATTEMPT_PREFIX}-deployment-receipt.json"',
        "deployment receipt identity",
    )
    needle = '''def command(*args: str) -> str:
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout


def main() -> int:
'''
    replacement = '''def command(*args: str) -> str:
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
'''
    preflight_text = replace_once(preflight_text, needle, replacement, "self-PID parser helper")
    old_scan = '''        ps = subprocess.run(["ps", "-eo", "pid=,args="], text=True, capture_output=True, check=True).stdout
        owned = [line for line in ps.splitlines() if RUN in line]
        if owned:
            raise RuntimeError(f"task-owned C2 process remains: {owned!r}")
'''
    new_scan = '''        ps = subprocess.run(["ps", "-eo", "pid=,args="], text=True, capture_output=True, check=True).stdout
        owned = task_owned_processes(ps, self_pid=os.getpid())
        if owned:
            raise RuntimeError(f"task-owned C2 process remains: {owned!r}")
'''
    preflight_text = replace_once(preflight_text, old_scan, new_scan, "self-PID scan")
    preflight.write_text(preflight_text, encoding="utf-8")

    remote_old_tools = 'TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2"'
    remote_new_tools = f'TOOLS="$RECORDS/tools/{NEW_TOOLS_NAME}"'
    for name in (
        "launch_query_diagnostic_smoke_timeout90_v2.sh",
        "run_query_diagnostic_pair_timeout90_v2.sh",
        "run_timeout90_v2_pipeline.sh",
    ):
        path = tools / name
        text = path.read_text(encoding="utf-8")
        if remote_old_tools not in text:
            raise ValueError(f"{name} does not reference the prior tools root")
        path.write_text(text.replace(remote_old_tools, remote_new_tools), encoding="utf-8")

    pipeline = tools / "run_timeout90_v2_pipeline.sh"
    pipeline_text = pipeline.read_text(encoding="utf-8")
    replacements = {
        "c2-query-diagnostic-timeout90-v2-pipeline-status.json": f"{ATTEMPT_PREFIX}-pipeline-status.json",
        "c2-query-diagnostic-timeout90-v2-pipeline.log": f"{ATTEMPT_PREFIX}-pipeline.log",
        "c2-query-diagnostic-timeout90-v2-preflight.json": f"{ATTEMPT_PREFIX}-preflight.json",
        "timeout90-v2-smoke-acceptance-full_t_plus_1.json": "timeout90-v2-preflight-selfpid-attempt2-smoke-acceptance-full_t_plus_1.json",
        "timeout90-v2-smoke-acceptance-serial_lag30.json": "timeout90-v2-preflight-selfpid-attempt2-smoke-acceptance-serial_lag30.json",
    }
    for old, new in replacements.items():
        pipeline_text = replace_once(pipeline_text, old, new, f"pipeline receipt {old}")
    pipeline.write_text(pipeline_text, encoding="utf-8")

    launcher = tools / "launch_query_diagnostic_smoke_timeout90_v2.sh"
    launcher_text = launcher.read_text(encoding="utf-8")
    launcher_text = replace_once(
        launcher_text,
        'timeout90-v2-config-validation-${VARIANT}.json',
        'timeout90-v2-preflight-selfpid-attempt2-config-validation-${VARIANT}.json',
        "launcher config validation receipt",
    )
    launcher.write_text(launcher_text, encoding="utf-8")

    changed_names = (
        "c2_timeout90_v2_preflight.py",
        "launch_query_diagnostic_smoke_timeout90_v2.sh",
        "run_query_diagnostic_pair_timeout90_v2.sh",
        "run_timeout90_v2_pipeline.sh",
    )
    diff_parts: list[str] = []
    changes: list[dict[str, object]] = []
    unchanged: list[dict[str, object]] = []
    for name in sorted(path.name for path in regular_files(SOURCE_ROOT / "tools") if path.name != "query_diagnostic_c2_timeout90_v2_tools_manifest.json"):
        before = SOURCE_ROOT / "tools" / name
        after = tools / name
        before_ref = ref(before)
        after_ref = ref(after)
        entry = {"name": name, "v2": before_ref, "attempt2": after_ref}
        if name in changed_names:
            changes.append(entry)
            diff_parts.extend(
                difflib.unified_diff(
                    before.read_text(encoding="utf-8").splitlines(keepends=True),
                    after.read_text(encoding="utf-8").splitlines(keepends=True),
                    fromfile=f"v2/tools/{name}",
                    tofile=f"preflight-selfpid-attempt2/tools/{name}",
                )
            )
        else:
            if before_ref != after_ref:
                raise ValueError(f"unexpected content change in {name}")
            unchanged.append(entry)
    diff_path = tools / "v2-to-preflight-selfpid-attempt2-tools.diff"
    diff_path.write_text("".join(diff_parts), encoding="utf-8")

    summary_path = tools / "preflight_selfpid_attempt2_change_summary.json"
    write_json(
        summary_path,
        {
            "schema_version": 1,
            "kind": "c2_timeout90_v2_preflight_selfpid_attempt2_change_summary",
            "task_id": TASK_ID,
            "manager_task_revision": MANAGER_REVISION,
            "original_preflight": {
                "path": str(SOURCE_ROOT / "tools" / "c2_timeout90_v2_preflight.py"),
                **ref(SOURCE_ROOT / "tools" / "c2_timeout90_v2_preflight.py"),
            },
            "repaired_preflight": {"path": str(preflight), **ref(preflight)},
            "minimal_functional_change": {
                "parse_pid_from_ps_output": True,
                "ignore_only_pid_equal_to_os_getpid": True,
                "reject_other_command_lines_containing_run_path": True,
                "no_script_name_or_parent_process_exemption": True,
            },
            "necessary_attempt_identity_changes": {
                "tools_root": str(NEW_TOOLS_ROOT),
                "deployment_receipt": f"{ATTEMPT_PREFIX}-deployment-receipt.json",
                "pipeline_status": f"{ATTEMPT_PREFIX}-pipeline-status.json",
                "pipeline_log": f"{ATTEMPT_PREFIX}-pipeline.log",
                "preflight_receipt": f"{ATTEMPT_PREFIX}-preflight.json",
                "config_validation_prefix": "timeout90-v2-preflight-selfpid-attempt2-config-validation-",
                "acceptance_prefix": "timeout90-v2-preflight-selfpid-attempt2-smoke-acceptance-",
            },
            "changed_tool_files": changes,
            "unchanged_tool_files": unchanged,
            "combined_diff": {"path": str(diff_path), **ref(diff_path)},
            "reused_runtime_outputs": {
                "result_group": "query_diagnostic_c2_20260914_timeout90_v2",
                "diagnostic_root": str(RECORDS / "diagnostics-timeout90-v2"),
                "manifest_root": str(MANIFESTS_ROOT),
                "pair_root": str(RECORDS / "pairs-timeout90-v2"),
            },
        },
    )

    tools_manifest_path = tools / "query_diagnostic_c2_timeout90_v2_preflight_selfpid_attempt2_tools_manifest.json"
    runtime_tools = []
    for path in regular_files(tools):
        if path == tools_manifest_path:
            continue
        runtime_tools.append(
            {
                "name": path.name,
                "expected_remote_path": str(NEW_TOOLS_ROOT / path.relative_to(tools)),
                "sha256": sha256(path),
            }
        )
    runtime_tools.sort(key=lambda item: str(item["name"]))
    write_json(
        tools_manifest_path,
        {
            "schema_version": 1,
            "kind": "frozen_c2_query_diagnostic_timeout90_v2_tools",
            "task_id": TASK_ID,
            "manager_task_revision": MANAGER_REVISION,
            "attempt": "preflight_selfpid_attempt2",
            "source_identity": {
                "RMBench": "f401f5279c95451eb424ac98b831bab5552b2120",
                "openpi": "bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6",
                "robot_bridge": "e147f600dc4329f330a6e2eb0335150b5b3093a3",
            },
            "only_authorized_runtime_change": {
                "params.policy_first_infer_timeout": 90.0,
                "subsequent_policy_rpc_seconds": 30.0,
                "preflight_self_pid_exact_exclusion": True,
                "no_extra_infer_prewarm": True,
            },
            "authorized_runs": {
                "full_t_plus_1": {
                    "episodes": [0, 1],
                    "env_seeds": [100000, 100001],
                    "query_ids": [1],
                    "horizon": 50,
                    "move_steps": 30,
                    "max_records": 2,
                    "max_array_bytes": 67108864,
                    "result_run": "query_diagnostic_full_t_plus_1_smoke_20260914_timeout90_v2",
                },
                "serial_lag30": {
                    "episodes": [0, 1],
                    "env_seeds": [100000, 100001],
                    "query_ids": [1],
                    "horizon": 50,
                    "move_steps": 30,
                    "max_records": 2,
                    "max_array_bytes": 67108864,
                    "result_run": "query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2",
                },
            },
            "runtime_tools": runtime_tools,
            "v2_sources": {
                "preflight": {
                    "sha256": sha256(SOURCE_ROOT / "tools" / "c2_timeout90_v2_preflight.py"),
                },
                "tools_manifest": {
                    "sha256": sha256(SOURCE_ROOT / "tools" / "query_diagnostic_c2_timeout90_v2_tools_manifest.json"),
                },
                "deployment_receipt": {
                    "path": str(RECORDS / "c2-query-diagnostic-timeout90-v2-deployment-receipt.json"),
                    "sha256": "eafdafba8534f86f6514c48da19094f1d902df879a1676726baabb8ae0f9a266",
                },
                "pipeline_failure_status": {
                    "path": str(RECORDS / "c2-query-diagnostic-timeout90-v2-pipeline-status.json"),
                    "sha256": "4b7d173e65a451edecdec5855ef3f59f7bbc5e5a428d998d20893e1014cfe039",
                },
            },
        },
    )

    verifier_source = SOURCE_ROOT / "deployment" / "verify_timeout90_v2_deployment.py"
    verifier = deployment / verifier_source.name
    shutil.copy2(verifier_source, verifier)
    deployment_manifest_path = deployment / "query_diagnostic_c2_timeout90_v2_preflight_selfpid_attempt2_deployment_manifest.json"
    files: list[dict[str, object]] = []
    for path in regular_files(tools):
        files.append(
            {
                "category": "runtime_tool",
                "logical_path": f"runtime_tools/{path.relative_to(tools).as_posix()}",
                "remote_path": str(NEW_TOOLS_ROOT / path.relative_to(tools)),
                **ref(path),
            }
        )
    for path in regular_files(SOURCE_ROOT / "manifests"):
        files.append(
            {
                "category": "manifest",
                "logical_path": f"manifests/{path.relative_to(SOURCE_ROOT / 'manifests').as_posix()}",
                "remote_path": str(MANIFESTS_ROOT / path.relative_to(SOURCE_ROOT / "manifests")),
                **ref(path),
            }
        )
    write_json(
        deployment_manifest_path,
        {
            "schema_version": 1,
            "kind": "c2_query_diagnostic_timeout90_v2_deployment_manifest",
            "task_id": TASK_ID,
            "manager_task_revision": MANAGER_REVISION,
            "attempt": "preflight_selfpid_attempt2",
            "remote_roots": {
                "records": str(RECORDS),
                "tools": str(NEW_TOOLS_ROOT),
                "manifests": str(MANIFESTS_ROOT),
                "deployment": str(NEW_DEPLOYMENT_ROOT),
            },
            "deployment_manifest_remote_path": str(NEW_DEPLOYMENT_ROOT / deployment_manifest_path.name),
            "receipt_path": str(RECORDS / f"{ATTEMPT_PREFIX}-deployment-receipt.json"),
            "verifier": {
                "remote_path": str(NEW_DEPLOYMENT_ROOT / verifier.name),
                **ref(verifier),
            },
            "frozen_tools_manifest": {
                "remote_path": str(NEW_TOOLS_ROOT / tools_manifest_path.name),
                **ref(tools_manifest_path),
            },
            "source_identity": {
                "RMBench": "f401f5279c95451eb424ac98b831bab5552b2120",
                "openpi": "bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6",
                "robot_bridge": "e147f600dc4329f330a6e2eb0335150b5b3093a3",
            },
            "transfer_scope": {
                "only_new_attempt_tools_and_deployment_verifier": True,
                "reuse_existing_verified_v2_manifests": True,
                "excluded": ["source trees", "checkpoints", "shared cache", "tools/__pycache__"],
                "v1_and_v2_artifacts_preserved": True,
            },
            "files": files,
        },
    )
    print(
        json.dumps(
            {
                "attempt_root": str(ATTEMPT_ROOT),
                "new_tools_manifest": {"path": str(tools_manifest_path), **ref(tools_manifest_path)},
                "deployment_manifest": {"path": str(deployment_manifest_path), **ref(deployment_manifest_path)},
                "repaired_preflight": {"path": str(preflight), **ref(preflight)},
                "combined_diff": {"path": str(diff_path), **ref(diff_path)},
                "runtime_tool_count": len(runtime_tools),
                "manifest_file_count": len(regular_files(SOURCE_ROOT / "manifests")),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
