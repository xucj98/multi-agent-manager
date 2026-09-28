"""Write a small current-release fixture through the current MAM CLI."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


def invoke(package_parent: Path, project_root: Path, args: list[str], agent: str) -> dict:
    sys.path.insert(0, str(package_parent))
    from multi_agent_manager.cli import main
    output = io.StringIO()
    old = os.environ.get("CODEX_THREAD_ID")
    os.environ["CODEX_THREAD_ID"] = agent
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = main(args, cwd=project_root)
    finally:
        if old is None:
            os.environ.pop("CODEX_THREAD_ID", None)
        else:
            os.environ["CODEX_THREAD_ID"] = old
    text = output.getvalue().strip()
    if code:
        raise RuntimeError(f"current mam {' '.join(args)} failed: {text[-2000:]}")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise RuntimeError("current mam returned an unexpected fixture value")
    return value


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def create(*, project_root: Path, mam_root: Path, package_parent: Path, version: str = "0.2.0") -> dict:
    repo = project_root / "sample-repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    git(repo, "config", "user.name", "MAM integration fixture")
    git(repo, "config", "user.email", "mam-fixture@example.invalid")
    (repo / "README.md").write_text("current fixture repository\n", encoding="utf-8")
    local = repo / ".local"
    local.mkdir()
    entry = local / "create_worktree.sh"
    entry.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        "source_root=$(cd -- \"$(dirname -- \"$0\")/..\" && pwd -P)\n"
        "target=\"$3/sample-repo\"\n"
        "git -C \"$source_root\" worktree add -b \"$2\" \"$target\" \"$1\" >/dev/null\n",
        encoding="utf-8",
    )
    entry.chmod(0o755)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "fixture base")
    manager = str(uuid.uuid4())
    worker = str(uuid.uuid4())
    task = invoke(package_parent, project_root, ["task", "create", "--title", "current 0.2.0 fixture"], manager)
    task_id = task["id"]
    # The release fixture runs without a native Codex App Server session.  Use
    # the current release's Store writer for the initial executor identity; a
    # real ``task start`` is exercised by the integration harness itself.
    sys.path.insert(0, str(package_parent))
    from multi_agent_manager import cli
    config = cli.project_config(project_root)
    store = cli.Store(config)
    record = store.read(task_id, writable=True)
    record["agent"] = worker
    record["identity"] = {"path": "/root/fixture", "tree_root": str(uuid.uuid4())}
    store.write(record)
    invoke(package_parent, project_root, ["workspace", "add", task_id, "--repo", "sample-repo", "--base", git(repo, "rev-parse", "HEAD")], worker)
    files = mam_root / ".tasks" / task_id / "files"
    files.mkdir(parents=True, exist_ok=True)
    (files / "fixture.txt").write_text("current fixture attachment\n", encoding="utf-8")
    invoke(package_parent, project_root, ["task", "publish", task_id], manager)
    report = mam_root / ".tasks" / task_id / "report.md"
    report.write_text("# current fixture report\n", encoding="utf-8")
    invoke(package_parent, project_root, ["task", "report", task_id], manager)
    report.write_text(report.read_text(encoding="utf-8") + "draft retained before upgrade\n", encoding="utf-8")
    return {"version": version, "task": task_id, "manager": manager, "worker": worker, "repository": str(repo)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--mam-root", type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--version", default="0.2.0")
    args = parser.parse_args(argv)
    project = (args.project_root or args.root).resolve()
    mam_root = (args.mam_root or project / "multi-agent-manager").resolve()
    print(json.dumps(create(project_root=project, mam_root=mam_root, package_parent=args.package.resolve(), version=args.version), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
