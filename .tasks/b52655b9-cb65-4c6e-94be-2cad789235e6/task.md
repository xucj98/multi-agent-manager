# 目标
实现 table-1000 纳入 MAM 的一键 worktree 环境：创建独立 worktree、独立 .venv、uv hardlink 复用缓存、资产软链接，使空白上下文 subagent 仅靠文档即可完成准备和 smoke。
# 范围与要求
先阅读 MAM AGENTS.md、README 核心原则/执行与交付、.local/README.md，了解 mam workspace add 实际调用的 .local 协议。通过 ssh wuwen-2 只读调研 /mnt/public/xcj/Projects 下各 repo 的 .local 参考（若别名不可用，调查本机 ssh 配置及可用对应主机，明确报告）。可并行调研旧源 /mnt/public/xcj/table-1000 的依赖与 smoke 入口，不修改源。
迁移 agent 正在创建 /mnt/public/xcj/Projects/table-1000/table-1000 与共享资产，请与 manager/迁移 agent 协调 base 和资产位置。canonical repo 就绪后，用 mam workspace add TASK-ID --repo table-1000 --base COMMIT 创建独立 worktree；若尚无 .local 入口无法执行，调研受支持引导流程并报告 manager，允许最小 bootstrap 后回到 MAM 协议。
在 task worktree 实施 .local 脚本/文档、需要的依赖锁定和 AGENTS.md 引导。确保新 worktree 有独立 .venv，通过 uv --link-mode hardlink（cache 同文件系统）节约时间空间；共享资产的软链接完整且安全；脚本幂等、失败清楚、可从新任务一键使用。不要硬链接可被工作修改的源代码；不复制旧 venv。根据实际项目做有意义 smoke，验证 hardlink inode 及 venv 独立性。不要运行正式训练。不要自行派发下级 agent。
# 交付验收
提交代码，报告 commit、精确一键命令、依赖来源、cache/资产路径、测试及边界；发布 mam report；后续另有独立 review 和空白上下文验收。
