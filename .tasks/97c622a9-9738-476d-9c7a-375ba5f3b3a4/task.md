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

## 本轮定向复核追加

Manager已依据首次报告修订同一文件，现SHA256为`3b6e0f3c7baf0e25e34c3b21e67034dda338de65c944c03d6c25bd7c64d36e55`。只复核原五项意见是否已处理，不重新展开完整审阅：同步P1/P2要求继续query前完成K，episode提前结束仍进入成功率统计但没有下一反馈；P1收窄为组合协议探索；P2明确不同损失时域/难度/重复权重，并把endpoint-only控制留给需要归因时；P3收窄为字段设计对照。

第5项补充证据允许读取同目录的`run_index.csv`，仅查询`pi05_rearrange_state_token_boundary_ablation/serial_soft_seed42@`这八行即可。23/25、35/49、64/81、38/54对应K15/20/30/50，train seed42与同一checkpoint已在正文补明，eval版本不完全一致和本地缺权重也已注明。这不是shared fixed20 seed42的24/26。

请在原report保留初审发现，追加定向复核结论并将task_revision更新为本次发布revision，再发布report。无须再次全量读guidelines、背景文件、Git历史或原始run；有未解决实质问题只简述，否则说明五项已处理、可供用户讨论。
