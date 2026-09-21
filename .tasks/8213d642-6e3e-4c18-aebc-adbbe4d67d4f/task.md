# 管理交接审计（2026-09-21）
用户要求先理解论文与当前实验，和用户梳理后再推进后续。模型固定 GPT 5.6-terra，reasoning max。
先读 MAM AGENTS/README 核心与任务管理/.local/README，再 mam task show 本 8213d642-6e3e-4c18-aebc-adbbe4d67d4f。创建自己的 RMBench worktree：mam workspace add 8213d642-6e3e-4c18-aebc-adbbe4d67d4f --repo RMBench --base HEAD；阅读 AGENTS 及实验规范。仅只读审计旧任务、结果、模型、远端状态，不启动训练/评测，不终止进程、不删除文件、不改旧任务或共享论文。报告写自己 .tasks/8213d642-6e3e-4c18-aebc-adbbe4d67d4f/report.md 并 mam task publish --file report，支持资料写自己的 workspace。可通过 SSH 只读访问集群，但先读 .local 对应集群说明。避免递归遍历巨型模型/视频目录，优先最新 report 与 JSON/日志定位。
明确区分计划、owner 声称、原始证据核验、Manager 已验收；按固定训练模型与评测批次分开计数，旧30k/新20k/episode-reset HF不混表。给精确路径、关键数字、状态差异及建议。尽早反馈最关键发现；无需改代码或大规模重跑验收。不要再派 subagent。

## 范围：执行进度和遗留任务
核查全部8个现存旧任务的发布报告（尤其2a792e9a、f0011538、fa928e8d、e34ba9b3、a98a1d8e）与四个stopped job。重点数据9任务50 demos/schema readiness、27 N/S/J checkpoint实际20k完成/回传/恢复/验收；V单卡或双卡profile最新状态。报告矩阵按task/method完成或待验收或阻塞；确认A/wuwen-1/B/C是否有活跃相关长进程、GPU情况（只读）。不得归档旧job/task；确定4个stopped job成功/失败/产物位置与收尾建议。原草稿14/27可能过时，给可复核最新数并区分Manager acceptance。
