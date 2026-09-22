# Multi-Agent Manager（MAM）

## 核心原则

MAM 用于协助管理本集群的 agents，提供 `mam task`、`mam workspace`、`mam job` 和可选的 `mam wait`，并自动唤醒需要处理后续工作的负责人。本集群的信息查看[本地说明](.local/README.md)，所有 `mam` 命令以及 agent 均在本机运行。

使用细节可用 `mam --help` 查询，语法中的大写词需要替换为实际值，方括号表示可选参数。

MAM 创建任务时生成 `TASK-ID`，同时用作任务标识、命名 workspace 和 git branch；`JOB-ID` 标识登记的进程；`AGENT-ID` 由 codex 生成，标识执行 agent。

MAM 使用共享根目录 `MAM_ROOT`：Manager 编辑其中的 `task.md`，执行者编辑自己的 `report.md`。任务和报告通过 `mam task publish` 发布，并使用 `mam task show` 查看，未发布的修改是草稿。

MAM 的未归档任务 TASK-ID 和当前执行者 AGENT-ID 一一绑定。每个执行者有自己独立的 workspace `PROJECT_ROOT/workspace/TASK-ID`，下面可以建立独立的 worktree，并使用独立的 git branch `task/TASK-ID`。`mam` 需在 `PROJECT_ROOT` 或其各级子目录中使用。

```text
PROJECT_ROOT/
  .mam/env.json               # 项目配置
  MAM_ROOT/                   # MAM 根目录
    .tasks/TASK-ID/task.md    # Manager 编辑任务要求
    .tasks/TASK-ID/report.md  # 执行者编辑结果简报
    .tasks/TASK-ID/files      # 其他有必要保留的一次性文件
  REPO/                       # 一个项目下可以有多个 git 仓库
  workspace/TASK-ID/          # 执行者的独立工作空间
    REPO/                     # 按需创建的 worktree，分支为 task/TASK-ID
    tmp/                      # 存放临时文件，任务归档时被清理
```

### 文件留存原则

为了保证项目的长期可维护性，需要严格控制留存的内容。项目文件根据用途分成4类：
1. 后续会**重复使用**的代码、配置、分析工具。进入各个 `REPO`，随 git 提交。
2. 一次性，但有必要保留以解释本次结论的分析代码。进入 `.tasks/TASK-ID/`，随 git 提交。
3. 正式数据、checkpoint、评测原始结果。放在 `REPO` 约定的稳定产物目录，不进入 git。
4. 一次性检查脚本、调试输出、中间版本。放在 `workspace/<task-id>/tmp/`。无需手动清理，`mam task archive` 时自动清理。

## 安装

安装与更新见[安装说明](docs/install.md)。

## 任务管理

Manager 创建任务、填写任务要求并发布，再绑定执行 agent，agent 任务完成后根据情况启动 review 或归档。

```text
mam task create --title TITLE [--review TARGET-TASK-ID]
mam task publish TASK-ID --file task
mam task bind TASK-ID --agent AGENT-ID
mam task rebind TASK-ID --agent AGENT-ID --note NOTE
mam task archive TASK-ID --note NOTE
```

- `create` 返回 `TASK-ID`；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求；然后发布任务。
- `archive` 要求该任务的所有 job 已归档；归档时移除已登记的 worktree、任务分支和 `workspace/TASK-ID`，但保留 `.tasks/TASK-ID` 的任务、简报和历史登记。
- 使用 codex 工具创建 subagent，要求其查看 `AGENTS.md` 并使用 `mam task show TASK-ID` 查看任务；获取 `AGENT-ID`，绑定执行 agent。
- 需要交接已有任务时，Manager 先让旧执行者和新执行者结束当前 turn；新执行者可先只读查看已发布内容，再用 `rebind` 接续原 `TASK-ID`、workspace、worktree 和 job。不要为交接后的 agent 再次运行 `workspace add`。
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

完成任务后，根据 [文件留存原则](#文件留存原则) 整理文件。然后在 `MAM_ROOT` 的 `.tasks/TASK-ID/report.md` 写结果简报，记录完成项、交付 commit、验证结果和成果位置。然后发布简报：

```text
mam task publish TASK-ID --file report
```

任务需要长期保留的一次性附件由执行者单独提交到 `MAM_BRANCH`；`mam task publish --file report` 只发布结果简报。Manager 归档前确认本任务需要保留的附件已提交，workspace 中的临时文件已经清理。

Manager 验收后，根据情况返工或合入主分支。全部工作完成后，由 Manager 调用 `mam task archive` 清理 worktree、git branch 和 workspace。

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

## 自动唤醒

当前可执行的工作处理完后，正常结束 turn。已登记的长进程可以继续运行，MAM 会在需要处理后续工作时唤醒负责人，无需调用等待命令或定时查询状态。

- 有未归档的 stopped job：由执行者按任务要求处理并归档。
- 只有 running job：MAM 继续监控，执行者可以结束 turn。
- 没有 job 或所有 job 都已归档，且执行者已结束 turn：由 Manager 检查成果，决定归档、委派 review 或追加要求。源任务已交给未归档的 review 任务时，等待 reviewer 的结果。

负责人正在工作时，MAM 保留待办，避免打断当前 turn。服务的启动、停止和故障处理见[安装说明](docs/install.md)，查看当前服务状态使用：

```text
mam service status
```

若状态显示 daemon 仍 `running`、`healthy`，但 `pending.events` 有 `delivery: blocked` 和
`failure_kind: unsupported_multi_agent_v2_direct_input`，说明原生 multi-agent v2 子 agent 拒绝
direct `turn/start`，不是 job 探测或 daemon 已停止。MAM 会停止重试该子 agent；只有存在有效且不同于
executor 的 Manager 时，才会在其空闲时投递包含 TASK-ID、JOB-ID、executor 和错误的升级消息。若
`manager == executor`，source 仍会 blocked，但不会创建自我升级。executor 显示 `active` 不表示 stopped
job 已收尾；job 未归档前，这一次升级仍可保留。Manager 收到消息后先核对执行者状态和 report，再决定是否
用 parent-native `collaboration.followup_task` 协调收尾和归档，避免重复 follow-up。普通 RPC/传输失败仍按
原有退避或不确定性语义处理。

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

## MAM 设计细节

详细接口、状态语义和归档保护见[MAM 设计细节](docs/task-management-design.zh-CN.md)，日常使用无需翻阅；参数以 `mam --help` 及相应子命令的帮助为准。
