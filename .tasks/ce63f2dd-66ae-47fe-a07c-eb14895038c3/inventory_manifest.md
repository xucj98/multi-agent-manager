# 20260910 memory_chunk 只读盘点 manifest

采样：2026-09-13 01:07 +08:00。根目录：
`/mnt/public/xcj/Projects/openpi/checkpoints`、
`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910` 与
`wuwen-4090-1:/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910`。

## 训练 checkpoint

| 组 | 完成数 | 实物模式 |
| --- | ---: | --- |
| Q2 | 12 | `memory20k_e7e5ac54_{rearrange,put_back}_{full_t_plus_1,full_t_plus_30}_s{0,1,2}/20000` |
| B | 12 | e7e5 的 rearrange serial/no-memory seed0（2）；7ae41311 的 rearrange serial/no-memory seed1/2（4）；695bc51f 的 put-back serial/no-memory seed0/1/2（6） |
| wash | 2 | `memory20k_ad6bb77e_wash_{full,serial}_s0/20000` |
| U | 0 | 六个 `memory20k_cbbba844_*_full_initial_s{0,1,2}/20000` 目录为空 |
| 未完成 wash | 4 | `memory20k_19e98b62_wash_{full,serial}_s{1,2}` 无有效 `20000` |

每个计入项的 `20000` 都有 params/assets/metadata 实物；published MAM 验收报告为 e7e5ac54（14）、695bc51f（6）、7ae41311（4）和 ad6bb77e（2）。

## 正式 100ep（去重后）

| 来源 | 独立 checkpoint/trainseed/evalseed 批次 |
| --- | ---: |
| Q2：两任务 × t+1/t+30 × trainseed0/1/2 的 eval0 | 12 |
| B：rearrange serial/no-memory 的 trainseed0 eval0 | 2 |
| B：rearrange no-memory trainseed1/2 × evalseed0/1/2（`*_r2/final_review.json`） | 6 |
| B：rearrange serial trainseed1 × evalseed0（`*_r2/final_review.json`） | 1 |
| 合计 | **21** |

因此为 17 个模型至少一批；其中 no-memory trainseed1、2 各有 evalseed0/1/2，故 **2 个模型完成 300ep**。本机与 C 同名镜像只取一次。`put_back_full_t_plus_1/s0` 的 69/100 与 `put_back_full_t_plus_30/s0` 的 70/100 是不同 checkpoint，各计一次；22ep partial 和所有 smoke/gate/retry 不计。

## 未完成 formal

MAM 与 C 结果树同时显示 7 个 serial-lag30 r3 formal 正在运行：
`trainseed{0}:evalseed{1,2}`、`trainseed{1}:evalseed{1,2}`、
`trainseed{2}:evalseed{0,1,2}`。采样 episode 数依次为 26/18、59/56、46/43/35，均无 `final_review.json`，不计入 21。

## Offline

`wash_memory_v1_20k_offline5ep_retry2`：wash_full 和 wash_serial 各完成固定 5 集（共 10 集，launcher exit 0、十集 exit 0）。它是训练集回放的 action/phase 指标，不是闭环成功率，也不计入 100ep。
