# MAM 后续开发规划

讨论稿，按以下顺序推进。

| 顺序 | 任务 | 要做什么 |
| --- | --- | --- |
| 1 | [附件提交与任务归档](commands/task.md#附件与归档) | 先提供附件提交及 workspace 内的 `.task` 入口，再完善成果留存检查和归档清理；作为同一项工作交付。 |
| 2 | [执行者开始与接续](commands/task.md#待开发) | 用 task start 统一登记、返工和接手；自动识别身份，支持协作路径与当前任务定位，workspace 和分支仍按 TASK-ID 命名。 |
| 3 | [Manager 接管](commands/service.md#manager-接管) | 让新的 Manager session 接管当前实例，继续处理已有任务和待办。 |
| 4 | [job 提交](commands/job.md#待开发) | 用 `mam job submit --command` 一次完成登记与启动，返回 JOB-ID。 |
| 5 | [跨集群同步](commands/workspace.md#跨集群同步) | 同步任务的 worktree 和指定文件，支持远端运行及结果取回。 |
| 6 | [GPU 排队](commands/job.md#待开发) | 为 job 指定 GPU 数量、空闲显存和平均利用率条件，在当前实例内排队启动。 |
| 7 | [消息与状态输出](commands/service.md#消息与状态输出) | 明确 Manager 转发 job 停止消息的动作，减少重复唤醒和输出；沿用降级路径，不维护 Codex fork。 |
| 8 | [执行者向 Manager 发消息](commands/service.md#执行者主动发消息) | 自动识别发送者，默认发送给当前实例 Manager，并能唤醒 idle Manager；TASK-ID 可选。 |
| 9 | Token 用量与优化 | 按用途统计 cache input、no-cache input、output 和费用，区分 272k 上下文价格；减少无效轮询、空操作和重复读取，比较优化前后的用量。 |
