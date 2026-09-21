# 集群C实验资产与workspace只读审计
# 目标

只读审计集群C（`wuwen-4090-1/2/3`，共享`/mnt/public`）的评测结果、活跃进程和workspace，重点核对计划内原协议与HF结果是否已回传集群A、是否存在partial/失败/smoke及可清理远端副本。

# 权威入口

- 先阅读项目根`AGENTS.md`、MAM `README.md`和`.local/wuwen-4090.md`；进入远端仓库前阅读对应`AGENTS.md`。
- 当前实验范围：`/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md`。
- 当前进度：`/root/Documents/task-state-vla-paper/docs/PROJECT_PROGRESS.zh-CN.md`。
- 集群C项目根：`/mnt/public/xcj/Projects/state-vla`；集群A同名路径不是同一存储。

# 核查范围

1. SSH核对三台主机可达性、GPU/相关进程、正在运行或遗留的评测/服务进程；不得停止进程。
2. 盘点C侧`workspace`：TASK-ID、大小、git dirty状态、活跃依赖、独有未提交内容和可清理前置条件。
3. 盘点C侧计划内eval结果：N/S/J/T/U和HF-J/HF-fixed/HF-event，按task/setting/train seed/eval seed核对100-terminal、partial、错误、smoke和重复目录。
4. 对照A侧`/mnt/public/xcj/Projects/RMBench/eval_result`及state-vla镜像，只核对必要metadata、summary和文件大小；明确已回传、未回传、覆盖冲突和C侧唯一结果。
5. 检查旧服务目录、失败结果、smoke和重复回传副本，列出清理候选但不删除。共享评测输入模型不随结果自动列为清理对象。
6. 与PROJECT_PROGRESS及两个CSV比较，报告任何进度差异，尤其是46个已有终态批次的可证实范围。

# 约束

- 全程只读；不得删除、移动、改名、启动训练/评测或修改远端仓库。
- 不创建worktree，不生成大JSON、hash清单、逐episode或逐文件索引。
- “可清理”必须证明A侧已有对应结果且无活跃依赖；无法证明则保留。

# 交付

在MAM `report.md`发布简洁报告，包含：三主机进程状态；计划内eval表；回传状态；workspace表；清理候选及前置条件；与当前进度的差异；阻塞项。不要在论文仓库新增审计文件。
