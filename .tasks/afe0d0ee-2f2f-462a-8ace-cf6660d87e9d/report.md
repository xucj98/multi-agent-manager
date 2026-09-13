# P0 选中 query 诊断记录接口：独立审查报告（待修复复审）

## 审查对象与隔离

- OpenPI：`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4..cb861d3824a46d9c243be7ff69159bcec17a0ac7`
  - review worktree：`/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/openpi`
- robot-bridge：`f9626636c4776d8eb15f9c556775cb2d12c000e5..a2c7f80b99556db2147c85ca9f625ffb840b276a`
  - review worktree：`/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge`

未修改作者源码，未运行 GPU、训练、正式 rollout、评测或部署。

## 已核验的正面行为

- 默认关闭时 scheduler 不创建 recorder、不添加私有 context，Policy 不添加 sidecar；CPU seam 覆盖 actions、state 与最终 JAX key 等价。
- J/T 记录的是生成的连续 raw memory coordinates，未冒称分类 logits；S 保留实际 logits（含 `-inf`）、decoder selected IDs 和 action-condition IDs。
- JSON/NPZ 关联、hash、filename/record ID 校验、严格 finite JSON、初始发布不覆盖以及记录 I/O 在 execute dispatch 前的边界均经源码和窄测试核对。
- Policy→OpenPI msgpack→bridge codec→recorder 的 serial `-inf` round trip 保留数组中的 `-inf`，JSON/NPZ validator 通过。

## 已发现并由 Manager 纳入修复的缺口

1. **P1：Memory-v1 execute RPC 非 `ok` 后错误收口。**
   `SchedulerBase.run_iteration` 在 execute 非 `ok` 时不会调用 `after_execute`；旧版
   `OpenPiSimulationScheduler._refresh_query_diagnostics` 却在 `next_consumption is None`
   时关闭尚未 accepted 的 record。下一 retry observation 后记录显示 `recorded`，但
   `accepted=false`、`discarded=null`、`actual_k=null`，且已不再 active。
2. **P1：legacy full-state J/T execute 非 `ok` 后 orphan active record。**
   `diagnostic_record_id` 旧版仅在 `after_execute` 赋给 dense feedback；失败后下一次
   `build_act_request` discard 收到 `None`，原 record 永远保持 active。
3. **P1：容量上限只在 bridge 收到完整 sidecar 后才执行。**
   OpenPI 在诊断专用复制、设备取回和 response 传输前没有预算，bridge 也已复制
   `scheduler_input`。真实 CPU Policy seam 使用 1024×1024 RGB、`max_array_bytes=1`
   时，sidecar msgpack response 仍为 `9,439,969` bytes；随后才写
   `not_recorded_array_limit`，无 NPZ。这不满足采集/传输开销受控。
4. **P2：只含 status/context 的残缺 sidecar 会被伪称完整。**
   对 matching context 传入最小
   `{schema_version: 1, status: "complete_policy_sidecar", context: ...}`，旧 recorder
   写外层 `status="recorded"`；validator 也返回 `recorded, array_count=0`，没有输入、
   RNG、动作或 memory evidence。

Manager 已发布源任务补充，要求作者仅作 lifecycle、budget 与 schema-completeness 窄修，并保留
Base retry/动作语义；当前冻结交付不准入 GPU。

## 已完成的 CPU 验证（冻结交付）

```bash
# openpi
JAX_PLATFORMS=cpu .venv/bin/pytest -q src/openpi/policies/policy_diagnostic_test.py
# 5 passed

JAX_PLATFORMS=cpu .venv/bin/pytest -q \
  src/openpi/models/pi0_memory_test.py src/openpi/training/memory_data_test.py
# 11 passed

# robot-bridge
PYTHONPATH=<openpi-client> .venv/bin/pytest -q tests/scheduler/test_query_diagnostic.py
# 10 passed

PYTHONPATH=<openpi-client> .venv/bin/pytest -q \
  tests/scheduler/test_openpi_simulation.py tests/scheduler/test_memory_v1_schedulers.py
# 25 passed
```

还执行了 `scripts/query_diagnostic_dry_run.py` 与 `validate_query_diagnostic.py`；一条合成
serial record（15 arrays）成功写入并校验。以上通过不覆盖四项缺口。

## 复审门槛

收到作者新的精确 commit 后，将仅审增量并重跑：

- Memory-v1 和 legacy J/T 的真实 `run_iteration`/controller execute-non-ok、retry、supersede、terminal、reset 生命周期反例；检查 accepted、discarded、terminal 与 unknown `actual_k` 不被伪造。
- 真实 Policy transform→sampling→msgpack→recorder 的大图像/小预算反例，确认超限前不构造或传输巨大 sidecar，且 actions/state/final RNG 等价。
- 空 complete sidecar 反例、有效 Policy sidecar、严格 JSON/NPZ validator 和相关 scheduler tests。

checkpoint 记录目前只是 `actual_path`/step 的位置身份，不是权重内容身份；本轮不引入权重哈希。后续正式诊断必须关联已核验的 run-level checkpoint manifest；若 manifest 自身没有内容 hash，不得据此声称强内容身份。

当前结论：**不通过，等待窄修复复审；不可进入 GPU smoke。**
