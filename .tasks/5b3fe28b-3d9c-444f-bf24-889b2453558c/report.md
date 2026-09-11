# 交付

- 在 `multi_agent_manager/wait_compat.py` 提供无参数 `require_compatible()`：每次调用都重新验证 live control socket、该次握手的 JSON trace 归因，以及独立 stdio App Server 的 ephemeral-thread 通知、无模型 `turn/steer` 拒绝和 `turn.id` trace 映射。返回 socket 路径、日志路径和本次 fingerprint；没有版本门槛、cursor/replay/ack 或持久化 PASS/证书。
- 版本仅保留在诊断信息中。CLI/App 版本变化或不匹配在行为探测通过时不会报错；行为失败会给出要求用户手动打开/重启 App 并重新运行安装脚本的 `RuntimeError`。
- 新增 `scripts/install_and_test.sh CHECKOUT`，从明确 checkout 经 `pipx` 安装、检查实际 `mam` 入口、运行完整单测和已安装模块的自检；不自动重启 App。`docs/install.md` 说明该流程和 trace 前提。
- 新增 9 个兼容性单测，覆盖版本变化/缺失、版本不匹配、重启或配置变化重新验证、失联 runtime、事件投递失败、trace 缺失、turn 映射缺失和安全请求失败。

## 验证

- `.venv/bin/python -B -m unittest tests.test_wait_compat -v`：9 passed。
- `.venv/bin/python -B -m unittest discover -s tests -q`：50 passed，30.655s。
- `.venv/bin/python -m multi_agent_manager.wait_compat`：live 行为探测 PASS；只读验证 `/root/.codex/app-server-control/app-server-control.sock` 与 `/root/.codex/app-server-control/app-server.log`，并验证一次 fresh trace 绑定。
- `bash -n scripts/install_and_test.sh` 与 `git diff --check`：通过。开发期间未执行 `pipx install`、未重启 live App，也未保留临时进程或文件。

## 交付位置

- Workspace: `/mnt/public/xcj/Projects/workspace/5b3fe28b-3d9c-444f-bf24-889b2453558c/multi-agent-manager`
- Branch: `task/5b3fe28b-3d9c-444f-bf24-889b2453558c`
- Commit: `e20da6d52525267e035549c3447fbd6d3409df27` (`Add behavioral wait compatibility checks`)

## 未认证范围

自检明确把 `native_message_wake` 标记为 `not-certified`。它不会宣称已经验证用户消息或 native manager-send 对真实 MAM wait 的端到端唤醒；这需要 Manager 协调真实线程试验。runtime 可按最新的 current-state pending-work 语义调用本接口，接口本身不保存或引入 replay/cursor 状态。
