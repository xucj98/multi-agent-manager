from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


MANAGER = "01a081fe-d6c2-74f2-a73d-68584e9d915b"


class InstallerScriptTests(unittest.TestCase):
    source_root = Path(__file__).resolve().parents[1]

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.primary = self.project / "mam-state"
        self.primary.mkdir()
        self._write_checkout_files(self.primary)
        self._git("init", self.primary)
        self._git("config", self.primary, "user.email", "tests@example.invalid")
        self._git("config", self.primary, "user.name", "MAM tests")
        self._git("add", self.primary, ".")
        self._git("commit", self.primary, "-m", "fixture")
        self.checkout = self.project / "installer-checkout"
        self._git("worktree", self.primary, "add", "-b", "fixture-installer", str(self.checkout), "HEAD")
        self.archive = self.root / "candidate.tar.gz"
        subprocess.run(["tar", "-czf", str(self.archive), "-C", str(self.checkout), "."], check=True)
        branch = subprocess.check_output(["git", "-C", str(self.primary), "branch", "--show-current"], text=True).strip()
        (self.project / ".mam").mkdir()
        (self.project / ".mam" / "env.json").write_text(
            json.dumps({"MAM_ROOT": str(self.primary), "PROJECT_ROOT": str(self.project), "MAM_BRANCH": branch}),
            encoding="utf-8",
        )
        self.home = self.root / "home"
        self.home.mkdir()
        (self.home / ".bashrc").write_text(
            "export KEEP_THIS=1\n"
            "# >>> MAM Codex App Server trace >>>\n"
            "if [[ \":$PATH:\" != *\":$HOME/.local/bin:\"* ]]; then\n"
            "    export PATH=\"$HOME/.local/bin:$PATH\"\n"
            "fi\n"
            "export RUST_LOG=\"off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info\"\n"
            "export LOG_FORMAT=json\n"
            "# <<< MAM Codex App Server trace <<<\n"
            "[[ -z \"$PS1\" ]] && return\n"
            "export AFTER_RETURN=1\n",
            encoding="utf-8",
        )
        (self.home / ".profile").write_text("export LOGIN_KEEP=1\n", encoding="utf-8")
        self.pipx_home = self.home / "pipx"
        self.venv = self.pipx_home / "venvs" / "multi-agent-manager"
        subprocess.run([sys.executable, "-m", "venv", str(self.venv)], check=True)
        installed_python = self.venv / "bin" / "python"
        site_packages = Path(
            subprocess.check_output([str(installed_python), "-c", "import site; print(site.getsitepackages()[0])"], text=True).strip()
        )
        os.symlink(self.checkout / "multi_agent_manager", site_packages / "multi_agent_manager")
        self.fake_bin = self.root / "fake-bin"
        self.fake_bin.mkdir()
        self.log = self.root / "commands.log"
        self.state = self.root / "service-state"
        self.state.write_text("stopped\n", encoding="utf-8")
        self._write_fake_mam()
        self._write_fake_pipx()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _git(*arguments: str | Path) -> None:
        if arguments[0] == "init":
            _, repository = arguments
            subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
            return
        command, repository, *rest = arguments
        subprocess.run(["git", "-C", str(repository), str(command), *(str(item) for item in rest)], check=True, stdout=subprocess.DEVNULL)

    def _write_checkout_files(self, root: Path) -> None:
        (root / "scripts").mkdir()
        (root / "multi_agent_manager").mkdir()
        (root / "tests").mkdir()
        for relative in (
            "scripts/install.sh",
            "multi_agent_manager/__init__.py",
            "multi_agent_manager/release.py",
            "multi_agent_manager/job_runtime.py",
            "multi_agent_manager/wake_compat.py",
            "multi_agent_manager/liveprobe.py",
            "multi_agent_manager/wake_runtime.py",
            "multi_agent_manager/cli.py",
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative == "multi_agent_manager/release.py":
                target.write_text(
                    'RELEASE_VERSION = "0.2.0"\n'
                    'RELEASE_TAG = "v0.2.0"\n'
                    'RELEASE_COMMIT = "' + "a" * 40 + '"\n',
                    encoding="utf-8",
                )
            else:
                shutil.copy2(self.source_root / relative, target)
        (root / "pyproject.toml").write_text(
            "[project]\nname = 'multi-agent-manager'\nversion = '0.2.0'\n", encoding="utf-8"
        )
        # Git does not retain an empty directory, while the installer requires
        # a tests directory before it will run its suite.
        (root / "tests" / "test_placeholder.py").write_text("# fixture\n", encoding="utf-8")

    def _write_fake_mam(self) -> None:
        self.fake_mam = self.root / "fake-mam"
        self.fake_mam.write_text(
            r'''#!/usr/bin/env bash
set -euo pipefail
{
    printf 'cwd=%s thread=%s args=' "$PWD" "${CODEX_THREAD_ID:-}"
    printf '%s ' "$@"
    printf '\n'
} >> "$FAKE_LOG"
if [[ "${1:-}" == --help ]]; then
    exit 0
fi
if [[ "${1:-}" != service ]]; then
    exit 64
fi
if [[ "$PWD" != "$FAKE_EXPECT_PROJECT" ]]; then
    printf 'wrong project context\n' >&2
    exit 65
fi
if [[ -n "${CODEX_THREAD_ID:-}" ]]; then
    printf 'installer thread leaked into service command\n' >&2
    exit 66
fi
state="$(cat "$FAKE_STATE")"
emit_status() {
    case "$1" in
        stopped)
            printf '%s\n' '{"running":false,"healthy":false,"manager":null,"pending":{"count":0,"events":[]},"status":"disabled"}'
            ;;
        healthy)
            printf '{"running":true,"healthy":true,"manager":"%s","pending":{"count":0,"events":[]},"status":"healthy"}\n' "$FAKE_MANAGER"
            ;;
        awaiting_manager)
            printf '%s\n' '{"running":true,"healthy":true,"manager":null,"pending":{"count":0,"events":[]},"status":"awaiting_manager"}'
            ;;
        missing_manager)
            printf '%s\n' '{"running":false,"healthy":false,"manager":null,"pending":{"count":0,"events":[]},"status":"error","error":"existing bound tasks have no determinable Manager; run mam service start --manager AGENT-ID"}'
            ;;
        invalid)
            printf '%s\n' 'not-json'
            ;;
        *)
            printf '%s\n' '{"running":false,"healthy":false,"manager":null,"pending":{"count":0,"events":[]},"status":"error","error":"launcher path missing; TOKEN=do-not-log"}'
            ;;
    esac
}
case "${2:-}" in
    status)
        emit_status "$state"
        ;;
    stop)
        if [[ "$state" != healthy && "$state" != awaiting_manager ]]; then
            printf 'stop requested without a running service\n' >&2
            exit 67
        fi
        printf 'stopped\n' > "$FAKE_STATE"
        emit_status stopped
        ;;
    start)
        if [[ "${FAKE_START_FAIL:-}" == 1 ]]; then
            printf 'launcher path missing; TOKEN=do-not-log\n' >&2
            exit 68
        fi
        if [[ "$state" != stopped ]]; then
            printf 'duplicate service start\n' >&2
            exit 69
        fi
        printf '%s\n' "${FAKE_START_STATE:-healthy}" > "$FAKE_STATE"
        emit_status "${FAKE_START_STATE:-healthy}"
        ;;
    *)
        exit 64
        ;;
esac
''',
            encoding="utf-8",
        )
        self.fake_mam.chmod(0o755)

    def _write_fake_pipx(self) -> None:
        path = self.fake_bin / "pipx"
        path.write_text(
            r'''#!/usr/bin/env bash
set -euo pipefail
printf 'pipx args=' >> "$FAKE_LOG"
printf '%s ' "$@" >> "$FAKE_LOG"
printf '\n' >> "$FAKE_LOG"
if [[ "${1:-}" == environment && "${2:-}" == --value && "${3:-}" == PIPX_HOME ]]; then
    printf '%s\n' "$PIPX_HOME"
    exit 0
fi
if [[ "${1:-}" == install ]]; then
    if [[ "${FAKE_PIPX_FAIL:-}" == 1 ]]; then
        printf 'simulated pipx failure\n' >&2
        exit 71
    fi
    mkdir -p "$PIPX_BIN_DIR"
    cp "$FAKE_MAM" "$PIPX_BIN_DIR/mam"
    chmod 755 "$PIPX_BIN_DIR/mam"
    exit 0
fi
exit 72
''',
            encoding="utf-8",
        )
        path.chmod(0o755)

    @staticmethod
    def _probe_stubs() -> str:
        return r'''
run_lightweight_probe() {
    printf 'lightweight python=%s\n' "$INSTALLED_PYTHON" >> "$FAKE_LOG"
    if [[ "${FAKE_LIGHTWEIGHT_FAIL:-}" == 1 ]]; then
        incomplete 'simulated App Server API compatibility failure'
        return 1
    fi
    COMPATIBILITY_JSON="$INSTALL_TMP/compatibility.json"
    printf '%s\n' '{"socket_path":"/tmp/fake-app-server.sock","capabilities":{"model_requests":0},"diagnostics":{}}' > "$COMPATIBILITY_JSON"
    printf 'MAM proactive wakeup: non-model App Server API compatibility PASS\n'
}
run_live_delivery_probe() {
    printf 'liveprobe python=%s\n' "$INSTALLED_PYTHON" >> "$FAKE_LOG"
    if [[ "${FAKE_LIVEPROBE_FAIL:-}" == 1 ]]; then
        incomplete 'simulated isolated delivery failure'
        return 1
    fi
    printf 'MAM proactive wakeup: isolated real delivery PASS\n'
}
'''

    def _fixture_environment(self, overrides: dict[str, str]) -> dict[str, str]:
        environment = dict(os.environ)
        # Test defaults must not inherit the real installer's optional Manager
        # selection.  Individual tests supply it explicitly when exercising
        # the final service-start path.
        environment.pop("MAM_SERVICE_MANAGER", None)
        environment.update({
            "HOME": str(self.home),
            "PIPX_HOME": str(self.pipx_home),
            "PATH": f"{self.fake_bin}:{os.environ['PATH']}",
            "FAKE_LOG": str(self.log),
            "FAKE_STATE": str(self.state),
            "FAKE_MAM": str(self.fake_mam),
            "FAKE_EXPECT_PROJECT": str(self.project),
            "FAKE_MANAGER": MANAGER,
            "MAM_INSTALL_ARCHIVE": str(self.archive),
        })
        environment.update(overrides)
        return environment

    def run_installer(self, *, probe_stubs: bool = True, **overrides: str) -> subprocess.CompletedProcess[str]:
        environment = self._fixture_environment(overrides)
        command = 'source "$1"\nrun_tests() { :; }\n'
        if probe_stubs:
            command += self._probe_stubs()
        command += "main\n"
        return subprocess.run(
            ["bash", "-c", command, "bash", str(self.checkout / "scripts" / "install.sh")],
            cwd=self.checkout,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def run_checkout_tests(self, **overrides: str) -> subprocess.CompletedProcess[str]:
        """Run the installer's pre-pipx test phase against the fixture checkout."""

        environment = self._fixture_environment(overrides)
        command = 'source "$1"\nCHECKOUT_ROOT="$2"\nchoose_source_python\nrun_tests\n'
        return subprocess.run(
            ["bash", "-c", command, "bash", str(self.checkout / "scripts" / "install.sh"), str(self.checkout)],
            cwd=self.checkout,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def service_commands(self) -> list[str]:
        if not self.log.exists():
            return []
        return [
            line.partition("args=")[2].strip()
            for line in self.log.read_text().splitlines()
            if line.startswith("cwd=") and "args=service " in line
        ]

    def test_installer_fixture_does_not_inherit_manager_control_value(self):
        with mock.patch.dict(os.environ, {"MAM_SERVICE_MANAGER": MANAGER}):
            result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.service_commands(), [])

    def test_checkout_tests_remove_manager_control_value(self):
        (self.checkout / "tests" / "test_manager_environment.py").write_text(
            "import os\n"
            "import unittest\n"
            "\n"
            "class ManagerEnvironmentTests(unittest.TestCase):\n"
            "    def test_manager_selection_is_not_a_test_input(self):\n"
            "        self.assertNotIn('MAM_SERVICE_MANAGER', os.environ)\n",
            encoding="utf-8",
        )
        result = self.run_checkout_tests(MAM_SERVICE_MANAGER=MANAGER)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_install_upgrade_failure_does_not_touch_probes_or_scheduler(self):
        result = self.run_installer(FAKE_PIPX_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pipx could not install", result.stdout)
        self.assertEqual(self.service_commands(), [])
        self.assertNotIn("liveprobe", self.log.read_text())

    def test_release_metadata_must_match_requested_version(self):
        (self.checkout / "multi_agent_manager" / "release.py").write_text(
            'RELEASE_VERSION = "0.1.0"\nRELEASE_TAG = "v0.1.0"\nRELEASE_COMMIT = "' + "a" * 40 + '"\n',
            encoding="utf-8",
        )
        subprocess.run(["tar", "-czf", str(self.archive), "-C", str(self.checkout), "."], check=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release metadata does not match requested version", result.stdout)
        self.assertEqual(self.service_commands(), [])

    def test_pyproject_version_must_match_requested_version(self):
        (self.checkout / "pyproject.toml").write_text(
            "[project]\nname = 'multi-agent-manager'\nversion = '0.1.0'\n", encoding="utf-8"
        )
        subprocess.run(["tar", "-czf", str(self.archive), "-C", str(self.checkout), "."], check=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release metadata does not match requested version", result.stdout)
        self.assertEqual(self.service_commands(), [])

    def test_archive_release_commit_placeholder_is_rejected(self):
        (self.checkout / "multi_agent_manager" / "release.py").write_text(
            'RELEASE_VERSION = "0.2.0"\nRELEASE_TAG = "v0.2.0"\nRELEASE_COMMIT = "$Format:%H$"\n',
            encoding="utf-8",
        )
        subprocess.run(["tar", "-czf", str(self.archive), "-C", str(self.checkout), "."], check=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release metadata does not match requested version", result.stdout)
        self.assertEqual(self.service_commands(), [])

    def test_same_repository_sibling_checkout_is_installed_and_path_persists(self):
        self.assertNotEqual(self.primary, self.checkout)
        original_bashrc = (self.home / ".bashrc").read_text()
        trace_begin = "# >>> MAM Codex App Server trace >>>"
        trace_end = "# <<< MAM Codex App Server trace <<<"
        legacy_trace = original_bashrc[original_bashrc.index(trace_begin) : original_bashrc.index(trace_end) + len(trace_end)]
        result = self.run_installer(CODEX_THREAD_ID="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("service start is a separate command", result.stdout)
        log = self.log.read_text()
        self.assertIn("pipx args=install --force", log)
        self.assertIn(f"lightweight python={self.venv / 'bin' / 'python'}", log)
        self.assertIn(f"liveprobe python={self.venv / 'bin' / 'python'}", log)
        self.assertNotIn("wait python", log)
        self.assertLess(log.index("lightweight"), log.index("liveprobe"))
        self.assertEqual(self.service_commands(), [])
        self.assertNotIn("aaaaaaaa", log)
        bashrc = (self.home / ".bashrc").read_text()
        self.assertIn("export KEEP_THIS=1", bashrc)
        self.assertIn("export AFTER_RETURN=1", bashrc)
        self.assertIn(legacy_trace, bashrc)
        self.assertEqual(bashrc.count(trace_begin), 1)
        self.assertEqual(bashrc.count("# >>> MAM PATH >>>"), 0)
        self.assertFalse(list(self.home.glob(".bashrc.mam-path.*.bak")))
        interactive = subprocess.run(
            ["bash", "--noprofile", "--rcfile", str(self.home / ".bashrc"), "-ic", "command -v mam"],
            env={**os.environ, "HOME": str(self.home), "PATH": "/usr/bin:/bin"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        # The installer does not promise to edit shell startup files; a
        # caller-supplied shell may still have its own PATH setup.
        self.assertEqual((self.home / ".bashrc").read_text(), original_bashrc)
        login = subprocess.run(
            ["bash", "--norc", "-lc", "command -v mam"],
            env={**os.environ, "HOME": str(self.home), "PATH": "/usr/bin:/bin"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual((self.home / ".profile").read_text(), "export LOGIN_KEEP=1\n")
        again = self.run_installer()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual((self.home / ".bashrc").read_text().count("# >>> MAM PATH >>>"), 0)
        self.assertIn(legacy_trace, (self.home / ".bashrc").read_text())

    def test_fresh_shell_startup_does_not_add_trace_configuration(self):
        bashrc = self.home / ".bashrc"
        bashrc.write_text('export KEEP_THIS=1\n[[ -z "$PS1" ]] && return\n', encoding="utf-8")
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        content = bashrc.read_text()
        self.assertNotIn("MAM Codex App Server trace", content)
        self.assertNotIn("export RUST_LOG=", content)
        self.assertNotIn("export LOG_FORMAT=", content)
        self.assertEqual(content.count("# >>> MAM PATH >>>"), 0)

    def test_checkout_test_environment_reaches_current_source_in_detached_daemon(self):
        """A fresh checkout must outrank an older package for the daemon child.

        The test interpreter deliberately has an old ``multi_agent_manager``
        in its site-packages.  The checkout has no editable environment.  The
        fixture test starts the real detached fresh-project daemon, whose cwd
        is the separate MAM state root just like ``_spawn_service`` uses.
        """

        self.assertFalse((self.checkout / ".venv").exists())
        source_environment = self.root / "old-installed-python"
        subprocess.run([sys.executable, "-m", "venv", str(source_environment)], check=True)
        source_python = source_environment / "bin" / "python"
        site_packages = Path(
            subprocess.check_output([str(source_python), "-c", "import site; print(site.getsitepackages()[0])"], text=True).strip()
        )
        stale_package = site_packages / "multi_agent_manager"
        stale_package.mkdir()
        (stale_package / "__init__.py").write_text('"""Old installed package fixture."""\n', encoding="utf-8")
        stale_marker = self.root / "old-package-daemon-ran"
        (stale_package / "wake_runtime.py").write_text(
            "from pathlib import Path\n"
            "import os\n"
            "Path(os.environ['MAM_STALE_DAEMON_MARKER']).write_text('old package ran\\n', encoding='utf-8')\n"
            "raise SystemExit(91)\n",
            encoding="utf-8",
        )
        daemon_root = self.root / "daemon-state"
        daemon_projects = self.root / "daemon-projects"
        daemon_root.mkdir()
        daemon_projects.mkdir()
        (self.checkout / "tests" / "test_detached_source_import.py").write_text(
            "from pathlib import Path\n"
            "import os\n"
            "import time\n"
            "import unittest\n"
            "\n"
            "from multi_agent_manager import cli, job_runtime, wake_runtime\n"
            "\n"
            "\n"
            "class DetachedSourceImportTests(unittest.TestCase):\n"
            "    def test_daemon_uses_checkout_runtime_after_cwd_changes(self):\n"
            "        checkout = Path(os.environ['MAM_CHECKOUT_ROOT']).resolve()\n"
            "        self.assertEqual(Path(wake_runtime.__file__).resolve(), checkout / 'multi_agent_manager' / 'wake_runtime.py')\n"
            "        config = cli.ProjectConfig(Path(os.environ['MAM_TEST_DAEMON_ROOT']), Path(os.environ['MAM_TEST_DAEMON_PROJECTS']), 'project/daemon')\n"
            "        store = cli.Store(config)\n"
            "        started = False\n"
            "        try:\n"
            "            result = wake_runtime.start_service(config)\n"
            "            started = True\n"
            "            self.assertEqual(result['status'], 'awaiting_manager')\n"
            "            self.assertTrue(result['healthy'])\n"
            "            self.assertFalse(Path(os.environ['MAM_STALE_DAEMON_MARKER']).exists())\n"
            "        finally:\n"
            "            if started:\n"
            "                wake_runtime.stop_service(config)\n"
            "                deadline = time.monotonic() + 5.0\n"
            "                while time.monotonic() < deadline:\n"
            "                    state = wake_runtime._load_state(store)\n"
            "                    observed = job_runtime.probe_process('local', state['pid'], state['identity'])\n"
            "                    if observed['status'] == 'exited':\n"
            "                        break\n"
            "                    time.sleep(0.05)\n"
            "                else:\n"
            "                    self.fail('fresh detached daemon did not stop')\n",
            encoding="utf-8",
        )
        result = self.run_checkout_tests(
            PATH=f"{source_python.parent}:{self.fake_bin}:{os.environ['PATH']}",
            PYTHONPATH="",
            MAM_CHECKOUT_ROOT=str(self.checkout),
            MAM_TEST_DAEMON_ROOT=str(daemon_root),
            MAM_TEST_DAEMON_PROJECTS=str(daemon_projects),
            MAM_STALE_DAEMON_MARKER=str(stale_marker),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(stale_marker.exists())

    def test_existing_service_requires_live_app_server_before_service_status(self):
        missing = self.root / "missing.sock"
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer(probe_stubs=False, MAM_APP_SERVER_SOCKET=str(missing), FAKE_START_STATE="awaiting_manager")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("App Server API compatibility probe failed", result.stdout + result.stderr)
        self.assertEqual(self.service_commands(), [])
        self.assertEqual(self.state.read_text().strip(), "healthy")

    def test_lightweight_compatibility_failure_keeps_existing_scheduler_running(self):
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer(FAKE_LIGHTWEIGHT_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated App Server API compatibility failure", result.stdout)
        log = self.log.read_text()
        self.assertIn("lightweight", log)
        self.assertNotIn("liveprobe", log)
        self.assertEqual(self.service_commands(), [])
        self.assertEqual(self.state.read_text().strip(), "healthy")

    def test_live_delivery_failure_happens_before_existing_scheduler_stop(self):
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer(FAKE_LIVEPROBE_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated isolated delivery failure", result.stdout)
        self.assertEqual(self.service_commands(), [])
        self.assertEqual(self.state.read_text().strip(), "healthy")

    def test_upgrade_stops_then_restarts_only_the_existing_project_singleton(self):
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.service_commands(), [])
        self.assertEqual(self.state.read_text().strip(), "healthy")

    def test_fresh_bootstrap_is_awaiting_manager_without_capturing_installer_thread(self):
        result = self.run_installer(
            CODEX_THREAD_ID="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", FAKE_START_STATE="awaiting_manager"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("service start is a separate command", result.stdout)
        self.assertEqual(self.service_commands(), [])
        self.assertNotIn("aaaaaaaa", self.log.read_text())
        self.assertEqual(self.state.read_text().strip(), "stopped")

    def test_installed_launcher_uses_project_context_and_explicit_manager_only(self):
        result = self.run_installer(MAM_SERVICE_MANAGER=MANAGER)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = self.log.read_text()
        self.assertNotIn("service", log)
        self.assertNotIn("CODEX_THREAD_ID", log)

    def test_bound_project_without_manager_is_nonzero_with_remediation(self):
        result = self.run_installer(FAKE_START_STATE="missing_manager")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("bound tasks have no persisted Manager", result.stdout)

    def test_start_failure_retains_specific_reason_and_redacts_secret(self):
        result = self.run_installer(FAKE_START_FAIL="1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("TOKEN=do-not-log", result.stdout + result.stderr)

    def test_unrecognized_trace_block_is_preserved(self):
        path = self.home / ".bashrc"
        content = path.read_text().replace("export LOG_FORMAT=json", "export LOG_FORMAT=custom")
        path.write_text(content, encoding="utf-8")
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        updated = path.read_text()
        self.assertIn('export RUST_LOG="off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info"\nexport LOG_FORMAT=custom', updated)
        self.assertIn("export KEEP_THIS=1", updated)
        self.assertIn("export AFTER_RETURN=1", updated)
        self.assertEqual(updated.count("# >>> MAM PATH >>>"), 0)
        self.assertEqual(self.service_commands(), [])

    def test_installer_does_not_implement_a_background_shell_supervisor(self):
        source = (self.source_root / "scripts" / "install.sh").read_text(encoding="utf-8")
        self.assertNotIn("nohup", source)
        self.assertNotIn("setsid", source)
        self.assertNotIn("disown", source)
        for line in source.splitlines():
            code = line.split("#", 1)[0]
            self.assertIsNone(re.search(r"(?<![>&])&(?![&0-9])", code), line)


class LiveprobeEvidenceValidationTests(unittest.TestCase):
    script = Path(__file__).resolve().parents[1] / "scripts" / "install.sh"
    required_checks = (
        "all_roles_baselined_before_service",
        "baseline_history_read_after_idle",
        "job_delivery",
        "manager_delivery",
        "manager_is_fixture_only",
        "turn_budget",
        "service_stopped_after_delivery",
        "idle_executors_received_no_turn",
    )

    def validate(self, evidence: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            return subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; INSTALLED_PYTHON="$2"; validate_liveprobe_evidence "$3"',
                    "bash",
                    str(self.script),
                    sys.executable,
                    str(path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

    def evidence(self, model_turns: object = 6) -> dict[str, object]:
        return {
            "status": "passed",
            "model_turns": model_turns,
            "checks": {name: True for name in self.required_checks},
        }

    def test_accepts_bounded_model_turns_with_service_shutdown_evidence(self):
        for turns in (6, 12):
            with self.subTest(turns=turns):
                result = self.validate(self.evidence(turns))
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_out_of_budget_or_obsolete_quiet_window_evidence(self):
        for turns in (5, 13, True):
            with self.subTest(turns=turns):
                self.assertNotEqual(self.validate(self.evidence(turns)).returncode, 0)
        evidence = self.evidence()
        checks = evidence["checks"]
        assert isinstance(checks, dict)
        checks.pop("service_stopped_after_delivery")
        checks["quiet_window_no_duplicate_starts"] = True
        self.assertNotEqual(self.validate(evidence).returncode, 0)


if __name__ == "__main__":
    unittest.main()
