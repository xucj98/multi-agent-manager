# MAM unified wait

Implement in MAM from main 351c3a3e6dc807cae280a99d5f3c824f8d5750ff. Read MAM AGENTS/README, create registered workspace via mam workspace add, then repo instructions. Empty-context agent, gpt-5.6-terra/max. Write code, focused tests, publish report/commits; no live server restarts, GPU work, or production job changes. Manager owns final README/AGENTS/design doc editing and integration.

## User contract
- `mam wait` without arguments is the sole agent waiting entry. Remove `mam wait jobs` and task/timeout/agent input options for waiting. Preserve `mam wait list` and manual stop commands as fallback.
- Caller identity comes from CODEX_THREAD_ID. Missing/invalid/unresolvable identity fails explicitly. An executor bound to one nonarchived MAM task waits on that task's nonarchived jobs. Manager is unbound; scope is THIS MAM project's registered agents/tasks, never global unrelated Codex threads. Ambiguous bindings fail.
- Manager waits on active subagents and jobs belonging to inactive subagents. Active includes a subagent currently waiting (its turn is active). Avoid duplicate manager responsibility for active owners' jobs. Snapshot bootstrap and update ownership while waiting; no gaps when state changes/agents/jobs get registered.
- Fixed 3600 seconds, no public timeout argument. Any selected agent turn completion, selected job stop, targeted input/steer, manual stop, or expiry returns compact reason and relevant IDs. Empty target set returns promptly. Unknown probe state cannot be treated as stopped/healthy.
- User queue stays queued. Accepted/observed steer releases only the corresponding current wait. User may steer manager or subagent. Manager send_input to subagent must ALSO release its wait; determine actual in-process/native path rather than assuming it emits turn/steer. Interrupt semantics must not kill jobs. Do not touch GPU processes.
- User says separate invalid-steer acceptance validation is unnecessary: spurious release of the EXACT matched current wait is acceptable. Wrong-agent/stale-wait release is not. No need for accepted-response gate if exact current turn mapping suffices.
- Block/event processing belongs in ordinary Python, never repeated LLM calls. Reuse stdlib/control socket. Keep complexity small; reconnect or schema failure returns explicit error rather than silently waiting 1h. No global daemon required unless concrete evidence needs it.

## Evidence available (read bounded relevant files)
Manager .local/hook-probe/ in MAM root contains watch_agent.py and agent-events.jsonl: _WebSocket + initialize + thread/resume (no overrides) subscribes to turn/started, thread/status/changed, turn/completed without polling. Beware resume side effects/history bulk; preserve model/config.
Native wait_agent is unnecessary after unified wait. Current server 0.154.0, App26.901.51231, socket /root/.codex/app-server-control/app-server-control.sock. CODEX_THREAD_ID is agent ID.
UserPromptSubmit hook runs AFTER blocked tool returns, so cannot wake wait. Existing trace log /root/.codex/app-server-control/app-server.log with RUST_LOG=off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info LOG_FORMAT=json supplies request rpc.method, rpc.request_id, app_server.connection_id, turn.id while tool still waiting. Map turn -> thread from public events/snapshot. Only current matching wait should be released; deduplicate spans, handle server restart/log rotate/stale logs. No message text stored. Hook unnecessary for agent lifecycle and must not be used as steer trigger.
Source snippets exact rust-v0.154.0 under .local/hook-probe/source. In-process native send_input may have typed request or core path; manager will coordinate real probe if needed. Do not emit stdout noise on unrelated events.

## Parallel compatibility integration contract
Another task owns multi_agent_manager/wait_compat.py, scripts/install_and_test.sh, tests/test_wait_compat.py and installation docs. You own cli.py/job_runtime.py, new wait runtime modules and focused runtime tests. Agree by Manager, no overlapping edits. At wait entry call wait_compat.require_compatible() (no arguments), which returns a dict including socket_path/log_path after checking real running runtime fingerprint and valid certificate. It raises RuntimeError with actionable details when incompatible. Do not stub success in production. This module may arrive separately; temporary test mocks allowed. Communicate any necessary contract change through Manager before changes.

## Acceptance
Meaningful tests: role/ownership matrix, unrelated projects, no jobs, unknown identity/status, dynamic handoff, existing completion/subscribe race, notification disconnect, targeted steer, native message path, stale/dedup log, one-hour expiry, concurrent wait cleanup/manual stop. No GPU needed. Manager will run real end-to-end test with registered subagent; provide exact short scenario. Run full unit suite. Keep live main untouched, publish task report and commit, clean own temporary files before delivery. Never minute-poll Manager; finish turn when deliverable or blocked.

## User correction (latest, authoritative)
Compatibility failure means tests/capabilities failed, NOT that app-server/proxy version changed. A new version passing checks must work. No version allowlist or fingerprint mismatch rejection. wait_compat contract should gate on tested behavior, with versions only diagnostic.

## User acceptance addition: explicit exit reason and identifying fields
Every mam wait return must explain why it ended. Required outcomes:
- timeout: fixed one-hour wait elapsed (3600 seconds).
- job stopped/completed: include job-id and its registered note. Process exit detection alone does not prove experimental success; retain truthful status.
- subagent completed its turn: include agent-id, task-id and task-title.
- cancelled: manual `mam wait stop` ended this wait.
Do not collapse automatic user steer/native manager-message wake into manual cancelled; give a concise distinct message/input reason and affected agent ID. Preserve compact actionable error and empty-target reasons already required. No full metadata dump. Add assertions for output reason and ALL required fields, including manual cancellation and timeout. Ensure CLI output (not just internal return dict) retains these fields.
