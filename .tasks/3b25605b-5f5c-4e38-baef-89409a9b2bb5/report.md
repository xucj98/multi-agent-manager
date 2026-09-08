task_revision: f6790c09c64e73eeb229b247e5ca65644d476e1a

# 空白独立验收简报

完成：已在本任务独立 workspace 创建并登记两个 worktree，未复用作者 workspace。

- `agent-workflow`：`/mnt/public/xcj/Projects/workspace/3b25605b-5f5c-4e38-baef-89409a9b2bb5/agent-workflow`，分支 `task/3b25605b-5f5c-4e38-baef-89409a9b2bb5`，HEAD `48d188b0da406c150e07033e61235095bcc1e06f`。私有 venv 为 Python 3.10.19，stdlib smoke、CLI help 与 show 可用。该库的固定入口只创建私有 venv，非可编辑业务包，也没有需要归属检查的共享数据软链接。
- `robot-bridge`：同 UUID 下 `robot-bridge`，同名分支，HEAD `0095a3f4b2830ef9cc09cd77befff199e4391eba`。私有 venv 为 Python 3.11.14；`scripts/worktree_env_smoke.py` 通过。`importlib.metadata` 显示 `robot-bridge 0.1.0` 的 `direct_url.json` 为该 worktree 的 editable 安装；`.local`、`logs`、`eval_result` 分别软链接到稳定源库的受管实体。
- 管理库 worktree 执行 `.venv/bin/python -B -m unittest discover -s tests -v`：19 项通过、无跳过，包含真实临时 Git fixture 的发布并发/暂存保留、版本与 review 固定、两库归档共享软链接保留、dirty/失败重试与 job 记录测试。源码审阅固定 `48d188b` 的 `scripts/task.py`、`scripts/job_runtime.py` 及对应测试。
- 本机管理 CLI 完成 help/show；本机与 SSH `wuwen-1` 的 robot mock CPU e2e 均正常完成 5 次 scheduler 迭代。当前运行边界下，管理 CLI 不在 `wuwen-1` 安装或运行；远端仅作为 SSH 执行/查询目标。未使用 GPU。
- 真实 job 闭环：由本机 CLI 登记和查询的本机 job `6ae0e1ae-f002-4030-a527-8e26e5c9a886` 与显式 `host=wuwen-1` job `4a007e8e-35bf-4dd7-aacd-7019948750be` 均观测 `running → stopped → archived`；现有 App Server 对本 agent 返回 `active`。测试进程、6 个 mock 日志和本轮 pycache 已清理。
- 文档审阅：实际读取 current main 的 `AGENTS.md`、`README.md` 和接口说明，三者最后修改 commit 均为 `b4701c955b1ecf4898508a43c8e2177b4afb0f94`。它们明确所有 agent、代码修改和管理 CLI 均在本机运行，远端仅经 SSH 执行/查询 GPU 作业；`.worklogs` 已由 `08d0bb14ceb786539857776d4751af49241bd28c` 删除并统一改用 `.tasks/`。robot-bridge、RMBench、OpenDM、openpi 的固定 AGENTS 和环境入口均按任务路由阅读，不引用公共任务管理或集中日志路径，环境入口明确只创建环境、不自动启动实验/GPU；各业务 README 仍保留各自项目操作说明。RMBench/OpenDM 的历史 `.worklogs` 页面未被入口文档引用，不构成当前任务登记入口。

限制与未覆盖：

- 跨主机运行管理 CLI 后再以 `localhost`/`local` 读取共享登记，会按读取端本机解释该别名。此前的自建 `wuwen-1` `sleep 90` 复现已记录并清理；按最新任务定义，这种跨主机 CLI 用法不受支持，不据此扩大实现或阻塞验收。受支持路径是本机 CLI 对远端作业显式登记 `--host wuwen-1`，该路径已完成真实闭环验证。
- 按任务要求保留本 UUID 的两个 worktree 待 Manager 最终归档，未对真实工作区执行 archive；完整套件中的自清理 Git fixture 覆盖多库删除、共享目标保留、dirty/活跃进程保护和失败重试，但最终 Manager archive 仍需现场核对。
- MAM/pipx 的名称与安装方式仍在讨论，不属于本次验收或改动范围。

workspace：`/mnt/public/xcj/Projects/workspace/3b25605b-5f5c-4e38-baef-89409a9b2bb5`。

交付：无代码或文档修改；成果为本已发布独立验收简报。两库完整 HEAD 如上。

验证：上述命令均在 CPU 上执行；未操作现有正式实验、数据实体或 GPU。

结论：按最新任务运行边界，已验证范围通过，无已确认阻塞。
