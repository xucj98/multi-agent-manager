from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/task.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("task_cli", SCRIPT)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="task tests with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.projects = Path(self.temp.name) / "Projects"
        self.root = self.source("agent-workflow")
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

    def call(self, *args, ok=True):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def task(self):
        return self.call("create", "--title", "test task")["id"]

    def add(self, task, repo="agent-workflow", ok=True):
        return self.call("workspace", "add", task, "--repo", repo, "--base", self.git(self.projects / repo, "rev-parse", "main"), ok=ok)

    def publish(self, task, kind="task"):
        return self.call("publish", task, "--file", kind)["revision"]

    def report(self, task, revision):
        self.store.doc(task, "report").write_text(f"task_revision: {revision}\nCompleted the task; tests passed.\n")
        return self.publish(task, "report")

    def test_parallel_publications_preserve_drafts_and_index(self):
        first, second, draft = self.task(), self.task(), self.task()
        (self.root / "code.py").write_text("staged = True\n")
        self.git(self.root, "add", "code.py")
        (self.root / "code.py").write_text("unstaged = True\n")
        index = (self.root / ".git/index").read_bytes()
        draft_bytes = self.store.doc(draft, "task").read_bytes()
        commands = [[sys.executable, "-B", str(SCRIPT), "--root", str(self.root), "publish", task, "--file", "task"] for task in (first, second)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for command in commands]
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, stderr)
        for task in (first, second):
            self.assertIn("test task", self.git(self.root, "show", f"main:.tasks/{task}/task.md"))
        self.assertEqual((self.root / ".git/index").read_bytes(), index)
        self.assertEqual((self.root / "code.py").read_text(), "unstaged = True\n")
        self.assertEqual(self.store.doc(draft, "task").read_bytes(), draft_bytes)
        self.assertEqual(self.git(self.root, "show", "main:code.py"), "original = True")

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
        self.assertEqual(review["review"]["commits"]["agent-workflow"], self.git(worktree, "rev-parse", "HEAD"))
        self.assertIn("test task", self.call("show", task, "--revision", revision)["content"])
        self.call("create", "--title", "bad review", "--review", self.task(), ok=False)

    def test_bind_and_empty_archive_have_no_accept_gate(self):
        first, second = self.task(), self.task()
        self.call("bind", first, "--agent", "agent-1")
        self.call("bind", second, "--agent", "agent-1", ok=False)
        self.call("archive", first, "--note", "cancelled before implementation")
        self.call("bind", second, "--agent", "agent-1")
        self.assertEqual(len(self.call("list", "--archived")), 1)
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
        self.assertTrue(self.call("status", task)["repos"]["agent-workflow"]["removed"])
        self.git(self.projects / "robot-bridge", "worktree", "unlock", str(second))
        self.call("archive", task, "--note", "retry")
        self.assertFalse(second.parent.exists())

    def test_real_stdlib_environment_entry_and_linked_defaults(self):
        scripts = self.root / "scripts"
        scripts.mkdir()
        implementation = SCRIPT.parent
        for name in ("create_worktree.sh", "local_create_worktree.sh"):
            (scripts / name).write_bytes((implementation / name).read_bytes())
        self.git(self.root, "add", "scripts")
        self.git(self.root, "commit", "-m", "environment entry")
        (self.root / ".local/create_worktree.sh").write_bytes((scripts / "local_create_worktree.sh").read_bytes())
        task = self.task()
        path = Path(self.add(task)["path"])
        subprocess.run([str(path / ".venv/bin/python"), "-c", "import argparse, fcntl, json"], check=True)
        self.assertEqual(cli.Store(path).root, self.root)
        self.call("archive", task, "--note", "stdlib smoke finished")
        self.assertFalse(path.parent.exists())

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
            self.assertEqual(saved["jobs"][1]["status"], "running")


if __name__ == "__main__":
    unittest.main()
