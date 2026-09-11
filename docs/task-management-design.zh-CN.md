# MAM 设计细节

本文档提供 MAM 设计细节，开发 MAM 请参考并同步本文档；日常使用参考[README](../README.md)，安装见[安装说明](install.md)。MAM 顶层命令为 `mam task`、`mam job`、`mam wait`、`mam workspace`。默认项目结构如下：

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

除 `--help` 外，命令从当前目录逐级向上寻找最近的 `.mam/env.json`；没有配置或最近配置无效都会报错，且不会回退到更上层的配置。配置是唯一的项目选择来源，文件必须包含绝对路径的 `MAM_ROOT`、`PROJECT_ROOT` 和现有本地分支名 `MAM_BRANCH`：

```json
{
  "MAM_ROOT": "/mnt/public/xcj/Projects/multi-agent-manager",
  "PROJECT_ROOT": "/mnt/public/xcj/Projects",
  "MAM_BRANCH": "project/state-vla"
}
```

`MAM_ROOT` 是保存任务、结果简报、job、wait、锁和归档登记的根目录。`PROJECT_ROOT` 包含业务仓库和 workspace。`MAM_BRANCH`
用于记录该项目的任务和结果简报，所有 `MAM_ROOT/.tasks` 的内容只保存在该分支，不进入 `main`。

使用者分为 Manager 和执行者。Manager 为 subagent 登记任务，自己的工作无需创建任务。代码实现、review、实验等是不同的任务内容，负责完成任务的 agent 统一称为执行者。

## 文件与发布

任务、workspace 和工作分支使用同一个 `TASK-ID`，由 MAM 在创建任务时生成。`MAM_BRANCH` 上的 task.md、report.md 是已发布内容，工作目录中的修改是草稿。读取已发布内容无需切换 checkout；发布前 `MAM_ROOT` 必须已 checkout 到 `MAM_BRANCH`，CLI 不自动切换分支。这样代码可从 `main` 安装或开发，而生产管理 worktree 使用独立的项目分支保存项目记录。

## 创建与执行

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task create --title TITLE` | Manager | 生成 `TASK-ID`，登记任务，创建 task.md、report.md 草稿和空 workspace；返回 `TASK-ID` 与文件、目录路径，状态为“进行中” |
| `mam task create --title TITLE --review TARGET-TASK-ID` | Manager | 创建任务，并在任务草稿中引用源 `TASK-ID` 当前已发布的要求、简报及已登记的交付代码 commit，供执行者 review |
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

job 状态为“进行中／已停止／已归档”：查询确认进程结束后变为“已停止”，表示尚待执行者处理；job archive 可在 running、stopped 或 unknown/待核实观测下标记“已归档”，只结束 MAM 跟踪，不停止进程。

`STATUS` 可为 `running`、`stopped`、`archived` 或 `all`。

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam job add TASK-ID --note NOTE --host HOST --pid PID` | 执行者 | 将指定进程登记到自己的任务下，记录用途、主机、PID 和实际启动时间；无法换算时列表显示 unknown，生成并返回 `JOB-ID` |
| `mam job list [--task TASK-ID] [--status STATUS]` | 所有人 | 默认有表头，每行固定为描述、job 状态、开始时间、`JOB-ID`、任务描述、`TASK-ID`；保留筛选，不提供 `--json`。unknown 探测显示 `unknown/待核实`，不冒充 running 或 stopped |
| `mam job list --attention` | Manager | 查询进程和 agent 状态，筛选已停止、未归档且执行者已不在运行的 job；不确定项仍在同一表中显示 `unknown/待核实` |
| `mam job status JOB-ID` | 所有人 | 只刷新该 job，不扫描其他进程；返回该次探测的精简 JSON 展示及所属任务和 agent |
| `mam job archive JOB-ID --note NOTE` | 执行者 | 记录简短的处理结论或成果位置，将该 job 标记为“已归档”，保留身份、最后观测和历史记录；不探测或停止进程 |

进程查询在其所属主机执行，远端通过 SSH 查询，核对 PID 和启动时间；查询失败时保留上次状态与时间，并标注“本次查询失败”，不据此判定进程停止。job archive 不触发进程查询。agent 状态由 CLI 连接承载这些线程的现有 Codex App Server，通过 `thread/read` 查询；`active` 对应执行者仍在运行，查询失败显示“待核实”。本机现有 Unix socket 的只读查询已验证可用，接口见 [App Server 文档](https://learn.chatgpt.com/docs/app-server)。

“需要 Manager 处理”是 job 与 agent 状态的组合筛选，不增加 job 状态。已停止但执行者仍为 running 的 job 由执行者继续处理；进程仍在运行或 job 已归档时，不进入该筛选。已归档 job 保持已归档状态，不再周期探测或触发 wait 待办。

job archive 只记录归档结论，不删除 workspace，也不要求进程已停止；任务归档也保留各 job 的独立状态与历史。

## 状态展示

`task status` 是对登记的轻量展示，不改变存储记录，也不探测进程。它保留任务的 `id`、标题、状态、agent 和 workspace；每个仓库保留路径、分支、状态、必要的 base 与交付 commit。`publications` 中可显示 task.md 和 report.md 各自最后一次发布的 Git commit。

未归档 job 位于 `jobs.unarchived`，每项只含 `id`、`note`、`status` 和 `checked_at`；`jobs.cached` 明确这些是已保存的观测，已归档 job 只给出 `archived_count`。有未发布改动时才显示 `drafts`。任务归档或出错时保留归档结论或失败原因；review 任务保留源任务和成果代码 commit 引用。旧登记中不再使用的字段在读取时忽略，无需迁移。空值及正常的 false 清理标记可省略。

`job status` 只刷新所请求的 `JOB-ID` 一次。正常结果保留该 job 的 `id`、`note`、所属任务与标题、agent、主机、PID、启动时间、状态和检查时间，不重复输出 `identity` 或 `probe`。探测为 unknown 时，`status` 为 `unknown`，并返回 `error` 及必要的最后已知状态和时间；进程身份不匹配等诊断以错误文本给出。已归档 job 保持 `archived`，并保留归档结论。

## 等待与待处理事项

`mam wait` 表示调用者已处理完当前工作，可以等待。它先根据当前 task、agent、job 状态检查待处理事项；有事项就立即返回，没有才阻塞。无需消息已读、补报或确认队列，事项未处理时再次调用仍会返回。

| 接口 | 具体操作 |
| --- | --- |
| `mam wait` | 从 `CODEX_THREAD_ID` 识别调用者，自动选择对象，最多等待 3600 秒；不接受 task、agent 或 timeout 参数 |
| `mam wait list` | 显示当前等待者、绑定任务、等待内容和开始时间，首行有表头 |
| `mam wait stop --agent AGENT-ID` | 解除该 agent 的当前等待；不停止 job，不归档任务 |
| `mam wait stop manager` | 解除当前项目唯一未绑定任务的 Manager 等待；不存在或无法唯一确定时明确反馈 |

执行者等待其绑定任务的未归档 jobs。Manager 的范围限于当前 MAM 项目：active 执行者负责自己的 jobs，Manager 等待执行者；非 active 执行者的未归档任务及 jobs 交由 Manager 处理。已归档 job 始终排除，不触发周期探测。已停止、未归档且由当前调用者负责的 job 立即返回；非 active、任务未归档且需 Manager 处理的执行者也立即返回。执行者被唤醒恢复 active 后，Manager 不必等它归档 job 即可继续等待。

源任务存在未归档的 review 任务时，源执行者非 active 不单独触发返回，Manager 转而检查 reviewer。reviewer 非 active 且 review 未归档时，返回 review 任务；review 归档后，源任务恢复通常判断。review 关联不隐藏源任务中无人负责的 stopped jobs。

| 返回原因 | 附带信息 |
| --- | --- |
| 等待超时 | 已达到一小时上限 |
| job 结束 | JOB-ID、note；进程停止不代表实验成功 |
| 执行者结束或已有待处理任务 | AGENT-ID、TASK-ID、task-title |
| `message`：`received new message` | 收到消息的 AGENT-ID |
| `cancelled` | 手动调用 wait stop |
| 空集或错误 | 明确说明没有等待对象或失败原因 |

用户 steer 与 Manager 给执行者的消息只解除接收者当前的等待；用户 queue 不解除等待。普通程序处理进程检查和 App Server 事件，不通过模型轮询。订阅与状态检查必须覆盖交接间隙；服务端断线、身份或必要能力无法确认时明确返回错误，不静默等待一小时。

临时等待登记按 agent 隔离，退出和取消核对进程身份及本次等待 token，陈旧事件不能取消后续等待。不通过返回结果自动归档任何 job 或任务。兼容性按行为测试结果判断，版本信息仅用于诊断。

## 归档

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task archive TASK-ID --note NOTE` | Manager | 要求所有 job 已归档，不检查已归档 job 的实际存活；记录结束结论，移除已登记的各库 worktree 及独立环境，删除对应的本地任务分支，移除 workspace；保留任务说明、简报和历史登记，状态改为“已归档” |

分支删除使用创建时登记的“仓库＋分支名”。移除软链接时保留其指向的共享数据。归档返回各项清理结果；未全部完成则保留未归档状态，再次调用继续清理。是否归档由 Manager 根据任务要求决定。
