from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from multi_agent_manager import compatibility, liveprobe


class CompatibilityTests(unittest.TestCase):
    def test_custom_call_requires_matching_output_call_id(self):
        turn = {
            "items": [
                {"type": "custom_tool_call", "name": "exec", "call_id": "call-1", "input": 'text("READY")'},
                {"type": "custom_tool_call_output", "call_id": "other", "output": [{"type": "input_text", "text": "Script completed\nREADY"}]},
            ]
        }
        self.assertIsNone(liveprobe._custom_tool_execution(turn, "READY"))
        turn["items"][1]["call_id"] = "call-1"
        self.assertEqual(liveprobe._custom_tool_execution(turn, "READY")["call_id"], "call-1")
        turn["items"][1]["output"][0]["text"] = "Script failed\nREADY"
        self.assertIsNone(liveprobe._custom_tool_execution(turn, "READY"))

    def test_assistant_marker_without_tool_items_is_not_execution(self):
        self.assertIsNone(liveprobe._custom_tool_execution({"items": [{"type": "agentMessage", "text": "READY"}]}, "READY"))

    def test_rollout_token_usage_reads_final_cumulative_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / "sessions" / "2026" / "10" / "01" / "rollout-thread-1.jsonl"
            rollout.parent.mkdir(parents=True)
            rows = [
                {"payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 10, "cached_input_tokens": 4, "output_tokens": 2, "reasoning_output_tokens": 1}}}},
                {"payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 25, "cached_input_tokens": 12, "output_tokens": 5, "reasoning_output_tokens": 3}}}},
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(root)}):
                self.assertEqual(liveprobe._rollout_token_usage("thread-1"), {
                    "input_tokens": 25, "cached_input_tokens": 12, "output_tokens": 5, "reasoning_tokens": 3,
                })

    def test_rollout_tool_execution_matches_raw_call_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / "sessions" / "2026" / "10" / "01" / "rollout-thread-raw.jsonl"
            rollout.parent.mkdir(parents=True)
            rows = [
                {"type": "session_meta", "payload": {"id": "thread-raw"}},
                {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-raw", "thread_id": "thread-raw"}},
                {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "call_id": "c1", "input": 'text("READY")'}},
                {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "c1", "output": [{"type": "input_text", "text": "Script completed\nREADY"}], "internal_chat_message_metadata_passthrough": {"turn_id": "turn-raw"}}},
                {"type": "event_msg", "payload": {"type": "item_completed", "thread_id": "thread-raw", "turn_id": "turn-raw"}},
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(root)}):
                self.assertEqual(liveprobe._rollout_tool_execution("thread-raw", "READY")["call_id"], "c1")
            rows[3]["payload"]["output"][0]["text"] = "Script failed\\nREADY"
            rollout.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(root)}):
                self.assertIsNone(liveprobe._rollout_tool_execution("thread-raw", "READY"))

    def test_rollout_tool_execution_does_not_accept_a_different_completed_turn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / "sessions" / "2026" / "10" / "01" / "rollout-thread-turns.jsonl"
            rollout.parent.mkdir(parents=True)
            rows = [
                {"type": "session_meta", "payload": {"id": "thread-turns"}},
                {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-other"}},
                {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "call_id": "other", "input": 'text("READY")'}},
                {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "other", "output": [{"type": "input_text", "text": "Script completed\\nREADY"}]}},
                {"type": "event_msg", "payload": {"type": "item_completed", "thread_id": "thread-turns", "turn_id": "turn-other"}},
                {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-target"}},
                {"type": "event_msg", "payload": {"type": "item_completed", "thread_id": "thread-turns", "turn_id": "turn-target"}},
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(root)}):
                self.assertIsNone(liveprobe._rollout_tool_execution("thread-turns", "READY", target_turn_id="turn-target"))

    def test_token_usage_does_not_fill_missing_thread_fields_with_zero(self):
        fixture = object.__new__(liveprobe._LiveFixture)
        fixture.threads = {"manager": "m", "job_executor": "w"}
        fixture.evidence = {"token_usage": {}}
        with mock.patch.object(liveprobe, "_rollout_token_usage", side_effect=[
            {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 3, "reasoning_tokens": 1},
            {"input_tokens": 4},
        ]):
            fixture._collect_token_usage()
        self.assertIsNone(fixture.evidence["token_usage"]["output_tokens"])
        self.assertIsNone(fixture.evidence["token_usage"]["reasoning_tokens"])

    def test_run_writes_two_stage_result_and_actual_counts(self):
        delivery = {
            "status": "passed",
            "resources": {
                "threads": {"manager": "m", "job_executor": "w"},
                "turns": {
                    "manager_baseline_completed": "1", "job_baseline_completed": "2", "job_delivery": "3",
                    "manager_compaction": "4", "manager_delivery": "5", "manager_user_followup": "6",
                },
            },
            "calls": {"direct_turn_start": 3, "compact_start": 1},
            "token_usage": {"input_tokens": 20, "cached_input_tokens": 10, "output_tokens": 8, "reasoning_tokens": 3},
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            with mock.patch.object(compatibility.wake_compat, "require_compatible", return_value={"socket_path": "/tmp/app.sock"}), mock.patch.object(
                compatibility.liveprobe, "run_live_delivery", return_value=delivery
            ):
                result = compatibility.run(output)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["counts"], {
                "sessions": 2, "turns": 6, "compactions": 1, "tests": 0, "model_requests": None,
                "input_tokens": 20, "cached_input_tokens": 10, "output_tokens": 8, "reasoning_tokens": 3,
            })
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["stages"][1]["status"], "passed")

    def test_rollout_subtotal_cannot_claim_usage_including_compaction(self):
        fixture = object.__new__(liveprobe._LiveFixture)
        fixture.threads = {"manager": "m", "job_executor": "w"}
        fixture.evidence = {"token_usage": {}, "calls": {"compact_start": 1}}
        with mock.patch.object(liveprobe, "_rollout_token_usage", return_value={
            "input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 3, "reasoning_tokens": 1,
        }):
            fixture._collect_token_usage()
        self.assertEqual(fixture.evidence["rollout_token_usage_excluding_compaction"]["input_tokens"], 20)
        self.assertEqual(fixture.evidence["token_usage"]["source"], "unavailable-including-explicit-compaction")
        counts = compatibility._counts(fixture.evidence)
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"):
            self.assertIsNone(counts[key])

    def test_non_model_failure_is_saved_and_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            with mock.patch.object(compatibility.wake_compat, "require_compatible", side_effect=RuntimeError("socket unavailable")):
                result = compatibility.run(output)
            self.assertEqual(result["status"], "failed")
            self.assertIsNone(result["live_delivery"])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["stages"][0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
