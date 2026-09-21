# 管理交接审计（2026-09-21）
用户要求先理解论文与当前实验，和用户梳理后再推进后续。模型固定 GPT 5.6-terra，reasoning max。
先读 MAM AGENTS/README 核心与任务管理/.local/README，再 mam task show 本 ea38430d-3538-49ea-9dac-0b022cee69d7。创建自己的 RMBench worktree：mam workspace add ea38430d-3538-49ea-9dac-0b022cee69d7 --repo RMBench --base HEAD；阅读 AGENTS 及实验规范。仅只读审计旧任务、结果、模型、远端状态，不启动训练/评测，不终止进程、不删除文件、不改旧任务或共享论文。报告写自己 .tasks/ea38430d-3538-49ea-9dac-0b022cee69d7/report.md 并 mam task publish --file report，支持资料写自己的 workspace。可通过 SSH 只读访问集群，但先读 .local 对应集群说明。避免递归遍历巨型模型/视频目录，优先最新 report 与 JSON/日志定位。
明确区分计划、owner 声称、原始证据核验、Manager 已验收；按固定训练模型与评测批次分开计数，旧30k/新20k/episode-reset HF不混表。给精确路径、关键数字、状态差异及建议。尽早反馈最关键发现；无需改代码或大规模重跑验收。不要再派 subagent。

## 范围：最新实验结果
审阅 RMBench experiments/memory_chunk_20260910 与 eval_result 最新正式实验，MAM 0acf5d43、f3488141 reports、其他最新已归档HF评测/验收任务，及论文 docs/analysis。重点找9月15日之后的新数据：两任务HF baseline/fixed/event 三eval，swap/battery/cover最新N/S/J，原协议52批之后增量。原始诊断直接复算每批完成数、成功数、seed身份，列accepted与待验收候选，不把smoke算入。对HF尽可能做按初始seed配对差异、trigger覆盖、成本可得性。只读远端C1/C2/C3定位本地尚未回传结果。产出紧凑结果表和最强/最弱证据。
