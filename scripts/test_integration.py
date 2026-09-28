#!/usr/bin/env python3
"""Run the 0.1.0 to 0.2.0 release installation and upgrade checks."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
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
    manager = root_dir().parents[2] / "multi-agent-manager"
    snapshot = manager / ".tasks" / "2eb71f96-e221-4571-9e18-c3352fc7634f" / "files" / "old_source_snapshot"
    if not snapshot.is_dir():
        raise IntegrationError(f"archived 0.1.0 source missing: {snapshot}")
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


def pipx_install(source: Path, env: dict[str, str], log: Path) -> Path:
    result = run(["pipx", "install", "--force", str(source)], cwd=source, env=env, log=log)
    if result.returncode:
        raise IntegrationError(f"pipx install failed: {result.stderr[-1200:]}")
    launcher = Path(env["PIPX_BIN_DIR"]) / "mam"
    if not launcher.is_file():
        raise IntegrationError(f"pipx launcher missing: {launcher}")
    return launcher


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
    result = run(["bash", str(install_script), "--version", "0.2.0"], cwd=instances[0][0], env=env, log=log)
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


def upgrade(instance: Path, launcher: Path, log: Path) -> None:
    result = run([str(launcher), "service", "upgrade"], cwd=instance, log=log)
    if result.returncode:
        raise IntegrationError(f"service upgrade failed for {instance}: {result.stderr[-1500:]}")
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrationError(f"service upgrade returned invalid JSON in {instance}") from exc
    if not isinstance(output, dict):
        raise IntegrationError(f"service upgrade returned an unexpected result in {instance}")


def integration(root: Path, from_version: str, to_version: str, keep: bool) -> tuple[int, dict[str, Any]]:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    results = root / "integration-results"
    results.mkdir(parents=True, exist_ok=True)
    log = results / "integration.log"
    outcome: dict[str, Any] = {"root": str(root), "from": from_version, "to": to_version, "scenarios": []}
    owned: list[Path] = []
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
        archive, commit = build_archive(root, log)
        outcome["candidate"] = {"archive": str(archive), "commit": commit}
        install_root = root / "mam-test-install"
        owned.append(install_root)
        launcher = install_candidate(instances, archive, install_root, log)
        outcome["scenarios"].append({"name": "pipx-install-and-update", "status": "passed", "launcher": str(launcher)})
        for instance, metadata in instances:
            upgrade(instance, launcher, log)
            verify_task(instance, launcher, metadata["fixture"], log)
            outcome["scenarios"].append({"name": f"upgrade:{instance.name}", "status": "passed"})
        new_instance = root / "mam-test-new"
        outcome["new_instance"] = create_instance(to_version, new_instance, log)
        owned.append(new_instance)
        outcome["scenarios"].append({"name": "first-use-new-instance", "status": "passed"})
    except (IntegrationError, OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
        outcome["error"] = str(exc)
        outcome["scenarios"].append({"name": "integration", "status": "failed", "error": str(exc)})
    finally:
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
