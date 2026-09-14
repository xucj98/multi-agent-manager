# 修复B/C发布就绪缺口

依据空白验收 bed9952b-c1a2-40ec-9f6d-34feeba91aa5/report.md，Manager裁决：三参数使用路径本身已通过三个仓库；剩余主要是部署前置未满足，不应给用户增加purpose/deployment参数或重复手册。

先读README核心/任务执行、.local/README及B/C入口、涉及仓库AGENTS。实际核查B稳定根缺RMBench/robot-bridge、C稳定openpi缺34002dce；最小修复使文档承诺可用。B根/mnt/public3/xcj/Projects/state-vla，C根/mnt/public/xcj/Projects/state-vla。原验收base：openpi34002dce65962734c59725a0f6d982ae2c438a2d、RMBenchf401f5279c95451eb424ac98b831bab5552b2120、bridgef9626636c4776d8eb15f9c556775cb2d12c000e5。

授权：只补缺失稳定仓库、所需git objects/受管入口和必要文档恢复说明。获取commit不重置已有稳定分支，不改活跃workspace、不重装他人环境、不动GPU进程/模型。复用现有缓存和共享依赖；任何预计>30min传输登记MAM job。不部署整个无关数据集。核验来源与完整commit；若需大范围环境变更，先交具体缺口由Manager裁决。

文档保持简洁：README只入口；集群文档只特有规范；通用仓库操作留repo文档。发布方须保证指定base可达，缺库/缺base不让新使用者猜代码或换commit。修复后以本任务独立worktree做必要CPU检查，记录精确复验命令但不替代空白使用者验收。交付commit/远端变化/验证和遗留；Manager再请原空白使用者仅按修订说明重试三个失败分支。

第一轮仅返回CODEX_THREAD_ID并结束以便绑定；正式工作待绑定通知。
