"""Create the first release's data with the archived 0.1.0 writer.

The fixture is deliberately a small command line program.  The public test
creator copies the archived package into an isolated environment and invokes
this file with that package on ``sys.path``.  Keeping all writes behind the
old CLI makes the fixture useful for detecting accidental changes to the old
on-disk format.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
import uuid


def _invoke(package_parent: Path, project_root: Path, args: list[str], *, agent: str) -> dict:
    """Run one archived CLI operation and return its JSON result."""

    sys.path.insert(0, str(package_parent))
    from multi_agent_manager.cli import main

    output = io.StringIO()
    old = os.environ.get("CODEX_THREAD_ID")
    os.environ["CODEX_THREAD_ID"] = agent
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = main(args, cwd=project_root)
    finally:
        if old is None:
            os.environ.pop("CODEX_THREAD_ID", None)
        else:
            os.environ["CODEX_THREAD_ID"] = old
    text = output.getvalue().strip()
    if result != 0:
        raise RuntimeError(f"archived mam {' '.join(args)} failed: {text[-2000:]}")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"archived mam returned non-JSON for {' '.join(args)}: {text[-2000:]}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"archived mam returned an unexpected value for {' '.join(args)}")
    return value


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _write_repository(project_root: Path) -> Path:
    repo = project_root / "sample-repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "MAM integration fixture")
    _git(repo, "config", "user.email", "mam-fixture@example.invalid")
    (repo / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (repo / "README.md").write_text("fixture repository\n", encoding="utf-8")
    local = repo / ".local"
    local.mkdir()
    entry = local / "create_worktree.sh"
    entry.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "source_root=$(cd -- \"$(dirname -- \"$0\")/..\" && pwd -P)\n"
        "target=\"$3/sample-repo\"\n"
        "git -C \"$source_root\" worktree add -b \"$2\" \"$target\" \"$1\" >/dev/null\n"
        "mkdir -p \"$target/.venv\"\n"
        "printf 'fixture=0.1.0\\n' > \"$target/.venv/fixture-version\"\n",
        encoding="utf-8",
    )
    entry.chmod(0o755)
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fixture base")
    return repo


def _service_history(package_parent: Path, project_root: Path, mam_root: Path, manager: str, task: str) -> None:
    """Seed old service state through its own durable state helpers.

    0.1.0 has no public command for inserting an already delivered message.
    Calling its state writer keeps the JSON layout and timestamps owned by the
    archived implementation while giving migration a realistic history.
    """

    sys.path.insert(0, str(package_parent))
    from multi_agent_manager import cli, wake_runtime

    config = cli.project_config(project_root)
    store = cli.Store(config)
    wake_runtime._record_manager(store, manager, source="fixture")
    state = wake_runtime._load_state(store)
    message_id = str(uuid.uuid4())
    event = {
        "signature": message_id,
        "kind": "message",
        "recipient": manager,
        "sender": str(uuid.uuid4()),
        "sender_path": "/root/fixture",
        "sender_tree": str(uuid.uuid4()),
        "task": task,
        "message": "retained fixture message",
        "defer": True,
        "created_at": "2024-01-01T00:00:00+00:00",
        "delivery": "accepted",
        "attempts": 1,
        "next_attempt_at": 0.0,
        "turn_id": "fixture-turn",
    }
    state.setdefault("history", []).append({**event, "resolved_at": "2024-01-01T00:00:01+00:00", "resolution": "accepted"})
    state.setdefault("events", {})[message_id] = {
        **event,
        "delivery": "pending",
        "attempts": 0,
    }
    state["manager"] = manager
    wake_runtime._save_state(store, state)


def _publish_attachment(package_parent: Path, project_root: Path, mam_root: Path, task: str) -> None:
    """Publish the old fixture's attachment with the archived Git helpers.

    The archived 0.1.0 CLI publishes task/report documents but has no public
    files publication command.  Keep the old CLI as the task/report writer,
    then use its Store/Git primitives to create the historical files tree.
    """

    sys.path.insert(0, str(package_parent))
    from multi_agent_manager import cli

    store = cli.Store(cli.project_config(project_root))
    parent = cli.head(store.root, store.branch)
    attachment = store.logs / task / "files" / "fixture.txt"
    path = f".tasks/{task}/files/fixture.txt"
    with tempfile.TemporaryDirectory(prefix="old-file-publish-") as temporary:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(temporary) / "index")}
        cli.git(store.root, "read-tree", parent, env=env)
        blob = cli.git(store.root, "hash-object", "-w", "--stdin", input=attachment.read_bytes()).stdout.decode().strip()
        cli.git(store.root, "update-index", "--add", "--cacheinfo", "100644", blob, path, env=env)
        tree = cli.git(store.root, "write-tree", env=env).stdout.decode().strip()
        commit = cli.git(
            store.root, "commit-tree", tree, "-p", parent, "-m", f"Publish {task} fixture attachment"
        ).stdout.decode().strip()
        cli.git(store.root, "update-ref", f"refs/heads/{store.branch}", commit, parent)
        # Keep the checkout index aligned with the branch updated above.  The
        # old report draft remains a working-tree edit, while the attachment
        # is now an ordinary tracked publication for the later release merge.
        cli.git(store.root, "read-tree", store.branch)


def create(*, project_root: Path, mam_root: Path, package_parent: Path, version: str = "0.1.0") -> dict:
    project_root = project_root.resolve()
    mam_root = mam_root.resolve()
    repo = _write_repository(project_root)
    manager = str(uuid.uuid4())
    worker = str(uuid.uuid4())
    task_result = _invoke(package_parent, project_root, ["task", "create", "--title", "archived 0.1.0 fixture"], agent=manager)
    task = task_result["id"]
    _invoke(package_parent, project_root, ["task", "bind", task, "--agent", worker], agent=manager)
    _invoke(package_parent, project_root, ["workspace", "add", task, "--repo", "sample-repo", "--base", _git(repo, "rev-parse", "HEAD")], agent=worker)

    task_file = mam_root / ".tasks" / task / "task.md"
    report_file = mam_root / ".tasks" / task / "report.md"
    files = mam_root / ".tasks" / task / "files"
    files.mkdir(parents=True, exist_ok=True)
    (files / "fixture.txt").write_text("archived fixture attachment\n", encoding="utf-8")
    _invoke(package_parent, project_root, ["task", "publish", task, "--file", "task"], agent=manager)
    report_file.write_text("# archived fixture report\n\nPublished by 0.1.0.\n", encoding="utf-8")
    _invoke(package_parent, project_root, ["task", "publish", task, "--file", "report"], agent=manager)
    _publish_attachment(package_parent, project_root, mam_root, task)
    # Leave a real draft behind so upgrade checks both published and working data.
    report_file.write_text(report_file.read_text(encoding="utf-8") + "draft retained before upgrade\n", encoding="utf-8")

    # Register the fixture process itself.  It is running while this writer is
    # active and naturally becomes an exited job once the creator returns.
    job = _invoke(
        package_parent,
        project_root,
        ["job", "add", task, "--note", "archived fixture process", "--host", "local", "--pid", str(os.getpid())],
        agent=worker,
    )
    _service_history(package_parent, project_root, mam_root, manager, task)
    return {
        "version": version,
        "task": task,
        "manager": manager,
        "worker": worker,
        "job": job.get("id"),
        "repository": str(repo),
        "published_task": str(task_file),
        "published_report": str(report_file),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="test project root")
    parser.add_argument("--mam-root", type=Path, help="MAM_ROOT (defaults to ROOT/multi-agent-manager)")
    parser.add_argument("--project-root", type=Path, help="PROJECT_ROOT (defaults to ROOT)")
    parser.add_argument("--package", required=True, type=Path, help="parent containing archived package")
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args(argv)
    project = (args.project_root or args.root).resolve()
    mam_root = (args.mam_root or project / "multi-agent-manager").resolve()
    result = create(project_root=project, mam_root=mam_root, package_parent=args.package.resolve(), version=args.version)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
