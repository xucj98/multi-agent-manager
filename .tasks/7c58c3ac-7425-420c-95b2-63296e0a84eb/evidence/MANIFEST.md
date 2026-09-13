# Native v2 delivery audit evidence manifest

Task: `7c58c3ac-7425-420c-95b2-63296e0a84eb`

## Runtime release recorded during the audit

- `codex --version`: `codex-cli 0.154.0`.
- App Server package executable:
  `/usr/local/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`
  - SHA-256: `3188814c35471432d4123203e0eb38e5bddc60226e3d7ddf0e59e649ea140022`
- Code Mode host package executable:
  `/usr/local/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex-code-mode-host`
  - SHA-256: `0c57be435e73b70d9106c850d751cd259a7f04da958a453d7ef59090d82b70f1`

## Source provenance

- Read-only upstream checkout: tag `rust-v0.154.0`, commit
  `6b9826e3aa83b1a5947db50f4332cb9c65f1b340`.
- `source/` contains only the request processors, collaboration handlers,
  resolver/wait handler, CLI/TUI queue implementation, and Code Mode proto
  cited by the report. It is not an upstream source-tree copy.
- `protocol/ClientRequest.ts` is the experimental generated App Server request
  union captured for this audit, not the full generated schema directory.

## Integrity

`SHA256SUMS` covers every copied source/protocol file. Verify after changing
into this directory with:

```text
sha256sum -c SHA256SUMS
```

The manifest deliberately contains no environment dump, process log, prompt,
credential, or authorization header.
