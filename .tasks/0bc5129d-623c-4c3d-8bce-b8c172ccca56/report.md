task_revision: 8a554f2c2383cc4ace5ef5c6915df2ba06577ef1

# bc842036：F0 / legacy RMBench simulation 独立 CPU 验收通过，可开始 GPU smoke

审查候选与工作区：

- F0 候选：`bc842036e3735390f35fe1138aa7b19f5ae2f95b`（`fix: skip terminal simulation inference in base`）。
- F0 审阅基线：`b247332`，是将该 terminal patch 合入 `fd38513` 的等价 cherry-pick；二者稳定 patch-id 同为 `d09ba4ad09d83d1181b47ec6109bb006f24ceb45`。作出本 F0 判断时后继仅为 live controller 增量 `281e0a7`；当前审阅树 HEAD `967ba14` 还后接新 schema runtime 增量 `f84edbd` 的等价 cherry-pick（patch-id `d3b9dbe1bebf60c7d06b20a0eb74f7bfc534b514`）。两项后继均不纳入 `bc842036` 的 F0 判断。
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

## 当前增量复核（78e1b4a / ffa308d；不重开 F0）

bridge 审阅 HEAD `87fbc9c` 是 `78e1b4a49677d7aef50b0915076a465a4523ba5b` 的等价 cherry-pick；OpenPI 已在原独立树合入 `ffa308d5485a2c8222d3e7735b08723c6e93a237`，合并后的文件树与该提交完全一致。以下覆盖只涉及 runtime 和 inference wire，训练/loss/checkpoint 由 Banach 专审。Manager 已确认 F0 row30 smoke 通过并启动正式100；先前 bc842036 放行保持有效。

- **drain 后跳 latency 的 P1 已关闭。** 两类 scheduler 在 build_obs_request 记录本轮是否同步 drain，并把 action 起点及 future 查询按有效 latency=0 处理；非 drain 仍保持 latency_step。独立运行 `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/robot/controllers/test_execution_progress.py tests/scheduler/test_memory_v1_schedulers.py tests/scheduler/test_openpi_takeover.py` 为 **48 passed in 15.01s**，含同步/异步 action slice、末行发送及原 takeover 回归。

- **末行 handoff 的 P1 部分修复，仍阻塞 live synchronous 验收。** 78e1b4a 增加 accepted endpoint 的最后一次真实发送，正常运行最终计数可达 K；但两个 controller 的 `_wait` 仍只检查 `action_queue.count_after(observation_base)`，没有等待该观察时间基上的 handoff 完成。独立 CPU 复现使用真实 `execute`、X1 `_exec_loop` / X1Pro `exec_worker_main` 和真实 `get_obs`，只把设备发送函数用 event 暂缓返回：一个合法单行 chunk 的终点已到期，传感器 buffer 时间戳已推进；发送尚未完成时 `get_obs(wait_condition={action_queue_remaining:0})` 已返回。X1 返回用时0.05ms、X1Pro 0.04ms，二者均为 `scheduled_remaining=0`，但 `execution_progress={completed:0,queued:1}`。释放 event 后线程正常退出，未使用硬件。`MemoryContext.observe()` 又无条件清 `_await_observation`，scheduler 随后仍可生成下一次 infer 输入，故“最终会发送末行”不等于“同步 query 前已获得 K 行证据”。修复需把同步 query 放行与本次观察对应的实际 handoff 绑定，并保留原异步语义。该复现不以排期时间冒充执行，也不要求硬件 ACK。

- **新 wire 实际跨库 CPU 联通正在复核。** 已使用正式 ffa308d，后续证据覆盖真实 tokenizer / policy input-output transforms / MemoryContext。旧58d6的缺接口是已替代的历史基线，不重复测试，也不计作新训练增量的实现缺陷。

- **轻量安装方案待作者交付。** 按最新裁定，以固定 OpenPI 版本 wheel + 全新隔离环境 import/创建 MemoryContext 为验收范围。无需先安装整套训练框架或 SDK，也不改动真机和现有 sdk_robot 环境；设备可运行性另列。

