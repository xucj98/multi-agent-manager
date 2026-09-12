# Multi-Agent Manager（MAM）

## 核心原则

MAM 用于协助管理本集群的 agents，提供 `mam task`、`mam workspace`、`mam job`，并自动唤醒需要处理后续工作的负责人。本集群的信息查看[本地说明](.local/README.md)，所有 `mam` 命令以及 agent 均在本机运行。

使用细节可用 `mam --help` 查询，语法中的大写词需要替换为实际值，方括号表示可选参数。

MAM 创建任务时生成 `TASK-ID`，同时用作任务标识、命名 workspace 和 git branch；`JOB-ID` 标识登记的进程；`AGENT-ID` 由 codex 生成，标识执行 agent。

MAM 使用共享根目录 `MAM_ROOT`：Manager 编辑其中的 `task.md`，执行者编辑自己的 `report.md`。任务和报告通过 `mam task publish` 发布，并使用 `mam task show` 查看，未发布的修改是草稿。

MAM 的任务 TASK-ID 和执行者 AGENT-ID 一一绑定。每个执行者有自己独立的 workspace `PROJECT_ROOT/workspace/TASK-ID`，下面可以建立独立的 worktree，并使用独立的 git branch `task/TASK-ID`。`mam` 需在 `PROJECT_ROOT` 或其各级子目录中使用。

```text
PROJECT_ROOT/
  .mam/env.json               # 项目配置
  MAM_ROOT/                   # MAM 根目录
    .tasks/TASK-ID/task.md    # Manager 编辑任务要求
    .tasks/TASK-ID/report.md  # 执行者编辑结果简报
  REPO/                       # 一个项目下可以有多个 git 仓库
  workspace/TASK-ID/          # 执行者的独立工作空间
    REPO/                     # 按需创建的 worktree，分支为 task/TASK-ID
```

## 安装

安装与更新见[安装说明](docs/install.md)。

## 任务管理

Manager 创建任务、填写任务要求并发布，再绑定执行 agent，agent 任务完成后根据情况启动 review 或归档。

```text
mam task create --title TITLE [--review TARGET-TASK-ID]
mam task publish TASK-ID --file task
mam task bind TASK-ID --agent AGENT-ID
mam task archive TASK-ID --note NOTE
```

- `create` 返回 `TASK-ID`；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求；然后发布任务。
- 使用 codex 工具创建 subagent，要求其查看 `AGENTS.md` 并使用 `mam task show TASK-ID` 查看任务；获取 `AGENT-ID`，绑定执行 agent。
- 途中追加要求时，先更新 `task.md` 并发布，再通知执行者读取新版本。
- Review 任务使用 `--review` 接收源任务的 `TASK-ID`。

查看已有任务和进程：

```bash
mam task list
mam job list
```

针对一个任务读取登记信息和已发布要求：

```text
mam task status TASK-ID
mam task show TASK-ID
```

`mam task status` 显示已保存的 job 观测，不会实时探测 job。

## 执行与交付

启动 prompt 会提供 `TASK-ID`。先运行 `mam task show TASK-ID`，再为每个需要修改或独立 review 的仓库创建 worktree：

```text
mam workspace add TASK-ID --repo REPO --base COMMIT
```

完成后，在 `MAM_ROOT` 的 `.tasks/TASK-ID/report.md` 写结果简报，记录完成项、workspace 与交付 commit、验证结果和成果位置。然后发布简报：

```text
mam task publish TASK-ID --file report
```

交付后清理临时文件，保留 worktree 供 Manager 验收、归档。

## 进程管理

预计运行超过一小时的正式数据生成、训练或评估需要登记；短 smoke 不需要。登记、查询和收尾使用：

```text
mam job add TASK-ID --note NOTE --host HOST --pid PID
mam job list [--task TASK-ID]
mam job status JOB-ID
mam job archive JOB-ID --note NOTE
```

- HOST 可以使用 ssh 别名或 username@hostname。
- list 不提供 TASK-ID 时显示所有任务中未归档的 job。

job 状态包括 `running`、`stopped`、`archived`。进程停止后，由执行者检查结果、完成收尾，再归档 job。`mam job archive` 可归档任意已登记 job，只结束 MAM 对它的跟踪并保留记录，不停止进程。`mam task archive` 要求其所有 job 已归档。

## 自动跟进

当前可执行的工作处理完后，正常结束 turn。已登记的长进程可以继续运行，MAM 会在需要处理后续工作时唤醒负责人，无需调用等待命令或定时查询状态。

- 有未归档的 stopped job：由执行者处理，即使同一任务还有其他 running job。
- 只有 running job：MAM 继续监控，执行者可以结束 turn。
- 没有 job 或所有 job 都已归档，且执行者已结束 turn：由 Manager 检查成果，决定归档、委派 review 或追加要求。源任务已交给未归档的 review 任务时，等待 reviewer 的结果。

唤醒消息包含待处理 job 的 `JOB-ID` 和用途，或任务的 `AGENT-ID`、`TASK-ID` 和标题。进程停止不代表实验成功，结束 turn 不代表任务已完成；仍需按任务要求检查和交付成果。

负责人正在工作时，MAM 保留待办，避免打断当前 turn。服务的启动、停止和故障处理见[安装说明](docs/install.md)，查看当前服务状态使用：

```text
mam service status
```

## MAM 开发指南

MAM 自身的开发 worktree、环境、验证和合并步骤见[MAM 开发指南](docs/development.md)。

## MAM 设计细节

详细接口、状态语义和归档保护见[MAM 设计细节](docs/task-management-design.zh-CN.md)，日常使用无需翻阅；参数以 `mam --help` 及相应子命令的帮助为准。
