from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ws.py"


class WorkspaceLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="ws lifecycle test ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / "Projects"
        self.root = self.base / "workspace"
        self.root.mkdir(parents=True)
        self.source = self.base / "source repo"
        self.source.mkdir()
        self.git("init", cwd=self.source)
        self.git("config", "user.email", "test@example.invalid", cwd=self.source)
        self.git("config", "user.name", "Test User", cwd=self.source)
        (self.source / "README.md").write_text("base\n", encoding="utf-8")
        (self.source / ".gitignore").write_text(".venv/\ntemp/\n", encoding="utf-8")
        self.git("add", ".", cwd=self.source)
        self.git("commit", "-m", "base", cwd=self.source)
        self.workspace = self.root / "task with spaces"
        self.workspace.mkdir()
        self.worktree = self.workspace / "repo with spaces"
        self.git("worktree", "add", "-b", "test/lifecycle", str(self.worktree), cwd=self.source)
        self.state = Path(self.temp.name) / "manager state"
        self.task = "lifecycle-test"

    def git(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)

    def ws(self, *args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--state-dir", str(self.state), *args],
            cwd=self.source,
            text=True,
            capture_output=True,
        )
        if ok and result.returncode:
            self.fail(f"ws {' '.join(args)} failed:\n{result.stderr}\n{result.stdout}")
        if not ok:
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        return result

    def register(self) -> None:
        self.ws(
            "register", self.task, "--owner", "agent-a", "--workspace-root", str(self.root),
            "--workspace", str(self.workspace), "--repo", str(self.worktree),
        )

    def delivered_commit(self) -> str:
        return self.git("rev-parse", "HEAD", cwd=self.worktree).stdout.strip()

    def deliver_and_accept(self) -> None:
        self.ws("deliver", self.task, "--by", "agent-a")
        self.ws("accept", self.task, "--manager", "manager", "--commit", f"{self.worktree.name}={self.delivered_commit()}")

    def close(self, ok: bool = True) -> subprocess.CompletedProcess[str]:
        return self.ws("close", self.task, "--workspace-root", str(self.root), ok=ok)

    def test_close_allows_ignored_and_preserves_symlink_target(self) -> None:
        self.register()
        self.deliver_and_accept()
        shared = Path(self.temp.name) / "shared entity"
        shared.mkdir()
        marker = shared / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        with (self.source / ".git" / "info" / "exclude").open("a", encoding="utf-8") as handle:
            handle.write("data\n")
        (self.worktree / "data").symlink_to(shared, target_is_directory=True)
        (self.worktree / ".venv").mkdir()
        (self.worktree / ".venv" / "shared").symlink_to(shared, target_is_directory=True)
        (self.worktree / "temp").mkdir()
        (self.worktree / "temp" / "cache.txt").write_text("cache", encoding="utf-8")
        self.close()
        self.assertFalse(self.workspace.exists())
        self.assertTrue(marker.exists())
        self.git("show-ref", "--verify", "refs/heads/test/lifecycle", cwd=self.source)
        self.assertFalse((self.state / f"{self.task}.json").exists())

    def test_close_refuses_pending_acceptance(self) -> None:
        self.register()
        self.ws("deliver", self.task, "--by", "agent-a")
        result = self.close(ok=False)
        self.assertIn("pending manager acceptance", result.stderr)
        self.assertTrue(self.worktree.exists())

    def test_close_refuses_active_job_until_manually_finished(self) -> None:
        self.register()
        self.deliver_and_accept()
        self.ws("job", "start", self.task, "train", "--pin", "host-a:process-42")
        result = self.close(ok=False)
        self.assertIn("active job pins", result.stderr)
        self.assertTrue(self.worktree.exists())
        self.ws("job", "finish", self.task, "train", "--by", "agent-a")
        self.close()

    def test_dirty_and_untracked_protect_then_retry(self) -> None:
        self.register()
        self.deliver_and_accept()
        (self.worktree / "README.md").write_text("changed\n", encoding="utf-8")
        useful = self.worktree / "useful.py"
        useful.write_text("print('keep')\n", encoding="utf-8")
        result = self.close(ok=False)
        self.assertIn("tracked changes", result.stderr)
        self.assertIn("untracked files", result.stderr)
        self.assertTrue(self.worktree.exists(), "preflight must not remove another worktree before failure")
        self.git("restore", "README.md", cwd=self.worktree)
        useful.unlink()
        self.close()
        self.assertFalse(self.workspace.exists())

    def test_close_rejects_physical_ignored_data(self) -> None:
        self.register()
        self.deliver_and_accept()
        with (self.source / ".git" / "info" / "exclude").open("a", encoding="utf-8") as handle:
            handle.write("data\n")
        data = self.worktree / "data"
        data.mkdir()
        (data / "checkpoint.bin").write_text("keep", encoding="utf-8")
        result = self.close(ok=False)
        self.assertIn("unrecognized ignored paths", result.stderr)
        self.assertTrue((data / "checkpoint.bin").exists())

    def test_register_rejects_workspace_registered_by_another_task(self) -> None:
        self.register()
        result = self.ws(
            "register", "other-task", "--owner", "agent-b", "--workspace-root", str(self.root),
            "--workspace", str(self.workspace), "--repo", str(self.worktree), ok=False,
        )
        self.assertIn("workspace is already registered", result.stderr)
        self.assertFalse((self.state / "other-task.json").exists())

    def test_register_rejects_symlinked_workspace_root(self) -> None:
        linked_root = Path(self.temp.name) / "linked workspace"
        linked_root.symlink_to(self.root, target_is_directory=True)
        result = self.ws(
            "register", self.task, "--owner", "agent-a", "--workspace-root", str(linked_root),
            "--workspace", str(self.workspace), "--repo", str(self.worktree), ok=False,
        )
        self.assertIn("workspace root", result.stderr)
        self.assertFalse((self.state / f"{self.task}.json").exists())


if __name__ == "__main__":
    unittest.main()
