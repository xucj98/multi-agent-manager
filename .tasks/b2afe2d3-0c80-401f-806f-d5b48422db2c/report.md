task_revision: d2ed2ba033298ed868e68e3bd41c10c313decc89

审阅快照：source task `b7f0a7af-2ffa-4596-8b88-4967dfc633f6` @ `ceb75a56b94356f7e0b8e868ec47196344247771`；source report 固定为 `3d16d1a819c402267e960d599964c4baeb48a994`（英文正文 1,258 词）。

## 结论

GO，附一项 P2 文字准确性修订。该项不要求新增实验、不改变既定比较或结果待补状态。

## 应修项

### P2：把统计单位写成 seed 级配对比较，而不是“三个模型”

**证据。** 英文稿 Protocol 段写道 “The three models remain separate statistical units”。但 Q2 和 Q3 都是在每个 training seed 下比较两个条件，各条件各有独立训练的模型；论文计划要求逐 seed 报告配对差异，再汇总三个 seed，不能把 300 条 rollout 合并为一个模型的重复。现有句子会把模型数和真正的 seed 级比较单位混在一起。

**最小修改建议。** 将该句改为类似："Training seed is the replication unit: for each comparison, we report the paired contrast separately for seeds 0, 1, and 2, using the condition-specific trained model(s) at that seed, and summarize the three contrasts by their mean and range rather than pooling 300 rollouts." 保留紧随其后的“区间包含零不等于等价”表述。

## 已核对且通过

- 时序段统一使用零基预测索引 `j` 与一基反馈行 `r=j+1`，以实际执行 `K_n` 定义下一 query；也清楚区分训练时的 GT 输入、部署递推预测、serial 的当前动作条件和 full 的下一 query 反馈。
- Q2 正确固定 full one-hot 的形状、输入、`H=50`、`K=30`、`r=30`，只改变 phase target；公共 mask、固定-H 归约、row-30/`j=29` 的同一消费时刻和边界离线诊断均与实验计划一致。
- Q1 明确它估计完整选行规则与 `K` 的交互，未将其读成 phase 或单一滞后机制的因果效应。Q3 正确给出固定 lag-30 下的 content-condition × deployment-`K` 差异之差，并要求直接评估交互不确定性，未声称 K 匹配训练下的最优性。
- 结果状态没有预写方向或未完成数字；wash-cup offline 与真机闭环范围分开，后者仍为待执行。三图一表的组织紧凑、正文可独立阅读；相关工作事实与指定定位文档一致，无需扩展查新。

验证结果与成果位置：只读核对固定 source report，以及 `docs/EXPERIMENT_PLAN_20260910.zh-CN.md` 和 `docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md`；未修改论文、业务代码或实验配置，未创建环境/worktree、未使用 GPU、未派发 agent。无业务库交付 commit；本报告为唯一交付。
