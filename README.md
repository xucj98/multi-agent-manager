# Multi-Agent Manager（MAM）

## 核心原则

MAM 是 multi-agent 项目管理工具。使用细节可查阅 `mam --help` 或[接口文档](docs/commands/)，语法中的大写词需要替换为实际值，`[]` 表示可选，`|` 表示任选其一。本文说明 MAM 通用流程；项目的文档、实验记录、产物留存和代码合并要求写在[项目说明](.local/README.md)或各 REPO 的 README.md、AGENTS.md。

项目的目录结构如下：

```text
PROJECT_ROOT/
  .mam/env.json               # MAM 配置，每个 MAM 实例唯一
  MAM_ROOT/                   # MAM 根目录
    .local/                   # 该项目的具体信息说明及 MAM service 持久化目录
    .tasks/TASK-ID/task.md    # Manager 编辑任务要求
    .tasks/TASK-ID/report.md  # 执行者编辑结果简报
    .tasks/TASK-ID/files      # 其他有必要保留的一次性文件
  REPO/                       # 一个项目下可以有多个 git 仓库
  workspace/TASK-ID/          # 执行者的独立工作空间
    .task                     # 软链接指向 MAM_ROOT/.tasks/TASK-ID
    REPO/                     # 按需创建的 worktree，分支为 task/TASK-ID
    tmp/                      # 本任务临时文件，归档时自动清理
```

MAM 创建任务时生成 `TASK-ID`，同时用作任务标识、命名 workspace 和 git branch；`JOB-ID` 标识登记的进程；`AGENT-ID` 是 Codex 线程 ID。`AGENT-PATH` 是 Codex 原生协作树内的执行者路径，如 `/root/worker`。

MAM 使用共享根目录 `MAM_ROOT`：Manager 编辑其中的 `task.md`，执行者编辑自己的 `report.md`。任务要求通过 `mam task publish` 发布，报告通过 `mam task report` 提交，使用 `mam task show` 查看；未发布的修改是草稿。

每个未归档任务和 subagent 一一绑定。每个任务有独立的 workspace `PROJECT_ROOT/workspace/TASK-ID`，下面可以建立独立的 worktree，并使用独立的 git branch `task/TASK-ID`。**原则上每个 subagent 都只能读写自己的 workspace**。

MAM 使用 `.mam/env.json` 区分不同的项目实例，因此 `mam` 命令需在 `PROJECT_ROOT` 或其各级子目录中使用。

Manager 主要负责任务的推进，进行排期，派遣 subagent 工作，验收，裁决。细节工作交给 subagent 进行，manager 主要通过 report 或者协作工具了解进展。subagent 工作可能出错，manager 可以根据需要派发 reviewer，并对最终结果进行裁定。涉及项目的核心工作，如后续计划安排，roadmap 调整，编写 README.md, AGENTS.md 这类工作由 manager 自己完成。Manager可以直接修改 PROJECT_ROOT/REPO，无需创建 task，worktree。

### 文件留存原则

为了保证项目的长期可维护性，需要严格控制留存的内容。项目文件根据用途分成4类：

1. 后续会**重复使用**的代码、配置、分析工具。进入各个 `REPO`，随 git 提交。
2. 一次性，但有必要保留以解释本次结论的分析代码或附件。进入 `.tasks/TASK-ID/files/`，随 `mam task report` 一起提交。
3. 正式数据、checkpoint、评测原始结果。放在 `REPO` 约定的稳定产物目录，不进入 git。
4. 一次性检查脚本、调试输出、中间版本和验收校验记录。无论由 Manager 还是执行者生成，都放在关联任务的 `workspace/<task-id>/tmp/`，归档时自动清理。

Manager 无关联任务的临时文件统一放在 `PROJECT_ROOT/workspace/tmp/`，按工作分目录。阶段收尾时检查并清理已不需要的文件，需要长期保留的按上述分类转存。

## 安装

安装、更新及项目 hooks 配置见[安装说明](docs/install.md)。

## 任务管理

Manager 先创建任务、填写并发布要求，再通过 Codex 原生工具创建 subagent，提供 TASK-ID 并要求其阅读 AGENTS.md 和已发布任务。执行者自行登记；完成后由 Manager 验收、安排 review 或归档。

```text
mam task create --title TITLE [--review TASK-ID|AGENT-PATH]
mam task publish TASK-ID|AGENT-PATH
mam task archive TASK-ID|AGENT-PATH --note NOTE [--force]
```

- `create` 返回 TASK-ID；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求。
- 途中追加要求时，先更新并发布 task.md，再通知执行者读取。执行者和 reviewer 始终以最新已发布要求为准；report 无需绑定要求版本。
- Review 任务用 `--review TASK-ID|AGENT-PATH` 指定源任务，结合最新 task.md、report.md 和交付代码独立验收。
- 返工时通知原执行者调用 `mam task start` 后继续；需要换人时，先确认旧执行者已结束 turn 和 wait，再让新执行者 `mam task start TASK-ID` 接手。原 workspace、分支、环境和 job 保留，无需再次创建。
- 交付后的验收、留存和归档按[任务收尾](#任务收尾)完成。

查看已有任务、进程及一个任务的详情：

```text
mam task list
mam job list
mam task status [TASK-ID|AGENT-PATH]
mam task show [TASK-ID|AGENT-PATH]
```

`mam task status` 显示已保存的 job 观测，不会实时探测。

## 执行与交付

Subagent 首次执行任务时调用 `mam task start` 登记，再读取已发布要求，为每个需要修改或独立 review 的仓库创建 worktree：

```text
mam task start TASK-ID
mam task show [TASK-ID|AGENT-PATH]
mam workspace add --repo REPO --base COMMIT
```

Subagent 查看自己任务时可不提供 `TASK-ID|AGENT-PATH`，MAM 从 `CODEX_THREAD_ID` 自动确认身份。返工时也要调用 `mam task start`，任务进入 working；发布 report 后进入 pending，归档后为 archived。普通问答无需 start。

subagent 执行任务过程中应及时更新任务进度。直接修改 `workspace/TASK-ID/.task/report.md` 草稿，简洁记录当前进展，中间结果无需发布。Manager 可读取草稿了解进度；`mam task show --file report` 只返回已发布。

完成后按[文件留存原则](#文件留存原则)整理成果，并在各 worktree 中用 `git commit` 提交代码。编辑 `workspace/TASK-ID/.task/report.md`，说明完成项、交付 commit、验证结果和成果位置；需要保留的一次性附件放 `.task/files/`。发布前将进度草稿整理为交付简报，再提交报告和附件：

```text
mam task report
```

report 在同一次提交中发布报告及 `.task/files/` 的新增、修改和删除。

### 任务收尾

1. 执行者整理代码和产物，同步相关文档；需保留的文件按[文件留存原则](#文件留存原则)、具体项目和代码库要求处理。报告说明结果、验证方法、未解决问题和产物位置，让接手者不依赖原对话也能理解。
2. 确认全部 job 已归档。job 的逐次收尾见[进程管理](#进程管理)，不能留到 task 归档时一并处理。
3. 执行者按项目要求提交需保留的代码，发布附件和最终 report；Manager 按最新 task.md 验收，需要时独立 review，并对 review 结论作出裁决。返工继续原任务。
4. Manager 按项目规则确认成果去向，再调用 `mam task archive TASK-ID|AGENT-PATH --note NOTE`。归档只检查全部 job 已归档、`.tasks/TASK-ID/` 下 Git 干净、项目归档 hook 通过（没有则跳过）。通过后清理 worktree 登记、任务分支和整个 workspace，含 ignored 内容；须提前保存成果，中央任务记录和软链接目标保留。
5. Manager 核对归档结果，确认任务已归档、工作目录和分支已清理。失败时按提示处理后重试；阶段结束时也检查自己的 workspace/tmp，将必要内容转存后清理其余文件。

执行者默认应先整理干净 worktree。归档使用 `git worktree remove` 和 `git branch -d`；明确舍弃剩余改动或未合并代码时，`--force` 改用 `git worktree remove --force` 和 `git branch -D`，不跳过上述归档条件。详见 [mam task](docs/commands/task.md#附件与归档)。

## 进程管理

预计运行超过 30 分钟的程序（如正式数据生成、训练、评估、传输拷贝）需要登记；短 smoke 不需要。登记、查询和收尾使用：

```text
mam job add [TASK-ID|AGENT-PATH] --note NOTE --host HOST --pid PID
mam job list [--task TASK-ID|AGENT-PATH]
mam job status JOB-ID
mam job archive JOB-ID --note NOTE
```

- HOST 可以使用 ssh 别名或 username@hostname。
- list 省略 `--task` 时显示所有任务中未归档的 job；已绑定执行者登记 job 时可省略任务参数。

job 状态包括 `running`、`exited`、`unknown`、`archived`；exited 表示进程已退出，unknown 表示暂时无法确认。进程退出后，Manager 收到转发通知时，通知对应执行者检查结果、按项目要求更新文档或实验记录，再归档该 job。原生转发方式见[自动唤醒](#自动唤醒)。

一个任务可以多次启动、处理和归档 job；全部 job 已归档、任务成果验收完成后，才进行一次最终 task 归档。`mam job archive` 只结束 MAM 跟踪并保留记录，不停止进程；也可用于明确不再跟踪的运行中进程。

拟议接口为 `mam job submit [TASK-ID|AGENT-PATH] --command COMMAND`，一次完成登记与启动；已绑定执行者可省略任务参数，Manager 可用协作路径定位任务。详见 [mam job](docs/commands/job.md#待开发)。

## 自动唤醒

当前可执行的工作处理完后，正常结束 turn。已登记的长进程可以继续运行，MAM 会在需要处理后续工作时唤醒负责人，无需调用等待命令或定时查询状态。

- 有未归档的 exited job：由执行者按任务要求处理并归档。
- 原任务与关联的未归档 review 中，任一执行者 active 或有 running job：等待执行推进。
- 原任务与关联 review 都空闲：提醒 Manager 检查报告，安排继续执行、review 或归档。Manager 再次空闲时，仍需处理的待办会继续提醒。

自动提醒在负责人空闲时合并投递。服务的启动、停止和故障处理见[安装说明](docs/install.md)，查看当前服务状态使用：

```text
mam service status
```

原生 subagent 无法直接唤醒时，MAM 通知 Manager 转发。Manager 按通知中的执行者路径调用 `followup_task`，要求检查指定 job 的结果、按最新 task.md 继续工作并归档 job。通知通过 TASK-ID 定位时，先查看任务并确认执行者；需要换人则按任务接续流程处理。消息格式见 [mam service](docs/commands/service.md#消息与状态输出)。

新 Manager 接管本实例时，在旧 Manager 已结束 turn 和 wait 后调用 `mam service rebind-manager --note NOTE`。任务和工作目录保留，后续 Manager 通知发给接管者；Codex 原生父子关系不变，旧树执行者仍需通过 TASK-ID 定位，或交给新 subagent 接手。

### 向 Manager 发消息

需要 Manager 反馈时，使用及时消息；可以等当前工作结束后处理的信息加 `--defer`：

```text
mam message send --message TEXT [--task TASK-ID|AGENT-PATH]
mam message send --message TEXT --defer [--task TASK-ID|AGENT-PATH]
```

及时消息进入 Manager 当前 turn，抄送消息等待其空闲；两类消息在 Manager idle 时都会唤醒。MAM 自动识别发送者并关联其任务，未绑定 task 也可发送。详见 [mam message](docs/commands/message.md)。

## 可选等待

需要在当前 turn 等待执行者或 job 时，运行 `mam wait`。MAM 自动识别调用者和待处理事项，最多等待一小时；有待办时直接返回。默认仍按[自动唤醒](#自动唤醒)结束 turn，由 MAM 后续唤醒。

```text
mam wait
mam wait list
mam wait stop manager
mam wait stop --agent AGENT-ID|AGENT-PATH
```

等待返回时会说明原因及相关 job 或任务。用户的 steer 或 Manager 发来的消息可以解除对应等待，也可通过 `wait stop` 手动解除；这些操作不停止 job。收到返回结果后，按其中的待办继续工作。

## MAM 开发指南

MAM 自身的开发 worktree、环境、验证和合并步骤见[MAM 开发指南](docs/development.md)。

## MAM 接口说明

各命令的参数、返回内容和使用约束见 [mam task](docs/commands/task.md)、[mam job](docs/commands/job.md)、[mam message](docs/commands/message.md)、[mam wait](docs/commands/wait.md)、[mam service](docs/commands/service.md)、[mam workspace](docs/commands/workspace.md)。各页的“待开发”部分为拟议接口，后续任务见 [roadmap](docs/roadmap.md)。
