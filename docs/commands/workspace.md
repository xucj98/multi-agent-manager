# mam workspace

为任务创建独立 worktree 和开发环境。任务可涉及多个仓库，每个仓库分别创建。

## 接口

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam workspace add TASK-ID --repo REPO --base COMMIT` | 执行者 | 从 PROJECT_ROOT/REPO 的指定 commit 创建任务 worktree 和环境，登记并返回路径、分支、base commit 和创建状态。 |

`REPO` 是 PROJECT_ROOT 下的仓库目录名；源目录必须是该仓库的主 checkout，并有非软链接的 `.local/create_worktree.sh`。`COMMIT` 可以是可解析为 commit 的分支、标签或提交号，具体由任务要求指定。

创建后的路径为 `PROJECT_ROOT/workspace/TASK-ID/REPO`，分支为 `task/TASK-ID`。同一任务在不同仓库使用相同分支名。

## 环境与后续使用

MAM 调用仓库的 `.local/create_worktree.sh`，依次传入 base commit、任务分支名和 workspace 根目录。脚本负责创建 worktree、安装环境及建立共享软链接；这些规则由各仓库决定。开发 MAM 时，每个 worktree 使用独立的 `.venv`。

同一任务、仓库和 base 重复调用时复用已登记的 worktree；创建失败会保留记录及错误，处理后可重试。通过 `mam task status TASK-ID` 查看已登记的仓库。执行者交接后继续使用原 workspace、worktree、环境和分支；目录名与分支名始终使用 TASK-ID，不随执行者或 Manager 更换而改变。

任务归档时统一移除 worktree、独立环境和任务分支，共享软链接的目标保留。归档前的文件整理见 [mam task](task.md#归档)。

## 待开发

### 调用者与任务定位

接口调整为 `mam workspace add [TARGET] --repo REPO --base COMMIT`，沿用 [任务定位规则](task.md#调用者与任务定位)。已绑定执行者可省略 TARGET，其他任务可用 TASK-ID 或协作路径指定；磁盘路径仍为 `workspace/TASK-ID/REPO`，分支仍为 `task/TASK-ID`。

### 任务文件入口

创建任务 workspace 时，在 `workspace/TASK-ID` 下建立 `.task` 软链接，指向 `MAM_ROOT/.tasks/TASK-ID`。执行者通过 `.task/report.md` 和 `.task/files/` 编辑报告与附件，再用 MAM 发布；task.md 仍由 Manager 修改，执行者通过 `mam task show` 读取最新已发布要求。

交接时沿用该链接。归档时删除链接，保留中央任务目录；报告、附件和代码仍按任务归档要求检查。链接提供统一文件入口，不改变文件的发布规则，也不构成访问权限隔离。

### 跨集群同步

提供跨集群同步接口，将任务 worktree 和指定文件同步到目标集群，并支持结果取回。集群连接和路径可配置，不绑定具体训练、评测项目。

同步仍属于当前实例和 TASK-ID，支持查看进度及中断后继续。远端环境按目标集群准备；`mam job submit` 可在准备好的远端 workspace 中运行。具体同步子命令和参数待定。
