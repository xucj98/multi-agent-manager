# 独立 review：C 首次 infer 预算修复与评测台账

## 结论

**通过，准入范围仅为新的 C matching smoke2；尚未直接准入 formal100。**

bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5` 满足本轮修复边界：

- `policy_first_infer_timeout` 在 `SchedulerBase` 中转换并拒绝非正或非有限值；默认仍为既有 30 秒。
- 只有一个 scheduler process 的第一个真实 `infer` 会在显式非默认值时传入 `WebSocketClient.call(..., timeout=...)`；后续调用仍使用 client 默认 30 秒。
- `get_metadata` 走独立 RPC，既不走 `_call_policy_infer`，也不会消耗首次 infer 标记。`OpenPiSimulationScheduler` 已把该参数传到 base，现有 `scripts/run_scheduler.py` 会把 scheduler YAML 的 `params` 原样传入。
- diff 只涉及 `scheduler/base.py`、`scheduler/openpi_simulation.py` 和一个 scheduler 单测；没有改 policy 动作、memory schema、seed、horizon、checkpoint 或 transport 默认值。

异常边界也符合当前运行语义：policy 返回非 `ok` 后首次标记已经消费，下一次 retry 使用普通 30 秒调用；transport `TimeoutError` 继续向上传播，而 `SchedulerBase.run()` 不捕获它，所以 scheduler 正常收尾并失败退出，未吞掉超时或同进程自动重试。若以后新增对该异常的同进程重试，应在 call 前消费标记并新增回归测试；这不影响当前没有此恢复路径的 smoke 准入。

建议在本次 C smoke 的 scheduler 配置中**显式固定**：

```yaml
params:
  policy_first_infer_timeout: 90.0
```

90 秒是本轮的运行上限，不设无限等待，也不改变后续 30 秒预算。它是原预算的三倍，给已观测到的 27.232250690 秒首次 XLA 编译留出约 63 秒调度余量，同时仍能及时暴露卡死或持续服务故障。

准入前仍须将 C 运行清单/实际 worktree 固定为 bridge `f962663`，记录上述显式参数和三库 SHA。对原来的 put-back t+30/s0、rearrange t+30/s0 两项分别使用新的 result leaf 重做 video/no-video 各一集的 smoke2；旧失败 leaf 保留且不可覆盖。仅当每项自身 smoke 通过产物、metadata、scheduler exit 和进程收尾检查后，才按既有门禁启动其同 checkpoint 的 formal100。

## 诊断证据审查

两份保留失败 leaf 的 scheduler traceback 都来自旧 bridge 在第一个
`_policy_client.call({"cmd": "infer", ...})`，底层报 `TimeoutError: timed out in 30.0s`；没有把它们记为 0 分或 formal 结果。单模型串行诊断的原始 policy log 确有首次 `jit(fun)` XLA compilation `27.232250690s`，并以默认 30 秒 scheduler 预算完成 2/2。

这些证据足以支持为冷启动首次调用给一个有限、一次性的余量；它们**不能严格证明**原先两个并发 smoke 的根因就是并发编译。冷启动编译、服务调度和其他阻塞点仍是待后续基础设施诊断区分的候选，故本结论没有把模型或 memory schema 归为故障原因。

## 本机验证

在独立 bridge review tree 上执行：

```text
PYTHONPATH=/mnt/public/xcj/Projects/openpi/packages/openpi-client/src \
  .venv/bin/python -m pytest -q tests/scheduler tests/transport/test_websocket.py
101 passed, 1 skipped in 28.25s
```

另以 CPU mock 直接核对：metadata 查询后首次 infer 仍取得 90 秒；首个非 `ok` 响应后第二次调用无 timeout 参数；`TimeoutError` 不被 helper 吞掉。两份提交均通过 `git diff --check`。未启动 GPU、服务或机器人，未修改 C 端任何文件。

## 台账抽核：`564024207898fef1d5cabee48550a8aebf233529`

该提交只更新 `experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`，diff-check 通过。

- 本机实际结果目录的 `_result.txt` 与 `final_review.json` 分别确认 put-back full t+1/s0 为 **69/100**、`0` runtime error、100 episode；rearrange full t+30/s1 为 **92/100**、`0` runtime error、100 episode。两处对应 checkpoint 目录均存在。
- C 端抽核 put-back t+30/s0、rearrange t+30/s0、rearrange serial-lag30/s0、rearrange no-memory/s0 四条相对路径；每条的 `_CHECKPOINT_METADATA`、`params`、`assets`、`metadata` 均存在。
- 两份 `scheduler_first_infer_timeout` smoke leaf 仍保留；对应 C formal leaf 均不存在。台账没有把失败 smoke 计作成绩。
- 台账明确区分已完成的两份完整 100、12 个已传但未产生新 formal 分数的 checkpoint，以及当时仍在训练、不可传输/不可评的 B 组快照。它也明确禁止将不同任务的 69 与 92 相减得出 Q2 结论，且把跨 schema、B 组范围和 paired difference 留待同协议完整 100 条结果。

## 工作区与交付

- bridge review tree：`/mnt/public/xcj/Projects/workspace/03d538a0-f68e-45e6-9758-8539048b32d7/robot-bridge`，从 C 端只读 SSH 导入并审查精确对象 `f9626636c4776d8eb15f9c556775cb2d12c000e5`；审查后已按 MAM 交付约束切回 `task/03d538a0-f68e-45e6-9758-8539048b32d7`，本地 `refs/review/f962663` 保留该精确对象，工作区干净。
- RMBench review tree：`/mnt/public/xcj/Projects/workspace/03d538a0-f68e-45e6-9758-8539048b32d7/RMBench`，task branch 基于 `564024207898fef1d5cabee48550a8aebf233529`，工作区干净。

本 review 未产生代码提交；以上 smoke 准入结论和台账抽核结果是本任务交付。
