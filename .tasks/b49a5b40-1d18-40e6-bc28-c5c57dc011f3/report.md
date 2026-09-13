# native multi-agent v2 wake rejection fix

代码交付：`46af8c2afd3790a8e1d0538e4f624170753e67fc`
（branch `task/b49a5b40-1d18-40e6-bc28-c5c57dc011f3`，worktree
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
