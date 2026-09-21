# 集群A实验资产与workspace只读审计
# 目标

只读审计集群A（当前主机与`wuwen-1`）的实验记录、训练checkpoint、评测结果、活跃进程、MAM workspace和普通项目workspace，给Manager一份可裁决的事实清单。

# 权威入口

- 先阅读项目根`AGENTS.md`、MAM `README.md`相关规则和`.local/README.md`。
- 当前实验范围：`/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md`。
- 当前进度：`/root/Documents/task-state-vla-paper/docs/PROJECT_PROGRESS.zh-CN.md`。
- 机器矩阵：同仓库`docs/planning/*.csv`。
- MAM任务和job：以`mam task list`、逐任务`mam task status/show`、`mam job list/status`为准。

# 核查范围

1. 当前主机与`wuwen-1`的可达性、GPU/相关进程和长进程状态；不得停止进程。
2. `/mnt/public/xcj/Projects/openpi/checkpoints`中的计划内N/S/J/U/T/P资产：只核对目录、关键metadata/step和大小，不做全量hash。
3. `/mnt/public/xcj/Projects/RMBench/eval_result`及`/mnt/public/xcj/Projects/state-vla/RMBench/eval_result`中的计划内结果：按task/setting/train seed/eval seed列出100-terminal完成情况、partial/失败/smoke候选和重复目录。
4. `/mnt/public/xcj/Projects/workspace`以及MAM记录涉及的workspace：列出大小、对应TASK-ID、任务状态、git dirty状态、是否有活跃进程/独有未提交内容。
5. 将事实与PROJECT_PROGRESS及两个CSV比较，明确一致项、缺失项和疑似误记项。

# 约束

- 全程只读；不得删除、移动、改名、启动训练/评测或修改仓库。
- 不创建worktree，不生成大JSON、hash清单或逐文件索引。
- “可清理”必须同时写明：对象、体积、为何无活跃依赖、保留的唯一信息在哪里、清理前置条件。无法证明则列为保留/待确认。
- 对失败或partial结果，只报告最小事实，不复制大日志。

# 交付

在MAM `report.md`发布简洁报告，包含：主机/进程状态；计划内checkpoint表；计划内eval表；进度差异；workspace表；清理候选；阻塞与不确定项。不要在论文仓库新增审计文件。
