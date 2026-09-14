# 第一波八条 N/J/S 正式 20k 均已完成并已归档

## 执行结果（2026-09-14 09:41 UTC）

- 八条指定 seed 0 正式训练均从 `pi05_base` 独立初始化，达到请求的 step 20,000，并完成 Orbax finalization；没有从 smoke checkpoint 续训、重训、补 seed 或拼接 checkpoint。
- 每个训练日志都包含有限的 `Step 20000` 指标、`Finished saving checkpoint (finalized tmp dir)`、`No errors found in background save thread` 和 `Done waiting for Save Finalize thread`，且没有 fatal marker。
- 八个 checkpoint 均为 model-only，顶层目录严格为 `_CHECKPOINT_METADATA`、`assets`、`metadata`、`params`，无 `train_state`。CPU 完整参数恢复和 GPU checkpoint-only policy 恢复均通过，且恢复 guard 拒绝读取训练 dataset、`pi05_base`、原 sidecar/assets 和原 YAML。
- 运行合同保持 seed 0、batch 32、H50/K30、20k steps、`save_interval=20000`、BF16 model-only、`/root/.cache` 规范化到 `/mnt/public/xcj/cache`，以及 `HF_LEROBOT_HOME` unset。CUDA 兼容项 `XLA_FLAGS=--xla_gpu_enable_command_buffer=` 保存在 launcher 与启动回执中。

N 的正式执行树为 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/loader/openpi`，commit `5835fa04055d520e418cc1448c1bd58fa1e665cb`；结果根目录为 `/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z`。J/S 的正式执行树为 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/js/openpi`，commit `34002dce65962734c59725a0f6d982ae2c438a2d`；结果根目录为 `/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z`。

| 路径 | 训练 GPU | 20k checkpoint（相对对应结果根） | 最终 loss / grad / param | GPU 恢复 |
| --- | ---: | --- | ---: | --- |
| swap N | 0 | `pi05_rmbench_swap_blocks_no_memory/memory20k_5835fa0_nocmdbuf_swap_blocks_n_s0/20000` | 0.0017 / 0.0469 / 1805.2899 | finite actions `[50,14]` |
| battery N | 2 | `pi05_rmbench_battery_try_no_memory/memory20k_5835fa0_nocmdbuf_battery_try_n_s0/20000` | 0.0007 / 0.0233 / 1804.6187 | finite actions `[50,14]` |
| cover N | 4 | `pi05_rmbench_cover_blocks_no_memory/memory20k_5835fa0_nocmdbuf_cover_blocks_n_s0/20000` | 0.0012 / 0.0249 / 1805.1487 | finite actions `[50,14]` |
| swap J | 1 | `pi05_rmbench_swap_blocks_full_t_plus_1/memory20k_34002dce_nocmdbuf_swap_blocks_j_s0/20000` | 0.0014 / 0.0497 / 1805.1434 | actions `[50,14]`, memory `[50,3]` |
| battery J | 3 | `pi05_rmbench_battery_try_full_t_plus_1/memory20k_34002dce_nocmdbuf_battery_try_j_s0/20000` | 0.0008 / 0.0286 / 1804.6823 | actions `[50,14]`, memory `[50,1]` |
| cover J | 5 | `pi05_rmbench_cover_blocks_full_t_plus_1/memory20k_34002dce_nocmdbuf_cover_blocks_j_s0/20000` | 0.0015 / 0.0470 / 1805.2087 | actions `[50,14]`, memory `[50,4]` |
| swap S | 6 | `pi05_rmbench_swap_blocks_serial_lag30/memory20k_34002dce_nocmdbuf_swap_blocks_s_s0/20000` | 0.0066 / 0.2260 / 1806.1981 | actions `[50,14]`, serial memory `[1,3]` |
| cover S | 7 | `pi05_rmbench_cover_blocks_serial_lag30/memory20k_34002dce_nocmdbuf_cover_blocks_s_s0/20000` | 0.0049 / 0.1810 / 1806.5916 | actions `[50,14]`, serial memory `[1,4]` |

N/J parameters have 51 leaves and 3,353,433,872 BF16 elements. swap S has 56 leaves and 3,353,474,844 elements. cover S independently restored 56 leaves, 3,353,503,528 BF16 elements and 6,707,007,056 bytes; all values were finite and all shapes matched the model abstraction.

## 数据与 provenance

N 使用各任务的 14D robot-only sidecar；J/S 使用 semantic sidecar。数据 repo 均为相应 `*_demo_clean_state_shared_memory`，各 50 episodes。checkpoint copied binding manifest 与原 sidecar、norm 和 source metadata 均逐项校验。

- swap 语义字段为 `phase, initial_empty_tray, first_origin_tray`；battery 为 `phase`；cover 为 `phase, red_pos, green_pos, blue_pos`。
- J/S semantic 字段均为 `current_truth`，availability 均为 `availability_at_row`；robot action target 为 `action_at_row`。
- cover S semantic sidecar SHA-256：`573b0a5e02aec8f16cf5800348e883ab9951dc5d0f8febeabef931e5e47886ea`；robot-only sidecar：`c006bde76f7fe988090d0d9ab0e7d80b0d63fb8c540990e72377e3f7bfa9013b`；binding manifest：`1b2a189e5c078fec45855ddf4e8be1b9fbe10acd920770ae40b0342cc65f7517`；norm：`ca4cf5ffdf648b61bcfa63e40532ab285b1368ceff728efa53fafa60bd27e551`。

## 可复核最终收据

- N：`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z/validation/final20k/final20k_receipt.json`，SHA-256 `b8240d5689c8f38f9e7d5ff5e198ccf9410b54749b41f734e4941fc78ea3b774`。
- J：`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/final20k/final20k_receipt.json`，SHA-256 `01a4ad8016b888f5a322dee2225b41e4a7e0bb0afc5530ffd6c99c31646e8577`。
- swap S：`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/final20k_swap_s/swap_s_final20k_receipt.json`，SHA-256 `4b8dde2011c800127eb74b25b65000e2821d42000535e573789d710f8f3f5fc9`。
- cover S：`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/final20k_cover_s/cover_s_final20k_receipt.json`，SHA-256 `da1073d98b5712b4aea843b95ae601458d9b41eacbd6a40d8b5dad25bf5f2a8d`。

cover S 的独立目录未改动 N/J 或 swap S receipt。它保留 byte-for-byte 复制的恢复 validator、CPU/GPU restore 日志及哈希、GPU preflight 和 post-validation snapshot、训练日志哈希、cache 状态、source-read guard、正式启动回执哈希和独立 JSON 解析通过证据。训练发生在 GPU 7；恢复验证时原计划的 GPU 6 已被其他隔离作业占用，因此在有足够空闲显存的 GPU 2 上以 checkpoint-only policy 完成验证，收据记录了该验证运行时与 preflight。

## MAM 收尾

八条正式训练作业均已归档：swap N `443b3b93-57ba-425e-bbce-f4903fea33c1`、battery N `86f8ee1f-3d30-40f5-ba98-973b18232897`、cover N `1495a251-7d9e-4f68-8afc-0a7cee6360f9`、swap J `4ea24e85-d5f4-40cc-8409-44beb7237e8f`、battery J `a6eeac71-c0e2-4701-9530-521362c34083`、cover J `191b644f-f116-4f0b-a096-1dab6da41ade`、swap S `cb3e5246-fa74-40df-8325-0431f9587f73`、cover S `081f64c5-ae21-4062-b7ea-1dd281ddaa1f`。cover S PID `2646146` 已被 MAM 确认为 `stopped`／`process not found`，随后在 CPU/GPU 收据验证后归档。此前的数据传输登记也已归档，因此该任务当前共有 9 条 archived MAM jobs，没有未归档 job。

## 完成边界

- **Executor complete：**八条训练、正常完成核验、checkpoint-only CPU/GPU 恢复、四份最终收据和全部 MAM job 归档均已完成。
- **Manager acceptance pending：**科学结论、独立 review 验收和该 MAM task 是否归档仍由 Manager 决定；执行者没有归档 task 本身。
