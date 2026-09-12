# 最终复核：主动唤醒安装与代码来源隔离

Review source delivery (source TASK-ID: e7183b34-6d86-4394-ada8-675f54b56c42):
{
  "task": "e7183b34-6d86-4394-ada8-675f54b56c42",
  "commits": {
    "multi-agent-manager": "8ad4220f9e050bc89a341871aae8b39661911125"
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

Source report:

# 主动唤醒安装与兼容性验收：完成

交付代码位于 `task/e7183b34-6d86-4394-ada8-675f54b56c42`：

- Runtime 组合提交：`9b7c2b2`、`dec9a09`。
- 安装器/兼容性/liveprobe：`9d753d7`、`59729b1`、`f5d22d2`、`322e7af`、`8ad4220`。

最后一个 clean-checkout 集成修复 `8ad4220` 让安装器的 `run_tests()` 在仅用于测试的子 shell 中将当前 checkout 置于 `PYTHONPATH` 首位。这样测试父进程和由 `start_service()`/`_spawn_service()` 启动、且 cwd 已切到 fixture `MAM_ROOT` 的 detached daemon 都导入当前源码；这项环境设置不会进入后续 pipx 安装或生产 service 命令。

新增回归创建无 checkout `.venv`、无 editable install 的临时 Git checkout，并使用 site-packages 中带旧 `multi_agent_manager` 的解释器。它运行安装器的实际测试阶段和真实 fresh-project detached daemon，确认 child 未执行旧包 marker 且可 ready/stop。修复前同一场景稳定得到 `detached service did not signal verified startup readiness`；修复后通过。

`liveprobe` 现在在启动 fixture service 前，依次为 Manager、stopped-job executor、no-job executor、archived-job executor 创建并绑定正常 persisted thread，然后各完成一个短 baseline。新 thread 在首个 user turn 前会拒绝 `thread/resume`；因此代码在成功 `turn/start` 后立即订阅同一 thread，等待该 turn 的 `turn/completed`，再确认 `thread/read` 为 idle，最后才分页读取历史。这样不会在 active baseline 上轮询历史。

验收固定为六次模型调用：四个 baseline、一次批量 Manager task-ready 投递和一次 stopped-job executor 投递。若 idle 后 `thread/turns/list` 仍明确返回 `list_turns is not supported yet`，liveprobe 会在同一 thread 上调用 `thread/read(includeTurns=true)`，把两个结果写进 receipt 后非零退出，不会新增 baseline。安装器证据校验和安装文档已同步为六次调用；liveprobe 仅由安装器调用，`wake_compat.require_compatible()` 保持零模型轻量检查。

验证通过：

- `.venv/bin/python -B -m unittest discover -s tests -q`：109 passed（67.866 秒），包括新增 clean-checkout daemon-source-import 回归。
- 该回归单独运行：通过；`bash -n scripts/install.sh`、`py_compile`、`git diff --check`：通过。
- 真实隔离验收：`wake_compat` 对随机未知 thread 的 `thread/read`、`thread/resume`、`thread/turns/list`、`turn/start` 均获明确拒绝，`model_requests=0`；随后 liveprobe 返回 `PASS`，`model turns: 6/6`。

真实 fixture receipt（全部为本任务创建的专用资源）：

| role | thread | baseline / delivery turn |
| --- | --- | --- |
| manager | `01a094d1-8ebd-7c91-b61a-891c3ca4cc3c` | baseline `01a094d1-8fdd-7d92-a911-2907c0040116`; Manager delivery `01a094d1-c767-7543-b425-27c7f1569411` |
| stopped-job executor | `01a094d1-8f08-7c40-98a5-c67c2c3c0e28` | baseline `01a094d1-9a72-7a43-8a99-6e524d7cb42d`; stopped-job delivery `01a094d2-3cd4-7280-b759-899064f422f1` |
| no-job executor | `01a094d1-8f51-7963-b233-cbfbe610293b` | baseline `01a094d1-a6e8-7c93-ab46-aa26d0a3eaf4` |
| archived-job executor | `01a094d1-8f94-7b71-8560-6b9a467d65ec` | baseline `01a094d1-b542-7291-8d38-8698cbb907ea` |

Fixture task IDs：job `49567f34-f948-491f-9c41-7e48e165fc6d`、idle `1e8f384e-c8a8-4421-9b94-39968c90e7dd`、archived `f0e7ed1d-83cc-4abb-b5de-785f9670e64e`。其 stopped job 为 `dafb30c1-6bbd-4ede-8560-78ece113fd44`，预先 archived job 为 `e76a294a-a864-4061-b921-1821ebeb76cb`。历史计数在 stopped job 前为 `{manager: 2, job_executor: 1, idle_executor: 1, archived_executor: 1}`，之后及两个 quiet window 均为 `{manager: 2, job_executor: 2, idle_executor: 1, archived_executor: 1}`。这确认了两条准确投递、idle/archived executor 未收到 scheduler turn，以及无重复 start。

清理完成：fixture service 已停止；两个 fixture job 和三个 fixture task 已归档；四个上表 persisted thread 均已 archive；marker-owned fixture 根已删除。此次 clean-checkout 回归的临时 checkout、旧包解释器和 fresh daemon 均在测试结束时删除/停止。未安装到全局、未启动/停止生产 service，未改动生产任务、用户 thread、远端任务或 GPU；按本次 CPU setup 修复要求，未重跑真实 6-turn liveprobe。

必要的历史清理收据：早期 ephemeral 尝试的已记录 baseline turn 为 `01a09498-344a-78c0-a6f6-718270589652`，唯一在原 stream 关闭后可确认的 thread ID 为 `01a09498-2cfc-7da1-a26a-a313733c2e23`；仅带 turn ID 的 interrupt 被 API 以缺少 `threadId` 拒绝，其他三个 ephemeral ID 未被旧实现保存，不能通过 API 安全重建，未对其猜测操作。随后两个失败的 persisted fixture 在 baseline 前/期间遇到 API 时序限制：已知 Manager turn `01a094c8-13ef-7921-a22f-26dabc2230a0` 被仅针对该已知 ID interrupt 后 archive；其余未 materialize thread，以及零模型 resume 失败 fixture 的四个 thread，archive 均明确返回 `no rollout found`。这些 API 无法确认的未 materialize IDs 没有被 unarchive、resume 或再次操作。最终通过 fixture 的全部资源已有明确 archive 回执。
# Final review: proactive wake installation and package source isolation

Your previous review3c97bd4f is archived with its valid blocking report preserved. New TASK-ID/workspace for this final review. Read MAM AGENTS, create mam workspace add for multi-agent-manager at current integration7074917, then read its development docs. Independent review only; no implementation, remote/GPU, global install, production service, or real model turns. Model gpt-5.6-terra/max.

Current candidate7074917 includes20ff584 plus installer clean-checkout fix8ad4220. Runtime ownerbc998553 is implementing the separately confirmed production daemon MAM_ROOT/cwd shadow fix; do not report the already-assigned old bug as a new finding or approve final before receiving that final commit. Manager will publish the exact runtime fix here. Meanwhile independently review installer source-import regression, installer startup/cleanup/PATH and actual6-turn acceptance receipt from e718. Prior runtime transition and concise README/AGENTS review already PASS and need not be redone without a new concern.

Final acceptance: source checkout without editable .venv runs current code in test parent and real detached child; current installed caller runtime starts even if state MAM_ROOT contains an older/shadow package. No path/PYTHONPATH hijack of selected runtime. Preserve per-project lock/Manager/jobs/pending data. Installer supports user's fresh clone + apt pipx + bash scripts/install.sh flow; behavioral tests before stopping production service; no version allowlist, bypass or unnecessary App Server restart. Fixtures operate/clean only owned paths/processes/threads and report actual failure nonzero. Use actual CPU subprocess reproduction for import isolation, not only mocks. Run full final combined unittest suite once both fixes are present; source reported previous108 plus new clean-checkout regression109. No extra real liveprobe until Manager's actual install.

Publish concise final report with reviewed full commit, independent repro/tests and verdict. If blocked, state exact reproducible issue and publish/end turn; Manager handles follow-up. Clean pycache and temporary fixture artifacts before final publication, leave worktree clean for archive. Do not include abandoned proposals in report.
# User scope update: wait is retained

Latest user decision supersedes earlier deletion requirement: keep mam wait, wait list, wait stop manager/--agent as optional in-turn waiting; normal end-turn/proactive wake is default. Runtime owner restores stable wait CLI/runtime/tests; installer owner restores wait_compat/setup/tests and must preserve working message/manual cancellation. Daemon still only wakes job/task events, no received-message/timeout/cancelled events. Manager updates README/AGENTS after code ready.

Final review must include coexistence: active waiter cannot receive an extra daemon turn/start, pending work remains visible and is resolved after actual handling, unchanged handled condition cannot trigger duplicate model calls. Current trace/setup cannot be deleted by install; fresh install must validate both features and require user's yes before any necessary existing App Server restart. Runtime source-import fix is still necessary and should remain a separate reviewed change. You may continue installer/import review while retention changes proceed; final approval waits for final integration SHA provided by Manager, no need to re-report known not-yet-restored files as new blockers.
# Daemon import fix available for independent reproduction

Runtime source23f9024 is integrated as a6c02b1 atop7074917 and Manager optional-wait docs289d2c9. Merge current integrationa6c02b1 into your registered worktree for source-vs-state import reproduction. Optional wait restoration by both owners is still in progress, so final whole-candidate verdict waits for later SHA. Do not cherry-pick old review branches containing project .tasks. New README/AGENTS wording is now also available to check: default normal turn end, optional wait usage only; concise user-facing usage, implementation details kept out.
# Optional wait runtime restoration committed

Runtime9ee6300 (after23f9024) is committed and integrated into codex/proactive-wake-integration. Restore includes wait storage/CLI/runtime/tests and explicit wait-record final lock guarding daemon turn/start. Inspect the current integration head for source/wait coexistence now; installer wait_compat/setup changes still pending. Source reports153 CPU tests passed; final combined count includes installer restore. Installer final SHA will follow. Do not add new model tests; independently verify the wait-start race/lock and handled-event suppression as final requirements.
# Final combined candidate a05aff6

Integration a05aff6 now includes runtime23f9024/9ee6300, installer8ad4220/fa530a0, Manager optionalwait docs289d2c9 and previous approved wake code. Merge this exact candidate (resolve full SHA locally) for final whole-project review and full CPU suite. Installerfa530a0 restores old wait_compat and tested trace installation alongside proactive acceptance; source final CPU run is underway. Runtime implementation taskbc998553 has been archived after delivery; all commits are retained in integration and its report, no need to access removed source workspace.

Do final behavior/README/AGENTS/install/design consistency and failure-path review on a05aff6, including no unnecessary App Server restart on an already compatible installation, explicit yes before an actually required restart, and bounded visible failure if unverified. User is away for dinner; Manager can prepare but cannot answer a required restart confirmation on their behalf. Report actionable blockers or final PASS; do not run real model turns, install globally or operate production service.
