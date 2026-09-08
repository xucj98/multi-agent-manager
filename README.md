# 本集群的 agent 任务管理

工具以 Git 管理任务要求和结果简报，以本地登记记录 workspace、执行者和长任务进程。当前正在实施，完整接口见 [CLI 说明](docs/task-management-design.zh-CN.md)。

## 集群与目录

本机与 wuwen-1 共享 `/mnt/public` 下的代码、数据、解释器和缓存；进程在实际运行主机查询。四个业务库各自维护 `.local/create_worktree.sh`，负责本库独立环境及数据、模型、结果软链接。

管理仓库为 `/mnt/public/xcj/Projects/agent-workflow`。任务文件位于 `.tasks/<uuid>/task.md` 和 `report.md`，管理状态位于 gitignored 的 `.local/tasks/`；workspace 为 `/mnt/public/xcj/Projects/workspace/<uuid>/`。历史工作记录保留在 `.worklogs/`，新任务统一使用 `.tasks/`。

## 使用流程

Manager 创建任务、编辑并发布要求，启动执行者后绑定 agent ID。执行者读取发布版本，再根据任务说明按需创建代码库 worktree。大家直接编辑各自负责的 task.md 或 report.md，通过 CLI 单独发布到 main；读取发布版本无需切换共享工作目录。

长时间运行的进程登记为 job。工具查询进程与执行者状态；已停止但尚未处理的进程由执行者收尾并归档。Manager 通过 attention 筛选找到执行者也已停止工作的待处理进程。

执行者完成后发布简报，Manager 安排独立 review、集成成果并决定何时归档。任务归档移除登记的 worktree、独立环境和本地任务分支，保留任务资料、进程记录及共享软链接指向的实体。

## 简报格式

report.md 首行填写 `task_revision: <通过 show 取得的完整 commit>`，正文写完成/未完成、workspace、各库完整交付 commit、验证结果与成果位置。实验详细记录按所属库要求保存，简报引用其位置。

实际可运行命令将在实现集成后补齐。
