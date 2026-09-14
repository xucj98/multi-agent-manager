# 第一波 N/J 与 swap S 正式 20k 已完成；仅 cover S 仍在运行

## 当前状态（2026-09-14 08:39 UTC）

- 七条已停止的 N/J/swap S 训练均以**达到请求的 step 20,000 并完成 Orbax finalization**结束；每个日志都有有限的 `Step 20000` 指标、`Finished saving checkpoint`、`No errors found in background save thread` 与 `Done waiting for Save Finalize thread`，没有 fatal marker。这是正常完成，不是异常中断。
- 七个 checkpoint 都是 model-only：目录项严格为 `_CHECKPOINT_METADATA`、`assets`、`metadata`、`params`，无 `train_state`。
- 每项均通过 CPU 完整参数恢复和 GPU checkpoint-only policy 恢复；N/J 为 51 leaves、3,353,433,872 elements，swap S 为 56 leaves、3,353,474,844 elements，全部 BF16/finite/shape 完整。恢复 guard 拒绝读取训练 dataset、pi05_base、原 sidecar/assets 与原 YAML。
- 七个已完成对应 MAM job 已归档。没有重训、没有补 seed、没有拼接 checkpoint，也没有设置 `HF_LEROBOT_HOME`。
- 仅 cover S 仍由 MAM 跟踪为 running，未触碰。后续由 MAM 停止通知唤醒后再收尾。

## 代码、数据与 20k checkpoint 清单

N 的正式执行树为 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/loader/openpi`，commit `5835fa04055d520e418cc1448c1bd58fa1e665cb`。N 根目录为 `/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z`。

| 项目 | 20k checkpoint（相对 N 根） | 20k 指标：loss / grad / param | robot-only sidecar SHA-256 | norm SHA-256 | GPU restore |
| --- | --- | ---: | --- | --- | --- |
| swap N | `pi05_rmbench_swap_blocks_no_memory/memory20k_5835fa0_nocmdbuf_swap_blocks_n_s0/20000` | 0.0017 / 0.0469 / 1805.2899 | `3736016d…6c22a0e6` | `acb30919…79f6b336` | finite actions `[50,14]` |
| battery N | `pi05_rmbench_battery_try_no_memory/memory20k_5835fa0_nocmdbuf_battery_try_n_s0/20000` | 0.0007 / 0.0233 / 1804.6187 | `2d4130e4…c781d8e27` | `5ebaa98a…bbb0be89` | finite actions `[50,14]` |
| cover N | `pi05_rmbench_cover_blocks_no_memory/memory20k_5835fa0_nocmdbuf_cover_blocks_n_s0/20000` | 0.0012 / 0.0249 / 1805.1487 | `c006bde7…f7bfa9013b` | `ca4cf5ff…bd27e551` | finite actions `[50,14]` |

N 的数据 repo 均为对应的 `*_demo_clean_state_shared_memory`、50 episodes；checkpoint copied binding manifest 证明 sidecar 为 `robot_only/episode_memory.json`、只含 `robot_action_target: action_at_row`，并保留 converted/source metadata。每个 copied norm 与 `/mnt/public/xcj/Projects/openpi/assets/memory_v1/rmbench_*_robot/norm_stats.json` 的已验收哈希一致。

J/S 的正式执行树为 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/js/openpi`，commit `34002dce65962734c59725a0f6d982ae2c438a2d`。J 根目录为 `/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z`。

| 项目 | 20k checkpoint（相对 J 根） | 20k 指标：loss / grad / param | semantic sidecar SHA-256 | norm SHA-256 | GPU restore |
| --- | --- | ---: | --- | --- | --- |
| swap J | `pi05_rmbench_swap_blocks_full_t_plus_1/memory20k_34002dce_nocmdbuf_swap_blocks_j_s0/20000` | 0.0014 / 0.0497 / 1805.1434 | `ba697b8c…defef5c1` | `acb30919…79f6b336` | actions `[50,14]`, memory `[50,3]` |
| swap S | `pi05_rmbench_swap_blocks_serial_lag30/memory20k_34002dce_nocmdbuf_swap_blocks_s_s0/20000` | 0.0066 / 0.2260 / 1806.1981 | `ba697b8c…defef5c1` | `acb30919…79f6b336` | actions `[50,14]`, serial memory `[1,3]` |
| battery J | `pi05_rmbench_battery_try_full_t_plus_1/memory20k_34002dce_nocmdbuf_battery_try_j_s0/20000` | 0.0008 / 0.0286 / 1804.6823 | `75bf1881…5de69cb` | `5ebaa98a…bbb0be89` | actions `[50,14]`, memory `[50,1]` |
| cover J | `pi05_rmbench_cover_blocks_full_t_plus_1/memory20k_34002dce_nocmdbuf_cover_blocks_j_s0/20000` | 0.0015 / 0.0470 / 1805.2087 | `573b0a5e…5e47886ea` | `ca4cf5ff…bd27e551` | actions `[50,14]`, memory `[50,4]` |

J 的 checkpoint copied binding manifest 与正式启动回执中记录的 source manifest/semantic sidecar 哈希完全一致；字段和语义分别为 swap `phase, initial_empty_tray, first_origin_tray`，battery `phase`，cover `phase, red_pos, green_pos, blue_pos`，且每个语义字段为 `current_truth`、availability 为 `availability_at_row`。三个 J formal run 与 swap S 都从 pi05_base 独立初始化，未从 smoke checkpoint 续训。swap S 使用同一 semantic sidecar、serial_token schema `swap_blocks_serial_lag30`，其独立 receipt 对 56-leaf 参数树及 `[1,3]` serial memory 输出作了专门断言。

## 可复核产物

- N 最终回执：`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z/validation/final20k/final20k_receipt.json`，SHA-256 `b8240d5689c8f38f9e7d5ff5e198ccf9410b54749b41f734e4941fc78ea3b774`。
- J 最终回执：`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/final20k/final20k_receipt.json`，SHA-256 `01a4ad8016b888f5a322dee2225b41e4a7e0bb0afc5530ffd6c99c31646e8577`。
- swap S 独立回执：`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/final20k_swap_s/swap_s_final20k_receipt.json`，SHA-256 `4b8dde2011c800127eb74b25b65000e2821d42000535e573789d710f8f3f5fc9`。该目录独立于既有 `validation/final20k/`，未覆盖 N/J receipt。
- 每份 receipt 包含最终训练日志 SHA、checkpoint copied norm/manifest/source metadata、CPU/GPU restore JSON 与日志 SHA、正式启动合同、commit、default cache 与 GPU pmon snapshot。验证脚本及日志位于各自的 `validation/final20k*/` 目录。
- 运行合同保持 seed 0、batch 32、H50/K30、model-only BF16、`/root/.cache -> /mnt/public/xcj/cache`、`HF_LEROBOT_HOME` unset；实际 CUDA 兼容项 `XLA_FLAGS=--xla_gpu_enable_command_buffer=` 保存在 launcher、pids/启动回执中，checkpoint `command.txt` 的既有 allowlist 不声称保存它。

## MAM 收尾与 GPU 状态

已归档：swap N `443b3b93-57ba-425e-bbce-f4903fea33c1`、battery N `86f8ee1f-3d30-40f5-ba98-973b18232897`、cover N `1495a251-7d9e-4f68-8afc-0a7cee6360f9`、swap J `4ea24e85-d5f4-40cc-8409-44beb7237e8f`、battery J `a6eeac71-c0e2-4701-9530-521362c34083`、cover J `191b644f-f116-4f0b-a096-1dab6da41ade`、swap S `cb3e5246-fa74-40df-8325-0431f9587f73`。

wuwen-1 在 swap S receipt 的 final GPU snapshot 中 GPU 0–6 没有本 VM 的已完成 N/J/swap-S process；GPU 4/5/6 的本 VM 视图已释放。仅 GPU 7 上 PID 2646146（cover S）仍在运行。GPU 0–3 的全局显存读数来自隔离 VM，不视为本任务进程或可用性声明。

MAM 当前仅保留 cover S `081f64c5-ae21-4062-b7ea-1dd281ddaa1f` 一个 running job；不主动轮询，等待 MAM 后续停止通知。

## Manager 可评清单

1. 检查两个 `final20k_receipt.json` 的 commit、20k metrics、model-only entries、norm/manifest/sidecar 哈希及 CPU/GPU restore 输出。
2. 从 receipt 引用的训练日志确认各条 `Step 20000` 和成功 finalization；从 checkpoint 路径检查固定的 `20000` 目录。
3. 检查 MAM archive note 与七个 archived job 的 PID identity；确认仅 cover S job 仍为 running。
4. cover S 结束后单独按同一合同验收，不将其结果混入已完成的 N/J/swap-S 结果。
