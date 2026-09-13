# native multi-agent v2 wake rejection fix

代码交付包括核心 runtime 修复
`46af8c2afd3790a8e1d0538e4f624170753e67fc`，以及本次终审修订
`fda59da93c2ba5bc74fd130b6c5ce0de33b3bad3`（branch
`task/b49a5b40-1d18-40e6-bc28-c5c57dc011f3`，worktree
`/mnt/public/xcj/Projects/workspace/b49a5b40-1d18-40e6-bc28-c5c57dc011f3/multi-agent-manager`，基线
`bc8726f3e2f13351c52650f03bc88bd76a68ed25`）。本次待真实验收的 source commit 是
`fda59da93c2ba5bc74fd130b6c5ce0de33b3bad3`。

诊断已作为项目记录提交：`981c165456be2ffbea2679d0200c6bfb9e5bd175` 的
`diagnosis.md`；它引用同目录已保存的 15 条 `incident_snapshot.json` 证据。确认根因是原生
multi-agent v2 child 对 direct `turn/start` 的精确拒绝，不是 PID/job 探测失败。

核心 runtime 已完成并经独立 review 条件性 PASS：

- 仅将精确错误 `direct app-server input is not allowed for multi-agent v2 sub-agents` 的 executor
  `job_stopped` delivery 转为持久 `blocked`，写入
  `failure_kind`/`block_kind: unsupported_multi_agent_v2_direct_input` 并取消 retry deadline；一般 RPC
  rejection 与 transport-uncertain 仍沿原有重试语义。
- 每个仍有效的 blocked source 生成一个按 source signature 去重的
  `manager_native_followup`。消息包含 TASK-ID、JOB-ID、executor、精确错误及使用 parent-native
  `collaboration.followup_task` 的动作；Manager active/paused/unknown/wait、restart、rebind/archive stale、
  Manager 缺失/self-recipient 与递归保护保持原有语义。
- README 与设计文档已经明确：只有有效且不同于 executor 的 Manager 才会收到升级；防御性
  `manager == executor == recipient` 的精确 `job_stopped` source 可以保持 `blocked`，但绝不创建
  self-escalation。executor `active` 不表示 stopped job 已收尾；Manager 收到通知先核对执行者状态和
  report，再决定是否原生 follow-up。

本次仅收紧真实 native-v2 fallback 的隔离验收工具和 runbook，未修改产品 runtime：

- `prepare` 的全部 Git 子进程经过统一 helper：移除继承的所有 `GIT_*`，禁用 system/global config，使用
  fixture-owned 空 global config/template/hooks，并以 `core.hooksPath` 与 `--no-verify` 固定 commit 行为。
  初始化后同一净化环境精确核验 fixture `state` 的 top-level 与 absolute git-dir。
- fixture 的全部 MAM CLI 统一为
  `SOURCE_ROOT/.venv/bin/python -I -m multi_agent_manager.cli`。`prepare` 在 `-I` 下实际导入 package、
  CLI 和 wake runtime，要求三个 module path 都属于 source worktree，并在 receipt 记录 source Python、
  controlled CLI、module paths、source Git top-level 和准确 HEAD。
- runbook 在 fixture `service stop` 后有 60 秒有界 `service status` 轮询，确认 `running: false` 后才启动；
  restart checkpoint 要求 PID 变化和至少 `baseline + 2` 个 post-restart cycles，且重验精确 pending payload。
- blocked/restarted/delivered receipts 持久化 source/escalation signature、delivery、attempts、error、
  `source_event`、action 和 `accepted_at`。delivered 将 baseline 的 TASK/JOB/Manager/child/signatures 与
  当前 state 精确对比，并要求人类 `[MAM Message]` attestation 包含精确 rejection。
- archive 必须以 `delivered.json` 为 baseline，按两个 signature 在 history 中精确定位并重验 blocked 与
  accepted 字段、`condition changed or resolved` resolution 和 active-event 消失。新增受控
  `record-child-archive` receipt：真实 native child 先运行 controlled `mam job archive`，该命令再核验 fixture
  job archive note/state 并留下 TASK/JOB/child/`mam job archive` attestation；不再以非空 report 推断 child
  操作。

本次有界、无模型、无 App Server 临时验证：

```
.venv/bin/python -B -m py_compile scripts/native_v2_fallback_acceptance.py
.venv/bin/python -I scripts/native_v2_fallback_acceptance.py plan
.venv/bin/python -I scripts/native_v2_fallback_acceptance.py --help
git diff --check
git diff --cached --check
git show --check fda59da
```

在自动删除的临时目录中，以恶意 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、`GIT_CONFIG_*`、
`GIT_TEMPLATE_DIR`、`GIT_EXEC_PATH` 和 shadow `PYTHONPATH` 调用 `prepare`：外部临时仓库的全部文件和 hook
marker 均未变化；fixture Git top-level/git-dir、source module paths、source CLI 与 source commit 均正确。
另以 shadow `PYTHONPATH` 调用受控 fixture CLI，`-I` 仍从 source worktree 导入。合成 fixture state 覆盖
blocked → restarted → delivered → child archive → archived 正例，并确认错误 escalation error、仅一个
post-restart cycle、错误 history signature 都被拒绝；runbook 的 11 个 Bash 代码块通过 `bash -n`。

此前核心 runtime 的完整回归保持其独立验证结果：

```
.venv/bin/python -B -m unittest discover -s tests -v
Ran 215 tests in 81.308s
OK
```

本次没有修改 runtime，因此未重复该 215 项套件。未运行真实 fixture、未通过 MAM 创建真实 fixture task/job、
未启动或停止任何 fixture/production scheduler、未安装、未重启 App Server 或 production MAM daemon，也未调用原生
follow-up。真实 native-v2 链路仍待本次差异复审通过后由 root Manager 安排。
