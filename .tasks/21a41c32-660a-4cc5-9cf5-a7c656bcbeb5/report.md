task_revision: 7a891f70c74a71b033638b6712c4c7da19e91574

# Unified \`mam wait\` runtime

Delivered commits on \`task/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5\`:

- \`cc69d43761ac7f28534bf062b75c031a7dcc891e\` — unified wait runtime.
- \`89d094b289285d288be4f887e3a00c0278cd9c0c\` — executable module entry and compatibility-mock isolation.
- \`675a53351a55be911b756b953c723e67f24929cb\` — native-wait setup/race and large snapshot fixes.

Worktree: \`/mnt/public/xcj/Projects/workspace/21a41c32-660a-4cc5-9cf5-a7c656bcbeb5/multi-agent-manager\` (base \`351c3a3e6dc807cae280a99d5f3c824f8d5750ff\`).

The runtime provides plain automatic \`mam wait\`, current-state ownership and review delegation, fixed 3600-second exits with required identifiers, lifecycle event handling, and targeted user/native Manager input wakeups. It has no delivery cursor, acknowledgement, replay state, server restart, or GPU behavior. Compatibility remains a no-argument \`wait_compat.require_compatible()\` gate; this task did not edit \`wait_compat.py\`, installer code, or documentation.

## Follow-up fixes

- Raised the bounded WebSocket frame cap from 4 MiB to 16 MiB. The live \`thread/resume\` frame that blocked the smoke was 4,938,839 bytes; after the change, a read-only live resume of the current active thread succeeded at 6,355,996 JSON bytes.
- The CLI now opens the authoritative App Server trace path before the compatibility probe and passes that tail into the wait runtime. It accepts a future public \`wait_compat.configured_paths()\` helper and uses the integrated module's current \`_configured_paths()\` helper otherwise; no guessed path is used. A changed path after compatibility returns an explicit error.
- Every trace increment, including the initial increment, is filtered by the invocation timestamp. Thus a buffered old span for the same turn cannot cancel a later wait.

Focused regressions cover a >4 MiB \`thread/resume\` response, input written during compatibility, and a late old same-turn trace span.

## Validation

\`\`\`text
.venv/bin/python -B -m unittest discover -s tests -v
# 69 tests passed
git diff --check
# passed before commit
\`\`\`

The live \`thread/resume\` check was read-only. No server restart, production job change, or GPU operation occurred.

## Native Manager-input smoke evidence

Actual smoke against integration HEAD \`18006592dadd19f923b8020a1e90a139997cc00d\` used the task worktree interpreter with integration as CWD, a registered <=180-second local sleep job \`ed2045cd-a69c-4a2c-afc8-8c417eea810b\`, and \`python -m multi_agent_manager.cli wait\`.

It failed before wait registration, so no readiness file was written and no Manager input was sent during an armed wait:

\`\`\`json
{"status":"error","reason":"error","message":"App Server event connection failed: WebSocket frame is too large","agent":"01a090d8-3590-7f91-b22c-3caf018058c1"}
\`\`\`

The sleep job was still alive when the CLI returned, then it was stopped and archived with the smoke cleanup note. This is a real FAIL for the old integration runtime, not native-message PASS evidence.

Manager integration must include \`675a53351a55be911b756b953c723e67f24929cb\`, then rerun the same bounded smoke from \`.local/wait-integration\` using this task worktree's \`.venv/bin/python\`. Write \`.local/native-wait-ready.json\` only after the actual wait record exists, send normal \`send_input\` with \`interrupt=false\`, and accept only CLI JSON with \`reason: "message"\`, \`message: "received new message"\`, the affected agent ID, and the job alive at return. Stop and archive that smoke job afterward.

