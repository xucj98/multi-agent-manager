# mam service

管理当前 MAM 实例的自动唤醒服务。Agent 完成当前可执行工作后结束 turn，服务在需要后续处理时通知负责人。

## 接口

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam service start [--manager AGENT-ID]` | Manager、安装者 | 启动或复用当前实例的服务，返回 JSON 状态；可显式指定首次绑定的 Manager。 |
| `mam service stop` | Manager、安装者 | 停止当前实例的服务；job 继续运行，任务和 workspace 保留。 |
| `mam service status` | 所有人 | 返回服务是否运行、健康状态、Manager、待办和错误信息。 |

新实例尚未绑定 Manager 时显示 awaiting_manager。Manager 首次 create 或 bind 任务后可自动登记；已有任务但无法确认 Manager 时，使用 start 的 `--manager` 参数。当前 start 不能替换已绑定的 Manager。

## 何时通知

| 情况 | 处理 |
| --- | --- |
| 有未归档的 stopped job | 通知执行者检查结果并归档 job |
| job 仍在运行 | 继续监控 |
| 执行者已结束 turn，且无未归档 job | 通知 Manager 检查交付、安排 review 或归档 |
| 源任务有未归档的 review | 等待 reviewer；源任务的 stopped job 仍通知执行者 |

负责人正在工作或使用 wait 时，服务保留待办；用户暂停或中断的 turn 不会被自动恢复。状态无法确认时保留诊断，待确认后处理。

通知以 `[MAM Message]` 开头，包含相关任务、job 或执行者标识及用途。收到通知后，负责人按任务要求处理；进程停止或执行者结束 turn 都不表示任务成功。

## 状态与故障处理

| status | 含义 |
| --- | --- |
| `healthy` | 服务正常运行 |
| `pending` | 有待办等待处理或投递 |
| `awaiting_manager` | 等待绑定 Manager |
| `disabled` | 服务已停用 |
| `error` | 服务存在需要处理的错误，详情见返回信息 |

`running` 和 `healthy` 描述服务自身；有这些标志仍可能存在未投递的待办。

某些 subagent 不接受直接唤醒时，服务会通知 Manager 协调。Manager 先查看执行者状态和 report，确认尚未处理后，通过原生 follow-up 通知执行者收尾。服务状态中的 blocked 待办会保留，直到对应工作被处理。

## 待开发

### Manager 接管

候选接口为 `mam service rebind-manager --note NOTE`，由新 Manager 调用，从 CODEX_THREAD_ID 自动取得身份。保留任务、执行者、job、workspace 和待办，并记录交接理由。

接管不改变 Codex 原生父子关系，也不把旧协作树的路径解释成新树中的同名执行者。需要换人时，由新 Manager 创建 subagent，再由执行者 `mam task start TASK-ID` 接续原任务。

### 执行者主动发消息

提供消息发送接口，正文必填，收件人默认当前实例的 Manager。MAM 自动识别发送者及其协作路径；TASK-ID 可选，未绑定任务的 subagent 也可请求裁决或报告问题。具体命令名和参数待定。

Manager idle 时投递并唤醒；正在工作时保留待办，继续遵守用户暂停或中断的保护。消息展示发送者和正文，有关联任务时再附任务信息。

### 消息与状态输出

区分“请验收任务”和“请转发 job 停止消息”，优先展示可用的执行者协作路径、相关任务或 job 及下一步动作；避免已处理交付或 Manager 自己整理报告后再次触发无事可做的唤醒。

原生 subagent 无法直接接收时，保留 Manager 转发路径，不维护 Codex fork。拟议消息如下（尚未实现）：

```text
[MAM Message]
需要 Manager 转发：登记的进程已停止，执行者无法直接唤醒。
TASK-ID: ...（任务标题）
JOB-ID: ...（进程用途）
执行者: /root/worker
请先确认该 job 尚未收尾，再通过原生 follow-up 通知当前执行者：
检查进程结果，按最新 task.md 继续任务，处理后归档该 job。
进程停止不表示成功；本消息不要求归档任务。
```
