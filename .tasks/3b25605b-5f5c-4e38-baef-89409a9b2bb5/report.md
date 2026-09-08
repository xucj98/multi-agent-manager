task_revision: cf76e9cb743f48b283ba7496462094ff13b144e6

# 空白独立验收简报

完成：已在本任务独立 workspace 创建并登记两个 worktree，未复用作者 workspace。

- `agent-workflow`：`/mnt/public/xcj/Projects/workspace/3b25605b-5f5c-4e38-baef-89409a9b2bb5/agent-workflow`，分支 `task/3b25605b-5f5c-4e38-baef-89409a9b2bb5`，HEAD `48d188b0da406c150e07033e61235095bcc1e06f`。私有 venv 为 Python 3.10.19，stdlib smoke、CLI help 与 show 可用。该库的固定入口只创建私有 venv，非可编辑业务包，也没有需要归属检查的共享数据软链接。
- `robot-bridge`：同 UUID 下 `robot-bridge`，同名分支，HEAD `0095a3f4b2830ef9cc09cd77befff199e4391eba`。私有 venv 为 Python 3.11.14；`scripts/worktree_env_smoke.py` 通过。`importlib.metadata` 显示 `robot-bridge 0.1.0` 的 `direct_url.json` 为该 worktree 的 editable 安装；`.local`、`logs`、`eval_result` 分别软链接到稳定源库的受管实体。
- 管理库 worktree 执行 `.venv/bin/python -B -m unittest discover -s tests -v`：19 项通过、无跳过，包含真实临时 Git fixture 的发布并发/暂存保留、版本与 review 固定、两库归档共享软链接保留、dirty/失败重试与 job 记录测试。源码审阅固定 `48d188b` 的 `scripts/task.py`、`scripts/job_runtime.py` 及对应测试。
- 本机和 `wuwen-1` 用同一共享 venv 完成 CLI help/show；两端均执行 `RB_PY=.venv/bin/python bash scripts/tests/local/test_mock_e2e.sh`，mock policy、robot 与 scheduler 正常完成 5 次迭代。未使用 GPU。
- 真实 job 闭环：本机 job `6ae0e1ae-f002-4030-a527-8e26e5c9a886` 与 `wuwen-1` job `4a007e8e-35bf-4dd7-aacd-7019948750be` 均经 CLI 观测 `running → stopped → archived`；现有 App Server 对本 agent 返回 `active`。测试进程、6 个 mock 日志和本轮 pycache 已清理。
- 文档审阅：当前管理库 main 的删除提交 `08d0bb14ceb786539857776d4751af49241bd28c` 删除 `.worklogs` 的 6 个旧记录并将 README 改为统一使用 `.tasks/`；当前 AGENTS/README/接口文档相互一致。robot-bridge、RMBench、OpenDM、openpi 的固定 AGENTS 和环境入口均按任务路由阅读，不引用公共任务管理或集中日志路径，环境入口明确只创建环境、不自动启动实验/GPU；各业务 README 仍保留各自项目操作说明。RMBench/OpenDM 的历史 `.worklogs` 页面未被入口文档引用，不构成当前任务登记入口。

问题：

- P1（阻塞验收）跨主机读取会错误重解释 `localhost`/`local`。固定源码 `scripts/job_runtime.py` 的 `_is_local_host()` 将这两个字面量视为**查询端**本机。最小现场复现：在 `wuwen-1` 启动自建 `sleep 90`（PID `3911951`），从该机以 `--host localhost` 经 CLI 登记 job `f9b02458-bd40-48ff-a208-33476acb0d80`，初始为 `running`，identity boot ID 为 `5b39eb3b-f8e7-4be0-888e-ad0667682d15`。随后在本机读取同一共享记录，CLI 将它改成 `stopped` / `process not found`，而同时 `wuwen-1` 的 `ps` 仍确认该 PID 为 `/bin/sleep 90`。这可使仍在运行的远端进程被误判停止，并进一步允许错误的 job 或 task 归档。测试进程已终止且该 job 已归档。建议在 job add 时将 `localhost/local` 规范化为实际可路由主机，或把实际注册主机单独持久化并在后续 probe 使用；不能按读取端重新解释本机别名。修复后需在两机交叉读取重新验收。

未完成与限制：

- 因上述 P1，固定 `48d188b` 的集成成果不通过验收；本任务不修改实现，等待原作者修复后复验。
- 按任务要求保留本 UUID 的两个 worktree 待 Manager 最终归档，未对真实工作区执行 archive；完整套件中的自清理 Git fixture 覆盖多库删除、共享目标保留、dirty/活跃进程保护和失败重试，但最终 Manager archive 仍需现场核对。

workspace：`/mnt/public/xcj/Projects/workspace/3b25605b-5f5c-4e38-baef-89409a9b2bb5`。

交付：无代码或文档修改；成果为本已发布独立验收简报。两库完整 HEAD 如上。

验证：上述命令均在 CPU 上执行；未操作现有正式实验、数据实体或 GPU。
