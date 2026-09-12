# 最终组合候选复核更新：阻断于 daemon 代码来源

## 当前结论

不批准最终候选 `20ff584fd4e79807a4ba926742b7e263513abffc`。我在既有独立 reviewer worktree 中将其合并为 `f694c88a7b65602efcf12da463202feddd8264b4`；此前 runtime 三项状态转换修复仍为通过，但安装/daemon 路径存在一个可复现的 clean-checkout 失败，以及同一根因导致的生产代码 shadow 风险。

## 阻断：`MAM_ROOT` 会覆盖已安装的当前 runtime

`wake_runtime._spawn_service` 用：

```text
sys.executable -m multi_agent_manager.wake_runtime ...
cwd=config.mam_root
```

运行 detached daemon。Python 的模块搜索会优先使用该 cwd。因此安装器支持的“当前代码 checkout 与同仓库的项目状态 worktree (`MAM_ROOT`) 不同”场景中，状态 worktree 里的旧 `multi_agent_manager` 会覆盖 pipx 刚安装的当前版本。旧状态 checkout 可以没有 `wake_runtime.py`，此时 daemon 直接无法导入；即使有旧模块，也可能运行错误版本。

这不是只影响测试。`scripts/install.sh` 的 `same_git_repository` 明确接受两个不同 worktree，随后 pipx launcher 的当前 `start_service` 正是通过上述 `_spawn_service` 启动子进程，因此会进入该搜索路径。

### 独立复现

1. 使用 Manager 指定的非 editable pipx 解释器运行当前候选的真实 daemon 生命周期单测：

```bash
/root/.local/share/pipx/venvs/multi-agent-manager/bin/python -B -m unittest -v \
  tests.test_wake_runtime.WakeRuntimeTests.test_fresh_daemon_process_confirms_readiness_and_stops_without_app_server_delivery
```

结果：5.055s 后 `ERROR`，`WakeRuntimeError: detached service did not signal verified startup readiness`。这独立确认了 Manager 的 107-pass/1-error clean-checkout 复现。

2. 在临时 `state-worktree/multi_agent_manager/wake_runtime.py` 写入仅输出 sentinel 的同名包，再从该目录运行当前解释器的同一 `-m` 形式。普通调用输出 `SHADOWED_FROM_MAM_ROOT`，证明 cwd 的包被选中；隔离导入调用不输出 sentinel 而加载安装的当前包。此复现不启动 daemon、App Server 或模型。

3. 本机旧 pipx 分发实际来自 `3302520`，其中没有 `multi_agent_manager.wake_runtime`；从该解释器隔离导入该模块得到 `ModuleNotFoundError`。这解释了生命周期测试的 readiness 超时，也表明真实旧 state checkout 会造成同类故障。

## 必要修复与回归要求

安装器所有者正在修 clean-checkout source-test setup；该改动还必须与 runtime owner/Manager 协调解决生产 child 的代码选择：daemon 必须从调用方的当前已安装 runtime 导入，而不能从 `MAM_ROOT` cwd 隐式导入。可采用隔离模块导入或其他显式、受信任的代码选择方式；仅加入 `PYTHONPATH` 不充分，因为 cwd 仍优先。

回归应同时覆盖：

- 无 `.venv`、无 editable 安装的源 checkout 测试及其 detached 子进程，确实执行当前 checkout；
- 当前安装代码与包含故意旧/缺失 `multi_agent_manager` 的同仓库状态 worktree 不同，daemon 仍由当前 runtime 启动并达到 verified readiness。

无需重跑 6-turn real liveprobe 来修这个 CPU/import 路径问题。修复后再运行完整组合 CPU suite，并重新检查 installer/liveprobe 的最终候选。

## 已完成且未受本阻断影响的审阅

`45614a60f63517eff3075381c697d370f09bdccc` 的 interruption recovery、unknown-source accepted-event 保留、明确 RPC rejection 分类均已独立复核通过。安装器已发布的真实隔离 receipt 显示 6/6 专用 fixture turns、两条准确 delivery、quiet-window 无重复和 fixture cleanup；本报告未重跑任何真实模型调用。该 receipt 不能弥补 daemon 从错误 worktree 导入的生产启动缺陷。

本轮未安装到全局、未启动或停止生产 service、未访问真实 App Server/thread、机器人或 GPU；临时复现目录和日志已清理。
