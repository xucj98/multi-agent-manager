# MAM agent 入口

MAM 是 multi-agent 项目管理工具，使用者包括 manager 和 subagent。按当前操作阅读对应说明：

- 开始任务前阅读[核心原则](README.md#核心原则)和本项目具体信息[项目说明](.local/README.md)。
- manager 派发或验收前，阅读[任务管理](README.md#任务管理)。
- subagent 接到任务后，按[执行与交付](README.md#执行与交付)登记、读取已发布要求并创建独立 worktree，再阅读任务涉及库的 AGENTS.md。
- 启动预计超过 30 分钟的程序（如正式数据生成、训练、评估、传输拷贝）时，按[进程管理](README.md#进程管理)登记，结束后归档。
- 任务报告、验收和收尾见[执行与交付](README.md#执行与交付)。
- 当前可执行的工作处理完后，正常结束 turn；MAM 按[自动唤醒](README.md#自动唤醒)唤醒负责人。
- 开发 MAM（包括修改 MAM 文档）请阅读 [MAM 开发指南](docs/development.md)。
