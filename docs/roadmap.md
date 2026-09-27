# MAM 后续开发规划

已完成：附件提交与任务归档、执行者开始与接续、Manager 接管。后续按以下顺序推进。

| 顺序 | 任务 | 要做什么 |
| --- | --- | --- |
| 4 | [job 提交](commands/job.md#待开发) | 用 `mam job submit --command` 一次完成登记与启动，返回 JOB-ID。 |
| 5 | [跨集群同步](commands/workspace.md#跨集群同步) | 同步任务的 worktree 和指定文件，支持远端运行及结果取回。 |
| 6 | [GPU 排队](commands/job.md#待开发) | 为 job 指定 GPU 数量、空闲显存和平均利用率条件，在当前实例内排队启动。 |
| 7 | [消息与状态输出](commands/service.md#消息与状态输出) | 明确 Manager 转发 job 停止消息的动作，减少重复唤醒和输出；沿用降级路径，不维护 Codex fork。 |
| 8 | [执行者向 Manager 发消息](commands/service.md#执行者主动发消息) | 自动识别发送者，默认发送给当前实例 Manager，并能唤醒 idle Manager；TASK-ID 可选。 |
| 9 | Token 用量与优化 | 按用途统计 cache input、no-cache input、output 和费用，区分 272k 上下文价格；减少无效轮询、空操作和重复读取，比较优化前后的用量。 |
