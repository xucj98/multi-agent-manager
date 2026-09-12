# 安装与更新

在新的 `PROJECT_ROOT` 中创建项目配置后，从任一属于同一 Git 仓库的 MAM worktree 运行安装器。`MAM_ROOT` 是项目状态与 service 所在的 worktree；安装 checkout 可以是另一个 worktree，二者不必是同一路径，但必须共享 Git common directory。

```bash
project=/absolute/path/to/PROJECT_ROOT
mkdir -p "$project/.mam"
cat > "$project/.mam/env.json" <<JSON
{
  "MAM_ROOT": "$project/multi-agent-manager",
  "PROJECT_ROOT": "$project",
  "MAM_BRANCH": "main"
}
JSON
git clone git@github.com:xucj98/multi-agent-manager.git "$project/multi-agent-manager"
cd "$project/multi-agent-manager"
sudo apt install -y pipx
bash scripts/install.sh
```

安装器先运行 checkout 的单元测试，并以 `pipx install --force` 安装当前 checkout。它将 `~/.local/bin` 写入带标记的 `~/.bashrc` 和一个 login startup file（已有的 `.bash_profile`、`.bash_login`，否则 `.profile`）；`.bashrc` 的块位于常见 noninteractive `return` 之前。正在运行的父 shell 不能被子脚本改写，重新打开 interactive 或 login shell 后 `mam` 会在 `PATH` 中。它同时保留并维护带标记的 MAM App Server trace 配置，改写前创建备份，且不删除可选 `mam wait` 所需的 trace 设置。

可选 `mam wait` 需要 App Server 输出 JSON trace：

```text
RUST_LOG=off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info
LOG_FORMAT=json
```

环境改写不会影响已运行的 App Server。安装器先核对 control socket 的唯一 app-managed listener、其启动方式、socket、日志和实际环境；已满足时不会重启。若必须应用设置，它只会在交互终端显示经核对的目标并收到**完全匹配的** `yes` 后，才向该 listener 发送 `TERM`，以原 node/npm 启动方式和捕获的环境重建它。非交互执行、EOF、任何非 `yes` 输入或重新核对失败都会保留所有进程并以非零状态结束。重启后的启动、socket、日志或环境验证失败会提供受保护的 recovery command；安装器不会创建 standalone App Server 或 shell supervisor。

当前集群没有可用 systemd bus。`mam service` 的 runtime 在 `MAM_ROOT/.local/service` 管理单项目、identity-safe 的 detached daemon；它不会影响其他项目的 service。

每次安装或更新都在接触生产 scheduler 前执行三类验收：

- 可选 wait 行为检查重新连接实际 control socket，确认 JSON trace 中的 initialize、隔离 stdio App Server 的事件通知和 `turn/steer` 到 `turn.id` 的 trace 映射。它使用 ephemeral fixture 和不可能的空 steer，零模型调用；版本仅作为诊断，不能代替行为检查。
- 无模型 API 检查使用新的随机未知 thread ID，依次验证 `thread/read`、`thread/resume`、latest-turn 和 `turn/start` 的实际 event-stream RPC 拒绝路径。它不创建或修改 thread，也不发模型请求。
- 隔离真实 delivery 检查在安装临时目录中新建 fixture project、已登记 task、四个持久化专用 thread 和短本地 job。四个角色先分别完成一个 `gpt-5.6-terra`/`max` baseline；新 persisted thread 只能在首个 `turn/start` 后订阅，每个 baseline 因而立即订阅、等待同一 turn 的 `turn/completed`，再由 `thread/read` 确认为 idle，才读取分页历史。随后验证 job 停止后 executor 收到准确的 `JOB-ID`/note/task title，并验证 no-job 与 archived-job task 一次批量投递到该 fixture 的 Manager；两个 executor 的历史各保持一个 baseline，证明没有收到 scheduler turn。验收固定六个模型 turn（四个 baseline、一次 Manager 批量投递和一次 stopped-job 投递），并跨两个 scheduler 周期确认没有重复 start。若已 idle 的 thread 仍明确拒绝分页历史，receipt 会对同一 thread 记录 `thread/read(includeTurns=true)` 的对照结果并使验收失败，不会新增 baseline 探索。随后 stop fixture service、archive fixture job/task 和仅本次创建的 thread，并删除带所有权标记的临时根；每次验收 JSON 记录 task/job/thread/turn ID、completion 与分页证据、清理结果。

因此 App Server 不可用时安装必定非零退出，即使生产项目尚无 Manager、最终会处于 `awaiting_manager`。wait 检查认证可选 wait 的 trace/notification 行为；wake 轻量检查不声称已观察真实 delivery；后一项才是每次安装的一键真实投递验收。失败时安装 transcript 保留截断并对常见 `TOKEN`/`SECRET`/`PASSWORD`/`API_KEY` assignment 打码的诊断，fixture 仍会清理自身资源。

三项验收通过后，安装器才对当前项目调用 `mam service status`、必要时 `stop`、`start` 和最终 `status`。更新时只会替换同一项目的 detached singleton，保留 runtime 的持久化 Manager binding 与 pending delivery state；它不会在任一 compatibility/live acceptance 失败时停止现有 service。

成功结果有两种：

- `scheduler healthy`：daemon 已有持久化 Manager binding，可投递待办。
- `scheduler awaiting first Manager binding`：新项目没有 Manager 且没有 bound task，daemon 空闲等待。首次由未绑定 Manager 执行的 task create/bind 会登记 Manager，此后无需重新安装；此状态不表示已经开始投递任务。

已有 bound task 却没有可确定的 Manager 时，安装以非零状态退出并提示：

```bash
mam service start --manager AGENT-ID
```

首次设置也可以显式传入该值；安装器不会从自己的 `CODEX_THREAD_ID` 猜测 Manager：

```bash
MAM_SERVICE_MANAGER=AGENT-ID bash scripts/install.sh
```

日常查看和恢复在项目目录中使用 pipx launcher：

```bash
mam service status
mam service start
mam service start --manager AGENT-ID
mam service stop
```

默认工作流是在当前工作完成后结束 turn，由 proactive service 后续投递待办。需要在当前 turn 内等待时，仍可选择使用稳定的 wait 接口：

```bash
mam wait
mam wait list
mam wait stop manager
mam wait stop --agent AGENT-ID
```

`mam wait` 最多等待一小时；已有待办会立即返回。用户 steer 或 Manager 消息会解除对应 wait，`wait stop` 也可手动解除，二者都不会停止 job。它们是 wait 的局部返回原因，proactive daemon 不产生 receive-message、timeout 或 cancelled delivery event。
