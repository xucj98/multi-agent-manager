# Multi-Agent Manager（MAM）

## 核心原则

MAM 用于协助管理本集群的 agents，提供 `mam task`、`mam workspace`、`mam job` 和可选的 `mam wait`，并自动唤醒需要处理后续工作的负责人。本集群的信息查看[本地说明](.local/README.md)，所有 `mam` 命令以及 agent 均在本机运行。

使用细节可用 `mam --help` 查询，语法中的大写词需要替换为实际值，方括号表示可选参数。

MAM 创建任务时生成 `TASK-ID`，同时用作任务标识、命名 workspace 和 git branch；`JOB-ID` 标识登记的进程；`AGENT-ID` 是 Codex 线程 ID。`TARGET` 可用 TASK-ID，或绑定后当前原生协作树内的完整执行者路径，如 `/root/worker`；已绑定执行者的日常操作可省略 TARGET。

MAM 使用共享根目录 `MAM_ROOT`：Manager 编辑其中的 `task.md`，执行者编辑自己的 `report.md`。任务和报告通过 `mam task publish` 发布，并使用 `mam task show` 查看，未发布的修改是草稿。

每个未归档任务最多绑定一个执行者，每个执行者同时只绑定一个未归档任务。每个任务有独立的 workspace `PROJECT_ROOT/workspace/TASK-ID`，下面可以建立独立的 worktree，并使用独立的 git branch `task/TASK-ID`。交接给新执行者时，沿用原目录、分支、环境和 job。**原则上每个 subagent 都只能读写自己的 workspace**。`mam` 需在 `PROJECT_ROOT` 或其各级子目录中使用。

```text
PROJECT_ROOT/
  .mam/env.json               # 项目配置
  MAM_ROOT/                   # MAM 根目录
    .tasks/TASK-ID/task.md    # Manager 编辑任务要求
    .tasks/TASK-ID/report.md  # 执行者编辑结果简报
    .tasks/TASK-ID/files      # 其他有必要保留的一次性文件
  REPO/                       # 一个项目下可以有多个 git 仓库
  workspace/TASK-ID/          # 执行者的独立工作空间
    .task                     # 软链接指向 MAM_ROOT/.tasks/TASK-ID
    REPO/                     # 按需创建的 worktree，分支为 task/TASK-ID
    tmp/                      # 本任务临时文件，归档时自动清理
```

Manager 主要负责任务的推进，进行排期，派遣 subagent 工作，验收，裁决。细节工作交给 subagent 进行，manager 主要通过 report 或者协作工具了解进展。subagent 工作可能出错，manager 可以根据需要派发 reviewer，并对最终结果进行裁定。涉及项目的核心工作，如后续计划安排，roadmap 调整，编写 README.md, AGENTS.md 这类工作由 manager 自己完成。Manager可以直接修改 PROJECT_ROOT/REPO，无需创建 task，worktree。

### 文件留存原则

为了保证项目的长期可维护性，需要严格控制留存的内容。项目文件根据用途分成4类：
1. 后续会**重复使用**的代码、配置、分析工具。进入各个 `REPO`，随 git 提交。
2. 一次性，但有必要保留以解释本次结论的分析代码或附件。进入 `.tasks/TASK-ID/files/`，通过 `mam task publish --file files` 发布。
3. 正式数据、checkpoint、评测原始结果。放在 `REPO` 约定的稳定产物目录，不进入 git。
4. 一次性检查脚本、调试输出、中间版本和验收校验记录。无论由 Manager 还是执行者生成，都放在关联任务的 `workspace/<task-id>/tmp/`，归档时自动清理。

Manager 无关联任务的临时文件统一放在 `PROJECT_ROOT/workspace/tmp/`，按工作分目录。阶段收尾时检查并清理已不需要的文件，需要长期保留的按上述分类转存。

## 安装

安装与更新见[安装说明](docs/install.md)。

## 任务管理

Manager 创建任务、填写并发布要求，再通过 Codex 原生工具创建 subagent，提供 TASK-ID 并要求其阅读 AGENTS.md 和已发布任务。执行者自行登记；完成后由 Manager 验收、安排 review 或归档。

```text
mam task create --title TITLE [--review TARGET]
mam task publish TASK-ID --file task
mam task archive TARGET --note NOTE
```

- `create` 返回 TASK-ID；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求，再用该 TASK-ID 首次发布，无需先绑定 subagent。
- 途中追加要求时，先更新并发布 task.md，再通知执行者读取。执行者和 reviewer 始终以最新已发布要求为准；report 无需绑定要求版本。
- Review 任务用 `--review TARGET` 指定源任务，结合最新 task.md、report.md 和交付代码独立验收。
- 返工时通知原执行者调用 `mam task start` 后继续；需要换人时，先确认旧执行者已结束 turn 和 wait，再让新执行者 `mam task start TASK-ID` 接手。原 workspace、分支、环境和 job 保留，无需再次创建。
- 交付后的验收、留存和归档按[任务收尾](#任务收尾)完成。

查看已有任务、进程及一个任务的详情：

```text
mam task list
mam job list
mam task status [TARGET]
mam task show [TARGET]
```

`mam task status` 显示已保存的 job 观测，不会实时探测。Manager 可用 `/root/worker` 定位当前协作树内的执行者；其他树或归档任务用 TASK-ID。

## 执行与交付

启动 prompt 会提供 TASK-ID。首次执行或接手时调用 start，再读取已发布要求，为每个需要修改或独立 review 的仓库创建 worktree：

```text
mam task start TASK-ID
mam task show
mam workspace add --repo REPO --base COMMIT
```

MAM 从 CODEX_THREAD_ID 自动确认执行者身份与协作路径。已绑定执行者返工时调用 `mam task start`，任务进入 working；发布 report 后进入 pending，归档后为 archived。普通问答无需 start。该命令不创建 agent，也不更换任务目录或分支。

完成一个阶段、遇到阻塞或准备交接时，更新 `.task/report.md` 草稿，简洁记录当前进展、验证结果、阻塞和下一步，不记操作流水账。Manager 可读取中央草稿了解进度；`mam task show --file report` 仍只返回已发布交付。草稿更新不改变状态，最终交付时再发布，不另建 progress.md。

完成后按[文件留存原则](#文件留存原则)整理成果，并提交 worktree 中的交付代码。通过 workspace 根目录的 `.task/report.md` 写简报，说明完成项、交付 commit、验证结果和成果位置；需要保留的一次性附件放 `.task/files/`。发布前将进度草稿整理为交付简报，再分别发布：

```text
mam task publish --file files
mam task publish --file report
```

没有附件时可省略 files 发布。发布附件会同步新增、修改和删除，report 不自动包含附件。执行者无需在共享管理仓库手工 git add/commit。读取要求仍用 `mam task show`，不能以 `.task/task.md` 中的未发布草稿代替。

### 任务收尾

1. 执行者整理代码和产物，同步相关文档；需保留的文件按上述规则转存，临时检查文件留在任务 tmp。报告说明结果、验证方法、未解决问题和产物位置，让接手者不依赖原对话也能理解。
2. 执行者检查已停止 job 的结果，完成项目侧收尾后归档 job。仍需监控的进程保留登记，任务暂不归档。
3. 执行者提交交付代码，发布附件和最终 report；Manager 按最新 task.md 验收，需要时独立 review，并对 review 结论作出裁决。返工继续原任务。
4. Manager 确认代码已合入主分支，必要报告和附件已发布，然后调用 `mam task archive TARGET --note NOTE`；明确舍弃时使用 `--discard-code` 或 `--discard-drafts` 并在 note 说明理由。归档检查留存，再清理 tmp、worktree、独立环境、任务分支及 `.task` 链接，保留中央任务记录和共享链接目标。
5. Manager 核对归档结果，确认任务已归档、工作目录和分支已清理。失败时按提示处理后重试；阶段结束时也检查自己的 workspace/tmp，将必要内容转存后清理其余文件。

MAM 提供通用的留存检查和清理工具；数据、checkpoint 等产物保留多久、放在哪里，由各项目规定。接口和拒绝归档的条件见 [mam task](docs/commands/task.md#附件与归档)。

## 进程管理

预计运行超过 30 分钟的程序（如正式数据生成、训练、评估、传输拷贝）需要登记；短 smoke 不需要。登记、查询和收尾使用：

```text
mam job add [TARGET] --note NOTE --host HOST --pid PID
mam job list [--task TARGET]
mam job status JOB-ID
mam job archive JOB-ID --note NOTE
```

- HOST 可以使用 ssh 别名或 username@hostname。
- list 不提供 TARGET 时显示所有任务中未归档的 job；已绑定执行者登记 job 时可省略 TARGET。

job 状态包括 `running`、`stopped`、`unknown`、`archived`；unknown 表示暂时无法确认。进程停止后，由执行者检查结果、完成收尾，再归档 job。`mam job archive` 可归档任意已登记 job，只结束 MAM 对它的跟踪并保留记录，不停止进程。`mam task archive` 要求其所有 job 已归档。

拟议接口为 `mam job submit [TARGET] --command COMMAND`，一次完成登记与启动；已绑定执行者可省略 TARGET，Manager 可用协作路径定位任务。详见 [mam job](docs/commands/job.md#待开发)。

## 自动唤醒

当前可执行的工作处理完后，正常结束 turn。已登记的长进程可以继续运行，MAM 会在需要处理后续工作时唤醒负责人，无需调用等待命令或定时查询状态。

- 有未归档的 stopped job：由执行者按任务要求处理并归档。
- 只有 running job：MAM 继续监控，执行者可以结束 turn。
- 没有 job 或所有 job 都已归档，且执行者已结束 turn：由 Manager 检查成果，决定归档、委派 review 或追加要求。源任务已交给未归档的 review 任务时，等待 reviewer 的结果。

负责人正在工作时，MAM 保留待办，避免打断当前 turn。服务的启动、停止和故障处理见[安装说明](docs/install.md)，查看当前服务状态使用：

```text
mam service status
```

原生 subagent 无法直接唤醒时，MAM 通知 Manager 转发。Manager 核对 job 尚未处理后，通过原生 follow-up 将 TASK-ID、JOB-ID 和用途发给当前执行者，要求检查结果、按最新 task.md 继续工作并在收尾后归档 job。进程停止不代表任务成功，也不是要求 Manager 立即归档任务。状态说明及拟议消息格式见 [mam service](docs/commands/service.md)。

新 Manager 接管本实例时，在旧 Manager 已结束 turn 和 wait 后调用 `mam service rebind-manager --note NOTE`。任务和工作目录保留，后续 Manager 通知发给接管者；Codex 原生父子关系不变，旧树执行者仍需通过 TASK-ID 定位，或交给新 subagent 接手。

另计划提供执行者主动发消息的接口：默认发送给当前实例的 Manager，自动识别发送者，TASK-ID 可选，并能唤醒 idle Manager；接口待实现。

## 可选等待

需要在当前 turn 等待执行者或 job 时，运行 `mam wait`。MAM 自动识别调用者和待处理事项，最多等待一小时；有待办时直接返回。默认仍按[自动唤醒](#自动唤醒)结束 turn，由 MAM 后续唤醒。

```text
mam wait
mam wait list
mam wait stop manager
mam wait stop --agent AGENT-ID|PATH
```

等待返回时会说明原因及相关 job 或任务。用户的 steer 或 Manager 发来的消息可以解除对应等待，也可通过 `wait stop` 手动解除；这些操作不停止 job。收到返回结果后，按其中的待办继续工作。

## MAM 开发指南

MAM 自身的开发 worktree、环境、验证和合并步骤见[MAM 开发指南](docs/development.md)。

## MAM 接口说明

各命令的参数、返回内容和使用约束见 [mam task](docs/commands/task.md)、[mam job](docs/commands/job.md)、[mam wait](docs/commands/wait.md)、[mam service](docs/commands/service.md)、[mam workspace](docs/commands/workspace.md)。各页的“待开发”部分为拟议接口，后续任务见 [roadmap](docs/roadmap.md)。
