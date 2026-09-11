# 安装与更新

在运行 agent 的本机安装。以下命令安装 GitHub 仓库 `main` 上的工具代码；更新时重新执行 `pipx install`：

```bash
apt install -y pipx
pipx install --force 'multi-agent-manager @ git+ssh://git@github.com/xucj98/multi-agent-manager.git@main'
```

首次安装后，将命令目录加入 PATH：

```bash
pipx ensurepath --force
export PATH="$PATH:$HOME/.local/bin"
mam --help
```

`ensurepath` 为后续终端保存 PATH，`export` 让当前终端立即生效。默认命令入口为 `~/.local/bin/mam`，可以从任意目录调用；`mam --help` 不需要项目配置。pipx 使用独立 Python 环境，安装内容固定于安装时的 Git 提交。

运行任务、job、wait 或 workspace 命令前，在项目目录或其祖先目录放置 `.mam/env.json`：

```json
{
  "MAM_ROOT": "/absolute/path/to/mam-worktree",
  "PROJECT_ROOT": "/absolute/path/to/projects",
  "MAM_BRANCH": "project/state-vla"
}
```

`MAM_ROOT` 可以是普通 checkout 或 linked worktree，必须已有配置中的本地分支。`PROJECT_ROOT` 下保留业务仓库与 `workspace` 的既有布局。安装来源的 `main` 只承载工具代码；项目任务和报告发布到 `MAM_BRANCH`，发布前该 MAM worktree 必须 checkout 在此分支。

## 从明确 checkout 安装并验证等待兼容性

在合并后的本地 checkout 上运行下面一条命令。它用 `pipx` 强制重装该 checkout、检查安装后的 `mam` 入口、运行完整单元测试，并执行 App Server 的行为探测：

```bash
/absolute/path/to/multi-agent-manager/scripts/install_and_test.sh /absolute/path/to/multi-agent-manager
```

运行前需要 `pipx`、可执行的 `codex`，以及已由用户启动的 Codex App。探测绝不会重启、停止或配置用户的 App。它只读连接现有 control socket，并在临时 cwd 中启动一个独立 stdio App Server；该服务器只创建 ephemeral thread，并用必定失败的空 `turn/steer` 请求检查通知送达和 `turn.id` trace 映射，不会启动模型或修改现有 thread。

真实 App 必须把 JSON trace 写到 `~/.codex/app-server-control/app-server.log`。当前所需配置是：

```text
RUST_LOG=off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info
LOG_FORMAT=json
```

失败会以非零状态退出，并说明不能安全启动或继续 MAM wait。按提示由用户手动打开或重启 Codex App、修复 trace 配置后再次运行该命令；脚本不会替用户重启 App。

`require_compatible()` 会在每次 wait 前重新执行这些检查，且会在 trace 中归因本次只读 control-socket 握手，返回 socket 路径、trace 日志路径和本次验证的 fingerprint。它不保存证书、不维护版本白名单，也不比较 App Server 与 CLI 的版本：版本信息仅用于诊断，版本变化本身不会阻塞通过行为测试的运行时。

该探测验证 control socket、一般服务器通知和 trace 关联。它不声称已经验证用户消息或 native manager-send 从 Codex App 到 MAM wait 的端到端唤醒；这项试验仍需要 Manager 协调的真实线程测试。
