# 目标
实现 table-1000 纳入 MAM 的一键 worktree 环境：创建独立 worktree、独立 .venv、uv hardlink 复用缓存、资产软链接，使空白上下文 subagent 仅靠文档即可完成准备和 smoke。
# 范围与要求
先阅读 MAM AGENTS.md、README 核心原则/执行与交付、.local/README.md，了解 mam workspace add 实际调用的 .local 协议。通过 ssh wuwen-2 只读调研 /mnt/public/xcj/Projects 下各 repo 的 .local 参考（若别名不可用，调查本机 ssh 配置及可用对应主机，明确报告）。可并行调研旧源 /mnt/public/xcj/table-1000 的依赖与 smoke 入口，不修改源。
迁移 agent 正在创建 /mnt/public/xcj/Projects/table-1000/table-1000 与共享资产，请与 manager/迁移 agent 协调 base 和资产位置。canonical repo 就绪后，用 mam workspace add TASK-ID --repo table-1000 --base COMMIT 创建独立 worktree；若尚无 .local 入口无法执行，调研受支持引导流程并报告 manager，允许最小 bootstrap 后回到 MAM 协议。
在 task worktree 实施 .local 脚本/文档、需要的依赖锁定和 AGENTS.md 引导。确保新 worktree 有独立 .venv，通过 uv --link-mode hardlink（cache 同文件系统）节约时间空间；共享资产的软链接完整且安全；脚本幂等、失败清楚、可从新任务一键使用。不要硬链接可被工作修改的源代码；不复制旧 venv。根据实际项目做有意义 smoke，验证 hardlink inode 及 venv 独立性。不要运行正式训练。不要自行派发下级 agent。
# 交付验收
提交代码，报告 commit、精确一键命令、依赖来源、cache/资产路径、测试及边界；发布 mam report；后续另有独立 review 和空白上下文验收。

# Manager 验收补充
默认一键环境须覆盖当前实际 ManiSkill/reference 工作流，不能只安装 CPU/dev 测试依赖而让后续 agent 手动补核心 simulator/torch。按现有 README/pyproject/旧环境核验依赖；至少执行真实资产加载及场景 smoke，GPU 可用时包含渲染/模拟。可以合理分层安装但默认入口需完成当前工作流。参考 wuwen-2 的版本化脚本加 .local wrapper 模式。验证任意 cwd 的底层入口、重复执行与失败恢复、独立 venv 以及真实 cache inode hardlink 证据。

# 用户追加：outputs 也纳入软链接管理
用户询问软链接数量并明确 outputs 类目录也应软链接。当前 primary 与 task worktree 各只有 .cache 一条顶层链接。请完善集中成果目录：PROJECT_ROOT/outputs/main 供 primary，PROJECT_ROOT/outputs/TASK-ID 供 task worktree，并在各 repo 创建 outputs 软链接指向对应目录，避免多 agent 覆盖且归档 worktree 后保留成果。已有 worktree outputs 内容要安全迁移，遇冲突不能覆盖；不要把历史研究备份当默认输出目录。对数据流核验是否还有其他真正需要共享/集中留存的 repo 顶层目录，按必要性实现并列清单。更新文档、smoke 与 report，明确每个 worktree 顶层业务软链总数/去向（区分 Python venv 内部软链）。

# 用户最新布局要求（覆盖之前路径约定）
用户明确：主仓库不要软链接，PROJECT_ROOT 下面只有 workspace、mam 及各个 repo。保留 MAM 必需隐藏 .mam 配置；所有业务实体目录归属 canonical repo。请由本环境任务协调并完成：将项目 assets 实体迁为 canonical/.cache 实体（先安全移除已核验旧软链），canonical/outputs 为实体，worktree/.cache -> canonical/.cache，worktree/outputs -> canonical/outputs/TASK-ID。uv cache 和本机配置收拢 canonical/.local 内；不再保留 PROJECT_ROOT/assets、outputs、cache 等业务目录。迁移任务负责备份目录收拢 canonical/.local/migration-backup，与你直接协调。更新所有路径、文档、已有worktree软链与验收；确保主repo顶层无业务软链，worktree仅链接实际需要资产/成果，清理先前空目录。主repo Python自身venv内部系统解释器软链无需改变。
