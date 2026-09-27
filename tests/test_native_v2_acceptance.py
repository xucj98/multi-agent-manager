from __future__ import annotations

import unittest

from scripts import native_v2_fallback_acceptance as fixture


class NativeV2AcceptanceTests(unittest.TestCase):
    def test_exited_job_accepts_legacy_stopped_record(self):
        self.assertTrue(fixture._job_exited("exited"))
        self.assertTrue(fixture._job_exited("stopped"))
        self.assertFalse(fixture._job_exited("running"))
        self.assertFalse(fixture._job_exited({"status": "exited"}))

    def test_manager_attestation_accepts_concise_path_and_repeated_reminders(self):
        escalation = {"delivery": "accepted", "attempts": 3, "accepted_at": "now",
                      "executor_path": "/root/worker"}
        baseline = {"turn_start_attempts": 1}
        message = "[MAM Message]\n/root/worker: job job-id has exited. Use followup_task to ask the executor to check the result and archive the job."
        self.assertEqual(
            fixture._assert_manager_delivery(escalation, baseline, 4, message, task="task-id", job="job-id"),
            message,
        )
        with self.assertRaisesRegex(fixture.FixtureError, "count"):
            fixture._assert_manager_delivery(escalation, baseline, 2, message, task="task-id", job="job-id")
        with self.assertRaisesRegex(fixture.FixtureError, "concise"):
            fixture._assert_manager_delivery(
                escalation, baseline, 4, message + fixture.EXACT_REJECTION, task="task-id", job="job-id"
            )

    def test_manager_attestation_falls_back_to_task_id_for_old_tree(self):
        escalation = {"delivery": "accepted", "attempts": 1, "accepted_at": "now"}
        baseline = {"turn_start_attempts": 1}
        message = "[MAM Message]\nTASK-ID task-id: job job-id has exited. Use followup_task to ask the executor to check the result and archive the job."
        self.assertEqual(
            fixture._assert_manager_delivery(escalation, baseline, 2, message, task="task-id", job="job-id"),
            message,
        )


if __name__ == "__main__":
    unittest.main()
