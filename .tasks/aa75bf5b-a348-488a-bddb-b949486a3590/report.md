task_revision: 300a8baea6b33f8e974d4b62f1105b31cbb39b26

完成与未完成：
- 已完成：按最新任务要求，以独享只读快照 `workspace/aa75bf5b-a348-488a-bddb-b949486a3590/review_v2` 为基准完成终审。复用上一版已完成的主规格、Schema、五个实例、重复键与 Draft-07 结构核验；仅追加核对 MEMORY_CONFIG 第 7 节的按调用阶段能力检查。
- 已完成：新增条款明确训练检查标注/尾部/模型变换，普通推理只检查 checkpoint 字段、模型资产和执行能力，显式 `reference` 推理才需要在线参考值，UI 不加载训练数据或模型。这一边界与“参考标注只供 Oracle/诊断”一致。
- 未完成：无。本任务不包含生产解析器、训练或 scheduler 接入；未将这些尚未实施事项记作代码缺陷。

workspace、各库交付 commit：
- workspace：`/mnt/public/xcj/Projects/workspace/aa75bf5b-a348-488a-bddb-b949486a3590`；审阅输入为其 `review_v2/`。
- 无代码 worktree、无业务库修改、无交付 commit；仅编辑并发布本 report。

验证结果与成果位置：
- 在 `review_v2/` 执行 `sha256sum -c SHA256SUMS`，10 个列出文件全部通过。
- 复用的只读核验：以拒绝重复键的 YAML loader 解析 `memory.schema.yaml` 与五个实例，并以 Draft-07 校验；`rearrange_full`、`rearrange_serial`、`rearrange_random_lag`、`battery_full`、`swap_T` 全部通过。已展开的正常时序也一致：full/battery 在 K=30 后取第 30 行，serial 的 query 反馈取当前类别，swap_T 首 chunk 完成后锁存第 30 行。
- 本次仅复核的第 7 节新增条款位于 `review_v2/docs/MEMORY_CONFIG.zh-CN.md`，其按阶段数据绑定规则没有引入与现有实例或 Schema 的冲突。

审阅结论：暂不建议将当前规格作为后续实现的唯一明确依据；以下两个结构合法的开放组合没有唯一运行语义。Manager 最终裁定。

阻塞问题：
1. 负的目标时间没有定义下界处理。`memory.schema.yaml` 的 `definitions.time.offset` 接受任意整数；第 3 节只为输入规定 `s < 0` 使用 `initial`，而目标的 `action.tail=clamp` 又只定义“取末有效帧”。第 7 节的语义检查没有禁止目标下界越界。将 `rearrange_full.yaml` 的 `protocol.target.fields.phase.offset` 在内存中改为 `-1` 后仍通过 Draft-07；首个 query 的第 0 行为 `s=-1`，无法从规格唯一判断是 initial、mask、首帧 clamp、dataset 映射还是拒绝。应明确禁止任何可产生 `s<0` 的目标/机器人目标时间，或定义统一的下界 tail 语义。
2. 在线 `reference` 输入允许引用训练 lag，却没有在线 L 的取值规则。所有 Time 都可带 `lag`，`infer_input.source=reference` 也可带 Time；第 3 节规定在线推理“不抽训练 lag”，第 7 节只检查引用存在且目标不含 lag。将 `rearrange_serial.yaml` 的 `input.infer.phase` 在内存中改为 `{source: reference, time: {anchor: query, offset: 0, stride: 0, lag: previous}}` 后仍通过 Draft-07；普通推理/Oracle 应使用哪个 L 无法确定。新增的按阶段条款要求此路径提供在线参考值，但仍未给出 L。应显式拒绝推理 reference（以及在线 reference feedback）中的 `lag`，或规定一个确定的在线 lag 来源。
