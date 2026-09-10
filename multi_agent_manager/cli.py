"""Local task records, Git publication and conservative workspace archival."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

DEFAULT_ROOT = Path("/mnt/public/xcj/Projects/multi-agent-manager")
REPOS = ("multi-agent-manager", "RMBench", "opendm", "openpi", "robot-bridge")


class Error(RuntimeError):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def identifier(value):
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, AttributeError):
        raise Error(f"expected canonical UUID: {value}")
    return value


def run(argv, *, env=None, input=None, check=True):
    result = subprocess.run([str(arg) for arg in argv], input=input, capture_output=True, env=env)
    if check and result.returncode:
        raise Error(os.fsdecode(result.stderr).strip() or f"command failed: {argv}")
    return result


def git(repo, *args, **kwargs):
    return run(["git", "-C", repo, *args], **kwargs)


def value(repo, *args):
    return os.fsdecode(git(repo, *args).stdout).strip()


def safe_path(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts or path == Path("/"):
        raise Error(f"unsafe absolute path: {path}")
    if path.resolve() != path or path.is_symlink():
        raise Error(f"symlinked path is not allowed: {path}")
    return path


def primary(repo):
    common = Path(value(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if common.name != ".git":
        raise Error("management and source repositories must have a primary checkout")
    return safe_path(common.parent)


def head(repo, ref="HEAD"):
    if ref.startswith("-"):
        raise Error(f"invalid commit: {ref}")
    return value(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")


def branch_exists(repo, branch):
    return git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0


class Store:
    def __init__(self, root):
        self.root = primary(safe_path(root))
        self.state = safe_path(self.root / ".local" / "tasks")
        self.logs = safe_path(self.root / ".tasks")
        self.workspaces = safe_path(self.root.parent / "workspace")
        self.state.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def lock(self, name):
        path = safe_path(self.state / f".{name}.lock")
        with path.open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def read(self, task, *, writable=False):
        path = safe_path(self.state / f"{identifier(task)}.json")
        if not path.is_file():
            raise Error(f"task is not registered: {task}")
        data = json.loads(path.read_text())
        if data["id"] != task or data["workspace"] != str(self.workspaces / task):
            raise Error(f"registration has inconsistent task/workspace: {path}")
        if writable and data["status"] == "archived":
            raise Error(f"task is archived: {task}")
        return data

    def all(self):
        return [self.read(path.stem) for path in sorted(self.state.glob("*.json"))]

    def write(self, data):
        target = safe_path(self.state / f"{identifier(data['id'])}.json")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=self.state, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def doc(self, task, kind):
        return safe_path(self.logs / identifier(task) / f"{kind}.md")


def published(store, task, kind, revision=None):
    path = f".tasks/{identifier(task)}/{kind}.md"
    commit = head(store.root, revision or "main")
    if git(store.root, "merge-base", "--is-ancestor", commit, "main", check=False).returncode:
        raise Error(f"revision is not published on main: {commit}")
    result = git(store.root, "show", f"{commit}:{path}", check=False)
    if result.returncode:
        raise Error(f"no published {kind} for task {task} at {commit}")
    return {"revision": value(store.root, "log", "-1", "--format=%H", commit, "--", path),
            "content": result.stdout.decode(), "blob": value(store.root, "rev-parse", f"{commit}:{path}")}


def optional_doc(store, task, kind):
    try:
        return published(store, task, kind)
    except Error:
        return None


def repo_context(store, data, name, record):
    if name not in REPOS:
        raise Error(f"unknown registered repository: {name}")
    source = safe_path(store.root.parent / name)
    workspace = safe_path(data["workspace"])
    path = safe_path(workspace / name)
    branch = f"task/{identifier(data['id'])}"
    if record["path"] != str(path) or record["branch"] != branch or record["source"] != str(source):
        raise Error(f"registration has inconsistent repo/path/branch: {name}")
    if primary(source) != source:
        raise Error(f"source is not a primary checkout: {source}")
    return source, path, branch


def live(store, data, name, record):
    source, path, branch = repo_context(store, data, name, record)
    if not (path / ".git").is_file() or (path / ".git").is_symlink():
        raise Error(f"not a linked worktree: {path}")
    if primary(path) != source or value(path, "rev-parse", "--show-toplevel") != str(path):
        raise Error(f"worktree belongs to another repository: {path}")
    if value(path, "symbolic-ref", "--short", "HEAD") != branch:
        raise Error(f"worktree branch differs from registration: {path}")
    return source, path, branch


def create(store, args):
    review = None
    if args.review:
        with store.lock(identifier(args.review)):
            source = store.read(args.review)
            task_doc = published(store, args.review, "task")
            report_doc = published(store, args.review, "report")
            report = source.get("report")
            if not report or report["revision"] != report_doc["revision"]:
                raise Error("source report has no registered published delivery")
            review = {"task": args.review, "task_revision": task_doc["revision"],
                      "report_revision": report_doc["revision"], "commits": report["commits"]}
    task = str(uuid.uuid4())
    data = {"id": task, "title": args.title, "agent": None, "status": "working", "created_at": now(),
            "workspace": str(store.workspaces / task), "repos": {}, "jobs": [], "report": None,
            "review": review, "archive": None, "error": None}
    with store.lock(task):
        store.write(data)  # record intent before allocating directories
        try:
            safe_path(data["workspace"]).mkdir(parents=True)
            draft = store.doc(task, "task")
            draft.parent.mkdir(parents=True)
            content = f"# {args.title}\n"
            if review:
                content += "\nReview fixed source delivery:\n" + json.dumps(review, indent=2) + "\n"
                content += "\nSource task:\n\n" + task_doc["content"] + "\nSource report:\n\n" + report_doc["content"]
            draft.write_text(content)
            store.doc(task, "report").write_text("")
        except OSError as exc:
            data["error"] = str(exc)
            store.write(data)
            raise Error(f"creation incomplete; task {task} remains registered: {exc}")
    return {**data, "task_file": str(store.doc(task, "task")), "report_file": str(store.doc(task, "report"))}


def bind(store, args):
    with store.lock("bindings"), store.lock(args.task):
        data = store.read(args.task, writable=True)
        if data["agent"] and data["agent"] != args.agent:
            raise Error("task already has another agent")
        if any(item["agent"] == args.agent and item["id"] != args.task and item["status"] != "archived" for item in store.all()):
            raise Error("agent is already bound to another task")
        data["agent"] = args.agent
        store.write(data)
    return data


def workspace_add(store, args):
    with store.lock(args.task):
        data = store.read(args.task, writable=True)
        source = safe_path(store.root.parent / args.repo)
        if primary(source) != source:
            raise Error(f"source is not a primary checkout: {source}")
        base = head(source, args.base)
        branch = f"task/{args.task}"
        path = safe_path(Path(data["workspace"]) / args.repo)
        record = data["repos"].get(args.repo)
        if record:
            repo_context(store, data, args.repo, record)
            if base != record["base"]:
                raise Error("retry base differs from registered base")
            if record["state"] == "ready":
                live(store, data, args.repo, record)
                return record
            if path.exists():
                live(store, data, args.repo, record)
            elif branch_exists(source, branch):
                raise Error("partial creation left a branch; archive this task before creating a replacement")
        else:
            if path.exists() or branch_exists(source, branch):
                raise Error("unregistered worktree or branch already exists; refusing to adopt it")
            record = {"source": str(source), "path": str(path), "branch": branch, "base": base,
                      "state": "creating", "removed": False, "branch_removed": False, "error": None}
            data["repos"][args.repo] = record
        safe_path(data["workspace"]).mkdir(parents=True, exist_ok=True)
        store.write(data)
        try:
            result = run(["bash", source / ".local/create_worktree.sh", base, branch, data["workspace"]], check=False)
            if result.returncode:
                raise Error((os.fsdecode(result.stderr + result.stdout).strip() or "environment entry failed")[-3000:])
            live(store, data, args.repo, record)
            record["state"], record["error"] = "ready", None
        except (OSError, Error) as exc:
            record["state"], record["error"] = "failed", str(exc)
            store.write(data)
            raise Error(f"workspace add failed; {args.repo} remains registered: {exc}")
        store.write(data)
    return record


def publish(store, args):
    with store.lock(args.task), store.lock("publish"):
        data = store.read(args.task, writable=True)
        draft = store.doc(args.task, args.file)
        if not draft.is_file():
            raise Error(f"missing draft: {draft}")
        content = draft.read_bytes()
        report = None
        if args.file == "report":
            first = content.decode().splitlines()
            match = re.fullmatch(r"task_revision: ([0-9a-f]{40})", first[0] if first else "")
            if not match:
                raise Error("report first line must be task_revision: <40-character published commit>")
            revision = match[1]
            published(store, args.task, "task", revision)
            delivery = {}
            for name, record in data["repos"].items():
                if record["state"] != "ready" or record["removed"]:
                    raise Error(f"cannot publish delivery from incomplete worktree: {name}")
                _, path, _ = live(store, data, name, record)
                delivery[name] = head(path)
            report = {"task_revision": revision, "commits": delivery}
        path = f".tasks/{args.task}/{args.file}.md"
        existing = optional_doc(store, args.task, args.file)
        if existing and existing["content"].encode() == content:
            if report is not None and (not data["report"] or report["commits"] != data["report"]["commits"]):
                raise Error("delivery HEAD changed; update the report draft before publishing")
            git(store.root, "update-index", "--add", "--cacheinfo", "100644", existing["blob"], path)
            return {"id": args.task, "file": args.file, "revision": existing["revision"], "unchanged": True}
        parent = head(store.root, "main")
        with tempfile.TemporaryDirectory(prefix="task-publish-") as temporary:
            env = {**os.environ, "GIT_INDEX_FILE": str(Path(temporary) / "index")}
            git(store.root, "read-tree", parent, env=env)
            blob = git(store.root, "hash-object", "-w", "--stdin", input=content).stdout.decode().strip()
            git(store.root, "update-index", "--add", "--cacheinfo", "100644", blob, path, env=env)
            tree = git(store.root, "write-tree", env=env).stdout.decode().strip()
            commit = git(store.root, "commit-tree", tree, "-p", parent, "-m", f"Publish {args.task} {args.file}").stdout.decode().strip()
            git(store.root, "update-ref", "refs/heads/main", commit, parent)
        if report is not None:
            data["report"] = {**report, "revision": commit}
            data["status"] = "pending"
        store.write(data)
        # Update only this entry; Git locks the shared index and keeps other entries.
        # Use the published blob so an edit made during publication stays a draft.
        git(store.root, "update-index", "--add", "--cacheinfo", "100644", blob, path)
    return {"id": args.task, "file": args.file, "revision": commit, "report": report}


def runtime():
    try:
        from . import job_runtime
    except ImportError as exc:
        raise Error("multi_agent_manager.job_runtime is required for process queries") from exc
    return job_runtime


def agent_observations(agent_ids):
    agent_ids = sorted(set(agent_ids))
    if not agent_ids:
        return {}
    observations = runtime().probe_agents(agent_ids)
    return observations if isinstance(observations, dict) else {}


def agent_state(agent, observations, *, unbound="unknown"):
    if not agent:
        error = None if unbound == "unbound" else "no bound agent"
        return {"status": unbound, "checked_at": None, "error": error}
    observation = observations.get(agent)
    if not isinstance(observation, dict) or not isinstance(observation.get("status"), str) or not observation["status"]:
        return {"status": "unknown", "checked_at": None, "error": "agent state unavailable"}
    return dict(observation)


def refresh_jobs(data, jobs=None):
    if data["status"] == "archived":
        return
    for job in data["jobs"] if jobs is None else jobs:
        if job["status"] == "archived":
            continue
        observation = runtime().probe_process(job["host"], job["pid"], job["identity"])
        job["probe"] = observation
        if observation["status"] in ("running", "stopped"):
            job["status"] = observation["status"]
            job["checked_at"] = observation["checked_at"]


def job_add(store, args):
    if args.pid <= 0:
        raise Error("PID must be positive")
    with store.lock(args.task):
        data = store.read(args.task, writable=True)
        observation = runtime().probe_process(args.host, args.pid)
        if observation["status"] != "running" or not observation.get("identity") or observation.get("error"):
            raise Error(f"cannot register process without confirmed running identity: {observation}")
        job = {"id": str(uuid.uuid4()), "note": args.note, "host": args.host, "pid": args.pid,
               "identity": observation["identity"], "status": "running", "checked_at": observation["checked_at"],
               "probe": observation, "archive": None}
        data["jobs"].append(job)
        store.write(data)
    return {"task": args.task, **job}


def static_jobs(data, args):
    if args.attention:
        return [job for job in data["jobs"] if job["status"] != "archived"]
    if args.status == "archived":
        return [job for job in data["jobs"] if job["status"] == "archived"]
    if args.status == "all":
        return list(data["jobs"])
    return [job for job in data["jobs"] if job["status"] != "archived"]


def job_list(store, args):
    tasks = [store.read(args.task)] if args.task else store.all()
    entries = []
    for item in tasks:
        with store.lock(item["id"]):
            data = store.read(item["id"])
            if data["status"] == "archived" and args.attention:
                continue
            jobs = static_jobs(data, args)
            current = [job for job in jobs if job["status"] != "archived"]
            if current and data["status"] != "archived":
                refresh_jobs(data, current)
                store.write(data)
            entries.extend((data["id"], data["agent"], data["status"], job) for job in jobs)
    if args.status in ("running", "stopped"):
        entries = [entry for entry in entries if entry[3]["status"] == args.status]
    if args.attention:
        agents = agent_observations(
            agent for _, agent, task_status, job in entries
            if task_status != "archived" and job["probe"]["status"] == "stopped" and agent
        )
    else:
        agents = agent_observations(
            agent for _, agent, task_status, job in entries
            if task_status != "archived" and job["status"] != "archived" and agent
        )
    selected, uncertain = [], []
    for task, agent, _, job in entries:
        row = {"task": task, "agent": agent, **job}
        row["agent_state"] = agent_state(agent, agents)
        if args.attention:
            if row["status"] == "archived":
                continue
            if row["probe"]["status"] not in ("running", "stopped"):
                uncertain.append(row)
            elif row["status"] == "stopped":
                if row["agent_state"]["status"] == "unknown" or row["agent_state"].get("error"):
                    uncertain.append(row)
                elif row["agent_state"]["status"] != "active":
                    selected.append(row)
        else:
            selected.append(row)
    return {"jobs": selected, "needs_verification": uncertain}


def job_archive(store, args):
    for item in store.all():
        if not any(job["id"] == args.job for job in item["jobs"]):
            continue
        with store.lock(item["id"]):
            data = store.read(item["id"])
            job = next(job for job in data["jobs"] if job["id"] == args.job)
            if job["status"] != "archived":
                refresh_jobs(data)
                store.write(data)
                if job["probe"]["status"] != "stopped":
                    raise Error("process must be confirmed stopped before job archive")
                job["status"] = "archived"
                job["archive"] = {"note": args.note, "at": now()}
                store.write(data)
            return job
    raise Error(f"job is not registered: {args.job}")


def status(store, args):
    data = store.read(args.task)
    docs = {kind: optional_doc(store, args.task, kind) for kind in ("task", "report")}
    drafts = {}
    for kind, document in docs.items():
        path = store.doc(args.task, kind)
        drafts[kind] = path.exists() and (document is None or path.read_text() != document["content"])
    report = data.get("report")
    changed = None
    if report and docs["task"]:
        previous = published(store, args.task, "task", report["task_revision"])
        changed = previous["blob"] != docs["task"]["blob"]
    return {**data, "publications": {kind: doc["revision"] if doc else None for kind, doc in docs.items()},
            "drafts": drafts, "requirements_changed": changed}


def task_list(store, args):
    tasks = [data for data in store.all() if args.all or (data["status"] == "archived") == args.archived]
    agents = agent_observations(data["agent"] for data in tasks if data["agent"])
    return [{**data, "agent_state": agent_state(data["agent"], agents, unbound="unbound")} for data in tasks]


def one_line(value):
    return " ".join(str(value).split())


def print_task_list(tasks):
    rows = []
    for task in tasks:
        agent = task["agent"] or "未绑定"
        state = task["agent_state"]["status"]
        rows.append("\t".join((one_line(task["title"]), one_line(task["status"]), task["id"], one_line(agent),
                              "未绑定" if state == "unbound" else one_line(state))))
    if rows:
        sys.stdout.write("\n".join(rows) + "\n")


def print_published(document):
    sys.stdout.write(f"revision: {document['revision']}\n\n")
    sys.stdout.write(document["content"])


def ignored_link(repo, name):
    path = repo
    for part in Path(name.rstrip("/")).parts:
        path /= part
        if path.is_symlink():
            return True
    return False


def dirty(repo):
    output = git(repo, "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--ignore-submodules=none", "--ignored=matching").stdout
    ignored, problems = [], []
    for item in output.split(b"\0"):
        if not item:
            continue
        code, name = item[:2], os.fsdecode(item[3:])
        if code == b"!!" and (name.rstrip("/").split("/", 1)[0] == ".venv" or ignored_link(repo, name)):
            ignored.append(name)
        else:
            problems.append(f"{os.fsdecode(code)} {name}")
    if problems:
        raise Error(f"archive refused; modified, untracked or unknown ignored contents in {repo}: " + "; ".join(problems))
    return ignored


def outer_check(workspace, records):
    if not workspace.exists():
        return
    known = {Path(record["path"]).name for record in records.values() if not record["removed"]}
    unknown = [str(path) for path in workspace.iterdir() if path.name not in known]
    if unknown:
        raise Error("archive refused; unregistered workspace entries: " + ", ".join(unknown))


def archive(store, args):
    with store.lock(args.task):
        data = store.read(args.task)
        if data["status"] == "archived":
            return data["archive"]
        refresh_jobs(data)
        store.write(data)
        blocked = [job["id"] for job in data["jobs"] if job["status"] != "archived" and job["probe"]["status"] != "stopped"]
        if blocked:
            raise Error("archive refused; running or unknown registered processes: " + ", ".join(blocked))
        workspace = safe_path(data["workspace"])
        outer_check(workspace, data["repos"])
        for name, record in data["repos"].items():  # preflight every repo before removing any
            source, path, branch = repo_context(store, data, name, record)
            if path.exists():
                if record["removed"]:
                    raise Error(f"removed worktree path reappeared: {path}")
                live(store, data, name, record)
                dirty(path)
            elif record["state"] == "ready" and not record["removed"]:
                raise Error(f"registered worktree unexpectedly missing: {path}")
            registrations = git(source, "worktree", "list", "--porcelain").stdout.decode().split("\n\n")
            for entry in registrations:
                if f"branch refs/heads/{branch}" in entry.splitlines() and f"worktree {path}" not in entry.splitlines():
                    raise Error(f"task branch is checked out elsewhere: {branch}")
        result = data["archive"] or {"note": args.note, "removed": [], "at": None}
        data["archive"] = result
        try:
            for name, record in data["repos"].items():
                source, path, branch = repo_context(store, data, name, record)
                if not record["removed"]:
                    if path.exists():
                        live(store, data, name, record)
                        ignored = dirty(path)
                        removal = git(source, "worktree", "remove", str(path), check=False)
                        if removal.returncode and ignored:
                            live(store, data, name, record)
                            dirty(path)
                            removal = git(source, "worktree", "remove", "--force", str(path), check=False)
                        if removal.returncode:
                            raise Error(os.fsdecode(removal.stderr).strip())
                        result["removed"].append({"worktree": str(path)})
                    record["removed"] = True
                    store.write(data)
                if not record["branch_removed"]:
                    if branch_exists(source, branch):
                        git(source, "branch", "-D", "--", branch)
                        result["removed"].append({"repo": name, "branch": branch})
                    record["branch_removed"] = True
                    store.write(data)
            outer_check(workspace, data["repos"])
            if workspace.exists():
                workspace.rmdir()
                result["removed"].append({"workspace": str(workspace)})
            data["status"], data["error"] = "archived", None
            result["at"] = now()
        except (Error, OSError) as exc:
            data["error"] = str(exc)
            store.write(data)
            raise Error(f"archive incomplete; retry remaining items; removed={result['removed']}: {exc}")
        store.write(data)
    return result


def parser():
    def command(sub, name, description):
        return sub.add_parser(name, help=description, description=description)

    cli = argparse.ArgumentParser(prog="mam", description="Manage local cluster tasks, workspaces and processes.",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="stable management checkout")
    commands = cli.add_subparsers(required=True)
    task = command(commands, "task", "manage tasks and publications")
    sub = task.add_subparsers(dest="command", required=True)
    p = command(sub, "create", "register UUID, drafts and empty workspace")
    p.add_argument("--title", required=True, help="short task title")
    p.add_argument("--review", help="source task UUID; fix its published task/report and commits")
    p.set_defaults(func=create)
    p = command(sub, "bind", "bind one execution agent")
    p.add_argument("task", help="task UUID")
    p.add_argument("--agent", required=True, help="execution agent ID; one active task per agent")
    p.set_defaults(func=bind)
    p = command(sub, "show", "read a published document")
    p.add_argument("task", help="task UUID")
    p.add_argument("--file", choices=("task", "report"), default="task", help="published document (default: task)")
    p.add_argument("--revision", help="published commit to read; defaults to main")
    p.add_argument("--json", action="store_true", help="emit the published document as JSON")
    p.set_defaults(func=lambda s, a: published(s, a.task, a.file, a.revision))
    p = command(sub, "publish", "publish only one draft to main using an isolated index")
    p.add_argument("task", help="task UUID")
    p.add_argument("--file", choices=("task", "report"), required=True, help="draft to publish; reports require task_revision on the first line")
    p.set_defaults(func=publish)
    p = command(sub, "list", "list registered task records")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--archived", action="store_true", help="show only archived tasks")
    group.add_argument("--all", action="store_true", help="include archived tasks")
    p.add_argument("--json", action="store_true", help="emit complete task records as JSON")
    p.set_defaults(func=task_list)
    p = command(sub, "status", "query jobs, versions, drafts and archive progress")
    p.add_argument("task", help="task UUID")
    p.set_defaults(func=status)
    p = command(sub, "archive", "remove owned worktrees and task branches; retain task records")
    p.add_argument("task", help="task UUID")
    p.add_argument("--note", required=True, help="purpose, result or reason for this operation")
    p.set_defaults(func=archive)
    jobs = command(commands, "job", "register, query and archive process records").add_subparsers(required=True)
    p = command(jobs, "add", "register a running process with its startup identity")
    p.add_argument("task", help="task UUID")
    p.add_argument("--note", required=True, help="purpose, result or reason for this operation")
    p.add_argument("--host", required=True, help="host running the process")
    p.add_argument("--pid", type=int, required=True, help="running process ID")
    p.set_defaults(func=job_add)
    p = command(jobs, "list", "query process and agent states; never wake agents")
    p.add_argument("--task", help="filter jobs by task UUID")
    p.add_argument("--status", choices=("running", "stopped", "archived", "all"), help="filter jobs; default excludes archived records")
    p.add_argument("--attention", action="store_true", help="show stopped jobs with inactive agents; list unknowns separately")
    p.set_defaults(func=job_list)
    p = command(jobs, "archive", "record the handling of a stopped process; retain history")
    p.add_argument("job", help="job UUID")
    p.add_argument("--note", required=True, help="purpose, result or reason for this operation")
    p.set_defaults(func=job_archive)
    w = command(commands, "workspace", "manage repository worktrees and their environments").add_subparsers(required=True)
    p = command(w, "add", "create a repository worktree using its local environment entry")
    p.add_argument("task", help="task UUID")
    p.add_argument("--repo", choices=REPOS, required=True, help="source repository")
    p.add_argument("--base", required=True, help="base commit for the task branch")
    p.set_defaults(func=workspace_add)
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if getattr(args, "task", None):
            identifier(args.task)
        result = args.func(Store(args.root), args)
        if getattr(args, "command", None) == "list" and not args.json:
            print_task_list(result)
        elif getattr(args, "command", None) == "show" and not args.json:
            print_published(result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0
