from __future__ import annotations

import json
import http.server
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
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
            "multi_agent_manager/task_state.py",
            "multi_agent_manager/wake_compat.py",
            "multi_agent_manager/liveprobe.py",
            "multi_agent_manager/wake_runtime.py",
            "multi_agent_manager/cli.py",
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative == "multi_agent_manager/release.py":
                target.write_text(
                    'RELEASE_VERSION = "0.2.1"\n'
                    'RELEASE_TAG = "v0.2.1"\n'
                    'RELEASE_COMMIT = "' + "a" * 40 + '"\n',
                    encoding="utf-8",
                )
            else:
                shutil.copy2(self.source_root / relative, target)
        (root / "pyproject.toml").write_text(
            "[project]\nname = 'multi-agent-manager'\nversion = '0.2.1'\n", encoding="utf-8"
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
run_compatibility_check() {
    printf 'compatibility python=%s\n' "$INSTALLED_PYTHON" >> "$FAKE_LOG"
    if [[ "${FAKE_COMPATIBILITY_FAIL:-}" == 1 ]]; then
        incomplete 'simulated Codex compatibility failure'
        return 1
    fi
    COMPATIBILITY_JSON="$INSTALL_TMP/compatibility.json"
    printf '%s\n' '{"status":"passed","code":"compatibility","stages":[{"name":"non-model","status":"passed","duration_seconds":0.01}],"counts":{"model_requests":0}}' > "$COMPATIBILITY_JSON"
    printf 'MAM installation: shared Codex compatibility PASS\n'
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
            'RELEASE_VERSION = "0.2.1"\nRELEASE_TAG = "v0.2.1"\nRELEASE_COMMIT = "$Format:%H$"\n',
            encoding="utf-8",
        )
        subprocess.run(["tar", "-czf", str(self.archive), "-C", str(self.checkout), "."], check=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release metadata does not match requested version", result.stdout)
        self.assertEqual(self.service_commands(), [])

    def test_default_archive_download_uses_real_local_http_and_curl_output_before_separator(self):
        directory = self.root / "http-root"
        directory.mkdir()
        shutil.copy2(self.archive, directory / "candidate.tar.gz")
        handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
            *args, directory=str(directory), **kwargs
        )
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        environment = self._fixture_environment({
            "MAM_INSTALL_URL": f"http://127.0.0.1:{server.server_port}/candidate.tar.gz",
        })
        environment.pop("MAM_INSTALL_ARCHIVE", None)
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; INSTALL_TMP="$2"; REQUESTED_VERSION="0.2.1"; prepare_release_source; test -f "$CHECKOUT_ROOT/pyproject.toml"',
             "bash", str(self.checkout / "scripts" / "install.sh"), str(self.root / "download-tmp")],
            cwd=self.checkout, env=environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_nested_relocatable_venv_python3_is_selected_without_python_alias(self):
        candidate = self.checkout / ".venv" / "bin" / "python3"
        candidate.parent.mkdir(parents=True)
        candidate.symlink_to(Path(sys.executable).resolve())
        environment = self._fixture_environment({"PATH": f"{self.fake_bin}:/usr/bin:/bin"})
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; CHECKOUT_ROOT="$2"; choose_source_python; printf "%s\\n" "$SOURCE_PYTHON"',
             "bash", str(self.checkout / "scripts" / "install.sh"), str(self.checkout)],
            cwd=self.checkout, env=environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(Path(result.stdout.strip()), candidate)

    def test_same_repository_sibling_checkout_is_installed_and_path_persists(self):
        self.assertNotEqual(self.primary, self.checkout)
        original_bashrc = (self.home / ".bashrc").read_text()
        trace_begin = "# >>> MAM Codex App Server trace >>>"
        trace_end = "# <<< MAM Codex App Server trace <<<"
        legacy_trace = original_bashrc[original_bashrc.index(trace_begin) : original_bashrc.index(trace_end) + len(trace_end)]
        result = self.run_installer(CODEX_THREAD_ID="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("evidence=", result.stdout)
        log = self.log.read_text()
        self.assertIn("pipx args=install --force", log)
        self.assertIn(f"compatibility python={self.venv / 'bin' / 'python'}", log)
        self.assertNotIn("wait python", log)
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

    def test_existing_service_requires_live_app_server_before_service_status(self):
        missing = self.root / "missing.sock"
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer(probe_stubs=False, MAM_APP_SERVER_SOCKET=str(missing), FAKE_START_STATE="awaiting_manager")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("shared Codex compatibility acceptance failed", result.stdout + result.stderr)
        self.assertEqual(self.service_commands(), [])
        self.assertEqual(self.state.read_text().strip(), "healthy")

    def test_compatibility_failure_keeps_existing_scheduler_running(self):
        self.state.write_text("healthy\n", encoding="utf-8")
        result = self.run_installer(FAKE_COMPATIBILITY_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated Codex compatibility failure", result.stdout)
        log = self.log.read_text()
        self.assertIn("compatibility", log)
        self.assertNotIn("liveprobe", log)
        self.assertEqual(self.service_commands(), [])
        self.assertEqual(self.state.read_text().strip(), "healthy")

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

    def test_release_installation_keeps_full_regression_out_of_installer(self):
        source = (self.source_root / "scripts" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("multi_agent_manager.compatibility --output", source)
        self.assertIn("scripts/test_integration.py", (self.source_root / "scripts" / "test_integration.py").read_text())
        self.assertNotIn("unittest discover", source)

    def test_install_evidence_is_persisted_outside_temporary_directory(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = sorted((self.home / ".local" / "share" / "multi-agent-manager" / "install-evidence").glob("*.json"))
        self.assertEqual(len(evidence), 2)
        summary = json.loads(next(path for path in evidence if not path.name.endswith("compatibility.json")).read_text())
        self.assertEqual(summary["version"], "0.2.1")
        self.assertEqual(summary["tests"]["mode"], "install-smoke")

if __name__ == "__main__":
    unittest.main()
