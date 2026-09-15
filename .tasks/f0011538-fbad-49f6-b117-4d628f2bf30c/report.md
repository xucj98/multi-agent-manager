# observe_and_pickup N 已在 B 启动正式训练；swap_T N 数据链已就绪

`observe_and_pickup` N 数据链已经验收，并已按 Manager 2026-09-15 授权完成 B 端 fresh smoke50 和 checkpoint-only CPU recovery。正式 20k 正在 B 的 GPU6 运行；它从 `pi05_base` fresh start，不从 smoke checkpoint 续训。

## 代码、数据与工作树

- A RMBench worktree：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench`，`05e512f529a4dea393d2f730b1f34ed6d5b5f212`。
- A OpenPI worktree：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/openpi`，`ec86d857d075cd8e1dc7aba2445e557d76ab2069`。
- B 独立 OpenPI worktree：`/mnt/public3/xcj/Projects/state-vla/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/openpi`，同一冻结 commit、clean status、独立 `.venv`；`worktree_env_smoke.py` 与依赖检查通过。

observe 原始数据已重验为 50 集、7,530 raw frames；转换后的 LeRobot 数据为 50 集、7,480 帧、50 Hz。训练列只有 14-D robot state/action、三路 RGB 和索引/时间字段；遮挡前 identity、候选、pose 和 wall trace 仅在 provenance/trace 中。sidecar SHA-256 是 `e6d52eab99b07cc1114fd24495d1f810a6d446a23dad8d4fd706e036cee4c159`，norm SHA-256 是 `b07a1b4f1dc488e032e0c85e3faaa8c1098dfa31ed88890182f98b69d61e9b27`。norm 实际使用 7,456 行（233 × 32），不是虚构的 10,000 行。

B 输入经过 `wuwen-nx-aic -> zx-data` 传输；四个 rsync checksum dry-run 均为空，bundle SHA-256 在两端一致为 `95b7acecfe5d93d4b6deac21d0b003d1a74d8f8acf0d22c8d890625724831c22`，dataset file-list digest 一致。收据位于：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/deployment/observe_n_b_20260914T162824Z/transfer_receipt.txt`

## B smoke、恢复与正式训练

B 合同预检已确认 `ec86d857`、50 集/7,480 帧、seed 0、bs32、H50/K30、empty task memory、model-only BF16、`pi05_base` 和 `HF_LEROBOT_HOME` unset。首个 smoke 在数据 loader 的 spawned worker 重执行未加主入口保护的外部 runner 时发生 CUDA OOM；没有产生 train step 或 checkpoint。失败根、日志 hash 和原控制文件已保留：

`/mnt/public3/xcj/Projects/state-vla/openpi/checkpoints/observe_and_pickup_n_b_smoke_ec86d857_20260914T162824Z`

修复只是在 B 部署控制 runner 中将参数解析和 `train_lib.main()` 置于 `if __name__ == '__main__'` 下；冻结 OpenPI commit、数据、配置和训练合同均未改动。修订控制文件通过 B 端逐文件 SHA-256 与 spawn import probe 验证。

retry smoke 使用独立根：

`/mnt/public3/xcj/Projects/state-vla/openpi/checkpoints/observe_and_pickup_n_b_smoke_ec86d857_retry1_20260914T165414Z`

它在 GPU6、PID `1270900` 成功完成 step 50，并写入 model-only checkpoint `.../pi05_rmbench_observe_and_pickup_no_memory/smoke50_ec86d857_observe_and_pickup_n_s0/50`。checkpoint 只含 `params`、`assets` 和 `metadata`，没有 `train_state`。

CPU checkpoint recovery 已通过，输出：

`.../observe_and_pickup_n_b_smoke_ec86d857_retry1_20260914T165414Z/validation/cpu_checkpoint_recovery.json`

它恢复了 51 个参数叶、3,353,433,872 个元素／6,706,867,744 bytes；全部 BF16、有限值、形状完整，并确认拒绝读取训练 source/base 路径。

正式 20k 已启动：

- GPU：B GPU6
- PID：`1274019`
- MAM job：`20b64634-3586-4500-b0e2-56de0e5da072`
- 根目录：`/mnt/public3/xcj/Projects/state-vla/openpi/checkpoints/observe_and_pickup_n_b_formal20k_ec86d857_20260914T162824Z`
- 设置：fresh `pi05_base`、seed 0、bs32、H50/K30、20,000 steps、BF16 model-only、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`。

正式训练已确认完成首个 update，并在最新观测中到达 step 13；稳定吞吐约 3.5 秒／step，训练日志给出的剩余时间约 19 小时 36 分钟。GPU4 未使用；按资源协调，observe 只使用 GPU6，若需回退优先 GPU7/5，不占用 GPU0/1/4。

## swap_T

swap_T 采集进程已自然结束，MAM job `a7b7eb97-5c5b-4803-a448-024b92afbd43` 已归档。源验证于 `2026-09-15T00:47:41Z` 通过，报告为：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench/data/swap_T/demo_clean_state/metadata/validation_report.json`

原始目录有 episode 0–49 的完整 HDF5、state trace、provenance、instructions、trajectory pickle 和 video 各 50 份，17,201 个 raw frames（每集 332–360）。`seed.txt` 使用 0–51 中除 13、34 外的 50 个 seed；`collection_attempts.jsonl` 保留全部 102 条记录（52 条 planning，含 2 条 rejected；50 条 replay），没有使用正式评测 seed。每个 episode 的初始二维 pose／yaw、Sapien `wxyz` quaternion 和成功阈值均保留在 source-only provenance，尚未绑定到 J/S。

N robot-only 转换已经完成。命令收据、日志和 MAM job `63c47f63-d60f-47e9-a7a1-2dae65b1c594`（已归档）位于：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048/`

processed HDF5 位于 `RMBench/policy/pi05/processed_data/swap_T-demo_clean_state-50`；LeRobot 数据位于 `/root/.cache/huggingface/lerobot/swap_T_demo_clean_state_shared_memory`（规范化到 `/mnt/public/xcj/cache`）。转换后为 50 集、17,151 帧、50 Hz，只有 14-D robot state/action、三路 RGB 与索引/时间列。端到端校验通过，报告：

`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048/swap_T_n_pipeline_validation.json`

校验确认 raw `q(t)`→processed `qpos`、raw `q(t+1)`→processed `action`、processed→LeRobot state/action 均为 50/50 集逐元素一致，并完成 600 个 RGB 首尾帧解码检查。LeRobot provenance 复制 106 对文件且 `not_training_columns=true`；conversion manifest SHA-256 为 `8afc1a90fb140cb159a58d6ea7d232dcae0c6a4b76acdc3470878024bbd79e25`。

N sidecar 与 norm 已生成：

- sidecar：`openpi/data/memory_v1/rmbench/swap_T_demo_clean_state_shared_memory/robot_only/`，SHA-256 `894faec572ad79c683e8112f418b7f5f2b148feafd242d3147a28d66d001de8a`；无 semantic series、availability 或 events。
- norm：`openpi/assets/memory_v1/rmbench_swap_T_robot/norm_stats.json`，SHA-256 `9a249ce79bc5f3b744ff666578f79893ac1f8d6b680fa5f378d14b4d4e0c96be`；14-D state/actions 全部 finite，统计采样 17,120 行（535×32，丢弃尾部 31 行）。
- 实际 CPU batch：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench/logs/wave1_missing_tasks_a/swap_T_n_conversion_20260915T0048/real_cpu_batch_swap_t_n.json`，通过 `pi05_rmbench_swap_T_no_memory` 的 seed 0、batch 32、H50/K30、20,000-step 合同；raw sample 为 14-D state、50×14 action，模型 batch 为 32×32 与 32×50×32，padding tail zero，semantic key-state fields 全部 None。

连续 swap_T schema 仍待 Manager 裁决；当前只准备并验收 N no-memory 链，不启动新的 swap_T 正式训练。

## MAM 收尾与后续

B 传输 job `1d1002a1-fa1a-4fd6-b227-34ef64f7c5b9` 已在零差异校验后归档。正式训练 job 保持登记并运行；训练完成后将 checkpoint、日志和元数据回传 A 端，完成本地恢复验证后按 B 规范删除本任务 B 模型副本并记录结果。
