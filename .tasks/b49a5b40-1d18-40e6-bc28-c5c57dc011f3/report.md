# native multi-agent v2 wake rejection fix

代码交付：核心修复 `46af8c2afd3790a8e1d0538e4f624170753e67fc`；本次 P3 文档修订与隔离验收预案
`95c99f8c5a5ea4eee9dc88139c334f37eb903e5d`（branch `task/b49a5b40-1d18-40e6-bc28-c5c57dc011f3`，worktree
`/mnt/public/xcj/Projects/workspace/b49a5b40-1d18-40e6-bc28-c5c57dc011f3/multi-agent-manager`，基线
`bc8726f3e2f13351c52650f03bc88bd76a68ed25`）。

诊断已作为项目记录提交：`981c165456be2ffbea2679d0200c6bfb9e5bd175` 的
`diagnosis.md`；它引用同目录已保存的 15 条 `incident_snapshot.json` 证据。确认根因是原生
multi-agent v2 child 对 direct `turn/start` 的精确拒绝，不是 PID/job 探测失败。

完成项：

- 仅将精确错误 `direct app-server input is not allowed for multi-agent v2 sub-agents` 的 executor
  `job_stopped` delivery 转为持久 `blocked`，写入
  `failure_kind`/`block_kind: unsupported_multi_agent_v2_direct_input` 并取消 retry deadline；已有旧版
  `rejected` state 会在下一 cycle、重试前升级。
- 每个仍有效的 blocked source 生成一个持久、按 source signature 去重的
  `manager_native_followup`；同一 Manager 的多个 JOB-ID 由既有 recipient batch 合并。消息包含
  TASK-ID、JOB-ID、executor、原始错误及使用 parent-native `collaboration.followup_task` 的动作。
  Manager active/paused/unknown/optional wait、restart、rebind、archive、self-recipient 和递归拒绝
  均保留或清理为既有语义。
- `mam service status` 可同时表达 `running: true`、`healthy: true` 和 `status: pending`，由 blocked
  event 与 `native_v2_wake_blocked` diagnostic 区分 daemon 正常和 delivery 受阻。
- 更新 README 操作提示、详细状态设计和安装验收边界：普通持久 thread liveprobe 通过不代表原生
  v2 child 可接收 direct input。

验证：

```text
.venv/bin/python -B -m unittest discover -s tests -v
Ran 215 tests in 81.308s
OK
```

新增 wake 回归覆盖精确拒绝、旧 state 升级、一次升级/合批、新 stopped job、Manager
active/unknown/paused/wait、rebind/archive stale、Manager missing/self-recipient、防递归、状态展示；
既有普通 RPC rejection 与 transport-uncertain 回归仍通过。`git diff --check` 和提交前
`git diff --cached --check` 均通过。

未运行 production 安装、未重启 MAM daemon 或 App Server，未声称 direct v2 child delivery 已恢复。
真实 v2 链路验证留给独立 review 后由 Manager 安排。

## P3 说明与真实验收预案（未执行）

- README 与设计文档现明确：只有有效且不同于 executor 的 Manager 才会收到升级；防御性
  `manager == executor == recipient` 的精确 `job_stopped` source 仍可为 `blocked`，但绝不创建
  self-escalation。executor `active` 不表示 stopped job 已收尾；job 未归档前，同一 escalation 可保留。
  Manager 应先核对 executor 状态与 report，再决定 native follow-up，避免重复通知。
- `docs/native-v2-fallback-acceptance.zh-CN.md` 与
  `scripts/native_v2_fallback_acceptance.py` 准备了隔离验收。脚本默认仅输出 plan；它不调用 `mam`、连接
  App Server、创建 thread、发送 follow-up、安装、改 Codex DB/feature flag 或重启服务。`prepare`/cleanup
  都需确认短语，fixture 必须为新建的 marker-owned 绝对目录。
- 预案指定 root Manager `01a09657-e0f3-7352-b726-aba5bbd5d498`，只在其原生明确委派后使用既有 child
  `01a096ab-e5f3-7672-8ff3-36328d3fcfb7`（`/root/u_training_owner`）。child 只登记和 archive fixture
  短 job；root 负责 fixture task、service、receipt、task archive 与目录清理，不触碰 child 的既有 review
  task/thread 或 production state。
- 顺序要求 root 保持 active，先证实精确 blocked、两轮 cycle 与 fixture scheduler restart 都没有 child retry；
  root 正常结束 turn 后只接收一次 fallback；随后 root native follow-up child archive fixture job，并核对
  source/escalation stale。root 在 archive fixture task 前保持 active，避免普通 `task_ready` 成为第二条
  idle-time 通知。脚本从 fixture state 校验 attempts、PID/cycle、accepted receipt、history stale 与受保护
  cleanup；人类可见 `[MAM Message]` 由 root attestation 留证。

## 安装器与环境只读评估

现有调用方式是在含最近 `.mam/env.json` 的 MAM checkout 中运行 `bash scripts/install.sh`（无位置参数）；已有
bound task 而 Manager 不可确定时可用 `MAM_SERVICE_MANAGER=AGENT-ID bash scripts/install.sh`。安装器会先跑
checkout tests、pipx install、兼容性和普通 persistent-thread liveprobe，随后才替换当前项目 scheduler。

未执行安装器。已只读核对默认 control socket 存在，listener PID `4126625` 的
`RUST_LOG=off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info` 及
`LOG_FORMAT=json` 与 `scripts/install.sh` 要求完全一致；`ensure_runtime_logging` 会直接返回，不走
`restart_app_server`。所以 trace 环境不需要 App Server restart；完整安装能否通过仍未验证，因为 tests、
compatibility 与 liveprobe 均未运行。当前 pipx `multi-agent-manager` 元数据为 `0.1.0`，来源仍是
`/mnt/public/xcj/Projects/workspace/d5cb66d7-36d9-4bfc-9d01-d56befd32de4/installer-main`；本任务没有安装或
替换它，也没有改变 production daemon。

本次仅文档/验收预案修订额外通过：

```text
.venv/bin/python -m py_compile scripts/native_v2_fallback_acceptance.py
.venv/bin/python scripts/native_v2_fallback_acceptance.py plan
.venv/bin/python scripts/native_v2_fallback_acceptance.py --help
git diff --check
git diff --cached --check
```

按任务要求，纯文档小修未重复 215 项全量测试。未运行真实 fixture、安装、App Server restart、production MAM
daemon restart 或任何 production task/job 操作；请独立终审 docs/脚本后再决定 fixture 准入。
