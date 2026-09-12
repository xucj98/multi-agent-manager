# 主动唤醒安装与可选 wait：最终组合验证

实施 worktree：`/mnt/public/xcj/Projects/workspace/e7183b34-6d86-4394-ada8-675f54b56c42/multi-agent-manager`，分支：`task/e7183b34-6d86-4394-ada8-675f54b56c42`。

## 交付

- `8ad4220 fix: test clean checkout source imports`：安装器在 pipx 安装前的 checkout 测试子进程中将当前 checkout 置于 `PYTHONPATH` 首位。回归使用无 editable install、含旧 site-packages 包和独立 `MAM_ROOT` cwd 的解释器，确认 detached daemon 从当前源码 ready/stop，未执行旧包。
- `fa530a0 fix: preserve wait compatibility during wake install`：恢复与 `3302520` 字节一致的 `wait_compat.py` 及其 32 项测试；安装器保留持久 trace 设置、已验证 listener 的精确 `yes` 重启/恢复路径和 PATH 设置。wait compatibility 在 wake compatibility、liveprobe 与 service replacement 前执行，失败会阻止后续替换；安装文档恢复 `mam wait`、`mam wait list`、`mam wait stop manager`、`mam wait stop --agent` 的说明。
- Runtime 所有者交付已组合为 `b7d2c57`（源代码隔离，对应 `23f9024`）和 `5ecde14`（可选 wait 恢复，对应 `9ee6300`）：包含 CLI、wait storage/runtime/tests，以及 daemon 在最终 `turn/start` 前对同 agent active wait 的锁保护。未手改 Runtime 所有权文件。

## 验证

```text
.venv/bin/python -B -m unittest discover -s tests -q
187 tests, OK (74.366s)

bash -n scripts/install.sh
git diff --check
git diff --cached --check
py_compile（wait/wake runtime、compat 和对应测试）
all passed
```

全量 suite 包含 wait compatibility 的 trace、通知、手动 stop、message cancellation 与重启恢复回归；可选 wait CLI/storage/runtime 和 active-wait delivery guard；wake compatibility/liveprobe 单元和 installer 顺序/失败门禁；以及 clean-checkout detached-daemon source-import setup 回归。

## 限制与清理

本轮未运行额外六 turn 模型 liveprobe，未做全局安装，未触碰生产 App Server、service、任务、线程或 GPU。最终生产安装仍会按安装器的一键验收执行实际 liveprobe。

已清理本 worktree 验证生成的 `multi_agent_manager/__pycache__` 与 `tests/__pycache__`；无未跟踪 fixture 或未提交改动。
