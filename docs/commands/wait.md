# mam wait

在当前 turn 内等待待办或消息。通常直接结束 turn，由[自动唤醒服务](service.md)后续通知；需要继续当前 turn 时才使用 wait。

## 接口

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam wait` | Manager、执行者 | 根据 CODEX_THREAD_ID 识别调用者及所属任务；有待办立即返回，否则最多等待一小时。 |
| `mam wait list` | 所有人 | 列出当前实例的等待者、绑定任务、等待内容和开始时间。 |
| `mam wait stop --agent AGENT-ID\|AGENT-PATH` | Manager、执行者 | 按线程 ID 或当前原生协作树内的完整路径解除指定执行者的等待；不停止 job、不归档任务。 |
| `mam wait stop manager` | Manager、执行者 | 解除 Manager 的等待；无法唯一确认等待者时返回错误。 |

执行者等待自己的 job；Manager 等待任务执行者的交接和 job 待办。只有运行中的 job 时继续等待；已停止的 job 优先返回，活动 review 不会掩盖它。
登记等待时会核对当前任务绑定或已登记的 Manager；交接后旧身份的等待请求会被拒绝。尚未登记 Manager 且没有活动执行者绑定时，仍允许未绑定调用者等待；已有执行者绑定则须先登记 Manager。

## 返回结果

结果为 JSON，包含返回原因和相关 agent；任务或进程待办还包含 TASK-ID，进程待办包含 JOB-ID 和用途。

| reason | 含义及后续操作 |
| --- | --- |
| `job_stopped` | 进程已停止，由所属执行者检查结果并收尾 |
| `agent_completed` | 执行者已结束 turn，且无未归档 job；Manager 检查交付，不代表任务已通过验收 |
| `message` | 收到用户或 Manager 的新消息，按消息继续工作 |
| `cancelled` | 等待被 wait stop 解除 |
| `timeout` | 等待已满一小时 |
| `empty` | 当前没有需要等待的执行者或 job |
| `error` | 无法确认调用者、连接或等待条件，按返回信息处理 |

解除或超时只结束本次等待。当前无事可做时结束 turn，无需反复调用 wait 或查询状态。

`mam wait` 继续自动识别调用者，无需传入执行者 UUID 或 TASK-ID。list 优先展示已登记的协作路径；路径无法唯一定位时返回错误，显式 AGENT-ID 仍可用于诊断。
