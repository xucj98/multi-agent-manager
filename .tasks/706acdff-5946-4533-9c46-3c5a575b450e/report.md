task_revision: 6da327722bf9e5834aebbd0475d554de6fdc3479

完成与未完成：
- 已按 review `8ecd5775172717b4c39b905f2bf2891a95e65c07` 和最新裁定修复两项：每个 target 前检查 deadline，probe timeout 受剩余预算约束；attention 的 needs_verification 全部明确显示 unknown/待核实，包含 stopped job + agent unknown。
- 完成 `mam wait jobs/list/stop`：以 `CODEX_THREAD_ID` 自动识别等待者，支持显式覆盖、超时、空集、已停止、取消、陈旧登记清理和每 agent 单活跃等待。
- 完成 task/job/wait 三类表格输出、`job status <job-id>` 的单 job 实时 JSON 查询，以及真实进程启动时间记录与 unknown/待核实显示。
- 更新 README 和 `docs/task-management-design.zh-CN.md`；未修改 AGENTS、真实 job、系统安装或 GPU 配置，也未派发 agent。
- 未完成项：无。

workspace、各库交付 commit：
- `/mnt/public/xcj/Projects/workspace/706acdff-5946-4533-9c46-3c5a575b450e/multi-agent-manager`
- `multi-agent-manager`：`e6892fe7d9d29be71f03d69a5c32318706207090` (`Fix per-target wait deadlines and attention uncertainty`)，在原交付 `1b8f4265dde093736dff2e0d77d185d9e640a6a8` 上增量提交，原 worktree 保留且干净。

变更文件：
- `multi_agent_manager/cli.py`、`multi_agent_manager/job_runtime.py`
- `tests/test_task.py`
- `README.md`、`docs/task-management-design.zh-CN.md`

验证结果与成果位置：
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest discover -s tests -v`：32 项通过（19.668 秒）。新增受控时钟、多远端 target 回归验证 0.01 秒和 0.75 秒总预算，耗尽后不探测后续 target；CLI 入口回归验证 stopped job + 未绑定/不可用 agent 的六列表格明确待核实。原有临时 root、短进程和并发取消测试全部通过。
- `git diff --check`、语法编译和 CLI help 检查通过；临时 root、测试进程和项目 `__pycache__` 已清理。

剩余限制与取舍：
- 等待使用 `.local/waits` 的文件锁、PID 启动身份和 token，不引入 daemon、数据库或调度框架；远端等待探测限制为 0.5 秒，保证 stop 不会被长 SSH 查询无限阻塞。
- 原实现生产代码净增约 336 行已获 Manager 接受，本轮修复净增 8 行，不扩框架、不新增依赖、不安装、不修改真实 job。
- deadline 允许小幅运行时调度开销，并非硬实时保证。本轮远端预算使用受控探测回归；正常远端可用性沿用独立 review 的 wuwen-1 0.5 秒探测 12/12 通过证据，未重复运行远端实验。
