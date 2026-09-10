# 任务管理 CLI 接口说明

MAM 通过文件和 CLI 管理当前集群的任务，顶层命令为 `mam task`、`mam job`、`mam wait`、`mam workspace`。所有 agent 和管理命令在本机运行；GPU 作业可通过 SSH 在 wuwen-1 运行，两端共享 `/mnt/public`。以下为已确认的实施接口。全局 `mam --root <目录> …` 可覆盖管理资料根目录；默认使用 `/mnt/public/xcj/Projects/multi-agent-manager`，日常无需指定。

使用者分为 Manager 和执行者。Manager 为 subagent 登记任务，自己的工作无需创建任务。代码实现、review、实验等是不同的任务内容，负责完成任务的 agent 统一称为执行者。

## 文件与版本

任务、workspace 和工作分支使用同一个 UUID，由工具生成：

```text
multi-agent-manager/
  .tasks/<uuid>/task.md       # Manager 编辑任务要求
  .tasks/<uuid>/report.md     # 执行者编辑结果简报
  .local/tasks/<uuid>.json    # 工具维护的登记与状态，不进入 Git
  .local/waits/*.json         # 当前等待和取消标记，不进入 Git

Projects/workspace/<uuid>/
  <repo>/                    # 按需创建的 worktree，分支为 task/<uuid>
```

大家共享管理仓库的工作目录，通过编辑工具修改各自负责的文件。`main` 上的 task.md、report.md 是已发布内容，工作目录中的修改是草稿；发布由 CLI 提交到 `main`。读取已发布内容无需 checkout。

## 创建与执行

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task create --title "…"` | Manager | 生成 UUID，登记任务，创建 task.md、report.md 草稿和空 workspace；返回 UUID 与文件、目录路径，状态为“进行中” |
| `mam task create --title "…" --review <source-uuid>` | Manager | 创建任务，并在任务草稿中引用源任务已发布的要求、简报及其代码 commit，固定所引用的版本，供执行者 review |
| `mam task bind <uuid> --agent <agent-id>` | Manager | 将已启动的 subagent 绑定到任务；一个未归档任务对应一个执行 agent，一个 agent 同时绑定一个任务 |
| `mam workspace add <uuid> --repo <repo> --base <commit>` | 执行者 | 调用该库的 `.local/create_worktree.sh`，从 base commit 新建 `task/<uuid>` 分支及对应 worktree，同时创建环境和共享软链接；登记并返回路径与分支名 |

涉及哪些库及其 base commit 由任务说明确定，每个库分别调用 workspace add。具体安装和软链接规则由各库脚本负责。同一任务在不同库使用相同分支名。

## 编辑、发布与查看

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task show <uuid> [--file task\|report] [--revision <commit>]` | 所有人 | 返回已发布的文件内容及版本；默认读取 main 上的 task.md，也可读取指定 commit |
| `mam task publish <uuid> --file task\|report` | 文件负责人 | 加锁，将指定文件的草稿单独提交到 main，返回发布 commit；同步本次文件的暂存内容，保留其他文件的暂存内容及所有草稿；发布 report 时关联简报中注明的任务版本，状态改为“待验收” |
| `mam task list [--archived\|--all]` | 所有人 | 即使为空也输出表头；每行固定为标题、task 状态、完整 UUID、agent、agent 状态。保留既有筛选，不提供 `--json` |
| `mam task status <uuid>` | 所有人 | 显示任务及简报版本、简报依据的任务版本、workspace、各库分支与交付 commit 和归档结果；返回保存的 job 观测而不隐式刷新；提示草稿，以及当前要求与简报所依据的要求是否不同 |

修改要求和简报使用普通编辑工具，再通过 publish 发布。执行者通过 show 获取任务及版本，在 report.md 中注明实际依据的任务 commit。版本差异以本任务文件内容为准，其他任务的提交不会使本任务失效。

## 长任务进程

job 指执行者登记的一个长时间运行的进程。预计运行超过 1 小时的程序（如正式数据生成、训练、评估）通过 `mam job add` 登记，通常的短 smoke 无需登记。同一执行者可为自己的任务登记多个进程，每条登记记录生成一个 job-id，并关联所属任务，以便 Manager 找到对应执行者。

job 状态为“进行中／已停止／已归档”：查询确认进程结束后变为“已停止”，表示尚待执行者处理；执行者完成结果记录、文件清理等任务要求后，通过 job archive 标记“已归档”。

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam job add <uuid> --note "…" --host <host> --pid <pid>` | 执行者 | 将指定进程登记到自己的任务下，记录用途、主机、PID 和实际启动时间；无法换算时列表显示 unknown，生成并返回 job-id |
| `mam job list [--task <uuid>] [--status running\|stopped\|archived\|all]` | 所有人 | 默认有表头，每行固定为描述、job 状态、开始时间、job-id、任务描述、task-id；保留筛选，不提供 `--json`。unknown 探测显示 `unknown/待核实`，不冒充 running 或 stopped |
| `mam job list --attention` | Manager | 查询进程和 agent 状态，筛选已停止、未归档且执行者已不在运行的 job；不确定项仍在同一表中显示 `unknown/待核实` |
| `mam job status <job-id>` | 所有人 | 只刷新该 job，不扫描其他进程；完整 JSON 返回登记、实时探测及其 checked_at、身份、所属 task 和 agent |
| `mam job archive <job-id> --note "…"` | 执行者 | 记录简短的处理结论或成果位置，将该 job 标记为“已归档”，保留历史记录 |

进程查询在其所属主机执行，远端通过 SSH 查询，核对 PID 和启动时间；查询失败时保留上次状态与时间，并标注“本次查询失败”，不据此判定进程停止。agent 状态由 CLI 连接承载这些线程的现有 Codex App Server，通过 `thread/read` 查询；`active` 对应执行者仍在运行，查询失败显示“待核实”。本机现有 Unix socket 的只读查询已验证可用，接口见 [App Server 文档](https://learn.chatgpt.com/docs/app-server)。

“需要 Manager 处理”是 job 与 agent 状态的组合筛选，不增加 job 状态。已停止但执行者仍为 running 的 job 由执行者继续处理；进程仍在运行或 job 已归档时，不进入该筛选。已归档 job 保持已归档状态。

job archive 只记录收尾结果，不删除 workspace；任务归档也保留各 job 的独立状态与历史。

## 可停止等待

等待只读取已登记的 job，不启动 daemon、数据库或调度器。临时登记和取消标记保存在本机共享 `.local/waits/`；每个 agent 一条活跃等待，记录本地 PID、启动身份和 token。start、stop、退出清理使用同一 agent 锁和 token，因此陈旧等待不能取消后来者；异常退出后 PID 身份已停止的登记会被清理，不会显示为仍在等待或阻止重开。

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam wait jobs [--task <uuid>] [--timeout <seconds>] [--agent <agent-id>]` | 所有人 | 默认监控当前所有未归档 job，`--task` 缩小范围。已有确定 stopped job 立即返回 `stopped`；任一运行 job 停止时返回 `stopped`；空集返回 `empty`，超时返回 `timeout`。unknown 探测不视作 stopped。轮询只探测必要 job，不探测 agent，也不持有 task 锁睡眠 |
| `mam wait list` | 所有人 | 即使为空也输出表头；每行是 agent-id、绑定 task 标题、task-id、等待内容、等待开始时间。绑定取等待者自己的未归档 task；没有绑定显示“未绑定”，不使用被监控 job 的负责人代替 |
| `mam wait stop --agent <agent-id>` | 所有人 | 仅为该 agent 写取消标记并唤醒等待，返回 `cancelled`；不存在当前等待返回 `not_waiting`。不向 job 进程发信号，不归档 job |

等待者未指定 `--agent` 时，只读取 `CODEX_THREAD_ID`；不从继承的 `CODEX_SESSION_ID` 推测身份。ID 缺失、空白或含换行会明确报错。远端 job 探测在等待中使用短超时，stop 不会被长 SSH 查询无限拖住。

## 归档

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task archive <uuid> --note "…"` | Manager | 记录结束结论，移除已登记的各库 worktree 及独立环境，删除对应的本地任务分支，移除 workspace；保留任务说明、简报和历史登记，状态改为“已归档” |

分支删除使用创建时登记的“仓库＋分支名”。移除软链接时保留其指向的共享数据。归档返回各项清理结果；未全部完成则保留未归档状态，再次调用继续清理。是否归档由 Manager 根据任务要求决定。
