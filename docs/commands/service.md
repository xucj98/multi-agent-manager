# mam service

管理当前 MAM 实例的自动唤醒服务。Agent 完成当前可执行工作后结束 turn，服务在需要后续处理时通知负责人。

## 接口

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam service start [--manager AGENT-ID]` | Manager、安装者 | 启动或复用当前实例的服务，返回 JSON 状态；可显式指定首次绑定的 Manager。 |
| `mam service stop` | Manager、安装者 | 停止当前实例的服务；job 继续运行，任务和 workspace 保留。 |
| `mam service status` | 所有人 | 返回服务是否运行、健康状态、Manager、待办和错误信息。 |
| `mam service set message-channel tool\|user` | Manager、安装者 | 设置本实例的消息渠道，立即生效并保存。 |
| `mam service rebind-manager --note NOTE` | 新 Manager | 从 CODEX_THREAD_ID 确认原生根线程身份，接管本实例 Manager 并记录交接理由。 |

新实例尚未绑定 Manager 时显示 awaiting_manager。Manager 首次 create 任务时可自动登记；已有任务但无法确认 Manager 时，使用 start 的 `--manager` 参数。当前 start 不能替换已绑定的 Manager。

接管前旧 Manager 必须已结束 turn，且状态可确认；新 Manager 正在调用命令不构成阻碍。已绑定的执行者不能成为 Manager。重复接管同一身份无副作用。任务、执行者、job、workspace 和服务记录保留；后续通知和未投递的主动消息发给新 Manager。原生父子关系不变，旧树的协作路径仍按旧树解释。

## 实例升级（待开发）

在 agent 暂停工作、现有 MAM 命令结束且 daemon 已停止后执行 `mam service upgrade`。命令根据当前目录对应的 `.mam/env.json` 升级一个实例：

1. 备份 `MAM_ROOT/.local/`。
2. 将已安装 `mam` 对应的发布 tag 或 commit 合并到 `MAM_BRANCH`；本地缺少该版本时，从 `MAM_ROOT` 已配置的 `origin` 获取。
3. 按版本顺序执行数据迁移，输出升级结果、备份位置和各版升级适配说明的位置。

新版程序保留自 0.1.0 起的完整迁移链，从实例记录的版本依次迁移到目标版本。每步迁移成功后再记录版本；中断或失败后可重试。测试在 [install.sh](install.md#安装与测试) 中完成，实例升级直接执行合并与迁移。

本地修改妨碍合并时，可先 `git stash push -u`，升级后 `git stash pop`。合并冲突时暂停升级，按 Git 提示处理后重试 `mam service upgrade`。

### 多实例与恢复

系统程序更新后，逐实例升级、适配配置及 hooks，并对原先运行的实例显式执行 `mam service start`。失败实例保留备份、保持停止。停止的旧实例可延后升级，再次使用前执行 `mam service upgrade`。

任务和 job 保留，长进程继续运行。恢复 daemon 后继续跟踪 job、处理停机期间退出的 job，并保留原有消息和投递记录。`mam service start` 启动时检查 App Server 连接与所需接口；`mam service status` 显示 `mam`、daemon 和数据版本。

## 何时通知

| 情况 | 处理 |
| --- | --- |
| 有未归档的 exited job | 通知执行者检查结果并归档 job |
| 原任务与关联的未归档 review 中，有 active agent 或 running job | 等待执行推进 |
| 原任务与关联 review 都空闲 | 通知 Manager 检查报告、继续派工、review 或归档 |

自动提醒在负责人空闲时投递。每次按当前任务、job 和 review 状态判断并合批；Manager 再次空闲时，尚待处理的事项继续提醒。原任务与 review 双向关联，同一 review 可以接续多轮返工。exited job 始终保留收尾待办。

用户暂停或中断的 turn 等待用户恢复；状态无法确认时保留诊断，待确认后处理。

通知以 `[MAM Message]` 开头，给出相关任务或执行者、job 及下一步动作。

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

## 消息渠道

```text
mam service set message-channel tool
mam service set message-channel user
```

默认 `tool`，以工具输出投递；`user` 以可见的用户消息投递，便于验收。设置作用于本实例全部 MAM 消息，运行中的服务无需重启，重启后继续沿用。`mam service status` 的 `message_channel` 显示当前选择。

执行者使用 [mam message](message.md) 发送消息，默认在 Manager 空闲时投递；加 `--immediate` 可投递到当前 turn。

## 消息与状态输出

通知优先使用当前 Manager 可用的执行者路径；其他任务用 TASK-ID 定位。Manager 转发 job 消息示例：

```text
[MAM Message]
/root/worker: job JOB-ID has exited. Use followup_task to ask the executor to check the result and archive the job.
```

执行者结束当前工作后的通知示例：

```text
[MAM Message]
/root/worker needs follow-up. Check the report; continue the work, request review, or archive the task.
```
