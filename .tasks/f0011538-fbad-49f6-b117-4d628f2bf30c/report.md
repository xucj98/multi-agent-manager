# observe_and_pickup N 已完成；swap_T N 链已就绪

## observe_and_pickup N

A 端 formal N 已完成 20,000 steps，checkpoint 已从 B 端回传并通过 checkpoint-only CPU restore。checkpoint：

`/mnt/public/xcj/Projects/openpi/checkpoints/observe_and_pickup_n_b_formal20k_ec86d857_20260914T162824Z/pi05_rmbench_observe_and_pickup_no_memory/memory20k_ec86d857_observe_and_pickup_n_s0/20000`

CPU restore 证据：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/checkpoint-transfer-20260920/observe_cpu_restore_final.json`

结果 PASS：51 个 parameter leaves、3,353,433,872 个 elements；全部 BF16、finite、shape complete，并验证恢复过程拒绝读取训练 source/base。

A/B transfer receipt：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/deployment/observe_n_b_20260914T162824Z/transfer_receipt.txt`

bundle SHA-256 为 `95b7acecfe5d93d4b6deac21d0b003d1a74d8f8acf0d22c8d890625724831c22`。B 端 formal 模型已删除，日志与验证记录保留。删除收据：

`/mnt/public3/xcj/Projects/state-vla/openpi/checkpoints/observe_and_pickup_n_b_formal20k_ec86d857_20260914T162824Z/validation/model_deletion_receipt_20260920.json`

删除状态为 `deleted_verified`；B 端 metadata hash 为 `2e7e3be87789a4a83469f06702797a6a1edf16f33aa1b0b50b7b6e175374f9e8`。

对应 MAM jobs 已归档：formal `20b64634-3586-4500-b0e2-56de0e5da072`，transfer `8ef019b7-faa8-47d8-b307-e3c1f03ee0ed`。当前没有 observe formal running job。

## swap_T N

source validation：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench/data/swap_T/demo_clean_state/metadata/validation_report.json`

数据为 50 episodes、17,201 raw frames、50 replay；seed 为 `0..51` 排除 `13,34`；保留 102 条 planning/replay 记录；没有正式 eval seed。

N processed/LeRobot pipeline validation：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048/swap_T_n_pipeline_validation.json`

50/50 raw `q(t)`、`q(t+1)` 对齐，RGB 首尾帧检查通过。sidecar SHA-256 为 `894faec572ad79c683e8112f418b7f5f2b148feafd242d3147a28d66d001de8a`；norm SHA-256 为 `9a249ce79bc5f3b744ff666578f79893ac1f8d6b680fa5f378d14b4d4e0c96be`。CPU batch evidence：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048/real_cpu_batch_swap_t_n.json`

连续 swap_T schema 尚未裁决，因此未启动 S/J formal training。

## MAM 状态

observe formal 已完成、回传、CPU restore 和 B 删除收据；swap_T N 链已就绪。当前没有新的 swap_T S/J 训练。f001 的 7 个 jobs 均已归档。
