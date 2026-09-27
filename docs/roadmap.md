# MAM 后续开发规划

任务 1–4、8、9 已完成。后续按以下顺序推进。

| 编号 | 任务 | 要做什么 |
| --- | --- | --- |
| 5 | [job 提交](commands/job.md#待开发) | 用 `mam job submit --command` 一次完成登记与启动，返回 JOB-ID。 |
| 6 | [跨集群同步](commands/workspace.md#跨集群同步) | 同步任务的 worktree 和指定文件，支持远端运行及结果取回。 |
| 7 | [GPU 排队](commands/job.md#待开发) | 为 job 指定 GPU 数量、空闲显存和平均利用率条件，在当前实例内排队启动。 |
| 10 | Token 用量与优化 | 按用途统计 cache input、no-cache input、output 和费用，区分 272k 上下文价格；减少无效轮询、空操作和重复读取，比较优化前后的用量。 |
