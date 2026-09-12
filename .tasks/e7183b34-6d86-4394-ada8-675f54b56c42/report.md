# 主动唤醒安装与可选 wait：d51 修复后的组合候选

实施 worktree：`/mnt/public/xcj/Projects/workspace/e7183b34-6d86-4394-ada8-675f54b56c42/multi-agent-manager`，分支：`task/e7183b34-6d86-4394-ada8-675f54b56c42`。

## d51 blocker 修复

新提交 `e7b3f57 fix: preserve unmarked shell trace settings` 将 `update_bashrc()` 的所有权边界收紧为完整且逐行完全匹配的 MAM 标记块：

- marker 外的内容不再按 `RUST_LOG` 或 `LOG_FORMAT` 文本过滤。用户未标记的 export、条件块和其他 shell 内容保持原样。
- 只有恰好一对 marker 且内容等于安装器当前完整 block 时才会替换为 canonical block；不完整、多个或内容未知的 marker 块会明确非零退出，原 `.bashrc` 不写回。
- 新回归复现 d51 的条件块：两个相同 export 保持在条件内，输出经 `bash -n`，第二次运行字节一致且不新增 backup。另有未知完整 marker 与 installer 门禁回归，验证不改写该文件且不会调用 service。

## 组合交付

- `8ad4220`：clean-checkout 测试的源码导入路径。
- `fa530a0`：wait compatibility、trace setup、PATH 与 installer 门禁恢复。
- `b7d2c57`（Runtime `23f9024`）：detached daemon 固定从调用方 runtime 导入。
- `5ecde14`（Runtime `9ee6300`）：可选 `mam wait` CLI/storage/runtime 与 active-wait delivery guard。
- `e7b3f57`：本次仅限 shell 配置所有权的修复。

## 验证

```text
.venv/bin/python -B -m unittest discover -s tests -p 'test_wait_compat.py' -v
33 tests, OK

.venv/bin/python -B -m unittest discover -s tests -p 'test_wake_compat.py' -q
26 tests, OK

.venv/bin/python -B -m unittest discover -s tests -q
188 tests, OK (73.920s)

bash -n scripts/install.sh
git diff --check
py_compile（修改的测试）
all passed
```

本轮未运行额外六 turn liveprobe，未做全局安装，也未触碰生产 App Server、service、任务、线程或 GPU。候选已准备接受独立的 d51 targeted recheck。
