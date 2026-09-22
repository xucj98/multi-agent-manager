# 项目迁移执行

目标：将集群 A 的 /mnt/public/xcj/Projects 下 RMBench、openpi、robot-bridge、opendm 完整搬迁到 state-vla/，在 state-vla/multi-agent-manager 创建新的 clone，保留旧 MAM 和当前 manager session 可用。其他顶层内容先分类汇报，不擅自删除。禁止启动 train/eval，禁止停止 MAM service。

先读 AGENTS.md、README.md 和 .local/README.md。本任务是物理仓库迁移，不为待搬迁库新建 worktree（避免制造迁移阻塞）；若需要实际代码开发才创建 worktree。先只读完成 preflight，将源目标存在性、git状态/worktree、未推送分支、活动进程引用路径、环境/软链接风险、新 MAM clone 来源和历史保留方式发给 manager，等待明确放行再执行 mv/clone/配置变更。

保留所有 .git 本地分支及用户未提交文件、正式数据/processed_data/checkpoints/eval。历史已归档171 task；旧 workspace 已清空，不搬迁旧 workspace。旧 MAM 不动、不 reset、不停止 service、不修改旧 .mam/env.json 指向新实例。新项目应独立 .mam/env.json；不要复制旧 service/runtime/session。新 clone 必须保留 project/state-vla 已提交历史（含未推送提交），并保留原远端，说明本地克隆与 Git 对象独立性。不对远端集群作迁移修改。

搬迁后修复必要的本地环境、路径和软链接，验证每个仓库 .local/create_worktree.sh；不添加大面积兼容层/历史入口。不盲目全局替换历史流水中的路径。迁移新 MAM 的 .local 配置应只保留现行需要的内容。根 manager 负责最终独立空白 agent 验收 mam workspace add。

可复用变更进对应仓库；一次性临时检查放本任务 workspace/tmp 并归档前手动清理；简洁 report.md 记录必要结果和限制。禁止生成海量清单/hash/重复交接文件。独立验收和最终归档前不要声称迁移全部完成。项目进展由 manager 协调更新。

用户补充：新 MAM 实例必须继续使用当前 MAM_BRANCH=project/state-vla，保留该分支全部已提交历史，不能只 clone main。新旧实例的 PROJECT_ROOT/MAM_ROOT 分别定位各自目录。

预检补充：manager 发现 4b77c25 合并 main 时仍保留了此前 84bef8c 的过期入口片段：git diff main..project/state-vla -- AGENTS.md docs/install.md 可见。main@ec047d3 是用户审阅并要求合入当前 MAM_BRANCH 的最终文档版本。迁移配置阶段请将这两个文件对齐 main@ec047d3（仅这两个文件），在旧 project/state-vla 提交修正后带入新 clone，报告说明；这是落实此前授权、修复遗漏，不引入新文档规则。先检查若期间用户又有改动不得覆盖。


用户明确修正：新 MAM 的代码和文档全部以 main 为准；只有 .tasks/ 内容从当前 project/state-vla 延续。不要把 project/state-vla 的 AGENTS.md、README.md、docs 或其他代码状态直接作为新 MAM 基线。新实例应从 main checkout/clone，再迁入 .tasks，并配置 MAM_BRANCH=project/state-vla。

Manager 预检裁决：放行物理迁移。OpenDM 编辑器/terminal 旧 cwd 不阻塞，不杀用户进程；报告提示用户切新目录。新 clone 使用 --no-local 保留全部项目分支历史，再用新提交对齐 origin/main 非 .tasks 树（取代此前从 main 新建历史的表述）；旧 MAM 不改。新 .local 必须也保留当前仍需使用的 wuwen-11.md 与 wuwen-4090.md（审核其中 A 路径引用；远端路径不盲改）。保留旧 untracked .tasks/838bfe79-ab08-4c58-9843-f8e84423f0e1/report.md 到新同目录，除非与现有 tracked 文件冲突；当前迁移任务简报稍后正式发布后同步。最终验收/归档后需将旧实例新产生的本次 task/report 文档提交同步到新 project/state-vla，仅同步 .tasks，不能把旧代码树重新带回；确保新实例没有指向旧实例的 active executor/job/runtime。执行者先完成迁移及自检、发布报告并返回，独立验收由 manager 安排。

下一阶段交付：请先更新 /root/Documents/task-state-vla-paper/docs/PROJECT_PROGRESS.zh-CN.md 当前迁移状态：四库实际新路径、新 MAM 入口/分支、未合入业务分支完整保留、实验未启动，注明独立 workspace 验收进行中。不要改变实验数字或科学结论，不追加日志副本，不操作 main.pdf；此文件更新可直接在现有 paper 分支提交（延续用户对项目进展直接提交的授权）。与 reviewer 并行时不要修改新 MAM Git/.local/runtime；最终同步须等 manager 通知。

最终收尾已放行：独立验收 d0ffda49 通过并归档，新实例验收 task 04ca83bb 也已归档。请将 paper 项目进展改为验收完成、任务收尾（准确说明历史 .tasks 文档保留而旧 runtime 不迁移，新 session 由用户创建，旧 MAM service 保持健康、新 service disabled），直接提交。更新旧本任务 report 为完成并发布；然后仅复制旧 MAM 当前受跟踪 .tasks 树中本轮尚未进入新 clone 的 task/report 到新实例并提交，保留新独立验收 task 文档，绝不能以旧树覆盖新树的额外文件、不得重新带入旧代码。原有 838bfe79 未跟踪 report 保留不动。清理本 task workspace/tmp。返回最终 commit、新旧 task/job 列表、非 .tasks diff为空的核对。Manager 随后归档本任务，runtime 不复制。
