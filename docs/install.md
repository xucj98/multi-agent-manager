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

安装器先运行 checkout 的单元测试，并以 `pipx install --force` 安装当前 checkout。它将 `~/.local/bin` 写入带标记的 `~/.bashrc` 和一个 login startup file（已有的 `.bash_profile`、`.bash_login`，否则 `.profile`）；`.bashrc` 的块位于常见 noninteractive `return` 之前。正在运行的父 shell 不能被子脚本改写，重新打开 interactive 或 login shell 后 `mam` 会在 `PATH` 中。安装器保留其他 startup 内容，只移除完全匹配的旧 MAM trace block，并在改写前创建备份。

当前集群没有可用 systemd bus。`mam service` 的 runtime 在 `MAM_ROOT/.local/service` 管理单项目、identity-safe 的 detached daemon；安装器不创建 shell supervisor，不重启 Codex App Server，也不会影响其他项目的 service。

每次安装或更新都在接触生产 scheduler 前执行两类验收：

- 无模型 API 检查使用新的随机未知 thread ID，依次验证 `thread/read`、`thread/resume`、latest-turn 和 `turn/start` 的实际 event-stream RPC 拒绝路径。它不创建或修改 thread，也不发模型请求。
- 隔离真实 delivery 检查在安装临时目录中新建 fixture project、已登记 task、四个持久化专用 thread 和短本地 job。四个角色先分别完成一个 `gpt-5.6-terra`/`max` baseline；新 persisted thread 只能在首个 `turn/start` 后订阅，每个 baseline 因而立即订阅、等待同一 turn 的 `turn/completed`，再由 `thread/read` 确认为 idle，才读取分页历史。随后验证 job 停止后 executor 收到准确的 `JOB-ID`/note/task title，并验证 no-job 与 archived-job task 一次批量投递到该 fixture 的 Manager；两个 executor 的历史各保持一个 baseline，证明没有收到 scheduler turn。验收固定六个模型 turn（四个 baseline、一次 Manager 批量投递和一次 stopped-job 投递），并跨两个 scheduler 周期确认没有重复 start。若已 idle 的 thread 仍明确拒绝分页历史，receipt 会对同一 thread 记录 `thread/read(includeTurns=true)` 的对照结果并使验收失败，不会新增 baseline 探索。随后 stop fixture service、archive fixture job/task 和仅本次创建的 thread，并删除带所有权标记的临时根；每次验收 JSON 记录 task/job/thread/turn ID、completion 与分页证据、清理结果。

因此 App Server 不可用时安装必定非零退出，即使生产项目尚无 Manager、最终会处于 `awaiting_manager`。轻量检查不声称已观察 event notification 或真实 delivery；后一项才是每次安装的一键真实投递验收。失败时安装 transcript 保留截断并对常见 `TOKEN`/`SECRET`/`PASSWORD`/`API_KEY` assignment 打码的诊断，fixture 仍会清理自身资源。

两项验收通过后，安装器才对当前项目调用 `mam service status`、必要时 `stop`、`start` 和最终 `status`。更新时只会替换同一项目的 detached singleton，保留 runtime 的持久化 Manager binding 与 pending delivery state；它不会在 compatibility/live acceptance 失败时停止现有 service。

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
