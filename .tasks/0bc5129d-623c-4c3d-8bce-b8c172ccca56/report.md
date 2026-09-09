task_revision: c84dfba0fe3b7b935ae6645526a7ba95a13773fa

# fd38513：F0 / legacy RMBench simulation 阶段审结（非最终 runtime 验收）

审查 HEAD / 工作区：

- `robot-bridge`：`fd38513adb5ba171327358f70f55f88059de49d2`
- `/mnt/public/xcj/Projects/workspace/0bc5129d-623c-4c3d-8bce-b8c172ccca56/robot-bridge`
- 另按任务要求创建并只读核对 `openpi` worktree：
  `/mnt/public/xcj/Projects/workspace/0bc5129d-623c-4c3d-8bce-b8c172ccca56/openpi`
  at `58d6f2155acc3af03017677bb3f536101e6699f4`。

本阶段只审旧 full checkpoint 的 F0 legacy simulation 路径、selector、progress/trace 和 terminal 边界。未修改作者实现、未启动 GPU、真机或 rollout；四行 smoke 和正式 100 rollout 仍归独立 eval 任务。

## 结论

**legacy H50/K30 selector / progress 没有阻塞；当前 F0 不可放行的唯一 simulation 阻塞是 terminal observation 仍额外调用一次 policy `infer`。**

因此，在作者交付并通过 terminal 局部修复前，不启动 rows 1/20/30/50 的各 2 rollout smoke，也不进入每行 100 rollout。修复只需局限于 simulation scheduler 的 terminal 分支；不应等待三项 live controller P1 一并解决。正式 recorder 的原完整配置检查保持，不加入新的白名单或兼容豁免。

## 已检查、可接受的 F0 行为

1. **旧 checkpoint 保持 legacy 路径。** 无 `memory_config` 的 `full_state` 不进入 `MemoryContext` / 新 schema 解码；其状态输入、密集输出切片和原有 one-hot 归一化仍由 `OpenPiSimulationScheduler` 的 legacy 路径处理。新 selector 只允许 legacy full-state；含 `memory_config` 的 checkpoint 会拒绝这个诊断参数，避免改变新 schema 的 metadata 事实源。

2. **H50/K30 基线正确。** 默认或显式 `{kind: last_executed}` 在实际完整执行 K=30 时选择 model index 29（人类 row 30）。选择从实际 `logical_step` 前进的 executed prefix 导出，未把 render/substep 当作 policy row。

3. **四种 row 诊断使用一条统一规则。** `{kind: index, value: 0|19|29|49}` 分别对应 rows 1/20/30/50；同一 raw output row 先被选出，再被用于所有 legacy dense memory fields 的既有投影。row 50 仍是模型预测而非 GT，trace 明确标记 `was_executed: false`，不会伪装为已执行行。

4. **trace 的实际执行和 terminal 表达正确。** 接受 chunk 后，以 `logical_step - source_step` 计算 `actual_k`；terminal 前仅执行 10 行的例子记录 `actual_k: 10`，且 `next_query: false`。在直接调用 scheduler hook 的路径，terminal `build_act_request()` 返回 `None`，不会生成 execute request。

5. **边界校验明确。** selector 越出 H50 会在初始化时报错；不足以容纳 selector 的模型输出也会被拒绝，不会静默回退到末行。

独立 CPU 验证（`CUDA_VISIBLE_DEVICES=''`）：

```text
.venv/bin/python -m pytest -q tests/scheduler/test_openpi_simulation.py \
  -k 'legacy_full_f0 or legacy_full_last_executed or legacy_full_selector_rejects'
7 passed, 7 deselected
```

该集合覆盖 rows 1/20/30/50、K30 的 `last_executed`/row30 等价、terminal 的 actual-k/trace，以及越界 selector 拒绝。

## F0 阻塞：terminal trace 与实际调用不一致

`OpenPiSimulationScheduler.build_policy_obs()` 已把 terminal 写入 `_episode_terminal`，而 `build_act_request()` 会据此返回 `None`。但共享 `SchedulerBase.run_iteration()` 的顺序仍是：`get_obs` → `build_policy_obs` → **policy `infer`** → `build_act_request`。所以 terminal observation 的 trace 虽写 `next_query: false`，实际仍有一次无用推理。

独立最小复现使用 terminal RMBench-shaped observation、真实 scheduler hook 和计数 policy client：`run_iteration()` 返回 `"skip"`，`infer_calls=1`，robot 端只收到 `get_obs`、未收到 execute。该结果确认风险在实际循环，不是只存在于手工 hook 调用。

作者已被 Manager 要求给出 simulation-only 小提交。收到后需复核以下条件：

- terminal trace 保留真实 `actual_k` 且 `next_query: false`；
- terminal observation 的 policy `infer` 调用数为 0；
- 没有 execute / action 入队；
- 非 terminal F0 K30 路径和 shared base/live 循环未被改动；
- 上述 7 个 selector 测试及新增实际循环 infer-count 回归测试通过。

通过后，F0 runtime 才可交给 eval 任务按 rows 1/20/30/50 各自 2 rollout smoke、再各自 100 rollout 的既定流程执行，并保留完整 recorder 检查。

## 尚未纳入本阶段结论

- Memory v1 多字段、serial、partial completion、reset/takeover 和 UI 全范围审查仍在继续。
- x1/x1pro 三项 live controller P1（排程时间冒充实际处理、takeover 后旧 proposal 作为锚点、跨 `get_obs` 时间基提前推进 progress）由作者另行修复；它们是 live runtime 的阻塞，不作为 F0 simulation 小修复的等待条件。
- `fd38513` 全量改动为 13 files、`+2252/-69`；其中 simulation scheduler 和其测试的增量规模分别为 `+342/-29`、`+131/-0`。关于其余实现必要性、重复逻辑、打包运行依赖及完整 schema/live 结论将在后续 report 更新中给出。
