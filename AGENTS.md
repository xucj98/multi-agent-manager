# 本集群的 agent 协作入口

本仓库管理当前集群的开发任务。本机与 `wuwen-1` 共享 `/mnt/public` 文件系统，同一路径下的代码、数据和环境两边都可见。具体操作见 [README.md](README.md)。

- 每个 subagent 开工前读取 Manager 分配的 `.worklogs/<task-id>/task.md`，确认目标、交付要求和自己的 workspace，再读取涉及代码库的 `AGENTS.md` 与相关规范。
- 任务要求发生变化时，Manager 先更新任务说明，再通知 agent；agent 按更新后的说明继续工作。
- 讨论、只读调查和监控直接读取已有资料。代码修改与独立 review 使用自己的 worktree，需要运行项目代码时才安装环境。
- 工作结束后，在同一任务目录提交 `report.md`：写明完成和未完成的内容、workspace、各 worktree 的 commit，以及验证结果。
- review agent 有自己的任务说明、workspace 和简报，依据被 review 的任务要求及交付 commit 独立验证。
- smoke、测试文件和其他临时产物由任务负责人处理。Manager 接收成果后归档任务，移除 workspace，保留任务说明、简报和代码提交。
- 仍有训练、评测或服务运行时，登记其依赖目录与负责人；交接完成前保留所需 workspace。
