# observe_and_pickup N 已在 B 启动正式训练；swap_T 原始采集完成

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

swap_T 采集进程已自然结束，MAM job `a7b7eb97-5c5b-4803-a448-024b92afbd43` 已归档。当前原始目录有 episode 0–49 的完整 HDF5、state trace、provenance、instructions、trajectory pickle 和 video 各 50 份，且保留初始二维 pose／yaw、Sapien `wxyz` quaternion 与成功合同。`collection_attempts.jsonl` 保留全部 102 条尝试记录（包括 2 条 rejected）；当前 50 个 episode 原始集合可供下一步 source 验证与连续 N/J/S 转换。连续 schema 尚待 Manager 裁决，尚未将 swap_T 作为训练准入。

## MAM 收尾与后续

B 传输 job `1d1002a1-fa1a-4fd6-b227-34ef64f7c5b9` 已在零差异校验后归档。正式训练 job 保持登记并运行；训练完成后将 checkpoint、日志和元数据回传 A 端，完成本地恢复验证后按 B 规范删除本任务 B 模型副本并记录结果。
