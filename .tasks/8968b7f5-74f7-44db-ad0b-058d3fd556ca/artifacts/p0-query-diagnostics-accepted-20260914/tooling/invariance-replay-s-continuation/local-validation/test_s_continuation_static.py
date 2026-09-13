#!/usr/bin/env python3
"""CPU-only checks that the prepared continuation cannot rerun J or relax replay."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


class SContinuationStaticTest(unittest.TestCase):
    def test_pipeline_is_serial_only(self) -> None:
        text = (TOOLS / "run_serial_lag30_continuation.sh").read_text(encoding="utf-8")
        self.assertIn("serial_lag30", text)
        self.assertNotIn("full_t_plus_1", text)
        self.assertIn("run_serial_lag30_pair_invariance_replay.sh", text)
        self.assertIn("c2_serial_lag30_continuation_preflight.py", text)

    def test_replay_has_one_explicit_actions_cast(self) -> None:
        text = (TOOLS / "pair_query_diagnostic_logging_invariance_replay.py").read_text(encoding="utf-8")
        expected = 'expected_replay["actions"] = np.asarray(saved_policy_actions, dtype=np.float32)'
        self.assertIn(expected, text)
        self.assertIn("_field_comparisons(ordinary_off, expected_replay", text)
        self.assertIn("_field_comparisons(ordinary_on, expected_replay", text)
        self.assertNotIn("allclose", text)

    def test_ordinary_output_bundle_is_capped(self) -> None:
        text = (TOOLS / "pair_query_diagnostic_logging_invariance_replay.py").read_text(encoding="utf-8")
        self.assertIn("_DEFAULT_MAX_ORDINARY_ARRAY_BYTES = 8 * 1024 * 1024", text)
        self.assertIn("ordinary output arrays total", text)
        self.assertIn("_write_ordinary_bundle", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
