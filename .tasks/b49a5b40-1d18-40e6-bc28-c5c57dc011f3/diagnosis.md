# multi-agent v2 wake rejection diagnosis

## Confirmed cause

The proactive scheduler correctly observed the stopped processes, but it used
the App Server `turn/start` path to send a text input directly to each bound
executor.  Native Codex multi-agent v2 child threads explicitly reject that
operation:

```text
App Server request turn/start failed: direct app-server input is not allowed for multi-agent v2 sub-agents
```

The captured [incident snapshot](incident_snapshot.json) records 15 current
`job_stopped` events (six U jobs and nine eval jobs), each with that exact
message.  The scheduler treated every `AppServerRpcError` alike, so it retained
these events as retryable `explicit_rpc_rejection` records.  Its stopped-job
routing intentionally targets the executor and does not create the normal
Manager-ready event.  The result was a healthy process with rejected delivery
records and no durable Manager escalation.

## Narrow repair

The repair recognizes only the explicit v2 direct-input rejection above.  It
persists the affected executor `job_stopped` event as blocked with no retry
deadline, then creates one durable Manager escalation for each still-current
stopped job.  Escalations are batched when the Manager is idle and tell the
Manager to use its native `followup_task` coordination path.  They are not an
attempt to inject input into the child, alter Codex state, or claim that direct
v2 delivery has started working.

Ordinary explicit RPC failures remain retryable, and transport failures remain
uncertain and retain their before-turn reconciliation.  The escalation is
removed when its source job is archived, its task is archived, or a rebind
changes the executor; a new stopped job has a distinct durable condition.

## Evidence boundary

The installer fixture exercises ordinary persisted threads.  Passing that
fixture confirms ordinary scheduler delivery only; it does not certify direct
input to a native multi-agent v2 child.  The current incident owners were
notified separately by the Manager through native follow-up, without changing
the captured state.  This task adds mocked regression coverage for the known
rejection but does not run a production install, restart an App Server, or
claim a new live v2 delivery result.
