task_revision: 80a513c1aec064823378adb5da1d8312b5e50149

进行中：已创建独立 openpi worktree，尚未启动训练。以下为先行 API 契约，供数据和 runtime 任务按此并行准备；首个代码 commit 将只实现这些轻量对象。

## Memory v1 API contract

模块：`openpi_client.memory_config`（纯 Python + NumPy/PyYAML；不导入 JAX/Torch）。

```python
load_memory_config(path_or_mapping) -> ResolvedMemoryConfig

ResolvedMemoryConfig.to_dict() -> dict
ResolvedMemoryConfig.make_training_sample(
    episode: EpisodeMemoryData, query_index: int, rng: random.Random,
) -> MemoryTrainingSample
ResolvedMemoryConfig.model_spec() -> MemoryModelSpec
ResolvedMemoryConfig.validate_model_dimensions(robot_dim: int, padded_dim: int) -> None
```

`EpisodeMemoryData(series, constants, events, tail=None)` 是适配器交付的规范化标签入口；字段按 YAML `memory` 列表顺序保存，`series` 长度、类别和值域在读取时严格检查。`make_training_sample` 每个命名 lag 每样本只抽一次，返回 `lag_draws`、有序 categorical `input_ids`、`target_ids`、每行 `target_mask`、robot target 的索引/有效位，以及 dense/token 编码所需的同一顺序布局。输入来源由 `protocol.input.train.<field>` 表达；`initial` 是明确的 train/infer 输入来源，仍保留同形状 `target_ids` 与 loss，不引入 auxiliary 模型类。`memory=[]` 是无 memory baseline，返回空字段布局，不等同辅助监督。

`MemoryModelSpec` 仅是可序列化的连接描述：representation、字段顺序/词表/initial IDs、dense offsets 或 token field sizes、loss 归约、显式 decoder 规则和反馈定义。默认 decoder 编译为全类别独立 argmax；只有 YAML 显式 `ordered_step`/`latch_category`/`conditional` 才产生 transition/selector 限制，因此 wash-cup 1..5 不会由字段名或位置被单调约束。`to_dict()` 是 checkpoint metadata 中的 resolved `memory_config`，保留 `schema_version`，排除 `record` 及实验结果引用。

P2 在实现时以有限的 target/tail 规则编码：H=50/K=30 可由 action 配置校验；phase 的 per-row/repeated-30 公共有效位分别保留、无效槽统一 zero、phase 使用固定 H 分母；robot 和其他字段的尾部/loss 位独立。

代码预估：新增约 450 行轻量 schema/sample 实现与约 250 行定向 CPU 测试；训练接入与模型/metadata 修改单独提交。
