# Interim independent core review — blockers found

Reviewed integration commit `f114fd6d7cc39f65bc76da9e782509bc1a256704` (runtime source declared as `bf157209d6eb9ebdc0d07f5344ca175501941598`, documentation parent `648acce84dc0543bf73e1b2a4f7a0a08b11c3c86`) in isolated worktree `/mnt/public/xcj/Projects/workspace/3c97bd4f-14e4-42bb-b7ec-ecf7aad0d5ff/multi-agent-manager`. This is an independent review; no production service, App Server, robot, GPU, or implementation code was operated or changed.

## Blocking findings

### 1. An interrupted recipient remains permanently blocked after an observable recovery

`WakeScheduler._deliver` calls `_preflight_failure(..., retry=False)` when the latest turn is interrupted, which writes `delivery="blocked"` and `next_attempt_at=None` ([wake_runtime.py](multi_agent_manager/wake_runtime.py) lines 931–938). The same event remains desired and `_reconcile_events` only updates its descriptive fields (813–838); `_deliver` skips all events whose retry time is `None` (964–975).

Reproduction with the existing in-memory test fixture: create one stopped job whose owner is idle and whose latest turn is `interrupted`; run one scheduler cycle; replace the latest turn with a new `completed` turn to model an explicit recovery while keeping the owner idle; run another cycle. The event remains `blocked`, `next_attempt_at` remains `None`, and `turn/start` calls remain `0`. It therefore cannot resume without an unrelated task/job signature change.

This violates the required behavior to preserve a user interruption while allowing explicit recovery. A recovery visible in current metadata must re-enable a still-current event under a deliberate, testable rule.

### 2. One transient source `unknown` probe discards an accepted Manager wake and later starts a duplicate turn

For an empty task with an idle executor, the scheduler accepts a `task_ready` event for Manager. If the executor is `unknown` for one cycle, `_desired_events` omits that event (wake_runtime.py 781–801), and `_reconcile_events` resolves every existing signature absent from the desired map as “condition changed or resolved” (813–819), including an already accepted event. When the executor returns to `idle` after the first Manager turn completes, a new event is created and a second Manager `turn/start` occurs.

Independent reproduction produced two Manager starts from the same unchanged empty task: first delivery `accepted`; one `unknown` source cycle leaves no event; source returns `idle` and Manager receives a second start. The accepted state must survive a transient unavailable source observation, or the system needs a durable condition generation that distinguishes true resolution from unknown metadata.

### 3. An explicit JSON-RPC rejection is classified as a lost response and can become a false ambiguity

`AppServerEventStream.request` turns a received JSON-RPC error response into the generic `AppServerEventError("App Server request turn/start failed: …")` (job_runtime.py 423–444). `_delivery_failure` then uses only message substrings; an explicit rejection not containing its small blocked-word list becomes `delivery="uncertain"` (wake_runtime.py 921–929). A later unrelated completed turn changes the boundary, so `_reconcile_uncertain_boundary` upgrades that known rejection to `ambiguous` (944–962).

I directly exercised `AppServerEventStream.request` with a controlled JSON-RPC `{ "error": { "message": "explicitly rejected" } }` response; it produced exactly `AppServerEventError: App Server request turn/start failed: explicitly rejected`. Feeding that error through the scheduler yielded `uncertain`; after a separate completed turn, it yielded `ambiguous` with zero successful wake starts. An acknowledged rejection is not a response-lost outcome, so the transport/RPC result needs structured distinction before boundary reconciliation.

## Verification performed

```text
.venv/bin/python -B -m unittest -v tests.test_wake_runtime tests.test_job_runtime tests.test_wait_compat
```

All 71 existing tests passed. The three reproductions above used the existing isolated fake Store/App Server fixture only; they leave no smoke artifacts. Current tests do not cover these transition sequences.

## Documentation interim verdict

The `AGENTS.md` end-turn guidance and README “自动跟进” section are concise and no longer conflict with a mandatory `mam wait` workflow. They keep ordinary-agent guidance separate from design detail. Installer/liveprobe files remain out of this interim verdict as directed while their replacement integration is pending.

Do not approve the runtime portion of `f114fd6` until Manager decides these three blockers and the original author supplies fixes plus regression coverage. This review task remains available for the final combined-commit review; no implementation or test commit was made here.
