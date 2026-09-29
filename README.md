# Multi-Agent Manager（MAM）

## 核心原则

MAM 是 multi-agent 项目管理工具。使用细节可查阅 `mam --help` 或[设计文档](docs/designs/)，语法中的大写词需要替换为实际值，`[]` 表示可选，`|` 表示任选其一，`$` 表示环境变量。本文说明 MAM 通用流程；项目具体要求写在[项目说明](.local/README.md)或各 REPO 的 README.md、AGENTS.md。

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

Manager 先创建任务、填写并发布要求，再通过 Codex 原生工具创建 subagent，提供 TASK-ID 并要求其阅读 AGENTS.md 和已发布任务。完成后由 Manager 验收、安排 review、设置 block 或归档。

```text
mam task create --title TITLE [--review TASK-ID|AGENT-PATH]
mam task publish TASK-ID|AGENT-PATH
mam task archive TASK-ID|AGENT-PATH --note NOTE [--force]
mam task block TASK-ID|AGENT-PATH --note NOTE
```

- `create` 返回 TASK-ID；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求。
- 途中追加要求时，先更新并发布 task.md，再通知执行者读取。
- Review 任务用 `--review TASK-ID|AGENT-PATH` 指定源任务，结合 task.md、report.md 和交付代码独立验收。
- 返工或收尾需补充工作时，通知原执行者继续；需要换人时，让新执行者 `mam task start TASK-ID` 接手。
- 交付后由 Manager [验收](#验收)，通过后进入[任务收尾](#任务收尾)。
- 需要暂缓处理时，例如等待用户裁决，由 Manager 设置 `blocked`。

查看已有任务、进程及一个任务的详情：

```text
mam task list
mam job list
mam task status [TASK-ID|AGENT-PATH]
mam task show [TASK-ID|AGENT-PATH]
```

## 执行与交付

任务按执行、报告、验收、收尾推进；各阶段的交付、验证与合入要求由项目约定。

### 开始任务

Subagent 首次接手时登记身份，再读取已发布要求，然后根据需要创建 worktree：

```text
mam task start TASK-ID                       # 登记身份
mam task show [TASK-ID|AGENT-PATH]           # 显示任务
mam workspace add --repo REPO --base COMMIT  # 创建 worktree
```

- Subagent 查看自己任务时可不提供 `TASK-ID|AGENT-PATH`，MAM 从 `$CODEX_THREAD_ID` 自动确认身份。

### 向 Manager 发消息

需要 Manager 反馈时，不要使用 Codex 原生协作工具。

```text
mam message send --message TEXT [--immediate]
```

默认在 Manager 空闲时唤醒并投递；加 `--immediate` 可投递到正在执行的 turn。

### 更新进展

Subagent 执行任务过程中应及时更新任务进度，如 job 开始或归档。直接修改 `workspace/TASK-ID/.task/report.md` 草稿，记录当前进展，无需提交报告。Manager 可读取草稿了解进度；`mam task show --file report` 只返回已发布。

### 报告结果

Subagent 在发布报告前完成交付准备：

1. 完成任务和相关文档更新，按[文件留存原则](#文件留存原则)和项目要求整理文件，并整理干净 worktree。
2. 将 `workspace/TASK-ID/.task/report.md` 的进度草稿整理为结果报告，说明完成项、交付 commit、实际验证的版本与结果、成果位置及未解决问题。

发布报告和附件：

```text
mam task report
```

### 验收

Manager 对照最新 task.md 检查报告和交付版本，可派遣 reviewer 独立验收，明确通过、返工、暂缓或舍弃的结论。返工由 subagent 处理并重新报告；通过或决定舍弃后进入收尾。

### 任务收尾

收尾由 Manager 组织，subagent 按需处理冲突、补充验证和整理成果，使代码交付可由 Manager 直接合入。

1. Manager 按项目要求，将成果合入目标分支，通过 ref/tag 保留或明确舍弃。
2. 确认最终报告及必要附件已发布，调用 `mam task archive TASK-ID|AGENT-PATH --note NOTE` 归档任务及关联 review；归档说明记录结论和成果去向。
3. 核对任务归档及 worktree、分支、workspace 的清理结果，并整理 Manager 本次工作的临时文件。

归档会删除整个 workspace，包括 ignored 内容；`.tasks/TASK-ID/report.md`和软链接目标保留。成果已另行留存或明确舍弃时，可用 `--force`；条件与清理范围见 [mam task](docs/designs/task.md#附件与归档)。

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

进程退出后，所属执行者检查结果、按项目要求更新文档或实验记录，再归档 job。

`mam job archive` 结束 MAM 跟踪并保留记录，不停止进程；也可用于明确不再跟踪的运行中进程。接口与状态定义见 [mam job](docs/designs/job.md)。

## 自动唤醒

当前可执行的工作处理完后，正常结束 turn。已登记的长进程可以继续运行，MAM 会在需要时唤醒负责人，无需调用等待命令或轮询。具体设计见[自动唤醒设计](docs/designs/wakeup.md)。

## MAM 开发指南

MAM 自身的开发 worktree、环境、验证和合并步骤见[MAM 开发指南](docs/development.md)。

## MAM 设计说明

接口与行为设计见 [mam task](docs/designs/task.md)、[mam job](docs/designs/job.md)、[mam message](docs/designs/message.md)、[mam service](docs/designs/service.md)、[mam workspace](docs/designs/workspace.md) 和[自动唤醒](docs/designs/wakeup.md)。各页的“待开发”部分为拟议设计，后续任务见 [roadmap](docs/roadmap.md)。
