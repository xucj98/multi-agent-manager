# Multi-Agent Manager（MAM）

## 核心原则

MAM 管理本集群的 agent 任务、workspace、长进程和可选等待，并在负责人空闲时自动通知。使用前阅读本集群的[本地说明](.local/README.md)。`mam` 在 `PROJECT_ROOT` 或其子目录运行；命令细节可用 `mam --help` 查询。

Manager 使用 Codex 原生工具创建 subagent，创建并发布任务要求。执行者调用 `mam task start TASK-ID` 自登记，MAM 从 `CODEX_THREAD_ID` 确认原生协作路径和所属树。一个未归档任务绑定一个执行者，一个执行者只绑定一个未归档任务。`TASK-ID` 同时命名 workspace 和任务分支；换人后这些路径不变。

```text
PROJECT_ROOT/
  .mam/env.json                 # 项目配置
  MAM_ROOT/
    .tasks/TASK-ID/task.md      # Manager 编辑要求
    .tasks/TASK-ID/report.md    # 执行者编辑简报
    .tasks/TASK-ID/files/       # 需要长期留存的一次性附件
  REPO/
  workspace/TASK-ID/
    .task                       # 指向 MAM_ROOT/.tasks/TASK-ID 的软链接
    REPO/                       # 分支 task/TASK-ID 的独立 worktree
    tmp/                        # 本任务的一次性检查文件，归档时清理
  workspace/tmp/                # Manager 无关联任务的临时文件
```

原则上 subagent 只读写自己的 workspace。代码、可复用工具和配置进仓库并提交；正式数据和 checkpoint 放项目约定的稳定产物目录。任务相关的一次性检查或验收记录放 `workspace/TASK-ID/tmp/`。Manager 无关联任务的临时文件放 `workspace/tmp/`，按工作分目录并在阶段收尾时清理；不要将需后续管理的文件留在 `.mam` 或系统临时目录。测试内部自行创建并清理的临时目录不受此限制。

## 安装

安装与项目配置见[安装说明](docs/install.md)。开发、review 和实例试用的隔离方法见[开发指南](docs/development.md)。

## 任务管理

Manager 创建任务并发布要求，再用原生工具通知执行者：

```text
mam task create --title TITLE [--review TARGET]
mam task publish TASK-ID --file task
mam task list [--archived|--all]
mam task status TARGET
mam task archive TARGET --note NOTE [--discard-drafts] [--discard-code]
```

`mam task show [TARGET]` 读取 MAM_BRANCH 上最新发布的要求或报告，不读取草稿。`TARGET` 是 TASK-ID 或当前原生协作树内的完整路径，例如 `/root/worker`；已绑定执行者可省略 TARGET，Manager 显式指定。不同树中的同名路径互不混用；身份不能确认时用 TASK-ID。已归档任务也可用 TASK-ID 查看。

Manager 追加要求时先修改 task.md 并发布，再通知执行者。Review 任务用 `--review TARGET` 引用源任务的最新已发布要求、报告和交付记录。任务状态只有 working、pending、archived；发布报告进入 pending，返工由执行者再次调用 start 进入 working。

归档先检查 job、草稿、代码和 workspace，再清理本任务的 tmp、worktree、独立环境、分支、`.task` 和 workspace。中央任务记录、共享链接目标及 Manager 的 `workspace/tmp` 保留。未合入源仓库主分支的代码不会因报告写了 commit 而被视为留存；若确需舍弃，在 `--note` 说明理由并使用 `--discard-code`。未发布草稿使用 `--discard-drafts` 明确舍弃。取消无交付的空任务可直接归档。

## 执行与交付

```text
mam task start TASK-ID
mam task show
mam workspace add --repo REPO --base COMMIT
mam task publish --file report
mam task publish --file files
```

首次登记和接手时指定 TASK-ID；已绑定执行者返工时可省略。交接前 Manager 让旧执行者结束当前 turn 和 wait；新执行者在旧执行者空闲后调用 start。workspace、worktree、环境、分支、job 和发布记录随任务保留，接手时无需再次创建 worktree。start 不创建 Codex agent。普通问答及 task.md 发布不会自动判定返工。

执行者通过 `.task/report.md` 和 `.task/files/` 编辑简报与附件，通过 publish 分别发布；附件新增、更新、删除由 `--file files` 单独提交。`mam task show` 始终读取最新已发布内容。任务完成后正常结束 turn，由 Manager 验收、安排 review、返工或合入，再归档。

## 进程与通知

预计运行超过 30 分钟的程序需登记；短 smoke 不需要：

```text
mam job add [TARGET] --note NOTE --host HOST --pid PID
mam job list [--task TARGET]
mam job status JOB-ID
mam job archive JOB-ID --note NOTE
mam service status
mam service rebind-manager --note NOTE
```

job 停止只表示进程已停，由执行者检查结果并归档 job。服务在负责人空闲且有待办时通知；原生 subagent 不接受直接唤醒时，Manager 核实后用原生 follow-up 协调。新 Manager 可在旧 Manager 已结束 turn 和 wait 后调用 `rebind-manager` 接管本实例；旧树路径仍属于旧树。

需要在当前 turn 等待时使用 `mam wait`。`mam wait list` 查看等待者；`mam wait stop manager` 或 `mam wait stop --agent AGENT-ID|PATH` 解除等待，不停止 job。通常直接结束 turn 即可。

## MAM 接口说明

参数、返回内容和使用约束见 [task](docs/commands/task.md)、[workspace](docs/commands/workspace.md)、[job](docs/commands/job.md)、[wait](docs/commands/wait.md)、[service](docs/commands/service.md)。后续工作见 [roadmap](docs/roadmap.md)。
