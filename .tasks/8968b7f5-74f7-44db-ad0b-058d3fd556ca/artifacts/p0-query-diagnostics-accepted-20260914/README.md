# P0 query diagnostics acceptance archive

This compact archive preserves task-private validation tooling and selected evidence for task `8968b7f5-74f7-44db-ad0b-058d3fd556ca` before its workspace and task branches can be removed. It was created for Manager final review under published task revision `506649777f83d7adbd4f7f9fb482246f525298eb`.

## Accepted code

- OpenPI: `codex/p0-query-diagnostics-accepted` → `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`
- robot-bridge: `codex/p0-query-diagnostics-accepted` → `e147f600dc4329f330a6e2eb0335150b5b3093a3`

The branches live in the primary repositories' shared Git databases, not in the task worktrees. They preserve the opt-in diagnostic implementation without changing any primary worktree HEAD.

## Contents

- `tooling/`: task-private source tools, diffs, deployment manifests, and CPU validation receipts. Python bytecode is excluded.
- `remote-evidence/records/`: compact copied C2 J/S record JSON/NPZ files, deployment/preflight/acceptance receipts, pair receipts, failure/status logs, and the S ordinary-output NPZ. Every copied file is rehashed against its C2 source.
- `artifact-index.json`: paths, SHA-256 values, sizes, retention scope, and C2-only result locations.
- `SHA256SUMS`: verification list for every archive file except itself.

The C2 run roots and original evidence remain in place. This archive deliberately does not copy virtual environments, dependencies, model checkpoints, caches, videos, or full runtime trees. Do not delete the referenced C2 evidence as part of source-task archival.

Verify this archive with `sha256sum -c SHA256SUMS` from this directory.
