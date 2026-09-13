# P0 选中 query 诊断记录接口：完成报告

## 交付

- OpenPI worktree：`/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/openpi`
  - 冻结基线：`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`
  - 交付 commit：`cb861d3824a46d9c243be7ff69159bcec17a0ac7` (`Add opt-in selected-query policy diagnostics`)
- robot-bridge worktree：`/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/robot-bridge`
  - 冻结基线：`f9626636c4776d8eb15f9c556775cb2d12c000e5`
  - 交付 commit：`a2c7f80b99556db2147c85ca9f625ffb840b276a` (`Persist selected-query diagnostic records`)

两个 worktree 均已在各自 `task/8968b7f5-74f7-44db-ad0b-058d3fd556ca` 分支干净提交。

## 实现范围

OpenPI 的 `Policy.infer` 新增仅由
`__openpi_diagnostic_context__` 启用的 sidecar；该字段在任何输入 transform 前移除，默认
请求和响应不增加字段、不写文件。选中调用记录变换前输入、batched transform 后输入、
`Observation.from_dict` 后传入 sampler 的输入（包括图像 uint8 到归一化 float 的变化）、
完整 raw action chunk、output transform 后输出、显式 noise，以及 JAX split 前 key、实际
sampling key 和 split 后 key。日志快照不额外 split RNG、生成 noise、调用 decoder 或改变
transform；捕获失败会以 `capture_failed` sidecar 明示，保持动作和最终 RNG 路径不变。

`Pi0.sample_actions_with_key_state_details` 在不改变既有三值普通 wire 的情况下，提供选中
诊断所需的 decoder selected IDs、实际用于 action condition 的 IDs 和真实 logits。J/T 的
tail 记录为连续 `raw_joint_memory_coordinates_before_output_transform`，并显式注明不是
classification logits；S 记录含 `-inf` padding 的真实 key-state logits、selected IDs 和
action-condition IDs。数组 descriptor 提供 dtype/shape；通用 policy 无法如实声明物理单位时
写为 `null`，RMBench scheduler 对最终 14 维 arms qpos target slice 另行声明单位约定。

robot-bridge 新增窄的 schema v1 `QueryDiagnosticRecorder`，只接受严格的
`params.diagnostic_trace` 配置。每个选中 query 写 strict-finite JSON 与 NPZ：数组、bytes
和非有限浮点外置，JSON 引用包含 key/dtype/shape/nonfinite；校验器核对 SHA-256、JSON 文件名、
`query.record_id` 与 NPZ 文件名的跨文件关联。首次 JSON/NPZ 发布使用同目录 hard-link，避免
并发 recorder 覆盖另一方的初始证据；同一记录的有限 lifecycle 更新使用 atomic replacement。
写入失败、数组上限、缺 policy response、sidecar link mismatch 都会留下显式状态或 recorder
status，不中断 policy/scheduler 动作路径。

`OpenPiSimulationScheduler` 将选中 context 注入 policy request，关联 policy sidecar、output
action chunk 与实际 `execute` request，并持续记录 cache、accepted/discarded/terminal、planned K、
已消费的 memory rows 与有 controller execution-progress 支持的 actual K。S 的
query-selected feedback 将旧 trace 的初始化 `actual_k=0` 规范为
`not_recorded_for_query_selected_feedback` / `value: null`，不声称执行零行。benchmark runner
把已接受 episode/seed 仅作为诊断构造参数传入 scheduler，未发起第二次 reset。

新增文档与入口：

- `docs/reference/query-diagnostic.md`
- `scripts/query_diagnostic_dry_run.py`
- `scripts/validate_query_diagnostic.py`

## CPU 验证

以下命令均在对应独立 worktree 完成，未启动 GPU rollout、训练、评测、部署或真机/仿真控制。

```bash
# openpi
JAX_PLATFORMS=cpu .venv/bin/pytest -q \
  src/openpi/policies/policy_diagnostic_test.py \
  src/openpi/training/memory_data_test.py \
  src/openpi/models/pi0_memory_test.py
# 16 passed

.venv/bin/ruff check src/openpi/policies/policy.py \
  src/openpi/policies/policy_diagnostic_test.py src/openpi/models/pi0.py
.venv/bin/python -m compileall -q src/openpi/policies/policy.py \
  src/openpi/policies/policy_diagnostic_test.py src/openpi/models/pi0.py
.venv/bin/python scripts/worktree_env_smoke.py
# 均通过
```

```bash
# robot-bridge
PYTHONPATH=/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/openpi/packages/openpi-client/src \
  .venv/bin/pytest -q \
  tests/scheduler/test_query_diagnostic.py \
  tests/scheduler/test_openpi_simulation.py \
  tests/scheduler/test_memory_v1_schedulers.py \
  tests/scheduler/test_memory_context.py \
  tests/scripts/test_run_scheduler.py \
  tests/benchmark/test_runner.py
# 66 passed

.venv/bin/ruff check --ignore EXE001 \
  robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py \
  robot_bridge/scheduler/memory_context.py robot_bridge/benchmark/runner.py \
  scripts/run_scheduler.py scripts/query_diagnostic_dry_run.py \
  scripts/validate_query_diagnostic.py tests/scheduler/test_query_diagnostic.py \
  tests/scripts/test_run_scheduler.py tests/benchmark/test_runner.py
.venv/bin/python -m compileall -q robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py robot_bridge/scheduler/memory_context.py \
  robot_bridge/benchmark/runner.py scripts/run_scheduler.py \
  scripts/query_diagnostic_dry_run.py scripts/validate_query_diagnostic.py
.venv/bin/python scripts/worktree_env_smoke.py
# 均通过；EXE001 仅忽略已有 run_scheduler.py shebang 非 executable mode
```

额外完成 OpenPI msgpack 与 bridge transport codec 的含 `-inf` logits round trip；结果通过。
新鲜 CPU dry-run 写入并校验了一条合成 S 记录，返回 `status=recorded`、`array_count=15`；
临时目录已删除：

```bash
.venv/bin/python scripts/query_diagnostic_dry_run.py --directory "$OUT"
.venv/bin/python scripts/validate_query_diagnostic.py "$OUT"/records/*.json
```

Policy 测试保留真实 Policy transform、batch、RNG split 与 output-transform 调用链，覆盖默认关闭、
J/T、S、显式 noise、`-inf`、image canonicalization 和 capture-failure 不干扰。Bridge 测试覆盖
多 query、严格 JSON/NPZ、hash/link、array cap、写失败、初始发布 race 不覆盖、J/T progress、S
unknown actual K，以及 runner identity 不触发 reset。

## 存储、时间与 I/O 边界

默认完全关闭。开启后必须显式选择 episode/query；`max_records` 默认 16、最大 64，
`max_array_bytes` 每条默认 64 MiB、最大 512 MiB。未压缩数组上界因此默认 1 GiB、极限 32 GiB；
NPZ 压缩、JSON 和文件系统开销不计入此界限。已存在的同名 evidence 不会被新 recorder 覆盖。

`model_infer_ms` 只覆盖 policy sampling；`diagnostic_capture_ms` 单独覆盖 sidecar snapshot/
构造，scheduler status 单独暴露最近 JSON、NPZ 与总写入耗时。选中 JSON/NPZ 是 policy response
后、execute dispatch 前的同步 I/O，会增加该次 dispatch 延迟；默认路径不执行这些操作。JAX
设备执行可能异步，因此 wall/monotonic、本地 infer timing 和写入 timing 只描述本地编排，不能
解释为 kernel、controller 或物理动作完成时刻。

记录止于 policy output transform 和 scheduler 形成的 `execute` request。未记录或验证
controller 内部排队、TOPP path、底层 SDK 命令、物理 tick、相机采集内部状态，也不证明启用记录
与关闭记录的物理实时轨迹逐时刻完全等价。

## 后续最小 GPU smoke（需 Manager 另行批准）

1. 在冻结 checkpoint 与本次两个 commit 上准备专用 scheduler YAML，使用空的诊断目录，选择一个
   accepted episode、`query_ids: [1]`、`max_records: 1` 和 64 MiB cap。
2. 只运行一个受控 simulation query，不开展正式评测；保存 scheduler status 和 record/NPZ，执行
   `scripts/validate_query_diagnostic.py`。
3. 对 policy 层使用相同输入、初始 key 和显式 noise 做 logging off/on 配对检查，比较 actions、
   state 与最终 RNG；再检查 scheduler record 的 checkpoint/source identity、episode/seed/query、
   J/T 或 S evidence 与 execute slice。
4. 单独报告 I/O 延迟，不把该 smoke 外推为 controller/TOPP/physical-tick 的验证或正式实验结果。
