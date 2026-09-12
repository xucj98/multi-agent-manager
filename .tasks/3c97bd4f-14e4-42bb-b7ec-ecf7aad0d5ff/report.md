# 阶段性独立复核：runtime 三项状态转换修复通过

## 结论

`45614a60f63517eff3075381c697d370f09bdccc` 关闭了此前报告的三个 runtime 阻断问题。该提交已在独立 reviewer worktree 中以 `3858047b176e66a316232ab60f700a0edf9f8e05` cherry-pick 到 `f114fd6d7cc39f65bc76da9e782509bc1a256704` 之上；工作树干净，未修改实现或测试。

本轮仅批准核心 runtime/docs 的这三项修复。最终整个主动唤醒功能的安装器和隔离 liveprobe 验收仍等待 installer 的组合候选提交，不能据此代替那一轮审阅。

## 三项反例复核

1. **interrupted 后恢复：通过。** `blocked` 的 stopped-job 事件在收件人再次被批量元数据确认 `idle`/`notLoaded` 后，仅调用 `latest_turn` 重查，不会在重查时 resume。只有观察到不同 ID 的 `completed` turn，才恢复为 `pending` 并在同一周期按正常 preflight 投递；边界未变、仍 interrupted 或收件人 active 时保持阻断。独立 fixture 走完 interrupted → 新 completed → idle，最终得到一次 owner `turn/start` 和 `delivery=accepted`。

2. **source metadata 瞬时 unknown：通过。** `_desired_events` 现在把同代 `task_ready` 标为 inconclusive，`_reconcile_events` 保留已存在的 pending/accepted 事件而不从 unknown 观察新建事件；发送前复核也将 unknown 保留为可见条件错误。独立 fixture 验证 accepted 事件跨一次 unknown 后仍使用原 signature，source 回到 idle 后 Manager `turn/start` 总数仍为 1。新增测试还覆盖 Manager busy 时的 pending 事件。

3. **明确 RPC 拒绝与 response loss：通过。** 收到 JSON-RPC `error` 的 `AppServerEventStream.request` 现在抛出 `AppServerRpcError`（仍为 `AppServerEventError` 子类）。发送后的该异常持久化为 `delivery=rejected`、`failure_kind=explicit_rpc_rejection`，可按退避重试且不进入 uncertain 的 turn-boundary 歧义判断；连接/响应丢失仍为 `uncertain`，保持原有 changed-boundary → `ambiguous` 保护。独立 fixture 在拒绝后插入无关 completed turn，事件仍为 rejected，重新 idle 后才成功投递。

未发现这三项修复引入新的核心阻断问题。公开生命周期接口未变：`start_service(config, manager=None)`、`stop_service(config)`、`service_status(config)` 保持原形。

## 验证

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

结果：109 passed，28.495s。

```bash
.venv/bin/python -B -m unittest -v \
  tests.test_wake_runtime.WakeRuntimeTests.test_interrupted_event_recovers_only_after_new_completed_turn_and_idle_recipient \
  tests.test_wake_runtime.WakeRuntimeTests.test_accepted_task_ready_survives_unknown_source_without_duplicate_manager_turn \
  tests.test_wake_runtime.WakeRuntimeTests.test_task_ready_pre_send_unknown_source_retains_pending_event \
  tests.test_wake_runtime.WakeRuntimeTests.test_explicit_rpc_rejection_retries_without_response_loss_ambiguity \
  tests.test_job_runtime.EventStreamTests.test_explicit_rpc_rejection_has_a_distinct_compatible_error_type
```

结果：5 passed，0.060s。

此外，在临时目录中独立构造 `Store`、agent metadata probe 和 stream，重走上述三条状态序列，结果依次为 `accepted`、单次 Manager start、`rejected → accepted`。临时目录在进程退出时清理。

## 文档与范围

本 follow-up 仅补充设计文档中 interruption recovery、unknown source 保留和 RPC rejection 的持久化语义；表述与代码一致。`AGENTS.md` 和 README 未在此提交改变，先前的简洁性结论仍成立：普通执行者可直接结束 turn，task/report 编辑与 publish 流程可发现，服务设计细节留在 design 文档。

没有启动生产服务、真实 App Server/thread、机器人或 GPU，也没有运行 installer/liveprobe。最终组合候选提交到位后，应在同一 reviewer worktree 对安装和隔离 live acceptance 单独完成最终结论。
