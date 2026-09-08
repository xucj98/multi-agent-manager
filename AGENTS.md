# MAM agent 入口

MAM 管理本集群的 subagent 任务、workspace 和长进程。按当前操作阅读对应说明：

- 派发或验收 subagent 前，阅读[任务管理](README.md#任务管理)。Manager 自己的工作无需创建 task。
- 接到任务后，先用 `mam task show <uuid>` 读取发布要求，再阅读[执行与交付](README.md#执行与交付)及任务涉及库的 AGENTS.md。
- 修改代码或独立 review 前，按[工作区说明](README.md#工作区)创建或复用本任务的 worktree。
- 启动预计超过 1 小时的程序（如正式数据生成、训练、评估）时，用 `mam job add` 登记，并按[进程管理](README.md#进程管理)收尾；通常的短 smoke 无需登记。
- 修改 MAM 实现时，阅读[开发验证](README.md#开发验证)。
