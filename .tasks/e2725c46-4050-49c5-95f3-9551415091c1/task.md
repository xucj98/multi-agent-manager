# 独立复核：安装脚本保留用户shell配置

Review source delivery (source TASK-ID: e7183b34-6d86-4394-ada8-675f54b56c42):
{
  "task": "e7183b34-6d86-4394-ada8-675f54b56c42",
  "commits": {
    "multi-agent-manager": "e7b3f5785e1ed98556e6815d255aa9d7ee80de5c"
  }
}

Source task requirements:

# MAM proactive wakeup installation and behavioral acceptance

This is the consolidated current task; it replaces the earlier draft and withdrawn proposals. User approved implementation, isolated real test turns, installation compatibility tests, and removing mam wait. Manager handles production installation, main/project merges, README and AGENTS. You own installer/compat/liveprobe code and docs/install.md. Model gpt-5.6-terra/max.

## Workspace and ownership
Use existing registered worktree /mnt/public/xcj/Projects/workspace/e7183b34-6d86-4394-ada8-675f54b56c42/multi-agent-manager. Runtime task bc998553-c309-4734-b625-429a27f09a3b delivered bf157209d6eb9ebdc0d07f5344ca175501941598 plus fixes45614a60f63517eff3075381c697d370f09bdccc; cherry-pick both as needed for combined verification. Runtime owns cli.py/job_runtime.py/wake_runtime.py/design; report runtime bugs to Manager. You may edit scripts/install.sh, replace wait_compat and its tests, add wake_compat/liveprobe and corresponding installer tests, and update docs/install.md. Do not modify README/AGENTS, production service/threads/robots/GPU, or install globally yourself.

## Installation contract
- Preserve user's workflow: PROJECT_ROOT/.mam/env.json with MAM_ROOT, PROJECT_ROOT, MAM_BRANCH; clone MAM; sudo apt install -y pipx; bash scripts/install.sh. Install current code checkout through pipx, including a main worktree of same Git repo while MAM_ROOT stores project branch state. Do not require code checkout == MAM_ROOT or overwrite code source with state root.
- Ensure ~/.local/bin PATH persists in .bashrc/login shell idempotently, preserve unrelated content and make backup when changing it. Remove only known installer-owned obsolete trace block. Proactive wake does not need message interception/trace log; do not restart Codex or manage npm/systemd for obsolete wait compatibility.
- No systemd available. Runtime owns detached per-project singleton start_service(config, manager=None), stop_service(config), service_status(config), or equivalent mam service CLI. Installer must not implement another daemon/supervisor or compatibility-bypass API. State is MAM_ROOT/.local/service.
- Service status mapping has status, running, healthy, manager, pending:{count,events}. Healthy/pending/awaiting_manager can be ready. On a fresh empty project, no Manager yet is allowed: awaiting_manager until first Manager task create/bind captures CODEX_THREAD_ID. Existing bound tasks without reliable Manager must fail with explicit mam service start --manager AGENT-ID; installer must not mistake its caller for Manager. Optional deliberate MAM_SERVICE_MANAGER setup is allowed.
- Tests and live compatibility must pass before stopping/replacing current project service. Preserve pending records/manager on update and never touch another project. Fail nonzero with concrete bounded diagnostics when tests, readiness or start fail. Versions are diagnostic only, never an allowlist. A missing live App Server is a compatibility failure even for fresh project; awaiting_manager does not skip tests.

## Compatibility and real delivery test
1. wake_compat.require_compatible() returns socket_path/capabilities/diagnostics and raises RuntimeError on failed behavior. It is lightweight and makes zero model calls; runtime can repeat it at startup/reconnect. Check the actual required RPC methods/parameter forms with explicit unknown-thread rejection, accepting observed thread not loaded/no rollout found/thread not found but rejecting method not found or unexpected acceptance. Never label untested eventstream/delivery validated from handshake only.
2. install.sh separately invokes liveprobe once. It must not be called by require_compatible, so there is no recursion or need for a bypass token/API/cached PASS certificate. Parent/child repeating lightweight checks is fine.
3. Real probe uses isolated disposable fixture MAM project and NORMAL PERSISTED dedicated test threads (do not use ephemeral=true: current API cannot list turns/archive them). Register fixture tasks/workspaces before creating/binding executors; bind before their first model turn. Fixture Manager is distinct from real Manager and executor. Use real App Server and actual background scheduler, real short local job/PID, no production state changes, no GPU. Tiny deterministic response instructions and gpt-5.6-terra/max, bounded calls (current plan four dedicated threads, three total model turns) and finite timeout.
4. Verify existing executor ends baseline turn, then stopped registered job produces a new turn with exact JOB-ID/note/task context. Verify no-job/all-archived-job idle executors produce Manager message with AGENT-ID/TASK-ID/title, never received new message. Test no duplicate starts in an unchanged quiet window. Keep observed delivery details and actual turn IDs; do not substitute fake RPC or mere metadata for real delivery proof.
5. On pass/failure stop only fixture daemon, archive fixture jobs/tasks, finish or interrupt only owned known test turns if needed, and archive only created persisted threads. Retain compact receipt including IDs/results/cleanup, then remove owned temporary fixture paths. Failure must not print PASS or retry indefinitely. Unit tests are isolated/no-model; liveprobe is explicitly install-time only.

## First failed ephemeral attempt
Keep compact receipt in this task directory with the four created IDs and baseline turn ID. Confirm that known baseline turn finished, or interrupt only that owned turn. Record precisely what API can confirm after original stream closed; no expansion of production runtime for ephemeral fixtures. No user approval is needed to correct this test configuration and use persisted threads. All real testing above is already authorized.

## Delivery
Run installer/compat/liveprobe unit/subprocess tests and full combined unittest suite, then one real isolated acceptance with current runtime. Commit your owned changes separately from cherry-picked runtime commits. Publish concise final .tasks/TASK-ID/report.md with final commits, concrete results, limits and cleanup; remove withdrawn proposals from final report. No global install or production activation. If an actual Manager decision is required, publish exact blocker and end turn so Manager can handle it; do not remain active merely waiting for an answer. Otherwise continue autonomously. Independent reviewer task3c97bd4f will review final combined candidate.

## Manager diagnosis of new liveprobe API timing issue
Manager read the owned archived probe01a094ac-e3e1-72b2-9825-ee3e099fc9f7: both thread/read(includeTurns=true) and thread/turns/list(limit1,itemsView=notLoaded) work when it is notLoaded/archived, and its baseline had been interrupted by cleanup. Thus do not conclude the method is globally unavailable from polling it while the baseline is still active. Production runtime intentionally reads latest history only after idle preflight.
For the next bounded probe, use actual turn/completed notifications or thread/read metadata to await each baseline finish before history retrieval; metadata alone is not the final delivery assertion. Give all four dedicated persisted fixture roles one tiny baseline turn first, so they are materialized and can resume/archive reliably. This raises the finite nominal total to SIX model turns (four baseline plus job wake plus one batched Manager wake), explicitly authorized. Keep per-role before/after turn counts; do not expect unstarted roles to have zero history now. This is simpler and closer to production than special-case cleanup of never-materialized threads.
After a completed baseline, try paged history. If it still returns explicit list_turns unsupported, compare thread/read(includeTurns=true) on that same short owned fixture without starting another model turn, report the precise result to Manager/runtime owner. Do not change production runtime or loop new baseline requests to explore. If failure remains an actual Manager dependency, publish concrete report and end turn. The owned archived probe remains archived (Manager attempted resume and it explicitly refused archived; no new model turn or unarchive occurred).
# Final integration blocker: clean-checkout installer tests

Manager integrated your owned commits at20ff584. Running /root/.local/share/pipx/venvs/multi-agent-manager/bin/python -B -m unittest discover -s tests -q from .local/integration-proactive-wake (no local editable venv) yields107 pass, one error: test_fresh_daemon_process_confirms_readiness_and_stops_without_app_server_delivery -> detached service did not signal verified startup readiness. _spawn_service invokes sys.executable -m multi_agent_manager.wake_runtime with cwd set to the isolated fixture MAM_ROOT; that interpreter has only the old installed package3302520, so cannot import the new source runtime there. run_tests currently chooses system python on a fresh clone and does not establish the source import path before pipx install. This means the user's exact clean-clone bash scripts/install.sh workflow can fail even though an editable agent worktree passes.

Reproduce and fix the installer/test source-environment setup, without installing globally or skipping the daemon subprocess test. Ensure source checkout tests and their subprocesses exercise this checkout even when no .venv/editable install exists. Add a meaningful regression for that clean-checkout case. Keep changes limited to installer/tests unless runtime owner needed. Publish fix commit; rerun appropriate/full unit tests. Do not repeat the already successful real6-turn liveprobe solely for this CPU setup fix. Manager will run full install's liveprobe after approval. Reviewer3c97 will be informed of this blocker.
# User decision: preserve optional wait, including installation compatibility

User explicitly decided to retain mam wait, mam wait list and mam wait stop manager/--agent through migration and later use. This supersedes previous removal of wait_compat, trace setup and all claims that optional wait is unavailable. Proactive normal end-turn remains default; ordinary wait remains optional with its existing stop/message behavior. Daemon does not add receive-message events.

Runtime ownerbc998553 restores stable3302520 wait CLI/storage/runtime/tests after separately committing current daemon import fix. You restore current-main330252072cb3c2a834a69a9d63cd1e34627668fa wait_compat.py and its tests, and adapt install.sh/docs/install.md so upgrade preserves working wait as well as validating proactive wake. Existing wait trace configuration must not be removed. Reuse the already tested stable compatibility/setup code where needed; behavior failures, not versions, determine acceptance. Do not silently degrade message cancellation or claim wait compatibility from wake-only tests. Both compatibility paths must pass before production service replacement.

On this machine trace setup already works (Manager just used old mam wait and it exited for agent completion and new message), so no unnecessary app-server restart. For fresh installs, retain required persistent trace setup; if applying settings actually requires restarting existing App Server, retain user's CLI yes-confirmation before killing it and clearly nonzero/incomplete on declined/unverified restart. Do not kill/restart production App Server or install globally from your task. Manager handles final installation. Keep source-checkout fix8ad4220. Do not repeat6-turn liveprobe solely for restoring tested wait code; final install will execute required real acceptance once. Commit restoration separately, combined CPU/subprocess tests and exact report. Coordinate only through published task/Manager; no new wait design or public flags.
# Both runtime follow-ups now committed

Runtime owner delivered23f9024 plus9ee6300; the latter restores optional wait CLI/storage/runtime/tests with explicit active-wait guard and final same-agent wait lock before daemon delivery. Cherry-pick9ee6300 after23f9024 into your combined tree for full final installer/wait compatibility validation. Do not duplicate source runtime commits. Current integration branch contains both plus8ad4220 and Manager docs. No extra real6turn probe in your task; final production install owns that acceptance.
# Final review blocker: preserve unmarked user shell configuration

Independent final reviewd51d8598 BLOCK on a05aff6: restored update_bashrc filters exact RUST_LOG/LOG_FORMAT export lines anywhere outside MAM markers. An unmarked user conditional block containing those lines is stripped, becomes empty and its settings are moved to global MAM block. Backup does not satisfy preserving unrelated config. Read d51 published report for exact reproduction. Manager accepts this as a necessary fix.

Change update_bashrc so only a complete exact known installer-owned marked block is replaced. Preserve all unmarked user lines including identical exports inside conditional blocks. Unknown/malformed marker content must fail clearly or remain untouched; do not silently remove it. Add meaningful regression for the unmarked conditional case and validate resulting bash syntax/idempotency. No broader installer refactor, no production shell/App Server/daemon modification, no extra live model test. Commit this narrow fix separately, rerun relevant/full CPU checks, publish final report then end turn. Existing all187 tests/real6turn receipt remain valid for their old candidate but do not substitute for this fix.

Source report:

# 主动唤醒安装与可选 wait：d51 修复后的组合候选

实施 worktree：`/mnt/public/xcj/Projects/workspace/e7183b34-6d86-4394-ada8-675f54b56c42/multi-agent-manager`，分支：`task/e7183b34-6d86-4394-ada8-675f54b56c42`。

## d51 blocker 修复

新提交 `e7b3f57 fix: preserve unmarked shell trace settings` 将 `update_bashrc()` 的所有权边界收紧为完整且逐行完全匹配的 MAM 标记块：

- marker 外的内容不再按 `RUST_LOG` 或 `LOG_FORMAT` 文本过滤。用户未标记的 export、条件块和其他 shell 内容保持原样。
- 只有恰好一对 marker 且内容等于安装器当前完整 block 时才会替换为 canonical block；不完整、多个或内容未知的 marker 块会明确非零退出，原 `.bashrc` 不写回。
- 新回归复现 d51 的条件块：两个相同 export 保持在条件内，输出经 `bash -n`，第二次运行字节一致且不新增 backup。另有未知完整 marker 与 installer 门禁回归，验证不改写该文件且不会调用 service。

## 组合交付

- `8ad4220`：clean-checkout 测试的源码导入路径。
- `fa530a0`：wait compatibility、trace setup、PATH 与 installer 门禁恢复。
- `b7d2c57`（Runtime `23f9024`）：detached daemon 固定从调用方 runtime 导入。
- `5ecde14`（Runtime `9ee6300`）：可选 `mam wait` CLI/storage/runtime 与 active-wait delivery guard。
- `e7b3f57`：本次仅限 shell 配置所有权的修复。

## 验证

```text
.venv/bin/python -B -m unittest discover -s tests -p 'test_wait_compat.py' -v
33 tests, OK

.venv/bin/python -B -m unittest discover -s tests -p 'test_wake_compat.py' -q
26 tests, OK

.venv/bin/python -B -m unittest discover -s tests -q
188 tests, OK (73.920s)

bash -n scripts/install.sh
git diff --check
py_compile（修改的测试）
all passed
```

本轮未运行额外六 turn liveprobe，未做全局安装，也未触碰生产 App Server、service、任务、线程或 GPU。候选已准备接受独立的 d51 targeted recheck。
# Independent targeted final review: shell configuration preservation

Prior full reviewd51d8598 is archived with its confirmed blocker and187-pass evidence; you did not implement this fix. New registered task/workspace. Read MAM AGENTS and create mam workspace add --repo multi-agent-manager --base e4bc982 (resolve full hash), then read repo development instructions. Model gpt-5.6-terra/max.

Final integratione4bc982 adds installer source e7b3f5785e1ed98556e6815d255aa9d7ee80de5c to previously reviewed a05aff6. Only remaining accepted blocker was update_bashrc deleting unmarked user exports. Independently reproduce that the exact original unmarked conditional case is now preserved, resulting shell parses, reinstall is idempotent, unknown/malformed/duplicate marked blocks fail without rewriting the original file or touching service. Check exact delta for regressions; run relevant wait/wake installer tests. Earlier runtime/source isolation/wait coexistence/docs/full187 checks remain accepted, no need to repeat unrelated audits; source now188 full tests PASS. Manager actual installation will run the full suite and real6turn probe.

No live App Server/model turns, global install, production shell/service/threads, robot or GPU actions. Use owned temporary fixtures only. Publish concise exact-candidate PASS or concrete remaining blocker, prior acceptance dependencies, tests and limits. Clean all own pycache/temp files before final report, leave worktree clean. End turn after delivery; Manager merges/installs only after approval. User is away for dinner: do not act as user's confirmation for App Server restart.
