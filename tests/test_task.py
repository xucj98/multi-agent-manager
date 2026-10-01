from __future__ import annotations

import io
import json
import os
import shlex
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
import uuid
from unittest.mock import patch

from multi_agent_manager import cli, identity, wake_runtime
from multi_agent_manager import task_state

ROOT = Path(__file__).resolve().parents[1]
_CLI_BOOTSTRAP = (
    "import sys; "
    "sys.path.insert(0, sys.argv.pop(1)); "
    "from multi_agent_manager.cli import main; "
    "raise SystemExit(main())"
)


def mam_command(*args: str, python: str | Path | None = None) -> list[str]:
    """Run this checkout's CLI without requiring an installed ``mam`` script."""

    return [
        str(python or sys.executable),
        "-I",
        "-S",
        "-B",
        "-c",
        _CLI_BOOTSTRAP,
        str(ROOT),
        *args,
    ]


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
        hooks = mam_root / ".local" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        entry = hooks / "workspace_add"
        entry.write_text("""#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
context = json.load(sys.stdin)
record = next(repo for repo in context['repos'] if repo['name'] == context['repo'])
source = Path(record['source'])
legacy = source / '.local/create_worktree.sh'
if not legacy.is_file() or legacy.is_symlink():
    sys.exit(f'source repository has no .local/create_worktree.sh: {source}')
sys.exit(subprocess.run(['bash', str(legacy), record['base'], record['branch'],
                         context['task']['workspace']], cwd=source).returncode)
""")
        entry.chmod(0o755)
        return cli.project_config(location)

    def call(self, *args, command="task", ok=True):
        result = subprocess.run(mam_command(command, *args), capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def task(self):
        return self.call("create", "--title", "test task")["id"]

    def task_with_manager(self):
        manager = str(uuid.uuid4())
        with patch.dict(os.environ, {"CODEX_THREAD_ID": manager}):
            task = self.task()
        self.assertEqual(wake_runtime.recorded_manager(self.store), manager)
        return task, manager

    def test_service_message_channel_set_is_persistent_and_visible(self):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cli.main(["service", "set", "message-channel", "user"], cwd=self.projects), 0)
        self.assertEqual(json.loads(output.getvalue()), {"message_channel": "user"})
        self.assertEqual(wake_runtime.service_status(self.config)["message_channel"], "user")
        self.assertEqual(wake_runtime._load_state(self.store)["message_channel"], "user")
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cli.main(["service", "set", "message-channel", "tool"], cwd=self.projects), 0)
        self.assertEqual(json.loads(output.getvalue()), {"message_channel": "tool"})

    def test_unbound_sender_can_queue_default_and_immediate_messages_with_optional_task(self):
        task, manager = self.task_with_manager()
        sender = str(uuid.uuid4())
        with patch.dict(os.environ, {"CODEX_THREAD_ID": sender}), \
             patch.object(identity, "read", return_value=identity.ThreadIdentity(sender, "/root/free", manager)):
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(cli.main(["message", "send", "--message", "FYI"], cwd=self.projects), 0)
            first = json.loads(output.getvalue())
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(cli.main(["message", "send", "--message", "Follow-up", "--immediate", "--task", task], cwd=self.projects), 0)
            second = json.loads(output.getvalue())
        events = wake_runtime._load_state(self.store)["events"]
        self.assertIsNone(events[first["id"]]["task"])
        self.assertEqual(events[second["id"]]["task"], task)
        self.assertTrue(events[first["id"]]["defer"])
        self.assertFalse(events[second["id"]]["defer"])
        self.assertEqual(first["status"], "queued")
        self.assertEqual(first["service"], "disabled")

    def test_message_send_help_uses_immediate_and_rejects_defer(self):
        help_output = subprocess.check_output(
            mam_command("message", "send", "--help"), cwd=self.projects, text=True,
        )
        self.assertIn("--immediate", help_output)
        self.assertNotIn("--defer", help_output)
        result = subprocess.run(
            mam_command("message", "send", "--message", "legacy", "--defer"),
            cwd=self.projects, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_cli_message_modes_follow_scheduler_delivery(self):
        manager = str(uuid.uuid4())
        sender = str(uuid.uuid4())
        wake_runtime._record_manager(self.store, manager, source="test")
        statuses = {manager: "active"}
        turns = {manager: {"id": "manager-turn", "status": "inProgress"}}
        starts = []

        class Stream:
            def resume(self, agent):
                return {"thread": {"id": agent, "status": {"type": statuses[agent]}, "turns": []}}

            def read(self, agent):
                return self.resume(agent)

            def latest_turn(self, agent):
                return turns.get(agent)

            def start_turn(self, agent, text, *, message_channel="tool"):
                starts.append((agent, text, message_channel))
                turns[agent] = {"id": f"accepted-{len(starts)}", "status": "inProgress"}
                return {"turn": {"id": turns[agent]["id"], "status": "inProgress"}}

            def close(self):
                return None

        scheduler = wake_runtime.WakeScheduler(
            self.store,
            compatibility=lambda: {"socket_path": "/tmp/fake.sock", "capabilities": {}, "diagnostics": {}},
            agent_probe=lambda agents, socket_path: {
                agent: {"status": statuses[agent], "error": None} for agent in agents
            },
            stream_factory=lambda socket_path: Stream(),
            clock=lambda: 1000.0,
        )

        def send(arguments):
            with patch.dict(os.environ, {"CODEX_THREAD_ID": sender}), \
                 patch.object(identity, "read", return_value=identity.ThreadIdentity(sender, "/root/free", manager)), \
                 patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(cli.main(["message", "send", *arguments], cwd=self.projects), 0)
            return json.loads(output.getvalue())

        default = send(["--message", "background"])
        immediate = send(["--message", "urgent", "--immediate"])
        scheduler.run_once()
        self.assertEqual(len(starts), 1)
        self.assertIn("urgent", starts[0][1])
        self.assertEqual(starts[0][2], "tool")
        events = wake_runtime._load_state(self.store)["events"]
        self.assertIn(default["id"], events)
        self.assertNotIn(immediate["id"], events)

        statuses[manager] = "idle"
        turns[manager] = {"id": "accepted-1", "status": "completed"}
        scheduler.run_once()
        self.assertEqual(len(starts), 2)
        self.assertIn("background", starts[1][1])
        self.assertEqual(starts[1][2], "tool")
        self.assertNotIn(default["id"], wake_runtime._load_state(self.store)["events"])

        turns[manager] = {"id": "accepted-2", "status": "completed"}
        idle_immediate = send(["--message", "idle urgent", "--immediate"])
        scheduler.run_once()
        self.assertEqual(len(starts), 3)
        self.assertIn("idle urgent", starts[2][1])
        self.assertEqual(starts[2][2], "tool")
        self.assertNotIn(idle_immediate["id"], wake_runtime._load_state(self.store)["events"])

    def test_message_queue_reports_enabled_service_without_process_as_unavailable(self):
        _, manager = self.task_with_manager()
        sender = str(uuid.uuid4())
        state = wake_runtime._load_state(self.store)
        state["enabled"] = True
        wake_runtime._save_state(self.store, state)
        with patch.dict(os.environ, {"CODEX_THREAD_ID": sender}), \
             patch.object(identity, "read", return_value=identity.ThreadIdentity(sender, "/root/free", manager)):
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(cli.main(["message", "send", "--message", "Check status"], cwd=self.projects), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "queued")
        self.assertEqual(result["service"], "unavailable")

    def fixture_bind(self, task, agent):
        data = self.store.read(task)
        data["agent"] = agent
        self.store.write(data)

    def add(self, task, repo="multi-agent-manager", ok=True):
        return self.call("add", task, "--repo", repo, "--base", self.git(self.projects / repo, "rev-parse", "main"), command="workspace", ok=ok)

    def publish(self, task, kind="task"):
        return self.call({"task": "publish", "report": "report"}[kind], task)["revision"]

    def report(self, task):
        self.store.doc(task, "report").write_text("Completed the task; tests passed.\n")
        return self.publish(task, "report")

    def clean_task(self, task):
        self.git(self.store.root, "add", "--", f".tasks/{task}")
        self.git(self.store.root, "commit", "-m", f"Record {task}", "--only", "--", f".tasks/{task}")

    def prepare_rebind(self, task, current="old-executor", replacement="new-executor", manager="manager-agent"):
        data = self.store.read(task)
        data["agent"] = current
        self.store.write(data)
        manager = wake_runtime.recorded_manager(self.store) or manager
        wake_runtime._record_manager(self.store, manager, source="test")
        states = {
            current: {"status": "idle", "checked_at": "test", "error": None},
            replacement: {"status": "idle", "checked_at": "test", "error": None},
        }
        args = types.SimpleNamespace(task=task, agent=replacement, note="handoff after old executor completed")
        return args, states, manager

    def rebind_direct(self, args, states, manager):
        with patch.dict(os.environ, {"CODEX_THREAD_ID": manager}, clear=False), \
                patch.object(cli, "agent_observations", return_value=states), \
                patch.object(identity, "read", side_effect=lambda agent: identity.ThreadIdentity(
                    agent, "/root" if agent == manager else "/root/replacement", manager)):
            return cli.rebind(self.store, args)

    def task_output(self, *args):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(cli.main(["task", *args], cwd=self.projects), 0)
        return output.getvalue()

    def task_command_output(self, *args):
        result = subprocess.run(mam_command("task", *args), capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def job_command_output(self, *args):
        result = subprocess.run(mam_command("job", *args), capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_source_cli_launcher_needs_no_adjacent_mam_or_site_package(self):
        launcher = Path(self.temp.name) / "bare-python"
        launcher.symlink_to(Path(sys.executable).resolve())
        self.assertFalse(launcher.with_name("mam").exists())

        shadow = Path(self.temp.name) / "shadow"
        package = shadow / "multi_agent_manager"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        marker = Path(self.temp.name) / "shadow-cli-ran"
        (package / "cli.py").write_text(
            "from pathlib import Path\n"
            "import os\n"
            "Path(os.environ['MAM_TEST_SHADOW_MARKER']).write_text('shadow', encoding='utf-8')\n"
            "raise SystemExit(91)\n",
            encoding="utf-8",
        )
        environment = dict(os.environ)
        environment.update({"PYTHONPATH": str(shadow), "MAM_TEST_SHADOW_MARKER": str(marker)})
        result = subprocess.run(
            mam_command("task", "list", python=launcher),
            capture_output=True,
            cwd=self.projects,
            env=environment,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["标题\t任务状态\tTASK-ID\t执行者\tagent状态"])
        self.assertFalse(marker.exists())


    def test_parallel_publications_preserve_drafts_and_index(self):
        first, second, draft = self.task(), self.task(), self.task()
        (self.root / "code.py").write_text("staged = True\n")
        self.git(self.root, "add", "code.py")
        (self.root / "code.py").write_text("unstaged = True\n")
        index = self.git(self.root, "ls-files", "--stage", "--", "code.py", ".gitignore")
        draft_bytes = self.store.doc(draft, "task").read_bytes()
        commands = [mam_command("task", "publish", task) for task in (first, second)]
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

    def test_publish_task_requires_explicit_target_even_for_bound_executor(self):
        task = self.task()
        initial_head = self.git(self.root, "rev-parse", "main")
        before = self.store.read(task)
        missing = subprocess.run(mam_command("task", "publish"), cwd=self.projects, capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("TASK-ID|AGENT-PATH", missing.stderr)
        self.assertEqual(self.git(self.root, "rev-parse", "main"), initial_head)
        self.assertEqual(self.store.read(task), before)

        agent = str(uuid.uuid4())
        self.fixture_bind(task, agent)
        before = self.store.read(task)
        with patch.dict(os.environ, {"CODEX_THREAD_ID": agent}):
            missing = subprocess.run(mam_command("task", "publish"), cwd=self.projects, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("TASK-ID|AGENT-PATH", missing.stderr)
            self.assertEqual(self.git(self.root, "rev-parse", "main"), initial_head)
            self.assertEqual(self.store.read(task), before)

        publication = self.call("publish", task)
        self.assertEqual(publication["id"], task)
        self.assertNotEqual(publication["revision"], initial_head)
        self.assertEqual(self.git(self.root, "show", f"main:.tasks/{task}/task.md"), "# test task")

        self.store.doc(task, "report").write_text("Done.\n")
        with patch.dict(os.environ, {"CODEX_THREAD_ID": agent}):
            report = self.call("report")
        self.assertEqual(report["id"], task)
        self.assertEqual(self.store.read(task)["status"], "pending")

    def test_target_help_and_required_option_values(self):
        def help_text(*args):
            return subprocess.check_output(mam_command(*args, "--help"), cwd=self.projects, text=True)

        publish_help = help_text("task", "publish")
        self.assertIn("mam task publish", publish_help)
        self.assertIn("TASK-ID|AGENT-PATH", publish_help)
        self.assertNotIn("[TASK-ID|AGENT-PATH]", publish_help)
        self.assertNotIn("--file", publish_help)
        for command in ("report",):
            help_output = help_text("task", command)
            self.assertIn("[TASK-ID|AGENT-PATH]", help_output)
            self.assertNotIn("--file", help_output)
        for command in (("task", "create"), ("task", "bind"), ("task", "show"),
                        ("task", "publish"), ("task", "report"),
                        ("task", "status"), ("task", "archive"),
                        ("job", "add"), ("job", "list"), ("workspace", "add")):
            text = help_text(*command)
            self.assertIn("TASK-ID|AGENT-PATH", text, command)
            self.assertNotIn("TARGET", text, command)
        self.assertNotIn("wait", help_text())
        for command in (("task", "start"), ("task", "rebind")):
            self.assertIn("TASK-ID", help_text(*command))
            self.assertNotIn("TASK-ID|AGENT-PATH", help_text(*command))

        task = self.task()
        for command in (("task", "archive", "--note", "done"),
                        ("task", "create", "--title", "review", "--review"),
                        ("job", "list", "--task")):
            result = subprocess.run(mam_command(*command), cwd=self.projects, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, command)
        self.assertEqual(self.store.read(task)["status"], "pending")

    def test_attach_command_is_removed(self):
        task = self.task()
        before = self.store.read(task)
        head = self.git(self.root, "rev-parse", "main")
        result = subprocess.run(mam_command("task", "attach", task), cwd=self.projects,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)
        self.assertNotIn("task attach", self.task_command_output("--help"))
        self.assertEqual(self.git(self.root, "rev-parse", "main"), head)
        self.assertEqual(self.store.read(task), before)

    def test_legacy_publish_file_option_is_rejected_without_side_effects(self):
        task = self.task()
        before = self.store.read(task)
        head = self.git(self.root, "rev-parse", "main")
        for kind in ("task", "report", "files"):
            with self.subTest(kind=kind):
                result = subprocess.run(mam_command("task", "publish", task, "--file", kind),
                                        cwd=self.projects, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("unrecognized arguments", result.stderr)
                self.assertEqual(self.git(self.root, "rev-parse", "main"), head)
                self.assertEqual(self.store.read(task), before)
        self.publish(task)
        self.store.doc(task, "report").write_text("Done.\n")
        self.call("report", task)
        self.assertEqual(self.call("show", task, "--file", "task", "--json")["content"], "# test task\n")
        self.assertEqual(self.call("show", task, "--file", "report", "--json")["content"], "Done.\n")

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
                    result = self.call({"task": "publish", "report": "report"}[kind], task)
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
                    {"task": cli.publish, "report": cli.report}[kind](self.store, types.SimpleNamespace(task=task))
                relative = f".tasks/{task}/{kind}.md"
                self.assertEqual(self.git(self.root, "show", f":{relative}"), content.strip())
                self.assertEqual(self.git(self.root, "show", f"main:{relative}"), content.strip())
                self.assertEqual(path.read_text(), content + "Later draft.\n")
                self.assertEqual(self.git(self.root, "diff", "--cached", "--", relative), "")

    def test_task_list_text_has_header_and_status_keeps_records(self):
        header = "标题\t任务状态\tTASK-ID\t执行者\tagent状态"
        self.assertEqual(self.task_command_output("list").splitlines(), [header])
        rejected = subprocess.run(mam_command("task", "list", "--json"), capture_output=True, text=True, cwd=self.projects)
        self.assertEqual(rejected.returncode, 2)
        unbound = self.call("create", "--title", "中文\n标题\twith whitespace")["id"]
        self.assertEqual(self.task_command_output("list").splitlines()[1].split("\t"),
                         ["中文 标题 with whitespace", "pending", unbound, "未绑定", "未绑定"])
        bound = self.task()
        self.fixture_bind(bound, "bound-agent")
        calls = []
        fake = types.SimpleNamespace(probe_agents=lambda ids: calls.append(ids) or {})
        with patch.object(cli, "runtime", return_value=fake):
            lines = self.task_output("list").splitlines()
            rows = {fields[2]: fields for fields in (line.split("\t") for line in lines[1:])}
            self.assertEqual(calls, [["bound-agent"]])
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[unbound], ["中文 标题 with whitespace", "pending", unbound, "未绑定", "未绑定"])
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
        rejected = subprocess.run(mam_command("task", "show", task, "--revision", first),
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
        after = json.loads(record.read_text())
        before_data = json.loads(before)
        self.assertEqual(after["status"], "working")
        self.assertEqual(after["wake_reminder_count"], 0)
        before_data["status"] = after["status"]
        before_data["wake_reminder_count"] = after["wake_reminder_count"]
        self.assertEqual(after, before_data)

    def test_job_list_filters_before_probes_and_keeps_realtime_status(self):
        def job(name, pid, status):
            return {"id": name, "note": name, "host": "local", "pid": pid,
                    "identity": {"boot_id": "boot", "start_ticks": pid}, "status": status,
                    "checked_at": "saved", "probe": {"status": status, "checked_at": "saved", "error": None}, "archive": None}

        active, archived = self.task(), self.task()
        self.fixture_bind(active, "active-agent")
        self.fixture_bind(archived, "archived-agent")
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
        self.assertEqual(result["status"], "exited")
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
        self.assertEqual(unknown["last_known_status"], "exited")
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
        reused = self.call("report", task)
        self.assertTrue(reused["unchanged"])
        self.assertEqual(reused["revision"], report_publication)
        self.assertEqual(self.store.read(task)["report"]["commits"]["multi-agent-manager"], delivery)
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

    def test_report_publishes_without_usable_worktree_and_forgets_old_head(self):
        task = self.task()
        worktree = Path(self.add(task)["path"])
        self.publish(task)
        self.report(task)
        self.assertIn("multi-agent-manager", self.store.read(task)["report"]["commits"])
        self.git(self.root, "worktree", "remove", str(worktree))
        attachment = self.store.logs / task / "files" / "result.txt"
        attachment.write_text("available evidence\n")
        self.store.doc(task, "report").write_text("Report is independent of checkout.\n")
        result = self.call("report", task)
        self.assertEqual(result["report"]["commits"], {})
        self.assertEqual(self.store.read(task)["report"]["commits"], {})
        self.assertEqual(self.store.read(task)["status"], "pending")
        self.assertEqual(self.git(self.root, "show", f"{result['revision']}:.tasks/{task}/files/result.txt"),
                         "available evidence")

        failed = self.task()
        (self.root / ".local/fail-before").touch()
        self.add(failed, ok=False)
        (self.root / ".local/fail-before").unlink()
        self.store.doc(failed, "report").write_text("Worktree creation failed.\n")
        self.assertEqual(self.call("report", failed)["report"]["commits"], {})

        unreadable = self.task()
        broken_path = Path(self.add(unreadable)["path"])
        (broken_path / ".git").write_text("invalid worktree metadata\n")
        self.store.doc(unreadable, "report").write_text("Git metadata is unreadable.\n")
        self.assertEqual(self.call("report", unreadable)["report"]["commits"], {})

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
        self.clean_task(first)
        agent = "00000000-0000-4000-8000-000000000011"
        native = identity.ThreadIdentity(agent, "/root/agent-1", "00000000-0000-4000-8000-000000000010")
        with patch.object(cli, "caller_identity", return_value=native):
            cli.start(self.store, types.SimpleNamespace(task=first))
            with self.assertRaisesRegex(cli.Error, "already bound to another task"):
                cli.start(self.store, types.SimpleNamespace(task=second))
        self.call("archive", first, "--note", "cancelled before implementation")
        with patch.object(cli, "caller_identity", return_value=native):
            cli.start(self.store, types.SimpleNamespace(task=second))
        self.assertEqual(len(self.task_command_output("list", "--archived").splitlines()), 2)
        self.assertTrue(self.store.doc(first, "task").exists())
        self.assertEqual(self.call("status", first)["status"], "archived")

    def test_rebind_preserves_workspace_jobs_publications_and_audits_handoff(self):
        task = self.task()
        workspace = self.add(task)
        task_revision = self.publish(task)
        report_revision = self.report(task)
        data = self.store.read(task)
        data["jobs"] = [{
            "id": "handoff-job", "note": "formal evaluation", "host": "remote", "pid": 42,
            "identity": {"host": "remote", "boot_id": "boot", "start_ticks": 42},
            "status": "running", "checked_at": "before", "started_at": "before",
            "probe": {"status": "running", "checked_at": "before", "error": None}, "archive": None,
        }]
        data["review"] = {"task": "source-task", "commits": {"multi-agent-manager": "source-commit"}}
        self.store.write(data)
        args, states, manager = self.prepare_rebind(task)
        before = self.store.read(task)
        result = self.rebind_direct(args, states, manager)
        after = self.store.read(task)

        self.assertEqual(result["agent"], "new-executor")
        self.assertEqual(after["workspace"], before["workspace"])
        self.assertEqual(after["repos"], before["repos"])
        self.assertEqual(after["jobs"], before["jobs"])
        self.assertEqual(after["report"], before["report"])
        self.assertEqual(after["review"], before["review"])
        self.assertEqual(self.call("status", task)["publications"], {"task": task_revision, "report": report_revision})
        self.assertEqual(after["repos"]["multi-agent-manager"]["path"], workspace["path"])
        self.assertEqual(after["handoffs"], [{
            "from_agent": "old-executor", "to_agent": "new-executor", "at": after["handoffs"][0]["at"],
            "note": args.note, "manager": manager,
        }])
        self.assertEqual(self.call("status", task)["handoffs"], after["handoffs"])

    def test_rebind_accepts_readonly_not_loaded_threads(self):
        task = self.task()
        args, states, manager = self.prepare_rebind(task)
        states["old-executor"]["status"] = "notLoaded"
        states["new-executor"]["status"] = "notLoaded"
        result = self.rebind_direct(args, states, manager)
        self.assertEqual(result["agent"], "new-executor")

    def test_rebind_rejects_busy_or_unverifiable_executor_or_replacement(self):
        cases = (
            ("old-executor", "active", "current executor is active"),
            ("old-executor", "unknown", "cannot verify current executor state"),
            ("new-executor", "active", "replacement agent is active"),
            ("new-executor", "unknown", "cannot verify replacement agent state"),
            ("new-executor", "idle", "cannot verify replacement agent state"),
        )
        for agent, state, message in cases:
            with self.subTest(agent=agent, state=state):
                task = self.task()
                args, states, manager = self.prepare_rebind(task)
                states[agent] = {"status": state, "checked_at": "test", "error": "App Server unavailable"}
                with self.assertRaisesRegex(cli.Error, message):
                    self.rebind_direct(args, states, manager)
                self.assertEqual(self.store.read(task)["agent"], "old-executor")
                self.assertNotIn("handoffs", self.store.read(task))

    def test_rebind_rejects_conflicts_manager_invalid_archived_and_unbound_tasks(self):
        task = self.task()
        args, states, manager = self.prepare_rebind(task)
        other = self.task()
        other_data = self.store.read(other)
        other_data["agent"] = args.agent
        self.store.write(other_data)
        with self.assertRaisesRegex(cli.Error, "already bound to another task"):
            self.rebind_direct(args, states, manager)

        other_data["status"] = "archived"
        self.store.write(other_data)
        manager_args = types.SimpleNamespace(task=task, agent=manager, note=args.note)
        with self.assertRaisesRegex(cli.Error, "recorded Manager"):
            self.rebind_direct(manager_args, states, manager)
        invalid_args = types.SimpleNamespace(task=task, agent="bad\nagent", note=args.note)
        with self.assertRaisesRegex(cli.Error, "single-line AGENT-ID"):
            self.rebind_direct(invalid_args, states, manager)

        unbound = self.task()
        unbound_args = types.SimpleNamespace(task=unbound, agent="new-unbound", note=args.note)
        unbound_states = {"new-unbound": {"status": "idle", "checked_at": "test", "error": None}}
        with self.assertRaisesRegex(cli.Error, "no current executor"):
            self.rebind_direct(unbound_args, unbound_states, manager)

        archived = self.task()
        archived_data = self.store.read(archived)
        archived_data.update({"agent": "old-archived", "status": "archived"})
        self.store.write(archived_data)
        archived_args = types.SimpleNamespace(task=archived, agent="new-archived", note=args.note)
        archived_states = {
            "old-archived": {"status": "idle", "checked_at": "test", "error": None},
            "new-archived": {"status": "idle", "checked_at": "test", "error": None},
        }
        with self.assertRaisesRegex(cli.Error, "is archived"):
            self.rebind_direct(archived_args, archived_states, manager)

        with patch.dict(os.environ, {"CODEX_THREAD_ID": "another-manager"}, clear=False), \
                patch.object(cli, "agent_observations", return_value=states):
            with self.assertRaisesRegex(cli.Error, "must be called by the recorded Manager"):
                cli.rebind(self.store, args)

    def test_rebind_same_target_is_a_non_mutating_retry(self):
        task = self.task()
        args, states, manager = self.prepare_rebind(task)
        self.rebind_direct(args, states, manager)
        path = self.store.state / f"{task}.json"
        before = path.read_bytes()
        repeated = types.SimpleNamespace(task=task, agent=args.agent, note="lost CLI response retry")
        result = self.rebind_direct(repeated, {args.agent: {"status": "active", "checked_at": "later", "error": None}}, manager)
        self.assertTrue(result["unchanged"])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(len(self.store.read(task)["handoffs"]), 1)

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

        help_result = subprocess.run(mam_command("workspace", "add", "--help"), capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)
        self.assertIn("below PROJECT_ROOT", help_result.stdout)
        self.assertNotIn("robot-bridge", help_result.stdout)

        missing = self.source("no-entry-repository")
        (missing / ".local" / "create_worktree.sh").unlink()
        missing_task = self.task()
        missing_result = self.add(missing_task, "no-entry-repository", ok=False)
        self.assertIn("has no .local/create_worktree.sh", missing_result["error"])
        self.assertEqual(self.store.read(missing_task)["repos"]["no-entry-repository"]["state"], "failed")

        linked_entry = self.source("linked-entry-repository")
        entry = linked_entry / ".local" / "create_worktree.sh"
        entry.unlink()
        entry.symlink_to(linked_entry / "code.py")
        linked_task = self.task()
        linked_result = self.add(linked_task, "linked-entry-repository", ok=False)
        self.assertIn("has no .local/create_worktree.sh", linked_result["error"])
        self.assertEqual(self.store.read(linked_task)["repos"]["linked-entry-repository"]["state"], "failed")

        self.clean_task(task)
        self.call("archive", task, "--note", "custom repository cleanup")
        self.assertFalse(Path(record["path"]).exists())
        self.assertFalse(cli.branch_exists(source, f"task/{task}"))

    def test_archive_force_removes_dirty_workspace_and_preserves_symlink_targets(self):
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
        self.clean_task(task)
        for path in (first / "checkpoint", first / "temp", first.parent / "temp"):
            path.mkdir()
            (path / "keep").write_text("keep")
        refused = self.call("archive", task, "--note", "done", ok=False)
        self.assertIn("archive incomplete", refused["error"])
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())
        self.call("archive", task, "--note", "done", "--force")
        self.assertFalse(first.parent.exists())
        self.assertTrue((shared / "keep").exists())
        self.assertFalse(cli.branch_exists(self.root, f"task/{task}"))
        self.assertFalse(cli.branch_exists(self.projects / "robot-bridge", f"task/{task}"))
        self.assertEqual(self.call("status", task)["status"], "archived")

    def test_git_removal_failure_is_retryable(self):
        self.source("robot-bridge")
        task = self.task()
        first, second = Path(self.add(task)["path"]), Path(self.add(task, "robot-bridge")["path"])
        self.clean_task(task)
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
        (scripts / "create_worktree.sh").write_bytes((implementation / "create_worktree.sh").read_bytes())
        self.assertNotIn(" task list", (implementation / "create_worktree.sh").read_text())
        shutil.copytree(ROOT / "multi_agent_manager", self.root / "multi_agent_manager", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "pyproject.toml", self.root / "pyproject.toml")
        self.git(self.root, "add", "scripts", "multi_agent_manager", "pyproject.toml")
        self.git(self.root, "commit", "-m", "environment entry")
        outside = tempfile.TemporaryDirectory(prefix="mam test Python ", dir="/tmp")
        self.addCleanup(outside.cleanup)
        test_python = Path(outside.name) / "python"
        test_python.symlink_to(Path(sys.executable).resolve())
        self.assertFalse(str(test_python).startswith("/mnt/public/"))
        (self.root / ".local/create_worktree.sh").write_text(
            """#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 ]]; then
  echo 'usage: .local/create_worktree.sh BASE_COMMIT BRANCH WORKSPACE_ROOT' >&2
  exit 2
fi
source_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$source_root"
base=$(git rev-parse --verify "$1^{commit}")
""" + f"python={shlex.quote(str(test_python))}\n" + """git show "$base:scripts/create_worktree.sh" | bash -s -- "$base" "$2" "$3" "$python"
""")
        self.assertIn('git show "$base:scripts/create_worktree.sh"', (self.root / ".local/create_worktree.sh").read_text())
        linked = self.projects / "production state"
        self.git(self.root, "worktree", "add", "-b", "project/state-vla", str(linked), "main")
        self.config = self.configure(self.projects, linked, "project/state-vla")
        self.store = cli.Store(self.config)

        missing = self.task()
        missing_path = Path(self.add(missing)["path"])
        self.assertFalse((missing_path / ".local").exists())
        self.clean_task(missing)
        self.call("archive", missing, "--note", "missing local README is allowed")

        source_readme = self.root / ".local/README.md"
        source_readme.write_text("Primary local instructions.\n")
        task = self.task()
        path = Path(self.add(task)["path"])
        local, linked_readme = path / ".local", path / ".local/README.md"
        self.assertTrue(local.is_dir())
        self.assertFalse(local.is_symlink())
        self.assertEqual(list(local.iterdir()), [linked_readme])
        self.assertTrue(linked_readme.is_symlink())
        self.assertEqual(linked_readme.readlink(), source_readme)
        self.assertEqual(linked_readme.read_text(), "Primary local instructions.\n")
        command = [str(path / ".venv/bin/python"), "-B", str(path / ".venv/bin/mam"), "task", "status", task]
        self.assertEqual(json.loads(subprocess.check_output(command, cwd=path))["id"], task)
        self.assertEqual(cli.Store(cli.project_config(path)).root, linked)

        linked_readme.unlink()
        linked_readme.write_text("Keep this conflicting file.\n")
        retry = subprocess.run(["bash", str(scripts / "create_worktree.sh"), self.git(self.root, "rev-parse", "main"),
                                f"task/{task}", str(path.parent), str(test_python)], cwd=self.root,
                               capture_output=True, text=True)
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assertEqual(linked_readme.read_text(), "Keep this conflicting file.\n")
        self.clean_task(task)
        self.call("archive", task, "--note", "stdlib smoke finished")
        self.assertEqual(source_readme.read_text(), "Primary local instructions.\n")
        self.assertFalse(path.parent.exists())

    def test_real_environment_uses_source_checkout_name(self):
        source = self.source("mam-dev")
        scripts = source / "scripts"
        scripts.mkdir()
        (scripts / "create_worktree.sh").write_bytes((ROOT / "scripts/create_worktree.sh").read_bytes())
        shutil.copytree(ROOT / "multi_agent_manager", source / "multi_agent_manager",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "pyproject.toml", source / "pyproject.toml")
        self.git(source, "add", "scripts", "multi_agent_manager", "pyproject.toml")
        self.git(source, "commit", "-m", "environment entry")
        entry = (ROOT / "scripts/local_create_worktree.sh").read_text()
        entry = entry.replace("python=${MAM_SHARED_PYTHON:-}", f"python={shlex.quote(sys.executable)}")
        (source / ".local/create_worktree.sh").write_text(entry)

        task = self.task()
        path = Path(self.add(task, "mam-dev")["path"])
        self.assertEqual(path, self.projects / "workspace" / task / "mam-dev")
        self.assertTrue((path / ".venv/bin/mam").is_file())
        self.assertEqual(cli.Store(cli.project_config(path)).root, self.root)
        self.clean_task(task)
        self.call("archive", task, "--note", "renamed source smoke finished")
        self.assertFalse(path.parent.exists())

    def test_worktree_entry_rejects_non_python_with_diagnostic(self):
        fake = Path(self.temp.name) / "not Python"
        fake.write_text("#!/usr/bin/env bash\nprintf 'not-a-python\\n'\n")
        fake.chmod(0o755)
        workspace = Path(self.temp.name) / "workspace"
        result = subprocess.run(["bash", str(ROOT / "scripts/create_worktree.sh"),
                                 self.git(self.root, "rev-parse", "main"), "task/diagnostic",
                                 str(workspace), str(fake)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("shared Python must be a runnable Python >= 3.10", result.stderr)
        self.assertFalse(workspace.exists())

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
        self.assertIn("delete the entire task workspace", " ".join(archive_help.split()))
        rows = subprocess.check_output([command, "task", "list"], cwd=self.projects, text=True)
        self.assertEqual(rows.splitlines(), ["标题\t任务状态\tTASK-ID\t执行者\tagent状态"])
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
            result = subprocess.run(mam_command("task", "create", "--title", title), cwd=project,
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
        rejected = subprocess.run(mam_command("task", "list"), cwd=nested, capture_output=True, text=True)
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
        missing = subprocess.run(mam_command("task", "list"), cwd=outside, capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("no .mam/env.json found", missing.stderr)
        help_result = subprocess.run(mam_command("--help"), cwd=outside, capture_output=True, text=True)
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

        created = subprocess.run(mam_command("task", "create", "--title", "linked MAM root"), cwd=self.projects,
                                 capture_output=True, text=True)
        self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
        task = json.loads(created.stdout)["id"]
        self.assertTrue((linked / ".local" / "tasks" / f"{task}.json").is_file())
        self.assertFalse((self.root / ".local" / "tasks" / f"{task}.json").exists())
        main_before = self.git(self.root, "rev-parse", "main")
        state_before = self.git(self.root, "rev-parse", "project/state-vla")
        published = subprocess.run(mam_command("task", "publish", task), cwd=self.projects,
                                   capture_output=True, text=True)
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
        self.assertEqual(self.git(self.root, "rev-parse", "main"), main_before)
        self.assertNotEqual(self.git(self.root, "rev-parse", "project/state-vla"), state_before)
        self.assertIn("linked MAM root", self.git(linked, "show", f"project/state-vla:.tasks/{task}/task.md"))

    def test_publish_rejects_wrong_configured_branch_without_changing_existing_job(self):
        self.git(self.root, "branch", "project/state-vla")
        config = self.configure(self.projects, self.root, "project/state-vla")
        store = cli.Store(config)
        created = subprocess.run(mam_command("task", "create", "--title", "wrong publication branch"), cwd=self.projects,
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

        rejected = subprocess.run(mam_command("task", "publish", task), cwd=self.projects,
                                  capture_output=True, text=True)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("must be checked out on MAM_BRANCH", rejected.stderr)
        self.assertEqual(record.read_bytes(), before)
        self.assertEqual(self.git(self.root, "rev-parse", "main"), main_before)
        self.assertEqual(self.git(self.root, "rev-parse", "project/state-vla"), branch_before)

    def test_archived_records_keep_historical_paths(self):
        task = self.task()
        self.clean_task(task)
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
            help_result = subprocess.run(mam_command(command, "--help"), capture_output=True, text=True)
            self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)
            self.assertIn(description, help_result.stdout)
            old = subprocess.run(mam_command("task", command, "--help"), capture_output=True, text=True)
            self.assertEqual(old.returncode, 2, old.stdout + old.stderr)
        self.assertEqual(self.job_command_output("list").splitlines(), ["描述\tjob状态\t开始时间\tJOB-ID\t任务描述\tTASK-ID\t执行者"])

    def test_symlink_workspace_is_unlinked_and_tampered_registration_rejected(self):
        task = self.task()
        self.clean_task(task)
        data = self.store.read(task)
        workspace = Path(data["workspace"])
        (workspace / ".task").unlink()
        workspace.rmdir()
        workspace.symlink_to(self.root, target_is_directory=True)
        self.call("archive", task, "--note", "remove link")
        self.assertFalse(workspace.exists())
        self.assertTrue((self.root / "code.py").exists())
        task = self.task()
        data = self.store.read(task)
        data["workspace"] = str(self.root)
        self.store.write(data)
        self.call("archive", task, "--note", "unsafe", ok=False)
        self.assertTrue((self.root / "code.py").exists())

    def test_running_process_archive_stops_tracking_without_stopping_process(self):
        try:
            process_runtime = cli.runtime()
        except cli.Error:
            self.skipTest("parallel job_runtime module has not been integrated")
        task = self.task()
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
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
            self.assertEqual(rows[0], "描述\tjob状态\t开始时间\tJOB-ID\t任务描述\tTASK-ID\t执行者")
            self.assertEqual(rows[1].split("\t"), ["owned smoke", "running", detail["started_at"], job["id"], "test task", task, "未绑定"])
            before = self.store.read(task)["jobs"][0]
            saved = cli.job_archive(self.store, types.SimpleNamespace(job=job["id"], note="tracking complete"))
            self.assertEqual(saved["status"], "archived")
            self.assertEqual(saved["identity"], before["identity"])
            self.assertEqual(saved["probe"], before["probe"])
            self.assertEqual(saved["checked_at"], before["checked_at"])
            self.assertEqual(saved["probe"]["status"], "running")
            self.assertIsNone(child.poll())
            self.assertEqual(process_runtime.probe_process("localhost", child.pid, job["identity"])["status"], "running")
            repeated = cli.job_archive(self.store, types.SimpleNamespace(job=job["id"], note="ignored retry note"))
            self.assertEqual(repeated["archive"], saved["archive"])
            archived = self.call("status", job["id"], command="job")
            self.assertEqual(archived["status"], "archived")
            self.assertEqual(archived["archive"]["note"], "tracking complete")
            self.clean_task(task)
            cli.archive(self.store, types.SimpleNamespace(task=task, note="smoke complete"))
            self.assertEqual(self.store.read(task)["status"], "archived")
            self.assertIsNone(child.poll())
            self.assertEqual(process_runtime.probe_process("localhost", child.pid, job["identity"])["status"], "running")
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)

    def test_job_archive_skips_unknown_remote_probe_and_preserves_history(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [{
            "id": "unreachable-job", "note": "remote results", "host": "unreachable.example", "pid": 42,
            "identity": {"host": "unreachable.example", "boot_id": "boot", "start_ticks": 42},
            "status": "running", "checked_at": "last-running",
            "probe": {"status": "unknown", "checked_at": "offline", "error": "SSH query timed out"},
            "archive": None,
        }]
        self.store.write(data)
        before = json.loads(json.dumps(data["jobs"][0]))
        with patch.object(cli, "runtime", side_effect=AssertionError("job archive must not probe processes")):
            archived = cli.job_archive(self.store, types.SimpleNamespace(job="unreachable-job", note="results copied"))
            repeated = cli.job_archive(self.store, types.SimpleNamespace(job="unreachable-job", note="ignored retry note"))
        self.assertEqual(archived["status"], "archived")
        self.assertEqual(archived["identity"], before["identity"])
        self.assertEqual(archived["probe"], before["probe"])
        self.assertEqual(archived["checked_at"], before["checked_at"])
        self.assertEqual(archived["archive"]["note"], "results copied")
        self.assertEqual(repeated["archive"], archived["archive"])

    def test_task_archive_requires_all_jobs_archived_without_probing(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [{
            "id": "unarchived-job", "note": "remote results", "host": "unreachable.example", "pid": 42,
            "identity": {"host": "unreachable.example", "boot_id": "boot", "start_ticks": 42},
            "status": "running", "checked_at": "last-running",
            "probe": {"status": "unknown", "checked_at": "offline", "error": "SSH query timed out"},
            "archive": None,
        }]
        self.store.write(data)
        with patch.object(cli, "runtime", side_effect=AssertionError("archive must not probe processes")):
            with self.assertRaisesRegex(cli.Error, "unarchived registered jobs: unarchived-job"):
                cli.archive(self.store, types.SimpleNamespace(task=task, note="blocked"))
            self.assertEqual(self.store.read(task)["status"], "working")
            cli.job_archive(self.store, types.SimpleNamespace(job="unarchived-job", note="results copied"))
            self.clean_task(task)
            cli.archive(self.store, types.SimpleNamespace(task=task, note="complete"))
        self.assertEqual(self.store.read(task)["status"], "archived")


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
                self.assertEqual(len(rows[1].split("\t")), 7)
                self.assertEqual(rows[1].split("\t")[1], "unknown/待核实")
                self.assertEqual(rows[1].split("\t")[3], job["id"])

    def test_job_identity_attention_and_history(self):
        task = self.task()
        self.fixture_bind(task, "agent-1")
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
            with self.assertRaisesRegex(cli.Error, "unarchived registered jobs"):
                cli.archive(self.store, types.SimpleNamespace(task=task, note="done"))
            process["status"] = "running"
            saved = self.store.read(task)
            cli.refresh_jobs(saved)
            self.assertEqual(saved["jobs"][0]["status"], "archived")
            self.assertEqual(saved["jobs"][1]["status"], "running")

    def test_files_publication_is_isolated_and_tracks_add_update_delete(self):
        task, other = self.task(), self.task()
        files = self.store.logs / task / "files"
        self.assertEqual((Path(self.store.read(task)["workspace"]) / ".task").resolve(), files.parent)
        self.publish(task)
        (self.root / "code.py").write_text("staged = True\n")
        self.git(self.root, "add", "code.py")
        staged = self.git(self.root, "ls-files", "--stage", "code.py")
        self.store.doc(other, "task").write_text("unpublished other task\n")
        (files / "note.txt").write_text("first\n")
        (files / "nested").mkdir()
        (files / "nested" / "trace.json").write_text('{"ok": true}\n')
        self.store.doc(task, "report").write_text("Evidence included.\n")
        first = self.call("report", task)
        self.assertEqual(len(first["added"]), 2)
        self.assertEqual(self.git(self.root, "show", f"{first['revision']}:.tasks/{task}/report.md"),
                         "Evidence included.")
        changed_paths = self.git(self.root, "diff-tree", "--no-commit-id", "--name-only", "-r",
                                 first["revision"]).splitlines()
        self.assertEqual(set(changed_paths), {
            f".tasks/{task}/report.md", f".tasks/{task}/files/note.txt",
            f".tasks/{task}/files/nested/trace.json"})
        self.assertEqual(self.store.read(task)["status"], "pending")
        self.assertEqual(self.git(self.root, "ls-files", "--stage", "code.py"), staged)
        self.assertEqual(self.store.doc(other, "task").read_text(), "unpublished other task\n")
        self.assertEqual(self.git(self.root, "show", f"main:.tasks/{task}/files/note.txt"), "first")
        (files / "note.txt").write_text("second\n")
        (files / "nested" / "trace.json").unlink()
        self.assertTrue(self.call("status", task)["drafts"]["files"])
        self.assertEqual(self.git(self.root, "show", f"main:.tasks/{task}/files/note.txt"), "first")
        second = self.call("report", task)
        self.assertNotEqual(first["revision"], second["revision"])
        self.assertEqual(len(second["updated"]), 1)
        self.assertEqual(len(second["deleted"]), 1)
        before_unchanged = self.git(self.root, "rev-parse", "main")
        self.assertTrue(self.call("report", task)["unchanged"])
        self.assertEqual(self.git(self.root, "rev-parse", "main"), before_unchanged)
        self.assertEqual(self.store.read(task)["status"], "pending")
        self.assertEqual(self.git(self.root, "ls-files", "--stage", "code.py"), staged)
        (files / "escape").symlink_to(self.root / "code.py")
        self.store.doc(task, "report").write_text("Changed report should stay a draft.\n")
        before_state = self.store.read(task)
        before_index = self.git(self.root, "ls-files", "--stage", "--", f".tasks/{task}", "code.py")
        self.call("report", task, ok=False)
        self.assertEqual(self.git(self.root, "rev-parse", "main"), before_unchanged)
        self.assertEqual(self.git(self.root, "ls-files", "--stage", "--", f".tasks/{task}", "code.py"),
                         before_index)
        self.assertEqual(self.store.read(task), before_state)
        self.assertEqual(self.call("show", task, "--file", "report", "--json")["content"],
                         "Evidence included.\n")

    def test_files_only_report_revision_supports_review_and_legacy_record(self):
        task = self.task()
        self.publish(task)
        original = self.report(task)
        files = self.store.logs / task / "files"
        (files / "evidence.txt").write_text("first\n")
        result = self.call("report", task)
        self.assertNotEqual(result["revision"], original)
        self.assertEqual(self.call("show", task, "--file", "report", "--json")["revision"],
                         result["revision"])
        self.assertEqual(self.call("status", task)["publications"]["report"], result["revision"])
        review = self.call("create", "--title", "review new files", "--review", task)
        self.assertEqual(review["review"]["task"], task)
        self.assertIn("Completed the task", self.store.doc(review["id"], "task").read_text())
        data = self.store.read(task)
        data["report"]["revision"] = original
        self.store.write(data)
        self.assertEqual(self.call("show", task, "--file", "report", "--json")["revision"], original)
        self.call("create", "--title", "review legacy record", "--review", task)

    def test_unchanged_report_repairs_only_its_files_index(self):
        task, other = self.task(), self.task()
        self.publish(task)
        files = self.store.logs / task / "files"
        retained = files / "retained.txt"
        retained.write_text("published\n")
        revision = self.report(task)
        self.git(self.root, "update-index", "--force-remove", "--", f".tasks/{task}/files/retained.txt")
        extra = files / "extra.txt"
        extra.write_text("staged only\n")
        self.git(self.root, "add", "--", str(extra))
        extra.unlink()
        other_path = self.store.doc(other, "task")
        other_path.write_text("staged other draft\n")
        self.git(self.root, "add", "--", str(other_path))
        other_index = self.git(self.root, "ls-files", "--stage", "--", f".tasks/{other}/task.md")
        result = self.call("report", task)
        self.assertTrue(result["unchanged"])
        self.assertEqual(result["revision"], revision)
        self.assertEqual(self.git(self.root, "ls-files", "--stage", "--", f".tasks/{other}/task.md"),
                         other_index)
        self.assertEqual(self.git(self.root, "diff", "--cached", "--", f".tasks/{task}/files"), "")
        self.assertEqual(self.git(self.root, "ls-files", "--", f".tasks/{task}/files/extra.txt"), "")
        self.assertEqual(self.git(self.root, "show", f":.tasks/{task}/files/retained.txt"), "published")

    def test_report_keeps_new_attachment_edit_as_draft(self):
        task = self.task()
        self.publish(task)
        self.report(task)
        attachment = self.store.logs / task / "files" / "trace.txt"
        attachment.write_text("published\n")
        original_git = cli.git

        def edit_during_commit(repo, *args, **kwargs):
            if args[0] == "commit-tree":
                attachment.write_text("later draft\n")
            return original_git(repo, *args, **kwargs)

        with patch.object(cli, "git", side_effect=edit_during_commit):
            result = cli.report(self.store, types.SimpleNamespace(task=task))
        path = f".tasks/{task}/files/trace.txt"
        self.assertEqual(self.git(self.root, "show", f"{result['revision']}:{path}"), "published")
        self.assertEqual(self.git(self.root, "show", f":{path}"), "published")
        self.assertEqual(attachment.read_text(), "later draft\n")
        self.assertTrue(self.call("status", task)["drafts"]["files"])

    def test_archive_requires_clean_task_directory_then_cleans_tmp_and_link(self):
        task = self.task()
        worktree = Path(self.add(task)["path"])
        workspace = worktree.parent
        self.publish(task)
        self.git(worktree, "commit", "--allow-empty", "-m", "delivery")
        self.report(task)
        (self.store.logs / task / "files" / "draft.txt").write_text("draft")
        (workspace / "tmp").mkdir()
        (workspace / "tmp" / "scratch").write_text("ephemeral")
        manager_tmp = self.projects / "workspace" / "tmp" / "review"
        manager_tmp.mkdir(parents=True)
        (manager_tmp / "notes").write_text("preserve")
        self.call("archive", task, "--note", "done", ok=False)
        self.assertTrue(worktree.exists())
        self.clean_task(task)
        refused = self.call("archive", task, "--note", "default branch removal", ok=False)
        self.assertIn("archive incomplete", refused["error"])
        self.assertFalse(worktree.exists())
        self.call("archive", task, "--note", "explicit force", "--force")
        self.assertFalse(workspace.exists())
        self.assertEqual((manager_tmp / "notes").read_text(), "preserve")
        self.assertTrue((self.store.logs / task / "report.md").exists())
        self.assertTrue((self.store.logs / task / "files" / "draft.txt").exists())

    def test_archive_checks_all_task_paths_but_ignores_other_tasks(self):
        task = self.task()
        workspace = Path(self.store.read(task)["workspace"])
        self.clean_task(task)
        other = self.task()
        self.store.doc(other, "task").write_text("other task draft\n")
        path = self.store.logs / task / "extra.txt"
        path.write_text("untracked\n")
        self.assertIn("uncommitted Git changes", self.call("archive", task, "--note", "check", "--force", ok=False)["error"])
        self.assertTrue(workspace.exists())
        self.git(self.root, "add", "--", str(path))
        self.assertIn("uncommitted Git changes", self.call("archive", task, "--note", "check", ok=False)["error"])
        self.git(self.root, "reset", "--", str(path))
        path.unlink()
        task_doc = self.store.doc(task, "task")
        task_doc.write_text("modified\n")
        self.assertIn("uncommitted Git changes", self.call("archive", task, "--note", "check", ok=False)["error"])
        self.git(self.root, "restore", "--", str(task_doc))
        self.git(self.root, "rm", "--", str(task_doc))
        self.assertIn("uncommitted Git changes", self.call("archive", task, "--note", "check", ok=False)["error"])
        self.git(self.root, "restore", "--staged", "--worktree", "--", str(task_doc))
        self.call("archive", task, "--note", "other task is unrelated")
        self.assertFalse(workspace.exists())

    def test_archive_missing_or_failed_worktree_does_not_block_cleanup(self):
        task = self.task()
        worktree = Path(self.add(task)["path"])
        self.git(self.root, "worktree", "remove", str(worktree))
        worktree.mkdir()
        (worktree / "partial.txt").write_text("partial\n")
        self.clean_task(task)
        self.call("archive", task, "--note", "partial path")
        self.assertFalse(worktree.parent.exists())

        failed = self.task()
        (self.root / ".local/fail-before").touch()
        self.add(failed, ok=False)
        (self.root / ".local/fail-before").unlink()
        self.clean_task(failed)
        self.call("archive", failed, "--note", "creation failed")

    def test_archive_force_does_not_override_job_or_hook(self):
        task = self.task()
        self.clean_task(task)
        data = self.store.read(task)
        data["jobs"] = [{"id": "unfinished", "status": "running"}]
        self.store.write(data)
        self.assertIn("unarchived registered jobs", self.call("archive", task, "--note", "check", "--force", ok=False)["error"])
        data["jobs"][0]["status"] = "archived"
        self.store.write(data)
        hook = self.root / ".local/hooks/before_task_archive"
        hook.write_text("#!/bin/sh\nexit 3\n")
        hook.chmod(0o755)
        self.assertIn("exited 3", self.call("archive", task, "--note", "check", "--force", ok=False)["error"])
        hook.unlink()
        self.call("archive", task, "--note", "finished", "--force")

    def test_archive_has_no_main_branch_precheck(self):
        task = self.task()
        source = self.source("delivery-repo")
        worktree = Path(self.add(task, "delivery-repo")["path"])
        self.publish(task)
        self.git(worktree, "commit", "--allow-empty", "-m", "delivery")
        self.report(task)
        self.git(source, "branch", "feature-retains-delivery", self.git(worktree, "rev-parse", "HEAD"))
        self.git(source, "switch", "feature-retains-delivery")
        self.call("archive", task, "--note", "retained on feature")
        self.assertFalse(worktree.parent.exists())

    def test_start_rework_republish_and_tree_scoped_target(self):
        first, second = self.task(), self.task()
        self.publish(first)
        root_a, root_b = str(uuid.uuid4()), str(uuid.uuid4())
        agent_a, agent_b = str(uuid.uuid4()), str(uuid.uuid4())
        a = identity.ThreadIdentity(agent_a, "/root/worker", root_a)
        b = identity.ThreadIdentity(agent_b, "/root/worker", root_b)
        with patch.object(cli, "caller_identity", return_value=a), patch.dict(os.environ, {"CODEX_THREAD_ID": agent_a}):
            self.assertFalse(cli.start(self.store, types.SimpleNamespace(task=first))["unchanged"])
            self.assertTrue(cli.start(self.store, types.SimpleNamespace(task=None))["unchanged"])
            self.assertEqual(cli.task_target(self.store, "/root/worker"), first)
            with self.assertRaisesRegex(cli.Error, "already bound"):
                cli.start(self.store, types.SimpleNamespace(task=second))
        self.report(first)
        self.assertEqual(self.store.read(first)["status"], "working")
        with patch.object(cli, "caller_identity", return_value=a), patch.dict(os.environ, {"CODEX_THREAD_ID": agent_a}):
            cli.start(self.store, types.SimpleNamespace(task=None))
        self.assertEqual(self.store.read(first)["status"], "working")
        self.assertTrue(self.call("report", first)["unchanged"])
        self.assertEqual(self.store.read(first)["status"], "working")
        with patch.object(cli, "caller_identity", return_value=b), patch.dict(os.environ, {"CODEX_THREAD_ID": agent_b}):
            cli.start(self.store, types.SimpleNamespace(task=second))
            self.assertEqual(cli.task_target(self.store, "/root/worker"), second)
        with patch.object(cli, "caller_identity", return_value=a), patch.dict(os.environ, {"CODEX_THREAD_ID": agent_a}):
            self.assertEqual(cli.task_target(self.store, "/root/worker"), first)

    def test_start_handoff_requires_old_executor_quiescent(self):
        task = self.task()
        old, new, root = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        for agent in (old, new):
            native = identity.ThreadIdentity(agent, f"/root/{agent[:4]}", root)
            with patch.object(cli, "caller_identity", return_value=native), \
                    patch.object(cli, "agent_observations", return_value={old: {"status": "active"}}):
                if agent == old:
                    cli.start(self.store, types.SimpleNamespace(task=task))
                else:
                    with self.assertRaisesRegex(cli.Error, "current executor is active"):
                        cli.start(self.store, types.SimpleNamespace(task=task))
        with patch.object(cli, "caller_identity", return_value=identity.ThreadIdentity(new, "/root/new", root)), \
                patch.object(cli, "agent_observations", return_value={old: {"status": "idle"}}):
            cli.start(self.store, types.SimpleNamespace(task=task))
        self.assertEqual(self.store.read(task)["agent"], new)
        self.assertEqual(len(self.store.read(task)["handoffs"]), 1)

    def test_manager_takeover_retires_old_delivery_and_preserves_bindings(self):
        task, old = self.task_with_manager()
        new = str(uuid.uuid4())
        self.fixture_bind(task, str(uuid.uuid4()))
        state = wake_runtime._load_state(self.store)
        state["events"]["old-event"] = {"signature": "old-event", "recipient": old, "task": task,
                                        "delivery": "pending", "kind": "task_ready"}
        wake_runtime._save_state(self.store, state)
        with patch.dict(os.environ, {"CODEX_THREAD_ID": new}), \
                patch.object(identity, "read", return_value=identity.ThreadIdentity(new, "/root", new)), \
                patch.object(cli, "agent_observations", return_value={old: {"status": "active"}}):
            with self.assertRaisesRegex(RuntimeError, "current Manager is active"):
                wake_runtime.rebind_manager(self.store, "handoff")
        with patch.dict(os.environ, {"CODEX_THREAD_ID": new}), \
                patch.object(identity, "read", return_value=identity.ThreadIdentity(new, "/root", new)), \
                patch.object(cli, "agent_observations", return_value={old: {"status": "unknown"}}):
            with self.assertRaisesRegex(RuntimeError, "cannot verify current Manager state"):
                wake_runtime.rebind_manager(self.store, "handoff")
        with patch.dict(os.environ, {"CODEX_THREAD_ID": new}), \
                patch.object(identity, "read", return_value=identity.ThreadIdentity(new, "/root", new)), \
                patch.object(cli, "agent_observations", return_value={old: {"status": "idle"}}):
            self.assertFalse(wake_runtime.rebind_manager(self.store, "handoff")["unchanged"])
            self.assertTrue(wake_runtime.rebind_manager(self.store, "retry")["unchanged"])
        self.assertEqual(wake_runtime.recorded_manager(self.store), new)
        self.assertEqual(self.store.read(task)["agent"] != new, True)
        current = wake_runtime._load_state(self.store)
        self.assertNotIn("old-event", current["events"])
        self.assertEqual(current["manager"], new)
        self.assertEqual(current["history"][-1]["resolution"], "Manager identity changed")
        scheduler = wake_runtime.WakeScheduler(self.store)
        scheduler.manager = new
        desired, _, _ = scheduler._desired_events([self.store.read(task)],
                                                   {self.store.read(task)["agent"]: {"status": "idle"}})
        self.assertEqual({event["recipient"] for event in desired.values()}, {new})

    def test_legacy_task_link_is_repaired_without_overwriting_conflict(self):
        task = self.task()
        link = Path(self.store.read(task)["workspace"]) / ".task"
        link.unlink()
        self.add(task)
        self.assertEqual(link.resolve(), self.store.logs / task)
        link.unlink()
        link.mkdir()
        with self.assertRaisesRegex(cli.Error, "conflicting .task path"):
            cli.workspace_add(self.store, types.SimpleNamespace(task=task, repo="multi-agent-manager",
                                                           base=self.git(self.root, "rev-parse", "main")))

    def test_rebind_rejects_another_native_root_as_executor(self):
        task = self.task()
        args, states, manager = self.prepare_rebind(task)
        other_root = str(uuid.uuid4())
        args.agent = other_root
        states[other_root] = {"status": "idle"}
        with patch.dict(os.environ, {"CODEX_THREAD_ID": manager}), \
                patch.object(cli, "agent_observations", return_value=states), \
                patch.object(identity, "read", side_effect=lambda agent: identity.ThreadIdentity(
                    agent, "/root", agent)):
            with self.assertRaisesRegex(cli.Error, "native subagent"):
                cli.rebind(self.store, args)
        self.assertNotEqual(self.store.read(task)["agent"], other_root)

    def test_executable_attachment_mode_survives_publication_and_archive(self):
        task = self.task()
        self.publish(task)
        attachment = self.store.logs / task / "files" / "run.sh"
        attachment.write_text("#!/bin/sh\nexit 0\n")
        attachment.chmod(0o755)
        self.call("report", task)
        path = f".tasks/{task}/files/run.sh"
        self.assertTrue(self.git(self.root, "ls-tree", "main", "--", path).startswith("100755 blob "))
        self.assertNotIn("files", self.call("status", task).get("drafts", {}))
        self.assertTrue(self.call("report", task)["unchanged"])
        attachment.chmod(0o644)
        self.assertTrue(self.call("status", task)["drafts"]["files"])
        changed = self.call("report", task)
        self.assertEqual(changed["updated"], [path])
        self.assertTrue(self.git(self.root, "ls-tree", "main", "--", path).startswith("100644 blob "))
        attachment.chmod(0o755)
        self.call("report", task)
        self.call("archive", task, "--note", "published executable retained")

    def test_archive_retry_rechecks_task_directory_and_force_branch_removal(self):
        task = self.task()
        second = self.source("second-repo")
        first_tree = Path(self.add(task)["path"])
        second_tree = Path(self.add(task, "second-repo")["path"])
        self.publish(task)
        self.git(first_tree, "commit", "--allow-empty", "-m", "first delivery")
        self.git(second_tree, "commit", "--allow-empty", "-m", "second delivery")
        self.report(task)
        self.git(second, "worktree", "lock", str(second_tree))
        failed = self.call("archive", task, "--note", "first pass", "--force", ok=False)
        self.assertIn("archive incomplete", failed["error"])
        self.assertFalse(first_tree.exists())
        self.assertTrue(second_tree.exists())
        self.git(second, "worktree", "unlock", str(second_tree))

        attachment = self.store.logs / task / "files" / "new.txt"
        attachment.write_text("new evidence\n")
        refused = self.call("archive", task, "--note", "retry", ok=False)
        self.assertIn("uncommitted Git changes", refused["error"])
        self.call("report", task)
        self.git(second_tree, "commit", "--allow-empty", "-m", "new delivery")
        refused = self.call("archive", task, "--note", "retry", ok=False)
        self.assertIn("archive incomplete", refused["error"])
        self.assertFalse(second_tree.exists())
        self.call("archive", task, "--note", "force unmerged branch", "--force")
        archived = self.store.read(task)
        self.assertEqual(archived["status"], "archived")
        self.assertNotIn("discard_confirmations", archived["archive"])

    def test_unchanged_report_republishes_new_delivery_head(self):
        task = self.task()
        worktree = Path(self.add(task)["path"])
        self.publish(task)
        revision = self.report(task)
        self.git(worktree, "commit", "--allow-empty", "-m", "rework")
        data = self.store.read(task)
        data["status"] = "working"
        self.store.write(data)
        result = self.call("report", task)
        self.assertTrue(result["unchanged"])
        self.assertEqual(result["revision"], revision)
        data = self.store.read(task)
        self.assertEqual(data["report"]["commits"]["multi-agent-manager"], self.git(worktree, "rev-parse", "HEAD"))
        self.assertEqual(data["status"], "pending")

    def test_project_hook_context_and_template_repo_dispatch(self):
        state = self.projects / "state"
        self.git(self.root, "worktree", "add", "-b", "project/state", str(state), "main")
        self.config = self.configure(self.projects, state, "project/state")
        self.store = cli.Store(self.config)
        source = self.source("hooked-repo")
        project_entry = state / ".local/hooks/workspace_add"
        shutil.copyfile(ROOT / "templates/hooks/project/workspace_add", project_entry)
        project_entry.chmod(0o755)
        repo_hooks = source / ".local/hooks"
        repo_hooks.mkdir()
        repo_entry = repo_hooks / "workspace_add"
        shutil.copyfile(ROOT / "templates/hooks/repo/workspace_add", repo_entry)
        repo_entry.chmod(0o755)
        legacy = source / ".local/create_worktree.sh"
        with legacy.open("a") as handle:
            handle.write('printf x >> "$source_root/.local/calls"\n')
        task = self.task()
        first = self.add(task, "hooked-repo")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(self.add(task, "hooked-repo"), first)
        self.assertEqual((source / ".local/calls").read_text(), "x")
        self.clean_task(task)
        self.call("archive", task, "--note", "template dispatch complete")

    def test_project_hook_dispatcher_rejects_self_forwarding(self):
        state = self.projects / "state-self"
        self.git(self.root, "worktree", "add", "-b", "project/state-self", str(state), "main")
        self.config = self.configure(self.projects, state, "project/state-self")
        self.store = cli.Store(self.config)
        source = self.source("self-hook")
        entry = state / ".local/hooks/workspace_add"
        shutil.copyfile(ROOT / "templates/hooks/project/workspace_add", entry)
        entry.chmod(0o755)
        repo_entry = source / ".local/hooks/workspace_add"
        repo_entry.parent.mkdir(exist_ok=True)
        shutil.copyfile(entry, repo_entry)
        repo_entry.chmod(0o755)
        task = self.task()
        result = self.add(task, "self-hook", ok=False)
        self.assertIn("cannot dispatch to itself", result["error"])

    def test_project_hook_entry_context_and_failure_retry(self):
        source = self.source("context-repo")
        task = self.task()
        entry = self.root / ".local/hooks/workspace_add"
        entry.unlink()
        missing = self.add(task, "context-repo", ok=False)
        self.assertIn("required project hook is missing", missing["error"])
        self.assertEqual(self.store.read(task)["repos"]["context-repo"]["state"], "failed")
        entry.write_text("#!/bin/sh\nexit 2\n")
        invalid = self.add(task, "context-repo", ok=False)
        self.assertIn("executable regular file", invalid["error"])
        entry.chmod(0o755)
        capture = self.projects / "hook-context.json"
        entry.write_text("""#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
context = json.load(sys.stdin)
Path(%r).write_text(json.dumps({'cwd': str(Path.cwd()), 'context': context}))
record = next(item for item in context['repos'] if item['name'] == context['repo'])
subprocess.run(['bash', str(Path(record['source']) / '.local/create_worktree.sh'),
                record['base'], record['branch'], context['task']['workspace']], check=True)
print('hook stdout')
print('hook stderr', file=sys.stderr)
""" % str(capture))
        ready = self.add(task, "context-repo")
        context = json.loads(capture.read_text())
        self.assertEqual(context["cwd"], str(self.root))
        payload = context["context"]
        self.assertEqual((payload["schema_version"], payload["event"], payload["repo"]),
                         (1, "workspace_add", "context-repo"))
        self.assertEqual(payload["project_root"], str(self.projects))
        self.assertEqual(payload["mam_root"], str(self.root))
        self.assertEqual(payload["task"]["task_dir"], str(self.store.logs / task))
        self.assertEqual(payload["repos"][0]["path"], ready["path"])
        self.assertEqual(payload["repos"][0]["state"], "failed")
        self.assertIsNone(payload["repos"][0]["commit"])
        self.assertEqual(payload["jobs"], [])

    def test_archive_hook_rejection_retry_and_whole_workspace(self):
        task = self.task()
        path = Path(self.add(task)["path"])
        workspace = path.parent
        self.publish(task)
        self.report(task)
        shared = self.projects / "shared"
        shared.mkdir()
        (shared / "keep").write_text("keep")
        (path / "shared-link").symlink_to(shared, target_is_directory=True)
        (path / "code.py").write_text("dirty = True\n")
        (path / "untracked.txt").write_text("untracked")
        (path / "checkpoint").mkdir()
        (path / "checkpoint" / "model").write_text("ignored")
        (workspace / "unknown").mkdir()
        (workspace / "unknown" / "file").write_text("extra")
        (workspace / "tmp").symlink_to(shared, target_is_directory=True)
        entry = self.root / ".local/hooks/before_task_archive"
        entry.write_text("#!/bin/sh\necho archive blocked >&2\nexit 9\n")
        entry.chmod(0o755)
        refused = self.call("archive", task, "--note", "hold", ok=False)
        self.assertIn("archive blocked", refused["error"])
        self.assertTrue(path.exists())
        self.assertTrue(cli.branch_exists(self.root, f"task/{task}"))
        capture = self.projects / "archive-context.json"
        entry.write_text("""#!/usr/bin/env python3
import json
from pathlib import Path
import sys
context = json.load(sys.stdin)
Path(%r).write_text(json.dumps({'cwd': str(Path.cwd()), 'context': context}))
""" % str(capture))
        result = self.call("archive", task, "--note", "cleanup", "--force")
        self.assertFalse(workspace.exists())
        self.assertEqual((shared / "keep").read_text(), "keep")
        self.assertFalse(cli.branch_exists(self.root, f"task/{task}"))
        payload = json.loads(capture.read_text())
        self.assertEqual(payload["cwd"], str(self.root))
        self.assertEqual(payload["context"]["event"], "before_task_archive")
        self.assertIsNone(payload["context"]["repo"])
        self.assertEqual(payload["context"]["options"]["note"], "cleanup")
        self.assertTrue(payload["context"]["options"]["force"])
        capture.unlink()
        self.call("archive", task, "--note", "already archived")
        self.assertFalse(capture.exists())
        self.assertIsNotNone(result["at"])

    def test_hook_timeout_kills_child_process_group(self):
        task = self.task()
        config_path = self.projects / ".mam/env.json"
        config = json.loads(config_path.read_text())
        config["HOOK_TIMEOUTS"] = {"workspace_add": 0.2}
        config_path.write_text(json.dumps(config))
        entry = self.root / ".local/hooks/workspace_add"
        marker = self.projects / "late-child"
        entry.write_text(f"#!/bin/sh\n(sleep 0.5; touch {shlex.quote(str(marker))}) &\nsleep 5\n")
        entry.chmod(0o755)
        refused = self.add(task, ok=False)
        self.assertIn("timed out", refused["error"])
        time.sleep(0.7)
        self.assertFalse(marker.exists())
    def test_hook_rejects_reentrant_task_command(self):
        task = self.task()
        entry = self.root / ".local/hooks/workspace_add"
        entry.write_text(f"#!/bin/sh\n{shlex.quote(sys.executable)} -B -c 'import sys; sys.path.insert(0, sys.argv.pop(1)); from multi_agent_manager.cli import main; raise SystemExit(main())' {shlex.quote(str(ROOT))} task report {task}\n")
        entry.chmod(0o755)
        refused = self.add(task, ok=False)
        self.assertIn("cannot invoke a command that may modify task state", refused["error"])
        self.assertEqual(self.store.read(task)["repos"]["multi-agent-manager"]["state"], "failed")

    def test_archive_template_forwards_repo_context_and_invalid_optional_hook(self):
        state = self.projects / "state"
        self.git(self.root, "worktree", "add", "-b", "project/state", str(state), "main")
        self.config = self.configure(self.projects, state, "project/state")
        self.store = cli.Store(self.config)
        source = self.source("archive-repo")
        project_entry = state / ".local/hooks/before_task_archive"
        shutil.copyfile(ROOT / "templates/hooks/project/before_task_archive", project_entry)
        project_entry.chmod(0o755)
        repo_hooks = source / ".local/hooks"
        repo_hooks.mkdir()
        repo_entry = repo_hooks / "before_task_archive"
        capture = self.projects / "repo-archive-context.json"
        repo_entry.write_text("""#!/usr/bin/env python3
import json
from pathlib import Path
import sys
context = json.load(sys.stdin)
Path(%r).write_text(json.dumps({'cwd': str(Path.cwd()), 'context': context}))
sys.exit(4)
""" % str(capture))
        repo_entry.chmod(0o755)
        task = self.task()
        path = Path(self.add(task, "archive-repo")["path"])
        self.publish(task)
        self.report(task)
        denied = self.call("archive", task, "--note", "gate", ok=False)
        self.assertIn("exited 4", denied["error"])
        self.assertTrue(path.exists())
        received = json.loads(capture.read_text())
        self.assertEqual(received["cwd"], str(source))
        self.assertEqual(received["context"]["repo"], "archive-repo")
        self.assertEqual(received["context"]["repos"][0]["state"], "ready")
        repo_entry.chmod(0o644)
        denied = self.call("archive", task, "--note", "bad hook", ok=False)
        self.assertIn("executable regular file", denied["error"])
        self.assertTrue(path.exists())
        repo_entry.unlink()
        self.call("archive", task, "--note", "optional repo hook absent")
        self.assertFalse(path.parent.exists())

    def test_project_archive_bad_entry_and_hook_config_validation(self):
        task = self.task()
        self.clean_task(task)
        entry = self.root / ".local/hooks/before_task_archive"
        entry.symlink_to(self.root / "missing-hook")
        denied = self.call("archive", task, "--note", "bad link", ok=False)
        self.assertIn("symlinked path is not allowed", denied["error"])
        self.assertTrue(Path(self.store.read(task)["workspace"]).exists())
        entry.unlink()
        entry.write_text("#!/bin/sh\nexit 0\n")
        denied = self.call("archive", task, "--note", "bad mode", ok=False)
        self.assertIn("executable regular file", denied["error"])
        entry.unlink()
        config_path = self.projects / ".mam/env.json"
        config = json.loads(config_path.read_text())
        for invalid in (0, -1, True, "60", float("inf")):
            config["HOOK_TIMEOUTS"] = {"before_task_archive": invalid}
            config_path.write_text(json.dumps(config))
            with self.subTest(invalid=invalid), self.assertRaisesRegex(cli.Error, "positive finite"):
                cli.project_config(self.projects)

    def test_archive_hook_runs_after_guards_and_rechecks_git_status(self):
        task = self.task()
        path = Path(self.add(task)["path"])
        entry = self.root / ".local/hooks/before_task_archive"
        marker = self.projects / "archive-hook-called"
        entry.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
        entry.chmod(0o755)
        data = self.store.read(task)
        data["jobs"].append({"id": "pending-job", "status": "running", "note": "test"})
        self.store.write(data)
        denied = self.call("archive", task, "--note", "job pending", ok=False)
        self.assertIn("unarchived registered jobs", denied["error"])
        self.assertFalse(marker.exists())
        data["jobs"][0]["status"] = "archived"
        self.store.write(data)
        self.publish(task)
        self.report(task)
        self.store.doc(task, "task").write_text("unpublished change")
        denied = self.call("archive", task, "--note", "draft pending", ok=False)
        self.assertIn("uncommitted Git changes", denied["error"])
        self.assertFalse(marker.exists())
        self.store.doc(task, "task").write_text("# test task\n")
        entry.write_text("""#!/usr/bin/env python3
import json
from pathlib import Path
import sys
context = json.load(sys.stdin)
Path(context['task']['task_dir'], 'task.md').write_text('changed during hook')
""")
        denied = self.call("archive", task, "--note", "hook changed task", ok=False)
        self.assertIn("uncommitted Git changes", denied["error"])
        self.assertTrue(path.exists())
        self.assertTrue(cli.branch_exists(self.root, f"task/{task}"))

    def test_archive_hook_reruns_after_partial_git_cleanup(self):
        second = self.source("second-repo")
        task = self.task()
        first_path = Path(self.add(task)["path"])
        second_path = Path(self.add(task, "second-repo")["path"])
        entry = self.root / ".local/hooks/before_task_archive"
        calls = self.projects / "archive-hook-calls"
        entry.write_text(f"#!/bin/sh\nprintf x >> {shlex.quote(str(calls))}\n")
        entry.chmod(0o755)
        self.clean_task(task)
        self.git(second, "worktree", "lock", str(second_path))
        denied = self.call("archive", task, "--note", "first pass", ok=False)
        self.assertIn("archive incomplete", denied["error"])
        self.assertEqual(calls.read_text(), "x")
        self.assertFalse(first_path.exists())
        self.assertTrue(second_path.exists())
        (second_path.parent / "unknown").write_text("discard on retry")
        self.git(second, "worktree", "unlock", str(second_path))
        self.call("archive", task, "--note", "second pass")
        self.assertEqual(calls.read_text(), "xx")
        self.assertFalse(second_path.parent.exists())

    def test_task_block_requires_manager_and_pending_status(self):
        task, manager = self.task_with_manager()
        args = types.SimpleNamespace(task=task, note="waiting on decision")
        with patch.object(cli, "caller_agent", return_value=manager), \
             patch.object(cli, "caller_identity", return_value=identity.ThreadIdentity(manager, "/root", manager)), \
             patch.object(wake_runtime, "resolve_manager", return_value=manager):
            result = cli.task_block(self.store, args)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["block_note"], "waiting on decision")
        data = self.store.read(task)
        self.assertEqual(data["wake_reminder_count"], 0)
        data["status"] = "pending"
        data["agent"] = "worker"
        self.store.write(data)
        with patch.object(cli, "caller_agent", return_value=manager), \
             patch.object(cli, "caller_identity", return_value=identity.ThreadIdentity(manager, "/root", manager)), \
             patch.object(wake_runtime, "resolve_manager", return_value=manager), \
             patch.object(cli, "agent_observations", return_value={"worker": {"status": "unknown"}}), \
             self.assertRaisesRegex(cli.Error, "requires a confirmed idle executor"):
            cli.task_block(self.store, args)
        self.assertEqual(self.store.read(task)["status"], "pending")
        with patch.object(cli, "caller_agent", return_value=manager), \
             patch.object(cli, "caller_identity", return_value=identity.ThreadIdentity(manager, "/root", manager)), \
             patch.object(wake_runtime, "resolve_manager", return_value=manager), \
             patch.object(cli, "agent_observations", return_value={"worker": {"status": "notLoaded"}}):
            allowed = cli.task_block(self.store, args)
        self.assertEqual(allowed["status"], "blocked")
        data = self.store.read(task)
        data["status"] = "pending"
        self.store.write(data)
        with patch.object(cli, "caller_agent", return_value=manager), \
             patch.object(cli, "caller_identity", return_value=identity.ThreadIdentity(manager, "/root", manager)), \
             patch.object(wake_runtime, "resolve_manager", return_value=manager), \
             patch.object(cli, "agent_observations", return_value={"worker": {"status": "notLoaded", "error": "systemError"}}), \
             self.assertRaisesRegex(cli.Error, "requires a confirmed idle executor"):
            cli.task_block(self.store, args)
        data["status"] = "working"
        self.store.write(data)
        with patch.object(cli, "caller_agent", return_value=manager), \
             patch.object(cli, "caller_identity", return_value=identity.ThreadIdentity(manager, "/root", manager)), \
             patch.object(wake_runtime, "resolve_manager", return_value=manager), \
             patch.object(cli, "agent_observations", return_value={"worker": {"status": "unknown"}}), \
             self.assertRaisesRegex(cli.Error, "requires a pending task"):
            cli.task_block(self.store, args)

    def test_task_block_rejects_non_manager(self):
        task, manager = self.task_with_manager()
        args = types.SimpleNamespace(task=task, note="waiting")
        with patch.object(cli, "caller_agent", return_value=str(uuid.uuid4())), \
             patch.object(wake_runtime, "resolve_manager", return_value=manager), \
             self.assertRaisesRegex(cli.Error, "recorded Manager"):
            cli.task_block(self.store, args)

    def test_task_list_and_status_refresh_task_lifecycle(self):
        task = self.task()
        agent = str(uuid.uuid4())
        self.fixture_bind(task, agent)
        observations = {agent: {"status": "active"}}
        with patch.object(cli, "agent_observations", side_effect=lambda _: observations):
            result = cli.task_list(self.store, types.SimpleNamespace(all=True, archived=False))
        saved = self.store.read(task)
        self.assertEqual(saved["status"], "working")
        self.assertEqual(result[0]["status"], "working")
        saved["wake_reminder_count"] = 2
        self.store.write(saved)
        with patch.object(cli, "agent_observations", side_effect=lambda _: {agent: {"status": "idle"}}):
            current = cli.status(self.store, types.SimpleNamespace(task=task))
        self.assertEqual(current["status"], "pending")
        self.assertEqual(current["wake_reminder_count"], 0)
        saved = self.store.read(task)
        saved["status"] = "blocked"
        saved["block_note"] = "waiting"
        saved["wake_reminder_count"] = 1
        self.store.write(saved)
        with patch.object(cli, "agent_observations", side_effect=lambda _: {agent: {"status": "unknown"}}):
            current = cli.status(self.store, types.SimpleNamespace(task=task))
        self.assertEqual(current["status"], "blocked")
        self.assertEqual(current["block_note"], "waiting")
        self.assertEqual(current["wake_reminder_count"], 1)
        with patch.object(cli, "agent_observations", side_effect=lambda _: {agent: {"status": "active"}}):
            current = cli.status(self.store, types.SimpleNamespace(task=task))
        self.assertEqual(current["status"], "working")
        self.assertEqual(current["wake_reminder_count"], 0)

    def test_task_state_refresh_and_reminder_accounting(self):
        legacy = {"status": "working", "agent": "worker", "jobs": []}
        self.assertEqual(task_state.reminder_count(legacy), 0)
        legacy, accepted = task_state.record_reminder(legacy, "working")
        self.assertTrue(accepted)
        self.assertEqual(task_state.reminder_count(legacy), 1)

        base = {"status": "pending", "agent": "worker", "jobs": [], "wake_reminder_count": 2}
        unknown, old, new = task_state.refresh_state(base, {"status": "unknown"})
        self.assertEqual((old, new, unknown["status"]), ("pending", "pending", "pending"))
        self.assertEqual(unknown["wake_reminder_count"], 2)
        not_loaded, _, _ = task_state.refresh_state(
            {"status": "working", "agent": "worker", "jobs": [], "wake_reminder_count": 1},
            {"status": "notLoaded"},
        )
        self.assertEqual((not_loaded["status"], not_loaded["wake_reminder_count"]), ("pending", 0))
        failed_probe, _, _ = task_state.refresh_state(
            {"status": "working", "agent": "worker", "jobs": [], "wake_reminder_count": 1},
            {"status": "notLoaded", "error": "systemError"},
        )
        self.assertEqual((failed_probe["status"], failed_probe["wake_reminder_count"]), ("working", 1))
        resumed, _, _ = task_state.refresh_state(
            {"status": "blocked", "agent": "worker", "jobs": [], "wake_reminder_count": 2},
            {"status": "active"},
        )
        self.assertEqual((resumed["status"], resumed["wake_reminder_count"]), ("working", 0))
        active, _, _ = task_state.refresh_state(unknown, {"status": "active"})
        self.assertEqual(active["status"], "working")
        self.assertEqual(active["wake_reminder_count"], 0)
        for expected in ("working", "working", "working"):
            active, accepted = task_state.record_reminder(active, expected)
            self.assertTrue(accepted)
        active, accepted = task_state.record_reminder(active, "working")
        self.assertFalse(accepted)
        self.assertEqual(task_state.reminder_count(active), 3)
        self.assertEqual(task_state.refresh_state(active, {"status": "active"})[0]["wake_reminder_count"], 3)
        with_job = {"status": "pending", "agent": None, "jobs": [{"status": "exited"}]}
        self.assertEqual(task_state.refresh_state(with_job, None)[0]["status"], "working")
        archived = {"status": "archived", "agent": "worker", "jobs": [{"status": "running"}]}
        self.assertEqual(task_state.refresh_state(archived, {"status": "active"})[0]["status"], "archived")

    def test_report_refuses_unarchived_jobs(self):
        task = self.task()
        data = self.store.read(task)
        data["jobs"] = [{"id": "unknown-job", "status": "unknown"}]
        self.store.write(data)
        self.store.doc(task, "report").write_text("Results are ready.\n")
        denied = self.call("report", task, ok=False)
        self.assertIn("unarchived registered jobs: unknown-job", denied["error"])
        self.assertEqual(self.store.read(task)["status"], "working")


if __name__ == "__main__":
    unittest.main()
