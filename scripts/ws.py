#!/usr/bin/env python3
"""Conservative lifecycle registry for existing Git worktree workspaces."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def primary_checkout(here: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(here), "worktree", "list", "--porcelain"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    paths = [Path(line[9:]).resolve() for line in result.stdout.splitlines() if line.startswith("worktree ")]
    return paths[0] if paths else here


HERE = Path(__file__).resolve().parents[1]
STABLE_REPO = primary_checkout(HERE)
DEFAULT_STATE = STABLE_REPO / ".local" / "tasks"
DEFAULT_ROOT = STABLE_REPO.parent / "workspace"
SAFE_TEMP = {".venv", "temp"}
TASK_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
SHA_RE = re.compile(r"[0-9a-fA-F]{7,64}$")


class Error(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def task_name(value: str) -> str:
    if not TASK_RE.fullmatch(value) or ".." in value:
        raise Error("task must be a short identifier without '..' or path separators")
    return value


def text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 160 or any(ord(char) < 32 for char in value):
        raise Error(f"{field} must be a non-empty plain label")
    return value


def absolute(value: str | Path, field: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise Error(f"{field} must be an absolute path without '..'")
    return Path(os.path.abspath(path))


def real_dir(value: str | Path, field: str) -> Path:
    path = absolute(value, field)
    if not path.is_dir():
        raise Error(f"{field} is not an existing directory: {path}")
    if path.resolve(strict=True) != path:
        raise Error(f"{field} may not be or sit below a symlink: {path}")
    return path


def root_path(value: str | Path) -> Path:
    root = real_dir(value, "workspace root")
    if root == Path("/") or root.name != "workspace" or root.parent.name != "Projects":
        raise Error("workspace root must be an existing .../Projects/workspace directory")
    return root


def direct_child(value: str | Path, parent: Path, field: str) -> Path:
    path = real_dir(value, field)
    if path.parent != parent:
        raise Error(f"{field} must be a direct child of {parent}: {path}")
    return path


def inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def git(cwd: Path, *args: str, check: bool = True, text_mode: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", "-C", str(cwd), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text_mode, check=False)
    if check and result.returncode:
        output = result.stderr if text_mode else os.fsdecode(result.stderr)
        raise Error(f"git failed for {cwd}: {(output.strip() or 'unknown Git error')[:500]}")
    return result


def git_path(repo: Path, raw: str) -> Path:
    path = Path(raw)
    return (path if path.is_absolute() else repo / path).resolve()


def worktree_info(repo: Path) -> tuple[Path, str, str | None, str]:
    lines = git(repo, "worktree", "list", "--porcelain").stdout.splitlines()
    paths = [Path(line[9:]).resolve() for line in lines if line.startswith("worktree ")]
    if not paths or repo not in paths or paths[0] == repo:
        raise Error(f"refusing non-linked or primary Git worktree: {repo}")
    common = git_path(repo, git(repo, "rev-parse", "--git-common-dir").stdout.strip())
    git_dir = git_path(repo, git(repo, "rev-parse", "--git-dir").stdout.strip())
    if common == git_dir:
        raise Error(f"refusing primary Git worktree: {repo}")
    branch = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    head = git(repo, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
    return paths[0], str(common), branch.stdout.strip() if branch.returncode == 0 else None, head


def state_dir(value: str | Path) -> Path:
    path = absolute(value, "state directory")
    if path == Path("/"):
        raise Error("state directory may not be /")
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.resolve(strict=True) != path:
        raise Error(f"state directory is unsafe: {path}")
    return path


def state_file(state: Path, task: str) -> Path:
    return state / f"{task_name(task)}.json"


@contextlib.contextmanager
def locked(value: Path, task: str):
    state = state_dir(value)
    locks = state / ".locks"
    locks.mkdir(exist_ok=True)
    lock_file = locks / f"{task_name(task)}.lock"
    if locks.is_symlink() or lock_file.is_symlink():
        raise Error("state lock path is a symlink")
    fd = os.open(lock_file, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield state
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def names(data: dict) -> dict[str, dict]:
    return {Path(record["path"]).name: record for record in data["repos"]}


def context(data: dict, task: str) -> tuple[Path, Path]:
    required = {"version", "task", "owner", "workspace_root", "workspace", "repos", "jobs", "handoffs", "delivery", "accepted"}
    if not isinstance(data, dict) or not required.issubset(data) or data.get("version") != 1 or data.get("task") != task:
        raise Error("registration has missing or incompatible lifecycle fields")
    root = root_path(data["workspace_root"])
    workspace = direct_child(data["workspace"], root, "workspace")
    if not isinstance(data["repos"], list) or not data["repos"] or not isinstance(data["jobs"], list) or not isinstance(data["handoffs"], list):
        raise Error("registration has invalid repository, job, or handoff records")
    seen = set()
    for record in data["repos"]:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str) or not isinstance(record.get("common"), str) or not isinstance(record.get("removed"), bool):
            raise Error("registration has an invalid repository record")
        path = absolute(record["path"], "registered repo")
        if path.parent != workspace or path in seen:
            raise Error("registered repo is outside workspace or duplicated")
        absolute(record["common"], "common Git directory")
        seen.add(path)
    return root, workspace


def commits(data: dict) -> dict[str, str]:
    delivery = data.get("delivery")
    if not isinstance(delivery, dict) or not isinstance(delivery.get("commits"), dict):
        raise Error("delivery has no commit mapping")
    mapping = delivery["commits"]
    if set(mapping) != set(names(data)) or not all(isinstance(sha, str) and SHA_RE.fullmatch(sha) for sha in mapping.values()):
        raise Error("delivery commits must cover every repo as REPO=SHA")
    return mapping


def read(state: Path, task: str) -> dict:
    path = state_file(state, task)
    if path.is_symlink() or not path.is_file():
        raise Error(f"no safe registration for task {task}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Error(f"cannot read registration {path}: {exc}") from exc
    context(data, task)
    return data


def write(state: Path, task: str, data: dict) -> None:
    context(data, task)
    target = state_file(state, task)
    if target.is_symlink():
        raise Error("registration file is a symlink")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=state, prefix=f".{task}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def live(record: dict, workspace: Path) -> tuple[Path, Path, str]:
    repo = direct_child(record["path"], workspace, "registered repo")
    main, common, _branch, head = worktree_info(repo)
    if common != record["common"]:
        raise Error(f"registered repo points at a different Git repository: {repo}")
    return repo, main, head


def ignored_link(repo: Path, name: str) -> bool:
    relative = Path(name.rstrip("/"))
    if relative.is_absolute() or ".." in relative.parts:
        return False
    path = repo
    for part in relative.parts:
        path /= part
        if path.is_symlink():
            return True
    return False


def dirty(repo: Path) -> list[str]:
    output = git(repo, "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--ignored=matching", text_mode=False).stdout
    tracked, untracked, ignored = [], [], []
    for item in output.split(b"\0"):
        if item:
            code, name = item[:2], os.fsdecode(item[3:])
            (untracked if code == b"??" else ignored if code == b"!!" else tracked).append(name)
    unknown = [name for name in ignored if name.rstrip("/").split("/", 1)[0] not in SAFE_TEMP and not ignored_link(repo, name)]
    if tracked or untracked or unknown:
        problems = (["tracked changes: " + ", ".join(tracked)] if tracked else []) + (["untracked files: " + ", ".join(untracked)] if untracked else []) + (["unrecognized ignored paths: " + ", ".join(unknown)] if unknown else [])
        raise Error(f"close refused for {repo}: " + "; ".join(problems))
    return ignored


def outer_issues(workspace: Path, repo_records: list[dict]) -> list[str]:
    registered = {Path(record["path"]).name: record for record in repo_records}
    issues = []
    for entry in sorted(workspace.iterdir(), key=lambda item: item.name):
        record = registered.get(entry.name)
        if record:
            if record["removed"]:
                issues.append(f"registered-as-removed path still exists: {entry}")
        elif entry.name not in SAFE_TEMP:
            issues.append(f"unknown workspace entry: {entry}")
        elif entry.is_dir() and not entry.is_symlink() and (entry / ".git").exists():
            issues.append(f"temporary-named entry is a Git repository: {entry}")
    return issues


def discover(workspace: Path, supplied: list[str]) -> list[dict]:
    found = [child for child in workspace.iterdir() if child.is_dir() and not child.is_symlink() and (child / ".git").exists()]
    selected = [direct_child(path, workspace, "repo") for path in supplied] if supplied else found
    if not selected:
        raise Error("register needs at least one existing linked Git worktree")
    if len(set(selected)) != len(selected):
        raise Error("a repository was supplied more than once")
    extras = set(found) - set(selected)
    if extras:
        raise Error("workspace has unregistered Git worktrees: " + ", ".join(map(str, sorted(extras))))
    records = []
    for repo in sorted(selected):
        if "=" in repo.name:
            raise Error(f"repo directory name cannot contain '=': {repo.name}")
        _main, common, branch, _head = worktree_info(repo)
        records.append({"path": str(repo), "common": common, "branch": branch, "removed": False})
    return records


def commit_map(data: dict, items: list[str], required: bool) -> dict[str, str]:
    if not items:
        if required:
            raise Error("--commit REPO=SHA is required for every registered repo")
        return {}
    mapping, known = {}, names(data)
    for item in items:
        if "=" not in item:
            raise Error("commit must use REPO=SHA")
        repo, sha = item.split("=", 1)
        if repo not in known or repo in mapping or not SHA_RE.fullmatch(sha):
            raise Error(f"invalid commit mapping: {item}")
        mapping[repo] = sha
    if set(mapping) != set(known):
        raise Error("commit mapping must cover every registered repo")
    return mapping


def resolve(repo: Path, sha: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{sha}^{{commit}}").stdout.strip()


def registered_task(state: Path, workspace: Path) -> str | None:
    for path in state.glob("*.json"):
        if path.is_symlink():
            raise Error(f"cannot verify symlinked registration: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            value = data.get("workspace") if isinstance(data, dict) else None
            if not isinstance(value, str):
                raise Error("missing workspace")
            if absolute(value, "registered workspace") == workspace:
                return str(data.get("task", path.stem))
        except (OSError, json.JSONDecodeError, Error) as exc:
            raise Error(f"cannot verify existing registration {path}: {exc}") from exc
    return None


def register(args: argparse.Namespace) -> None:
    root = root_path(args.workspace_root)
    workspace = direct_child(args.workspace, root, "workspace")
    with locked(args.state_dir, "registry") as state:  # serializes workspace ownership checks
        if state_file(state, args.task).exists():
            raise Error(f"task is already registered: {args.task}")
        other = registered_task(state, workspace)
        if other:
            raise Error(f"workspace is already registered by task {other}: {workspace}")
        repos = discover(workspace, args.repo)
        issues = outer_issues(workspace, repos)
        if issues:
            raise Error("register refused; " + "; ".join(issues))
        data = {"version": 1, "task": args.task, "owner": text(args.owner, "owner"), "workspace_root": str(root), "workspace": str(workspace), "repos": repos, "jobs": [], "handoffs": [], "delivery": None, "accepted": None}
        write(state, args.task, data)
    print(f"registered {args.task}: {len(repos)} worktree(s) in {workspace}")


def status_line(data: dict) -> str:
    jobs = data.get("jobs") if isinstance(data.get("jobs"), list) else []
    active = [job for job in jobs if isinstance(job, dict) and job.get("finished_at") is None]
    phase = "accepted" if data.get("accepted") else "pending acceptance" if data.get("delivery") else "working"
    blockers = ", ".join(f"{job.get('name')}@{job.get('pin')}" for job in active) or "-"
    return f"{data.get('task', '?')}\towner={data.get('owner', '?')}\tworkspace={data.get('workspace', '?')}\tphase={phase}\tactive-jobs={blockers}"


def status(args: argparse.Namespace) -> None:
    if args.task:
        with locked(args.state_dir, args.task) as state:
            data = read(state, args.task)
        print(status_line(data))
        for record in data["repos"]:
            print(f"repo: {record['path']} ({record.get('branch') or 'detached'}, {'removed' if record['removed'] else 'registered'})")
        return
    state = state_dir(args.state_dir)
    entries = sorted(state.glob("*.json"))
    if not entries:
        print("no registered tasks")
    for path in entries:
        try:
            if path.is_symlink():
                raise Error("symlinked registration")
            print(status_line(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError, Error) as exc:
            print(f"{path.name}: invalid registration ({exc})")


def job(args: argparse.Namespace) -> None:
    with locked(args.state_dir, args.task) as state:
        data = read(state, args.task)
        if args.job_action == "start":
            name, pin = text(args.name, "job name"), text(args.pin, "job pin")
            if any(item.get("name") == name for item in data["jobs"]):
                raise Error(f"job name already recorded: {name}")
            data["jobs"].append({"name": name, "owner": text(args.owner or data["owner"], "job owner"), "pin": pin, "started_at": now(), "finished_at": None})
            print(f"started job {name} with pin {pin}")
        else:
            item = next((item for item in data["jobs"] if item.get("name") == args.name and item.get("finished_at") is None), None)
            if not item:
                raise Error(f"no active job named {args.name}")
            item["finished_at"], item["finished_by"] = now(), text(args.by, "finisher")
            print(f"finished job {args.name}")
        write(state, args.task, data)


def handoff(args: argparse.Namespace) -> None:
    with locked(args.state_dir, args.task) as state:
        data = read(state, args.task)
        target = data if not args.job else next((item for item in data["jobs"] if item.get("name") == args.job and item.get("finished_at") is None), None)
        if not target:
            raise Error(f"no active job named {args.job}")
        target["owner"] = text(args.to_owner, "new owner")
        data["handoffs"].append({"from": text(args.from_owner, "previous owner"), "to": args.to_owner, "job": args.job, "at": now()})
        write(state, args.task, data)
    print(f"handed off {'job ' + args.job if args.job else 'task'} from {args.from_owner} to {args.to_owner}")


def deliver(args: argparse.Namespace) -> None:
    with locked(args.state_dir, args.task) as state:
        data = read(state, args.task)
        _, workspace = context(data, args.task)
        if any(record["removed"] for record in data["repos"]):
            raise Error("cannot deliver a partly removed task")
        supplied, mapping = commit_map(data, args.commit, False), {}
        for name, record in names(data).items():
            repo, _main, head = live(record, workspace)
            chosen = resolve(repo, supplied[name]) if supplied else head
            if chosen != head:
                raise Error(f"delivery commit must equal current HEAD for {name}")
            mapping[name] = chosen
        data["delivery"] = {"by": text(args.by, "delivery owner"), "at": now(), "commits": mapping}
        data["accepted"] = None
        write(state, args.task, data)
    print("delivered " + ", ".join(f"{name}={sha}" for name, sha in mapping.items()))


def accept(args: argparse.Namespace) -> None:
    with locked(args.state_dir, args.task) as state:
        data = read(state, args.task)
        _, workspace = context(data, args.task)
        delivered, supplied = commits(data), commit_map(data, args.commit, True)
        for name, record in names(data).items():
            repo, _main, head = live(record, workspace)
            if resolve(repo, supplied[name]) != delivered[name] or head != delivered[name]:
                raise Error(f"accept commit does not match current delivered commit for {name}")
        data["accepted"] = {"manager": text(args.manager, "manager"), "at": now()}
        write(state, args.task, data)
    print(f"accepted {args.task} by {args.manager}")


def close(args: argparse.Namespace) -> None:
    expected = root_path(args.workspace_root)
    with locked(args.state_dir, args.task) as state:
        data = read(state, args.task)
        root, workspace = context(data, args.task)
        if root != expected:
            raise Error("close workspace root does not match registration")
        if inside(state.resolve(), workspace):
            raise Error("state directory is inside this workspace")
        active = [item for item in data["jobs"] if item.get("finished_at") is None]
        if active:
            raise Error("close refused; active job pins are not released: " + ", ".join(f"{item.get('name')} ({item.get('pin')})" for item in active))
        if data["delivery"] is None:
            raise Error("close refused; no delivery has been recorded")
        if data["accepted"] is None:
            raise Error("close refused; delivery is pending manager acceptance")
        issues = outer_issues(workspace, data["repos"])
        if issues:
            raise Error("close refused; " + "; ".join(issues))
        delivered, pending = commits(data), []
        for name, record in names(data).items():
            if not record["removed"]:
                repo, main, head = live(record, workspace)
                if head != delivered[name]:
                    raise Error(f"close refused; HEAD changed after accepted delivery: {repo}")
                dirty(repo)
                pending.append((record, repo, main))
        for record, repo, main in pending:  # full preflight completed before first removal
            repo, main, head = live(record, workspace)
            if head != delivered[repo.name]:
                raise Error(f"close refused; HEAD changed after preflight: {repo}")
            ignored = dirty(repo)
            result = git(main, "worktree", "remove", str(repo), check=False)
            forced = False
            if result.returncode and ignored:
                repo, main, _head = live(record, workspace)
                dirty(repo)  # never force after useful source changes appear
                result, forced = git(main, "worktree", "remove", "--force", str(repo), check=False), True
            if result.returncode:
                message = result.stderr.strip() if isinstance(result.stderr, str) else os.fsdecode(result.stderr).strip()
                raise Error(f"Git failed to remove {repo}: {(message or 'unknown Git error')[:500]}")
            record["removed"] = True
            write(state, args.task, data)  # a later failure can retry remaining repos
            print(f"removed {repo}{' after ignored-path check with --force' if forced else ''}; retained branch ref {record.get('branch') or 'HEAD'}")
        issues = outer_issues(workspace, data["repos"])
        if issues:
            raise Error("close stopped after worktree removal; " + "; ".join(issues))
        for entry in list(workspace.iterdir()):
            if entry.name not in SAFE_TEMP:
                raise Error(f"refusing to remove unknown outer artifact: {entry}")
            if entry.is_symlink() or entry.is_file():
                entry.unlink()
            elif entry.is_dir():
                shutil.rmtree(entry)
            else:
                raise Error(f"outer artifact is not a file, symlink, or directory: {entry}")
        workspace.rmdir()
        state_file(state, args.task).unlink()
    print(f"closed {args.task}")


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="登记既有 Git linked worktree，并保守地回收已验收 workspace。",
        epilog="""示例：
  ws.py register TASK --owner AGENT --workspace /.../Projects/workspace/TASK
  ws.py job start TASK train --pin host:identity
  ws.py deliver TASK --by AGENT
  ws.py accept TASK --manager MANAGER --commit repo=abcdef1
  ws.py close TASK

register 不创建 worktree。默认 workspace root 是稳定主仓库同级 workspace，
默认 state 是稳定主仓库 .local/tasks。只支持该 root 下直接子目录；不支持主
worktree、软链根目录或外部 /tmp workspace。accept 每库须提供 REPO=SHA。""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    root.add_argument("--state-dir", type=Path, default=DEFAULT_STATE, help="登记目录，默认稳定主仓库 .local/tasks")
    sub = root.add_subparsers(dest="command", required=True)
    p = sub.add_parser("register", help="登记已有 linked worktree，不创建它们")
    p.add_argument("task", type=task_name); p.add_argument("--owner", required=True); p.add_argument("--workspace-root", default=DEFAULT_ROOT); p.add_argument("--workspace", required=True); p.add_argument("--repo", action="append", default=[], help="直接 worktree 路径，可重复"); p.set_defaults(func=register)
    p = sub.add_parser("status", help="无 TASK 时列出所有登记任务")
    p.add_argument("task", type=task_name, nargs="?"); p.set_defaults(func=status)
    p = sub.add_parser("job", help="人工登记或结束带 pin 的运行 job")
    j = p.add_subparsers(dest="job_action", required=True)
    q = j.add_parser("start"); q.add_argument("task", type=task_name); q.add_argument("name"); q.add_argument("--pin", required=True, help="人工 host/process 身份；不探测 PID"); q.add_argument("--owner"); q.set_defaults(func=job)
    q = j.add_parser("finish"); q.add_argument("task", type=task_name); q.add_argument("name"); q.add_argument("--by", required=True); q.set_defaults(func=job)
    p = sub.add_parser("handoff", help="交接 task 或一个活跃 job 的责任")
    p.add_argument("task", type=task_name); p.add_argument("--from", dest="from_owner", required=True); p.add_argument("--to", dest="to_owner", required=True); p.add_argument("--job"); p.set_defaults(func=handoff)
    p = sub.add_parser("deliver", help="记录交付 commit；不传 --commit 则捕获当前 HEAD")
    p.add_argument("task", type=task_name); p.add_argument("--by", required=True); p.add_argument("--commit", action="append", default=[], help="REPO=SHA；传入时须覆盖每库"); p.set_defaults(func=deliver)
    p = sub.add_parser("accept", help="Manager 接收明确的交付 commit")
    p.add_argument("task", type=task_name); p.add_argument("--manager", required=True); p.add_argument("--commit", action="append", required=True, help="REPO=SHA，每库重复一次"); p.set_defaults(func=accept)
    p = sub.add_parser("close", help="完整预检后移除 linked worktree 并清理已知临时产物")
    p.add_argument("task", type=task_name); p.add_argument("--workspace-root", default=DEFAULT_ROOT); p.set_defaults(func=close)
    return root


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (Error, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
