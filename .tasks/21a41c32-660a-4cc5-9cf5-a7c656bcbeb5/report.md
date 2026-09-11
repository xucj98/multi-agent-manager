# Unified mam wait runtime

## Delivery

Delivered commits on branch task/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5:

- cc69d43761ac7f28534bf062b75c031a7dcc891e — unified wait runtime.
- 89d094b289285d288be4f887e3a00c0278cd9c0 — executable module entry and compatibility-mock isolation.
- 675a53351a55be911b756b953c723e67f24929cb — native-wait setup/race and large snapshot fixes.
- 8539bfe73da3bac847e1b02315acf4d4900ac171 — native Manager-input wake path.
- 0dd2bcdf17f24688bc5452fd79a9066be543c782 — ignore lifecycle notifications for a bound agent that this executor wait has not snapshotted.

Worktree: /mnt/public/xcj/Projects/workspace/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5/multi-agent-manager

The runtime provides plain automatic mam wait, current-state ownership and review delegation, fixed 3600-second exits with required identifiers, lifecycle event handling, targeted user/native Manager input wakeups, and explicit errors. It has no delivery cursor, acknowledgement, replay state, server restart, GPU behavior, or production job changes.

Compatibility remains a no-argument wait_compat.require_compatible() gate. This task did not edit wait_compat.py, installer code, or documentation.

## Native Manager-input implementation

The observed normal Manager send_input path writes a current-turn response_item to the exact Codex session journal with role user and content_item_kinds containing user.text; it did not emit a traced turn/steer or turn/start request in the original diagnosis.

8539bfe opens that exact journal before the compatibility probe using CODEX_HOME, CODEX_SESSION_ID, and CODEX_THREAD_ID. It tails only new records and retains only turn/message identifiers and content kind. A matching current-turn user.text returns reason message, message received new message, and the affected agent. Timestamp floors reject old same-turn records; malformed, rotated, truncated, or ambiguous journals return explicit errors.

The App Server subscription also recognizes matching item/started and item/completed userMessage notifications. It validates the caller, current turn, item ID, and timestamp floor. Trace handling remains for turn/steer and turn/start.

0dd2bcd fixes a real integration smoke defect: an executor snapshots only its caller, while the shared control stream can contain lifecycle events from another bound agent. Such unsnapshotted events are ignored until the next state reconciliation instead of aborting the caller's wait. The regression verifies that this event followed by a matching native item returns message.

## Coordinated 900-second native smoke: PASS

Integration checkout: /mnt/public/xcj/Projects/multi-agent-manager/.local/wait-integration at 87f02d3db36546d23b6d65ee98f56224cf8c9f57.

One registered harmless local sleep 900s job was used, as required:

- job: fb8b8aa3-843b-422d-83f9-603950d0f79d
- wait PID: 67161
- sleep PID: 67154
- wait turn: 01a09167-b47b-7ac2-9829-65a89e6156c9
- armed: 2026-09-11T16:59:10.002497Z

Manager sent normal input after ready. The session journal recorded the matching current-turn user.text item at 2026-09-11T16:59:57.550Z. The actual CLI output completed at 2026-09-11T16:59:57.551423Z:

~~~json
{
  "status": "message",
  "reason": "message",
  "message": "received new message",
  "agent": "01a090d8-3590-7f91-b22c-3caf018058c1"
}
~~~

The monitor observed the sleep alive immediately at wait return. A later pre-cleanup job status still reported running at 2026-09-11T17:01:31.421887Z. Only after that observation, the smoke sleep was stopped and the registered job was archived with the factual note coordinated 900s native input smoke passed; stopped after message return cleanup.

Complete no-message-body evidence is retained at:

- /mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-coordinated-900-1789145948-result.json
- /mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-coordinated-900-1789145948-output.txt
- /mnt/public/xcj/Projects/multi-agent-manager/.local/native-wait-coordinated-900-1789145948-meta.json

Earlier 180-second smoke evidence, including the initial real failure before the native journal implementation, remains separately retained and was not counted as a pass.

## Validation

~~~text
Task worktree:
.venv/bin/python -B -m unittest discover -s tests -v
75 tests passed

Integrated checkout, using this task worktree interpreter:
.venv/bin/python -B -m unittest discover -s tests -v
102 tests passed
~~~

All smoke jobs for this task are archived. No server restart, production job change, or GPU operation occurred.

## Final review: journal discovery-to-open race repair

Delivered commit 86bc9688cf1945d49aef19fc18a64d399b701509 fixes the accepted final-review finding without changing live smoke behavior.

The invocation timestamp is captured before journal discovery. After identifying the unique journal, the watcher performs one bounded 32 MiB backwards lookup for the latest complete row older than that timestamp and opens from the following offset. Rows written after invocation, including rows written between discovery and the actual open, are therefore still read and passed through the existing timestamp filter. If the bounded tail has no safe older boundary, it opens from offset zero once rather than risk skipping a native input. Ordinary polls retain their forward-only incremental read behavior and do not rescan history.

The regression test test_session_lookup_window_captures_input_written_between_discovery_and_open simulates a valid current-turn user.text row appended after identity discovery but before file open. It verifies that the watcher returns the matching SessionMessage. This test failed with the previous EOF-open behavior.

Validation after this commit:

~~~text
.venv/bin/python -B -m unittest discover -s tests -v
76 tests passed
~~~

The previously recorded coordinated 900-second native smoke PASS remains the live evidence. Per the published requirement, no unrelated smoke was repeated for this lookup-window-only repair.

