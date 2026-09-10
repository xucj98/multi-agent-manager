# 任务管理 CLI 接口说明

MAM 通过文件和 CLI 管理当前集群的任务，顶层命令为 `mam task`、`mam job`、`mam wait`、`mam workspace`。所有 agent 和管理命令在本机运行；GPU 作业可通过 SSH 在 wuwen-1 运行，两端共享 `/mnt/public`。除 `--help` 外，命令从当前目录逐级向上寻找最近的 `.mam/env.json`；没有配置或最近配置无效都会报错，且不会回退到更上层的配置。

配置是唯一的项目选择来源，不提供 `--root` 或环境变量默认值。文件必须包含绝对路径的 `MAM_ROOT`、`PROJECT_ROOT` 和现有本地分支名 `MAM_BRANCH`：

```json
{
  "MAM_ROOT": "/mnt/public/xcj/Projects/multi-agent-manager",
  "PROJECT_ROOT": "/mnt/public/xcj/Projects",
  "MAM_BRANCH": "project/state-vla"
}
```

`MAM_ROOT` 是保存任务、job、wait、锁和归档登记的 Git worktree 根，可为普通 checkout 或 linked worktree；工具不会将 linked worktree 归并到 primary checkout。`PROJECT_ROOT` 包含业务仓库和 workspace。路径在读取配置时解析为实际目录，避免同一目录的别名形成不同边界。

日常命令和交付步骤见 [README 的任务管理](../README.md#任务管理)、[执行与交付](../README.md#执行与交付)、[进程管理](../README.md#进程管理)与[休眠管理](../README.md#休眠管理)。本文保留接口设计、状态语义和归档保护；安装见[安装说明](install.md)。

使用者分为 Manager 和执行者。Manager 为 subagent 登记任务，自己的工作无需创建任务。代码实现、review、实验等是不同的任务内容，负责完成任务的 agent 统一称为执行者。

## 文件与发布

任务、workspace 和工作分支使用同一个 `TASK-ID`，由工具生成：

```text
MAM_ROOT/
  .tasks/TASK-ID/task.md       # Manager 编辑任务要求
  .tasks/TASK-ID/report.md     # 执行者编辑结果简报
  .local/tasks/TASK-ID.json    # 工具维护的登记与状态，不进入 Git
  .local/waits/*.json          # 当前等待登记，不进入 Git

PROJECT_ROOT/workspace/TASK-ID/
  REPO/                        # 按需创建的 worktree，分支为 task/TASK-ID
```

`MAM_BRANCH` 上的 task.md、report.md 是已发布内容，工作目录中的修改是草稿。读取已发布内容无需切换 checkout；发布前 `MAM_ROOT` 必须已 checkout 到 `MAM_BRANCH`，CLI 不自动切换分支。这样代码可从 `main` 安装或开发，而生产管理 worktree 使用独立的项目分支保存项目记录。

## 创建与执行

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task create --title TITLE` | Manager | 生成 `TASK-ID`，登记任务，创建 task.md、report.md 草稿和空 workspace；返回 `TASK-ID` 与文件、目录路径，状态为“进行中” |
| `mam task create --title TITLE --review TASK-ID` | Manager | 创建任务，并在任务草稿中引用源 `TASK-ID` 当前已发布的要求、简报及已登记的交付代码 commit，供执行者 review |
| `mam task bind TASK-ID --agent AGENT-ID` | Manager | 将已启动的 subagent 绑定到任务；一个未归档任务对应一个执行 agent，一个 agent 同时绑定一个任务 |
| `mam workspace add TASK-ID --repo REPO --base COMMIT` | 执行者 | 从 `PROJECT_ROOT/REPO` 调用该库的 `.local/create_worktree.sh`，从 base commit 新建 `task/TASK-ID` 分支及对应 `PROJECT_ROOT/workspace` worktree，同时创建环境和受控共享软链接；登记并返回路径与分支名 |

`REPO` 不使用固定注册表，而是 `PROJECT_ROOT` 下非空的单层目录名；绝对路径、`.`、`..`、正反斜杠和其他路径逃逸形式都会被拒绝。MAM 仍会确认该目录是 primary Git checkout，并要求其中存在非软链接的 `.local/create_worktree.sh`。涉及哪些库及其 base commit 由任务说明确定，每个库分别调用 workspace add。具体安装和软链接规则由各库脚本负责。同一任务在不同库使用同名 `task/TASK-ID` 分支。

MAM 自身的 `scripts/create_worktree.sh` 在源 MAM 根存在 `.local/README.md` 时，才会在新 worktree 建立指向它的单文件 `.local/README.md` 软链接；不会共享整个 `.local`。源文件缺失或目标已有文件时仍可创建 worktree，且不会覆盖目标。归档只将目录内仅有、且精确指向 primary MAM 根该 README 的链接视为已知忽略内容，其他 `.local` 内容仍会阻止删除。

## 编辑、发布与查看

`FILE` 为 `task` 或 `report`。

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task show TASK-ID [--file FILE]` | 所有人 | 直接返回 `MAM_BRANCH` 上当前已发布的文件内容；默认读取 task.md，`--file report` 读取 report.md |
| `mam task publish TASK-ID --file FILE` | 文件负责人 | 加锁，将指定文件的草稿单独提交到 `MAM_BRANCH`，返回发布 commit。发布要求 `MAM_ROOT` 当前 checkout 正是该分支；同步本次文件的暂存内容，保留其他文件的暂存内容及所有草稿；发布 report 时记录各 ready worktree 的当前 HEAD 为交付代码 commit，状态改为“待验收” |
| `mam task list [--archived\|--all]` | 所有人 | 即使为空也输出表头；每行固定为标题、任务状态、`TASK-ID`、agent、agent 状态。保留既有筛选，不提供 `--json` |
| `mam task status TASK-ID` | 所有人 | 返回任务、workspace、各库交付和已保存 job 观测的精简 JSON 展示；不隐式刷新 job，并提示未发布草稿 |

修改要求和简报使用普通编辑工具，再通过 publish 发布。执行者通过 show 获取当前已发布的任务要求；已发布内容的历史由普通 Git 提交保留，CLI 不维护任务要求与简报的版本绑定。

## 长任务进程

job 指执行者登记的一个长时间运行的进程。预计运行超过 1 小时的程序（如正式数据生成、训练、评估）通过 `mam job add` 登记，通常的短 smoke 无需登记。同一执行者可为自己的任务登记多个进程，每条登记记录生成一个 `JOB-ID`，并关联所属任务，以便 Manager 找到对应执行者。

job 状态为“进行中／已停止／已归档”：查询确认进程结束后变为“已停止”，表示尚待执行者处理；执行者完成结果记录、文件清理等任务要求后，通过 job archive 标记“已归档”。

`STATUS` 可为 `running`、`stopped`、`archived` 或 `all`。

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam job add TASK-ID --note NOTE --host HOST --pid PID` | 执行者 | 将指定进程登记到自己的任务下，记录用途、主机、PID 和实际启动时间；无法换算时列表显示 unknown，生成并返回 `JOB-ID` |
| `mam job list [--task TASK-ID] [--status STATUS]` | 所有人 | 默认有表头，每行固定为描述、job 状态、开始时间、`JOB-ID`、任务描述、`TASK-ID`；保留筛选，不提供 `--json`。unknown 探测显示 `unknown/待核实`，不冒充 running 或 stopped |
| `mam job list --attention` | Manager | 查询进程和 agent 状态，筛选已停止、未归档且执行者已不在运行的 job；不确定项仍在同一表中显示 `unknown/待核实` |
| `mam job status JOB-ID` | 所有人 | 只刷新该 job，不扫描其他进程；返回该次探测的精简 JSON 展示及所属任务和 agent |
| `mam job archive JOB-ID --note NOTE` | 执行者 | 记录简短的处理结论或成果位置，将该 job 标记为“已归档”，保留历史记录 |

进程查询在其所属主机执行，远端通过 SSH 查询，核对 PID 和启动时间；查询失败时保留上次状态与时间，并标注“本次查询失败”，不据此判定进程停止。agent 状态由 CLI 连接承载这些线程的现有 Codex App Server，通过 `thread/read` 查询；`active` 对应执行者仍在运行，查询失败显示“待核实”。本机现有 Unix socket 的只读查询已验证可用，接口见 [App Server 文档](https://learn.chatgpt.com/docs/app-server)。

“需要 Manager 处理”是 job 与 agent 状态的组合筛选，不增加 job 状态。已停止但执行者仍为 running 的 job 由执行者继续处理；进程仍在运行或 job 已归档时，不进入该筛选。已归档 job 保持已归档状态。

job archive 只记录收尾结果，不删除 workspace；任务归档也保留各 job 的独立状态与历史。

## 状态展示

`task status` 是对登记的轻量展示，不改变存储记录，也不探测进程。它保留任务的 `id`、标题、状态、agent 和 workspace；每个仓库保留路径、分支、状态、必要的 base 与交付 commit。`publications` 中可显示 task.md 和 report.md 各自最后一次发布的 Git commit。

未归档 job 位于 `jobs.unarchived`，每项只含 `id`、`note`、`status` 和 `checked_at`；`jobs.cached` 明确这些是已保存的观测，已归档 job 只给出 `archived_count`。有未发布改动时才显示 `drafts`。任务归档或出错时保留归档结论或失败原因；review 任务保留源任务和成果代码 commit 引用。旧登记中不再使用的字段在读取时忽略，无需迁移。空值及正常的 false 清理标记可省略。

`job status` 只刷新所请求的 `JOB-ID` 一次。正常结果保留该 job 的 `id`、`note`、所属任务与标题、agent、主机、PID、启动时间、状态和检查时间，不重复输出 `identity` 或 `probe`。探测为 unknown 时，`status` 为 `unknown`，并返回 `error` 及必要的最后已知状态和时间；进程身份不匹配等诊断以错误文本给出。已归档 job 保持 `archived`，并保留归档结论。

## 可停止等待

等待只读取已登记的 job，不启动 daemon、数据库或调度器。临时登记保存在本机共享 `.local/waits/`；每个 agent 一条活跃等待，记录本地 PID、启动身份和 token。start、stop、退出清理使用同一 agent 锁和 token，因此陈旧等待不能取消后来者；异常退出后 PID 身份已停止的登记会被清理，不会显示为仍在等待或阻止重开。

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam wait jobs [--task TASK-ID] [--timeout TIMEOUT] [--agent AGENT-ID]` | 所有人 | 默认监控当前所有未归档 job，`--task` 缩小范围。已有确定 stopped job 立即返回 `stopped`；任一运行 job 停止时返回 `stopped`；空集返回 `empty`，超时返回 `timeout`。unknown 探测不视作 stopped。轮询只探测必要 job，不探测 agent，也不持有任务锁睡眠 |
| `mam wait list` | 所有人 | 即使为空也输出表头；每行是 `AGENT-ID`、绑定任务标题、`TASK-ID`、等待内容、等待开始时间。绑定取等待者自己的未归档任务；没有绑定显示“未绑定”，不使用被监控 job 的负责人代替 |
| `mam wait stop --agent AGENT-ID` | 所有人 | 仅为该 agent 写取消标记并唤醒等待，返回 `cancelled`；不存在当前等待返回 `not_waiting`。不向 job 进程发信号，不归档 job |
| `mam wait stop manager` | Manager | 从当前有效等待及未归档任务绑定中找出唯一未绑定任务的等待者并写取消标记。零个、多个或身份无法确认都会报错；等待中的 `--task` 只是监控范围，不是绑定。选中后若原等待已结束或被替换，返回 `not_waiting`，不会取消替换后的等待 |

`mam wait stop` 必须且只能使用 `manager` 或 `--agent AGENT-ID` 之一。等待者未指定 `--agent` 时，只读取 `CODEX_THREAD_ID`；不从继承的 `CODEX_SESSION_ID` 推测身份。`AGENT-ID` 缺失、空白或含换行会明确报错。每次 target 探测前检查 deadline，单次远端探测预算不超过 0.5 秒与剩余时限的较小值；允许小幅运行时调度开销。stop 不会被长 SSH 查询无限拖住。

`job list --attention` 中，即使 job 已确认 stopped，只要 agent 状态未知或查询失败，也明确显示 `unknown/待核实`，与普通待处理项区分。

## 归档

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task archive TASK-ID --note NOTE` | Manager | 记录结束结论，移除已登记的各库 worktree 及独立环境，删除对应的本地任务分支，移除 workspace；保留任务说明、简报和历史登记，状态改为“已归档” |

分支删除使用创建时登记的“仓库＋分支名”。移除软链接时保留其指向的共享数据。归档返回各项清理结果；未全部完成则保留未归档状态，再次调用继续清理。是否归档由 Manager 根据任务要求决定。
