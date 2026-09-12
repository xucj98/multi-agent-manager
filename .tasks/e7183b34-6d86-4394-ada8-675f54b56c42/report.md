# 主动唤醒安装与可选 wait：最终组合候选

实施 worktree：`/mnt/public/xcj/Projects/workspace/e7183b34-6d86-4394-ada8-675f54b56c42/multi-agent-manager`；分支：`task/e7183b34-6d86-4394-ada8-675f54b56c42`。

## 本次 clean-clone 安装修复

新提交 `a2cb5ce fix: run clean clone tests before pipx install` 修复了真实安装在 pipx 之前的两项阻断：

- `tests/test_task.py` 的 CLI 子进程改为通过所选 Python 的隔离模块启动器显式把当前 checkout 放在 `sys.path` 首位。它不再假定 `sys.executable` 同目录存在 `mam`，也不会误用旧 pipx/site-package 或 `PYTHONPATH` 中的同名包；回归测试使用无相邻 launcher 的 Python 和恶意 shadow 包验证这一点。
- `scripts/install.sh` 仅在 checkout 测试的子 shell 中清除 `MAM_SERVICE_MANAGER`。这样真实安装传入的 Manager 选择不会污染安装夹具断言，测试结束后外层变量仍可用于最终 `mam service start --manager`。
- installer 测试夹具默认剥离继承的 Manager 值，同时保留每个测试显式传入值的能力；覆盖了继承变量、实际 pre-pipx test phase 和显式 Manager 服务启动三种情况。

组合候选还包含已提交的 `8ad4220`（clean-checkout daemon 源码导入）、`fa530a0`（wait compatibility/trace/PATH 安装门禁）、`b7d2c57`（Runtime daemon 导入）、`5ecde14`（可选 `mam wait` 及 active-wait guard）和 `e7b3f57`（仅替换完整已知 MAM shell block，保留未标记用户配置）。

## 验证

```text
.venv/bin/python -B -m unittest discover -s tests -p 'test_task.py' -q
35 tests, OK

.venv/bin/python -B -m unittest discover -s tests -p 'test_wake_compat.py' -q
28 tests, OK

# 安装器实际 pre-pipx run_tests 路径：
# /root/miniconda3/bin/python3 无相邻 mam，外层设置 MAM_SERVICE_MANAGER。
CHECKOUT_ROOT=$PWD
source scripts/install.sh
SOURCE_PYTHON=/root/miniconda3/bin/python3
run_tests
191 tests, OK (59.702s)

bash -n scripts/install.sh
git diff --check / git show --check
passed
```

最后一项复现了原始失败的同一系统 Python、无 launcher 与 Manager 环境，但没有调用 `main`，因此未执行 pipx、全局安装、服务替换或 liveprobe。未重复六 turn liveprobe，也未触碰生产 App Server、service、任务、线程或 GPU。已清理本 worktree 生成的源码/测试 Python 缓存；生产安装仍保持原状，交由 Manager 继续验收和执行。
