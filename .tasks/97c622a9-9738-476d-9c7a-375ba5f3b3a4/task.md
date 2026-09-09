# 审阅论文任务记忆分析框架与最小实验设计
# 任务：只读审阅论文分析框架

## 目标

Manager 已亲自完成第一稿。独立检查这套 schema 是否能成为实证论文的分析框架：定义清楚、覆盖已知实现、区分混杂因素、能导出少量真正可判别的实验。请提出具体问题与最小修正，不代写设计，不实施算法。

## 阅读对象

- `/root/Documents/task-state-vla-paper/docs/MEMORY_DESIGN_FRAMEWORK.zh-CN.md`，本次固定 SHA256 `4322e9adeb6f23a633b0077de847be7dc7af3ef4827363b85d2dc6ae291a0fc2`。论文 Git HEAD `ee3f411dfa94d1fce4790d9c6b580ce16e1dc019`；本文是未提交的新文件，不能声称由 HEAD 提供。
- `/root/Documents/task-state-vla-paper/ROADMAP.zh-CN.md` 为研究方向背景，不是必须维持的旧实现约束。
- 必要的历史依据限定在 `/mnt/public/xcj/Projects/RMBench/experiments/history_audit_20260909/` 的 `README.md`、`shared_memory_timing.zh-CN.md`、`rearrange_tokens.zh-CN.md`、`early_state_designs.zh-CN.md`。已独立审计，无需重做原始184个run扫描。

## 审阅重点

1. S/P/E和六组协议是否有关键遗漏或含义重叠；逐字段时间、标签与输入unknown、状态约束是否描述充分。
2. 预测/消费时刻定义是否正确，是否混淆动作被接受与已执行、观测时间与wall-clock、未来预测与事实；特别注意 K=h+d 带来的不可独立变化。
3. P1的固定模型反馈位置对照、P2的逐帧/重复终点训练是否能回答所写问题，是否仍混入未承认的因素；优先提出会改变实验结论的问题。
4. 历史覆盖与数字是否忠于上述审计；Oracle、独立训练种子、offline replay的结论范围是否合适。
5. 新读者能否读懂；指出可以合并/删除的冗余以及难懂术语。不要把审阅变成无边界扩充schema或实验矩阵。

## 范围与交付

本任务为只读研究文档调查。使用登记的空workspace作为任务归属，不创建代码worktree或环境，不修改论文/业务库文件，不训练、不评测、不启动其他agent。若需要临时笔记，仅在本task工作区，交付前自行清理。

在MAM的report.md写简报并通过CLI发布：task_revision、完成/未完成、workspace、阅读文件SHA、论文HEAD（注明新稿不在HEAD内）、按重要程度列出的具体问题（文件行号、原因、最小建议），最后说明是否可作为下一轮用户讨论的框架。最多五个主要问题，次要措辞合并列举；若没有实质问题明确说明。

Manager 会自己修订正文；你的职责是独立审阅。完成后结束本轮，等待Manager需要时追问，workspace由Manager验收归档。
