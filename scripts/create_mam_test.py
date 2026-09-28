#!/usr/bin/env python3
"""Create one isolated, versioned MAM integration-test instance.

The command only allocates files below ``--root``.  It never starts a
service or a daemon; callers that need those resources own their lifecycle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


TASK_BASELINE = "2eb71f96-e221-4571-9e18-c3352fc7634f"
SUPPORTED = {"0.1.0", "0.2.0"}


class CreateError(RuntimeError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(argv: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, env=env, check=True, text=True, capture_output=True)


def git(repo: Path, *args: str) -> str:
    return run(["git", "-C", str(repo), *args]).stdout.strip()


def _copy_package(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name == "__pycache__":
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def _old_snapshot(repo: Path) -> Path:
    snapshot = repo / "tests" / "baselines" / "0.1.0" / "multi_agent_manager"
    if not snapshot.is_dir():
        raise CreateError(f"0.1.0 archived source is missing: {snapshot}")
    hashes = snapshot.parent / "package_hashes.txt"
    if not hashes.is_file():
        raise CreateError(f"0.1.0 package hashes are missing: {hashes}")
    expected: dict[str, str] = {}
    section = False
    for line in hashes.read_text(encoding="utf-8").splitlines():
        if line.strip() == "Old package files:":
            section = True
            continue
        if section and line.strip() == "New package files:":
            break
        if section and line.strip():
            digest, name = line.split(None, 1)
            expected[name.strip()] = digest
    for name, digest in expected.items():
        path = snapshot / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise CreateError(f"archived 0.1.0 source hash mismatch: {path}")
    return snapshot


def _package_for_version(repo: Path, version: str, destination: Path) -> tuple[Path, str]:
    package = destination / "package"
    if version == "0.1.0":
        source = _old_snapshot(repo)
        _copy_package(source, package / "multi_agent_manager")
        source_commit = "archived-old-source-snapshot"
    elif version == "0.2.0":
        source = repo / "multi_agent_manager"
        if not source.is_dir():
            raise CreateError(f"candidate package source is missing: {source}")
        _copy_package(source, package / "multi_agent_manager")
        try:
            source_commit = git(repo, "rev-parse", "HEAD")
        except subprocess.CalledProcessError:
            source_commit = "working-tree"
    else:
        raise CreateError(f"unsupported test version: {version}")
    return package, source_commit


def _venv_and_launcher(destination: Path, package_parent: Path) -> Path:
    environment = destination / ".venv"
    # The developer checkout itself runs inside a venv.  Creating a nested
    # venv from that interpreter records the inner venv as ``home`` and loses
    # the standard library on this cluster's relocatable Python build.  Use
    # the actual shared base interpreter instead.
    base_python = Path(sys.base_prefix) / "bin" / "python3.10"
    if not base_python.is_file():
        base_python = Path(sys.base_prefix) / "bin" / "python"
    result = subprocess.run([str(base_python), "-m", "venv", "--without-pip", str(environment)], capture_output=True, text=True)
    if result.returncode:
        raise CreateError(f"cannot create isolated test environment: {result.stderr[-1000:]}")
    launcher = environment / "bin" / "mam"
    launcher.write_text(
        "#!/bin/sh\n"
        "exec \"$(dirname -- \"$0\")/python\" - \"$@\" <<'PY'\n"
        f"PACKAGE_PARENT = {str(package_parent)!r}\n"
        "import sys\n"
        "sys.path.insert(0, PACKAGE_PARENT)\n"
        "from multi_agent_manager.cli import main\n"
        "raise SystemExit(main())\n"
        "PY\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    return launcher


def _write_project(project: Path, mam_root: Path, branch: str, seed_repo: Path, seed: str = "HEAD") -> None:
    project.mkdir(parents=True, exist_ok=False)
    mam_root.mkdir(parents=True)
    # Keep the instance branch mergeable with the candidate release whenever
    # this checkout has Git history.  A source archive has no `.git`; fixture
    # unit tests still need a valid standalone instance, so use an ordinary
    # local branch in that case and let release integration provide history.
    if (seed_repo / ".git").exists():
        run(["git", "init", "-q", str(mam_root)])
        run(["git", "-C", str(mam_root), "remote", "add", "origin", str(seed_repo)])
        run(["git", "-C", str(mam_root), "fetch", "-q", "origin", seed])
        run(["git", "-C", str(mam_root), "switch", "-q", "-c", branch, "FETCH_HEAD"])
    else:
        run(["git", "init", "-q", "-b", branch, str(mam_root)])
    git(mam_root, "config", "user.name", "MAM release integration")
    git(mam_root, "config", "user.email", "mam-integration@example.invalid")
    (project / ".mam").mkdir()
    (project / ".mam" / "env.json").write_text(
        json.dumps({"MAM_ROOT": str(mam_root), "PROJECT_ROOT": str(project), "MAM_BRANCH": branch}, indent=2) + "\n",
        encoding="utf-8",
    )
    local = mam_root / ".local"
    hooks = local / "hooks"
    hooks.mkdir(parents=True)
    (local / "README.md").write_text("MAM release integration fixture\n", encoding="utf-8")
    (local / ".gitignore").write_text("tasks/\nservice/\n*.lock\n", encoding="utf-8")
    (hooks / "workspace_add").write_text(
        "#!/usr/bin/env python3\n"
        "import json, subprocess, sys\n"
        "from pathlib import Path\n"
        "context = json.load(sys.stdin)\n"
        "record = next(item for item in context['repos'] if item['name'] == context['repo'])\n"
        "source = Path(record['source'])\n"
        "entry = source / '.local' / 'create_worktree.sh'\n"
        "raise SystemExit(subprocess.run(['bash', str(entry), record['base'], record['branch'], context['task']['workspace']], cwd=source).returncode)\n",
        encoding="utf-8",
    )
    (hooks / "workspace_add").chmod(0o755)
    (mam_root / ".gitignore").write_text(
        ".local/tasks/\n.local/service/\n.local/*.lock\n.local/*-lock\n", encoding="utf-8"
    )
    run(["git", "-C", str(mam_root), "add", "."])
    run(["git", "-C", str(mam_root), "commit", "-q", "-m", "fixture base"])


def _run_fixture(repo: Path, version: str, root: Path, mam_root: Path, package_parent: Path) -> dict:
    fixture = repo / "tests" / "fixtures" / version / "create.py"
    if not fixture.is_file():
        raise CreateError(f"fixture writer is missing: {fixture}")
    command = [
        str(package_parent.parent / ".venv" / "bin" / "python"),
        str(fixture),
        "--version", version,
        "--root", str(root),
        "--project-root", str(root),
        "--mam-root", str(mam_root),
        "--package", str(package_parent),
    ]
    result = subprocess.run(command, cwd=repo, capture_output=True, text=True)
    if result.returncode:
        raise CreateError(f"fixture failed for {version}: {result.stderr[-3000:]}{result.stdout[-1000:]}")
    try:
        value = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise CreateError(f"fixture did not return JSON: {result.stdout[-2000:]}") from exc
    if not isinstance(value, dict):
        raise CreateError("fixture returned an unexpected value")
    return value


def create(version: str, root: Path, *, seed: str = "HEAD") -> dict:
    if version not in SUPPORTED:
        raise CreateError(f"unsupported test version: {version}; choose one of {', '.join(sorted(SUPPORTED))}")
    root = root.expanduser().resolve()
    if root.exists():
        raise CreateError(f"test instance already exists; refusing to modify it: {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    repo = repository_root()
    mam_root = root / "multi-agent-manager"
    branch = "project/mam-test"
    # Check prerequisites before allocating the caller's requested root.
    if version == "0.1.0":
        _old_snapshot(repo)
    try:
        _write_project(root, mam_root, branch, repo, seed)
        version_dir = root / ".versions" / version
        package_parent, source_commit = _package_for_version(repo, version, version_dir)
        launcher = _venv_and_launcher(version_dir, package_parent)
        metadata = {
            "version": version,
            "source_commit": source_commit,
            "package": str(package_parent),
            "program": str(launcher),
            "fixture": str(repo / "tests" / "fixtures" / version / "create.py"),
        }
        (version_dir / "release.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        fixture = _run_fixture(repo, version, root, mam_root, package_parent)
        metadata["fixture_result"] = fixture
        (root / ".mam" / "test-instance.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return {"root": str(root), "version": version, "mam": str(launcher), "mam_root": str(mam_root), "fixture": fixture}
    except Exception:
        # All files below root were allocated by this invocation.  Preserve a
        # pre-existing root via the early refusal above, while ensuring a
        # failed fixture cannot leave a daemon-ready half-instance behind.
        shutil.rmtree(root, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="data/program version, for example 0.1.0")
    parser.add_argument("--root", required=True, type=Path, help="new test PROJECT_ROOT")
    parser.add_argument("--seed", default="HEAD", help="candidate repository commit used as the MAM_ROOT base")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(create(args.version, args.root, seed=args.seed), ensure_ascii=False, indent=2, sort_keys=True))
    except (CreateError, OSError, subprocess.CalledProcessError) as exc:
        print(f"create_mam_test: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
