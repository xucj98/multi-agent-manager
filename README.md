# Multi-Agent Manager（MAM）

## 核心原则

MAM 用于协助管理本集群的 agents，提供 `mam task`、`mam workspace`、`mam job` 和可选的 `mam wait`，并自动唤醒需要处理后续工作的负责人。本集群的信息查看[本地说明](.local/README.md)，所有 `mam` 命令以及 agent 均在本机运行。

使用细节可用 `mam --help` 查询，语法中的大写词需要替换为实际值，方括号表示可选参数。

MAM 创建任务时生成 `TASK-ID`，同时用作任务标识、命名 workspace 和 git branch；`JOB-ID` 标识登记的进程；当前接口中的 `AGENT-ID` 是 Codex 线程 ID。

MAM 使用共享根目录 `MAM_ROOT`：Manager 编辑其中的 `task.md`，执行者编辑自己的 `report.md`。任务和报告通过 `mam task publish` 发布，并使用 `mam task show` 查看，未发布的修改是草稿。

MAM 的未归档任务 TASK-ID 和当前执行者 AGENT-ID 一一绑定。每个任务有独立的 workspace `PROJECT_ROOT/workspace/TASK-ID`，下面可以建立独立的 worktree，并使用独立的 git branch `task/TASK-ID`。交接给新执行者时，沿用原目录、分支、环境和 job。**原则上每个 subagent 都只能读写自己的 workspace**。`mam` 需在 `PROJECT_ROOT` 或其各级子目录中使用。

```text
PROJECT_ROOT/
  .mam/env.json               # 项目配置
  MAM_ROOT/                   # MAM 根目录
    .tasks/TASK-ID/task.md    # Manager 编辑任务要求
    .tasks/TASK-ID/report.md  # 执行者编辑结果简报
    .tasks/TASK-ID/files      # 其他有必要保留的一次性文件
  REPO/                       # 一个项目下可以有多个 git 仓库
  workspace/TASK-ID/          # 执行者的独立工作空间
    .task                     # 待实现：软链接指向 MAM_ROOT/.tasks/TASK-ID
    REPO/                     # 按需创建的 worktree，分支为 task/TASK-ID
    tmp/                      # 存放临时文件，归档前清理
```

Manager 主要负责任务的推进，进行排期，派遣 subagent 工作，验收，裁决。细节工作交给 subagent 进行，manager 主要通过 report 或者协作工具了解进展。subagent 工作可能出错，manager 可以根据需要派发 reviewer，并对最终结果进行裁定。涉及项目的核心工作，如后续计划安排，roadmap 调整，编写 README.md, AGENTS.md 这类工作由 manager 自己完成。Manager可以直接修改 PROJECT_ROOT/REPO，无需创建 task，worktree。

### 文件留存原则

为了保证项目的长期可维护性，需要严格控制留存的内容。项目文件根据用途分成4类：
1. 后续会**重复使用**的代码、配置、分析工具。进入各个 `REPO`，随 git 提交。
2. 一次性，但有必要保留以解释本次结论的分析代码。进入 `.tasks/TASK-ID/`，随 git 提交。
3. 正式数据、checkpoint、评测原始结果。放在 `REPO` 约定的稳定产物目录，不进入 git。
4. 一次性检查脚本、调试输出、中间版本和验收校验记录。无论由 Manager 还是执行者生成，都放在关联任务的 `workspace/<task-id>/tmp/`，归档前清理；自动清理列入[后续规划](docs/roadmap.md)。

Manager 无关联任务的临时文件统一放在 `PROJECT_ROOT/workspace/tmp/`，按工作分目录。阶段收尾时检查并清理已不需要的文件，需要长期保留的按上述分类转存。

## 安装

安装与更新见[安装说明](docs/install.md)。

## 任务管理

Manager 创建任务、填写任务要求并发布，再绑定执行 agent，agent 任务完成后根据情况启动 review 或归档。以下为当前接口；拟议的自登记流程见[执行与交付](#执行与交付)。

```text
mam task create --title TITLE [--review TARGET-TASK-ID]
mam task publish TASK-ID --file task
mam task bind TASK-ID --agent AGENT-ID
mam task rebind TASK-ID --agent AGENT-ID --note NOTE
mam task archive TASK-ID --note NOTE
```

- `create` 返回 `TASK-ID`；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求；然后发布任务。
- `archive` 要求该任务的所有 job 已归档；归档时移除已登记的 worktree、任务分支和 `workspace/TASK-ID`，但保留 `.tasks/TASK-ID` 的任务、简报和历史登记。
- 使用 Codex 原生工具创建 subagent，提供 TASK-ID，要求其阅读 `AGENTS.md` 和已发布任务。首次绑定可由执行者调用 `mam task bind TASK-ID --agent "$CODEX_THREAD_ID"`，无需向 Manager 上报线程 ID。
- 需要交接已有任务时，Manager 先让旧执行者和新执行者结束当前 turn；新执行者可先只读查看已发布内容，再用 `rebind` 接续原 `TASK-ID`、workspace、worktree 和 job。不要为交接后的 agent 再次运行 `workspace add`。
- 途中追加要求时，先更新 `task.md` 并发布，再通知执行者读取最新已发布要求。执行者和 reviewer 始终以此为准，report 无需绑定要求版本。
- Review 任务使用 `--review` 接收源任务的 `TASK-ID`。

查看已有任务和进程：

```bash
mam task list
mam job list
```

针对一个任务读取登记信息和已发布要求：

```text
mam task status [TASK-ID]
mam task show [TASK-ID]
```

`mam task status` 显示已保存的 job 观测，不会实时探测 job。

## 执行与交付

拟议流程（待实现）：用执行者调用的 `mam task start [TASK-ID]` 替代 bind/rebind。Manager 仍用原生工具创建 subagent；首次登记或新执行者接手时指定 TASK-ID，绑定后可省略：

```text
mam task start TASK-ID
mam task show [TASK-ID]
mam workspace add --repo REPO --base COMMIT
mam task publish --file report
```

MAM 从 CODEX_THREAD_ID 自动识别线程及协作路径。Manager 可用 `mam task show /root/worker` 等接口定位当前执行者的任务；路径按所属协作树区分，任务 ID、workspace 和分支不变。已绑定执行者返工时调用 `mam task start`，任务进入 working；发布 report 后进入 pending。start 不创建 agent，普通问答无需调用。

换人由 Manager 安排，确认旧执行者已停止接续后，新执行者 start 原任务。执行者通过 workspace 根目录的 `.task/report.md` 和 `.task/files/` 编辑报告与附件，再由 MAM 发布；读取要求仍用 show，避免读到未发布草稿。归档删除 `.task` 链接，保留中央任务目录。接口约定见 [mam task](docs/commands/task.md#待开发)。以下为当前已实现的执行流程。

启动 prompt 会提供 `TASK-ID`。先运行 `mam task show TASK-ID`，再为每个需要修改或独立 review 的仓库创建 worktree：

```text
mam workspace add TASK-ID --repo REPO --base COMMIT
```

完成任务后，根据 [文件留存原则](#文件留存原则) 整理文件。然后在 `MAM_ROOT` 的 `.tasks/TASK-ID/report.md` 写结果简报，记录完成项、交付 commit、验证结果和成果位置。然后发布简报：

```text
mam task publish TASK-ID --file report
```

任务需要长期保留的一次性附件由执行者单独提交到 `MAM_BRANCH`；`mam task publish --file report` 只发布结果简报。Manager 归档前确认本任务需要保留的附件已提交，workspace 中的临时文件已经清理。

Manager 验收后，根据情况返工或合入主分支。归档前确认交付代码已合入主分支或明确可以舍弃，必要报告和附件已留存，再调用 `mam task archive` 清理 worktree、git branch 和 workspace。

## 进程管理

预计运行超过 30 分钟的程序（如正式数据生成、训练、评估、传输拷贝）需要登记；短 smoke 不需要。登记、查询和收尾使用：

```text
mam job add TASK-ID --note NOTE --host HOST --pid PID
mam job list [--task TASK-ID]
mam job status JOB-ID
mam job archive JOB-ID --note NOTE
```

- HOST 可以使用 ssh 别名或 username@hostname。
- list 不提供 TASK-ID 时显示所有任务中未归档的 job。

job 状态包括 `running`、`stopped`、`archived`。进程停止后，由执行者检查结果、完成收尾，再归档 job。`mam job archive` 可归档任意已登记 job，只结束 MAM 对它的跟踪并保留记录，不停止进程。`mam task archive` 要求其所有 job 已归档。

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

另计划提供执行者主动发消息的接口：默认发送给当前实例的 Manager，自动识别发送者，TASK-ID 可选，并能唤醒 idle Manager；接口待实现。

## 可选等待

需要在当前 turn 等待执行者或 job 时，运行 `mam wait`。MAM 自动识别调用者和待处理事项，最多等待一小时；有待办时直接返回。默认仍按[自动唤醒](#自动唤醒)结束 turn，由 MAM 后续唤醒。

```text
mam wait
mam wait list
mam wait stop manager
mam wait stop --agent AGENT-ID
```

等待返回时会说明原因及相关 job 或任务。用户的 steer 或 Manager 发来的消息可以解除对应等待，也可通过 `wait stop` 手动解除；这些操作不停止 job。收到返回结果后，按其中的待办继续工作。

## MAM 开发指南

MAM 自身的开发 worktree、环境、验证和合并步骤见[MAM 开发指南](docs/development.md)。

## MAM 接口说明

各命令的参数、返回内容和使用约束见 [mam task](docs/commands/task.md)、[mam job](docs/commands/job.md)、[mam wait](docs/commands/wait.md)、[mam service](docs/commands/service.md)、[mam workspace](docs/commands/workspace.md)。各页的“待开发”部分为拟议接口，后续任务见 [roadmap](docs/roadmap.md)。
