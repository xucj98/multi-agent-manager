# Clean-clone 安装回归独立复核：PASS

候选：`061eadcf38b45c10477a0268823308e1abb450f2`（新增源提交：`a2cb5ce2e810ffda283f40531a4d5c7a2db0d71e`）。

审阅 workspace：`/mnt/public/xcj/Projects/workspace/9128f418-33c6-4aa3-a684-8aafde0ecfb9/multi-agent-manager`。

本轮仅复核相对已接受 `e4bc982` 的三文件 clean-clone 修复：`scripts/install.sh`、`tests/test_task.py`、`tests/test_wake_compat.py`。

结论：通过，无新 blocker。

- 源码 suite 的 CLI 子进程不再依赖 `Path(sys.executable).with_name("mam")`。它以 `-I -S -B` 启动选定解释器，并显式将 checkout 根置于导入路径首位；因此不会使用相邻 console script、site-package 或继承的 `PYTHONPATH` shadow package。保留的实际安装测试仍覆盖安装后的 `bin/mam`。
- `run_tests()` 仅在其测试子 shell 中 `unset MAM_SERVICE_MANAGER`。测试返回后外层变量保留，后续 `validate_explicit_manager` 仍读取该原值并将其传给实际 `service start --manager` 路径。没有改变接口、pipx 前失败门禁或生产生命周期。
- 新回归覆盖无相邻 `mam`/shadow import、预 pipx suite 不接收 Manager 控制变量，以及 fixture 的最终 service-start 明确使用该变量。差异未增加 skip 或跳过检查。

独立复现使用一个新的本地 Git clean clone（无 `.venv`），将父环境设置为：

```text
SOURCE_PYTHON=/root/miniconda3/bin/python3
MAM_SERVICE_MANAGER=01a081fe-d6c2-74f2-a73d-68584e9d915b
PYTHONPATH=<会抛异常的临时 multi_agent_manager shadow package>
```

在 clone 中仅 `source scripts/install.sh`，显式设置 `CHECKOUT_ROOT` 与 `SOURCE_PYTHON` 后调用 `run_tests`，未调用 `main`。`/root/miniconda3/bin/mam` 不存在；suite 后外层 Manager 值仍为原值。结果：

```text
Ran 191 tests in 61.622s
OK
manager_preserved=01a081fe-d6c2-74f2-a73d-68584e9d915b

bash -n scripts/install.sh
git diff --check e4bc982..061eadc
```

上述检查均通过。未运行 installer main、pipx、liveprobe 或模型调用，未写生产 shell，也未触及生产 App Server、service、任务、线程、机器人或 GPU。临时 clone/shadow fixture 自动清理；review worktree 无未提交改动和非 `.venv` Python 缓存。
