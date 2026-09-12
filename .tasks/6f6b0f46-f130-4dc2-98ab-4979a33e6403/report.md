# PASS — optional wait ownership correction

- Candidate reviewed: `3c88cf6a3772631f0bc252fef82e11315a9524b5` against `21e27c7`.
- Independent workspace: `/mnt/public/xcj/Projects/workspace/6f6b0f46-f130-4dc2-98ab-4979a33e6403/multi-agent-manager`.

The manager target classification now creates `agent_completed` only for an idle owner with no unarchived jobs. A running-only job stays in the wait set; stored/probed stopped jobs retain the executor handoff with JOB-ID and note; all-archived jobs and no-job tasks remain Manager follow-up. The `turn/completed` fast path reloads task, review, and wait-owner state before the same reconciliation, so it has the same ownership result as the initial snapshot.

I checked that active owners still exclude job probing, unknown probe states remain explicit errors, review suppression still leaves stopped source jobs visible, and message/cancel/one-hour timeout behavior is unchanged. `_refresh` reuses existing subscriptions, and the completion path does one finite reconciliation without recursive or unbounded polling.

Validation:

- `.venv/bin/python -B -m unittest discover -s tests -p 'test_wait_runtime.py' -v` — 42 passed.
- `.venv/bin/python -B -m py_compile multi_agent_manager/wait_runtime.py tests/test_wait_runtime.py` and `git diff --check 21e27c7..3c88cf6a3772631f0bc252fef82e11315a9524b5` — passed.
- Independent in-memory completion-event cases passed: a job becoming running continued waiting, an archived job returned `agent_completed`, and a newly registered active review continued waiting.

No blocker found. No production, liveprobe, GPU, service, or implementation actions were performed. Transient non-`.venv` Python caches were removed; the review worktree is clean.
