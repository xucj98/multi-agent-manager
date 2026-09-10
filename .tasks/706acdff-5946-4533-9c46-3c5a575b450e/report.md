task_revision: 9f56caad79d2bb55a5ecb16829dfe60301456d9c

完成与未完成：
- 完成 `mam wait jobs/list/stop`：以 `CODEX_THREAD_ID` 自动识别等待者，支持显式覆盖、超时、空集、已停止、取消、陈旧登记清理和每 agent 单活跃等待。
- 完成 task/job/wait 三类表格输出、`job status <job-id>` 的单 job 实时 JSON 查询，以及真实进程启动时间记录与 unknown/待核实显示。
- 更新 README 和 `docs/task-management-design.zh-CN.md`；未修改 AGENTS、真实 job、系统安装或 GPU 配置，也未派发 agent。
- 未完成项：无。

workspace、各库交付 commit：
- `/mnt/public/xcj/Projects/workspace/706acdff-5946-4533-9c46-3c5a575b450e/multi-agent-manager`
- `multi-agent-manager`：`1b8f4265dde093736dff2e0d77d185d9e640a6a8` (`Add stoppable job waits and list details`)

变更文件：
- `multi_agent_manager/cli.py`、`multi_agent_manager/job_runtime.py`
- `tests/test_task.py`
- `README.md`、`docs/task-management-design.zh-CN.md`

验证结果与成果位置：
- `.venv/bin/python -B -m unittest discover -s tests -v`：30 项通过；测试使用临时 root 和短 sleep，覆盖表头/单行/筛选/详情、停止不影响被监控进程、双等待者隔离、重复等待、超时、空集、已停止、unknown 与陈旧登记。
- `git diff --check`、语法编译和 CLI help 检查通过；临时 root、测试进程和项目 `__pycache__` 已清理。

剩余限制与取舍：
- 等待使用 `.local/waits` 的文件锁、PID 启动身份和 token，不引入 daemon、数据库或调度框架；远端等待探测限制为 0.5 秒，保证 stop 不会被长 SSH 查询无限阻塞。
- 为同时实现并发取消防串扰、陈旧清理、短超时远端探测、实际启动时间和新接口测试，生产代码 diff 为新增约 361 行、删除 25 行（净增约 336 行），略超过约 300 行的规模提示；未新增第三方依赖或独立框架。
