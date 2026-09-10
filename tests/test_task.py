from __future__ import annotations

import io
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from multi_agent_manager import cli

ROOT = Path(__file__).resolve().parents[1]
MAM = Path(sys.executable).with_name("mam")


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="task tests with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.projects = Path(self.temp.name) / "Projects"
        self.root = self.source("multi-agent-manager")
        self.store = cli.Store(self.root)

    def git(self, repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE).decode().strip()

    def source(self, name):
        repo = self.projects / name
        repo.mkdir(parents=True)
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Task test")
        self.git(repo, "config", "user.email", "test@example.invalid")
        (repo / ".gitignore").write_text(".local\n.venv/\ndata\nassets\neval_result\ncheckpoint/\ntemp/\n")
        (repo / "code.py").write_text("original = True\n")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "base")
        (repo / ".local").mkdir()
        (repo / ".local/create_worktree.sh").write_text('''#!/bin/bash
set -eu
source_root=$(dirname "$(dirname "$0")")
name=$(basename "$source_root")
target="$3/$name"
if test -f "$source_root/.local/fail-before"; then exit 7; fi
if ! test -d "$target"; then git -C "$source_root" worktree add -b "$2" "$target" "$1"; fi
if test -f "$source_root/.local/fail-after"; then exit 8; fi
mkdir -p "$target/.venv"
printf env > "$target/.venv/marker"
''')
        return repo

    def call(self, *args, command="task", ok=True):
        result = subprocess.run([str(MAM), "--root", str(self.root), command, *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def task(self):
        return self.call("create", "--title", "test task")["id"]

    def add(self, task, repo="multi-agent-manager", ok=True):
        return self.call("add", task, "--repo", repo, "--base", self.git(self.projects / repo, "rev-parse", "main"), command="workspace", ok=ok)

    def publish(self, task, kind="task"):
        return self.call("publish", task, "--file", kind)["revision"]

    def report(self, task, revision):
        self.store.doc(task, "report").write_text(f"task_revision: {revision}\nCompleted the task; tests passed.\n")
        return self.publish(task, "report")

    def task_output(self, *args):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cli.main(["--root", str(self.root), "task", *args]), 0)
        return output.getvalue()

    def task_command_output(self, *args):
        result = subprocess.run([str(MAM), "--root", str(self.root), "task", *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_parallel_publications_preserve_drafts_and_index(self):
        first, second, draft = self.task(), self.task(), self.task()
        (self.root / "code.py").write_text("staged = True\n")
        self.git(self.root, "add", "code.py")
        (self.root / "code.py").write_text("unstaged = True\n")
        index = self.git(self.root, "ls-files", "--stage", "--", "code.py", ".gitignore")
        draft_bytes = self.store.doc(draft, "task").read_bytes()
        commands = [[str(MAM), "--root", str(self.root), "task", "publish", task, "--file", "task"] for task in (first, second)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for command in commands]
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, stderr)
        for task in (first, second):
            self.assertIn("test task", self.git(self.root, "show", f"main:.tasks/{task}/task.md"))
        self.assertEqual(self.git(self.root, "ls-files", "--stage", "--", "code.py", ".gitignore"), index)
        for task in (first, second):
            path = f".tasks/{task}/task.md"
            self.assertEqual(self.git(self.root, "show", f":{path}"), self.git(self.root, "show", f"main:{path}"))
            self.assertEqual(self.git(self.root, "status", "--porcelain", "--", path), "")
        self.assertEqual((self.root / "code.py").read_text(), "unstaged = True\n")
        self.assertEqual(self.store.doc(draft, "task").read_bytes(), draft_bytes)
        self.assertEqual(self.git(self.root, "show", "main:code.py"), "original = True")
        self.git(self.root, "commit", "-m", "ordinary code commit after publication")
        for task in (first, second):
            self.assertIn("test task", self.git(self.root, "show", f"main:.tasks/{task}/task.md"))
        self.assertEqual(self.git(self.root, "show", "main:code.py"), "staged = True")

    def test_publish_unchanged_repairs_only_its_index_entry(self):
        task, other = self.task(), self.task()
        task_revision = self.publish(task)
        report_revision = self.report(task, task_revision)
        self.git(self.root, "add", "code.py", str(self.store.doc(other, "task")))
        (self.root / "code.py").write_text("staged = True\n")
        self.git(self.root, "add", "code.py")
        (self.root / "code.py").write_text("unstaged = True\n")
        self.store.doc(other, "task").write_text("other task draft\n")
        other_index = self.git(self.root, "ls-files", "--stage", "--", "code.py", f".tasks/{other}/task.md")
        for kind, revision in (("task", task_revision), ("report", report_revision)):
            path = f".tasks/{task}/{kind}.md"
            published_bytes = self.store.doc(task, kind).read_bytes()
            for damage in ("deleted", "stale"):
                with self.subTest(kind=kind, damage=damage):
                    if damage == "deleted":
                        self.git(self.root, "update-index", "--force-remove", "--", path)
                    else:
                        blob = self.git(self.root, "rev-parse", "HEAD:code.py")
                        self.git(self.root, "update-index", "--add", "--cacheinfo", "100644", blob, path)
                    before = self.git(self.root, "rev-parse", "main")
                    result = self.call("publish", task, "--file", kind)
                    self.assertTrue(result["unchanged"])
                    self.assertEqual(result["revision"], revision)
                    self.assertEqual(self.git(self.root, "rev-parse", "main"), before)
                    self.assertEqual(self.git(self.root, "show", f":{path}"), published_bytes.decode().strip())
                    self.assertEqual(self.git(self.root, "status", "--porcelain", "--", path), "")
                    self.assertEqual(self.store.doc(task, kind).read_bytes(), published_bytes)
        self.assertEqual(self.git(self.root, "ls-files", "--stage", "--", "code.py", f".tasks/{other}/task.md"), other_index)
        self.assertEqual((self.root / "code.py").read_text(), "unstaged = True\n")
        self.assertEqual(self.store.doc(other, "task").read_text(), "other task draft\n")
        self.git(self.root, "commit", "-m", "ordinary commit after index repair")
        self.assertEqual(self.call("show", task, "--json")["revision"], task_revision)
        self.assertEqual(self.call("show", task, "--file", "report", "--json")["revision"], report_revision)

    def test_publish_keeps_concurrent_edit_as_unstaged_draft(self):
        task = self.task()
        revision = self.publish(task)
        self.report(task, revision)
        for kind in ("task", "report"):
            with self.subTest(kind=kind):
                path = self.store.doc(task, kind)
                content = path.read_text() + "Published update.\n"
                path.write_text(content)
                original_git = cli.git
                def edit_during_commit(repo, *args, **kwargs):
                    if args[0] == "commit-tree":
                        path.write_text(content + "Later draft.\n")
                    return original_git(repo, *args, **kwargs)
                with patch.object(cli, "git", side_effect=edit_during_commit):
                    cli.publish(self.store, types.SimpleNamespace(task=task, file=kind))
                relative = f".tasks/{task}/{kind}.md"
                self.assertEqual(self.git(self.root, "show", f":{relative}"), content.strip())
                self.assertEqual(self.git(self.root, "show", f"main:{relative}"), content.strip())
                self.assertEqual(path.read_text(), content + "Later draft.\n")
                self.assertEqual(self.git(self.root, "diff", "--cached", "--", relative), "")

    def test_task_list_text_is_one_line_per_task_and_json_keeps_records(self):
        self.assertEqual(self.task_command_output("list"), "")
        self.assertEqual(json.loads(self.task_command_output("list", "--json")), [])
        unbound = self.call("create", "--title", "中文\n标题\twith whitespace")["id"]
        self.assertEqual(self.task_command_output("list").splitlines()[0].split("\t"),
                         ["中文 标题 with whitespace", "working", unbound, "未绑定", "未绑定"])
        bound = self.task()
        self.call("bind", bound, "--agent", "bound-agent")
        calls = []
        fake = types.SimpleNamespace(probe_agents=lambda ids: calls.append(ids) or {})
        with patch.object(cli, "runtime", return_value=fake):
            lines = self.task_output("list").splitlines()
            rows = {fields[2]: fields for fields in (line.split("\t") for line in lines)}
            self.assertEqual(calls, [["bound-agent"]])
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[unbound], ["中文 标题 with whitespace", "working", unbound, "未绑定", "未绑定"])
            self.assertEqual(rows[bound][3:], ["bound-agent", "unknown"])
            calls.clear()
            structured = json.loads(self.task_output("list", "--json"))
        self.assertEqual(calls, [["bound-agent"]])
        structured_by_id = {row["id"]: row for row in structured}
        self.assertEqual(structured_by_id[unbound]["title"], "中文\n标题\twith whitespace")
        self.assertEqual(structured_by_id[unbound]["agent_state"]["status"], "unbound")
        self.assertEqual(structured_by_id[bound]["agent_state"]["status"], "unknown")
        self.assertIn("workspace", structured_by_id[bound])
        self.assertIn("jobs", structured_by_id[bound])

    def test_task_show_text_keeps_markdown_and_json_keeps_history(self):
        task = self.task()
        first = self.publish(task)
        first_document = json.loads(self.task_command_output("show", task, "--json"))
        self.assertEqual(self.task_command_output("show", task), f"revision: {first}\n\n{first_document['content']}")
        self.store.doc(task, "task").write_text("# 更新后的要求\n\n正文不应被 JSON 转义。\n")
        second = self.publish(task)
        self.assertNotEqual(first, second)
        historical = json.loads(self.task_command_output("show", task, "--revision", first, "--json"))
        self.assertEqual(historical, first_document)
        self.assertEqual(self.task_command_output("show", task),
                         "revision: " + second + "\n\n# 更新后的要求\n\n正文不应被 JSON 转义。\n")

    def test_status_preserves_saved_job_observation_without_probing(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [{"id": "saved-job", "note": "saved", "host": "local", "pid": 1,
                         "identity": {"boot_id": "boot", "start_ticks": 1}, "status": "running",
                         "checked_at": "saved-at", "probe": {"status": "unknown", "checked_at": "saved-at", "error": "offline"},
                         "archive": None}]
        self.store.write(data)
        record = self.store.state / f"{task}.json"
        before = record.read_bytes()
        with patch.object(cli, "runtime", side_effect=AssertionError("status must not probe jobs")):
            result = cli.status(self.store, types.SimpleNamespace(task=task))
        self.assertEqual(result["jobs"][0]["checked_at"], "saved-at")
        self.assertEqual(result["jobs"][0]["probe"]["status"], "unknown")
        self.assertEqual(record.read_bytes(), before)

    def test_job_list_filters_before_probes_and_keeps_realtime_status(self):
        def job(name, pid, status):
            return {"id": name, "note": name, "host": "local", "pid": pid,
                    "identity": {"boot_id": "boot", "start_ticks": pid}, "status": status,
                    "checked_at": "saved", "probe": {"status": status, "checked_at": "saved", "error": None}, "archive": None}

        active, archived = self.task(), self.task()
        self.call("bind", active, "--agent", "active-agent")
        self.call("bind", archived, "--agent", "archived-agent")
        active_data = self.store.read(active)
        active_data["jobs"] = [job("becomes-running", 10, "stopped"), job("becomes-stopped", 11, "running"),
                               job("already-archived", 12, "archived")]
        self.store.write(active_data)
        archived_data = self.store.read(archived)
        archived_data["status"] = "archived"
        archived_data["jobs"] = [job("historical", 13, "stopped")]
        self.store.write(archived_data)
        process_status = {10: "running", 11: "stopped"}
        process_calls, agent_calls = [], []

        def probe_process(host, pid, identity):
            self.assertNotIn(pid, (12, 13))
            process_calls.append(pid)
            status = process_status[pid]
            return {"status": status, "identity": identity, "checked_at": f"check-{pid}",
                    "error": "offline" if status == "unknown" else None}

        def probe_agents(ids):
            agent_calls.append(ids)
            self.assertNotIn("archived-agent", ids)
            return {agent: {"status": "idle", "checked_at": "agents", "error": None} for agent in ids}

        fake = types.SimpleNamespace(probe_process=probe_process, probe_agents=probe_agents)
        with patch.object(cli, "runtime", return_value=fake):
            running = cli.job_list(self.store, types.SimpleNamespace(task=None, status="running", attention=False))
            self.assertEqual([row["id"] for row in running["jobs"]], ["becomes-running"])
            self.assertEqual(process_calls, [10, 11])
            self.assertEqual(agent_calls, [["active-agent"]])
            process_calls.clear()
            agent_calls.clear()
            process_status[10] = "unknown"
            attention = cli.job_list(self.store, types.SimpleNamespace(task=None, status=None, attention=True))
        self.assertEqual([row["id"] for row in attention["jobs"]], ["becomes-stopped"])
        self.assertEqual([row["id"] for row in attention["needs_verification"]], ["becomes-running"])
        self.assertEqual(process_calls, [10, 11])
        self.assertEqual(agent_calls, [["active-agent"]])

    def test_versions_reports_and_review_do_not_drift(self):
        task = self.task()
        worktree = Path(self.add(task)["path"])
        revision = self.publish(task)
        self.call("publish", task, "--file", "report", ok=False)
        report = self.report(task, revision)
        self.assertEqual(self.publish(task, "report"), report)
        review = self.call("create", "--title", "review", "--review", task)
        fixed = self.store.doc(review["id"], "task").read_text()
        self.publish(self.task())
        self.assertFalse(self.call("status", task)["requirements_changed"])
        self.store.doc(task, "task").write_text("new requirements\n")
        self.assertTrue(self.call("status", task)["drafts"]["task"])
        self.publish(task)
        self.assertTrue(self.call("status", task)["requirements_changed"])
        self.assertEqual(self.store.doc(review["id"], "task").read_text(), fixed)
        self.assertEqual(review["review"]["report_revision"], report)
        self.assertEqual(review["review"]["commits"]["multi-agent-manager"], self.git(worktree, "rev-parse", "HEAD"))
        self.assertIn("test task", self.call("show", task, "--revision", revision, "--json")["content"])
        self.call("create", "--title", "bad review", "--review", self.task(), ok=False)

    def test_bind_and_empty_archive_have_no_accept_gate(self):
        first, second = self.task(), self.task()
        self.call("bind", first, "--agent", "agent-1")
        self.call("bind", second, "--agent", "agent-1", ok=False)
        self.call("archive", first, "--note", "cancelled before implementation")
        self.call("bind", second, "--agent", "agent-1")
        self.assertEqual(len(self.call("list", "--archived", "--json")), 1)
        self.assertTrue(self.store.doc(first, "task").exists())
        self.assertEqual(self.call("status", first)["status"], "archived")

    def test_partial_creation_retry_and_no_foreign_branch_adoption(self):
        source = self.source("robot-bridge")
        task = self.task()
        first = self.add(task)
        marker = source / ".local/fail-after"
        marker.touch()
        self.add(task, "robot-bridge", ok=False)
        self.assertEqual(self.call("status", task)["repos"]["robot-bridge"]["state"], "failed")
        marker.unlink()
        self.assertEqual(self.add(task, "robot-bridge")["state"], "ready")
        other = self.task()
        self.git(source, "branch", f"task/{other}")
        self.add(other, "robot-bridge", ok=False)
        self.assertFalse(self.call("status", other)["repos"])
        self.assertTrue(Path(first["path"]).is_dir())

    def test_archive_protects_code_and_shared_entities(self):
        self.source("robot-bridge")
        task = self.task()
        first, second = Path(self.add(task)["path"]), Path(self.add(task, "robot-bridge")["path"])
        shared = Path(self.temp.name) / "shared"
        shared.mkdir()
        (shared / "keep").write_text("shared data")
        for name in ("data", "assets", "eval_result", ".local"):
            (first / name).symlink_to(shared, target_is_directory=True)
        (first / ".venv/link").symlink_to(shared, target_is_directory=True)
        (first / "code.py").write_text("exclusive_commit = True\n")
        self.git(first, "commit", "-am", "unmerged task code without report")
        self.assertNotEqual(self.git(first, "rev-parse", "HEAD"), self.git(self.root, "rev-parse", "main"))
        (second / "code.py").write_text("keep modifications\n")
        (second / "useful.py").write_text("keep untracked\n")
        self.call("archive", task, "--note", "done", ok=False)
        self.assertTrue(first.exists(), "preflight must protect the earlier clean repository")
        self.git(second, "restore", "code.py")
        (second / "useful.py").unlink()
        for path in (first / "checkpoint", first / "temp", first.parent / "temp"):
            path.mkdir()
            (path / "keep").write_text("keep")
            self.call("archive", task, "--note", "done", ok=False)
            self.assertTrue((path / "keep").exists())
            (path / "keep").unlink()
            path.rmdir()
        self.call("archive", task, "--note", "done")
        self.assertFalse(first.parent.exists())
        self.assertTrue((shared / "keep").exists())
        self.assertFalse(cli.branch_exists(self.root, f"task/{task}"))
        self.assertFalse(cli.branch_exists(self.projects / "robot-bridge", f"task/{task}"))
        self.assertEqual(self.call("status", task)["status"], "archived")

    def test_git_removal_failure_is_retryable(self):
        self.source("robot-bridge")
        task = self.task()
        first, second = Path(self.add(task)["path"]), Path(self.add(task, "robot-bridge")["path"])
        self.git(self.projects / "robot-bridge", "worktree", "lock", str(second))
        self.call("archive", task, "--note", "done", ok=False)
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())
        self.assertTrue(self.call("status", task)["repos"]["multi-agent-manager"]["removed"])
        self.git(self.projects / "robot-bridge", "worktree", "unlock", str(second))
        self.call("archive", task, "--note", "retry")
        self.assertFalse(second.parent.exists())

    def test_real_stdlib_environment_entry_and_linked_defaults(self):
        scripts = self.root / "scripts"
        scripts.mkdir()
        implementation = ROOT / "scripts"
        for name in ("create_worktree.sh", "local_create_worktree.sh"):
            (scripts / name).write_bytes((implementation / name).read_bytes())
        shutil.copytree(ROOT / "multi_agent_manager", self.root / "multi_agent_manager", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "pyproject.toml", self.root / "pyproject.toml")
        self.git(self.root, "add", "scripts", "multi_agent_manager", "pyproject.toml")
        self.git(self.root, "commit", "-m", "environment entry")
        (self.root / ".local/create_worktree.sh").write_bytes((scripts / "local_create_worktree.sh").read_bytes())
        task = self.task()
        path = Path(self.add(task)["path"])
        command = [str(path / ".venv/bin/python"), "-B", str(path / ".venv/bin/mam"), "--root", str(self.root), "task", "status", task]
        self.assertEqual(json.loads(subprocess.check_output(command, cwd=self.temp.name))["id"], task)
        self.assertEqual(cli.Store(path).root, self.root)
        self.call("archive", task, "--note", "stdlib smoke finished")
        self.assertFalse(path.parent.exists())

    def test_regular_install_runs_without_source_or_git_cwd(self):
        source = Path(self.temp.name) / "package source"
        source.mkdir()
        shutil.copytree(ROOT / "multi_agent_manager", source / "multi_agent_manager", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "pyproject.toml", source / "pyproject.toml")
        environment = Path(self.temp.name) / "installed env"
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True, capture_output=True)
        python = environment / "bin/python"
        subprocess.run([str(python), "-m", "pip", "install", "--no-deps", str(source)], check=True, capture_output=True)
        shutil.rmtree(source)
        command = str(environment / "bin/mam")
        help_text = subprocess.check_output([command, "--help"], cwd="/tmp", text=True)
        self.assertIn(str(cli.DEFAULT_ROOT), help_text)
        archive_help = subprocess.check_output([command, "task", "archive", "--help"], cwd="/tmp", text=True)
        self.assertIn("remove owned worktrees and task branches", " ".join(archive_help.split()))
        self.assertEqual(cli.DEFAULT_ROOT, Path("/mnt/public/xcj/Projects/multi-agent-manager"))
        rows = subprocess.check_output([command, "--root", str(self.root), "task", "list", "--json"], cwd="/tmp")
        self.assertEqual(json.loads(rows), [])
        installed = subprocess.check_output([str(python), "-I", "-c",
            "import multi_agent_manager; print(multi_agent_manager.__file__)"], cwd="/tmp", text=True)
        self.assertTrue(Path(installed.strip()).is_relative_to(environment))
        old = subprocess.run([command, "list"], cwd="/tmp", capture_output=True)
        self.assertEqual(old.returncode, 2)

    def test_archived_records_keep_historical_paths(self):
        task = self.task()
        self.call("archive", task, "--note", "historical task")
        data = self.store.read(task)
        data["repos"]["agent-workflow"] = {"source": str(self.projects / "agent-workflow"),
            "path": str(Path(data["workspace"]) / "agent-workflow"), "removed": True}
        self.store.write(data)
        record = self.store.state / f"{task}.json"
        before = (record.read_bytes(), record.stat().st_mtime_ns)
        self.assertEqual(self.call("status", task)["repos"], data["repos"])
        self.assertEqual(self.call("list", "--archived", "--json")[0]["repos"], data["repos"])
        self.call("list", "--task", task, command="job")
        self.assertEqual((record.read_bytes(), record.stat().st_mtime_ns), before)

    def test_job_and_workspace_are_top_level_only(self):
        for command, description in (("job", "register, query and archive process records"),
                                     ("workspace", "manage repository worktrees and their environments")):
            help_result = subprocess.run([str(MAM), "--root", str(self.root), command, "--help"], capture_output=True, text=True)
            self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)
            self.assertIn(description, help_result.stdout)
            old = subprocess.run([str(MAM), "--root", str(self.root), "task", command, "--help"], capture_output=True, text=True)
            self.assertEqual(old.returncode, 2, old.stdout + old.stderr)
        self.assertEqual(self.call("list", command="job"), {"jobs": [], "needs_verification": []})

    def test_tampered_paths_and_symlink_workspace_rejected(self):
        task = self.task()
        data = self.store.read(task)
        workspace = Path(data["workspace"])
        workspace.rmdir()
        workspace.symlink_to(self.root, target_is_directory=True)
        self.call("archive", task, "--note", "unsafe", ok=False)
        workspace.unlink()
        workspace.mkdir()
        data["workspace"] = str(self.root)
        self.store.write(data)
        self.call("archive", task, "--note", "unsafe", ok=False)
        self.assertTrue((self.root / "code.py").exists())

    def test_real_process_runtime_contract(self):
        try:
            process_runtime = cli.runtime()
        except cli.Error:
            self.skipTest("parallel job_runtime module has not been integrated")
        task = self.task()
        child = subprocess.Popen([sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE)
        try:
            args = types.SimpleNamespace(task=task, note="owned smoke", host="localhost", pid=child.pid)
            job = cli.job_add(self.store, args)
            self.assertEqual(job["status"], "running")
            child.stdin.close()
            child.wait(timeout=10)
            self.assertEqual(process_runtime.probe_process("localhost", child.pid, job["identity"])["status"], "stopped")
            saved = cli.job_archive(self.store, types.SimpleNamespace(job=job["id"], note="test exited"))
            self.assertEqual(saved["status"], "archived")
            cli.archive(self.store, types.SimpleNamespace(task=task, note="smoke complete"))
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)

    def test_job_identity_attention_and_history(self):
        task = self.task()
        self.call("bind", task, "--agent", "agent-1")
        process = {"status": "running", "identity": {"boot_id": "boot", "start_ticks": 10}, "checked_at": "first", "error": None}
        agent = {"status": "idle", "checked_at": "first", "error": None}
        fake = types.SimpleNamespace(probe_process=lambda *a: dict(process), probe_agents=lambda ids: {key: dict(agent) for key in ids})
        with patch.object(cli, "runtime", return_value=fake):
            args = types.SimpleNamespace(task=task, note="test", host="local", pid=42)
            one, two = cli.job_add(self.store, args), cli.job_add(self.store, args)
            self.assertNotEqual(one["id"], two["id"])
            with self.assertRaises(cli.Error):
                cli.archive(self.store, types.SimpleNamespace(task=task, note="done"))
            process.update(status="unknown", error="offline", checked_at="second")
            query = types.SimpleNamespace(task=task, status=None, attention=True)
            result = cli.job_list(self.store, query)
            self.assertEqual(len(result["needs_verification"]), 2)
            self.assertEqual(result["needs_verification"][0]["checked_at"], "first")
            process.update(status="stopped", error="process identity changed")
            self.assertEqual(len(cli.job_list(self.store, query)["jobs"]), 2)
            agent["status"] = "systemError"
            self.assertEqual(len(cli.job_list(self.store, query)["jobs"]), 2)
            agent["status"] = "unknown"
            self.assertEqual(len(cli.job_list(self.store, query)["needs_verification"]), 2)
            agent["status"] = "active"
            self.assertFalse(cli.job_list(self.store, query)["jobs"])
            cli.job_archive(self.store, types.SimpleNamespace(job=one["id"], note="results saved"))
            cli.archive(self.store, types.SimpleNamespace(task=task, note="done"))
            process["status"] = "running"
            saved = self.store.read(task)
            cli.refresh_jobs(saved)
            self.assertEqual(saved["jobs"][0]["status"], "archived")
            self.assertEqual(saved["jobs"][1]["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
