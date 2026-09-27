# mam message

向当前实例的 Manager 发送消息。MAM 从 `CODEX_THREAD_ID` 识别发送者，无需调用者查询 Manager 状态。

| 接口 | 操作 |
| --- | --- |
| `mam message send --message TEXT [--defer] [--task TASK-ID\|AGENT-PATH]` | 保存消息并返回消息标识和投递状态；默认及时发送，`--defer` 表示抄送。 |

| 类型 | Manager active | Manager idle |
| --- | --- | --- |
| 及时信息（默认） | 送入当前 turn | 唤醒并投递 |
| 抄送信息（`--defer`） | 排队，等当前 turn 结束 | 唤醒并投递 |

已绑定任务时自动关联；`--task` 可显式指定当前实例的任务，未绑定任务也可发送。消息包含发送者和正文，接收后由 Manager 决定后续动作。

命令不等待 Manager 回复。未投递消息保留到后续处理，服务重启后继续；Manager 接管后发给当前 Manager。暂停或中断的 turn 等待用户恢复，投递问题可查 `mam service status`。

消息默认以工具输出送达；需要在客户端查看消息时，用 `mam service set message-channel user` 切换。详见[服务配置](service.md#消息渠道)。
