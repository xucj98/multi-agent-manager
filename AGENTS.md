# 本集群的 agent 协作入口

本仓库服务于本机和 `wuwen-1`。两者共享 `/mnt/public` 下的代码、数据、解释器和缓存；进程在实际运行的主机查询。操作见 [README.md](README.md)，完整接口见 [CLI 说明](docs/task-management-design.zh-CN.md)。

## 任务与工作区

- Manager 先创建任务并发布要求，再启动执行者、绑定 agent ID。每个执行者对应一个未归档任务，使用该任务的 UUID workspace；实施、review 和实验都按此登记。
- 执行者先用 `show` 读取已发布任务及其版本，再阅读涉及库的 `AGENTS.md` 和其中要求的相关规范。任务追加要求由 Manager 写入 task.md、发布后通知执行者。
- 修改代码和独立代码 review 时，通过 `workspace add` 按任务指定的 repo、base commit 创建 worktree。工具调用各库本地入口，创建独立环境和 `task/<uuid>` 分支；同一任务按需添加多个库。
- 讨论、只读调查和监控按任务登记即可，无需创建代码环境。已有任务继续使用自己的 workspace。

## 编辑与交付

- 管理仓库共享 checkout：Manager 编辑 `.tasks/<uuid>/task.md`，执行者编辑自己的 `report.md`。`main` 是发布版本，工作目录修改是草稿；task/report 统一通过 CLI 发布，读取发布版本使用 `show`。
- 执行者完成后发布简报，注明所依据的任务版本、完成与未完成内容、workspace、各库交付 commit、验证结论和成果位置。review 基于固定版本的任务、简报与代码，在自己的 workspace 验证。
- 新工作记录统一放在本仓库 `.tasks/`。业务库保留本库的开发规范和实验记录。
- 执行者登记自己启动的长任务进程。进程停止后，按任务要求记录结果、处理临时文件，再归档 job。Manager 用 `job list --attention` 查找执行者已空闲的待处理进程并通知其继续工作。
- Manager 决定归档任务时，工具删除登记的 worktree、独立环境和任务分支，保留共享数据及任务记录。smoke 和其他临时产物由执行者按任务及所属库规范清理。

## 修改管理工具

实现使用 Python 标准库。代码修改和独立代码 review 使用自己的 worktree；运行 `python -B -m unittest discover -s tests -v` 验证。修改删除操作时，验证其保留软链接目标、拒绝删除未登记目录或未提交内容，并保留仍有运行进程的 workspace。
