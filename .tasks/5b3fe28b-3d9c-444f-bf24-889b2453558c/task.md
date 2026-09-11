# MAM one-command installation and behavioral compatibility validation

Start from main 351c3a3e6dc807cae280a99d5f3c824f8d5750ff in a MAM-registered worktree. Follow AGENTS/README and publish report/commits. gpt-5.6-terra/max. No live app-server restart, modifying global binaries or production environment during development. Manager integrates/installs after review. Write scope: multi_agent_manager/wait_compat.py, scripts/install_and_test.sh, tests/test_wait_compat.py, docs/install.md. Manager owns README/AGENTS/design. Runtime task owns cli.py, job_runtime.py and other wait modules.

## Goal
User requests one-command MAM install+test and obvious errors ONLY when behavioral compatibility tests fail. Version changes themselves are NOT errors; new versions passing the tests must work. A message must never silently sit for 1h because integration broke. Keep small, no new dependency framework/daemon. Use stdlib + existing pipx/install entry. Inspect existing install docs first. Script must work from explicit checkout and installed CLI. Install failures/tests errors nonzero, clear summaries. No automatic kill/restart of user's Codex App.

## Runtime contract (coordinate Manager if changes)
Provide `wait_compat.require_compatible()` no args -> dict with socket_path, log_path and validated fingerprint; raises RuntimeError/actionable explanation on incompatibility. Runtime calls before blocking. Check actual running app-server behavior and connected proxy/runtime where observable, not just `codex --version`. Version is diagnostic information, not a gate or allowlist. A version change may trigger revalidation but must not itself fail require_compatible or block waiting when behavioral checks pass. Avoid a version-certificate approval workflow. No false PASS from merely unit tests or version string. Expose a narrow Python entry for installer self-tests if needed; do not add many user CLI flags.

Current actual server0.154.0, Windows App26.901.51231, official npm codex app-server proxy; app-managed process, NOT standalone daemon-managed. Socket /root/.codex/app-server-control/app-server-control.sock. Managed daemon restart cannot be assumed. App restarts must remain user-operated if necessary. Runtime may use trace log /root/.codex/app-server-control/app-server.log, RUST_LOG=off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info LOG_FORMAT=json. Known hook input cannot wake waits: executes after tools return.

Evidence in root .local/hook-probe/: watch_agent.py/agent-events.jsonl prove event subscription; check_mapping_trace.py isolates an ephemeral server and validates trace turn.id without model calls. Server log maps request to turn.id before wait ends. Test whether prerequisites actually work; don't simply trust log path exists. Keep payload/message bodies out of diagnostics.

## Validation scope
Unit tests must prove a changed/new version can PASS, and that broken event delivery, missing trace/capability, disconnected runtime and failed behavioral checks produce clear errors. Server/CLI version differences alone must not fail. Keep version metadata only for troubleshooting. Useful live protocol checks can use an independent temporary stdio server or read-only current control socket; must not start real model work or alter live threads. Full user-message/native-manager-send end-to-end checks require Manager coordination; report what cannot yet be certified instead of marking it passed. Installer should indicate exact needed test/restart action. User seeks one practical installation/test flow, not a large management system.

Run own tests and full suite. Publish small report with evidence and commits; clean temporary schemas, ephemeral processes/files. Do not keep active turn in a minute polling loop. Report blockers/contract questions then end turn so Manager can act.

## User correction (latest, authoritative)
Not “version changes cause error”; only failed tests cause error. Do not introduce version pinning, allowlists, mandatory approval certificates, or a fingerprint mismatch error. Revalidate behavior when appropriate; if tests pass, proceed.

## Final state-based semantics
Runtime now intentionally uses current-state pending-work checks, no completion replay/cursor/ack. Tests should cover inactive unarchived task returns (except delegated source under unarchived review), active owner job responsibility, and repeated return until handled. Only failing BEHAVIOR tests cause compatibility error, never version change. User asks no short polling.
