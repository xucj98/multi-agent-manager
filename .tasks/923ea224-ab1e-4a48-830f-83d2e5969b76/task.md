# Diagnose repeated cluster C simulator worker EOF

Your prior put-back training task695bc51f is accepted and archived. This is a new independent task. Read MAM AGENTS/README and this published task. Create independent worktrees using mam workspace add: robot-bridge base f9626636c4776d8eb15f9c556775cb2d12c000e5 and RMBench base 9d8f47887a50ea691e5624de139f10bfcfb54412; then read each repo AGENTS and robot-bridge docs/design/conventions.md. Do not reuse the archived workspace. Only create another repo worktree if the evidence actually requires its code.

## Problem and scope

Evaluation task e6908de7-4b02-465a-987b-a19eba7a315a report records six formal runs across C2 GPU6/7 and C3 GPU0/1/2/3 stopping at episode22 accepted reset with worker closed the RPC stream (EOFError). These partial results have no final_review.json and must not be counted as formal scores. C1 healthy runs continue untouched. Read that published report and the relevant failure_review.json, worker stderr, process records and outer logs under cluster C /mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910. Access via existing SSH wuwen-4090-1/2/3, read remote evaluation guide at /mnt/public/xcj/Projects/state-vla/README.md. Assets are shared but root filesystems may differ.

Find the earliest concrete process failure and explain the repeated episode index. Compare affected C2/C3 runs and healthy C1 runs for process lifecycle/reset/restart behavior, renderer setup, resource limits and relevant cache behavior. Inspect actual frozen source and existing logs before any reproduction. Do not assume Vulkan initialization text or Warp cache is causal merely because present. Warp0.15.1 ignores WARP_CACHE_PATH unless explicitly set in Python; this was already established, and no cache corruption is proven.

## Deliverable and boundaries

Provide a concise evidence-backed diagnosis and smallest proposed fix, affected code/version and a specific validation plan. Distinguish confirmed cause from hypotheses and state whether completed results are affected. Do not make code changes or start a formal rerun before Manager adjudicates the proposal. This phase uses read-only remote inspection and local CPU analysis; no GPU loading, process termination, cache deletion, driver changes or modifications to active worktrees/servers. Do not install new remote environments merely for inspecting logs. Ask for a bounded reproduction only if existing evidence cannot discriminate causes.

Write and publish report.md with workspace/commit IDs, evidence paths, findings and proposed next step, then end turn. Current MAM proactive wake is installed; no standing wait or recurring polling. Manager will assign review/implementation once the concrete cause is understood. The eval owner handles normal run completion, transfers and ledger updates; do not duplicate their ownership.
