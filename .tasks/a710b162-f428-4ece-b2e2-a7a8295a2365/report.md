# 自动唤醒 prompt 来源标记

实施 worktree：`/mnt/public/xcj/Projects/workspace/a710b162-f428-4ece-b2e2-a7a8295a2365/multi-agent-manager`；分支：`task/a710b162-f428-4ece-b2e2-a7a8295a2365`。

交付提交：`21e27c7 feat: label automated wake prompts`。

- `WakeScheduler._payload()` 对每个非空 daemon 投递 payload 仅在首行加入字面 `[MAM Message]`，随后保留原有 actionable 内容和批量换行。它覆盖 `job_stopped`、`task_ready` 与 `task_unbound`，不改事件签名、路由、去重或状态记录。
- 更新 liveprobe 的本地验收文本检查，要求 Manager-ready 和 stopped-job scheduler delivery 含同一标记；更新设计说明。
- 未修改 `wait` 或人类消息处理路径。新增批量 formatter 回归，精确覆盖两条 stopped-job、两条 task-ready 和 unbound 内容，确认 label 只出现一次且在第一行；现有 scheduler 路由测试确认实际 job 和 Manager 投递均以该行开头。

验证：

```text
.venv/bin/python -B -m unittest discover -s tests -p 'test_wake_runtime.py' -v
37 tests, OK

.venv/bin/python -B -m unittest discover -s tests -p 'test_liveprobe.py' -v
7 tests, OK

.venv/bin/python -B -m unittest discover -s tests -p 'test_wait_runtime.py' -q
38 tests, OK

Python 3.10 py_compile、bash-free git diff --check / git show --check
passed
```

未运行 live model probe，未做全局安装，也未操作生产 App Server、service、任务、线程或 GPU。已清理本 worktree 的源码和测试 Python 缓存。
