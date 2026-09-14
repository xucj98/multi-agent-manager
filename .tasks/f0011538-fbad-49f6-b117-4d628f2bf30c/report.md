# observe_and_pickup N 已具备准入候选；swap_T 仍在采集

本次已完成 `observe_and_pickup` 的 50 条 source → processed HDF5 → 14-D robot-only LeRobot → N sidecar/norm 全链路验收，并生成了受 Manager 环境变量门禁保护的 50-step、CPU checkpoint recovery 和 formal 20k 候选。**没有启动 20k，也没有启动 50-step smoke 或 CPU recovery。**

`swap_T` 的正式采集进程仍在运行，尚不把其未完成数据或未裁决的连续 J/S schema 作为训练准入。

## Worktree 与提交

- RMBench：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench`，commit `05e512f529a4dea393d2f730b1f34ed6d5b5f212`。
- OpenPI：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/openpi`，commit `ec86d857d075cd8e1dc7aba2445e557d76ab2069`。
  - `ec86d85` 在已有 N 转换/配置提交 `6c05017` 之上显式将 RMBench Memory-v1 builder 默认 seed 固定为 0，避免继承通用默认 42。
  - `ruff check`、4 个 targeted tests 和完整 `src/openpi/training/config_memory_test.py`（7 passed）通过；两个新 N config 均 materialize 为 seed 0、bs32、H50/K30、empty memory。

已实际读取 Manager 指定的 `/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md` 与 `ASSET_AUDIT.zh-CN.md`；先前报告中把资料缺失归因于仅搜索 `/mnt/public` 的说法已更正。

## observe_and_pickup 数据准入事实

原始 source 通过完整重验：50 集、7,530 raw frames，accepted generation seeds 为 `0..15,17..50`，没有使用正式 eval seed 范围。每个 episode 均保留遮挡前可辨认的 reference `(modelname, model_id)`、候选集合、初始 pose 和 wall frame；这些事实仅在 source provenance/trace 中，不进入在线 N 输入或训练列。

转换后数据为 50 集、7,480 frames、50 Hz。全 50 集逐行验证：

- processed `qpos == raw q(t)`，processed `action == raw q(t+1)`；
- LeRobot state/action 与 processed 值逐行精确一致；
- 14-D robot-only sidecar 与 converted action 对齐，尾行重复末 action；
- 训练列仅包括 14-D state、action、三路 RGB 和 LeRobot 索引/时间字段。`meta/rmbench/` 的 trace/provenance 不是训练列。

主要证据位于：

- `/mnt/public/xcj/Projects/RMBench/logs/wave1_missing_tasks_a/observe_and_pickup_n_conversion_20260914T1456/observe_and_pickup_n_pipeline_validation.json`，SHA-256 `f8517117558e23c1b3c0a4945abdba70d284e975c9b61a95e7a4eebf3e4bde29`；
- 同目录 `source_validation_rerun.json` 与 `real_cpu_batch_observe_n.json`；
- sidecar `episode_memory.json` SHA-256 `e6d52eab99b07cc1114fd24495d1f810a6d446a23dad8d4fd706e036cee4c159`；
- norm `norm_stats.json` SHA-256 `b07a1b4f1dc488e032e0c85e3faaa8c1098dfa31ed88890182f98b69d61e9b27`。

`--max-frames 10000` 并未产生 10,000 个训练样本：数据集只有 7,480 行，因此 norm 使用了 `shuffle=False` 下 233 个完整 batch × 32，即 **7,456 行**，丢弃末尾 24 行。后续报告不得将其写成“使用 10,000 帧”。

实际 CPU batch 已通过：`CUDA_VISIBLE_DEVICES=''`、`JAX_PLATFORMS=cpu`、`HF_LEROBOT_HOME` unset。原始 sample 为 14-D state、`[50,14]` action 和三路 RGB；模型输入按 Pi0.5 pad 为 `[32,32]` state、`[32,50,32]` action，后 18 个维度为零，loss 只启用前 14 维。所有 semantic key-state fields 为 `None`，没有 provenance 键。

## Manager-gated N 候选

共享 checkpoint 根下的候选目录：

`/mnt/public/xcj/Projects/openpi/checkpoints/observe_and_pickup_n_candidates_ec86d857_20260914T153601Z`

其中固定 OpenPI `ec86d857...`、`pi05_rmbench_observe_and_pickup_no_memory`、pi05_base 新初始化、seed 0、bs32、H50/K30、BF16 model-only、共享 `/root/.cache -> /mnt/public/xcj/cache`、`HF_LEROBOT_HOME` unset，以及 CUDA `XLA_FLAGS=--xla_gpu_enable_command_buffer=` 和 `XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`。预检还固定 50 集/7,480 frames、sidecar/norm/pipeline report 的上述 hash，拒绝任何额外训练列。

- `launch_observe_and_pickup_n_smoke50_candidate.sh GPU_INDEX`：50 个 fresh updates，门禁 `MAM_OBSERVE_N_SMOKE50_APPROVED=f0011538-fbad-49f6-b117-4d628f2bf30c`。
- `launch_observe_and_pickup_n_cpu_recovery_candidate.sh`：仅在 CPU 恢复配套 smoke 的 model-only 参数并拒绝读取训练 source/base/YAML，门禁 `MAM_OBSERVE_N_CPU_RECOVERY_APPROVED=f0011538-fbad-49f6-b117-4d628f2bf30c`。
- `launch_observe_and_pickup_n_formal20k_candidate.sh GPU_INDEX`：从 pi05_base fresh start 的 20,000-step 正式候选，绝不从 smoke 续训，门禁 `MAM_FORMAL_20K_APPROVED=f0011538-fbad-49f6-b117-4d628f2bf30c`。

候选文件汇总 SHA-256 为 `3cf2f86d7a9b21ddc1a908d51794defead0bf2d9e8e54119a2af7ded841eebe5`，manifest SHA-256 为 `a2443f6c5e8e9913eec7486b8d011258eacc9a85875fff76864fdcd6e61e6b52`。静态 shell/Python 检查以及 smoke/formal 预检都通过。未设置三个授权变量时，三个入口均实测 exit 77，`smoke50/` 和 `formal20k/` 结果根不存在，没有启动训练或 recovery 进程。门禁与预检收据在：

`/mnt/public/xcj/Projects/multi-agent-manager/.tasks/f0011538-fbad-49f6-b117-4d628f2bf30c/evidence/observe_n_candidate_controls_20260914T153601Z/candidate_admission_receipt.json`

CPU recovery 目前只是候选：它必须在 Manager 准入并完成对应 smoke checkpoint 后执行。formal 20k 仍严格等待 Manager 准入和 MAM 长进程登记。

## swap_T 状态

MAM job `a7b7eb97-5c5b-4803-a448-024b92afbd43`（PID `1498697`，GPU5）在本次 15:43Z 刷新时仍为 running。15:44Z 的只读快照已有 42 组 HDF5 / trace / provenance 和 94 条 attempt records；尚未达到最终 50 集验收，因此未运行 swap_T 的 source validator、N 转换、sidecar、norm 或 CPU batch，也没有建立其训练候选。

原始采集继续保留 actor-origin 与首帧落稳两种 initial-pose 来源、当前 pose、Sapien `wxyz` quaternion 和 `[x,y,yaw]`。连续 swap_T J/S 的 canonical source、归一化与接口仍交由 Manager 裁决；不会量化成类别字段替代该研究问题。

## MAM job 收尾与下一步

observe 转换 job `0cfdfc00-e935-4fae-8c33-21e53042a515` 已停止，receipt 记录 exit status 0（2026-09-14 15:11:30Z），且上述数据、CPU batch 和候选证据已经核验。本报告发布后可归档该 stopped job。swap_T 的 running job 保持登记和运行，不干预。

swap_T 停止后应依序进行完整 source 验证、processed/LeRobot 转换、robot-only sidecar、实际 norm 采样说明、CPU batch 和独立候选，再提交给 Manager。任何 observe smoke、CPU recovery 或 formal 20k 均只在相应 Manager 门禁授权后执行；本执行者未启动正式训练。
