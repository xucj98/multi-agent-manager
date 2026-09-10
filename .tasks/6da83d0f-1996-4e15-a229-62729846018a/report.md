# 交付简报

代码交付：`963f619f2356822ce628682cdb073f4a46417582`（`task/6da83d0f-1996-4e15-a229-62729846018a`）

完成内容：

- 增加 `mam wait stop manager`。它只从当前未归档 task 未绑定的有效等待中选择唯一目标；零个、多个或身份无法确认都会明确报错。`--task` 仅作为监控过滤，不参与绑定判断；保留 `mam wait stop --agent AGENT-ID`，且两种目标必须二选一。
- manager 模式复用现有 agent 锁、PID、identity 与 token。选中后重新核对记录；原等待结束或被替换时返回 `not_waiting`，不会取消替换后的等待，也不会向被监控 job 发信号或归档 job。
- `scripts/create_worktree.sh` 在源 MAM 根存在 `.local/README.md` 时，只在新 worktree 建立该单文件软链接；源文件缺失或目标冲突时继续创建且不覆盖。归档只认可这个精确、目录内唯一的受控链接，未知 `.local` 内容仍会拒绝归档。
- 更新任务管理设计文档和测试；未修改 Manager 维护的 `README.md`。

改动文件：

- `multi_agent_manager/cli.py`
- `scripts/create_worktree.sh`
- `tests/test_task.py`
- `docs/task-management-design.zh-CN.md`

验证：

- `.venv/bin/python -B -m unittest discover -s tests -v`：41 项通过。
- 真实本地短进程 smoke：`mam wait stop manager` 在 2 秒内返回；对应等待被取消，绑定执行者等待和被监控 job 保持运行。
- 集成测试覆盖两个项目配置隔离、唯一/零/多候选、绑定排除、身份未知、结束与替换竞态，以及本地 README 的链接、缺失、冲突和归档保护。

限制：manager 模式只使用当前 MAM 根的本地 wait/task 记录，不查询外部 agent，也不管理 job 生命周期。

成果位置：`/mnt/public/xcj/Projects/workspace/6da83d0f-1996-4e15-a229-62729846018a/multi-agent-manager`
