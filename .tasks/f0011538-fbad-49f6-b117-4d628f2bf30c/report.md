# 2026-09-22 归档准备草稿（未发布）

为保留未合入的可复用代码，已建立稳定 ref，未合入主线：RMBench `codex/state-vla-delivery-f0011538` 指向 `05e512f529a4dea393d2f730b1f34ed6d5b5f212`，OpenPI `codex/state-vla-delivery-f0011538` 指向 `ec86d857d075cd8e1dc7aba2445e557d76ab2069`。robot-bridge 的 task HEAD `f45c6a472d51365e60847cd028502395c47f1575` 已由非 task ref `codex/unified-sim-real-runtime` 承载，不另建重复 ref。

正式产物仍在稳定业务路径：observe checkpoint 位于 `openpi/checkpoints/observe_and_pickup_n_b_formal20k_ec86d857_20260914T162824Z/.../20000`，swap_T 原始数据和转换验证位于 `RMBench/data/swap_T/demo_clean_state` 与 `RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048`。workspace 内历史 `checkpoint-transfer-20260920/`、`deployment/`、三个 `.venv`、pytest/ruff 缓存及 15 个 source `__pycache__` 目录已删除；其中前七个根目录清理 133,850 个文件、逻辑约 15.7 GiB。删除范围均为 task-local 普通目录，未遍历符号链接，也未删除正式产物。

`policy/pi05/processed_data` 中的两组 50-episode HDF5 输入与 `RMBench/data` 的原始 HDF5 并非同一字节副本，故未删除：已迁移至主 RMBench checkout 的稳定 ignored 路径 `/mnt/public/xcj/Projects/RMBench/policy/pi05/processed_data`（100 个 HDF5，约 2.5 GiB），workspace 路径改为该位置的符号链接。两组 2-episode smoke 副本已删除。

全部 7 条 MAM job 已 archive；workspace 顶层仅剩登记的 RMBench、OpenPI、robot-bridge worktree，满足 `outer_check` 的结构条件。下方对已删除 workspace receipt/transfer 路径的历史引用不再是交付要求。Manager 可在本草稿发布后 archive task；不再存在本 task 的代码 ref、job 或 workspace 外层目录阻塞。

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

## 2026-09-22 当前交付与归档状态

已核对稳定产物：observe formal checkpoint 位于
`/mnt/public/xcj/Projects/openpi/checkpoints/observe_and_pickup_n_b_formal20k_ec86d857_20260914T162824Z/pi05_rmbench_observe_and_pickup_no_memory/memory20k_ec86d857_observe_and_pickup_n_s0/20000`；swap_T 的 source validation、pipeline validation 和 CPU batch 分别位于
`/mnt/public/xcj/Projects/RMBench/data/swap_T/demo_clean_state/metadata/validation_report.json`、
`/mnt/public/xcj/Projects/RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048/swap_T_n_pipeline_validation.json` 和
`/mnt/public/xcj/Projects/RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048/real_cpu_batch_swap_t_n.json`。

当前归档阻塞是代码尚未交付：RMBench `05e512f529a4dea393d2f730b1f34ed6d5b5f212` 与 openpi `ec86d857d075cd8e1dc7aba2445e557d76ab2069` 尚未被任何非 `task/f0011538-fbad-49f6-b117-4d628f2bf30c` 分支包含。workspace 中的 transfer/restore 收据仅按历史要求暂留，不构成当前归档阻塞；本轮未迁移产物或扩展清理 workspace。

## 最终状态

Task 已于 2026-09-22T08:43:57Z 归档，旧 workspace 与 task 分支已删除；上述稳定数据、checkpoint 和交付分支保留。
