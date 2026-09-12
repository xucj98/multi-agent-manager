# 论文实验进展清点：训练与正式评测去重核验

采样于 **2026-09-13 01:07 +08:00**；全程只读 checkpoint、结果树和 MAM 已发布报告，未修改实验、台账或 job。

## 可用于当前论文进展的计数

| 项目 | 数量 | 口径 |
| --- | ---: | --- |
| 当前范围的训练完成 | **26 / 36** | 有非空 `20000` checkpoint，且可由 published 验收报告追溯 |
| 新模型正式完成的独立 100ep 批次 | **21** | 按 checkpoint/trainseed/evalseed 去重；本机/C 镜像只计一次 |
| 至少完成一个正式 100ep 的模型 | **17** | 同一 checkpoint 的不同 eval seed 只算一个模型 |
| 完成 evalseed0/1/2、共 300ep 的模型 | **2** | rearrange no-memory 的 trainseed1、2 |
| 当前 running formal 批次 | **7** | C 上 rearrange serial-lag30 的 r3 leaves；尚未完成 100ep |
| wash offline | **full 5ep + serial 5ep** | 训练集回放，非闭环 success rate；不计入正式 100ep |

训练的 26 个实物构成为 Q2 12、B 12、wash seed0 两项。B 的 12 包括 e7e5 的 rearrange serial/no-memory seed0 两项、7ae41311 的 rearrange serial/no-memory seed1/2 四项，以及 695bc51f 的 put-back serial/no-memory seed0/1/2 六项。U full-initial 六项的 `20000` 目录为空；wash seed1/2 四项没有有效 `20000`，故这十项未计入完成数。

正式 21 批构成为：Q2 12 个 evalseed0、B 的 rearrange serial/no-memory trainseed0 各一个 evalseed0（2）、rearrange no-memory trainseed1/2 的三 eval seed（6），以及 rearrange serial trainseed1 的 evalseed0（1）。所有计入 leaf 均有 100 episode；r2 leaf 另有 `final_review.json` 的 `completed100_verified`、`episode_count=100`、`runtime_errors=0` 证据。

`put_back_full_t_plus_1/s0` 的 69/100 和 `put_back_full_t_plus_30/s0` 的 70/100 由各自的 checkpoint metadata command 指向不同 `full_t_plus_1` / `full_t_plus_30` 训练配置，分别计一次；C 上 put-back 的 22ep r2 leaves 属于 partial，不计。F0、BF16、pilot、smoke、gate、失败/重试 leaf 都已排除。

采样时 7 个 C serial r3 formal leaf 分别为 trainseed0/eval1=26、0/2=18、1/1=59、1/2=56、2/0=46、2/1=43、2/2=35 episode，均未出现 `final_review.json`；MAM `job list` 同时列出 7 个对应 formal job 为 running。

简短 run/checkpoint manifest 位于执行 workspace：
`/mnt/public/xcj/Projects/workspace/ce63f2dd-66ae-47fe-a07c-eb14895038c3/inventory_manifest.md`。

## 主要证据

- 实物 checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints`；计入项的 `20000` 下均有 params、assets、metadata。
- 已发布 MAM 报告：e7e5ac54（14 项 20k 完成）、695bc51f（put-back B 六项 READY）、7ae41311（rearrange B 重复四项验收）与 ad6bb77e（wash 两项 20k 验收）。
- 正式结果树：本机 `/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910` 和 C `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910`；C 通过 `wuwen-4090-1` 只读采样。
- offline：`wash_memory_v1_20k_offline5ep_retry2/RESULTS.md` 记录 full/serial 各固定五集、launcher exit 0 与十集 exit 0。
