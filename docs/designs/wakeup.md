# 自动唤醒设计（待开发）

收件人空闲时，依据当前 task/job 状态即时生成并合并投递自动提醒。`blocked` 和已归档任务不产生自动提醒。

## 通知条件

| 类型 | 条件 | 收件人 |
| --- | --- | --- |
| `job exited` | 有未归档的 exited job | 执行者；由于当前 codex 版本无法直接投递，因此投递给 Manager 转达 |
| `task pending` | 原任务与关联 review 中，未归档任务均为 pending | Manager |

review 只考虑与原任务的直接关联；没有 review 时只检查本任务。状态定义见[任务状态](task.md#任务状态)。

## 提醒次数

每个 task（包括 review）独立保存自动提醒次数，两种类型共用一个计数器，仅在自身状态实际变化时清零。成功发起一次自动唤醒，本次涉及的各 task 分别计一次；同一 task 的多条提醒合并计一次。次数未达上限且当前条件仍成立时，可在收件人再次空闲时提醒。

最后一次在对应条目末尾追加 `Final reminder (N/N) for this round.`，达到上限后停止自动提醒。`mam task status` 展示次数和上限，达到上限时显示 `Reminder limit reached`。上限 N 暂定为 3。

自动提醒采用统一的[消息格式](service.md#消息格式待开发)。[主动消息](message.md)按发送者提供的正文保存和投递。
