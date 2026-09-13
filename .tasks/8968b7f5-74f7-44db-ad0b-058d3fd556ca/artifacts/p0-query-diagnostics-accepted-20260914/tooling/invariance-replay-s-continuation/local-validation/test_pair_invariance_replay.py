#!/usr/bin/env python3
"""CPU checks for strict pair comparison and compact ordinary-output persistence."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np


TOOLS = Path(__file__).resolve().parents[1] / "tools"
SPEC = importlib.util.spec_from_file_location(
    "pair_invariance_replay", TOOLS / "pair_query_diagnostic_logging_invariance_replay.py"
)
assert SPEC is not None and SPEC.loader is not None
PAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PAIR)


class StrictComparisonTest(unittest.TestCase):
    def test_same_actions_are_strictly_equal(self) -> None:
        actions = np.arange(12, dtype=np.float32).reshape(3, 4)
        self.assertIsNone(PAIR._same_value(actions, actions.copy(), "actions"))

    def test_dtype_or_value_change_fails(self) -> None:
        actions = np.arange(12, dtype=np.float32).reshape(3, 4)
        self.assertIn("dtype/shape", PAIR._same_value(actions, actions.astype(np.float64), "actions"))
        near = actions.copy()
        near[0, 0] += np.float32(1e-6)
        self.assertEqual("actions: array values differ", PAIR._same_value(actions, near, "actions"))

    def test_other_replay_field_is_not_cast(self) -> None:
        actual = {
            "actions": np.arange(6, dtype=np.float32).reshape(3, 2),
            "memory_prediction_ids": np.array([[1, 2]], dtype=np.int32),
        }
        expected = {
            "actions": np.asarray(actual["actions"], dtype=np.float32),
            "memory_prediction_ids": actual["memory_prediction_ids"].astype(np.int64),
        }
        fields = PAIR._field_comparisons(actual, expected, "output")
        self.assertTrue(fields["actions"]["equal"])
        self.assertFalse(fields["memory_prediction_ids"]["equal"])
        self.assertFalse(PAIR._all_equal(fields))

    def test_rng_difference_fails(self) -> None:
        left = {"algorithm": "threefry2x32", "key_data": np.array([1, 2], dtype=np.uint32)}
        right = {"algorithm": "threefry2x32", "key_data": np.array([1, 3], dtype=np.uint32)}
        self.assertFalse(PAIR._comparison(left, right, "rng")["equal"])

    def test_state_difference_fails(self) -> None:
        off = {
            "actions": np.zeros((2, 14), dtype=np.float32),
            "state": np.array([1.0, 2.0], dtype=np.float32),
        }
        on = {"actions": off["actions"].copy(), "state": off["state"].copy()}
        on["state"][1] = np.float32(3.0)
        self.assertFalse(PAIR._comparison(off, on, "ordinary_output")["equal"])


class OrdinaryBundleTest(unittest.TestCase):
    def test_bundle_persists_both_direct_outputs(self) -> None:
        off = {
            "actions": np.arange(12, dtype=np.float32).reshape(3, 4),
            "memory_prediction_ids": np.array([[1, 2]], dtype=np.int32),
        }
        on = {key: value.copy() for key, value in off.items()}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ordinary.npz"
            receipt = PAIR._write_ordinary_bundle(path, off, on, max_bytes=4096)
            self.assertTrue(path.is_file())
            self.assertEqual(2 * (off["actions"].nbytes + off["memory_prediction_ids"].nbytes), receipt["uncompressed_array_bytes"])
            self.assertEqual(4, len(receipt["arrays"]))
            with np.load(path, allow_pickle=False) as loaded:
                self.assertEqual(4, len(loaded.files))
            with self.assertRaises(FileExistsError):
                PAIR._write_ordinary_bundle(path, off, on, max_bytes=4096)

    def test_bundle_cap_rejects_before_write(self) -> None:
        off = {"actions": np.zeros((64, 64), dtype=np.float32)}
        on = {"actions": np.zeros((64, 64), dtype=np.float32)}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ordinary.npz"
            with self.assertRaises(ValueError):
                PAIR._write_ordinary_bundle(path, off, on, max_bytes=128)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
