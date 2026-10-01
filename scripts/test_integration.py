#!/usr/bin/env python3
"""Run the complete 0.1.0 to 0.2.1 release installation and upgrade checks."""
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

try:
    from scripts.integration_runtime import RuntimeHarness, RuntimeIntegrationError
except ModuleNotFoundError:  # direct ``python scripts/test_integration.py`` execution
    from integration_runtime import RuntimeHarness, RuntimeIntegrationError


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


def create_instance(
    version: str,
    path: Path,
    log: Path,
    *,
    seed: str = "HEAD",
    source_ref: str | None = None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(root_dir() / "scripts" / "create_mam_test.py"),
        "--version",
        version,
        "--root",
        str(path),
        "--seed",
        seed,
    ]
    if source_ref:
        command.extend(("--source-ref", source_ref))
    result = run(command, log=log)
    if result.returncode:
        raise IntegrationError(f"create {path} failed: {result.stderr[-1000:]}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"create returned invalid JSON: {result.stdout[-1000:]}") from exc
    if not isinstance(value, dict) or not value.get("mam") or not isinstance(value.get("fixture"), dict):
        raise IntegrationError("create returned incomplete instance metadata")
    return value


def build_archive(output_root: Path, log: Path, expected_version: str, *, published: bool = False) -> tuple[Path, str]:
    checkout = root_dir()
    ref = f"refs/tags/v{expected_version}" if published else "HEAD"
    # Resolve annotated tags to their commit object.  Archival substitution
    # and installed release metadata identify the commit, never the tag object.
    rev = run(["git", "-C", str(checkout), "rev-parse", f"{ref}^{{commit}}"], log=log)
    if rev.returncode:
        source = f"tag v{expected_version}" if published else "candidate checkout"
        raise IntegrationError(f"{source} is not available in the local repository")
    metadata = run(["git", "-C", str(checkout), "show", f"{rev.stdout.strip()}:multi_agent_manager/release.py"], log=log)
    project = run(["git", "-C", str(checkout), "show", f"{rev.stdout.strip()}:pyproject.toml"], log=log)
    if metadata.returncode or f'RELEASE_VERSION = "{expected_version}"' not in metadata.stdout:
        raise IntegrationError(f"published source does not provide release metadata for {expected_version}")
    if project.returncode or f'version = "{expected_version}"' not in project.stdout:
        raise IntegrationError(f"published source metadata does not select version {expected_version}")
    archive = output_root / "mam-test-install" / "candidate.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    result = run(["git", "-C", str(checkout), "archive", "--format=tar.gz", f"--output={archive}", ref], log=log)
    if result.returncode:
        raise IntegrationError(f"candidate archive failed: {result.stderr[-1000:]}")
    try:
        with tarfile.open(archive, "r:gz") as package:
            release_members = [member for member in package.getmembers() if member.name.endswith("multi_agent_manager/release.py")]
            if len(release_members) != 1:
                raise IntegrationError("candidate archive has no unique release metadata file")
            release_text = package.extractfile(release_members[0]).read().decode("utf-8")
    except (OSError, UnicodeDecodeError, tarfile.TarError, AttributeError) as exc:
        raise IntegrationError(f"candidate archive metadata could not be read: {exc}") from exc
    if f'RELEASE_COMMIT = "{rev.stdout.strip()}"' not in release_text:
        raise IntegrationError("candidate archive did not substitute its selected commit in release metadata")
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


def git_refs(repo: Path) -> dict[str, str]:
    output = git_output(repo, "for-each-ref", "--format=%(refname) %(objectname)")
    return {line.split(" ", 1)[0]: line.split(" ", 1)[1] for line in output.splitlines() if " " in line}


def source_refs(repo: Path) -> dict[str, str]:
    """Snapshot refs owned by this checkout, excluding sibling task branches.

    Multiple MAM tasks share the development repository.  A reviewer or
    producer may advance its own task branch while this run is active; those
    external refs are not writable by this integration process.  Keep the
    candidate branch, main, tags, and remotes in the isolation assertion.
    """

    refs = git_refs(repo)
    current = run(["git", "-C", str(repo), "symbolic-ref", "--quiet", "--short", "HEAD"])
    current_ref = f"refs/heads/{current.stdout.strip()}" if current.returncode == 0 else ""
    return {
        name: value
        for name, value in refs.items()
        if name in {"refs/heads/main", current_ref}
        or name.startswith("refs/remotes/")
        or name.startswith("refs/tags/")
    }


def target_exists(repo: Path, target: str) -> bool:
    return run(["git", "-C", str(repo), "cat-file", "-e", f"{target}^{{commit}}"],).returncode == 0


def verify_instance_data(
    instance: Path,
    metadata: dict[str, Any],
    launcher: Path,
    upgrade_result: dict[str, Any],
    expected_commit: str,
    log: Path,
    *,
    env: dict[str, str] | None = None,
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
    if version.get("version") != "0.2.1":
        raise IntegrationError(f"data version was not migrated in {instance}: {version}")
    if upgrade_result.get("data_version") != "0.2.1":
        raise IntegrationError(f"upgrade result has no 0.2.1 data version in {instance}: {upgrade_result}")
    if upgrade_result.get("program_version") != "0.2.1":
        raise IntegrationError(f"upgrade result has no 0.2.1 program version in {instance}: {upgrade_result}")
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
    event_message = isinstance(events, dict) and any(
        item.get("message") == "retained fixture message" for item in events.values() if isinstance(item, dict)
    )
    history_message = next(
        (item for item in history if isinstance(item, dict) and item.get("message") == "retained fixture message"), None
    )
    if history_message is None or (not event_message and history_message.get("delivery") != "accepted"):
        raise IntegrationError(f"message event/history was lost in {instance}")
    backup = upgrade_result.get("backup")
    if not isinstance(backup, str) or not Path(backup).is_dir():
        raise IntegrationError(f"upgrade backup is missing in {instance}: {backup}")
    if not (Path(backup) / "tasks" / f"{task}.json").is_file():
        raise IntegrationError(f"upgrade backup does not contain the old task record in {instance}")
    status = run([str(launcher), "service", "status"], cwd=instance, env=env, log=log)
    if status.returncode:
        raise IntegrationError(f"service status failed after upgrade in {instance}: {status.stderr[-800:]}")
    status_value = json.loads(status.stdout)
    if not isinstance(status_value, dict) or status_value.get("program_version") != "0.2.1" or status_value.get("data_version") != "0.2.1":
        raise IntegrationError(f"service status omitted migrated versions in {instance}: {status.stdout}")
    return {
        "task": task,
        "data_version": version.get("version"),
        "branch": branch,
        "workspace": str(workspace),
        "manager": manager,
        "history_entries": len(history),
        "event_entries": len(events) if isinstance(events, dict) else 0,
        "message_delivery": "pending" if event_message else history_message.get("delivery"),
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
        "assert result['changed'] and migrations.read_data_version(root)=='0.2.1'\n"
        "print('{\"status\":\"retried\",\"version\":\"'+migrations.read_data_version(root)+'\"}')\n"
    )
    result = run([str(python), "-c", code], cwd=instance, log=log)
    if result.returncode:
        raise IntegrationError(f"interrupted migration retry failed in {instance}: {result.stderr[-1000:]}")
    try:
        value = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"migration retry returned invalid evidence in {instance}") from exc
    if value != {"status": "retried", "version": "0.2.1"}:
        raise IntegrationError(f"migration retry returned incomplete evidence: {value}")
    return value


def verify_source_isolation(
    instances: list[tuple[Path, dict[str, Any]]],
    candidate_commit: str,
    selected_ref: str,
    checkout_head: str,
    baseline_refs: dict[str, dict[str, str]],
    expected_source_refs: dict[str, str],
) -> dict[str, Any]:
    source = root_dir()
    if git_output(source, "rev-parse", "HEAD") != checkout_head:
        raise IntegrationError("candidate checkout HEAD changed during integration")
    if source_refs(source) != expected_source_refs:
        raise IntegrationError("candidate checkout refs changed during integration")
    selected = git_output(source, "rev-parse", f"{selected_ref}^{{commit}}")
    if selected != candidate_commit:
        raise IntegrationError("selected release ref no longer names the archived candidate commit")
    working_tree = run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"]).stdout.strip()
    if working_tree:
        raise IntegrationError(f"candidate checkout gained working-tree changes during integration: {working_tree.splitlines()}")
    origins: dict[str, str] = {}
    for instance, metadata in instances:
        root = Path(metadata["mam_root"])
        origin = run(["git", "-C", str(root), "config", "--get", "remote.origin.url"])
        if origin.returncode:
            raise IntegrationError(f"upgraded instance lost its isolated origin: {instance}")
        origins[instance.name] = origin.stdout.strip()
        current = git_refs(root)
        before = baseline_refs[instance.name]
        allowed = {"refs/heads/project/mam-test"}
        if {key: value for key, value in current.items() if key not in allowed} != {
            key: value for key, value in before.items() if key not in allowed
        }:
            raise IntegrationError(f"non-MAM refs changed in isolated instance {instance}")
    return {
        "candidate_head": candidate_commit,
        "checkout_head": checkout_head,
        "selected_ref": selected_ref,
        "origins": origins,
        "task_roots": [str(path) for path, _ in instances],
        "baseline_refs": baseline_refs,
    }


def pipx_install(source: Path, env: dict[str, str], log: Path) -> Path:
    result = run(["pipx", "install", "--force", str(source)], cwd=source, env=env, log=log)
    if result.returncode:
        raise IntegrationError(f"pipx install failed: {result.stderr[-1200:]}")
    launcher = Path(env["PIPX_BIN_DIR"]) / "mam"
    if not launcher.is_file():
        raise IntegrationError(f"pipx launcher missing: {launcher}")
    return launcher


def controlled_job(
    instance: Path,
    metadata: dict[str, Any],
    log: Path,
    *,
    runtime_env: dict[str, str] | None = None,
) -> tuple[subprocess.Popen[bytes], str]:
    """Start and register one owned process using the old installed writer."""

    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    fixture = metadata["fixture"]
    result = run(
        [metadata["mam"], "job", "add", fixture["task"], "--note", "release integration controlled job",
         "--host", "local", "--pid", str(process.pid)],
        cwd=instance,
        env={**(runtime_env or os.environ), "CODEX_THREAD_ID": fixture["worker"]},
        log=log,
    )
    if result.returncode:
        terminate_owned_process(process)
        raise IntegrationError(f"could not register controlled job in {instance}: {result.stderr[-1000:]}")
    try:
        value = json.loads(result.stdout)
        return process, value["id"]
    except (json.JSONDecodeError, KeyError) as exc:
        terminate_owned_process(process)
        raise IntegrationError(f"old job writer returned invalid JSON in {instance}") from exc


def terminate_owned_process(process: subprocess.Popen[bytes]) -> None:
    """Stop an owned process and always reap it, including kill fallback."""

    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


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


def install_candidate(
    instances: list[tuple[Path, dict[str, Any]]], archive: Path, install_root: Path, log: Path,
    *, runtime_env: dict[str, str] | None = None,
) -> tuple[Path, dict[str, Any]]:
    env = {**(runtime_env or os.environ), "MAM_INSTALL_ARCHIVE": str(archive.resolve()), "PIPX_HOME": str(install_root / "pipx"),
           "PIPX_BIN_DIR": str(install_root / "bin"), "HOME": str(install_root / "home")}
    controlled = env.get("MAM_INTEGRATION_RUNTIME") == "controlled"
    if controlled and not Path(env.get("MAM_APP_SERVER_SOCKET", "")).is_socket():
        raise IntegrationError("controlled archive install has no live private App Server endpoint")
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
    install_command = ["bash", str(install_script), "--version", "0.2.1"]
    # One installer regression test intentionally starts an interactive bash
    # session.  Run the real installer under a local pseudo-terminal so that
    # this check observes the same terminal boundary as a user invocation.
    if shutil.which("script"):
        command_text = " ".join(shlex.quote(item) for item in install_command)
        install_command = ["script", "-qefc", command_text, "/dev/null"]
    result = run(install_command, cwd=instances[0][0], env=env, log=log)
    launcher = Path(env["PIPX_BIN_DIR"]) / "mam"
    if not launcher.is_file():
        detail = (result.stderr or result.stdout)[-1500:]
        raise IntegrationError(f"candidate install failed before pipx launcher was available: {detail}")
    if result.returncode:
        transcript = (result.stdout + result.stderr)[-5000:]
        # The real Codex session is a separately reported acceptance gate.  A
        # candidate that completed unit tests, metadata checks and pipx
        # installation remains usable for controlled instance migration.
        marker = "isolated real delivery acceptance failed:"
        if marker not in transcript:
            raise IntegrationError(f"candidate install failed: {transcript[-1500:]}")
        return launcher, {
            "status": "failed",
            "kind": "real-codex-delivery",
            "error": transcript[transcript.rfind(marker):].strip(),
            "controlled_migration_allowed": True,
        }
    if controlled:
        return launcher, {
            "status": "failed",
            "kind": "real-codex-delivery",
            "error": "not accepted: installer probe used the controlled App Server endpoint; no real Codex delivery was exercised",
            "controlled_migration_allowed": True,
        }
    return launcher, {"status": "passed", "kind": "real-codex-delivery"}


def installer_runtime_environment(
    runtimes: list[RuntimeHarness], instances: list[tuple[Path, dict[str, Any]]]
) -> dict[str, str] | None:
    """Use the private App Server during install only when explicitly requested."""

    if os.environ.get("MAM_INTEGRATION_RUNTIME") != "controlled":
        return None
    return {
        **runtimes[0].env,
        "CODEX_THREAD_ID": instances[0][1]["fixture"]["worker"],
    }


def verify_installed_candidate(install_root: Path, expected_version: str, expected_commit: str, log: Path) -> dict[str, str]:
    interpreters = sorted((install_root / "pipx" / "venvs").glob("*/bin/python"))
    if len(interpreters) != 1:
        raise IntegrationError(f"installed candidate interpreter is ambiguous: {interpreters}")
    code = (
        "from multi_agent_manager import release\n"
        "print(release.RELEASE_VERSION)\n"
        "print(release.RELEASE_COMMIT)\n"
    )
    # The integration runner itself lives in this checkout.  Do not let its
    # cwd or PYTHONPATH shadow the package installed in the isolated pipx venv.
    isolated_env = os.environ.copy()
    isolated_env.pop("PYTHONPATH", None)
    result = run([str(interpreters[0]), "-c", code], cwd=install_root, env=isolated_env, log=log)
    if result.returncode:
        raise IntegrationError(f"installed candidate metadata query failed: {result.stderr[-800:]}")
    values = result.stdout.strip().splitlines()
    if values != [expected_version, expected_commit]:
        raise IntegrationError(f"installed candidate metadata mismatch: {values!r}")
    return {"version": values[0], "commit": values[1], "python": str(interpreters[0])}


def verify_task(
    instance: Path, launcher: Path, fixture: dict[str, Any], log: Path, *, env: dict[str, str] | None = None
) -> None:
    task = fixture.get("task")
    if not task:
        raise IntegrationError(f"fixture did not report a task for {instance}")
    result = run([str(launcher), "task", "status", str(task)], cwd=instance, env=env, log=log)
    if result.returncode:
        raise IntegrationError(f"task was not readable after upgrade in {instance}: {result.stderr[-700:]}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"task status returned invalid JSON in {instance}") from exc
    if value.get("id") != task:
        raise IntegrationError(f"task status returned an unexpected task in {instance}")


def upgrade(
    instance: Path, launcher: Path, log: Path, *, env: dict[str, str] | None = None
) -> dict[str, Any]:
    result = run([str(launcher), "service", "upgrade"], cwd=instance, env=env, log=log)
    if result.returncode:
        raise IntegrationError(f"service upgrade failed for {instance}: {result.stderr[-1500:]}")
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"service upgrade returned invalid JSON in {instance}") from exc
    if not isinstance(output, dict):
        raise IntegrationError(f"service upgrade returned an unexpected result in {instance}")
    return output


def integration(
    root: Path,
    from_version: str,
    to_version: str,
    keep: bool,
    *,
    published: bool = False,
) -> tuple[int, dict[str, Any]]:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    results = root / "integration-results"
    results.mkdir(parents=True, exist_ok=True)
    log = results / "integration.log"
    outcome: dict[str, Any] = {"root": str(root), "from": from_version, "to": to_version, "scenarios": []}
    owned: list[Path] = []
    processes: list[subprocess.Popen[bytes]] = []
    runtimes: list[RuntimeHarness] = []
    try:
        if (from_version, to_version) != ("0.1.0", "0.2.1"):
            raise IntegrationError("only the complete 0.1.0 -> 0.2.1 chain is supported")
        selected_ref = f"refs/tags/v{to_version}" if published else "HEAD"
        checkout_head = git_output(root_dir(), "rev-parse", "HEAD")
        if published:
            selected_check = run(["git", "-C", str(root_dir()), "rev-parse", f"{selected_ref}^{{commit}}"], log=log)
            if selected_check.returncode:
                raise IntegrationError(f"published source tag v{to_version} is not available in the local repository")
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
        for instance, metadata in instances:
            runtimes.append(RuntimeHarness(instance, metadata, log))
        jobs: list[tuple[Path, dict[str, Any], subprocess.Popen[bytes], str]] = []
        for (instance, metadata), runtime in zip(instances, runtimes):
            process, job_id = controlled_job(instance, metadata, log, runtime_env=runtime.env)
            processes.append(process)
            jobs.append((instance, metadata, process, job_id))
        old_daemons = []
        for (instance, metadata), runtime in zip(instances, runtimes):
            old_daemons.append(runtime.start(Path(metadata["mam"])))
            if not runtime.status(Path(metadata["mam"])).get("running"):
                raise IntegrationError(f"old daemon did not report running in {instance}")
        for (instance, metadata), runtime in zip(instances, runtimes):
            stopped = runtime.stop(Path(metadata["mam"]))
            if not stopped.get("stopped"):
                raise IntegrationError(f"old daemon did not stop in {instance}")
        # The second process exits during the real daemon-stopped window; the
        # first remains alive across package installation and upgrade.
        terminate_owned_process(jobs[1][2])
        outcome["scenarios"].append({
            "name": "controlled-jobs-and-daemon-stop",
            "status": "passed",
            "codex": "simulated",
            "old_daemons": old_daemons,
        })
        baseline_refs = {instance.name: git_refs(Path(metadata["mam_root"])) for instance, metadata in instances}
        source_ref_snapshot = source_refs(root_dir())
        archive, commit = build_archive(root, log, to_version, published=published)
        outcome["candidate"] = {"archive": str(archive), "commit": commit}
        if target_exists(Path(instances[0][1]["mam_root"]), commit):
            raise IntegrationError("old instance unexpectedly already contains the candidate commit")
        outcome["scenarios"].append({"name": "target-commit-missing-before-upgrade", "status": "passed", "instance": instances[0][0].name})
        install_root = root / "mam-test-install"
        owned.append(install_root)
        install_env = installer_runtime_environment(runtimes, instances)
        launcher, real_delivery = install_candidate(
            instances, archive, install_root, log, runtime_env=install_env
        )
        outcome["real_delivery"] = real_delivery
        outcome["installed_metadata"] = verify_installed_candidate(install_root, to_version, commit, log)
        outcome["scenarios"].append({
            "name": "pipx-install-and-update",
            "status": "passed",
            "launcher": str(launcher),
            "real_delivery": real_delivery["status"],
        })
        # Keep a real 0.2.0 writer in the default run so the no-op 0.2.0 to
        # 0.2.1 migration is exercised separately from the full 0.1 chain.
        prior_path = root / "mam-test-0.2.0"
        prior = create_instance("0.2.0", prior_path, log, seed="refs/tags/v0.2.0", source_ref="refs/tags/v0.2.0")
        owned.append(prior_path)
        prior_upgrade = upgrade(prior_path, launcher, log)
        if prior_upgrade.get("data_version") != "0.2.1" or prior_upgrade.get("status") != "upgraded":
            raise IntegrationError(f"0.2.0 -> 0.2.1 upgrade was not applied: {prior_upgrade}")
        outcome["scenarios"].append({
            "name": "upgrade:0.2.0-to-0.2.1",
            "status": "passed",
            "data_version": prior_upgrade.get("data_version"),
        })
        upgrade_results: list[dict[str, Any]] = []
        conflict_file = induce_git_conflict(instances[0][0], root_dir(), commit, log)
        conflict_error = None
        try:
            upgrade(instances[0][0], launcher, log, env=runtimes[0].env)
        except IntegrationError as exc:
            conflict_error = str(exc)
        if not conflict_error or "merge" not in conflict_error.lower():
            raise IntegrationError("Git conflict scenario did not fail at the merge boundary")
        conflict_backups = sorted(Path(instances[0][1]["mam_root"]).glob(".local.backup-*"))
        if not conflict_backups or (Path(instances[0][1]["mam_root"]) / ".local" / "data-version.json").exists():
            raise IntegrationError("failed Git upgrade did not retain backup or baseline data version")
        resolve_git_conflict(instances[0][0], conflict_file, commit, log)
        outcome["scenarios"].append({"name": "git-conflict-and-retry", "status": "passed", "path": conflict_file})
        for (instance, metadata), runtime in zip(instances, runtimes):
            result = upgrade(instance, launcher, log, env=runtime.env)
            upgrade_results.append(result)
            verify_task(instance, launcher, metadata["fixture"], log, env=runtime.env)
            evidence = verify_instance_data(instance, metadata, launcher, result, commit, log, env=runtime.env)
            outcome.setdefault("instance_evidence", {})[instance.name] = evidence
            outcome["scenarios"].append({"name": f"upgrade:{instance.name}", "status": "passed", "data": evidence})
            if instance == instances[0][0]:
                other_root = Path(instances[1][1]["mam_root"])
                if git_refs(other_root) != baseline_refs[instances[1][0].name]:
                    raise IntegrationError("upgrading the first instance changed the second instance refs")
            repeat = upgrade(instance, launcher, log, env=runtime.env)
            if repeat.get("status") != "up-to-date":
                raise IntegrationError(f"repeated upgrade was not idempotent for {instance}")
        outcome["upgrade_results"] = upgrade_results
        outcome["scenarios"].append({"name": "repeat-upgrade-and-backup", "status": "passed"})
        missing_result = None
        try:
            upgrade(no_origin_path, launcher, log, env=runtimes[0].env)
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
        restored = upgrade(instances[0][0], launcher, log, env=runtimes[0].env)
        if restored.get("data_version") != "0.2.1" or restored.get("status") != "upgraded":
            raise IntegrationError(f"backup restore did not complete a fresh migration: {restored}")
        outcome["scenarios"].append({"name": "backup-restore-and-retry", "status": "passed", "backup": str(first_backup)})
        runtime_starts = []
        for (instance, metadata), runtime in zip(instances, runtimes):
            runtime_starts.append(runtime.start(launcher))
            if not runtime.status(launcher).get("running"):
                raise IntegrationError(f"candidate daemon did not report running in {instance}")
        running_job = runtimes[0].wait_for_job_state(jobs[0][3], "running", timeout=60)
        exited_job = runtimes[1].wait_for_job_state(jobs[1][3], "exited", timeout=60)
        notification = runtimes[1].verify_notification(jobs[1][3], timeout=60)
        job_states = [running_job, exited_job]
        outcome["job_states"] = job_states
        outcome["runtime"] = {
            "candidate_daemons": runtime_starts,
            "running_job": running_job,
            "exited_job": exited_job,
            "notification": notification,
            "codex": "controlled",
        }
        for runtime in runtimes:
            if not runtime.stop(launcher).get("stopped"):
                raise IntegrationError("candidate daemon did not stop after notification")
        outcome["scenarios"].append({"name": "restart-and-job-notification", "status": "passed", "codex": "controlled"})
        new_instance = root / "mam-test-new"
        outcome["new_instance"] = create_instance(to_version, new_instance, log, seed=commit, source_ref=selected_ref if published else None)
        owned.append(new_instance)
        outcome["scenarios"].append({"name": "first-use-new-instance", "status": "passed"})
        outcome["source_isolation"] = verify_source_isolation(
            instances, commit, selected_ref, checkout_head, baseline_refs, source_ref_snapshot
        )
        outcome["scenarios"].append({"name": "candidate-and-instance-isolation", "status": "passed"})
    except (IntegrationError, OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
        outcome["error"] = str(exc)
        outcome["scenarios"].append({"name": "integration", "status": "failed", "error": str(exc)})
    finally:
        for runtime in runtimes:
            try:
                runtime.close()
            except (RuntimeIntegrationError, OSError) as exc:
                outcome.setdefault("cleanup_errors", []).append(str(exc))
        for process in processes:
            terminate_owned_process(process)
        if not keep:
            for path in owned:
                if path.exists():
                    shutil.rmtree(path)
        (results / "result.json").write_text(json.dumps(outcome, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if "error" not in outcome and outcome.get("real_delivery", {}).get("status") != "passed":
        outcome["error"] = "real Codex delivery acceptance did not pass"
    if outcome.get("cleanup_errors"):
        outcome.setdefault("error", "integration cleanup failed")
    # Rewrite after the final gate/cleanup status is known; result.json must
    # agree with the process exit code even when controlled migration passed.
    (results / "result.json").write_text(json.dumps(outcome, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return (0 if "error" not in outcome else 1), outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("../tmp"))
    parser.add_argument("--from", dest="from_version", default="0.1.0")
    parser.add_argument("--to", dest="to_version", default=None, help="published target version; omit to test current checkout")
    parser.add_argument("--keep", action="store_true", help="retain created instances for diagnosis")
    args = parser.parse_args(argv)
    explicit_target = args.to_version is not None
    target_version = args.to_version or "0.2.1"
    code, outcome = integration(args.root, args.from_version, target_version, args.keep, published=explicit_target)
    print(json.dumps(outcome, indent=2, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
