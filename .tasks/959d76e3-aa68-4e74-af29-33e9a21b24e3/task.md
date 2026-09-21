# 管理交接审计（2026-09-21）
用户要求先理解论文与当前实验，和用户梳理后再推进后续。模型固定 GPT 5.6-terra，reasoning max。
先读 MAM AGENTS/README 核心与任务管理/.local/README，再 mam task show 本 959d76e3-aa68-4e74-af29-33e9a21b24e3。创建自己的 RMBench worktree：mam workspace add 959d76e3-aa68-4e74-af29-33e9a21b24e3 --repo RMBench --base HEAD；阅读 AGENTS 及实验规范。仅只读审计旧任务、结果、模型、远端状态，不启动训练/评测，不终止进程、不删除文件、不改旧任务或共享论文。报告写自己 .tasks/959d76e3-aa68-4e74-af29-33e9a21b24e3/report.md 并 mam task publish --file report，支持资料写自己的 workspace。可通过 SSH 只读访问集群，但先读 .local 对应集群说明。避免递归遍历巨型模型/视频目录，优先最新 report 与 JSON/日志定位。
明确区分计划、owner 声称、原始证据核验、Manager 已验收；按固定训练模型与评测批次分开计数，旧30k/新20k/episode-reset HF不混表。给精确路径、关键数字、状态差异及建议。尽早反馈最关键发现；无需改代码或大规模重跑验收。不要再派 subagent。

## 范围：科学评估
完整阅读 /root/Documents/task-state-vla-paper 论文源文件与 docs/EXPERIMENT_PLAN、RESEARCH_POSITIONING、RESULT_ANALYSIS_AND_FOLLOWUPS、STATE_PREDICTION_FREQUENCY、reviews/20260915-plan-independent-review；查看最新MAM cba8b004科学审稿报告及用户研究决策记录。独立判断：核心主张、先前实验如何回答问题、已支持/尚不支持的假设、哪些计划保留/降级/应补最小区分实验；特别单seed、S/J整套协议混杂、HF固定vs边界刷新LR、J forecast≠已发生状态、V成本。不要外网扩展文献或新跑实验。交付简洁科学裁决建议和关键风险；最新数由另一个agent核查，不重复原始数据遍历。
