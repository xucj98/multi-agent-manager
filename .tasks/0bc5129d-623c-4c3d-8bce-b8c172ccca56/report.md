task_revision: be14f517c506b6e8281f4733275abb2e77d7fdd3

# bc842036：F0 / legacy RMBench simulation 独立 CPU 验收通过，可开始 GPU smoke

审查候选与工作区：

- F0 候选：`bc842036e3735390f35fe1138aa7b19f5ae2f95b`（`fix: skip terminal simulation inference in base`）。
- F0 审阅基线：`b247332`，是将该 terminal patch 合入 `fd38513` 的等价 cherry-pick；二者稳定 patch-id 同为 `d09ba4ad09d83d1181b47ec6109bb006f24ceb45`。作出本 F0 判断时后继仅为 live controller 增量 `281e0a7`；该阶段审阅树 HEAD `967ba14` 还后接新 schema runtime 增量 `f84edbd` 的等价 cherry-pick（patch-id `d3b9dbe1bebf60c7d06b20a0eb74f7bfc534b514`）。两项后继均不纳入 `bc842036` 的 F0 判断。
- 作出 F0 结论时的 OpenPI 基线：`58d6f2155acc3af03017677bb3f536101e6699f4`；同一个独立 worktree 后续已合入正式 ffa308d，当前版本见下文。

本节放行旧 full checkpoint 的 F0 simulation CPU gate；后续新 wire 与 live 结论分列。未修改作者实现，未启动 GPU、真机或 rollout；GPU smoke/100 rollout 仍由独立 eval 任务执行。

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

- **live P1：延迟 tick 跨端点时，handoff 次数被误映射成连续轨迹前缀。** 两 controller 均用真实 execute 接收3个目标（每行14维，依次全1/全2/全3，间隔20ms），延迟90ms才运行真实 X1 loop / X1Pro worker，随后再观察50ms。两者都只成功发送 `[3.0]`（轨迹第3个目标），tracker 为 `{completed:1,queued:2}`；真实 MemoryContext（H50/K3、action_completed/last_executed、预测前3行分别1/2/3）却得到 `actual_k=1`、消费 `model_index=0`、cache `[1]`，仍列出后两行待完成。没有被选为 before 的前两个 timestamp 永久留在 tracker pending；目前 timestamp-only 的 wait 则会提前返回，若仅改成等待 queued=0 将卡住。根因是 exact-timestamp 事件累计“处理次数”与 Context 所假定的连续已执行前缀不同。修复应以成功 handoff 及其轨迹位置表述进度，保留实时插值允许跳过中间端点的行为；不建议事后补发过期动作，不以墙钟或 SDK 发送次数替代 policy row。仅阻塞 live，sim/训练不受影响。

- **新 wire 的实际跨库 CPU 联通通过本轮定向验收。** 正式 ffa308d 与当前 runtime 已通过下列7个独立用例；不是对两个 mock 字典分别测试。旧58d6的缺接口已被正式增量替代，不再列作缺陷。这不关闭前述 live 进度/等待 P1。

- **轻量安装方案待作者交付。** 按最新裁定，以固定 OpenPI 版本 wheel + 全新隔离环境 import/创建 MemoryContext 为验收范围。无需先安装整套训练框架或 SDK，也不改动真机和现有 sdk_robot 环境；设备可运行性另列。

## 真实 inference wire 的独立 CPU 证据

本轮准确版本：bridge `87fbc9ca4d4d9801aba752807357c57580a3bd61`；OpenPI `f3f645938170cc6f84082d3b07bdc9820cb223c1`，`git diff ffa308d5485a2c8222d3e7735b08723c6e93a237 HEAD` 为空。工作区均位于 `/mnt/public/xcj/Projects/workspace/0bc5129d-623c-4c3d-8bce-b8c172ccca56/` 下的原 `robot-bridge`、`openpi` 树；使用本任务 OpenPI 的 `.venv` 和 editable，`CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1`。

独立 harness 采用真实 `OpenPiSimulationScheduler.init_state/build_policy_obs/build_act_request/after_execute`、真实 `MemoryContext`、`TrainConfig.create_data_config(training=False)`、真实 Aloha input/output transforms、Normalize/Unnormalize、memory transforms、Paligemma tokenizer，以及 `Policy.infer()`。输入为14维 qpos、3路 RGB 和 prompt，执行进度观察由0变30；未读取训练 GT。使用正式 `pi05_rmbench_rearrange_blocks_full_t_plus_1`、`serial_lag30`、`no_memory` 配置；单字段用例只缩窄该配置的字段及对应 bindings/schema maps。

模型计算的界限明确：full 用构造的 `(1,50,32)` 原始 dense 输出，memory 每行不同；serial 使用真正的 `Pi0.sample_actions_with_key_state`、选择/规则及动作条件路径，只替换昂贵 embedding/LLM/投影计算，并捕获进入 `_embed_key_state_values(segment_index=1)` 的 ID。`nnx_utils.module_jit` 在 harness 构造 Policy 时暂替为 identity；真实 transform、tokenizer、Observation、Policy 输出分支和 Context 未替换。因此证据支持接口及语义联通，不声称完整模型权重/JIT、GPU 或硬件通过。

| 用例 | 实际观测与断言 |
| --- | --- |
| full 3字段 | request IDs `[3,2,2]` 确实改变真实 `tokenized_prompt`；policy 输入 state 仍为14维；最终 actions `(50,14)`，IDs `(50,3)`；执行请求30行后 Context `actual_k=30`，所有字段消费 index29/row30，下一次 IDs `[2,1,2]`。 |
| full 1字段 | request `[3]` 改变 token 输入；输出 actions `(50,14)`、IDs `(50,1)`；K30 下一次 IDs `[2]`，消费 index29。 |
| serial 3字段 | request `[3,2,2]` 到达真实 `Observation.key_state_input_ids`；输出 IDs `(1,3)` 与实际动作条件完全相同，并进入下一次 Context 输入。另以现有 `action_condition_state_ids=[[1,1,1]]` 覆盖 logits 选择，统一输出仍精确等于实际 condition，且不同于原 logits argmax。 |
| serial 1字段 | 相同路径输出 `(1,1)`，覆盖 condition `[[1]]` 后统一输出保持相同；无字段数量硬编码。 |
| no-memory | request 不含 memory_input_ids，结果可不含 memory_prediction_ids；actions `(50,14)`，真实 scheduler 可生成 `(30,14)` 执行请求并进入下一次观察。 |
| full request previous | 保存 schema 的 decoder 改为 `ordered_step/max_advance=0`；第一个字段 infer.source=initial，其余 cache。复用同一 Policy，三次请求分别 `[0,0,0] → [0,2,2] → [0,0,0]`，每次50行解码都等于本次请求 IDs，Context trace previous 也相同。证实没有错误使用非输入 cache 或跨请求隐式 previous。 |
| serial request previous | 同样三次请求和 decoder；每次统一输出及实际动作条件均等于本次请求 IDs，Context trace previous 完全一致。 |

全部 **7个独立用例通过**。full 输出经过真实机器人裁剪及反归一化后 ID sidecar 未丢失；scheduler 从 sidecar 校验/反馈，没有重新从14维 actions 解码。serial 使用真正的条件选择结果，没有在 Context 再 argmax。尚未覆盖 GPU50step 保存加载后真实权重返回 keys/shape，该项随训练/评测交付再复核，不重复 Banach 的训练/loss/checkpoint 专审。本轮实际跨 transform 的机器人适配器是 RMBench/Aloha；不能据此宣称其它 live 机器人配置或真实 transport 均已验收。

额外运行以下 runtime 定向回归：

```text
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/scheduler/test_memory_context.py tests/scheduler/test_control_server.py \
  tests/scheduler/test_lifecycle.py tests/policy/test_openpi_metadata.py \
  tests/scheduler/test_openpi_feedback.py
35 passed in 3.02s
```

包括多字段与独立 selector、query/chunk/实际完成反馈、控制命令到 policy row 映射、拒绝/中断清 pending、非法或缺失进度、公共 IDs layout/类别边界、no-memory、控制 UI 及原生命周期。此前78e增量48项仍保留，不重新跑整套训练测试。UI静态代码遍历同一 Context 的 `memory.fields`，按 field.name 发出 set_memory；新字段数未硬编码为 phase/attribute。没有进行浏览器或真机交互验收。

## 规模、必要性和重复逻辑

口径为作者起始基线 `b17f6c53ffbc1030972a9820cf592f28b937d501` 到本轮 bridge `87fbc9c` 的 `git diff --numstat`，含前置 controller/metadata、完整 runtime、F0 terminal、新 wire 和78e修复，不含 OpenPI 训练实现：

| 类别 | 文件数 | 新增行 | 删除行 |
| --- | ---: | ---: | ---: |
| runtime（含 control.html） | 15 | 1893 | 165 |
| tests | 7 | 1523 | 3 |
| docs | 4 | 88 | 11 |

`MemoryContext` 660行集中拥有 cache、反馈事件、接受/完成映射、trace 和 UI 数据；三个 scheduler 的新增对接分别172/162/365行，sim中还包含 legacy F0 trace/selector。没有三份独立反馈状态机或新 plugin bus/session/RPC。live/offline 在 metadata、pending 接受/丢弃、drain 配置处仍有相似接线，但机器人历史、插值及 master 布局不同，不能只按行数认定应合并或删除。

实质结构缺陷是 controller 的 completed 表示实际发送次数，而 Context 将其解释为连续轨迹前缀，以及 `_wait` 另用排期队列决定完成；上述两个 live P1 是这两套进度语义不一致的实际后果。现有末行测试只验证最终 handoff；补上该测试仍未覆盖“同步观察是否提前返回”和“tick跳端点如何映射”两个边界。应保留既有必要测试，并使修复覆盖这两条真实 loop/worker 路径，不能靠删测试或补发过期动作化解。

本轮没有修改作者实现。独立临时 harness 按任务要求清理，原两库工作树及已发布证据保留；没有启动GPU、硬件、rollout或需登记的长进程。后续仅复核新交付的 live 修复、最小 wheel 安装路径和实际权重接口证据；F0与已通过的CPU wire不因这些待办重开。
