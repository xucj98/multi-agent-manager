#!/usr/bin/env python3
"""Run the 0.1.0 to 0.2.0 release installation and upgrade checks."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tarfile
from typing import Any


class IntegrationError(RuntimeError):
    pass


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def run(argv: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, log: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)
    if log is not None:
        with log.open("a", encoding="utf-8") as stream:
            stream.write("$ " + " ".join(str(x) for x in argv) + "\n")
            stream.write(result.stdout)
            stream.write(result.stderr)
            stream.write(f"[exit {result.returncode}]\n")
    return result


def create_instance(version: str, path: Path, log: Path, *, seed: str = "HEAD") -> dict[str, Any]:
    result = run([sys.executable, str(root_dir() / "scripts" / "create_mam_test.py"), "--version", version, "--root", str(path), "--seed", seed], log=log)
    if result.returncode:
        raise IntegrationError(f"create {path} failed: {result.stderr[-1000:]}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"create returned invalid JSON: {result.stdout[-1000:]}") from exc
    if not isinstance(value, dict) or not value.get("mam") or not isinstance(value.get("fixture"), dict):
        raise IntegrationError("create returned incomplete instance metadata")
    return value


def build_archive(output_root: Path, log: Path) -> tuple[Path, str]:
    checkout = root_dir()
    rev = run(["git", "-C", str(checkout), "rev-parse", "HEAD"], log=log)
    if rev.returncode:
        raise IntegrationError("candidate checkout is not a Git repository")
    archive = output_root / "mam-test-install" / "candidate.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    result = run(["git", "-C", str(checkout), "archive", "--format=tar.gz", f"--output={archive}", "HEAD"], log=log)
    if result.returncode:
        raise IntegrationError(f"candidate archive failed: {result.stderr[-1000:]}")
    return archive, rev.stdout.strip()


def old_source(install_root: Path) -> Path:
    # The old writer is part of this repository's immutable test fixture.  Do
    # not read the currently running manager's task archive: that would make
    # the one-click test depend on another instance's layout and retention.
    snapshot = root_dir() / "tests" / "baselines" / "0.1.0" / "multi_agent_manager"
    if not snapshot.is_dir():
        raise IntegrationError(f"archived 0.1.0 source baseline missing: {snapshot}")
    hashes = snapshot.parent / "package_hashes.txt"
    if not hashes.is_file():
        raise IntegrationError(f"archived 0.1.0 package hash manifest missing: {hashes}")
    expected: dict[str, str] = {}
    for line in hashes.read_text(encoding="utf-8").splitlines():
        if line == "New package files:":
            break
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            expected[parts[1]] = parts[0]
    for name, digest in expected.items():
        path = snapshot / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise IntegrationError(f"archived 0.1.0 baseline hash mismatch: {path}")
    source = install_root / "old-source"
    package = source / "multi_agent_manager"
    package.mkdir(parents=True)
    for item in snapshot.iterdir():
        shutil.copy2(item, package / item.name)
    (source / "pyproject.toml").write_text(
        "[build-system]\nrequires=['flit_core>=3.11,<5']\nbuild-backend='flit_core.buildapi'\n"
        "[project]\nname='multi-agent-manager'\nversion='0.1.0'\ndescription='archived MAM fixture'\nrequires-python='>=3.10'\n"
        "[project.scripts]\nmam='multi_agent_manager.cli:main'\n", encoding="utf-8")
    return source


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntegrationError(f"{label} is not a JSON object: {path}")
    return value


def git_output(repo: Path, *args: str) -> str:
    result = run(["git", "-C", str(repo), *args])
    if result.returncode:
        raise IntegrationError(f"git {' '.join(args)} failed in {repo}: {result.stderr[-800:]}")
    return result.stdout.strip()


def target_exists(repo: Path, target: str) -> bool:
    return run(["git", "-C", str(repo), "cat-file", "-e", f"{target}^{{commit}}"],).returncode == 0


def verify_instance_data(
    instance: Path,
    metadata: dict[str, Any],
    launcher: Path,
    upgrade_result: dict[str, Any],
    expected_commit: str,
    log: Path,
) -> dict[str, Any]:
    """Check durable records, publication, workspace and the merged release."""

    target = metadata.get("fixture")
    if not isinstance(target, dict):
        raise IntegrationError(f"fixture metadata is missing for {instance}")
    task = target.get("task")
    manager = target.get("manager")
    if not isinstance(task, str) or not isinstance(manager, str):
        raise IntegrationError(f"fixture metadata has no task/manager for {instance}")
    root = Path(metadata["mam_root"])
    version = read_json(root / ".local" / "data-version.json", "data version")
    if version.get("version") != "0.2.0":
        raise IntegrationError(f"data version was not migrated in {instance}: {version}")
    if upgrade_result.get("data_version") != "0.2.0":
        raise IntegrationError(f"upgrade result has no 0.2.0 data version in {instance}: {upgrade_result}")
    if upgrade_result.get("program_version") != "0.2.0":
        raise IntegrationError(f"upgrade result has no 0.2.0 program version in {instance}: {upgrade_result}")
    if upgrade_result.get("status") != "upgraded":
        raise IntegrationError(f"first upgrade did not migrate {instance}: {upgrade_result}")
    target_result = upgrade_result.get("target_commit")
    if target_result != expected_commit or len(target_result or "") != 40:
        raise IntegrationError(f"upgrade target commit is not the archive HEAD in {instance}: {upgrade_result}")
    if not isinstance(upgrade_result.get("target_tag"), str) or not upgrade_result["target_tag"]:
        raise IntegrationError(f"upgrade result omitted release tag in {instance}")
    branch = git_output(root, "branch", "--show-current")
    if branch != "project/mam-test":
        raise IntegrationError(f"MAM_BRANCH changed during upgrade in {instance}: {branch}")
    if run(["git", "-C", str(root), "merge-base", "--is-ancestor", expected_commit, branch]).returncode:
        raise IntegrationError(f"release commit was not merged into MAM_BRANCH in {instance}")

    record = read_json(root / ".local" / "tasks" / f"{task}.json", "task record")
    if record.get("id") != task or record.get("agent") != target.get("worker"):
        raise IntegrationError(f"task binding changed during upgrade in {instance}: {record}")
    repos = record.get("repos")
    repo_record = repos.get("sample-repo") if isinstance(repos, dict) else None
    if not isinstance(repo_record, dict) or repo_record.get("state") != "ready":
        raise IntegrationError(f"workspace registration was not retained in {instance}: {record}")
    workspace = Path(record.get("workspace", "")) / "sample-repo"
    if not workspace.is_dir() or git_output(workspace, "branch", "--show-current") != f"task/{task}":
        raise IntegrationError(f"workspace branch was not retained in {instance}: {workspace}")

    task_path = f".tasks/{task}/task.md"
    report_path = f".tasks/{task}/report.md"
    attachment_path = f".tasks/{task}/files/fixture.txt"
    for path, marker in ((task_path, None), (report_path, "Published"), (attachment_path, "fixture")):
        result = run(["git", "-C", str(root), "show", f"{branch}:{path}"])
        if result.returncode or (marker and marker not in result.stdout):
            raise IntegrationError(f"published {path} was not retained in {instance}")
    draft = root / ".tasks" / task / "report.md"
    if not draft.is_file() or "draft retained before upgrade" not in draft.read_text(encoding="utf-8"):
        raise IntegrationError(f"report draft was not retained in {instance}")

    service_manager = read_json(root / ".local" / "service" / "manager.json", "service manager")
    state = read_json(root / ".local" / "service" / "state.json", "service state")
    if service_manager.get("manager") != manager or state.get("manager") != manager:
        raise IntegrationError(f"recorded Manager changed during upgrade in {instance}")
    history = state.get("history")
    events = state.get("events")
    if not isinstance(history, list) or not any(item.get("message") == "retained fixture message" for item in history if isinstance(item, dict)):
        raise IntegrationError(f"message delivery history was lost in {instance}")
    if not isinstance(events, dict) or not any(item.get("message") == "retained fixture message" for item in events.values() if isinstance(item, dict)):
        raise IntegrationError(f"pending message event was lost in {instance}")
    backup = upgrade_result.get("backup")
    if not isinstance(backup, str) or not Path(backup).is_dir():
        raise IntegrationError(f"upgrade backup is missing in {instance}: {backup}")
    if not (Path(backup) / "tasks" / f"{task}.json").is_file():
        raise IntegrationError(f"upgrade backup does not contain the old task record in {instance}")
    status = run([str(launcher), "service", "status"], cwd=instance, log=log)
    if status.returncode:
        raise IntegrationError(f"service status failed after upgrade in {instance}: {status.stderr[-800:]}")
    status_value = json.loads(status.stdout)
    if not isinstance(status_value, dict) or status_value.get("program_version") != "0.2.0" or status_value.get("data_version") != "0.2.0":
        raise IntegrationError(f"service status omitted migrated versions in {instance}: {status.stdout}")
    return {
        "task": task,
        "data_version": version.get("version"),
        "branch": branch,
        "workspace": str(workspace),
        "manager": manager,
        "history_entries": len(history),
        "event_entries": len(events),
        "backup": backup,
        "service_status": status_value,
    }


def induce_git_conflict(instance: Path, candidate_checkout: Path, target: str, log: Path) -> str:
    """Create a tracked local edit that conflicts with the release merge."""

    root = instance / "multi-agent-manager"
    for relative in ("CHANGELOG.md", "docs/commands/service.md", "docs/install.md"):
        old = run(["git", "-C", str(root), "show", f"project/mam-test:{relative}"])
        release = run(["git", "-C", str(candidate_checkout), "show", f"{target}:{relative}"])
        if old.returncode == 0 and release.returncode == 0 and old.stdout != release.stdout:
            path = root / relative
            path.write_text("local conflicting release edit\n", encoding="utf-8")
            staged = run(["git", "-C", str(root), "add", relative], log=log)
            committed = run(["git", "-C", str(root), "commit", "-m", "fixture conflict"], log=log)
            if staged.returncode or committed.returncode:
                raise IntegrationError(f"could not create Git conflict in {instance}")
            return relative
    raise IntegrationError(f"could not find a release file suitable for a Git conflict in {instance}")


def resolve_git_conflict(instance: Path, relative: str, target: str, log: Path) -> None:
    root = instance / "multi-agent-manager"
    # service upgrade leaves a normal merge conflict in progress.  Abort it,
    # then record the release version of the conflicting path as an explicit
    # local resolution before retrying the real upgrade command.
    aborted = run(["git", "-C", str(root), "merge", "--abort"], log=log)
    if aborted.returncode:
        raise IntegrationError(f"could not abort the expected Git conflict in {instance}: {aborted.stderr}")
    checked = run(["git", "-C", str(root), "checkout", target, "--", relative], log=log)
    staged = run(["git", "-C", str(root), "add", relative], log=log)
    committed = run(["git", "-C", str(root), "commit", "-m", "resolve release conflict"], log=log)
    if checked.returncode or staged.returncode or committed.returncode:
        raise IntegrationError(f"could not record Git conflict resolution in {instance}")


def restore_backup(instance: Path, backup: Path) -> None:
    root = instance / "multi-agent-manager"
    local = root / ".local"
    if local.exists():
        shutil.rmtree(local)
    shutil.copytree(backup, local, symlinks=True)


def migration_retry(launcher: Path, instance: Path, install_root: Path, log: Path) -> dict[str, Any]:
    """Exercise an interrupted migration and retry against an isolated root."""

    candidates = sorted((install_root / "pipx" / "venvs").glob("*/bin/python"))
    if len(candidates) != 1:
        raise IntegrationError(f"candidate Python is ambiguous in isolated pipx home: {candidates}")
    python = candidates[0]
    code = (
        "from pathlib import Path\n"
        "from multi_agent_manager import migrations\n"
        f"root=Path({str(instance / 'multi-agent-manager')!r})\n"
        "original=migrations.MIGRATIONS[('0.1.0','0.2.0')]\n"
        "calls=[]\n"
        "def fail_once(path):\n"
        "    calls.append(path)\n"
        "    if len(calls) == 1: raise migrations.MigrationError('integration interruption')\n"
        "    return original(path)\n"
        "migrations.MIGRATIONS[('0.1.0','0.2.0')]=fail_once\n"
        "try:\n"
        "    migrations.migrate_data(root)\n"
        "except migrations.MigrationError as exc:\n"
        "    assert 'interruption' in str(exc)\n"
        "else:\n"
        "    raise SystemExit('first migration unexpectedly succeeded')\n"
        "assert not (root/'.local'/'data-version.json').exists()\n"
        "result=migrations.migrate_data(root)\n"
        "assert result['changed'] and migrations.read_data_version(root)=='0.2.0'\n"
        "print('{\"status\":\"retried\",\"version\":\"'+migrations.read_data_version(root)+'\"}')\n"
    )
    result = run([str(python), "-c", code], cwd=instance, log=log)
    if result.returncode:
        raise IntegrationError(f"interrupted migration retry failed in {instance}: {result.stderr[-1000:]}")
    try:
        value = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"migration retry returned invalid evidence in {instance}") from exc
    if value != {"status": "retried", "version": "0.2.0"}:
        raise IntegrationError(f"migration retry returned incomplete evidence: {value}")
    return value


def pipx_install(source: Path, env: dict[str, str], log: Path) -> Path:
    result = run(["pipx", "install", "--force", str(source)], cwd=source, env=env, log=log)
    if result.returncode:
        raise IntegrationError(f"pipx install failed: {result.stderr[-1200:]}")
    launcher = Path(env["PIPX_BIN_DIR"]) / "mam"
    if not launcher.is_file():
        raise IntegrationError(f"pipx launcher missing: {launcher}")
    return launcher


def controlled_job(instance: Path, metadata: dict[str, Any], log: Path) -> tuple[subprocess.Popen[bytes], str]:
    """Start and register one owned process using the old installed writer."""

    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    fixture = metadata["fixture"]
    result = run(
        [metadata["mam"], "job", "add", fixture["task"], "--note", "release integration controlled job",
         "--host", "local", "--pid", str(process.pid)],
        cwd=instance,
        env={**os.environ, "CODEX_THREAD_ID": fixture["worker"]},
        log=log,
    )
    if result.returncode:
        process.terminate()
        raise IntegrationError(f"could not register controlled job in {instance}: {result.stderr[-1000:]}")
    try:
        value = json.loads(result.stdout)
        return process, value["id"]
    except (json.JSONDecodeError, KeyError) as exc:
        process.terminate()
        raise IntegrationError(f"old job writer returned invalid JSON in {instance}") from exc


def verify_job(launcher: Path, instance: Path, job_id: str, log: Path) -> dict[str, Any]:
    result = run([str(launcher), "job", "status", job_id], cwd=instance, log=log)
    if result.returncode:
        raise IntegrationError(f"registered job was lost after upgrade in {instance}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"job status returned invalid JSON in {instance}") from exc
    if value.get("status") not in {"running", "exited", "unknown"}:
        raise IntegrationError(f"job status is malformed in {instance}")
    return value


def install_candidate(instances: list[tuple[Path, dict[str, Any]]], archive: Path, install_root: Path, log: Path) -> Path:
    env = {**os.environ, "MAM_INSTALL_ARCHIVE": str(archive.resolve()), "PIPX_HOME": str(install_root / "pipx"),
           "PIPX_BIN_DIR": str(install_root / "bin"), "HOME": str(install_root / "home")}
    for key in ("PIPX_HOME", "PIPX_BIN_DIR", "HOME"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    pipx_install(old_source(install_root), env, log)
    extracted = install_root / "candidate"
    extracted.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as package:
        package.extractall(extracted)
    entries = [item for item in extracted.iterdir() if item.is_dir()]
    source = entries[0] if len(entries) == 1 and (entries[0] / "scripts" / "install.sh").is_file() else extracted
    install_script = source / "scripts" / "install.sh"
    if not install_script.is_file():
        raise IntegrationError("candidate archive has no scripts/install.sh")
    install_command = ["bash", str(install_script), "--version", "0.2.0"]
    # One installer regression test intentionally starts an interactive bash
    # session.  Run the real installer under a local pseudo-terminal so that
    # this check observes the same terminal boundary as a user invocation.
    if shutil.which("script"):
        command_text = " ".join(shlex.quote(item) for item in install_command)
        install_command = ["script", "-qefc", command_text, "/dev/null"]
    result = run(install_command, cwd=instances[0][0], env=env, log=log)
    if result.returncode:
        raise IntegrationError(f"candidate install failed: {result.stderr[-1500:]}")
    launcher = Path(env["PIPX_BIN_DIR"]) / "mam"
    if not launcher.is_file():
        raise IntegrationError(f"candidate launcher missing after install: {launcher}")
    return launcher


def verify_task(instance: Path, launcher: Path, fixture: dict[str, Any], log: Path) -> None:
    task = fixture.get("task")
    if not task:
        raise IntegrationError(f"fixture did not report a task for {instance}")
    result = run([str(launcher), "task", "status", str(task)], cwd=instance, log=log)
    if result.returncode:
        raise IntegrationError(f"task was not readable after upgrade in {instance}: {result.stderr[-700:]}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"task status returned invalid JSON in {instance}") from exc
    if value.get("id") != task:
        raise IntegrationError(f"task status returned an unexpected task in {instance}")


def upgrade(instance: Path, launcher: Path, log: Path) -> dict[str, Any]:
    result = run([str(launcher), "service", "upgrade"], cwd=instance, log=log)
    if result.returncode:
        raise IntegrationError(f"service upgrade failed for {instance}: {result.stderr[-1500:]}")
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"service upgrade returned invalid JSON in {instance}") from exc
    if not isinstance(output, dict):
        raise IntegrationError(f"service upgrade returned an unexpected result in {instance}")
    return output


def integration(root: Path, from_version: str, to_version: str, keep: bool) -> tuple[int, dict[str, Any]]:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    results = root / "integration-results"
    results.mkdir(parents=True, exist_ok=True)
    log = results / "integration.log"
    outcome: dict[str, Any] = {"root": str(root), "from": from_version, "to": to_version, "scenarios": []}
    owned: list[Path] = []
    processes: list[subprocess.Popen[bytes]] = []
    try:
        if (from_version, to_version) != ("0.1.0", "0.2.0"):
            raise IntegrationError("only the complete 0.1.0 -> 0.2.0 chain is supported")
        instances: list[tuple[Path, dict[str, Any]]] = []
        for index, name in enumerate(("mam-test", "mam-test-2")):
            path = root / name
            # The first instance starts from the last pre-release commit.  It
            # has the origin configured but no target object, so upgrade must
            # fetch the release commit through the normal Git path.
            seed = "9cf9ff9139a269ff49280d43c3b3510e4056df04" if index == 0 else "HEAD"
            metadata = create_instance(from_version, path, log, seed=seed)
            owned.append(path)
            instances.append((path, metadata))
        outcome["scenarios"].append({"name": "create-old-instances", "status": "passed"})
        no_origin_path = root / "mam-test-no-origin"
        no_origin = create_instance(from_version, no_origin_path, log, seed="9cf9ff9139a269ff49280d43c3b3510e4056df04")
        owned.append(no_origin_path)
        no_origin_root = Path(no_origin["mam_root"])
        removed_origin = run(["git", "-C", str(no_origin_root), "remote", "remove", "origin"], log=log)
        if removed_origin.returncode:
            raise IntegrationError(f"could not prepare the no-origin instance: {removed_origin.stderr[-800:]}")
        outcome["scenarios"].append({"name": "create-no-origin-instance", "status": "passed"})
        jobs: list[tuple[Path, dict[str, Any], subprocess.Popen[bytes], str]] = []
        for instance, metadata in instances:
            process, job_id = controlled_job(instance, metadata, log)
            processes.append(process)
            jobs.append((instance, metadata, process, job_id))
        # The second process exits while the service is considered stopped;
        # the first remains alive across package installation and upgrade.
        jobs[1][2].terminate()
        jobs[1][2].wait(timeout=5)
        outcome["scenarios"].append({"name": "controlled-jobs-and-daemon-stop", "status": "passed", "codex": "simulated"})
        archive, commit = build_archive(root, log)
        outcome["candidate"] = {"archive": str(archive), "commit": commit}
        if target_exists(Path(instances[0][1]["mam_root"]), commit):
            raise IntegrationError("old instance unexpectedly already contains the candidate commit")
        outcome["scenarios"].append({"name": "target-commit-missing-before-upgrade", "status": "passed", "instance": instances[0][0].name})
        install_root = root / "mam-test-install"
        owned.append(install_root)
        launcher = install_candidate(instances, archive, install_root, log)
        outcome["scenarios"].append({"name": "pipx-install-and-update", "status": "passed", "launcher": str(launcher)})
        upgrade_results: list[dict[str, Any]] = []
        conflict_file = induce_git_conflict(instances[0][0], root_dir(), commit, log)
        conflict_error = None
        try:
            upgrade(instances[0][0], launcher, log)
        except IntegrationError as exc:
            conflict_error = str(exc)
        if not conflict_error or "merge" not in conflict_error.lower():
            raise IntegrationError("Git conflict scenario did not fail at the merge boundary")
        conflict_backups = sorted(Path(instances[0][1]["mam_root"]).glob(".local.backup-*"))
        if not conflict_backups or (Path(instances[0][1]["mam_root"]) / ".local" / "data-version.json").exists():
            raise IntegrationError("failed Git upgrade did not retain backup or baseline data version")
        resolve_git_conflict(instances[0][0], conflict_file, commit, log)
        outcome["scenarios"].append({"name": "git-conflict-and-retry", "status": "passed", "path": conflict_file})
        for instance, metadata in instances:
            result = upgrade(instance, launcher, log)
            upgrade_results.append(result)
            verify_task(instance, launcher, metadata["fixture"], log)
            evidence = verify_instance_data(instance, metadata, launcher, result, commit, log)
            outcome.setdefault("instance_evidence", {})[instance.name] = evidence
            outcome["scenarios"].append({"name": f"upgrade:{instance.name}", "status": "passed", "data": evidence})
            repeat = upgrade(instance, launcher, log)
            if repeat.get("status") != "up-to-date":
                raise IntegrationError(f"repeated upgrade was not idempotent for {instance}")
        outcome["upgrade_results"] = upgrade_results
        outcome["scenarios"].append({"name": "repeat-upgrade-and-backup", "status": "passed"})
        missing_result = None
        try:
            upgrade(no_origin_path, launcher, log)
        except IntegrationError as exc:
            missing_result = str(exc)
        if not missing_result or "origin" not in missing_result.lower():
            raise IntegrationError("missing-origin upgrade did not fail with an origin diagnostic")
        if target_exists(no_origin_root, commit) or list(no_origin_root.glob(".local.backup-*")):
            raise IntegrationError("missing-origin failure unexpectedly mutated the instance")
        outcome["scenarios"].append({"name": "missing-origin-failure", "status": "passed", "error": missing_result})
        outcome["scenarios"].append({"name": "interrupted-migration-retry", "status": "passed", "evidence": migration_retry(launcher, no_origin_path, install_root, log)})
        first_backup = Path(upgrade_results[0]["backup"])
        restore_backup(instances[0][0], first_backup)
        restored = upgrade(instances[0][0], launcher, log)
        if restored.get("data_version") != "0.2.0" or restored.get("status") != "upgraded":
            raise IntegrationError(f"backup restore did not complete a fresh migration: {restored}")
        outcome["scenarios"].append({"name": "backup-restore-and-retry", "status": "passed", "backup": str(first_backup)})
        job_states = [verify_job(launcher, instance, job_id, log) for instance, _, _, job_id in jobs]
        if job_states[0].get("status") != "running" or job_states[1].get("status") != "exited":
            raise IntegrationError(f"controlled job lifecycle was not retained: {job_states}")
        outcome["job_states"] = job_states
        new_instance = root / "mam-test-new"
        outcome["new_instance"] = create_instance(to_version, new_instance, log)
        owned.append(new_instance)
        outcome["scenarios"].append({"name": "first-use-new-instance", "status": "passed"})
    except (IntegrationError, OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
        outcome["error"] = str(exc)
        outcome["scenarios"].append({"name": "integration", "status": "failed", "error": str(exc)})
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
        if not keep:
            for path in owned:
                if path.exists():
                    shutil.rmtree(path)
        (results / "result.json").write_text(json.dumps(outcome, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return (0 if "error" not in outcome else 1), outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("../tmp"))
    parser.add_argument("--from", dest="from_version", default="0.1.0")
    parser.add_argument("--to", dest="to_version", default="0.2.0")
    parser.add_argument("--keep", action="store_true", help="retain created instances for diagnosis")
    args = parser.parse_args(argv)
    code, outcome = integration(args.root, args.from_version, args.to_version, args.keep)
    print(json.dumps(outcome, indent=2, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
