# mam message

向当前实例的 Manager 发送消息。MAM 从 `CODEX_THREAD_ID` 识别发送者，无需调用者查询 Manager 状态。

| 接口 | 操作 |
| --- | --- |
| `mam message send --message TEXT [--immediate] [--task TASK-ID\|AGENT-PATH]` | 保存消息并返回消息标识和投递状态。 |

| 类型 | Manager active | Manager idle |
| --- | --- | --- |
| 默认 | 排队，等当前 turn 结束 | 唤醒并投递 |
| `--immediate` | 送入当前 turn | 唤醒并投递 |

已绑定任务时自动关联；`--task` 可显式指定当前实例的任务，未绑定任务也可发送。展示规则见[消息格式](service.md#消息格式待开发)。

命令不等待 Manager 回复。未投递消息保留到后续处理，服务重启后继续；Manager 接管后发给当前 Manager。投递问题可查 `mam service status`。

投递渠道见[服务配置](service.md#消息渠道)。
