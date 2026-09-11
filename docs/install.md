# 安装与更新

在新的 `PROJECT_ROOT` 中先创建项目配置，再 clone MAM。将示例中的绝对路径替换为实际路径；`MAM_BRANCH` 必须是 clone 中已有的本地分支。

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
sudo apt install pipx
bash scripts/install.sh
```

`bash scripts/install.sh` 是唯一的安装入口。它从当前 checkout 用 `pipx install --force` 安装 MAM，把 `~/.local/bin` 加入当前 shell 的 `PATH`，并在 `~/.bashrc` 的非交互 return 之前维护一个带标记的 trace 配置块。更新同一 checkout 后再次运行这一条命令即可。脚本为每次 `.bashrc` 更新创建保留权限的备份，并打印可直接执行的 rollback 命令；它只删除完全匹配的旧 MAM trace export，不改其他内容。

当前 Codex App Server 需要以下环境才会写入行为探测需要的 JSON trace：

```text
RUST_LOG=off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info
LOG_FORMAT=json
```

环境修改不会改变已经运行的 App Server。安装器先从 control socket 确认唯一的 app-managed npm listener，再检查该 listener 的实际环境。若需要重启，它会显示准确的 PID、可执行文件和 socket，并且只有在交互终端输入**完全匹配的** `yes` 后才会向这个单一 PID 发送 `TERM`。请从单独的终端运行安装器，因为重启可能断开 Codex App 的连接。默认输入、`no`、EOF 或非交互运行都会保留所有进程、以非零状态报告安装/验证未完成。

确认后，安装器取得已有的 `app-server-startup.lock`，重新核对 listener 的 PID/启动时间/可执行文件/socket，以及 npm `node … codex … app-server` 父进程的 PID、argv、cwd、环境和 stdio。它只停止这个已重核对的 listener，等待原 npm wrapper 退出后，以捕获的同一 node/npm 命令、cwd 和 app-server log 重启；捕获的环境保持不变，只有 `RUST_LOG` 与 `LOG_FORMAT` 被替换为上述 trace 值。它不会启动 native standalone daemon 或新的 supervisor。随后它确认替换 listener 的 socket、log 和实际环境。若 App 在确认后自行替换目标，安装器不会停止替换进程：替换进程通过同样检查时继续，否则明确以非零状态结束。

随后它在 pipx 安装的 Python 环境中运行完整单元测试与 `multi_agent_manager.wait_compat` 的实时行为检查。无法验证 listener、log、环境或行为测试时都会非零退出，并且不会尝试 standalone fallback。

`require_compatible()` 每次 wait 前都重新检查 control socket、只读 initialize trace、隔离 stdio App Server 的通知送达和 `turn.id` trace 映射。它返回本次验证的 socket、trace 日志和 fingerprint。版本信息只用于排障；版本变化从不阻止通过行为测试的运行时。探测不会创建真实模型 turn 或修改现有 thread。

该探测尚未认证从真实用户消息或 native manager-send 到 MAM wait 的端到端唤醒；需要 Manager 协调真实线程测试后才能将该能力标为已验证。
