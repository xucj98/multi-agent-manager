# Multi-Agent Manager（MAM）

## 核心原则

MAM 用于协助管理本集群的 agents，提供 `mam task`、`mam workspace`、`mam job`、`mam wait`。本集群的信息查看[本地说明](.local/README.md)，所有 `mam` 命令以及 agent 均在本机运行。

使用细节可用 `mam --help` 查询，语法中的大写词需要替换为实际值，方括号表示可选参数。

MAM 创建任务时生成 `TASK-ID`，同时用作任务标识、命名 workspace 和 git branch；`JOB-ID` 标识登记的进程；`AGENT-ID` 由 codex 生成，标识执行 agent。

MAM 使用共享根目录 `MAM_ROOT`：Manager 编辑其中的 `task.md`，执行者编辑自己的 `report.md`。任务和报告通过 `mam task publish` 发布，并使用 `mam task show` 查看，未发布的修改是草稿。

MAM 的任务 TASK-ID 和执行者 AGENT-ID 一一绑定。每个执行者有自己独立的 workspace `PROJECT_ROOT/workspace/TASK-ID`，下面可以建立独立的 worktree，并使用独立的 git branch `task/TASK-ID`。`mam` 需在 `PROJECT_ROOT` 或其各级子目录中使用。

```text
PROJECT_ROOT/
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
mam task create --title TITLE
mam task create --title TITLE --review TARGET-TASK-ID
mam task publish TASK-ID --file task
mam task bind TASK-ID --agent AGENT-ID
mam task archive TASK-ID --note NOTE
```

- `create` 返回 `TASK-ID`；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求；然后发布任务。
- 使用 codex 工具创建 subagent，要求其查看 `AGENTS.md` 并使用 `mam task show TASK-ID` 查看任务；获取 `AGENT-ID`，绑定执行 agent。
- 途中追加要求时，先更新 `task.md` 并发布，再通知执行者读取新版本。
- Review 的 `--review` 接收源任务的 `TASK-ID`。

先用这些可执行命令查看已有任务和等待：

```bash
mam task list
mam job list
mam wait list
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
mam job list
mam job list --task TASK-ID
mam job status JOB-ID
mam job archive JOB-ID --note NOTE
```

进程结束后，先记录结果并处理任务要求的临时文件，再执行 `mam job archive`。Manager 可用 `mam job list --attention` 查找需要跟进的登记。

## 休眠管理

当前工作已处理完、需要保持 active turn 等待时，直接运行：

```bash
mam wait
```

MAM 从 `CODEX_THREAD_ID` 识别调用者。执行者等待自己任务的 jobs；Manager 等待 active 的执行者，并负责非 active 执行者留下的 jobs 和未归档任务。源任务已交给未归档的 review 任务时，Manager 等待 reviewer。

有待处理事项就立即返回；否则最多等待一小时。退出时说明原因，并附上对应 job 或任务的信息。用户的 steer 和 Manager 发来的消息会解除对应等待，queue 消息保持排队。等待结束不会停止 job，也不会归档任务。

查看或手动解除等待：

```text
mam wait list
mam wait stop manager
mam wait stop --agent AGENT-ID
```

## 开发验证

MAM 自身的开发 worktree、环境、验证和合并步骤见[开发说明](docs/development.md)。

详细接口、状态语义和归档保护见[任务管理 CLI 接口说明](docs/task-management-design.zh-CN.md)；参数以 `mam task --help`、`mam workspace --help`、`mam job --help`、`mam wait --help` 及相应子命令的帮助为准。
