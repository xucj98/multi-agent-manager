# Review the fresh-clone installation fix

Independently review candidate `061eadc` in multi-agent-manager. This adds source `a2cb5ce` to previously approved `e4bc982`; review the new three-file change, not already accepted runtime/wait semantics. Read AGENTS.md and this published task, create your own registered MAM worktree at the exact candidate, and read its development instructions.

## Questions to decide

- Does the full source suite run on a clean checkout whose selected Python has no adjacent `mam` executable, including CLI subprocesses launched from temporary fixture directories? Do those subprocesses reliably execute candidate code rather than an installed or PYTHONPATH-shadowed package?
- Does the real installer pre-pipx test phase isolate inherited `MAM_SERVICE_MANAGER`, while retaining its original intended value for actual final service activation?
- Are tests meaningful and the fix narrow, with no skipped checks, required pre-installation, production changes, or new public interface?

Reproduce the formerly failing actual `run_tests` path using `/root/miniconda3/bin/python3`, with `MAM_SERVICE_MANAGER=01a081fe-d6c2-74f2-a73d-68584e9d915b` set in the parent. Source `scripts/install.sh` without invoking main; set CHECKOUT_ROOT and SOURCE_PYTHON as required. Verify that the parent variable remains intact afterwards. It is sufficient to run the full source suite once in this exact scenario plus any focused checks needed for an identified concern; earlier broad reviews remain valid.

No pipx installation, shell configuration writes, production service/App Server operations, model liveprobe, robot access, or GPU work. Manager owns real installation after approval. Do not change implementation; report actionable blockers precisely or PASS. Write and publish `.tasks/9128f418-33c6-4aa3-a684-8aafde0ecfb9/report.md` with candidate, workspace, findings and exact validation, clean temporary artifacts, then end turn. No waiting merely for Manager feedback.
