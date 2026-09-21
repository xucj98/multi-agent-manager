# 集群C实验资产与workspace审计

审计时间：2026-09-22。范围为`wuwen-4090-1/2/3`共享项目根、计划内eval目录、主机进程和workspace。审计阶段只读；Manager随后按既定规则清理失败/smoke目录，并启动计划内结果回传。

## 主机与进程

- 三台主机均可SSH访问；共享存储从C1核对。
- 未发现命令行属于本项目的训练、评测、policy server或仿真worker进程。
- C1/C2的`nvidia-smi`显示若干本实例`ps`不可见的GPU PID，按集群说明判定为其他隔离实例占用，不能由本项目停止或清理；C3无compute PID。

## 结果目录

审计前，`memory_chunk_20260910`中有81个名称含`100ep`的目录：

- 72个`diagnostics_summary.json`为`completed`且`episode_count=100`。
- 8个在23个accepted episode后因worker reset RPC EOF失败。
- 1个零episode，原因是formal与matching smoke启动合同不一致。

72个完成目录同时包含当前计划、补充training seed和历史结果，不能直接作为当前计划完成数。当前计划需要从C回传而A侧缺失的canonical目录共40个：HF 18个、两任务N/S/J/T的eval1/2共16个、wave1单批4个、put-back N/S eval0 canonical重跑2个，合计约4GB。Manager以MAM job `bad9c9ef-d899-4bee-8442-c3e6fc2c3c08`完成逐目录回传；每个目录在A侧隐藏临时路径完成后，用系统Python验证`completed/100/error=null`再原子改名，未覆盖既有结果。完成后再次核对40个summary，并比较C源端与A目标端逐目录文件数和总字节数，40/40一致；job已归档。

首次传输job `6d2940d1-0e0f-4735-a32f-6055529c51ee`因中转机无`jq`在首个目录发布前停止，未产生canonical目录；临时目录已删除，job已归档。

## 已执行清理

- 删除64个smoke/diagnostic目录。
- 删除9个failed formal目录（8个23-episode RPC失败、1个零episode门禁失败）。
- 删除约44MB的`memory_chunk_20260910_hf_engineering`工程目录；正式HF 18批保留。
- 合计73个主结果中间目录约0.26GB；没有删除任何`completed/100`目录。

## C workspace

共享workspace共有7个：

| TASK-ID | MAM状态 | 裁决 |
| --- | --- | --- |
| `0acf5d43...` | pending | HF正式结果和运行代码来源；保留到首动作门禁及任务收尾 |
| `f3488141...` | pending | wave1结果来源，且有2个stopped MAM job；回传验收后收尾 |
| `2b8c1566...` | archived | 环境修复任务；无活跃进程，可清理候选 |
| `39bdb4b8...` | archived | cover N eval0已完成；canonical结果回传后可清理 |
| `8968b7f5...` | archived | 旧P0诊断；当前计划不依赖，可清理候选 |
| `bed9952b...` | archived | 文档/环境验收；无当前实验依赖，可清理候选 |
| `e6908de7...` | archived | 原协议评测历史runtime；canonical结果回传并确认新入口后可清理 |

归档workspace的git记录均显示clean或工作树已由MAM移除；本轮未直接删除，避免在C结果尚未回传完成时切断唯一运行上下文。

## 与当前进度的关系

- 当前计划的46批算术仍为原协议28批+HF18批；C侧72个完成目录不能上调该数值。
- wave1四个结果与PROJECT_PROGRESS一致：swap N 14/100、swap J 90/100、battery N 23/100、cover N 0/100。
- HF两任务18批终态与PROJECT_PROGRESS一致，但first-action/RNG/runtime门禁未闭合，仍只能作描述性结果。
- C侧没有U或P正式eval。

## 阻塞与后续

1. 第4项先收尾`f3488141...`和`0acf5d43...`，再删除5个已归档C workspace。
2. 补后续eval时使用新的clean workspace和当前正式计划，不复用已删除的失败/smoke目录。
