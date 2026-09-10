from __future__ import annotations

import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
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
        self.config = self.configure(self.projects, self.root)
        self.store = cli.Store(self.config)

    def git(self, repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE).decode().strip()

    def source(self, name, projects=None):
        repo = (projects or self.projects) / name
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

    def configure(self, project, mam_root, branch="main", location=None):
        location = location or project
        directory = location / ".mam"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "env.json").write_text(json.dumps({
            "MAM_ROOT": str(mam_root),
            "PROJECT_ROOT": str(project),
            "MAM_BRANCH": branch,
        }))
        return cli.project_config(location)

    def call(self, *args, command="task", ok=True):
        result = subprocess.run([str(MAM), command, *args], capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def task(self):
        return self.call("create", "--title", "test task")["id"]

    def add(self, task, repo="multi-agent-manager", ok=True):
        return self.call("add", task, "--repo", repo, "--base", self.git(self.projects / repo, "rev-parse", "main"), command="workspace", ok=ok)

    def publish(self, task, kind="task"):
        return self.call("publish", task, "--file", kind)["revision"]

    def report(self, task):
        self.store.doc(task, "report").write_text("Completed the task; tests passed.\n")
        return self.publish(task, "report")

    def task_output(self, *args):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cli.main(["task", *args], cwd=self.projects), 0)
        return output.getvalue()

    def task_command_output(self, *args):
        result = subprocess.run([str(MAM), "task", *args], capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def job_command_output(self, *args):
        result = subprocess.run([str(MAM), "job", *args], capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def wait_call(self, *args, env=None, ok=True):
        result = subprocess.run([str(MAM), "wait", *args], capture_output=True, text=True, env=env, cwd=self.projects)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def wait_list_lines(self):
        result = subprocess.run([str(MAM), "wait", "list"], capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.splitlines()

    def test_parallel_publications_preserve_drafts_and_index(self):
        first, second, draft = self.task(), self.task(), self.task()
        (self.root / "code.py").write_text("staged = True\n")
        self.git(self.root, "add", "code.py")
        (self.root / "code.py").write_text("unstaged = True\n")
        index = self.git(self.root, "ls-files", "--stage", "--", "code.py", ".gitignore")
        draft_bytes = self.store.doc(draft, "task").read_bytes()
        commands = [[str(MAM), "task", "publish", task, "--file", "task"] for task in (first, second)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.projects) for command in commands]
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
        task_publication = self.publish(task)
        report_publication = self.report(task)
        self.git(self.root, "add", "code.py", str(self.store.doc(other, "task")))
        (self.root / "code.py").write_text("staged = True\n")
        self.git(self.root, "add", "code.py")
        (self.root / "code.py").write_text("unstaged = True\n")
        self.store.doc(other, "task").write_text("other task draft\n")
        other_index = self.git(self.root, "ls-files", "--stage", "--", "code.py", f".tasks/{other}/task.md")
        for kind, publication in (("task", task_publication), ("report", report_publication)):
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
                    self.assertEqual(result["revision"], publication)
                    self.assertEqual(self.git(self.root, "rev-parse", "main"), before)
                    self.assertEqual(self.git(self.root, "show", f":{path}"), published_bytes.decode().strip())
                    self.assertEqual(self.git(self.root, "status", "--porcelain", "--", path), "")
                    self.assertEqual(self.store.doc(task, kind).read_bytes(), published_bytes)
        self.assertEqual(self.git(self.root, "ls-files", "--stage", "--", "code.py", f".tasks/{other}/task.md"), other_index)
        self.assertEqual((self.root / "code.py").read_text(), "unstaged = True\n")
        self.assertEqual(self.store.doc(other, "task").read_text(), "other task draft\n")
        self.git(self.root, "commit", "-m", "ordinary commit after index repair")
        self.assertEqual(self.call("show", task, "--json")["revision"], task_publication)
        self.assertEqual(self.call("show", task, "--file", "report", "--json")["revision"], report_publication)

    def test_publish_keeps_concurrent_edit_as_unstaged_draft(self):
        task = self.task()
        self.publish(task)
        self.report(task)
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

    def test_task_list_text_has_header_and_status_keeps_records(self):
        header = "标题\t任务状态\tTASK-ID\tAGENT-ID\tagent状态"
        self.assertEqual(self.task_command_output("list").splitlines(), [header])
        rejected = subprocess.run([str(MAM), "task", "list", "--json"], capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(rejected.returncode, 2)
        unbound = self.call("create", "--title", "中文\n标题\twith whitespace")["id"]
        self.assertEqual(self.task_command_output("list").splitlines()[1].split("\t"),
                         ["中文 标题 with whitespace", "working", unbound, "未绑定", "未绑定"])
        bound = self.task()
        self.call("bind", bound, "--agent", "bound-agent")
        calls = []
        fake = types.SimpleNamespace(probe_agents=lambda ids: calls.append(ids) or {})
        with patch.object(cli, "runtime", return_value=fake):
            lines = self.task_output("list").splitlines()
            rows = {fields[2]: fields for fields in (line.split("\t") for line in lines[1:])}
            self.assertEqual(calls, [["bound-agent"]])
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[unbound], ["中文 标题 with whitespace", "working", unbound, "未绑定", "未绑定"])
            self.assertEqual(rows[bound][3:], ["bound-agent", "unknown"])
        self.assertEqual(self.call("status", bound)["agent"], "bound-agent")

    def test_task_show_text_is_published_markdown(self):
        task = self.task()
        first = self.publish(task)
        first_document = json.loads(self.task_command_output("show", task, "--json"))
        self.assertEqual(self.task_command_output("show", task), first_document["content"])
        self.assertNotIn("--revision", self.task_command_output("show", "--help"))
        self.store.doc(task, "task").write_text("# 更新后的要求\n\n正文不应被 JSON 转义。\n")
        second = self.publish(task)
        self.assertNotEqual(first, second)
        self.assertEqual(json.loads(self.task_command_output("show", task, "--json"))["content"],
                         "# 更新后的要求\n\n正文不应被 JSON 转义。\n")
        self.assertEqual(self.task_command_output("show", task), "# 更新后的要求\n\n正文不应被 JSON 转义。\n")
        rejected = subprocess.run([str(MAM), "task", "show", task, "--revision", first],
                                  capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(rejected.returncode, 2)

    def test_status_preserves_saved_job_observation_without_probing(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [
            {"id": "saved-job", "note": "saved", "host": "local", "pid": 1,
             "identity": {"boot_id": "boot", "start_ticks": 1}, "status": "running",
             "checked_at": "saved-at", "probe": {"status": "unknown", "checked_at": "saved-at", "error": "offline"},
             "archive": None},
            {"id": "archived-job", "note": "old", "host": "local", "pid": 2,
             "identity": {"boot_id": "boot", "start_ticks": 2}, "status": "archived",
             "checked_at": "old-at", "probe": {"status": "stopped", "checked_at": "old-at", "error": None},
             "archive": {"note": "done", "at": "old-at"}},
        ]
        self.store.write(data)
        record = self.store.state / f"{task}.json"
        before = record.read_bytes()
        with patch.object(cli, "runtime", side_effect=AssertionError("status must not probe jobs")):
            result = cli.status(self.store, types.SimpleNamespace(task=task))
        self.assertEqual(result["jobs"], {"cached": True, "unarchived": [
            {"id": "saved-job", "note": "saved", "status": "unknown", "checked_at": "saved-at"}],
            "archived_count": 1})
        self.assertNotIn("identity", result["jobs"]["unarchived"][0])
        self.assertNotIn("probe", result["jobs"]["unarchived"][0])
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
        self.assertEqual(cli.displayed_job_status(attention["needs_verification"][0]), "unknown/待核实")
        self.assertEqual(process_calls, [10, 11])
        self.assertEqual(agent_calls, [["active-agent"]])

    def test_job_status_refreshes_only_the_requested_job(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [
            {"id": "first", "note": "first", "host": "local", "pid": 10,
             "identity": {"boot_id": "boot", "start_ticks": 10}, "status": "running", "checked_at": "saved",
             "started_at": "started-first", "probe": {"status": "running", "checked_at": "saved", "error": None}, "archive": None},
            {"id": "second", "note": "second", "host": "local", "pid": 11,
             "identity": {"boot_id": "boot", "start_ticks": 11}, "status": "running", "checked_at": "saved",
             "started_at": "started-second", "probe": {"status": "running", "checked_at": "saved", "error": None}, "archive": None},
        ]
        self.store.write(data)
        calls = []

        def probe(host, pid, identity):
            calls.append(pid)
            return {"status": "stopped", "identity": identity, "checked_at": "checked", "error": "process not found"}

        with patch.object(cli, "runtime", return_value=types.SimpleNamespace(probe_process=probe)):
            result = cli.job_status(self.store, types.SimpleNamespace(job="second"))
        self.assertEqual(calls, [11])
        self.assertEqual(result["task"], task)
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["checked_at"], "checked")
        self.assertEqual(result["started_at"], "started-second")
        self.assertNotIn("identity", result)
        self.assertNotIn("probe", result)
        self.assertEqual(self.store.read(task)["jobs"][0]["status"], "running")

        def unknown_probe(host, pid, identity):
            calls.append(pid)
            return {"status": "unknown", "identity": None, "checked_at": "unavailable", "error": "offline"}

        with patch.object(cli, "runtime", return_value=types.SimpleNamespace(probe_process=unknown_probe)):
            unknown = cli.job_status(self.store, types.SimpleNamespace(job="second"))
        self.assertEqual(calls, [11, 11])
        self.assertEqual(unknown["status"], "unknown")
        self.assertEqual(unknown["checked_at"], "unavailable")
        self.assertEqual(unknown["last_known_status"], "stopped")
        self.assertEqual(unknown["last_known_checked_at"], "checked")
        self.assertEqual(unknown["error"], "offline")

    def test_reports_track_delivery_and_review_reads_latest_publications(self):
        task = self.task()
        worktree = Path(self.add(task)["path"])
        self.publish(task)
        self.store.doc(task, "report").write_text("Completed initial requirements.\n")
        report_publication = self.publish(task, "report")
        first_delivery = self.git(worktree, "rev-parse", "HEAD")
        self.store.doc(task, "task").write_text("latest requirements\n")
        task_publication = self.publish(task)
        initial_status = self.call("status", task)
        self.assertEqual(initial_status["publications"], {"task": task_publication, "report": report_publication})
        self.assertEqual(initial_status["repos"]["multi-agent-manager"]["commit"], first_delivery)
        self.assertNotIn("report", initial_status)
        self.assertNotIn("requirements_changed", initial_status)

        (worktree / "code.py").write_text("delivered = True\n")
        self.git(worktree, "add", "code.py")
        self.git(worktree, "commit", "-m", "record delivery")
        delivery = self.git(worktree, "rev-parse", "HEAD")
        self.call("publish", task, "--file", "report", ok=False)
        self.store.doc(task, "report").write_text("Completed latest requirements and recorded delivery.\n")
        report_publication = self.publish(task, "report")
        final_status = self.call("status", task)
        self.assertEqual(final_status["publications"], {"task": task_publication, "report": report_publication})
        self.assertEqual(final_status["repos"]["multi-agent-manager"]["commit"], delivery)

        review = self.call("create", "--title", "review", "--review", task)
        review_task = self.store.doc(review["id"], "task").read_text()
        self.assertIn("latest requirements", review_task)
        self.assertIn("Completed latest requirements and recorded delivery.", review_task)
        self.assertIn(delivery, review_task)
        self.assertEqual(review["review"], {"task": task, "commits": {"multi-agent-manager": delivery}})
        self.assertEqual(self.call("status", review["id"])["review"], {
            "source_task": task, "commits": {"multi-agent-manager": delivery}})
        self.call("create", "--title", "bad review", "--review", self.task(), ok=False)

    def test_legacy_revision_metadata_is_ignored_when_querying_records(self):
        task = self.task()
        task_publication = self.publish(task)
        report_publication = self.report(task)
        legacy_commits = {"multi-agent-manager": "legacy-delivery"}
        data = self.store.read(task)
        data["report"] = {"task_revision": task_publication, "commits": legacy_commits,
                          "revision": report_publication}
        data["review"] = {"task": task, "task_revision": task_publication,
                          "report_revision": report_publication, "commits": legacy_commits}
        self.store.write(data)
        status = self.call("status", task)
        self.assertEqual(self.task_command_output("show", task), self.store.doc(task, "task").read_text())
        self.assertEqual(self.task_command_output("show", task, "--file", "report"), self.store.doc(task, "report").read_text())
        self.assertEqual(status["review"], {"source_task": task, "commits": legacy_commits})
        self.assertNotIn("report", status)
        self.assertNotIn("requirements_changed", status)

    def test_bind_and_empty_archive_have_no_accept_gate(self):
        first, second = self.task(), self.task()
        self.call("bind", first, "--agent", "agent-1")
        self.call("bind", second, "--agent", "agent-1", ok=False)
        self.call("archive", first, "--note", "cancelled before implementation")
        self.call("bind", second, "--agent", "agent-1")
        self.assertEqual(len(self.task_command_output("list", "--archived").splitlines()), 2)
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

    def test_workspace_add_accepts_project_repo_names_and_rejects_path_inputs(self):
        name = "project-specific-repository"
        source = self.source(name)
        task = self.task()
        record = self.add(task, name)
        self.assertEqual(record["source"], str(source))
        self.assertEqual(record["path"], str(self.projects / "workspace" / task / name))
        self.assertEqual(self.call("status", task)["repos"][name]["state"], "ready")

        state = self.store.state / f"{task}.json"
        before = state.read_bytes()
        base = self.git(source, "rev-parse", "main")
        for invalid in ("", ".", "..", "../outside", "/tmp/outside", "nested/repository", "nested\\repository"):
            with self.subTest(invalid=invalid):
                rejected = self.call("add", task, "--repo", invalid, "--base", base, command="workspace", ok=False)
                self.assertIn("repository name must be a non-empty single directory name", rejected["error"])
                self.assertEqual(state.read_bytes(), before)

        help_result = subprocess.run([str(MAM), "workspace", "add", "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)
        self.assertIn("below PROJECT_ROOT", help_result.stdout)
        self.assertNotIn("robot-bridge", help_result.stdout)

        missing = self.source("no-entry-repository")
        (missing / ".local" / "create_worktree.sh").unlink()
        missing_task = self.task()
        missing_result = self.add(missing_task, "no-entry-repository", ok=False)
        self.assertIn("has no .local/create_worktree.sh", missing_result["error"])
        self.assertFalse(self.store.read(missing_task)["repos"])

        linked_entry = self.source("linked-entry-repository")
        entry = linked_entry / ".local" / "create_worktree.sh"
        entry.unlink()
        entry.symlink_to(linked_entry / "code.py")
        linked_task = self.task()
        linked_result = self.add(linked_task, "linked-entry-repository", ok=False)
        self.assertIn("symlinked path is not allowed", linked_result["error"])
        self.assertFalse(self.store.read(linked_task)["repos"])

        self.call("archive", task, "--note", "custom repository cleanup")
        self.assertFalse(Path(record["path"]).exists())
        self.assertFalse(cli.branch_exists(source, f"task/{task}"))

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
        linked = self.projects / "production state"
        self.git(self.root, "worktree", "add", "-b", "project/state-vla", str(linked), "main")
        self.configure(self.projects, linked, "project/state-vla")
        task = self.task()
        path = Path(self.add(task)["path"])
        command = [str(path / ".venv/bin/python"), "-B", str(path / ".venv/bin/mam"), "task", "status", task]
        self.assertEqual(json.loads(subprocess.check_output(command, cwd=path))["id"], task)
        self.assertEqual(cli.Store(cli.project_config(path)).root, linked)
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
        self.assertNotIn("--root", help_text)
        archive_help = subprocess.check_output([command, "task", "archive", "--help"], cwd="/tmp", text=True)
        self.assertIn("remove owned worktrees and task branches", " ".join(archive_help.split()))
        rows = subprocess.check_output([command, "task", "list"], cwd=self.projects, text=True)
        self.assertEqual(rows.splitlines(), ["标题\t任务状态\tTASK-ID\tAGENT-ID\tagent状态"])
        installed = subprocess.check_output([str(python), "-I", "-c",
            "import multi_agent_manager; print(multi_agent_manager.__file__)"], cwd="/tmp", text=True)
        self.assertTrue(Path(installed.strip()).is_relative_to(environment))
        old = subprocess.run([command, "task", "list"], cwd="/tmp", capture_output=True)
        self.assertEqual(old.returncode, 2)

    def test_project_configuration_discovers_subdirectories_uses_nearest_and_isolates_projects(self):
        nested = self.projects / "nested" / "deeper"
        nested.mkdir(parents=True)
        self.assertEqual(cli.project_config(nested), self.config)

        other_projects = Path(self.temp.name) / "Other Projects"
        other_root = self.source("multi-agent-manager", other_projects)
        other_config = self.configure(other_projects, other_root)

        def create(project, title):
            result = subprocess.run([str(MAM), "task", "create", "--title", title], cwd=project,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)["id"]

        first, second = create(self.projects, "first project"), create(other_projects, "second project")
        self.assertTrue((self.root / ".local" / "tasks" / f"{first}.json").is_file())
        self.assertFalse((self.root / ".local" / "tasks" / f"{second}.json").exists())
        self.assertTrue((other_root / ".local" / "tasks" / f"{second}.json").is_file())
        self.assertEqual(cli.Store(self.config).read(first)["workspace"], str(self.projects / "workspace" / first))
        self.assertEqual(cli.Store(other_config).read(second)["workspace"], str(other_projects / "workspace" / second))

        self.configure(other_projects, other_root, location=nested.parent)
        self.assertEqual(cli.project_config(nested), other_config)
        nearest = create(nested, "nearest configuration")
        self.assertTrue((other_root / ".local" / "tasks" / f"{nearest}.json").is_file())
        self.assertFalse((self.root / ".local" / "tasks" / f"{nearest}.json").exists())

    def test_missing_or_invalid_nearest_configuration_does_not_fall_back_or_change_records(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [{"id": "existing-job", "note": "preserve", "host": "local", "pid": 1,
                         "identity": {"host": "local", "boot_id": "boot", "start_ticks": 1}, "status": "running",
                         "checked_at": "saved", "probe": {"status": "unknown", "checked_at": "saved", "error": "offline"},
                         "archive": None}]
        self.store.write(data)
        record = self.store.state / f"{task}.json"
        before = record.read_bytes()

        nested = self.projects / "invalid" / "child"
        nested.mkdir(parents=True)
        invalid = nested.parent / ".mam"
        invalid.mkdir()
        (invalid / "env.json").write_text(json.dumps({"MAM_ROOT": str(self.root)}))
        with self.assertRaisesRegex(cli.Error, "missing required keys"):
            cli.project_config(nested)
        rejected = subprocess.run([str(MAM), "task", "list"], cwd=nested, capture_output=True, text=True)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("invalid project configuration", rejected.stderr)
        (invalid / "env.json").write_text("{")
        with self.assertRaisesRegex(cli.Error, "invalid project configuration"):
            cli.project_config(nested)
        (invalid / "env.json").write_text(json.dumps({
            "MAM_ROOT": str(self.root), "PROJECT_ROOT": "relative", "MAM_BRANCH": "main"}))
        with self.assertRaisesRegex(cli.Error, "PROJECT_ROOT must be an absolute path"):
            cli.project_config(nested)
        (invalid / "env.json").write_text(json.dumps({
            "MAM_ROOT": str(self.root), "PROJECT_ROOT": str(self.projects), "MAM_BRANCH": "missing-branch"}))
        with self.assertRaisesRegex(cli.Error, "not an existing local branch"):
            cli.project_config(nested)
        self.assertEqual(record.read_bytes(), before)

        outside = Path(self.temp.name) / "without configuration"
        outside.mkdir()
        missing = subprocess.run([str(MAM), "task", "list"], cwd=outside, capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("no .mam/env.json found", missing.stderr)
        help_result = subprocess.run([str(MAM), "--help"], cwd=outside, capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)

    def test_configuration_resolves_path_aliases_and_keeps_linked_mam_root_distinct(self):
        alias = self.projects / "path alias"
        alias.mkdir()
        (self.projects / ".mam" / "env.json").write_text(json.dumps({
            "MAM_ROOT": str(alias / ".." / "multi-agent-manager"),
            "PROJECT_ROOT": str(alias / ".."),
            "MAM_BRANCH": "main",
        }))
        aliases = cli.project_config(self.projects)
        self.assertEqual((aliases.mam_root, aliases.project_root), (self.root, self.projects))

        linked = self.projects / "project state"
        self.git(self.root, "worktree", "add", "-b", "project/state-vla", str(linked), "main")
        config = self.configure(self.projects, linked, "project/state-vla")
        store = cli.Store(config)
        self.assertEqual(store.root, linked)
        self.assertEqual(cli.primary(linked), self.root)
        self.assertEqual(store.workspaces, self.projects / "workspace")

        created = subprocess.run([str(MAM), "task", "create", "--title", "linked MAM root"], cwd=self.projects,
                                 capture_output=True, text=True)
        self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
        task = json.loads(created.stdout)["id"]
        self.assertTrue((linked / ".local" / "tasks" / f"{task}.json").is_file())
        self.assertFalse((self.root / ".local" / "tasks" / f"{task}.json").exists())
        main_before = self.git(self.root, "rev-parse", "main")
        state_before = self.git(self.root, "rev-parse", "project/state-vla")
        published = subprocess.run([str(MAM), "task", "publish", task, "--file", "task"], cwd=self.projects,
                                   capture_output=True, text=True)
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
        self.assertEqual(self.git(self.root, "rev-parse", "main"), main_before)
        self.assertNotEqual(self.git(self.root, "rev-parse", "project/state-vla"), state_before)
        self.assertIn("linked MAM root", self.git(linked, "show", f"project/state-vla:.tasks/{task}/task.md"))

    def test_publish_rejects_wrong_configured_branch_without_changing_existing_job(self):
        self.git(self.root, "branch", "project/state-vla")
        config = self.configure(self.projects, self.root, "project/state-vla")
        store = cli.Store(config)
        created = subprocess.run([str(MAM), "task", "create", "--title", "wrong publication branch"], cwd=self.projects,
                                 capture_output=True, text=True)
        self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
        task = json.loads(created.stdout)["id"]
        data = store.read(task)
        data["jobs"] = [{"id": "existing-job", "note": "preserve", "host": "local", "pid": 1,
                         "identity": {"host": "local", "boot_id": "boot", "start_ticks": 1}, "status": "running",
                         "checked_at": "saved", "probe": {"status": "unknown", "checked_at": "saved", "error": "offline"},
                         "archive": None}]
        store.write(data)
        record = store.state / f"{task}.json"
        before = record.read_bytes()
        main_before = self.git(self.root, "rev-parse", "main")
        branch_before = self.git(self.root, "rev-parse", "project/state-vla")

        rejected = subprocess.run([str(MAM), "task", "publish", task, "--file", "task"], cwd=self.projects,
                                  capture_output=True, text=True)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("must be checked out on MAM_BRANCH", rejected.stderr)
        self.assertEqual(record.read_bytes(), before)
        self.assertEqual(self.git(self.root, "rev-parse", "main"), main_before)
        self.assertEqual(self.git(self.root, "rev-parse", "project/state-vla"), branch_before)

    def test_archived_records_keep_historical_paths(self):
        task = self.task()
        self.call("archive", task, "--note", "historical task")
        data = self.store.read(task)
        data["repos"]["agent-workflow"] = {"source": str(self.projects / "agent-workflow"),
            "path": str(Path(data["workspace"]) / "agent-workflow"), "removed": True}
        self.store.write(data)
        record = self.store.state / f"{task}.json"
        before = (record.read_bytes(), record.stat().st_mtime_ns)
        archived_status = self.call("status", task)
        self.assertEqual(archived_status["repos"], {
            "agent-workflow": {"path": str(Path(data["workspace"]) / "agent-workflow"), "removed": True}})
        self.assertEqual(archived_status["archive"]["note"], "historical task")
        self.assertEqual(self.task_command_output("list", "--archived").splitlines()[1].split("\t")[2], task)
        self.job_command_output("list", "--task", task)
        self.assertEqual((record.read_bytes(), record.stat().st_mtime_ns), before)

    def test_job_and_workspace_are_top_level_only(self):
        for command, description in (("job", "register, query and archive process records"),
                                     ("workspace", "manage repository worktrees and their environments")):
            help_result = subprocess.run([str(MAM), command, "--help"], capture_output=True, text=True)
            self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)
            self.assertIn(description, help_result.stdout)
            old = subprocess.run([str(MAM), "task", command, "--help"], capture_output=True, text=True)
            self.assertEqual(old.returncode, 2, old.stdout + old.stderr)
        self.assertEqual(self.job_command_output("list").splitlines(), ["描述\tjob状态\t开始时间\tJOB-ID\t任务描述\tTASK-ID"])

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
            detail = self.call("status", job["id"], command="job")
            self.assertEqual(detail["task"], task)
            self.assertEqual(detail["agent"], None)
            self.assertEqual(detail["status"], "running")
            self.assertNotIn("probe", detail)
            self.assertTrue(detail["started_at"].endswith("Z"))
            rows = self.job_command_output("list", "--task", task, "--status", "running").splitlines()
            self.assertEqual(rows[0], "描述\tjob状态\t开始时间\tJOB-ID\t任务描述\tTASK-ID")
            self.assertEqual(rows[1].split("\t"), ["owned smoke", "running", detail["started_at"], job["id"], "test task", task])
            child.stdin.close()
            child.wait(timeout=10)
            self.assertEqual(process_runtime.probe_process("localhost", child.pid, job["identity"])["status"], "stopped")
            saved = cli.job_archive(self.store, types.SimpleNamespace(job=job["id"], note="test exited"))
            self.assertEqual(saved["status"], "archived")
            archived = self.call("status", job["id"], command="job")
            self.assertEqual(archived["status"], "archived")
            self.assertEqual(archived["archive"]["note"], "test exited")
            cli.archive(self.store, types.SimpleNamespace(task=task, note="smoke complete"))
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)

    def test_wait_stop_keeps_process_and_uses_waiter_binding(self):
        monitored = self.call("create", "--title", "monitored task")["id"]
        waiter_task = self.call("create", "--title", "waiter binding")["id"]
        self.call("bind", monitored, "--agent", "job-owner")
        self.call("bind", waiter_task, "--agent", "waiter-one")
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
        waiter = None
        try:
            self.call("add", monitored, "--note", "wait smoke", "--host", "localhost", "--pid", str(child.pid), command="job")
            environment = {**os.environ, "CODEX_THREAD_ID": "waiter-one"}
            waiter = subprocess.Popen([str(MAM), "wait", "jobs", "--task", monitored,
                                       "--timeout", "10"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                       env=environment, cwd=self.projects)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                rows = self.wait_list_lines()
                if len(rows) == 2:
                    break
                time.sleep(0.05)
            else:
                self.fail("waiter was not registered")
            self.assertEqual(rows[0], "AGENT-ID\t绑定任务标题\tTASK-ID\t等待内容\t等待开始时间")
            self.assertEqual(rows[1].split("\t")[:4], ["waiter-one", "waiter binding", waiter_task, f"jobs TASK-ID={monitored}"])
            duplicate = self.wait_call("jobs", "--task", monitored, "--agent", "waiter-one", "--timeout", "1", ok=False)
            self.assertIn("already waiting", duplicate["error"])
            self.assertEqual(self.wait_call("stop", "--agent", "waiter-one")["status"], "cancelled")
            stdout, stderr = waiter.communicate(timeout=3)
            self.assertEqual(waiter.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["status"], "cancelled")
            self.assertIsNone(child.poll(), "wait stop must not signal the monitored process")
            self.assertEqual(self.wait_list_lines(), ["AGENT-ID\t绑定任务标题\tTASK-ID\t等待内容\t等待开始时间"])
            self.assertEqual(self.wait_call("stop", "--agent", "waiter-one")["status"], "not_waiting")
        finally:
            if waiter and waiter.poll() is None:
                subprocess.run([str(MAM), "wait", "stop", "--agent", "waiter-one"], capture_output=True, cwd=self.projects)
                waiter.terminate()
                waiter.wait(timeout=3)
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=3)

    def test_waiters_for_two_agents_are_independent(self):
        task = self.task()
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
        waiters = []
        try:
            self.call("add", task, "--note", "shared wait", "--host", "localhost", "--pid", str(child.pid), command="job")
            for agent in ("waiter-left", "waiter-right"):
                waiters.append(subprocess.Popen([str(MAM), "wait", "jobs", "--task", task,
                                                  "--agent", agent, "--timeout", "10"], stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, text=True, cwd=self.projects))
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                agents = {row.split("\t")[0] for row in self.wait_list_lines()[1:]}
                if agents == {"waiter-left", "waiter-right"}:
                    break
                time.sleep(0.05)
            else:
                self.fail("both waiters were not registered")
            self.wait_call("stop", "--agent", "waiter-left")
            stdout, stderr = waiters[0].communicate(timeout=3)
            self.assertEqual(waiters[0].returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["status"], "cancelled")
            self.assertIsNone(waiters[1].poll())
            self.assertEqual({row.split("\t")[0] for row in self.wait_list_lines()[1:]}, {"waiter-right"})
            self.wait_call("stop", "--agent", "waiter-right")
            stdout, stderr = waiters[1].communicate(timeout=3)
            self.assertEqual(waiters[1].returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["status"], "cancelled")
        finally:
            for agent, waiter in zip(("waiter-left", "waiter-right"), waiters):
                if waiter.poll() is None:
                    subprocess.run([str(MAM), "wait", "stop", "--agent", agent], capture_output=True, cwd=self.projects)
                    waiter.terminate()
                    waiter.wait(timeout=3)
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=3)

    def test_wait_reports_empty_timeout_stopped_unknown_and_stale_records(self):
        empty = self.task()
        environment = {key: value for key, value in os.environ.items() if key != "CODEX_THREAD_ID"}
        environment["CODEX_SESSION_ID"] = "inherited-root-session"
        missing = self.wait_call("jobs", "--task", empty, env=environment, ok=False)
        self.assertIn("CODEX_THREAD_ID", missing["error"])
        self.assertEqual(self.wait_call("jobs", "--task", empty, "--agent", "empty-agent")["status"], "empty")

        task = self.task()
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
        try:
            job = self.call("add", task, "--note", "timeout smoke", "--host", "localhost", "--pid", str(child.pid), command="job")
            self.assertEqual(self.wait_call("jobs", "--task", task, "--agent", "timeout-agent", "--timeout", "0.05")["status"], "timeout")
            self.assertIsNone(child.poll())
            child.terminate()
            child.wait(timeout=3)
            self.assertEqual(self.call("status", job["id"], command="job")["status"], "stopped")
            stopped = self.wait_call("jobs", "--task", task, "--agent", "stopped-agent")
            self.assertEqual((stopped["status"], stopped["job"]), ("stopped", job["id"]))
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=3)

        unknown = self.task()
        data = self.store.read(unknown)
        data["jobs"] = [{"id": "unknown-job", "note": "offline", "host": "invalid;host", "pid": 1,
                         "identity": {"host": "invalid;host", "boot_id": "boot", "start_ticks": 1}, "status": "running",
                         "checked_at": "saved", "probe": {"status": "unknown", "checked_at": "saved", "error": "offline"},
                         "archive": None}]
        self.store.write(data)
        self.assertEqual(self.wait_call("jobs", "--task", unknown, "--agent", "unknown-agent", "--timeout", "0.05")["status"], "timeout")
        self.store.write_wait({"agent": "stale-agent", "pid": 999999, "identity": {"host": "local", "boot_id": "old", "start_ticks": 1},
                               "token": "stale", "kind": "jobs", "task": unknown, "timeout": None, "started_at": "old", "cancelled": None})
        self.assertEqual(self.wait_list_lines(), ["AGENT-ID\t绑定任务标题\tTASK-ID\t等待内容\t等待开始时间"])
        self.assertEqual(self.wait_call("jobs", "--task", unknown, "--agent", "stale-agent", "--timeout", "0.05")["status"], "timeout")

    def test_wait_deadline_limits_each_remote_probe(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [{"id": str(index), "status": "running", "host": "remote",
                         "pid": index + 1, "identity": None} for index in range(8)]
        self.store.write(data)
        real_probe = cli.runtime().probe_process
        for duration, expected in ((0.01, [0.01]), (0.75, [0.5, 0.25])):
            clock, budgets = [100.0], []

            def probe(host, pid, identity=None, timeout=None):
                if host == "local":
                    return real_probe(host, pid, identity)
                budgets.append(timeout)
                clock[0] += timeout
                return {"status": "unknown", "error": "SSH query timed out"}

            with self.subTest(duration=duration), patch.object(cli.time, "monotonic", side_effect=lambda: clock[0]), \
                    patch.object(cli, "runtime", return_value=types.SimpleNamespace(probe_process=probe)):
                result = cli.wait_jobs(self.store, types.SimpleNamespace(
                    task=task, agent="deadline-agent", timeout=duration))
            self.assertEqual(result["status"], "timeout")
            self.assertEqual(len(budgets), len(expected))
            for actual, wanted in zip(budgets, expected):
                self.assertAlmostEqual(actual, wanted)
            self.assertFalse(self.store.wait_path("deadline-agent").exists())

    def test_attention_marks_stopped_job_with_unknown_agent(self):
        task = self.task()
        process = {"status": "running", "identity": {"boot_id": "boot", "start_ticks": 10},
                   "checked_at": "checked", "error": None}
        fake = types.SimpleNamespace(probe_process=lambda *args: dict(process),
                                     probe_agents=lambda ids: {})
        with patch.object(cli, "runtime", return_value=fake):
            job = cli.job_add(self.store, types.SimpleNamespace(task=task, note="stopped job", host="local", pid=10))
            process["status"] = "stopped"
            for agent in (None, "unavailable-agent"):
                data = self.store.read(task)
                data["agent"] = agent
                self.store.write(data)
                with self.subTest(agent=agent), patch("sys.stdout", new_callable=io.StringIO) as output:
                    self.assertEqual(cli.main(["job", "list", "--attention"], cwd=self.projects), 0)
                rows = output.getvalue().splitlines()
                self.assertEqual(len(rows), 2)
                self.assertEqual(len(rows[1].split("\t")), 6)
                self.assertEqual(rows[1].split("\t")[1], "unknown/待核实")
                self.assertEqual(rows[1].split("\t")[3], job["id"])

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
