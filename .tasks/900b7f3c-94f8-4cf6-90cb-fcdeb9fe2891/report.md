# Optional wait ownership fix

- Workspace: `/mnt/public/xcj/Projects/workspace/900b7f3c-94f8-4cf6-90cb-fcdeb9fe2891/multi-agent-manager`
- Delivery commit: `3c88cf6a3772631f0bc252fef82e11315a9524b5` (`fix: preserve job ownership in optional wait`)
- Manager reconciliation now treats an inactive executor as completed only when it has no unarchived jobs. Running jobs keep `mam wait` pending; stopped jobs remain executor handoffs with their `JOB-ID` and note.
- `turn/completed` reloads current task, job, review, and wait-owner state before applying the same reconciliation, preserving stopped and unknown-state handling.
- Added coverage for idle running-only ownership, completed owners with running or stopped jobs, mixed job states, archived jobs, active wait ownership, and live stopped probes. Existing review suppression coverage remains exercised.

Validation:

- `.venv/bin/python -B -m unittest discover -s tests -p 'test_wait_runtime.py' -v` — 42 passed.
- `.venv/bin/python -B -m py_compile multi_agent_manager/wait_runtime.py tests/test_wait_runtime.py` and `git diff --check` — passed.
