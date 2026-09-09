task_revision: ead6025c9add5190880feb43b7a1fa6b64c40965

完成与未完成：
- 已完成：按最新要求对独享只读快照 `workspace/aa75bf5b-a348-488a-bddb-b949486a3590/review_v3` 作定向终审。复用已完成的主规格、五实例、重复键与时序核验，仅复核 MEMORY_CONFIG 和 `memory.schema.yaml` 的两项修订。
- 已完成：确认第 7 节的按调用阶段能力检查仍成立：普通推理不要求训练标注，显式 `reference` 路径才要求在线参考值，UI 不加载训练数据或模型。
- 未完成：无。本任务不包含生产解析器、训练或 scheduler 接入；未将这些尚未实施事项记作代码缺陷。

workspace、各库交付 commit：
- workspace：`/mnt/public/xcj/Projects/workspace/aa75bf5b-a348-488a-bddb-b949486a3590`；审阅输入为其 `review_v3/`。
- 无代码 worktree、无业务库修改、无交付 commit；仅更新并发布本 report。

验证结果与成果位置：
- 在 `review_v3/` 执行 `sha256sum -c SHA256SUMS`，10 个列出文件全部通过。
- 用拒绝重复键的 YAML loader 解析新 `memory.schema.yaml`，并运行 Draft-07 schema 自检及五实例校验；`rearrange_full`、`rearrange_serial`、`rearrange_random_lag`、`battery_full`、`swap_T` 均通过。
- 定向回归：内存中将 target offset 改为 `-1`、给 target 加 lag、给 reference 推理输入加 lag、给 reference 反馈加 lag，均被新 Schema 拒绝；不带 lag 的 reference 历史 `offset: -20` 通过。该组合的 `s<0`/`s>=T` 行为由新增文字明确采用输入边界规则。

原终审发现与修复结论：
1. 原阻塞“负的目标时间没有定义下界处理”已修复。`target_time` 以结构约束覆盖 memory target fields 与 `action.robot_target.time`：`offset >= 0` 且禁止 `lag`。文档同步说明 t、j 非负，目标只会使用 `action.tail` 处理超过 episode 末尾的情况；此前 `offset: -1` 的结构合法反例现已无效。
2. 原阻塞“在线 reference 使用训练 lag 没有 L 来源”已修复。`online_time` 以结构约束覆盖 `input.infer.source=reference` 和 `feedback.source=reference`，均禁止 `lag`；训练输入保留原 `time`，因此固定/随机训练 lag 不受影响。文档明确在线固定历史读取用 `offset` 表示，并沿用输入的下界 initial 与序列上界报错规则；此前两个含 lag 的在线反例现已无效。

审阅结论：两项原阻塞均已由结构约束与语义文字一致地修复，五个既有实例仍通过。定向范围内未发现新的阻塞问题；该规格可作为后续实现的明确依据。Manager 最终裁定。
