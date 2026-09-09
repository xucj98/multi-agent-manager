task_revision: d606b3740789a1ed496f84d9bd2f462797d1078f

# bc842036：F0 / legacy RMBench simulation 独立 CPU 验收通过，可开始 GPU smoke

审查候选与工作区：

- F0 候选：`bc842036e3735390f35fe1138aa7b19f5ae2f95b`（`fix: skip terminal simulation inference in base`）。
- F0 审阅基线：`b247332`，是将该 terminal patch 合入 `fd38513` 的等价 cherry-pick；二者稳定 patch-id 同为 `d09ba4ad09d83d1181b47ec6109bb006f24ceb45`。当前审阅树 HEAD 为其后仅含 live controller 增量的 `281e0a7`；该后继不纳入本 F0 判断。
- 按任务要求只读核对的 OpenPI worktree：`/mnt/public/xcj/Projects/workspace/0bc5129d-623c-4c3d-8bce-b8c172ccca56/openpi`，`58d6f2155acc3af03017677bb3f536101e6699f4`。

本报告只放行旧 full checkpoint 的 F0 simulation CPU gate。未修改作者实现，未启动 GPU、真机或 rollout；GPU smoke/100 rollout 仍由独立 eval 任务执行。

## F0 结论

**`bc842036e3735390f35fe1138aa7b19f5ae2f95b` 通过 F0 runtime CPU 验收，F0 可进入 GPU smoke。** legacy H50/K30 selector、实际执行进度/trace，以及 terminal observation 的真实调用路径均无剩余 F0 runtime blocker。

固定的完整 eval 入口 `425afaf` 可按既定流程执行 rows **1 / 20 / 30 / 50**：每行先各 2 rollout smoke，再各 100 rollout。保留原完整 recorder 检查；不增加白名单、兼容绕过或放宽 recorder 检查。本 CPU 结论不替代 GPU rollout、视频产物或真实 recorder 验收。

## 已检查的行为

1. **旧 checkpoint 保持旧路径。** 不含 `memory_config` 的 `full_state` 不进入 `MemoryContext` / 新 schema 输入输出处理；原有 state、dense memory tail、one-hot 投影和动作切片保持 F0 可比性。legacy selector 只用于该旧 full-state 路径，新 schema checkpoint 不会借此伪造旧 metadata 语义。

2. **H50/K30 selector/progress 正确。** `last_executed` 在完整 K30 时选 model index 29（人类 row 30）；显式 index `0/19/29/49` 分别对应 rows `1/20/30/50`。每次先选择同一条 raw output row，再用于全部 legacy dense memory fields。row 50 保持模型预测，trace 标记 `was_executed: false`，不读取或伪造未来 GT。

3. **实际终止时刻正确记录。** 一个 F0 K30 chunk 在 terminal observation 前只实际推进 10 行时，trace 为 `actual_k: 10`、`next_query: false`；不会生成 execute request，也不会把仿真积分/render substep 计为 policy row。

4. **terminal infer blocker 已消除。** 候选删除每轮 policy-client 代理和 simulation 的 `run_iteration` 包装。`OpenPiSimulationScheduler.build_policy_obs()` 先处理 terminal feedback/trace，再返回 `None`；共享 `SchedulerBase.run_iteration()` 在 hook 后立即返回 `"skip"`，所以不调用 infer 或 execute。Base 只接受已有 hook 的最小 `dict | None` 契约，未读取仿真字段、未新增 RPC/session，live/offline 对正常 dict 的顺序不变。

5. **reset 兼容。** Base 原有 reset 位于 hook 之前；terminal 场景中若 `_policy_reset_pending=True`，仍先向 backend 发送一次 `reset` 并清除 pending，随后因 `None` 跳过 infer/execute。这保持既有 reset 生命周期而不把 terminal 变成一轮模型调用。

6. **边界校验明确。** selector 超出 H50，以及输出不足以容纳选择行，均显式报错，不会静默退回最后一行。

## 独立 CPU 验证

在审阅 worktree 以 `CUDA_VISIBLE_DEVICES=''` 执行：

```text
.venv/bin/python -m pytest -q \
  tests/scheduler/test_openpi_simulation.py \
  tests/scheduler/test_openpi_takeover.py
40 passed in 14.95s

.venv/bin/python -m pytest -q tests/scheduler/test_openpi_simulation.py \
  -k 'legacy_full_f0 or legacy_full_last_executed or legacy_full_selector_rejects'
7 passed, 8 deselected in 0.69s

.venv/bin/python -m pytest -q tests/scheduler/test_openpi_simulation.py \
  -k terminal_observation_skips_policy_infer_and_records_f0_trace -vv
1 passed, 14 deselected in 0.14s
```

另外以 terminal RMBench-shaped observation、真实 `SchedulerBase.run_iteration()`、计数 policy/robot client 独立复现，输出为：

```json
{
  "result": "skip",
  "policy_cmds": ["reset"],
  "infer_count": 0,
  "robot_cmds": ["get_obs"],
  "execute_count": 0,
  "actual_k": 10,
  "next_query": false
}
```

这验证的是实际共享循环，不只是直接调用 `build_act_request()` 的局部 hook。它不证明真机 transport 已通过，真机验证仍属于 live 复核范围。

## 后续独立范围（不影响上述 bc842036 F0 结论）

- **新 Memory v1 wire 契约尚未验收。** 当前实现的 `MemoryContext.add_inputs()` 将 dense 编码写入 padded `state`，真实训练 input transform 却读取 `memory_input_ids`；真实 output transform 又会把 `actions` 裁为 14 维机器人动作，而 runtime 曾从该尾部解码 memory。这两处断链须按已发布契约修为 scheduler 传 `(F,)` 的语义 `memory_input_ids`、policy transform 负责编码、输出以 `memory_prediction_ids`（full `(H,F)`、serial `(1,F)`）交给 `MemoryContext`。收到作者小增量后将跨真实 input/output transforms 与真实 context 做 CPU 联通复核，覆盖单/多字段、no-memory、K30 row30 和 serial 的实际 selected 条件；不会用两端 mock 字典代替。旧 F0 checkpoint 无 `memory_config`，因此不受此项阻塞。

- **新增 live P1：`281e0a7` 在 synchronous row 边界漏掉 chunk 末行。** 该增量正确把已完成进度从“时间戳已过”改为实际 transport handoff，但 X1 loop 和 X1Pro worker 都只在有下一个 `after` endpoint 时把 `before` 命令标为 processed。对 3 行实际 `execute` chunk，独立无硬件复现得到：X1 已 `queue_idle: true` 时 `completed_rows: 2`、`queued_rows: 1`（只发布 2 次，最后值约 2.994）；X1Pro 也只有两个不同 command timestamp 的 handoff event（末次发布约 2.50）。`MemoryContext.apply_wait_condition()` 对 `synchronous_rows` 只写 `action_queue_remaining: 0`，因此下一次 `get_obs` 可以在最后 policy row 未完成时返回；`observe()` 只得到 K−1 行，`last_executed`/`chunk_completed` 的第 K 行反馈会滞后一 query 或在 terminal/takeover 时丢失。这直接违反 “synchronous rows” 与实际执行行的契约，阻塞 live runtime 验收。修复必须让该模式在下一 infer 前拥有 K 行真实 handoff evidence（或显式继续等待），不能把已排期 timestamp 当作完成；回归须覆盖真实 X1 loop、X1Pro worker、插值 factor>1、最后 chunk/terminal 和 takeover/reset。

  `281e0a7` 的现有定向回归仍通过：`tests/robot/controllers/test_execution_progress.py` 为 `9 passed`，`tests/scheduler/test_memory_v1_schedulers.py tests/scheduler/test_openpi_takeover.py` 为 `28 passed`；它们没有覆盖 queue drain 后末行 completion。

- **其余 live / takeover 项仍待完成复核。** 该增量旨在修复先前的三项 P1：timestamp 过期即冒充实际执行、takeover 后旧 proposal 作为插值锚点、另一 `get_obs` 时间基提前推进 progress。另有 `synchronous_rows + latency_step>0` 在 queue drain 后仍保留 latency、令 H20/K15/latency2 从模型 rows 2..16 而不是 row 0 反馈的问题。这些与新末行 P1 都不随本 F0 terminal 修复自动关闭，均只阻塞完整 live runtime 结论，不阻塞旧 RMBench F0 smoke。

- **部署 P1：新 checkpoint 的轻量配置包没有可复现安装路径。** `MemoryContext.from_checkpoint_metadata()` 在检测到 `memory_config` 后必然导入 `openpi_client.memory_config`，但 robot-bridge 的 `pyproject.toml` / `uv.lock` 没有 `openpi-client`，`scripts/deployment/x1pro_master.sh` 只 clone `robot-bridge` 和 `sdk_robot` 并在 sdk_robot venv 中 `pip install -e .`，远端 scheduler 脚本也默认该 venv。因而干净部署对任一新 memory checkpoint 会立即抛出“openpi-client is unavailable”；本审阅 venv 中的 editable 安装只用于 CPU review，不能作为生产依赖。需要提交明确的包版本/安装来源和部署入口，并在干净 sdk_robot 环境实际创建 `MemoryContext` 验证。旧 F0 checkpoint 没有 `memory_config`，不受此项影响。

- 真实硬件通信没有在本阶段宣称通过；后续 report 将随新 wire 与 live 增量复核更新。
