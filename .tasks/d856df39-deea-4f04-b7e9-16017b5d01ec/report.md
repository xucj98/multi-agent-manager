# 集群A只读审计与Manager清理裁决

审计时间：2026-09-22。范围为当前主机、`wuwen-1`、A侧checkpoint/eval目录、项目workspace和MAM记录。审计阶段未启动或停止训练/评测；Manager随后按既定清理规则删除了已被正式产物替代的smoke/失败checkpoint目录。

## 主机与进程

- 当前主机和`wuwen-1`均可达，审计时`nvidia-smi --query-compute-apps`无计算进程。
- press-button、swap_T、blocks-ranking和wave1历史PID均已不存在；对应MAM中4个job状态为stopped而非running。
- 没有证据表明A侧存在仍在运行的本项目训练、评测或传输。

## 计划内checkpoint

- A侧存在23个当前计划内20k产物：N/S/J共19个、U两个、T两个。
- 已验收21个；`swap_T.N.t0`和`blocks_ranking_try.N.t0`有step20000产物及CPU gate PASS记录，但MAM job尚未归档，当前矩阵继续标为`artifact_pending_restore_acceptance`。
- battery S和observe-and-pickup N由B回传，A侧正式参数树与CPU restore均存在；B审计确认远端正式模型已验证删除。
- 未发现P checkpoint；四个新增任务仍没有S/J checkpoint，与正式计划一致。

## eval记录

- 审计开始时A侧`memory_chunk_20260910`仅有30个名称含`100ep`的目录，未包含当前进展引用的全部C侧canonical原件。
- 当前计划记录的46批为：原协议28批加HF独立协议18批。A侧原缺少40个canonical目录，现已由C回传；逐目录summary均为`completed/100/error=null`，源/目标文件数与总字节数40/40一致。加上原有6个canonical eval0，A侧当前46/46计划批次原始目录自包含。
- A侧未发现额外计划内完成批次；PROJECT_PROGRESS的成功数与已知终态一致。

## workspace

`/mnt/public/xcj/Projects/workspace`中旧项目workspace均对应当前未归档任务：

| TASK-ID | 约大小 | 状态/裁决 |
| --- | ---: | --- |
| `0acf5d43...` | 16G | HF实现，pending；保留到协议门禁和任务收尾 |
| `2a792e9a...` | 16G | press/ranking数据与N训练，pending且有2个stopped job；保留 |
| `a98a1d8e...` | 16G | V review，pending但已移出主计划；第4项优先归档后删除 |
| `e34ba9b3...` | 16G | V实现，pending但已移出主计划；第4项优先归档后删除 |
| `f0011538...` | 19G | observe/swap_T，pending；四任务S/J合同仍可能引用，保留 |
| `f3488141...` | 16G | wave1 C评测，pending且有2个stopped job；回传/验收后收尾 |

三个本轮审计workspace为空。MAM `.local/retained-workspaces`只有`cba8b004...`约13M和`fa928e8d...`约6.2M；没有空间压力，待第4项确认任务历史已足够后统一删除。

## 已执行清理

Manager删除了明确被正式20k替代且无活跃PID的A侧中间目录：battery、blocks-ranking、press-button、swap_T、wave1 N/J/S的smoke，observe候选失败目录，swap_T失败formal/lock，以及V单/双卡OOM profile。按清理前目录表合计约55GB以上；未删除任何正式20k checkpoint。结果侧另删除4个smoke/诊断目录和4个summary为failed的历史目录，约0.08GB；删除后46/46 canonical计划结果再次通过门禁。

## 剩余阻塞

1. `swap_T.N`和`blocks_ranking_try.N`的两个stopped MAM job需在第4项归档，随后可将训练状态升级为accepted。
2. V两个pending任务和约32G A workspace已不在当前主计划，应在第4项归档任务后物理清理。
