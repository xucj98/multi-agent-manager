from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

from multi_agent_manager import __version__, version


class VersionTests(unittest.TestCase):
    def test_program_version_and_release_metadata_are_stable(self):
        self.assertEqual(__version__, "0.2.2")
        self.assertEqual(version.info()["version"], "0.2.2")
        self.assertEqual(version.info()["tag"], "v0.2.2")
        self.assertRegex(version.source_commit() or "", r"^[0-9a-f]{40}$")

    def test_cli_version_does_not_require_an_instance_configuration(self):
        result = subprocess.run(
            [sys.executable, "-m", "multi_agent_manager.cli", "--version"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "0.2.2")


if __name__ == "__main__":
    unittest.main()
