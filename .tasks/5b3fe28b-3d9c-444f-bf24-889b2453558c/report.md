# 交付

- `multi_agent_manager/wait_compat.py` 提供无参数 `require_compatible()`：每次重新验证 live control socket、该次 initialize 的 JSON trace 归因，以及隔离 stdio App Server 的 notification、无模型 `turn/steer` 拒绝和 `turn.id` trace 映射。版本仅在 diagnostics 中显示；没有 version gate、allowlist、certificate、cursor、replay 或 ack。
- `scripts/install.sh` 是唯一入口。它从 checkout 经 `pipx install --force` 安装 MAM，并幂等维护 `.bashrc` 的标记 trace block、权限与可回滚备份。
- 当 listener 缺少 trace 环境时，安装器只在交互终端输入精确的 `yes` 后才继续。它捕获 listener 与 npm `node … codex … app-server` wrapper 的 PID/start ticks、executable、argv、cwd、完整环境、stdio 和 log identity；取得已有 `app-server-startup.lock` 后重新比较该 record，才向该单一 listener 发 `TERM`。
- 原 listener 与 wrapper 离开后，安装器以捕获的同一 node/npm wrapper 命令、cwd 和 app-server log 重建 listener。环境保持捕获值，只有 `RUST_LOG` 和 `LOG_FORMAT` 被替换为 trace 值；不会启动 native standalone daemon 或新 supervisor。替换 listener 必须通过 socket、log、环境和 wrapper-record 验证。
- 若 App 在确认前后并发替换 target，安装器不 signal replacement：可验证的 replacement 继续运行，未验证的 replacement 清晰非零退出。没有版本、fingerprint、certificate 或 allowlist 会拒绝行为测试通过的版本。
- `docs/install.md` 说明 fresh `PROJECT_ROOT`、`.mam/env.json`、clone、`sudo apt install pipx` 和唯一的 `bash scripts/install.sh` 工作流，以及 deterministic app-managed restart 的边界。

## Review 8d648d66 fixes

- `runtime_logging_ready()` 现在保留 embedded Python 的真实退出状态；`ensure_runtime_logging()` 将缺少 trace 环境（可走确认后的 restart）与 PID/environment 不可读（不 restart）分开处理。
- 隔离测试覆盖两种状态、exact-yes/noninteractive、startup-lock cleanup、confirmation/replacement races、record 环境匹配、wrapper argv/cwd/env/log 重放，以及一个真实临时 Unix-socket node/npm wrapper 的完整 stop/relaunch/validate/cleanup。

## 最终 review 修复（`fe108cc`）

- 在重新核对 listener record 后、发送 `TERM` 前，安装器用同一启动路径完整预检捕获的 node/npm launch plan：socket 仍为当前 control socket、node/Codex wrapper、argv、cwd、环境、stdio、log identity，以及 `/dev/null` 和 append log 都可用。预检失败明确报告“no process was stopped”。
- 紧邻 `TERM` 前，在 control 目录下创建 `700` 私有恢复目录，把含完整捕获环境的 `launch-plan.b64` 以 `600` 保存，并生成 `700` 的 `recover-app-server.sh`。任何 TERM 后的等待、启动、验证失败，或受管 `INT`/`HUP`/`TERM`/异常退出，都会释放 startup lock、以非零状态结束并仅打印可复制的 `Recovery command: bash …/recover-app-server.sh`；不会输出计划或环境内容。验证成功后删除恢复工件并清除 traps。
- 恢复脚本取得同一 startup lock 后按捕获的 app-managed node/npm 命令启动；它不引入 supervisor、retry 或 standalone fallback。若 wrapper 已不可执行，它报告该失败且不声称服务已恢复。
- `docs/install.md` 说明预检、TERM 后的恢复命令、`600` 计划文件，以及恢复后须再次运行安装器验证的边界。

## 验证

- `bash -n scripts/install.sh` 与 `git diff --check`：通过。
- `.venv/bin/python -W error::ResourceWarning -B -m unittest discover -s tests -v`：73 passed。
- `.venv/bin/python -W error::ResourceWarning -B -m multi_agent_manager.wait_compat`：PASS；只读验证当前 control socket，并启动隔离 stdio probe。输出仍明确 native user-message/native-manager-send wake 未认证。
- 新增隔离覆盖：预检失败不 TERM；TERM 后 wrapper 启动失败时的私有 mode-600 恢复计划和命令；`INT` 与受管退出的非零恢复路径和 lock 释放；成功路径的 artifact/trap cleanup；已有临时 Unix-socket node/npm 完整重启 harness 断言成功后没有残留恢复目录。

## 交付位置

- Workspace: `/mnt/public/xcj/Projects/workspace/5b3fe28b-3d9c-444f-bf24-889b2453558c/multi-agent-manager`
- Branch: `task/5b3fe28b-3d9c-444f-bf24-889b2453558c`
- Commits: `e20da6d52525267e035549c3447fbd6d3409df27` (behavioral compatibility), `e23d693e5f8af5c9234da0c60148af3dc72b2fcd` (installer), `80b190fbdb17466d49a90cdc394bd97a2fafb6c9` (probe pipe cleanup), `679c859` (deterministic restart), `fe108cc` (preflight and post-TERM recovery).

Development did not run installer main: no production `.bashrc` edit, pipx/global installation, or live App Server restart occurred. Native user-message/native-manager-send wake behavior remains `not-certified`; the compatibility probe does not falsely claim that end-to-end behavior is tested.
