# MAM proactive wake runtime — final integration follow-up

实施 worktree：`/mnt/public/xcj/Projects/workspace/bc998553-c309-4734-b625-429a27f09a3b/multi-agent-manager`；分支：`task/bc998553-c309-4734-b625-429a27f09a3b`。本分支已合并最终集成基线 `555f6ff`（含 integration `20ff584` 与此前 runtime 阻断修复）。

供 Manager 按顺序 cherry-pick 的新增提交：

- `23f9024` `fix: launch wake daemon from caller runtime`
- `9ee6300` `feat: restore optional mam wait`

## daemon 代码来源隔离

`_spawn_service()` 不再以 `MAM_ROOT` cwd 的 `python -m multi_agent_manager.wake_runtime` 选取代码。它以 `-I -S -c` 的小 bootstrap 运行，并把当前调用方已解析的 `wake_runtime.__file__` 包父目录置于导入路径首位；子进程同时移除继承的 `PYTHONPATH`。`MAM_ROOT` 仍只承担状态和日志 cwd，独立状态 worktree 中的旧、缺失或同名包不会覆盖当前安装或 source-checkout 调用方。

回归使用故意放入 `MAM_ROOT/multi_agent_manager/` 的 shadow runtime：真实 detached daemon 仍到达 `awaiting_manager` ready 状态、正常 stop，shadow sentinel 未生成。另一个子进程以 `-I -S` 手工加入 source root、cwd 设为 `MAM_ROOT` 且污染 `PYTHONPATH`，验证未 editable/install 的 source 调用同样启动正确 daemon。两者均无 Manager，未连接真实 App Server 或发起模型调用。

## 可选 `mam wait` 恢复与主动服务共存

从 `main` 的 `3302520` 恢复了稳定的 wait 存储、CLI、runtime 和回归：`mam wait`、`mam wait list`、`mam wait stop --agent`、`mam wait stop manager`，包括固定一小时、当前 turn/身份选择、立即待办返回、手动 stop、原生输入取消和可见兼容性失败。`cli.py` 同时保留 proactive 的 service 命令与首次 Manager 绑定逻辑。

主动 scheduler 在待投递 recipient 已有 wait 登记时保留 durable event；在最终 `turn/start` 前再次以同一 agent 的 wait 锁检查，防止 preflight 期间新登记的 wait 与新 turn 并行。无法核验 wait 身份也保守保留事件。wait 返回后，task/job 已归档会使旧事件失效而不产生冗余唤醒。

`wait_compat.py`、其测试和 installer 仍完全由 installer task 所有；本次未修改这些文件。合并时 installer 应按已发布合同恢复该模块及其安装/兼容性覆盖。

设计文档已同步默认主动跟进、可选 wait 的边界和锁定语义。

## 验证

```text
.venv/bin/python -B -m unittest -v tests.test_wake_runtime
# 36 passed
.venv/bin/python -B -m unittest -v tests.test_wait_runtime
# 38 passed
.venv/bin/python -B -m unittest -v tests.test_task
# 34 passed
.venv/bin/python -B -m unittest discover -s tests -q
# 153 passed
.venv/bin/python -B -m py_compile multi_agent_manager/cli.py multi_agent_manager/wait_runtime.py multi_agent_manager/wake_runtime.py tests/test_task.py tests/test_wait_runtime.py tests/test_wake_runtime.py
# passed
git diff --check
# passed
```

新增调度回归覆盖已登记 wait 阻止 stopped-job 投递、wait 返回后任务归档不再唤醒，以及 wait 在 delivery preflight 后才登记时最终边界仍阻止 `turn/start`。未进行全局安装、生产 daemon 操作、真实 App Server/model 调用或 GPU 作业；未改 installer、README 或 AGENTS。
