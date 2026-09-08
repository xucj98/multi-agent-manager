# 本集群的 agent 协作入口

本仓库管理本机与 wuwen-1 的任务；两者共享 `/mnt/public` 下的代码、数据和环境。操作见 [README.md](README.md)，接口见 [CLI 说明](docs/task-management-design.zh-CN.md)。

- Manager 创建并发布 `.tasks/<uuid>/task.md`，启动执行者并绑定 agent ID。执行者先读取已发布任务要求及版本，再读取涉及代码库的 AGENTS.md 与相关规范。
- 实施、review 和实验都是任务，由执行者完成。执行者通过工具在自己的 UUID workspace 按需创建各库 worktree，分支统一为 `task/<uuid>`。
- 管理仓库的任务文件共享编辑：Manager 写 task.md，执行者写自己的 report.md。main 是已发布版本，工作目录修改是草稿，发布统一通过 CLI。追加要求先发布，再通知执行者。
- 简报注明所依据的任务版本、完成与未完成内容、workspace、交付 commits 和验证结论。review 依据固定版本的任务要求、简报与代码，在自己的 workspace 验证。
- 长时间运行的进程由执行者登记，结束后按任务要求处理并归档该进程记录。Manager 查询需要介入的进程，通知已停止执行的负责人继续工作。
- 临时文件和 smoke 按任务及业务库规范处理。Manager 决定任务归档时，工具移除登记的 worktree、独立环境和工作分支，保留共享实体与任务记录。
- 本仓库工具使用 Python 标准库。代码修改与独立代码 review 使用自己的 worktree；任务说明和简报在共享管理目录编辑。业务算法、GPU使用及实验产物规则由任务和所属库规定。

本轮首次实施在 CLI 就绪前由 Manager 初始化任务登记和发布；CLI 就绪后统一使用新入口。
