# mam service

管理当前 MAM 实例的自动唤醒服务。通知条件与次数限制见[自动唤醒设计](wakeup.md)。

## 接口

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam service start [--manager AGENT-ID]` | Manager、安装者 | 启动或复用当前实例的服务，返回 JSON 状态；可显式指定首次绑定的 Manager。 |
| `mam service stop` | Manager、安装者 | 停止当前实例的服务；job 继续运行，任务和 workspace 保留。 |
| `mam service status` | 所有人 | 返回服务是否运行、健康状态、Manager、待办和错误信息。 |
| `mam service set message-channel tool\|user` | Manager、安装者 | 设置本实例的消息渠道，立即生效并保存。 |
| `mam service rebind-manager --note NOTE` | 新 Manager | 从 CODEX_THREAD_ID 确认原生根线程身份，接管本实例 Manager 并记录交接理由。 |

新实例尚未绑定 Manager 时显示 awaiting_manager。Manager 首次 create 任务时可自动登记；已有任务但无法确认 Manager 时，使用 start 的 `--manager` 参数。当前 start 不能替换已绑定的 Manager。

接管由新 Manager 显式调用，不查询或限制旧 Manager 的线程状态。已绑定的执行者不能成为 Manager。重复接管同一身份无副作用。任务、执行者、job、workspace 和服务记录保留；后续通知和未投递的主动消息发给新 Manager。原生父子关系不变，旧树的协作路径仍按旧树解释。

## 实例升级

在 agent 暂停工作、现有 MAM 命令结束且 daemon 已停止后执行 `mam service upgrade`。命令根据当前目录对应的 `.mam/env.json` 升级一个实例：

1. 备份 `MAM_ROOT/.local/`。
2. 将已安装 `mam` 对应的发布 tag 或 commit 合并到 `MAM_BRANCH`；本地缺少该版本时，从 `MAM_ROOT` 已配置的 `origin` 获取。
3. 按版本顺序执行数据迁移，输出升级结果、备份位置和各版升级适配说明的位置。

新版程序保留自 0.1.0 起的完整迁移链，从实例记录的版本依次迁移到目标版本。每步迁移成功后再记录版本；中断或失败后可重试。测试在 [install.sh](install.md#安装与测试) 中完成，实例升级直接执行合并与迁移。

本地修改妨碍合并时，可先 `git stash push -u`，升级后 `git stash pop`。合并冲突时暂停升级，按 Git 提示处理后重试 `mam service upgrade`。

### 多实例与恢复

系统程序更新后，逐实例升级、适配配置及 hooks，并对原先运行的实例显式执行 `mam service start`。失败实例保留备份、保持停止。停止的旧实例可延后升级，再次使用前执行 `mam service upgrade`。

任务和 job 保留，长进程继续运行。恢复 daemon 后继续跟踪 job、处理停机期间退出的 job，并保留原有消息和投递记录。`mam service start` 启动时检查 App Server 连接与所需接口；`mam service status` 显示 `mam`、daemon 和数据版本。

## 状态与故障处理

| status | 含义 |
| --- | --- |
| `healthy` | 服务正常运行 |
| `pending` | 有待办等待处理或投递 |
| `awaiting_manager` | 等待绑定 Manager |
| `disabled` | 服务已停用 |
| `error` | 服务存在需要处理的错误，详情见返回信息 |

`running` 和 `healthy` 描述服务自身；有这些标志仍可能存在未投递的待办。

## 消息渠道

```text
mam service set message-channel tool
mam service set message-channel user
```

默认 `tool`，以工具输出投递；`user` 以可见的用户消息投递，便于验收。设置作用于本实例全部 MAM 消息，运行中的服务无需重启，重启后继续沿用。`mam service status` 的 `message_channel` 显示当前选择。

主动消息的发送方式见 [mam message](message.md)。

## 消息格式

一次投递使用一个 `[MAM MESSAGE]` 总标题。每条消息以 `[类型 | 来源]` 开头，正文另起一行，条目之间空一行；两种投递渠道使用相同格式。

消息共三类：`message` 为主动消息，来源是发送者；`job exited` 为进程退出通知，`task pending` 为任务待处理提醒，来源均为对应任务的执行者。

```text
[MAM MESSAGE]

[message | /root/worker]
我已完成迁移并发布报告，请检查。

[job exited | /root/trainer]
There are exited jobs. Ask the executor to check the results and archive them.

[task pending | /root/reviewer]
Check the task and any published report; start or continue the work, request review, block or archive the task.
```

固定提示使用英文，主动消息保留发送者的正文。job 直接通知执行者时，正文为 `There are exited jobs. Check the results and archive them.`；需要 Manager 转发时使用上例。具体 job 由执行者通过 `mam job list --task TASK-ID` 查询。

来源优先显示当前 Manager 可识别的 `AGENT-PATH`；缺少路径时，主动消息显示 `agent: AGENT-ID`，自动提醒显示 `task: TASK-ID`。
