# Unified `mam wait` runtime

Delivered commits on `task/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5`:

- `cc69d43761ac7f28534bf062b75c031a7dcc891e` — unified wait runtime.
- `89d094b289285d288be4f887e3a00c0278cd9c0c` — executable module entry and compatibility-mock isolation.
- `675a53351a55be911b756b953c723e67f24929cb` — native-wait setup/race and large snapshot fixes.
- `8539bfe73da3bac847e1b02315acf4d4900ac171` — native Manager-input wake path.

Worktree: `/mnt/public/xcj/Projects/workspace/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5/multi-agent-manager` (base `351c3a3e6dc807cae280a99d5f3c824f8d5750ff`).

The runtime provides plain automatic `mam wait`, current-state ownership and review delegation, fixed 3600-second exits with required identifiers, lifecycle event handling, and targeted user/native Manager input wakeups. It has no delivery cursor, acknowledgement, replay state, server restart, or GPU behavior. Compatibility remains a no-argument `wait_compat.require_compatible()` gate; this task did not edit `wait_compat.py`, installer code, or documentation.

## Native Manager-input diagnosis and fix

The real normal `send_input` submission `01a09133-80ed-7873-ba02-89aa409e69c9` reached the target agent while its wait was armed. The target session journal recorded a new `response_item` with `role: user`, `content_item_kinds: ["user.text"]`, and the current wait turn at 2026-09-11T16:01:25.671Z. The read-only App Server `thread/read` snapshot contains the matching `userMessage` item ID. In the same interval, App Server request tracing showed only `configRequirements/read` and `fs/getMetadata`; it did not show `turn/steer` or `turn/start`.

`8539bfe` treats this as the actual native path. Before the compatibility probe it opens the exact current-session journal identified by `CODEX_HOME`, `CODEX_SESSION_ID`, and `CODEX_THREAD_ID`, tails only new records, and retains only turn/message identifiers and the `user.text` kind. It returns `reason: "message"`, `message: "received new message"`, and the affected agent only when the journal turn equals the current wait turn. The timestamp floor rejects late old same-turn records. Journal rotation, truncation, malformed records, or ambiguous identity return an explicit error.

The App Server subscription now also recognizes a matching `item/started` or `item/completed` `userMessage` notification. It validates caller agent, current turn, item ID, and the invocation timestamp floor. This covers the direct event form without reading message text. RPC trace handling remains for `turn/steer` and `turn/start` paths.

## Validation

```text
.venv/bin/python -B -m unittest discover -s tests -v
# 74 tests passed

git diff --check
# passed
```

New regressions cover native `userMessage` events, wrong-agent/wrong-turn/stale-event rejection, session-journal targeting and deduplication, session identity validation, and input appended while compatibility is running. Existing tests retain CLI reason/identifier assertions, manual cancellation, timeout, ownership/review, trace-boundary, and stale-trace coverage.

The live `thread/read` diagnosis was read-only. No server restart, production job change, or GPU operation occurred.

## Native smoke status

The completed smoke against integration HEAD `60cfd89eab19de290872227c539ce4c706421436` is a real failure, not a pass. With registered job `e92b592d-87e4-4a7d-9888-d5fac284683e` and wait PID `29223`, Manager sent normal `send_input` with `interrupt=false` after the ready record. The CLI did not return `message`; after the 180-second sleep ended it returned:

```json
{
  "reason": "job_stopped",
  "job": "e92b592d-87e4-4a7d-9888-d5fac284683e",
  "note": "native Manager send_input smoke (sleep <=180s)"
}
```

The job was no longer alive at return and was archived with `native_message_pass=False`. Evidence is retained at `/mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-result.json` and `/mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-output.txt`.

For the required retest, integrate `8539bfe`, run from `/mnt/public/xcj/Projects/multi-agent-manager/.local/wait-integration` with this task worktree's `.venv/bin/python`, register a harmless local sleep of at most 180 seconds, and write `.local/native-wait-ready.json` only after the actual wait record exists. After normal Manager `send_input` with `interrupt=false`, accept only real CLI JSON with `reason: "message"`, `message: "received new message"`, this agent ID, and the sleep still alive; then stop and archive the smoke job.
