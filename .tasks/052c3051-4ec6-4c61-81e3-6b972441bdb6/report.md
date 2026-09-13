# 独立代码审核：native multi-agent v2 wake rejection 修复

审核对象为 `46af8c2afd3790a8e1d0538e4f624170753e67fc`，相对基线
`bc8726f3e2f13351c52650f03bc88bd76a68ed25`。审核 worktree 为
`workspace/052c3051-4ec6-4c61-81e3-6b972441bdb6/multi-agent-manager`，未改动作者
worktree、生产 daemon、App Server 或真实用户线程。

## 结论

**条件性 PASS。** 未发现会让正常 executor 路径继续盲重试、丢失 Manager fallback、或把普通
RPC/transport 语义退化的功能性缺陷。精确 native-v2 拒绝、旧 state 升级、持久 escalation
签名和 stale 清理的 cycle 顺序均与既有 accepted/uncertain/interrupted 状态机相容。

有一处非阻塞 **P3 文档一致性问题**，建议在合入/上线说明前修正：

- [docs/task-management-design.zh-CN.md:141](../../docs/task-management-design.zh-CN.md#L141)
  写着该特例“不适用于 Manager 自己的待办”，但
  [wake_runtime.py:1305](../../multi_agent_manager/wake_runtime.py#L1305) 到 1311 会把
  `manager == executor == recipient` 的精确 `job_stopped` 拒绝持久化为 blocked；只有
  [wake_runtime.py:904](../../multi_agent_manager/wake_runtime.py#L904) 到 912 抑制
  self-escalation。现有
  [test_wake_runtime.py:828](../../tests/test_wake_runtime.py#L828) 到 838 也明确断言这个行为。
  正常 CLI 会拒绝把已登记的 Manager 绑定为 active task，因此这是防御性/异常记录边界；但文档
  应说明“source 仍可 blocked，但不创建 Manager 对自身的 escalation”，README 中“会投递升级消息”
  的无条件描述也应加同一例外。

另外确认一个需要明确给上线操作方的保守语义：如果外部的 parent-native followup 已使 executor
变为 `active`，但 stopped job 尚未归档且该 escalation 还未被 Manager 接受，Manager 在转为
`idle` 后仍会收到这一次 escalation。`manager_native_followup` 的 currentness 只检查 task、
executor binding、job/note/title，而不把 executor 的 active 状态当作完成；它在 job/task archive
或 rebind 时才 stale。这避免把无关 active 误判为收尾完成，但说明 blocked/pending 不能被解释为
“尚未有任何人开始处理”。建议把这一点写入运行说明或上线验收记录。

## 审阅证据

- `git diff --check bc8726f..46af8c2` 与 `git show --check 46af8c2` 均通过；变更仅包括
  README、安装/设计文档、`wake_runtime.py` 和 wake runtime 测试。
- 独立运行规定命令：

  ```text
  .venv/bin/python -B -m unittest discover -s tests -v
  Ran 215 tests in 81.356s
  OK
  ```

- 使用临时 Store/Fake App Server 做了额外状态机复现，未接触真实 App Server：
  - 已知错误带额外后缀仍为 `rejected/explicit_rpc_rejection`，不会被宽泛识别；
  - 同文本的 `AppServerEventError` 保持
    `uncertain/response_loss_or_transport`；
  - archive 和 rebind 都将 blocked source 与其 `manager_native_followup` 同时移入 history；
  - self-recipient 仅 blocked、不递归升级；executor 已 active 但 job 未归档时上述一次 pending
    escalation 仍会在 Manager idle 时投递。

实现层面的检查还确认：旧 `rejected/explicit_rpc_rejection` 会在 retry 前升级；Manager
active/paused/unknown/optional wait 不被打断；相同 source 在重启后复用签名；新 stopped job 有独立
signature；Manager 缺失、self-recipient 与 Manager delivery 的普通 RPC rejection 不会递归生成
fallback；`service status` 可合法同时为 `running: true`、`healthy: true`、`status: pending`。

## 上线前最小真实验收

215 项测试和安装器 liveprobe 只验证模拟路径或**普通 persistent thread**，不能宣称 native-v2
direct child input 已恢复。真实隔离验收应分别留下三段证据：

1. 现有普通 persistent-thread liveprobe 继续通过，证明常规 scheduler delivery 未回归。
2. 在隔离 fixture 中使用真实 native multi-agent v2 child 和已登记 stopped job，确认实际的精确
   rejection 后 source 持久化为 blocked，两个 cycle 和一次 scheduler restart 均不再向 child
   `turn/start`；Manager 仅在 idle 时收到一次包含 TASK-ID/JOB-ID/executor/error 的 followup。
3. 由该 fixture 的真实父 Manager 使用 `collaboration.followup_task` 激活 child，随后归档 job，确认
   不再产生旧 escalation。该证据只能证明 fallback 协调成功，不能称为 direct child input 恢复。

本审核未安装或重启生产组件、未发送实验通知，也未调用 task archive。
