"""Local task records, Git publication and workspace archival."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
from dataclasses import dataclass, field
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import uuid

from .job_runtime import job_status as normalize_job_status

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
    if not isinstance(ref, str) or not ref or ref.startswith("-"):
        raise Error(f"invalid commit: {ref}")
    return value(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")


def branch_exists(repo, branch):
    return git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0


@dataclass(frozen=True)
class ProjectConfig:
    mam_root: Path
    project_root: Path
    branch: str
    hook_timeouts: dict[str, float] = field(default_factory=dict)


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
    timeouts = data.get("HOOK_TIMEOUTS", {})
    if not isinstance(timeouts, dict):
        raise Error("HOOK_TIMEOUTS must be an object")
    for event, seconds in timeouts.items():
        if event not in ("workspace_add", "before_task_archive"):
            raise Error(f"unknown HOOK_TIMEOUTS event: {event}")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
            raise Error(f"HOOK_TIMEOUTS.{event} must be a positive finite number of seconds")
    return ProjectConfig(mam_root=mam_root, project_root=project_root, branch=branch, hook_timeouts=timeouts)


class Store:
    def __init__(self, config):
        if not isinstance(config, ProjectConfig):
            raise Error("Store requires a project configuration")
        self.config = config
        self.root = config.mam_root
        self.project_root = config.project_root
        self.branch = config.branch
        self.state = safe_path(self.root / ".local" / "tasks")
        self.logs = safe_path(self.root / ".tasks")
        self.workspaces = safe_path(self.project_root / "workspace")
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

    def doc(self, task, kind):
        return safe_path(self.logs / identifier(task) / f"{kind}.md")


def published(store, task, kind):
    path = f".tasks/{identifier(task)}/{kind}.md"
    commit = head(store.root, store.branch)
    result = git(store.root, "show", f"{commit}:{path}", check=False)
    if result.returncode:
        raise Error(f"no published {kind} for TASK-ID {task} at {commit}")
    blob = value(store.root, "rev-parse", f"{commit}:{path}")
    revision = value(store.root, "log", "-1", "--format=%H", commit, "--", path)
    if kind == "report":
        recorded = store.read(task).get("report")
        candidate = recorded.get("revision") if isinstance(recorded, dict) else None
        if (isinstance(candidate, str) and re.fullmatch(r"[0-9a-f]{40,64}", candidate)
                and git(store.root, "merge-base", "--is-ancestor", candidate, commit, check=False).returncode == 0
                and git(store.root, "merge-base", "--is-ancestor", revision, candidate, check=False).returncode == 0
                and value(store.root, "rev-parse", f"{candidate}:{path}") == blob):
            revision = candidate
    return {"revision": revision, "content": result.stdout.decode(), "blob": blob}


def optional_doc(store, task, kind):
    try:
        return published(store, task, kind)
    except Error:
        return None


def caller_identity():
    from . import identity
    try:
        return identity.read(caller_agent())
    except identity.IdentityError as exc:
        raise Error(str(exc)) from exc


def task_target(store, target, *, include_archived=False):
    """Resolve a TASK-ID or a path only within the caller's native tree."""
    if target is None:
        caller = caller_agent()
        found = [data for data in store.all()
                 if (include_archived or data.get("status") != "archived") and data.get("agent") == caller]
        if len(found) != 1:
            raise Error("current executor has no unique active task; specify TASK-ID")
        return found[0]["id"]
    if not target.startswith("/"):
        return identifier(target)
    current = caller_identity()
    matches = []
    for data in store.all():
        if (not include_archived and data.get("status") == "archived") or not data.get("agent"):
            continue
        known = data.get("identity")
        if not isinstance(known, dict) or not known.get("tree_root") or not known.get("path"):
            from . import identity
            try:
                observed = identity.read(data["agent"])
            except identity.IdentityError as exc:
                raise Error(f"cannot verify legacy executor identity for {data['id']}: {exc}") from exc
            known = {"path": observed.path, "tree_root": observed.tree_root}
        if known["tree_root"] == current.tree_root and known["path"] == target:
            matches.append(data["id"])
    if len(matches) != 1:
        raise Error(f"native path {target} has {len(matches)} matching active tasks in this collaboration tree")
    return matches[0]


def task_link(store, data):
    workspace = safe_path(data["workspace"])
    workspace.mkdir(parents=True, exist_ok=True)
    link = workspace / ".task"
    target = safe_path(store.logs / identifier(data["id"]))
    if not target.is_dir():
        raise Error(f"task directory is missing: {target}")
    if link.is_symlink():
        if os.readlink(link) != str(target):
            raise Error(f"conflicting .task link: {link}")
    elif link.exists():
        raise Error(f"conflicting .task path: {link}")
    else:
        link.symlink_to(target, target_is_directory=True)
    return link


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


def hook_context(store, data, event, *, repo=None, options=None):
    delivery = (data.get("report") or {}).get("commits") or {}
    repos = []
    for name, record in data["repos"].items():
        repos.append({"name": name, **{key: record.get(key) for key in
                      ("source", "path", "branch", "base", "state", "removed", "branch_removed")},
                      "commit": delivery.get(name)})
    return {"schema_version": 1, "event": event, "project_root": str(store.project_root),
            "mam_root": str(store.root),
            "task": {"id": data["id"], "title": data["title"], "status": data["status"],
                     "workspace": data["workspace"], "task_dir": str(store.logs / data["id"])},
            "repos": repos, "repo": repo,
            "jobs": [{**job_summary(job), **{key: job.get(key) for key in ("host", "pid", "started_at")}}
                     for job in data["jobs"]],
            "options": options or {"note": None, "force": False}}


def project_hook(store, data, event, *, required=False, repo=None, options=None):
    if os.environ.get("MAM_HOOK_ACTIVE"):
        raise Error("MAM hook cannot invoke workspace add or task archive recursively")
    entry = store.root / ".local" / "hooks" / event
    if not entry.exists() and not entry.is_symlink():
        if required:
            raise Error(f"required project hook is missing: {entry}")
        return
    safe_path(entry)
    if not entry.is_file() or not os.access(entry, os.X_OK):
        raise Error(f"project hook must be an executable regular file: {entry}")
    timeout = store.config.hook_timeouts.get(event, {"workspace_add": 1800, "before_task_archive": 60}[event])
    payload = json.dumps(hook_context(store, data, event, repo=repo, options=options)).encode()
    env = {**os.environ, "MAM_HOOK_ACTIVE": event}
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            process = subprocess.Popen([str(entry)], cwd=store.root, stdin=subprocess.PIPE,
                                       stdout=stdout, stderr=stderr, env=env, start_new_session=True)
            try:
                process.communicate(payload, timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.communicate()
                raise Error(f"project hook {event} timed out after {timeout:g} seconds")
        except OSError as exc:
            raise Error(f"project hook {event} could not start: {exc}") from exc
        if process.returncode:
            stderr.seek(0, os.SEEK_END)
            stderr.seek(max(0, stderr.tell() - 3000))
            stdout.seek(0, os.SEEK_END)
            stdout.seek(max(0, stdout.tell() - 3000))
            detail = (stderr.read() or stdout.read()).decode(errors="replace").strip()
            raise Error(f"project hook {event} exited {process.returncode}: {detail[:3000]}")


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
        args.review = task_target(store, args.review)
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
    data = {"id": task, "title": args.title, "agent": None, "status": "pending", "created_at": now(),
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
            (draft.parent / "files").mkdir(exist_ok=True)
            task_link(store, data)
        except OSError as exc:
            data["error"] = str(exc)
            store.write(data)
            raise Error(f"creation incomplete; TASK-ID {task} remains registered: {exc}")
    return {**data, "task_file": str(store.doc(task, "task")), "report_file": str(store.doc(task, "report"))}


def bind(store, args):
    if args.agent != caller_agent():
        raise Error("task bind may only register the calling executor; use task start")
    return start(store, args)


def start(store, args):
    identity = caller_identity()
    if identity.path == "/root":
        raise Error("task start requires a native subagent executor")
    from . import wake_runtime
    task = task_target(store, args.task)
    with wake_runtime.task_rebind_lock(store, task):
        if wake_runtime.recorded_manager(store) == identity.agent:
            raise Error("the recorded Manager cannot become a task executor")
        data = store.read(task, writable=True)
        if data.get("status") == "archived":
            raise Error("archived tasks cannot be started")
        conflicts = [item["id"] for item in store.all() if item["id"] != task and
                     item["status"] != "archived" and item.get("agent") == identity.agent]
        if conflicts:
            raise Error("executor is already bound to another task: " + ", ".join(conflicts))
        current = data.get("agent")
        if current and current != identity.agent:
            states = agent_observations([current])
            _rebind_quiescent(current, agent_state(current, states), role="current executor")
            data.setdefault("handoffs", []).append({
                "from_agent": current, "to_agent": identity.agent, "at": now(),
                "note": "replacement executor started", "manager": wake_runtime.recorded_manager(store),
            })
        task_link(store, data)
        changed = current != identity.agent or data["status"] != "working" or data.get("identity") != {
            "path": identity.path, "tree_root": identity.tree_root,
        }
        old_status = data.get("status")
        data["agent"] = identity.agent
        data["identity"] = {"path": identity.path, "tree_root": identity.tree_root}
        data["status"] = "working"
        if old_status != "working":
            data["wake_reminder_count"] = 0
        if changed:
            store.write(data)
    return {"id": task, "agent": identity.agent, "path": identity.path,
            "tree_root": identity.tree_root, "status": data["status"], "workspace": data["workspace"],
            "unchanged": not changed}


def rebind_agent(value, *, field="--agent"):
    """Return one well-formed Agent identity for a task handoff."""

    if not isinstance(value, str) or not value or value != value.strip() or any(character in value for character in "\r\n\t"):
        raise Error(f"{field} must be a non-empty single-line AGENT-ID")
    return value


def rebind_note(value):
    if not isinstance(value, str) or not value.strip():
        raise Error("--note must describe the executor handoff")
    return value


def _rebind_quiescent(agent, state, *, role):
    status = state.get("status") if isinstance(state, dict) else None
    detail = state.get("error") if isinstance(state, dict) and isinstance(state.get("error"), str) else None
    if status in {"idle", "notLoaded"} and not detail:
        return
    if status == "active":
        if role == "replacement agent":
            raise Error("replacement agent is active; finish its read-only preparation before rebind")
        raise Error(f"{role} is active; wait for its current turn to end before rebind")
    message = f"cannot verify {role} state ({status or 'unknown'})"
    if detail:
        message += f": {detail}"
    raise Error(message + "; retry after the App Server can confirm the thread")


def rebind(store, args):
    """Atomically hand an existing task and its retained workspace to an agent.

    The manager must prove both threads are dormant while the binding is replaced.
    """

    task = task_target(store, args.task)
    replacement = rebind_agent(args.agent)
    note = rebind_note(args.note)
    caller = rebind_agent(os.environ.get("CODEX_THREAD_ID"), field="CODEX_THREAD_ID")
    try:
        from . import wake_runtime
    except ImportError as exc:
        raise Error("multi_agent_manager.wake_runtime is required for task rebind") from exc

    # The scheduler owns these first two locks for a complete cycle.  Taking
    # them before bindings prevents a delivery to the old executor between its
    # final quiescence observation and the durable binding replacement.
    with wake_runtime.task_rebind_lock(store, task):
        try:
            manager = wake_runtime.resolve_manager(store)
        except RuntimeError as exc:
            raise Error(str(exc)) from exc
        if manager is None:
            raise Error("task rebind requires a recorded Manager; run mam service start --manager AGENT-ID first")
        if caller != manager:
            raise Error("task rebind must be called by the recorded Manager")
        from . import identity as thread_identity
        try:
            manager_identity = thread_identity.read(caller)
        except thread_identity.IdentityError as exc:
            raise Error(str(exc)) from exc
        if manager_identity.path != "/root" or manager_identity.tree_root != caller:
            raise Error("task rebind requires the recorded native root Manager")
        if replacement == manager:
            raise Error("replacement agent is the recorded Manager")
        try:
            replacement_identity = thread_identity.read(replacement)
        except thread_identity.IdentityError as exc:
            raise Error(str(exc)) from exc
        if replacement_identity.path == "/root" or replacement_identity.tree_root == replacement:
            raise Error("replacement executor must be a native subagent")

        data = store.read(task, writable=True)
        current = data.get("agent")
        if not current:
            raise Error("task has no current executor; use task bind instead")
        current = rebind_agent(current, field="current task executor")
        conflicts = [
            item["id"]
            for item in store.all()
            if item.get("id") != task and item.get("status") != "archived" and item.get("agent") == replacement
        ]
        if conflicts:
            raise Error("replacement agent is already bound to another task: " + ", ".join(conflicts))

        # A repeated Manager command is safe after a lost CLI response.  It
        # does not re-probe a newly active replacement or append another audit
        # row; the previous handoff remains the durable result.
        if current == replacement:
            return {**data, "unchanged": True}

        try:
            observations = agent_observations([current, replacement])
        except Exception as exc:
            raise Error(f"cannot verify executor thread states: {exc}") from exc
        _rebind_quiescent(current, agent_state(current, observations), role="current executor")
        _rebind_quiescent(replacement, agent_state(replacement, observations), role="replacement agent")
        handoffs = data.get("handoffs")
        if handoffs is None:
            handoffs = []
            data["handoffs"] = handoffs
        if not isinstance(handoffs, list):
            raise Error("task handoff audit is invalid")
        handoffs.append({
            "from_agent": current,
            "to_agent": replacement,
            "at": now(),
            "note": note,
            "manager": caller,
        })
        data["agent"] = replacement
        data["identity"] = {"path": replacement_identity.path, "tree_root": replacement_identity.tree_root}
        data["status"] = "working"
        store.write(data)
    return data


def workspace_add(store, args):
    if os.environ.get("MAM_HOOK_ACTIVE"):
        raise Error("MAM hook cannot invoke workspace add recursively")
    name = repository_name(args.repo)
    with store.lock(args.task):
        data = store.read(args.task, writable=True)
        task_link(store, data)
        source = safe_path(store.project_root / name)
        if primary(source) != source:
            raise Error(f"source is not a primary checkout: {source}")
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
            project_hook(store, data, "workspace_add", required=True, repo=name)
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


def files_snapshot(store, task):
    root = safe_path(store.logs / identifier(task) / "files")
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise Error(f"invalid task files directory: {root}")
    entries = {}
    if not root.exists():
        return entries
    for directory, folders, names in os.walk(root, followlinks=False):
        for name in folders:
            if (Path(directory) / name).is_symlink():
                raise Error("task files cannot contain symlinked directories")
        for name in names:
            path = Path(directory) / name
            if not stat.S_ISREG(path.lstat().st_mode):
                raise Error(f"task files must be regular files: {path}")
            relative = path.relative_to(store.root).as_posix()
            mode = "100755" if path.stat().st_mode & 0o111 else "100644"
            entries[relative] = (mode, path.read_bytes())
    return entries


def published_files(store, task):
    prefix = f".tasks/{identifier(task)}/files/"
    output = git(store.root, "ls-tree", "-r", "-z", store.branch, "--", prefix).stdout
    entries = {}
    for row in output.split(b"\0"):
        if not row:
            continue
        meta, raw = row.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        path = os.fsdecode(raw)
        if not path.startswith(prefix) or kind != "blob" or mode not in ("100644", "100755"):
            raise Error(f"published task files contain an unsupported entry: {path}")
        entries[path] = (mode, blob)
    return entries


def draft_file_blobs(store, files):
    return {path: (mode, git(store.root, "hash-object", "--stdin", input=content).stdout.decode().strip())
            for path, (mode, content) in files.items()}


def sync_files_index(store, task, files):
    prefix = f".tasks/{identifier(task)}/files/"
    output = git(store.root, "ls-files", "--cached", "-z", "--", prefix).stdout
    staged = {os.fsdecode(path) for path in output.split(b"\0") if path}
    for path in staged - files.keys():
        git(store.root, "update-index", "--force-remove", "--", path)
    for path, (mode, blob) in files.items():
        git(store.root, "update-index", "--add", "--cacheinfo", mode, blob, path)


def publish_draft(store, args, kind):
    with store.lock(args.task), store.lock("publish"):
        publish_branch(store)
        data = store.read(args.task, writable=True)
        if kind == "report":
            observations = agent_observations([data["agent"]] if data.get("agent") else [])
            from .task_state import refresh_state
            updated, _, _ = refresh_state(data, agent_state(data.get("agent"), observations))
            if updated != data:
                data = updated
                store.write(data)
            if data.get("status") not in {"working", "pending"}:
                raise Error("report refused; task must be working or pending")
            unarchived = [job.get("id") for job in data.get("jobs", [])
                          if isinstance(job, dict) and job.get("status") != "archived"]
            if unarchived:
                raise Error("report refused; unarchived registered jobs: " + ", ".join(unarchived))
        draft = store.doc(args.task, kind)
        if not draft.is_file():
            raise Error(f"missing draft: {draft}")
        content = draft.read_bytes()
        report = None
        current_files, file_draft, file_blobs = {}, {}, {}
        if kind == "report":
            delivery = {}
            for name, record in data["repos"].items():
                try:
                    _, path, _ = repo_context(store, data, name, record)
                    if primary(path) == Path(record["source"]) and value(path, "rev-parse", "--show-toplevel") == str(path):
                        delivery[name] = head(path)
                except (Error, OSError):
                    continue
            report = {"commits": delivery}
            file_draft = files_snapshot(store, args.task)
            current_files = published_files(store, args.task)
            file_blobs = draft_file_blobs(store, file_draft)
        path = f".tasks/{args.task}/{kind}.md"
        existing = optional_doc(store, args.task, kind)
        if existing and existing["content"].encode() == content and current_files == file_blobs:
            git(store.root, "update-index", "--add", "--cacheinfo", "100644", existing["blob"], path)
            if report is not None:
                sync_files_index(store, args.task, file_blobs)
                data["report"] = {**report, "revision": existing["revision"]}
                store.write(data)
            return {"id": args.task, "file": kind, "revision": existing["revision"], "unchanged": True}
        parent = head(store.root, store.branch)
        for _, attachment in file_draft.values():
            git(store.root, "hash-object", "-w", "--stdin", input=attachment)
        with tempfile.TemporaryDirectory(prefix="task-publish-") as temporary:
            env = {**os.environ, "GIT_INDEX_FILE": str(Path(temporary) / "index")}
            git(store.root, "read-tree", parent, env=env)
            blob = git(store.root, "hash-object", "-w", "--stdin", input=content).stdout.decode().strip()
            git(store.root, "update-index", "--add", "--cacheinfo", "100644", blob, path, env=env)
            for file_path in current_files.keys() - file_blobs.keys():
                git(store.root, "update-index", "--force-remove", "--", file_path, env=env)
            for file_path, (mode, file_blob) in file_blobs.items():
                git(store.root, "update-index", "--add", "--cacheinfo", mode, file_blob, file_path, env=env)
            tree = git(store.root, "write-tree", env=env).stdout.decode().strip()
            commit = git(store.root, "commit-tree", tree, "-p", parent, "-m", f"Publish {args.task} {kind}").stdout.decode().strip()
            git(store.root, "update-ref", f"refs/heads/{store.branch}", commit, parent)
        if report is not None:
            data["report"] = {**report, "revision": commit}
        store.write(data)
        # Update only this entry; Git locks the shared index and keeps other entries.
        # Use the published blob so an edit made during publication stays a draft.
        git(store.root, "update-index", "--add", "--cacheinfo", "100644", blob, path)
        if report is not None:
            sync_files_index(store, args.task, file_blobs)
    result = {"id": args.task, "file": kind, "revision": commit, "report": report}
    if kind == "report":
        result.update(added=sorted(file_blobs.keys() - current_files.keys()),
                      updated=sorted(path for path in file_blobs.keys() & current_files.keys()
                                     if file_blobs[path] != current_files[path]),
                      deleted=sorted(current_files.keys() - file_blobs.keys()))
    return result


def publish(store, args):
    return publish_draft(store, args, "task")


def report(store, args):
    return publish_draft(store, args, "report")


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
        observation["status"] = normalize_job_status(observation.get("status"))
        job["probe"] = observation
        identity = observation.get("identity")
        if not job.get("started_at") and isinstance(identity, dict) and identity.get("started_at"):
            job["started_at"] = identity["started_at"]
        if observation["status"] in ("running", "exited"):
            job["status"] = observation["status"]
            job["checked_at"] = observation["checked_at"]
    from .task_state import refresh_state
    updated, _, _ = refresh_state(data, None)
    data.update(updated)


def job_add(store, args):
    if args.pid <= 0:
        raise Error("PID must be positive")
    with store.lock(args.task):
        data = store.read(args.task, writable=True)
        if data.get("status") == "archived":
            raise Error("archived tasks cannot register jobs")
        observation = runtime().probe_process(args.host, args.pid)
        if observation["status"] != "running" or not observation.get("identity") or observation.get("error"):
            raise Error(f"cannot register process without confirmed running identity: {observation}")
        job = {"id": str(uuid.uuid4()), "note": args.note, "host": args.host, "pid": args.pid,
               "identity": observation["identity"], "status": "running", "checked_at": observation["checked_at"],
               "started_at": observation["identity"].get("started_at"), "probe": observation, "archive": None}
        data["jobs"].append(job)
        if data.get("status") != "working":
            data["status"] = "working"
            data["wake_reminder_count"] = 0
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
    paths = {}
    for item in tasks:
        with store.lock(item["id"]):
            data = store.read(item["id"])
            known = data.get("identity")
            if isinstance(known, dict) and known.get("path"):
                paths[data["id"]] = known["path"]
            if data["status"] == "archived" and args.attention:
                continue
            jobs = static_jobs(data, args)
            current = [job for job in jobs if job["status"] != "archived"]
            if current and data["status"] != "archived":
                refresh_jobs(data, current)
                store.write(data)
            entries.extend((data["id"], data["title"], data["agent"], data["status"], job) for job in jobs)
    if args.status in ("running", "exited", "stopped"):
        requested = normalize_job_status(args.status)
        entries = [entry for entry in entries if normalize_job_status(entry[4]["status"]) == requested]
    if args.attention:
        agents = agent_observations(
            agent for _, _, agent, task_status, job in entries
            if task_status != "archived" and normalize_job_status(job["probe"]["status"]) == "exited" and agent
        )
    else:
        agents = agent_observations(
            agent for _, _, agent, task_status, job in entries
            if task_status != "archived" and job["status"] != "archived" and agent
        )
    selected, uncertain = [], []
    for task, task_title, agent, _, job in entries:
        row = {"task": task, "task_title": task_title, "agent": agent, **job}
        if task in paths:
            row["agent_path"] = paths[task]
        row["agent_state"] = agent_state(agent, agents)
        if args.attention:
            if row["status"] == "archived":
                continue
            if normalize_job_status(row["probe"]["status"]) not in ("running", "exited"):
                uncertain.append(row)
            elif normalize_job_status(row["status"]) == "exited":
                if row["agent_state"]["status"] == "unknown" or row["agent_state"].get("error"):
                    uncertain.append(row)
                elif row["agent_state"]["status"] != "active":
                    selected.append(row)
        else:
            selected.append(row)
    for row in selected + uncertain:
        row["status"] = normalize_job_status(row["status"])
        if isinstance(row.get("probe"), dict):
            row["probe"] = {**row["probe"], "status": normalize_job_status(row["probe"].get("status"))}
    return {"jobs": selected, "needs_verification": uncertain}


def saved_job_state(job):
    """Return the saved observation shown by task status without probing."""

    probe = job.get("probe")
    if job.get("status") != "archived" and isinstance(probe, dict) and probe.get("status") == "unknown":
        return "unknown", probe.get("checked_at") or job.get("checked_at")
    return normalize_job_status(job.get("status", "unknown")), job.get("checked_at")


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
    from .task_state import REMINDER_LIMIT, reminder_count
    count = reminder_count(data)
    result["wake_reminder_count"] = count
    result["wake_reminder_limit"] = REMINDER_LIMIT
    if count >= REMINDER_LIMIT:
        result["reminder_status"] = "Reminder limit reached"
    if data.get("status") == "blocked" and data.get("block_note"):
        result["block_note"] = data["block_note"]
    known = data.get("identity")
    if isinstance(known, dict) and known.get("path") and known.get("tree_root"):
        result["agent_path"] = known["path"]
        result["tree_root"] = known["tree_root"]
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
    handoffs = data.get("handoffs")
    if isinstance(handoffs, list):
        displayed_handoffs = []
        for handoff in handoffs:
            if not isinstance(handoff, dict):
                continue
            row = {
                key: handoff[key]
                for key in ("from_agent", "to_agent", "at", "note", "manager")
                if handoff.get(key) is not None
            }
            if row:
                displayed_handoffs.append(row)
        if displayed_handoffs:
            result["handoffs"] = displayed_handoffs
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
    stored_status = normalize_job_status(job.get("status", "unknown"))
    probe = job.get("probe") if isinstance(job.get("probe"), dict) else {}
    observed_status = normalize_job_status(probe.get("status"))
    status, checked_at, error = stored_status, job.get("checked_at"), None
    if stored_status != "archived" and observed_status in ("running", "exited"):
        status = observed_status
        checked_at = probe.get("checked_at") or checked_at
        error = probe.get("error")
    elif stored_status != "archived" and observed_status == "unknown":
        status = "unknown"
        checked_at = probe.get("checked_at") or checked_at
        error = probe.get("error")
    result = {"id": job["id"], "note": job.get("note"), "task": data["id"], "task_title": data["title"],
              "agent": data.get("agent"), "host": job.get("host"), "pid": job.get("pid"), "status": status}
    known = data.get("identity")
    if isinstance(known, dict) and known.get("path"):
        result["agent_path"] = known["path"]
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
                from .task_state import refresh_state
                observations = agent_observations([data["agent"]] if data.get("agent") else [])
                updated, _, _ = refresh_state(data, agent_state(data.get("agent"), observations))
                data.update(updated)
                store.write(data)
            return job
    raise Error(f"JOB-ID is not registered: {args.job}")


def status(store, args):
    if os.environ.get("MAM_HOOK_ACTIVE"):
        data = store.read(args.task)
    else:
        with store.lock(args.task):
            data = store.read(args.task)
            if data.get("status") != "archived":
                data = store.read(args.task, writable=True)
                observations = agent_observations([data["agent"]] if data.get("agent") else [])
                from .task_state import refresh_state
                updated, _, _ = refresh_state(data, agent_state(data.get("agent"), observations))
                if updated != data:
                    data = updated
                    store.write(data)
    docs = {kind: optional_doc(store, args.task, kind) for kind in ("task", "report")}
    drafts = {}
    for kind, document in docs.items():
        path = store.doc(args.task, kind)
        drafts[kind] = path.exists() and (document is None or path.read_text() != document["content"])
    files = files_snapshot(store, args.task)
    committed = published_files(store, args.task)
    drafts["files"] = draft_file_blobs(store, files) != committed
    return render_task_status(data, docs, drafts)


def caller_agent():
    agent = os.environ.get("CODEX_THREAD_ID")
    if not isinstance(agent, str) or not agent or agent != agent.strip() or any(char in agent for char in "\r\n\t"):
        raise Error("CODEX_THREAD_ID must be a non-empty canonical AGENT-ID")
    try:
        if str(uuid.UUID(agent)) != agent:
            raise ValueError()
    except ValueError:
        raise Error("CODEX_THREAD_ID must be a canonical AGENT-ID") from None
    return agent


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


def service_set(store, args):
    try:
        return service_module().set_message_channel(store.config, args.value)
    except RuntimeError as exc:
        raise Error(str(exc)) from exc


def message_send(store, args):
    sender = caller_identity()
    task = task_target(store, args.task) if args.task else None
    if task:
        store.read(task)
    else:
        bound = [item["id"] for item in store.all()
                 if item.get("status") != "archived" and item.get("agent") == sender.agent]
        task = bound[0] if len(bound) == 1 else None
    try:
        return service_module().enqueue_message(
            store, sender=sender.agent, sender_path=sender.path, sender_tree=sender.tree_root,
            message=args.message, defer=not args.immediate, task=task,
        )
    except RuntimeError as exc:
        raise Error(str(exc)) from exc


def service_rebind_manager(store, args):
    try:
        return service_module().rebind_manager(store, args.note)
    except RuntimeError as exc:
        raise Error(str(exc)) from exc


def service_upgrade(store, args):
    try:
        return service_module().service_upgrade(store.config)
    except RuntimeError as exc:
        raise Error(str(exc)) from exc


def task_list(store, args):
    from .task_state import refresh_state
    tasks = store.all()
    agents = agent_observations(data["agent"] for data in tasks if data.get("agent"))
    refreshed = []
    for item in tasks:
        if os.environ.get("MAM_HOOK_ACTIVE") or item.get("status") == "archived":
            data = item
            observation = agent_state(data.get("agent"), agents, unbound="unbound")
        else:
            with store.lock(item["id"]):
                data = store.read(item["id"])
                if data.get("status") == "archived":
                    observation = agent_state(data.get("agent"), agents, unbound="unbound")
                    if args.all or args.archived:
                        refreshed.append({**data, "agent_state": observation})
                    continue
                data = store.read(item["id"], writable=True)
                observation = agent_state(data.get("agent"), agents, unbound="unbound")
                updated, _, _ = refresh_state(data, observation)
                if updated != data:
                    data = updated
                    store.write(data)
        if args.all or (data["status"] == "archived") == args.archived:
            refreshed.append({**data, "agent_state": observation})
    return refreshed


def task_block(store, args):
    from . import wake_runtime
    from .task_state import confirmed_idle, refresh_state, set_blocked
    caller = caller_agent()
    try:
        manager = wake_runtime.resolve_manager(store)
    except RuntimeError as exc:
        raise Error(str(exc)) from exc
    if manager is None or caller != manager:
        raise Error("task block must be called by the recorded Manager")
    identity = caller_identity()
    if identity.path != "/root" or identity.tree_root != caller:
        raise Error("task block requires the recorded native root Manager")
    if not isinstance(args.note, str) or not args.note.strip():
        raise Error("--note must describe why the task is blocked")
    with store.lock(args.task):
        data = store.read(args.task, writable=True)
        observations = agent_observations([data["agent"]] if data.get("agent") else [])
        executor_state = agent_state(data.get("agent"), observations)
        updated, _, _ = refresh_state(data, executor_state)
        if updated != data:
            data = updated
            store.write(data)
        if data.get("status") != "pending":
            raise Error("task block requires a pending task")
        if data.get("agent") and not confirmed_idle(executor_state):
            raise Error("task block requires a confirmed idle executor")
        data = set_blocked(data, args.note.strip())
        store.write(data)
    return {"id": args.task, "status": data["status"], "block_note": data["block_note"],
            "wake_reminder_count": data.get("wake_reminder_count", 0)}


def show(store, args):
    return published(store, args.task, args.file)


def one_line(value):
    return "" if value is None else " ".join(str(value).split())


def print_table(header, rows):
    rows = list(rows)
    sys.stdout.write("\t".join(header) + "\n")
    if rows:
        sys.stdout.write("\n".join("\t".join(one_line(value) for value in row) for row in rows) + "\n")


def print_task_list(tasks):
    from .task_state import REMINDER_LIMIT, reminder_count
    rows = []
    for task in tasks:
        agent = task.get("identity", {}).get("path") or task["agent"] or "未绑定"
        state = task["agent_state"]["status"]
        rows.append("\t".join((one_line(task["title"]), one_line(task["status"]), task["id"], one_line(agent),
                              "未绑定" if state == "unbound" else one_line(state),
                              f"{reminder_count(task)}/{REMINDER_LIMIT}",
                              "Reminder limit reached" if reminder_count(task) >= REMINDER_LIMIT else "",
                              one_line(task.get("block_note") if task.get("status") == "blocked" else None))))
    print_table(("标题", "任务状态", "TASK-ID", "执行者", "agent状态", "提醒次数", "提醒状态", "阻断说明"),
                (row.split("\t") for row in rows))


def displayed_job_status(job):
    if job["status"] == "archived":
        return "archived"
    probe = job.get("probe")
    if not isinstance(probe, dict) or normalize_job_status(probe.get("status")) not in ("running", "exited"):
        return "unknown/待核实"
    return normalize_job_status(job["status"])


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
            rows.append((job["note"], state, job_started_at(job), job["id"], job["task_title"], job["task"],
                         job.get("agent_path") or job.get("agent") or "未绑定"))
    print_table(("描述", "job状态", "开始时间", "JOB-ID", "任务描述", "TASK-ID", "执行者"), rows)


def print_published(document):
    sys.stdout.write(document["content"])


def archive_preflight(store, data):
    blocked = [job["id"] for job in data["jobs"] if job["status"] != "archived"]
    if blocked:
        raise Error("archive refused; unarchived registered jobs: " + ", ".join(blocked))
    relative = f".tasks/{identifier(data['id'])}"
    if git(store.root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", relative).stdout:
        raise Error(f"archive refused; task directory has uncommitted Git changes: {relative}")


def archive_repo_context(store, data, name, record):
    name = repository_name(name)
    source = safe_path(store.project_root / name)
    path = Path(data["workspace"]) / name
    branch = f"task/{identifier(data['id'])}"
    if record["source"] != str(source) or record["path"] != str(path) or record["branch"] != branch:
        raise Error(f"registration has inconsistent repo/path/branch: {name}")
    if primary(source) != source:
        raise Error(f"source is not a primary checkout: {source}")
    return source, path, branch


def remove_task_worktree(source, path, *, force):
    registrations = git(source, "worktree", "list", "--porcelain").stdout.decode().splitlines()
    if f"worktree {path}" not in registrations:
        return False
    args = ("worktree", "remove", "--force", str(path)) if force else ("worktree", "remove", str(path))
    git(source, *args)
    return True


def archive(store, args):
    if os.environ.get("MAM_HOOK_ACTIVE"):
        raise Error("MAM hook cannot invoke task archive recursively")
    with store.lock(args.task):
        data = store.read(args.task)
        if data["status"] == "archived":
            return data["archive"]
        from .task_state import refresh_state
        updated, _, _ = refresh_state(data, None)
        if updated != data:
            data = updated
            store.write(data)
        archive_preflight(store, data)
        force = bool(getattr(args, "force", False))
        project_hook(store, data, "before_task_archive", options={"note": args.note, "force": force})
        data = store.read(args.task)
        archive_preflight(store, data)
        workspace = Path(data["workspace"])
        result = data["archive"] or {"note": args.note, "removed": [], "at": None}
        data["archive"] = result
        try:
            for name, record in data["repos"].items():
                source, path, branch = archive_repo_context(store, data, name, record)
                if not record["removed"] or path.exists() or path.is_symlink():
                    if remove_task_worktree(source, path, force=force):
                        result["removed"].append({"worktree": str(path)})
                    record["removed"] = True
                    store.write(data)
                if branch_exists(source, branch):
                    git(source, "branch", "-D" if force else "-d", "--", branch)
                    result["removed"].append({"repo": name, "branch": branch})
                if not record["branch_removed"]:
                    record["branch_removed"] = True
                    store.write(data)
            if workspace.is_symlink() or (workspace.exists() and not workspace.is_dir()):
                workspace.unlink()
                result["removed"].append({"workspace": str(workspace)})
            elif workspace.exists():
                shutil.rmtree(workspace)
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
    from .version import PROGRAM_VERSION
    cli.add_argument("--version", action="version", version=PROGRAM_VERSION)
    commands = cli.add_subparsers(required=True)
    task = command(commands, "task", "manage tasks and publications")
    sub = task.add_subparsers(dest="command", required=True)
    p = command(sub, "create", "register a TASK-ID, drafts and empty workspace")
    p.add_argument("--title", required=True, metavar="TITLE", help="short task title")
    p.add_argument("--review", metavar="TASK-ID|AGENT-PATH", help="source task; read its latest published task/report and delivery commits")
    p.set_defaults(func=create)
    p = command(sub, "bind", "bind one execution agent")
    p.add_argument("task", metavar="TASK-ID|AGENT-PATH", help="registered TASK-ID or native collaboration path")
    p.add_argument("--agent", required=True, metavar="AGENT-ID", help="execution AGENT-ID; one active task per agent")
    p.set_defaults(func=bind)
    p = command(sub, "start", "register or resume the calling executor")
    p.add_argument("task", nargs="?", metavar="TASK-ID", help="required for first registration or handoff")
    p.set_defaults(func=start)
    p = command(sub, "rebind", "hand an existing task to a dormant replacement agent")
    p.add_argument("task", metavar="TASK-ID", help="registered task with a current executor")
    p.add_argument("--agent", required=True, metavar="AGENT-ID", help="dormant replacement AGENT-ID")
    p.add_argument("--note", required=True, metavar="NOTE", help="short Manager handoff reason")
    p.set_defaults(func=rebind)
    p = command(sub, "show", "read a published document")
    p.add_argument("task", nargs="?", metavar="TASK-ID|AGENT-PATH", help="TASK-ID or native collaboration path; defaults to caller task")
    p.add_argument("--file", choices=("task", "report"), default="task", metavar="FILE", help="published document: task or report (default: task)")
    p.add_argument("--json", action="store_true", help="emit the published document as JSON")
    p.set_defaults(func=show, renderer="published")
    p = command(sub, "publish", "publish task requirements")
    p.add_argument("task", metavar="TASK-ID|AGENT-PATH", help="task whose requirements to publish")
    p.set_defaults(func=publish)
    p = command(sub, "report", "publish report and attachments; collect available worktree commits")
    p.add_argument("task", nargs="?", metavar="TASK-ID|AGENT-PATH", help="defaults to the calling executor's task")
    p.set_defaults(func=report)
    p = command(sub, "list", "list registered task records")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--archived", action="store_true", help="show only archived tasks")
    group.add_argument("--all", action="store_true", help="include archived tasks")
    p.set_defaults(func=task_list, renderer="task_list")
    p = command(sub, "status", "show concise task, repo and cached job status")
    p.add_argument("task", nargs="?", metavar="TASK-ID|AGENT-PATH", help="TASK-ID or native collaboration path; defaults to caller task")
    p.set_defaults(func=status)
    p = command(sub, "block", "mark a pending task blocked as the recorded Manager")
    p.add_argument("task", metavar="TASK-ID|AGENT-PATH", help="registered TASK-ID or native collaboration path")
    p.add_argument("--note", required=True, metavar="NOTE", help="why the task is blocked")
    p.set_defaults(func=task_block)
    p = command(sub, "archive", "delete the entire task workspace, registered worktrees and task branches; Manager owns deliverables and branch policy")
    p.add_argument("task", metavar="TASK-ID|AGENT-PATH", help="registered TASK-ID or native collaboration path")
    p.add_argument("--note", required=True, metavar="NOTE", help="purpose, result or reason for this operation")
    p.add_argument("--force", action="store_true", help="use git worktree remove --force and git branch -D; does not bypass archive checks")
    p.set_defaults(func=archive)
    jobs = command(commands, "job", "register, query and archive process records").add_subparsers(required=True)
    p = command(jobs, "add", "register a running process with its startup identity")
    p.add_argument("task", nargs="?", metavar="TASK-ID|AGENT-PATH", help="TASK-ID or native collaboration path; defaults to caller task")
    p.add_argument("--note", required=True, metavar="NOTE", help="purpose, result or reason for this operation")
    p.add_argument("--host", required=True, metavar="HOST", help="host running the process")
    p.add_argument("--pid", type=int, required=True, metavar="PID", help="running process ID")
    p.set_defaults(func=job_add)
    p = command(jobs, "list", "query process and agent states; never wake agents")
    p.add_argument("--task", metavar="TASK-ID|AGENT-PATH", help="filter jobs by TASK-ID or native collaboration path")
    p.add_argument("--status", choices=("running", "exited", "stopped", "archived", "all"), metavar="STATUS", help="filter jobs by running, exited, archived or all; default excludes archived records")
    p.add_argument("--attention", action="store_true", help="show exited jobs with inactive agents; list unknowns separately")
    p.set_defaults(func=job_list, renderer="job_list")
    p = command(jobs, "status", "refresh and show one registered process summary as JSON")
    p.add_argument("job", metavar="JOB-ID", help="registered job")
    p.set_defaults(func=job_status)
    p = command(jobs, "archive", "archive one registered job; retain history without probing or stopping its process")
    p.add_argument("job", metavar="JOB-ID", help="registered job")
    p.add_argument("--note", required=True, metavar="NOTE", help="purpose, result or reason for this operation")
    p.set_defaults(func=job_archive)
    service = command(commands, "service", "manage the project-local proactive wakeup scheduler").add_subparsers(required=True)
    p = command(service, "start", "start the detached project-local scheduler")
    p.add_argument("--manager", metavar="AGENT-ID", help="explicit Manager identity for an existing project")
    p.set_defaults(func=service_start)
    p = command(service, "stop", "gracefully stop this project's scheduler")
    p.set_defaults(func=service_stop)
    p = command(service, "status", "show scheduler health, pending items and diagnostics")
    p.set_defaults(func=service_status)
    p = command(service, "set", "set an instance service option")
    p.add_argument("setting", choices=("message-channel",))
    p.add_argument("value", choices=("tool", "user"))
    p.set_defaults(func=service_set)
    p = command(service, "rebind-manager", "transfer this instance to the calling native Manager")
    p.add_argument("--note", required=True, metavar="NOTE", help="reason for Manager handoff")
    p.set_defaults(func=service_rebind_manager)
    p = command(service, "upgrade", "upgrade this stopped instance and migrate its local data")
    p.set_defaults(func=service_upgrade)
    messages = command(commands, "message", "send a message to this project's Manager").add_subparsers(required=True)
    p = command(messages, "send", "queue a message for the Manager")
    p.add_argument("--message", required=True, metavar="TEXT", help="message text")
    p.add_argument("--immediate", action="store_true", help="deliver in the Manager's current turn or wake when idle")
    p.add_argument("--task", metavar="TASK-ID|AGENT-PATH", help="related task, if any")
    p.set_defaults(func=message_send)
    w = command(commands, "workspace", "manage repository worktrees and their environments").add_subparsers(required=True)
    p = command(w, "add", "create a repository worktree using the project workspace_add hook")
    p.add_argument("task", nargs="?", metavar="TASK-ID|AGENT-PATH", help="TASK-ID or native collaboration path; defaults to caller task")
    p.add_argument("--repo", required=True, metavar="REPO", help="single source repository directory below PROJECT_ROOT")
    p.add_argument("--base", required=True, metavar="COMMIT", help="base commit for the task branch")
    p.set_defaults(func=workspace_add)
    return cli


def main(argv=None, *, cwd=None):
    args = parser().parse_args(argv)
    try:
        if os.environ.get("MAM_HOOK_ACTIVE") and args.func not in {show, status, task_list, service_status}:
            raise Error("MAM hook cannot invoke a command that may modify task state")
        store = Store(project_config(cwd))
        if args.func in {show, publish, report, status, task_block, workspace_add, job_add, archive}:
            args.task = task_target(store, args.task, include_archived=args.func == status)
        elif args.func == job_list and args.task:
            args.task = task_target(store, args.task)
        result = args.func(store, args)
        if getattr(args, "renderer", None) == "task_list":
            print_task_list(result)
        elif getattr(args, "renderer", None) == "job_list":
            print_job_list(result)
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
