# Production installation accepted

Manager installed the reviewed MAM implementation on 2026-09-12 at approximately 18:35 CST. Main code commit: `061eadcf38b45c10477a0268823308e1abb450f2`; merged into `project/state-vla` before installation. Independent final review: task `9128f418-33c6-4aa3-a684-8aafde0ecfb9` (PASS). Earlier runtime, wait coexistence and shell ownership reviews remain recorded in their archived tasks.

Command from the primary MAM root:

```bash
MAM_SERVICE_MANAGER=01a081fe-d6c2-74f2-a73d-68584e9d915b bash scripts/install.sh
```

The initial attempt failed before production mutation because source CLI tests required an adjacent mam launcher and inherited the Manager setting. The reviewed fix addresses both. The second attempt exited 0:

- 191 source tests passed before pipx installation.
- Pipx installed current code using Python 3.12.3. All eight installed package Python files match the source checkout byte for byte.
- Existing App Server JSON trace configuration was already valid; no App Server restart was needed or performed.
- Optional wait trace/message compatibility and no-model wake API compatibility passed.
- Isolated real delivery acceptance passed with exactly six model turns, including stopped-job delivery, batched Manager delivery and the quiet-window duplicate-start checks. The installer validated the fixture evidence then cleaned its temporary resources.
- `mam service status` confirmed `running: true`, `healthy: true`, Manager `01a081fe-d6c2-74f2-a73d-68584e9d915b`, and initial readiness at `2026-09-12T10:35:25+00:00`. Pending work for currently active recipients was retained without starting another turn.
- Migration requirements were published to all four active experiment tasks before steering their agents. The three existing executor waits were released by those messages; `mam wait list` subsequently contained only its header.

Local installation transcripts remain at `.local/proactive-install-20260912.log` (failed pre-install attempt) and `.local/proactive-install-20260912-retry.log` (successful attempt). PATH changes were backed up by the installer. Running GPU processes were not stopped or migrated during installation.

Normal turn end with proactive follow-up is now available. Optional `mam wait`, `mam wait list`, and `mam wait stop` remain installed. This is a detached per-project service; a future host/App Server failure still needs the documented service recovery, rather than assuming this acceptance proves permanent availability.
