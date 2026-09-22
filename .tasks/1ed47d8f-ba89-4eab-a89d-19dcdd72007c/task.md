# 项目迁移执行

目标：将集群 A 的 /mnt/public/xcj/Projects 下 RMBench、openpi、robot-bridge、opendm 完整搬迁到 state-vla/，在 state-vla/multi-agent-manager 创建新的 clone，保留旧 MAM 和当前 manager session 可用。其他顶层内容先分类汇报，不擅自删除。禁止启动 train/eval，禁止停止 MAM service。

先读 AGENTS.md、README.md 和 .local/README.md。本任务是物理仓库迁移，不为待搬迁库新建 worktree（避免制造迁移阻塞）；若需要实际代码开发才创建 worktree。先只读完成 preflight，将源目标存在性、git状态/worktree、未推送分支、活动进程引用路径、环境/软链接风险、新 MAM clone 来源和历史保留方式发给 manager，等待明确放行再执行 mv/clone/配置变更。

保留所有 .git 本地分支及用户未提交文件、正式数据/processed_data/checkpoints/eval。历史已归档171 task；旧 workspace 已清空，不搬迁旧 workspace。旧 MAM 不动、不 reset、不停止 service、不修改旧 .mam/env.json 指向新实例。新项目应独立 .mam/env.json；不要复制旧 service/runtime/session。新 clone 必须保留 project/state-vla 已提交历史（含未推送提交），并保留原远端，说明本地克隆与 Git 对象独立性。不对远端集群作迁移修改。

搬迁后修复必要的本地环境、路径和软链接，验证每个仓库 .local/create_worktree.sh；不添加大面积兼容层/历史入口。不盲目全局替换历史流水中的路径。迁移新 MAM 的 .local 配置应只保留现行需要的内容。根 manager 负责最终独立空白 agent 验收 mam workspace add。

可复用变更进对应仓库；一次性临时检查放本任务 workspace/tmp 并归档前手动清理；简洁 report.md 记录必要结果和限制。禁止生成海量清单/hash/重复交接文件。独立验收和最终归档前不要声称迁移全部完成。项目进展由 manager 协调更新。

用户补充：新 MAM 实例必须继续使用当前 MAM_BRANCH=project/state-vla，保留该分支全部已提交历史，不能只 clone main。新旧实例的 PROJECT_ROOT/MAM_ROOT 分别定位各自目录。

预检补充：manager 发现 4b77c25 合并 main 时仍保留了此前 84bef8c 的过期入口片段：git diff main..project/state-vla -- AGENTS.md docs/install.md 可见。main@ec047d3 是用户审阅并要求合入当前 MAM_BRANCH 的最终文档版本。迁移配置阶段请将这两个文件对齐 main@ec047d3（仅这两个文件），在旧 project/state-vla 提交修正后带入新 clone，报告说明；这是落实此前授权、修复遗漏，不引入新文档规则。先检查若期间用户又有改动不得覆盖。
