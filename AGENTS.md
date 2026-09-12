# MAM agent 入口

MAM 管理本集群的 subagent 任务、workspace 和长进程。按当前操作阅读对应说明：

- 开始任务前阅读[核心原则](README.md#核心原则)和本集群的信息[本地说明](.local/README.md)。
- 派发或验收 subagent 前，阅读[任务管理](README.md#任务管理)。Manager 自己的工作无需创建 task。
- 接到任务后，用 prompt 中的 TASK-ID 按[执行与交付](README.md#执行与交付)查询任务和发布要求，创建独立 worktree，再阅读任务涉及库的 AGENTS.md。
- 启动预计超过 1 小时的程序（如正式数据生成、训练、评估）时，用 `mam job add` 登记，并按[进程管理](README.md#进程管理)收尾；通常的短 smoke 无需登记。
- 当前可执行的工作处理完后，正常结束 turn；MAM 按[自动跟进](README.md#自动跟进)唤醒负责人。需要在当前 turn 等待时，可用[可选等待](README.md#可选等待)。
- 开发 MAM 请先阅读 [MAM 开发指南](docs/development.md) 和 [MAM 设计细节](docs/task-management-design.zh-CN.md)。
