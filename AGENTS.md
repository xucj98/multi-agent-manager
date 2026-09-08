# MAM 协作约定

操作和运行位置见 [README.md](README.md)。

- Manager 为每个 subagent 创建任务、编辑并发布要求，再启动执行者并绑定 agent ID。每个 subagent 对应一个未归档任务及其 UUID workspace；Manager 自己的工作无需创建任务。
- 执行者先用 `mam task show` 读取发布要求和版本，再阅读涉及库的 `AGENTS.md` 及任务所需规范。追加要求由 Manager 写入任务、发布后通知执行者。
- 修改代码和独立代码 review 通过 `mam task workspace add` 创建各库 worktree。
- 管理仓库共享 checkout：Manager 编辑 task.md，执行者编辑自己的 report.md。main 是发布版本，工作目录改动是草稿；任务和简报通过 CLI 发布。
- 执行者按 README 的格式交付简报。review 使用固定版本的任务、简报和代码，在自己的 workspace 验证。
- 工作记录统一放在本库 `.tasks/`；各业务库保留自己的规范和实验记录。
- 执行者启动预计运行超过 1 小时的程序（如正式数据生成、训练、评估）时，使用 `mam job add` 登记进程；通常的短 smoke 无需登记。进程停止后，按任务要求处理结果并归档 job；Manager 查看待处理进程并通知已空闲的负责人继续工作。
- 临时文件和 smoke 由执行者按任务及所属库规范清理。Manager 决定任务结束后，通过 CLI 归档 workspace。

本工具使用 Python 标准库，代码修改须通过本库单元测试。修改删除操作时，验证共享软链接目标、未提交文件、未登记目录和运行进程得到保护。
