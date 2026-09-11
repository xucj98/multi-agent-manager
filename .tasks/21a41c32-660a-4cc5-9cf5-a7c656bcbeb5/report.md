# Unified `mam wait` runtime

Delivered commit: `cc69d43761ac7f28534bf062b75c031a7dcc891e` on `task/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5`.

Worktree: `/mnt/public/xcj/Projects/workspace/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5/multi-agent-manager` (base `351c3a3e6dc807cae280a99d5f3c824f8d5750ff`).

Implemented the published runtime scope:

- Plain `mam wait` now resolves the canonical `CODEX_THREAD_ID`, selects Manager or executor responsibility automatically, and has a fixed 3600-second budget. The former `wait jobs` and wait scope/timeout/agent options are removed; `wait list` and manual stop remain.
- Added lifecycle subscriptions that preserve notifications arriving during `thread/resume`, current-state reconciliation for inactive tasks and stopped jobs, active-owner job exclusion, review delegation, dynamic task refresh, explicit unknown/error handling, and no delivery cursor or acknowledgement state.
- Added exact-current-turn wake detection for user steering and native Manager input. Both trace methods `turn/steer` and in-process `turn/start` return compact JSON with `reason: "message"`, `message: "received new message"`, and the affected `agent`.
- All wait exits retain required identifiers: job stop includes `job` and `note`; agent completion includes `agent`, `task`, and `task_title`; timeout includes `timeout_seconds: 3600`; manual stop returns `reason: "cancelled"` with `manual mam wait stop`.

Validation:

```text
.venv/bin/python -B -m unittest discover -s tests -v
# 65 tests passed
git diff --check
```

I also made one read-only `thread/resume` protocol-shape check against the running App Server: it returned the caller's active thread and active turn list. No server restart, production job change, or GPU operation was performed.

Compatibility handoff: runtime calls `wait_compat.require_compatible()` with no arguments and requires its returned string `socket_path` and `log_path`. The compatibility/installer task owns that module and installer integration.

Manager native-input smoke scenario after integration:

1. Bind a disposable executor task, register a harmless local sleep job, and let the executor call plain `mam wait`.
2. Send normal Manager `send_input` to that executor.
3. Confirm its CLI JSON returns `reason: "message"`, `message: "received new message"`, and the executor `agent`; confirm the registered job is still running.
4. Separately use `mam wait stop --agent AGENT-ID` and confirm the waiter returns `reason: "cancelled"` with `manual mam wait stop`.

## Native smoke precondition finding

The first real-smoke launcher did **not** arm. The integrated checkout accepted
`python -m multi_agent_manager.cli job add …` as a no-op because
`multi_agent_manager/cli.py` had no `__main__` invocation. It therefore returned
no job JSON, wrote no wait registration or readiness file, and the transient
unregistered local sleep was stopped immediately. The Manager input sent before
readiness is explicitly not evidence of a native-message wake.

Follow-up commit `89d094b289285d288be4f887e3a00c0278cd9c0c` adds the module
entry point and a subprocess test for it, and fixes the compatibility mock so it
does not invoke the real compatibility probe when that module is integrated.
The task-branch suite passes 66 tests. The real smoke must be rerun from the
integration checkout after that follow-up commit is included; no PASS or FAIL
for native Manager input is claimed yet.
