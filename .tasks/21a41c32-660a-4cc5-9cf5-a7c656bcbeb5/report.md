# Unified mam wait runtime

Delivered commits on branch task/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5:

- cc69d43761ac7f28534bf062b75c031a7dcc891e — unified wait runtime.
- 89d094b289285d288be4f887e3a00c0278cd9c0 — executable module entry and compatibility-mock isolation.
- 675a53351a55be911b756b953c723e67f24929cb — native-wait setup/race and large snapshot fixes.
- 8539bfe73da3bac847e1b02315acf4d4900ac171 — native Manager-input wake path.
- 0dd2bcdf17f24688bc5452fd79a9066be543c782 — ignore lifecycle notifications for a bound agent that this executor wait has not snapshotted.

Worktree: /mnt/public/xcj/Projects/workspace/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5/multi-agent-manager (base 351c3a3e6dc807cae280a99d5f3c824f8d5750ff).

The runtime provides plain automatic mam wait, current-state ownership and review delegation, fixed 3600-second exits with required identifiers, lifecycle event handling, and targeted user/native Manager input wakeups. It has no delivery cursor, acknowledgement, replay state, server restart, or GPU behavior. Compatibility remains a no-argument wait_compat.require_compatible() gate; this task did not edit wait_compat.py, installer code, or documentation.

## Native Manager-input diagnosis and native path

The earlier real normal send_input submission 01a09133-80ed-7873-ba02-89aa409e69c9 reached the target agent while its wait was armed. The target session journal recorded a new response_item with role user, content_item_kinds ["user.text"], and the current wait turn at 2026-09-11T16:01:25.671Z. The read-only App Server thread/read snapshot contains the matching userMessage item ID. In the same interval, App Server request tracing showed only configRequirements/read and fs/getMetadata; it did not show turn/steer or turn/start.

8539bfe treats the session journal as the observed native path. Before the compatibility probe it opens the exact current-session journal identified by CODEX_HOME, CODEX_SESSION_ID, and CODEX_THREAD_ID, tails only new records, and retains only turn/message identifiers and the user.text kind. It returns reason message, message received new message, and the affected agent only when the journal turn equals the current wait turn. The timestamp floor rejects late old same-turn records. Journal rotation, truncation, malformed records, or ambiguous identity return an explicit error.

The App Server subscription also recognizes matching item/started or item/completed userMessage notifications. It validates caller agent, current turn, item ID, and the invocation timestamp floor. RPC trace handling remains for turn/steer and turn/start paths.

## Retry evidence and follow-up fix

The initial smoke against integration HEAD 60cfd89eab19de290872227c539ce4c706421436 was a real failure: normal Manager input arrived after readiness, but the CLI returned job_stopped for job e92b592d-87e4-4a7d-9888-d5fac284683e. Its evidence remains at:

- /mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-result.json
- /mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-output.txt

After integration HEAD 758d523914ac5586cd9a5dda1a732c998b40a078, two subsequent ready-file attempts timed out before any fresh user input arrived. Their session-journal metadata contained only assistant records after arm, no role user / user.text record, so neither is a native-message pass or failure:

- job c92e728c-47a6-443f-95a7-e2677470836f, armed at 2026-09-11T16:40:55Z, later returned job_stopped;
- job e11a2ad0-d828-4ad1-94c8-4f254512c319, armed at 2026-09-11T16:45:02Z, later returned job_stopped.

A third attempt, job 92758ba3-ae87-467b-a7b0-9e5275d837b2, exposed a separate runtime bug. While the smoke sleep was still alive, CLI output was:

~~~json
{
  "reason": "error",
  "message": "App Server event arrived before snapshot for 01a08f82-48d5-73c1-93c1-5c2734a2c0fe",
  "agent": "01a090d8-3590-7f91-b22c-3caf018058c1"
}
~~~

That agent is a different bound task. An executor wait intentionally snapshots only its caller, but the shared control stream can emit lifecycle events for other bound agents. 0dd2bcd ignores an event for a bound agent absent from this wait's snapshot; its current state is reconciled on the next refresh. The new regression sends such an event before a matching native userMessage event and verifies the executor returns reason message instead of failing.

All three retry smoke jobs were stopped and archived with factual notes. Their independent output, stderr, metadata, and job-add records remain under /mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-retry-20260912-*.

## Validation

~~~text
.venv/bin/python -B -m unittest discover -s tests -v
# 75 tests passed

git diff --check
# passed before commit
~~~

The focused runtime suite also passed with the new regression. No server restart, production job change, or GPU operation occurred.

## Remaining integration step

Manager owns integration. Integrate 0dd2bcd into .local/wait-integration, then repeat the ready-file smoke from that checkout with this task worktree's .venv/bin/python. A pass requires actual CLI JSON with reason message, message received new message, agent 01a090d8-3590-7f91-b22c-3caf018058c1, and the registered sleep still alive at return. Do not count a coordination timeout or job_stopped as a native pass.
