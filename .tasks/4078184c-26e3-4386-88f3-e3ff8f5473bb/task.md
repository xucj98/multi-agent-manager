# MAM job archive：结束跟踪

## 目标
允许归档任意已登记job，无需实际进程停止。archive只结束MAM跟踪并保留历史，绝不停止进程。task归档要求其所有job已archived，不检查已归档job的实际存活。保留既有worktree路径/改动等清理保护，不扩展CLI或新增状态。

## 执行
从MAM main建立本任务独立worktree，阅读AGENTS、开发指南和设计文档。修改job archive、task archive中相关门禁及必要wait过滤，去掉归档时不必要的远端探测。running/stopped/unknown均可archive；--note仍必填；重复归档沿既有幂等行为。保留原进程身份、历史观测、归档时间和原因，不能伪写stopped。已归档job不再触发wait待办，不再周期探测。
同步README、CLI help、docs/task-management-design.zh-CN.md中的相关语义，文字简洁。不要改无关文档或生产.tasks记录，不安装、不合并、不push、不触碰实际PM。

## 验收交付
必要测试覆盖运行中的真实本地sleep被归档后仍存活、unknown/SSH不可达无需连接即可归档、未归档job仍阻止task归档、全部archived后无需进程停止、wait排除归档job。测试自己的sleep最后自行清理。运行适当测试及开发规定全套；提交代码，report写commit/改动/测试/限制，发布后结束turn，Manager安排独立review。不要空等待或无变化汇报。
