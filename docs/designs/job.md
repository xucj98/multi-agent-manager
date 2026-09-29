# mam job

job 是任务下登记的长进程，每条记录有独立 JOB-ID。预计超过 30 分钟的程序需要登记，短 smoke 无需登记。

## 登记与查询

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam job add [TASK-ID\|AGENT-PATH] --note NOTE --host HOST --pid PID` | 执行者 | 将已启动的进程登记到任务，记录用途、主机、PID 和启动身份，返回 JOB-ID。 |
| `mam job list [--task TASK-ID\|AGENT-PATH] [--status STATUS]` | 所有人 | 查询并列出 job；默认显示未归档项。表格包含描述、状态、开始时间、JOB-ID、任务描述、TASK-ID 和执行者路径（旧记录回退为 AGENT-ID）。 |
| `mam job list --attention` | Manager | 筛选已退出、未归档且执行者已空闲的 job，同时列出需要核实的项目。 |
| `mam job status JOB-ID` | 所有人 | 刷新指定 job，返回精简 JSON，包含任务、执行者、主机、PID、开始时间、进程状态和检查时间。 |
| `mam job archive JOB-ID --note NOTE` | 执行者 | 记录处理结论或成果位置，结束跟踪，保留最后观测及历史记录；不停止进程。 |

`HOST` 可用 `local`、SSH 别名或 `username@hostname`；远端查询需要 SSH 可达。`STATUS` 可为 `running`、`exited`、`archived` 或 `all`。
任务可用 TASK-ID 或当前原生协作树内的完整执行者路径 AGENT-PATH 定位；已绑定执行者使用 add 时可省略任务参数。历史任务仍用 TASK-ID。

## 状态与收尾

| 状态 | 含义 |
| --- | --- |
| `running` | 登记成功时的初始状态，已确认进程正在运行 |
| `exited` | 已确认进程退出，等待执行者处理 |
| `unknown` | 本次无法确认，返回原因及已有的最后观测 |
| `archived` | 已结束 MAM 跟踪，保留记录 |

查询按当前观测更新状态，`unknown` 时保留最后一次确认的状态。`job archive` 可将任一未归档状态转为 `archived`。

进程退出后，执行者查询自己的 job、判断结果、按项目要求更新记录并归档。

archive 也可用于不再需要跟踪的运行中进程，不会查询或终止它。已归档 job 不再探测或唤醒。

## 待开发

新增 `mam job submit [TASK-ID|AGENT-PATH] --command COMMAND`，一次完成登记与启动，立即返回 JOB-ID。命令属于当前实例中的任务，可在本地或指定远端运行；现有 add 保留给已经启动的进程，不另设 exec 接口。

submit 将沿用 [任务定位规则](task.md)：已绑定执行者可省略任务参数，显式指定时可用 TASK-ID 或 AGENT-PATH。list 的 `--task` 使用相同定位规则；省略筛选时仍列出当前实例全部未归档 job。一个任务可有多个 job，status 和 archive 继续使用 JOB-ID。

submit 可附带 GPU 条件：需要 N 张卡，每张卡空闲显存大于 X GiB，过去 30 秒平均利用率小于 20%（阈值和窗口可配置）。条件未满足时排队，由同一 MAM 实例分配资源，避免自己的 job 重复拿到同一张卡。可使用同步后的远端 workspace。

不同 MAM 实例无需互相协调。外部进程竞争资源后，若本进程停止，MAM 通知所属执行者处理；不判断业务失败，也不自动重跑。具体资源参数和排队操作待定。
