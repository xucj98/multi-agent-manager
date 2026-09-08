task_revision: 38073292eb672242a668adf52f18483a19c0669b

完成：实现 `probe_process` 与 `probe_agents` 的只读运行时查询模块，并覆盖本地 `/proc`、受控 SSH、App Server Unix WebSocket 握手和 JSON-RPC `thread/read(includeTurns=false)` 查询。进程身份记录 host、boot_id 和 start_ticks；PID 身份变化、目标不存在和 zombie 均返回 stopped，访问失败返回 unknown。远端固定 Python 查询先以 `kill(pid, 0)` 确认 PID，再读取 `/proc/<pid>/stat`，将不存在与存在但不可读分别映射为 stopped 和 unknown。App Server 查询复用单个连接，按线程区分 RPC 错误、传输错误与超时。

未完成：无。管理 CLI 尚未集成到稳定管理库，本报告作为共享目录草稿，待工具可用后按流程发布。

workspace：`/mnt/public/xcj/Projects/workspace/91ba98dd-3356-493a-98e9-a5e9ea94f04b`

交付代码库：`agent-workflow`，分支 `task/91ba98dd-3356-493a-98e9-a5e9ea94f04b`，提交 `d408bda1d06d96337bf4058208d77f1c5397352d`（包含前序提交 `19cec0d149ee91e0afebb08ed44622a5d4da3f43`）。

验证：`python -m unittest discover -s tests -v` 通过（7 项）；覆盖本地进程 running→stopped、身份不匹配、zombie、SSH 超时/主机注入拦截、远端不存在与不可读的状态区分，以及 socket fixture 的握手、批量查询、ping、分帧、RPC 错误、notLoaded 与超时。真实 smoke 已验证两个由本任务创建的 `wuwen-1` 进程 running→stopped，SSH 不可达返回 unknown；现有 App Server 对本执行者 `01a08160-52bc-70e1-81a6-9af5125ea787` 和 Ptolemy `01a080d9-44a2-77f3-a185-737341387aaa` 的只读查询均返回 active。所有测试进程、socket fixture 和字节码产物已清理；未使用 GPU。

成果位置：`scripts/job_runtime.py`、`tests/test_job_runtime.py`，均位于上述 workspace 的 `agent-workflow` worktree。
