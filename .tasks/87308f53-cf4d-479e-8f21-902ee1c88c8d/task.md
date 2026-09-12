# Independent review: restored renderer lifecycle patch

Read MAM AGENTS/core/local instructions and this published task. Create your own registered RMBench worktree at77477931bee18c2476bea36b400ab45dc67d9ebe, then read repo AGENTS. Review source task923ea224 published requirements/report and original diagnosis report at MAM project commit1a5be7932382a61804a933c82edd4336640f6848. Source/CPU review only; no remote writes, GPU imports/execution, installation, production changes or formal reruns.

## Decision needed

Current C r2 base9d8f478 accidentally omitted previously reviewed renderer fix17b55bff1c79a0c5a836d1da089765934cb3a5b0. Six C2/C3 processes failed after22 terminals on reset23, native renderer error before worker EOF. Candidate eba81b41b39652b940fdb6d93dc4451a91352960 restores the exact patch;7747793 adds AST CPU regression separately. Verify patch identity/scope and compatibility with current reset lifecycle: one renderer per fixed-device worker, but fresh per-episode engine/scene/task state. No protocol/action/seed/memory changes. Review test quality and claims without mistaking AST checks for native proof. Source implementation may be minimal; avoid proposing unrelated redesign.

Run targeted CPU tests using unittest, no pytest installation required. Do not run full discover because test_dm05_integration imports SAPIEN and may block on this host. If bridge lifecycle source is required create an independent bridge worktree atf9626636c4776d8eb15f9c556775cb2d12c000e5 and use only relevant CPU-safe checks.

Assess planned deployment validation: new frozen runtime tree, bounded40-reset lifecycle gate on affected C2/C3 hosts to cross old failure index, matching video/no-video smoke2 on each target host, then fresh formal100 runs from original full seed lists. Existing partials never reused;22terminal+1reset-error not23accepted. Completed healthy C1 results remain valid unless concrete counterevidence. Historical2a879870 gate/100 result is supporting evidence, not a substitute for new combined-runtime validation.

Deliver PASS or actionable blocker, exact candidate, workspace/commits, checks and limitations in your published report.md. No implementation changes. Clean own temporary artifacts and end turn. Manager adjudicates and authorizes deployment after review; no standing wait required.
