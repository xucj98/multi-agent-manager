#!/usr/bin/env python3
"""CPU checks for the S continuation preflight's exact process boundary."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "tools"
SPEC = importlib.util.spec_from_file_location(
    "serial_continuation_preflight", TOOLS / "c2_serial_lag30_continuation_preflight.py"
)
assert SPEC is not None and SPEC.loader is not None
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


class TaskProcessBoundaryTest(unittest.TestCase):
    def test_only_current_preflight_pid_is_ignored(self) -> None:
        run = PREFLIGHT.RUN
        rows = "\n".join([
            f"101 python {run}/records/tools/c2_serial_lag30_continuation_preflight.py",
            f"102 python {run}/robot-bridge/scripts/run_policy_server.py",
            "103 python unrelated.py",
        ])
        owned = PREFLIGHT.task_owned_processes(rows, self_pid=101)
        self.assertEqual([{ "pid": 102, "args": f"python {run}/robot-bridge/scripts/run_policy_server.py"}], owned)

    def test_frozen_j_evidence_and_serial_leaves_are_explicit(self) -> None:
        self.assertIn("acceptance", PREFLIGHT.EXPECTED_J)
        self.assertIn("legacy_pair", PREFLIGHT.EXPECTED_J)
        self.assertTrue(PREFLIGHT.DEPLOYMENT_RECEIPT[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
