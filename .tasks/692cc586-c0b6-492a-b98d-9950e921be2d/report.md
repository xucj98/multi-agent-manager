task_revision: 3bc5f4f192afdf84c633048901b6b325479a315c

结论：NO-GO（代码、help 与 status 投影通过；README 有一个阻塞性操作流程缺口）。

阻塞：README 已删去共享管理 checkout 的职责和发布规则。空白执行者无法只靠操作手册得知 Manager 编辑 task.md、执行者编辑 report.md，main 是已发布版本而工作目录是草稿；也未说明追加要求要先编辑 task.md、publish 后通知执行者，发布 report 后保留 worktree 供 Manager archive。这些是操作流程，不是输出字段规格，缺失后需跳到设计文档才能正确交付。建议在任务管理/执行与交付各补一句，保留现有简洁命令表。

建议同时将 README“只读调查…不需要创建 workspace”改为“不需要创建 worktree/环境”；task create 本身会登记空 workspace，当前表述有歧义。

通过：固定提交 b338dbdd4398af307fd070606288101b8c1d2901 的 AGENTS wait 规则只适用于需保持 active turn 的长任务；20 个顶层及递归子命令 --help 均实际运行，TASK-ID/JOB-ID/AGENT-ID 与其他大写 metavar 一致，dest 未变。临时 root 实测 task status 为只读 cached 投影，正常/unknown（含 error 与 last_known）/archived/review/requirements_changed/交付版本均可定位，job status 只显示必要摘要。`.venv/bin/python -B -m unittest discover -s tests -v`：32 passed；`git diff --check b338dbdd^ b338dbdd`：通过。

workspace: /mnt/public/xcj/Projects/workspace/692cc586-c0b6-492a-b98d-9950e921be2d/multi-agent-manager
reviewed commit: b338dbdd4398af307fd070606288101b8c1d2901
清理：临时 root、短进程和本次源码 pycache 已清理；未修改实现、未占 GPU、未派 agent，worktree 干净。
