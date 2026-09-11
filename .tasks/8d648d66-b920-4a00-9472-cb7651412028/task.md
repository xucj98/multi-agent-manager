# Independent review of unified MAM wait

Read MAM AGENTS/README, latest published task 21a41c32-660a-4cc5-9cf5-a7c656bcbeb5 and installer task 5b3fe28b-3d9c-444f-bf24-889b2453558c. Create registered worktree from current implementation cc69d43761ac7f28534bf062b75c031a7dcc891e. Reviewer is an executor with own task/workspace. Read-only review, don't edit source code; can add temporary tests in own tree and remove before report. gpt-5.6-terra/max, empty context. No production server restart or GPU changes.

Runtime owner is completing live native-message evidence; this review can independently test finalized state matrix now. Do not claim final acceptance until Manager supplies final commit/delta and live native-message evidence. Installer latest commit will follow; don't block waiting/polling, report concrete findings on available runtime first.

Review focus:
- Plain mam wait automatic caller identity, subagent own jobs, manager current-project active agents + inactive agents/jobs, current-state immediate pending returns, no historical completion replay/cursors/ack.
- Review task links delegate source inactive signal to reviewer, but do not hide inactive source owner's stopped unarchived jobs. owner active exempts jobs from manager. Subagent completion doesn't mean task acceptance.
- Required exit fields and compact CLI output: timeout3600, job-id/note, agent-id/task-id/task-title, message='received new message', manual cancelled. No waiting timeout/agent/task args; list/stop fallback retained.
- Real caller vs inherited parent identity, scope isolation, events/dynamic registration/races, stale trace/wait tokens, disconnect explicit error. Native manager send_input cannot be assumed to emit turn/steer. Missing capability must fail rather than one-hour silence.
- No overengineering. Compatibility tests should fail on broken behavior, not changed version. Review if heavy isolated-server startup on EVERY wait is necessary or excessive; report evidence/cost/alternative, not speculative demands for certificates.
- Do not broaden unrelated API. Review against user latest task, not abandoned designs. Findings concise with file/line, trigger, practical effect, tests.

Run meaningful independent tests and full suite where dependencies available. Installer module may be separate commit; use e20da6d52525267e035549c3447fbd6d3409df27 if needed in own review branch (this contains older installer script but current baseline wait_compat), disclose exact tested commits. Do not cherry-pick ongoing unstaged author changes. Publish report and end turn when useful findings ready. Manager later supplies final docs/installer for final pass. No minute polling.

## Integration review update
Final installer commit e23d693e5f8af5c9234da0c60148af3dc72b2fcd now available on top of e20da6d. Manager provisional integration in .local/wait-integration on local main includes runtime+installer, and README/AGENTS/design edits; use current local main as final integrated review base after preserving own tests. Review actual final docs for brevity/clarity/no conflicts, and installer bashrc+yes+precise restart+failed-tests behavior. Don't trust unit tests as real native-message evidence; that smoke is in progress. No live restart permitted in reviewer. Report findings promptly, especially any work-blocking runtime path. User requested no high-frequency model polling.
