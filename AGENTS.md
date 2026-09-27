# MAM agent 入口

MAM 管理本集群的 subagent 任务、workspace 和长进程。按当前操作阅读对应说明：

- 开始任务前阅读[核心原则](README.md#核心原则)和本集群的信息[本地说明](.local/README.md)。
- 派发或验收 subagent 前，阅读[任务管理](README.md#任务管理)。Manager 的项目管理工作无需创建 task。
- 接到任务后，用 prompt 中的 TASK-ID 按[执行与交付](README.md#执行与交付)自登记、读取已发布要求并创建独立 worktree，再阅读任务涉及库的 AGENTS.md。
- 启动预计超过 30 分钟的程序（如正式数据生成、训练、评估、传输拷贝）时，用 `mam job add` 登记，并按[进程管理](README.md#进程管理)收尾；通常的短 smoke 无需登记。
- 交付、验收和归档按[任务收尾](README.md#任务收尾)完成。
- 当前可执行的工作处理完后，正常结束 turn；MAM 按[自动唤醒](README.md#自动唤醒)唤醒负责人。
- 开发 MAM 请先阅读 [MAM 开发指南](docs/development.md)，再按 [MAM 接口说明](README.md#mam-接口说明) 阅读相关命令。修改 MAM 文档，如 `README.md`，也属于开发MAM。
