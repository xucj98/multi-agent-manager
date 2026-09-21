# 集群B实验资产与workspace只读审计
# 目标

只读审计集群B（`wuwen-11`、`wuwen-12`，共享`/mnt/public3`）的实验资产、活跃进程和workspace，重点确认训练产物是否已回传集群A以及远端副本是否满足清理条件。

# 权威入口

- 先阅读项目根`AGENTS.md`、MAM `README.md`和`.local/wuwen-11.md`；进入远端仓库前阅读对应`AGENTS.md`。
- 当前实验范围：`/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md`。
- 当前进度：`/root/Documents/task-state-vla-paper/docs/PROJECT_PROGRESS.zh-CN.md`。
- 集群B项目根：`/mnt/public3/xcj/Projects/state-vla`，对应集群A的`/mnt/public/xcj/Projects`。

# 核查范围

1. SSH核对两台主机可达性、GPU/相关进程、正在运行或遗留的训练/传输进程；不得停止进程。
2. 盘点B侧`workspace`：TASK-ID、大小、git dirty状态、活跃依赖、独有未提交内容和可清理前置条件。
3. 盘点B侧计划内checkpoint和训练日志，重点覆盖battery S及九任务新增N/S/J；核对step、完成状态、相对路径和大小。
4. 对照A侧对应checkpoint，仅做目录/metadata/关键文件大小核对；明确已回传、未回传、回传未验证、B侧唯一副本。不要做多GB全量hash。
5. 检查B侧失败checkpoint、smoke、缓存和重复副本，列出清理候选但不删除。
6. 与PROJECT_PROGRESS及两个CSV比较，报告任何进度差异。

# 约束

- 全程只读；不得删除、移动、改名、启动训练/评测或修改远端仓库。
- 不创建worktree，不生成大JSON、hash清单或逐文件索引。
- 共享预训练模型和其他项目资产不列为清理候选。
- “可清理”必须证明无活跃依赖，并明确A侧已接收位置；无法证明则保留。

# 交付

在MAM `report.md`发布简洁报告，包含：两主机进程状态；checkpoint回传表；workspace表；远端独有资产；清理候选及前置条件；与当前进度的差异；阻塞项。不要在论文仓库新增审计文件。
