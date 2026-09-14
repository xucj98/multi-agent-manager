# 空白科学审稿

独立审查实证RA-L论文与实验计划。冻结论文仓库 /root/Documents/task-state-vla-paper commit 37b23a7；先创建该仓库独立worktree。阅读paper.pdf、正文TeX、docs/EXPERIMENT_PLAN.zh-CN.md、docs/planning/experiment_matrix.csv、docs/planning/pre_review_snapshot.json，以及需要的原始证据。不要阅读此前review、Manager裁决或对话历史。

判断：论文科学主张、九任务范围、对照可辨识性、单train seed边界、缺失控制、优先级与资源、是否足以支持RA-L实证贡献。指出缺陷并给最小可执行修订，不为凑数量增加实验。每项新增/删除/替换建议给任务、设定、train模型和eval批次数；区分必需和可选。特别判断机制是否过度集中两个开发任务、V与具名外部比较是否足够、JE损失尺度/目标时间与serial条件差异能支持哪些结论。

这是只读科学审稿，不实现、不训练、不编辑论文；结果写MAM report.md并publish，清晰列出优先级、证据和理由。第一轮只读查看要求并返回CODEX_THREAD_ID，结束turn待绑定；绑定后再开展正式review。
