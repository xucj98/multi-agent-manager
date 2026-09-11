# 交付

- `multi_agent_manager/wait_compat.py` 提供无参数 `require_compatible()`。每次调用都会重新验证 live control socket、该次 initialize 的 JSON trace 归因，以及隔离 stdio App Server 的 ephemeral-thread 通知、无模型 `turn/steer` 拒绝和 `turn.id` trace 映射；没有版本门槛、allowlist、证书、cursor、replay 或 ack 状态。
- CLI/App 版本只在 `diagnostics` 中显示，且已从 behavioral fingerprint 排除：版本变化本身不会改变兼容性结论，只有探测行为失败才会报错。
- `scripts/install.sh` 取代 `install_and_test.sh`，成为唯一入口 `bash scripts/install.sh`。它从当前 checkout 经 `pipx install --force` 安装 MAM，维护 `.bashrc` 的标记 trace 块（位于非交互 return 之前、仅删除完全匹配的旧 MAM trace 行、保留 mode、变更前备份并打印 rollback）；重复运行不累积 block 或备份。
- 安装器用 control socket 的 kernel inode 找到唯一 listener，核对 `app-server --listen unix://`、listener 的 PID/start ticks/executable/socket 和 npm `node … codex … app-server` 父进程。只有交互终端输入完全匹配的 `yes` 后才会向该单一 listener 发 `TERM`；确认后再次核对完整 identity。默认、`no`、EOF、非交互或目标变化均不发信号且非零退出。替换 listener 未能由 App 自身出现时也非零退出，且不会启动 standalone fallback。
- `docs/install.md` 现在给出 fresh `PROJECT_ROOT`、`.mam/env.json`、clone、`sudo apt install pipx` 和唯一安装命令的实际流程。
- 兼容性测试增至 15 项，覆盖版本变化仍通过且 fingerprint 不变、断开的 live runtime、事件/trace/safety 失败，以及隔离的 `.bashrc` 幂等/回滚、精确 `yes`、非交互拒绝和确认后目标身份变化不发送信号。

## 验证

- `bash -n scripts/install.sh` 与 `git diff --check`：通过。
- `.venv/bin/python -B -m unittest tests.test_wait_compat -v`：15 passed。
- `.venv/bin/python -B -m unittest discover -s tests -v`：56 passed，30.727s。
- `python -m multi_agent_manager.wait_compat`：live 行为探测 PASS；只读验证 control socket、fresh trace binding 和隔离无模型 probe。
- 只读执行 `discover_app_server` 与 `runtime_logging_ready`：识别当前 app-managed npm listener 及其 JSON trace 环境。开发期间未运行安装器主流程，因此未修改真实 `.bashrc`、未执行全局 `pipx install`、未重启 live App Server。

## 交付位置

- Workspace: `/mnt/public/xcj/Projects/workspace/5b3fe28b-3d9c-444f-bf24-889b2453558c/multi-agent-manager`
- Branch: `task/5b3fe28b-3d9c-444f-bf24-889b2453558c`
- Commits: `e20da6d52525267e035549c3447fbd6d3409df27` (`Add behavioral wait compatibility checks`)；`e23d693e5f8af5c9234da0c60148af3dc72b2fcd` (`Add confirmed App Server installer`)

## Runtime 交接与未认证范围

`require_compatible()` 的公开接口已就绪，Runtime owner 应在每次真正进入 block 前调用它；`cli.py`、`job_runtime.py` 和其他 wait 模块不在本任务的写入范围，未在本 worktree 改动。接口不保存 completion replay/cursor 状态，可直接配合当前 state-based pending-work 语义。

自检仍将 `native_message_wake` 标为 `not-certified`：它不宣称已验证真实用户消息或 native manager-send 到 MAM wait 的端到端唤醒。真实 restart 的 App-supervisor replacement 行为同样按任务要求未在 live 服务上试验；安装器会在无法观察到 replacement 时安全失败，Manager 可在独立终端协调一次确认后的实机验收。
