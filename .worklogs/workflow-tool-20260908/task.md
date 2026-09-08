# 任务登记与 workspace 归档工具

## 目标与负责人

负责人：Ptolemy（gpt-5.6-terra max）。用一个小型标准库工具支持任务说明、结果简报、状态查询和 workspace 归档。

本文件在实施中补建，替代此前零散消息中的要求。用户最新明确：smoke 和临时文件清理由 subagent 完成，系统只负责任务管理和归档时移除 workspace。

## 工作区与修改范围

workspace：`/mnt/public/xcj/Projects/workspace/workflow-tool-20260908`，代码 worktree 为其下 `agent-workflow`；初始 base 为 `12195fd`，工作分支 `codex/workspace-lifecycle-tool`，合入分支 `xcj-dev`。
修改 `scripts/ws.py` 与必要的标准库测试，AGENTS.md/README.md 由 Manager 编写。开始工作和收到更新时先读本文件与管理库入口。

## 当前要求

- 每项任务的持久说明位于 `.worklogs/<task-id>/task.md`，结果简报位于同目录 `report.md`，进入 Git。Manager 更新说明后才通知 agent 执行追加要求。
- 简报包含完成/未完成情况、workspace、涉及各 worktree 的完整 commit 和验证结论。review 自己也有说明和简报，引用被 review 的任务及交付。
- `.local/tasks/` 存管理状态，默认定位稳定原仓库；从 linked worktree 调用使用同一处状态。workspace 默认在本集群 Projects/workspace。
- 登记与任务说明关联；`status` 可列全部任务，显示负责人、workspace、状态和仍在运行的 job。状态是负责人维护的任务状态，不冒称实时探测 agent。
- 保留现有 register/status/job/handoff/deliver/accept 命令可用部分，增加或将 close 改名为 archive。提交报告后等待接收，归档保留任务说明、简报和可查询的归档状态，移除 workspace；不要删除历史任务状态记录。
- 同一个 workspace 不得被多个任务重复登记，防止绕过另一个任务的 job 保护。采用简易登记锁，避免多机同时写坏。
- 运行 job 人工登记与释放，未释放或状态未知时不能归档；负责人可交接。首次注册允许尚未建 worktree 的已规划 workspace 或只读任务空目录，以便开工前登记（若会扩大代码，请先说明最小替代流程）。
- deliver/accept 必须有关联任务说明和结果简报；归档前核对交付 commit 与各 worktree HEAD，保护未提交和未跟踪代码。报告内容由 agent 编写，不生成假结论。
- 归档只移除已登记的 worktree 及其独立 `.venv`，删除软链接本身而不删除共享目标。gitignored 的 data/assets/eval_result/.local 软链接必须正常支持；真实数据/checkpoint 实体不能当临时目录删除。
- 不自动清理 smoke、实验结果、外层 temp 或任意 /tmp；未处理文件具体报错，由负责人处理后重试。归档只移除清理后的 workspace 外壳。
- 全部预检完成后再删除，部分 Git 移除失败能够重试剩余项；不删除提交分支引用，不做自动归档代码快照。
- 不加入环境 provenance、后台调度、UI、权限系统、复杂兼容或迁移框架。保留已有简洁实现，避免重写和机械压行；新增代码先评估是否必要。

## 必要验证与交付

用临时真实 Git 仓库验证：正常登记/交付/接收/归档，报告或说明缺失拒绝，待验收拒绝，活跃 job 拒绝，重复 workspace 拒绝，dirty/untracked 保护，ignored 共享软链接目标保留，真实 ignored checkpoint 拒绝，外层 temp 不自动删除，路径含空格，失败后重试。测试完成自行删除临时测试文件。

先完成可运行版本及测试，提交后给 Manager 和独立 reviewer 精确 commit；在本目录 report.md 写完成情况、workspace、worktree 完整 commit、测试结论和任何限制。自身 workspace 待 Manager 验收后由新工具归档。
