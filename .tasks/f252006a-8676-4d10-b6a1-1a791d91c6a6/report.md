task_revision: 2ad5547fa73332de3b6ef412fa9290f8c6e9540f

进行中：已创建独立 openpi worktree，未启动训练。API/契约 commit：openpi `de79cce20e54c612634fdc2598b91cc0ab5034ec`（`feat: add resolved memory config API`）。该 commit 不含 RMBench、`demo_clean_state` 或其他数据集名；本批来源约束留给任务配置/资产验收，不能硬编码进通用库。

## Memory v1 API contract

模块：`openpi_client.memory_config`（纯 Python + NumPy/PyYAML；不导入 JAX/Torch）。

```python
load_memory_config(path_or_mapping) -> ResolvedMemoryConfig

ResolvedMemoryConfig.to_dict() -> dict
ResolvedMemoryConfig.make_training_sample(
    episode: EpisodeMemoryData, query_index: int, rng: random.Random,
) -> MemoryTrainingSample
ResolvedMemoryConfig.compile_model_spec(model_config=None) -> MemoryModelSpec
ResolvedMemoryConfig.validate_model_dimensions(robot_dim: int, padded_dim: int) -> None
```

`EpisodeMemoryData(series, constants, events, tail=None)` 是适配器交付的规范化标签入口；字段按 YAML `memory` 列表顺序保存，`series` 长度、类别和值域在读取时严格检查。`make_training_sample` 每个命名 lag 每样本只抽一次，返回 `lag_draws`、有序 categorical `input_ids`、`target_ids`、每行 `target_mask`、robot target、`dense_actions`、逐坐标 `action_loss_mask/action_loss_weights`。输入来源由 `protocol.input.train.<field>` 表达；`initial` 是明确的 train/infer 输入来源，仍保留同形状 `target_ids` 与 loss，不引入 auxiliary 模型类。`memory=[]` 是无 memory baseline，返回空字段布局，不等同辅助监督。

`MemoryModelSpec` 的 runtime 属性完整为 `representation`, `field_names`, `field_values`, `initial_ids`, `encoding`, `dense_offsets`, `robot_dim`, `padded_dim`, `action_horizon`, `execution_rows`, `target_layout`, `loss_kind/weight`, `current_condition`, `decoder_rules`, `feedback`。runtime 直接复用 `encode_dense_ids(ids)`、`decode_ids(ids)`、`decode_dense_actions(actions, previous_ids)`、`decode_token_logits(logits, previous_ids)`，不再维护一份 one-hot 切片或词表。默认 decoder 编译为全类别独立 argmax；只有 YAML 显式 `ordered_step`/`latch_category`/`conditional` 才产生限制，因此任意顺序的 wash-cup 1..5 不会由字段名或位置被单调约束。

checkpoint 只存 `ResolvedMemoryConfig.to_dict()` 的 `memory_config` 字典（含 `schema_version`，排除 `record`）；`MemoryModelSpec` 在恢复时从此对象推导，绝不并存为第二份 metadata。P2 使用有限字段写法 `validity: {kind: all_in_bounds, times: [...]}` 和 `loss_reduction: fixed_horizon`；无效 phase 槽为 category ID 0 且逐坐标 loss weight 为零，robot/其他字段保持各自权重。

验证（API commit）：`pytest -q packages/openpi-client/src/openpi_client/memory_config_test.py`，16 passed；ruff check/format 与 diff check 通过。当前新增 1,838 行（实现与定向 CPU tests）；训练、模型、metadata 接入将单独提交。

代码预估：新增约 450 行轻量 schema/sample 实现与约 250 行定向 CPU 测试；训练接入与模型/metadata 修改单独提交。
