# 目标
为manager做table-1000现状审计，支持研究路线与2–3位新硕士任务分配。不是实现新功能。
# 操作
读MAM规范，回报CODEX_THREAD_ID；通过mam workspace add创建table-1000独立worktree（base=canonical main），读repo AGENTS。阅读docs/proposal/research-proposal.md，并对照README、roadmap、git近期历史、docs/reports、实际data/config/src/tests。不要重跑整套GPU tests、正式生成或训练；优先只读现成证据。明确区分：已实现接口/单元验证/物理闭环/真正人类标注/真实模型实验。计数以实际数据而非文件名或路线图目标；核验Table-10、Table-10-open等各自规模、参考终态/轨迹是否多样、人类偏好是否fixture，语言目标开放性/泄漏边界、现有baselines及下一步缺口。
# 交付
报告含具体文件路径行号或commit作证；列5–8个已完成/未完成项，最重要3个研究瓶颈和适合新硕士的有边界任务（交付/验收/依赖）。不改repo代码、不自行派发agent，保留workspace待验收，按MAM发布report。
