"""Local task records, Git publication and conservative workspace archival."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

ENV_FILE = Path(".mam") / "env.json"
class Error(RuntimeError):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def identifier(value):
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, AttributeError):
        raise Error(f"expected canonical TASK-ID: {value}")
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


def repository_name(value):
    if not isinstance(value, str) or not value:
        raise Error("repository name must be a non-empty single directory name")
    if value in (".", "..") or "/" in value or "\\" in value or "\0" in value:
        raise Error("repository name must be a non-empty single directory name")
    path = Path(value)
    if path.is_absolute():
        raise Error("repository name must be a non-empty single directory name")
    if len(path.parts) != 1 or path.name != value:
        raise Error("repository name must be a non-empty single directory name")
    return value


def configured_directory(key, raw):
    if not isinstance(raw, str) or not raw:
        raise Error(f"{key} must be a non-empty absolute path")
    path = Path(raw)
    if not path.is_absolute():
        raise Error(f"{key} must be an absolute path: {raw}")
    try:
        path = path.resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise Error(f"{key} cannot be resolved: {raw}: {exc}") from exc
    if not path.is_dir():
        raise Error(f"{key} must be a directory: {path}")
    return safe_path(path)


def worktree_root(repo, key):
    root = safe_path(repo)
    top = safe_path(Path(value(root, "rev-parse", "--show-toplevel")))
    if top != root:
        raise Error(f"{key} must be a repository worktree root: {root}")
    return root


def primary(repo):
    common = Path(value(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if common.name != ".git":
        raise Error("source repository must have a primary checkout")
    return safe_path(common.parent)


def head(repo, ref="HEAD"):
    if ref.startswith("-"):
        raise Error(f"invalid commit: {ref}")
    return value(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")


def branch_exists(repo, branch):
    return git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0


@dataclass(frozen=True)
class ProjectConfig:
    mam_root: Path
    project_root: Path
    branch: str


def environment_file(cwd=None):
    try:
        current = (Path.cwd() if cwd is None else Path(cwd)).resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise Error(f"cannot resolve current directory for project configuration: {exc}") from exc
    if not current.is_dir():
        raise Error(f"current directory is not a directory: {current}")
    while True:
        candidate = current / ENV_FILE
        if candidate.exists() or candidate.is_symlink():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    raise Error(f"no {ENV_FILE} found from {Path.cwd() if cwd is None else cwd}")


def project_config(cwd=None):
    path = environment_file(cwd)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Error(f"invalid project configuration {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise Error(f"invalid project configuration {path}: expected a JSON object")
    required = ("MAM_ROOT", "PROJECT_ROOT", "MAM_BRANCH")
    missing = [key for key in required if key not in data]
    if missing:
        raise Error(f"invalid project configuration {path}: missing required keys: {', '.join(missing)}")
    mam_root = worktree_root(configured_directory("MAM_ROOT", data["MAM_ROOT"]), "MAM_ROOT")
    project_root = configured_directory("PROJECT_ROOT", data["PROJECT_ROOT"])
    branch = data["MAM_BRANCH"]
    if not isinstance(branch, str) or not branch:
        raise Error("MAM_BRANCH must be a non-empty local branch name")
    if git(mam_root, "check-ref-format", "--branch", branch, check=False).returncode:
        raise Error(f"MAM_BRANCH is not a valid local branch name: {branch}")
    if not branch_exists(mam_root, branch):
        raise Error(f"MAM_BRANCH is not an existing local branch: {branch}")
    return ProjectConfig(mam_root=mam_root, project_root=project_root, branch=branch)


def wait_key(agent):
    return hashlib.sha256(agent.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, config):
        if not isinstance(config, ProjectConfig):
            raise Error("Store requires a project configuration")
        self.config = config
        self.root = config.mam_root
        self.project_root = config.project_root
        self.branch = config.branch
        self.state = safe_path(self.root / ".local" / "tasks")
        self.waits = safe_path(self.root / ".local" / "waits")
        self.logs = safe_path(self.root / ".tasks")
        self.workspaces = safe_path(self.project_root / "workspace")
        self.state.mkdir(parents=True, exist_ok=True)
        self.waits.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def lock(self, name):
        path = safe_path(self.state / f".{name}.lock")
        with path.open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def read(self, task, *, writable=False):
        path = safe_path(self.state / f"{identifier(task)}.json")
        if not path.is_file():
            raise Error(f"TASK-ID is not registered: {task}")
        data = json.loads(path.read_text())
        if data["id"] != task or data["workspace"] != str(self.workspaces / task):
            raise Error(f"registration has inconsistent TASK-ID/workspace: {path}")
        if writable and data["status"] == "archived":
            raise Error(f"TASK-ID is archived: {task}")
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

    def wait_path(self, agent):
        return safe_path(self.waits / f"{wait_key(agent)}.json")

    def read_wait(self, agent):
        path = self.wait_path(agent)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            path.unlink(missing_ok=True)
            return None
        if not isinstance(data, dict) or data.get("agent") != agent or wait_key(agent) != path.stem:
            path.unlink(missing_ok=True)
            return None
        return data

    def write_wait(self, data):
        target = self.wait_path(data["agent"])
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=self.waits, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def remove_wait(self, agent):
        self.wait_path(agent).unlink(missing_ok=True)

    def doc(self, task, kind):
        return safe_path(self.logs / identifier(task) / f"{kind}.md")


def published(store, task, kind):
    path = f".tasks/{identifier(task)}/{kind}.md"
    commit = head(store.root, store.branch)
    result = git(store.root, "show", f"{commit}:{path}", check=False)
    if result.returncode:
        raise Error(f"no published {kind} for TASK-ID {task} at {commit}")
    return {"revision": value(store.root, "log", "-1", "--format=%H", commit, "--", path),
            "content": result.stdout.decode(), "blob": value(store.root, "rev-parse", f"{commit}:{path}")}


def optional_doc(store, task, kind):
    try:
        return published(store, task, kind)
    except Error:
        return None


def repo_context(store, data, name, record):
    name = repository_name(name)
    source = safe_path(store.project_root / name)
    workspace = safe_path(data["workspace"])
    path = safe_path(workspace / name)
    branch = f"task/{identifier(data['id'])}"
    if record["path"] != str(path) or record["branch"] != branch or record["source"] != str(source):
        raise Error(f"registration has inconsistent repo/path/branch: {name}")
    if primary(source) != source:
        raise Error(f"source is not a primary checkout: {source}")
    return source, path, branch


def workspace_entry(source):
    entry = safe_path(source / ".local" / "create_worktree.sh")
    if not entry.is_file():
        raise Error(f"source repository has no .local/create_worktree.sh: {source}")
    return entry


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
            if not isinstance(report, dict) or report.get("revision") != report_doc["revision"]:
                raise Error("source report has no registered published delivery")
            commits = report.get("commits")
            if not isinstance(commits, dict):
                raise Error("source report has no registered delivery commits")
            review = {"task": args.review, "commits": commits}
    task = str(uuid.uuid4())
    data = {"id": task, "title": args.title, "agent": None, "status": "working", "created_at": now(),
            "workspace": str(store.workspaces / task), "repos": {}, "jobs": [], "report": None,
            "review": review, "archive": None, "error": None}
    with store.lock("bindings"), store.lock(task):
        try:
            from . import wake_runtime
            wake_runtime.capture_manager_for_task(store)
        except RuntimeError as exc:
            raise Error(str(exc)) from exc
        store.write(data)  # record intent before allocating directories
        try:
            safe_path(data["workspace"]).mkdir(parents=True)
            draft = store.doc(task, "task")
            draft.parent.mkdir(parents=True)
            content = f"# {args.title}\n"
            if review:
                content += f"\nReview source delivery (source TASK-ID: {args.review}):\n" + json.dumps(review, indent=2) + "\n"
                content += "\nSource task requirements:\n\n" + task_doc["content"] + "\nSource report:\n\n" + report_doc["content"]
            draft.write_text(content)
            store.doc(task, "report").write_text("")
        except OSError as exc:
            data["error"] = str(exc)
            store.write(data)
            raise Error(f"creation incomplete; TASK-ID {task} remains registered: {exc}")
    return {**data, "task_file": str(store.doc(task, "task")), "report_file": str(store.doc(task, "report"))}


def bind(store, args):
    with store.lock("bindings"), store.lock(args.task):
        try:
            from . import wake_runtime
            wake_runtime.capture_manager_for_task(store, excluded_agent=args.agent)
        except RuntimeError as exc:
            raise Error(str(exc)) from exc
        data = store.read(args.task, writable=True)
        if data["agent"] and data["agent"] != args.agent:
            raise Error("task already has another agent")
        if any(item["agent"] == args.agent and item["id"] != args.task and item["status"] != "archived" for item in store.all()):
            raise Error("agent is already bound to another task")
        data["agent"] = args.agent
        store.write(data)
    return data


def workspace_add(store, args):
    name = repository_name(args.repo)
    with store.lock(args.task):
        data = store.read(args.task, writable=True)
        source = safe_path(store.project_root / name)
        if primary(source) != source:
            raise Error(f"source is not a primary checkout: {source}")
        entry = workspace_entry(source)
        base = head(source, args.base)
        branch = f"task/{args.task}"
        path = safe_path(Path(data["workspace"]) / name)
        record = data["repos"].get(name)
        if record:
            repo_context(store, data, name, record)
            if base != record["base"]:
                raise Error("retry base differs from registered base")
            if record["state"] == "ready":
                live(store, data, name, record)
                return record
            if path.exists():
                live(store, data, name, record)
            elif branch_exists(source, branch):
                raise Error("partial creation left a branch; archive this task before creating a replacement")
        else:
            if path.exists() or branch_exists(source, branch):
                raise Error("unregistered worktree or branch already exists; refusing to adopt it")
            record = {"source": str(source), "path": str(path), "branch": branch, "base": base,
                      "state": "creating", "removed": False, "branch_removed": False, "error": None}
            data["repos"][name] = record
        safe_path(data["workspace"]).mkdir(parents=True, exist_ok=True)
        store.write(data)
        try:
            result = run(["bash", entry, base, branch, data["workspace"]], check=False)
            if result.returncode:
                raise Error((os.fsdecode(result.stderr + result.stdout).strip() or "environment entry failed")[-3000:])
            live(store, data, name, record)
            record["state"], record["error"] = "ready", None
        except (OSError, Error) as exc:
            record["state"], record["error"] = "failed", str(exc)
            store.write(data)
            raise Error(f"workspace add failed; {name} remains registered: {exc}")
        store.write(data)
    return record


def publish_branch(store):
    current = value(store.root, "branch", "--show-current")
    if current != store.branch:
        observed = current or "detached HEAD"
        raise Error(f"MAM_ROOT must be checked out on MAM_BRANCH {store.branch}; current branch is {observed}")


def publish(store, args):
    with store.lock(args.task), store.lock("publish"):
        publish_branch(store)
        data = store.read(args.task, writable=True)
        draft = store.doc(args.task, args.file)
        if not draft.is_file():
            raise Error(f"missing draft: {draft}")
        content = draft.read_bytes()
        report = None
        if args.file == "report":
            delivery = {}
            for name, record in data["repos"].items():
                if record["state"] != "ready" or record["removed"]:
                    raise Error(f"cannot publish delivery from incomplete worktree: {name}")
                _, path, _ = live(store, data, name, record)
                delivery[name] = head(path)
            report = {"commits": delivery}
        path = f".tasks/{args.task}/{args.file}.md"
        existing = optional_doc(store, args.task, args.file)
        if existing and existing["content"].encode() == content:
            if report is not None and (not data["report"] or report["commits"] != data["report"]["commits"]):
                raise Error("delivery HEAD changed; update the report draft before publishing")
            git(store.root, "update-index", "--add", "--cacheinfo", "100644", existing["blob"], path)
            return {"id": args.task, "file": args.file, "revision": existing["revision"], "unchanged": True}
        parent = head(store.root, store.branch)
        with tempfile.TemporaryDirectory(prefix="task-publish-") as temporary:
            env = {**os.environ, "GIT_INDEX_FILE": str(Path(temporary) / "index")}
            git(store.root, "read-tree", parent, env=env)
            blob = git(store.root, "hash-object", "-w", "--stdin", input=content).stdout.decode().strip()
            git(store.root, "update-index", "--add", "--cacheinfo", "100644", blob, path, env=env)
            tree = git(store.root, "write-tree", env=env).stdout.decode().strip()
            commit = git(store.root, "commit-tree", tree, "-p", parent, "-m", f"Publish {args.task} {args.file}").stdout.decode().strip()
            git(store.root, "update-ref", f"refs/heads/{store.branch}", commit, parent)
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
        identity = observation.get("identity")
        if not job.get("started_at") and isinstance(identity, dict) and identity.get("started_at"):
            job["started_at"] = identity["started_at"]
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
               "started_at": observation["identity"].get("started_at"), "probe": observation, "archive": None}
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
            entries.extend((data["id"], data["title"], data["agent"], data["status"], job) for job in jobs)
    if args.status in ("running", "stopped"):
        entries = [entry for entry in entries if entry[4]["status"] == args.status]
    if args.attention:
        agents = agent_observations(
            agent for _, _, agent, task_status, job in entries
            if task_status != "archived" and job["probe"]["status"] == "stopped" and agent
        )
    else:
        agents = agent_observations(
            agent for _, _, agent, task_status, job in entries
            if task_status != "archived" and job["status"] != "archived" and agent
        )
    selected, uncertain = [], []
    for task, task_title, agent, _, job in entries:
        row = {"task": task, "task_title": task_title, "agent": agent, **job}
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


def saved_job_state(job):
    """Return the saved observation shown by task status without probing."""

    probe = job.get("probe")
    if job.get("status") != "archived" and isinstance(probe, dict) and probe.get("status") == "unknown":
        return "unknown", probe.get("checked_at") or job.get("checked_at")
    return job.get("status", "unknown"), job.get("checked_at")


def job_summary(job):
    status, checked_at = saved_job_state(job)
    result = {"id": job["id"], "note": job.get("note"), "status": status}
    if checked_at is not None:
        result["checked_at"] = checked_at
    return result


def archive_summary(archive):
    if not isinstance(archive, dict):
        return None
    return {key: archive[key] for key in ("note", "at") if archive.get(key) is not None}


def repo_summary(record, commit):
    result = {key: record[key] for key in ("path", "branch", "state", "base") if record.get(key) is not None}
    if commit is not None:
        result["commit"] = commit
    for key in ("removed", "branch_removed"):
        if record.get(key):
            result[key] = True
    if record.get("error"):
        result["error"] = record["error"]
    return result


def render_task_status(data, docs, drafts):
    report = data.get("report") if isinstance(data.get("report"), dict) else {}
    commits = report.get("commits") if isinstance(report.get("commits"), dict) else {}
    result = {key: data.get(key) for key in ("id", "title", "status", "agent", "workspace")}
    result["repos"] = {name: repo_summary(record, commits.get(name)) for name, record in data["repos"].items()}
    publications = {kind: document["revision"] for kind, document in docs.items() if document}
    if publications:
        result["publications"] = publications
    unarchived = [job_summary(job) for job in data["jobs"] if job.get("status") != "archived"]
    archived_count = sum(job.get("status") == "archived" for job in data["jobs"])
    if unarchived or archived_count:
        result["jobs"] = {"cached": True}
        if unarchived:
            result["jobs"]["unarchived"] = unarchived
        if archived_count:
            result["jobs"]["archived_count"] = archived_count
    changed_drafts = {kind: True for kind, dirty in drafts.items() if dirty}
    if changed_drafts:
        result["drafts"] = changed_drafts
    archive = archive_summary(data.get("archive"))
    if archive:
        result["archive"] = archive
    if data.get("error"):
        result["error"] = data["error"]
    review = data.get("review")
    if isinstance(review, dict):
        fixed = {}
        if review.get("task") is not None:
            fixed["source_task"] = review["task"]
        if review.get("commits") is not None:
            fixed["commits"] = review["commits"]
        if fixed:
            result["review"] = fixed
    return result


def render_job_status(data, job):
    stored_status = job.get("status", "unknown")
    probe = job.get("probe") if isinstance(job.get("probe"), dict) else {}
    observed_status = probe.get("status")
    status, checked_at, error = stored_status, job.get("checked_at"), None
    if stored_status != "archived" and observed_status in ("running", "stopped"):
        status = observed_status
        checked_at = probe.get("checked_at") or checked_at
        error = probe.get("error")
    elif stored_status != "archived" and observed_status == "unknown":
        status = "unknown"
        checked_at = probe.get("checked_at") or checked_at
        error = probe.get("error")
    result = {"id": job["id"], "note": job.get("note"), "task": data["id"], "task_title": data["title"],
              "agent": data.get("agent"), "host": job.get("host"), "pid": job.get("pid"), "status": status}
    if job.get("started_at") is not None:
        result["started_at"] = job["started_at"]
    if checked_at is not None:
        result["checked_at"] = checked_at
    if error:
        result["error"] = error
    if status == "unknown":
        if stored_status != "unknown":
            result["last_known_status"] = stored_status
        if job.get("checked_at") is not None:
            result["last_known_checked_at"] = job["checked_at"]
    if stored_status == "archived":
        archive = archive_summary(job.get("archive"))
        if archive:
            result["archive"] = archive
    return result


def job_status(store, args):
    for item in store.all():
        if not any(job["id"] == args.job for job in item["jobs"]):
            continue
        with store.lock(item["id"]):
            data = store.read(item["id"])
            job = next(job for job in data["jobs"] if job["id"] == args.job)
            if data["status"] != "archived" and job["status"] != "archived":
                refresh_jobs(data, [job])
                store.write(data)
            return render_job_status(data, job)
    raise Error(f"JOB-ID is not registered: {args.job}")


def job_archive(store, args):
    for item in store.all():
        if not any(job["id"] == args.job for job in item["jobs"]):
            continue
        with store.lock(item["id"]):
            data = store.read(item["id"])
            job = next(job for job in data["jobs"] if job["id"] == args.job)
            if job["status"] != "archived":
                job["status"] = "archived"
                job["archive"] = {"note": args.note, "at": now()}
                store.write(data)
            return job
    raise Error(f"JOB-ID is not registered: {args.job}")


def status(store, args):
    data = store.read(args.task)
    docs = {kind: optional_doc(store, args.task, kind) for kind in ("task", "report")}
    drafts = {}
    for kind, document in docs.items():
        path = store.doc(args.task, kind)
        drafts[kind] = path.exists() and (document is None or path.read_text() != document["content"])
    return render_task_status(data, docs, drafts)


def wait_agent(args):
    agent = getattr(args, "agent", None)
    if not isinstance(agent, str) or not agent or agent != agent.strip() or any(char in agent for char in "\r\n\t"):
        raise Error("--agent must be a non-empty single-line AGENT-ID")
    return agent


def wait_caller():
    agent = os.environ.get("CODEX_THREAD_ID")
    if not isinstance(agent, str) or not agent or agent != agent.strip() or any(char in agent for char in "\r\n\t"):
        raise Error("CODEX_THREAD_ID must be a non-empty canonical AGENT-ID")
    try:
        if str(uuid.UUID(agent)) != agent:
            raise ValueError()
    except ValueError:
        raise Error("CODEX_THREAD_ID must be a canonical AGENT-ID") from None
    return agent


def wait_compat_module():
    try:
        from . import wait_compat
    except ImportError as exc:
        raise Error("multi_agent_manager.wait_compat is required for mam wait") from exc
    return wait_compat


def wait_compatibility(module=None):
    wait_compat = module or wait_compat_module()
    try:
        result = wait_compat.require_compatible()
    except RuntimeError as exc:
        raise Error(str(exc)) from exc
    if not isinstance(result, dict):
        raise Error("wait compatibility check returned no runtime paths")
    socket_path, log_path = result.get("socket_path"), result.get("log_path")
    if not isinstance(socket_path, str) or not socket_path or not isinstance(log_path, str) or not log_path:
        raise Error("wait compatibility check returned invalid runtime paths")
    return result


def wait_trace_path(wait_compat):
    # The compatibility module is the authority for configured runtime paths.
    # Discover its trace path before the intentionally thorough probe, so an
    # input received during that probe remains in this wait's trace tail.
    discover = getattr(wait_compat, "configured_paths", None)
    if not callable(discover):
        discover = getattr(wait_compat, "_configured_paths", None)
    if not callable(discover):
        raise Error("wait compatibility module cannot discover its configured trace path")
    try:
        _, log_path = discover()
        path = Path(log_path)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise Error(f"cannot discover App Server trace path: {exc}") from exc
    if not path.is_absolute():
        raise Error("wait compatibility module returned a non-absolute trace path")
    return str(path)


def wait_session_messages(wait_runtime, caller, started_at):
    try:
        return wait_runtime.SessionMessages.from_environment(caller, started_at=started_at)
    except (wait_runtime.WaitRuntimeError, OSError, ValueError) as exc:
        raise Error(str(exc)) from exc


def wait_lock(agent):
    return f"wait-{wait_key(agent)}"


def valid_wait_record(record, agent):
    identity = record.get("identity") if isinstance(record, dict) else None
    return (isinstance(record, dict) and record.get("agent") == agent and isinstance(record.get("token"), str)
            and bool(record["token"]) and isinstance(record.get("pid"), int) and not isinstance(record["pid"], bool)
            and record["pid"] > 0 and isinstance(identity, dict)
            and isinstance(identity.get("host"), str) and isinstance(identity.get("boot_id"), str)
            and isinstance(identity.get("start_ticks"), int) and not isinstance(identity["start_ticks"], bool))


def active_wait(store, agent):
    record = store.read_wait(agent)
    if record is None:
        return None, "empty"
    if not valid_wait_record(record, agent):
        store.remove_wait(agent)
        return None, "stale"
    observation = runtime().probe_process("local", record["pid"], record["identity"])
    if observation["status"] == "stopped":
        store.remove_wait(agent)
        return None, "stale"
    return record, observation["status"]


def active_wait_records(store):
    records = []
    for path in sorted(store.waits.glob("*.json")):
        if path.is_symlink() or not re.fullmatch(r"[0-9a-f]{64}", path.stem):
            continue
        with store.lock(f"wait-{path.stem}"):
            try:
                raw = json.loads(path.read_text())
            except (OSError, ValueError):
                path.unlink(missing_ok=True)
                continue
            agent = raw.get("agent") if isinstance(raw, dict) else None
            if not isinstance(agent, str) or wait_key(agent) != path.stem:
                path.unlink(missing_ok=True)
                continue
            record, state = active_wait(store, agent)
            if record:
                records.append((record, state))
    return records


def bound_wait_agents(store):
    return {data["agent"] for data in store.all()
            if data["status"] != "archived" and isinstance(data.get("agent"), str)}


def same_wait_record(record, expected):
    return all(record.get(key) == expected.get(key) for key in ("agent", "pid", "identity", "token"))


def cancel_wait(store, agent, expected=None):
    with store.lock(wait_lock(agent)):
        record, state = active_wait(store, agent)
        if not record or (expected is not None and not same_wait_record(record, expected)):
            return {"status": "not_waiting", "agent": agent}
        if state != "running":
            raise Error("waiter identity cannot be verified")
        record["cancelled"] = now()
        store.write_wait(record)
    return {"status": "cancelled", "agent": agent}


def manager_wait_target(store):
    bindings = bound_wait_agents(store)
    candidates, unverifiable = [], []
    for record, state in active_wait_records(store):
        if record["agent"] in bindings:
            continue
        if state != "running":
            unverifiable.append(record["agent"])
        else:
            candidates.append(record)
    if unverifiable:
        raise Error("cannot verify unbound manager wait identity: " + ", ".join(sorted(unverifiable)))
    if not candidates:
        raise Error("no unbound active wait found for manager")
    if len(candidates) != 1:
        raise Error("multiple unbound active waits found for manager: "
                    + ", ".join(sorted(record["agent"] for record in candidates)))
    return candidates[0]


def wait_stop_manager(store):
    # Keep a task binding from changing while the selected unbound wait is cancelled.
    with store.lock("bindings"):
        target = manager_wait_target(store)
        return cancel_wait(store, target["agent"], expected=target)


def begin_wait(store, agent, role, task, turn_id):
    observation = runtime().probe_process("local", os.getpid())
    if observation["status"] != "running" or not isinstance(observation.get("identity"), dict):
        raise Error("cannot confirm this wait process identity")
    record = {"agent": agent, "pid": os.getpid(), "identity": observation["identity"], "token": str(uuid.uuid4()),
              "kind": "unified", "role": role, "task": task, "turn_id": turn_id, "timeout": 3600,
              "started_at": now(), "cancelled": None}
    with store.lock(wait_lock(agent)):
        existing, state = active_wait(store, agent)
        if existing:
            if state == "unknown":
                raise Error("existing wait cannot be verified")
            raise Error("AGENT-ID is already waiting")
        store.write_wait(record)
    return record


def wait_cancelled(store, record):
    with store.lock(wait_lock(record["agent"])):
        current = store.read_wait(record["agent"])
        if not current or current.get("token") != record["token"] or current.get("identity") != record["identity"]:
            raise Error("current wait registration changed unexpectedly")
        return bool(current.get("cancelled"))


def finish_wait(store, record):
    with store.lock(wait_lock(record["agent"])):
        current = store.read_wait(record["agent"])
        if current and current.get("token") == record["token"] and current.get("identity") == record["identity"]:
            store.remove_wait(record["agent"])


def wait_description(record):
    if record.get("kind") == "unified":
        role = record.get("role", "unknown")
        return f"unified {role} TASK-ID={record['task']}" if record.get("task") else f"unified {role}"
    return "legacy jobs wait"


def active_wait_states(store):
    return {record["agent"]: state for record, state in active_wait_records(store)}


def wait_unified(store, args):
    caller = wait_caller()
    try:
        from . import wait_runtime
    except ImportError as exc:
        raise Error("multi_agent_manager.wait_runtime is required for mam wait") from exc
    started_at = time.time()
    wait_compat = wait_compat_module()
    trace_path = wait_trace_path(wait_compat)
    trace = None
    messages = None
    try:
        trace = wait_runtime.TraceMessages(trace_path, started_at=started_at)
        messages = wait_session_messages(wait_runtime, caller, started_at)
        compatible = wait_compatibility(wait_compat)
        if compatible["log_path"] != trace_path:
            raise Error("App Server trace path changed while validating compatibility")

        def begin(role, task, turn_id):
            return begin_wait(store, caller, role, task, turn_id)

        return wait_runtime.wait(
            store,
            caller,
            socket_path=compatible["socket_path"],
            log_path=compatible["log_path"],
            begin_wait=begin,
            cancelled=lambda record: wait_cancelled(store, record),
            finish_wait=lambda record: finish_wait(store, record),
            active_wait_states=lambda: active_wait_states(store),
            process_probe=runtime().probe_process,
            trace=trace,
            messages=messages,
            message_floor_ms=int(started_at * 1000),
        )
    except wait_runtime.WaitRuntimeError as exc:
        raise Error(str(exc)) from exc
    finally:
        if trace is not None:
            trace.close()
        if messages is not None:
            messages.close()


def wait_list(store, args):
    records = [record for record, state in active_wait_records(store) if state == "running"]
    bindings = {data["agent"]: data for data in store.all() if data["status"] != "archived" and data["agent"]}
    return [{"agent": record["agent"], "task_title": bindings[record["agent"]]["title"] if record["agent"] in bindings else "未绑定",
             "task": bindings[record["agent"]]["id"] if record["agent"] in bindings else "未绑定",
             "waiting": wait_description(record), "started_at": record["started_at"]} for record in records]


def wait_stop(store, args):
    agent, manager = getattr(args, "agent", None), getattr(args, "manager", None)
    if (agent is None) == (manager is None):
        raise Error("choose exactly one wait stop target: manager or --agent AGENT-ID")
    if manager is not None:
        return wait_stop_manager(store)
    return cancel_wait(store, wait_agent(args))


def service_module():
    try:
        from . import wake_runtime
    except ImportError as exc:
        raise Error("multi_agent_manager.wake_runtime is required for service commands") from exc
    return wake_runtime


def service_start(store, args):
    try:
        return service_module().start_service(store.config, manager=args.manager)
    except RuntimeError as exc:
        raise Error(str(exc)) from exc


def service_stop(store, args):
    try:
        return service_module().stop_service(store.config)
    except RuntimeError as exc:
        raise Error(str(exc)) from exc


def service_status(store, args):
    try:
        return service_module().service_status(store.config)
    except RuntimeError as exc:
        raise Error(str(exc)) from exc


def task_list(store, args):
    tasks = [data for data in store.all() if args.all or (data["status"] == "archived") == args.archived]
    agents = agent_observations(data["agent"] for data in tasks if data["agent"])
    return [{**data, "agent_state": agent_state(data["agent"], agents, unbound="unbound")} for data in tasks]


def one_line(value):
    return "" if value is None else " ".join(str(value).split())


def print_table(header, rows):
    rows = list(rows)
    sys.stdout.write("\t".join(header) + "\n")
    if rows:
        sys.stdout.write("\n".join("\t".join(one_line(value) for value in row) for row in rows) + "\n")


def print_task_list(tasks):
    rows = []
    for task in tasks:
        agent = task["agent"] or "未绑定"
        state = task["agent_state"]["status"]
        rows.append("\t".join((one_line(task["title"]), one_line(task["status"]), task["id"], one_line(agent),
                              "未绑定" if state == "unbound" else one_line(state))))
    print_table(("标题", "任务状态", "TASK-ID", "AGENT-ID", "agent状态"), (row.split("\t") for row in rows))


def displayed_job_status(job):
    if job["status"] == "archived":
        return "archived"
    probe = job.get("probe")
    if not isinstance(probe, dict) or probe.get("status") not in ("running", "stopped"):
        return "unknown/待核实"
    return job["status"]


def job_started_at(job):
    identity = job.get("identity")
    started_at = job.get("started_at")
    if not started_at and isinstance(identity, dict):
        started_at = identity.get("started_at")
    return started_at or "unknown"


def print_job_list(result):
    rows = []
    for group in ("jobs", "needs_verification"):
        for job in result[group]:
            state = "unknown/待核实" if group == "needs_verification" else displayed_job_status(job)
            rows.append((job["note"], state, job_started_at(job), job["id"], job["task_title"], job["task"]))
    print_table(("描述", "job状态", "开始时间", "JOB-ID", "任务描述", "TASK-ID"), rows)


def print_wait_list(records):
    print_table(("AGENT-ID", "绑定任务标题", "TASK-ID", "等待内容", "等待开始时间"),
                ((record["agent"], record["task_title"], record["task"], record["waiting"], record["started_at"])
                 for record in records))


def print_published(document):
    sys.stdout.write(document["content"])


def ignored_link(repo, name):
    path = repo
    for part in Path(name.rstrip("/")).parts:
        path /= part
        if path.is_symlink():
            return True
    return False


def controlled_local_readme(repo):
    local = repo / ".local"
    readme = local / "README.md"
    if local.is_symlink() or not local.is_dir() or not readme.is_symlink():
        return False
    try:
        entries = list(local.iterdir())
        expected = primary(repo) / ".local" / "README.md"
        return entries == [readme] and os.readlink(readme) == str(expected)
    except OSError:
        return False


def dirty(repo):
    output = git(repo, "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--ignore-submodules=none", "--ignored=matching").stdout
    ignored, problems = [], []
    for item in output.split(b"\0"):
        if not item:
            continue
        code, name = item[:2], os.fsdecode(item[3:])
        if code == b"!!" and (name.rstrip("/").split("/", 1)[0] == ".venv" or ignored_link(repo, name)
                              or (name.rstrip("/") in (".local", ".local/README.md")
                                  and controlled_local_readme(repo))):
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
        blocked = [job["id"] for job in data["jobs"] if job["status"] != "archived"]
        if blocked:
            raise Error("archive refused; unarchived registered jobs: " + ", ".join(blocked))
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
    commands = cli.add_subparsers(required=True)
    task = command(commands, "task", "manage tasks and publications")
    sub = task.add_subparsers(dest="command", required=True)
    p = command(sub, "create", "register a TASK-ID, drafts and empty workspace")
    p.add_argument("--title", required=True, metavar="TITLE", help="short task title")
    p.add_argument("--review", metavar="TASK-ID", help="source TASK-ID; read its latest published task/report and delivery commits")
    p.set_defaults(func=create)
    p = command(sub, "bind", "bind one execution agent")
    p.add_argument("task", metavar="TASK-ID", help="registered task")
    p.add_argument("--agent", required=True, metavar="AGENT-ID", help="execution AGENT-ID; one active task per agent")
    p.set_defaults(func=bind)
    p = command(sub, "show", "read a published document")
    p.add_argument("task", metavar="TASK-ID", help="registered task")
    p.add_argument("--file", choices=("task", "report"), default="task", metavar="FILE", help="published document: task or report (default: task)")
    p.add_argument("--json", action="store_true", help="emit the published document as JSON")
    p.set_defaults(func=lambda s, a: published(s, a.task, a.file), renderer="published")
    p = command(sub, "publish", "publish one draft to the configured branch using an isolated index")
    p.add_argument("task", metavar="TASK-ID", help="registered task")
    p.add_argument("--file", choices=("task", "report"), required=True, metavar="FILE", help="draft to publish: task or report")
    p.set_defaults(func=publish)
    p = command(sub, "list", "list registered task records")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--archived", action="store_true", help="show only archived tasks")
    group.add_argument("--all", action="store_true", help="include archived tasks")
    p.set_defaults(func=task_list, renderer="task_list")
    p = command(sub, "status", "show concise task, repo and cached job status")
    p.add_argument("task", metavar="TASK-ID", help="registered task")
    p.set_defaults(func=status)
    p = command(sub, "archive", "remove owned worktrees and task branches after all jobs are archived; retain task records")
    p.add_argument("task", metavar="TASK-ID", help="registered task")
    p.add_argument("--note", required=True, metavar="NOTE", help="purpose, result or reason for this operation")
    p.set_defaults(func=archive)
    jobs = command(commands, "job", "register, query and archive process records").add_subparsers(required=True)
    p = command(jobs, "add", "register a running process with its startup identity")
    p.add_argument("task", metavar="TASK-ID", help="registered task")
    p.add_argument("--note", required=True, metavar="NOTE", help="purpose, result or reason for this operation")
    p.add_argument("--host", required=True, metavar="HOST", help="host running the process")
    p.add_argument("--pid", type=int, required=True, metavar="PID", help="running process ID")
    p.set_defaults(func=job_add)
    p = command(jobs, "list", "query process and agent states; never wake agents")
    p.add_argument("--task", metavar="TASK-ID", help="filter jobs by TASK-ID")
    p.add_argument("--status", choices=("running", "stopped", "archived", "all"), metavar="STATUS", help="filter jobs; default excludes archived records")
    p.add_argument("--attention", action="store_true", help="show stopped jobs with inactive agents; list unknowns separately")
    p.set_defaults(func=job_list, renderer="job_list")
    p = command(jobs, "status", "refresh and show one registered process summary as JSON")
    p.add_argument("job", metavar="JOB-ID", help="registered job")
    p.set_defaults(func=job_status)
    p = command(jobs, "archive", "archive one registered job; retain history without probing or stopping its process")
    p.add_argument("job", metavar="JOB-ID", help="registered job")
    p.add_argument("--note", required=True, metavar="NOTE", help="purpose, result or reason for this operation")
    p.set_defaults(func=job_archive)
    wait = command(commands, "wait", "wait for this agent's MAM work and manage wakeups")
    wait.set_defaults(func=wait_unified)
    waits = wait.add_subparsers(dest="wait_command")
    p = command(waits, "list", "list current waits")
    p.set_defaults(func=wait_list, renderer="wait_list")
    p = command(waits, "stop", "wake one waiter without changing its monitored jobs")
    p.add_argument("manager", nargs="?", choices=("manager",), help="stop the unique unbound manager wait")
    p.add_argument("--agent", metavar="AGENT-ID", help="waiter AGENT-ID")
    p.set_defaults(func=wait_stop)
    service = command(commands, "service", "manage the project-local proactive wakeup scheduler").add_subparsers(required=True)
    p = command(service, "start", "start the detached project-local scheduler")
    p.add_argument("--manager", metavar="AGENT-ID", help="explicit Manager identity for an existing project")
    p.set_defaults(func=service_start)
    p = command(service, "stop", "gracefully stop this project's scheduler")
    p.set_defaults(func=service_stop)
    p = command(service, "status", "show scheduler health, pending items and diagnostics")
    p.set_defaults(func=service_status)
    w = command(commands, "workspace", "manage repository worktrees and their environments").add_subparsers(required=True)
    p = command(w, "add", "create a repository worktree using its local environment entry")
    p.add_argument("task", metavar="TASK-ID", help="registered task")
    p.add_argument("--repo", required=True, metavar="REPO", help="single source repository directory below PROJECT_ROOT")
    p.add_argument("--base", required=True, metavar="COMMIT", help="base commit for the task branch")
    p.set_defaults(func=workspace_add)
    return cli


def main(argv=None, *, cwd=None):
    args = parser().parse_args(argv)
    try:
        if getattr(args, "task", None):
            identifier(args.task)
        result = args.func(Store(project_config(cwd)), args)
        if getattr(args, "renderer", None) == "task_list":
            print_task_list(result)
        elif getattr(args, "renderer", None) == "job_list":
            print_job_list(result)
        elif getattr(args, "renderer", None) == "wait_list":
            print_wait_list(result)
        elif getattr(args, "renderer", None) == "published" and not args.json:
            print_published(result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
