# swap / cover S 20k 最终 checkpoint 独立只读审计

## 审计意见

**`pass_with_scope_limits`。** 两条被指定的 S run 均有相互一致的固定 final receipt、20k 训练完成日志、model-only checkpoint 拓扑、训练合同、数据 provenance、既有的 checkpoint-only CPU/GPU 恢复记录和已归档 MAM job。没有发现证据不一致或缺失的阻断项。

训练身份是 clean commit `34002dce65962734c59725a0f6d982ae2c438a2d`，不是 MAM review 栏中自动列出的开发 HEAD `867aa05e…`。独立 worktree 位于 `/mnt/public/xcj/Projects/workspace/82d5c109-365f-4071-ac80-f7e1754575e8/openpi`，复核结束时仍 clean 且 HEAD 为该训练 commit。

可复核证据包位于 `evidence/s_final20k/`。其 `receipt.json` 的 SHA-256 是 `1188fd7ca55cde602c20804473fd0f7055180c06439cd71042167df6e177e840`；`collector_manifest.json` 的 SHA-256 是 `be08e7c31fda77910ffc535d7452d0b56c1895b2ccfe8b08cc2cdcae5b72ad93`。运行 `python -B evidence/s_final20k/audit_s_final20k.py` 可重新执行同一只读审计。

## 两条 checkpoint 的核验结果

| Run | checkpoint | 训练 GPU | Step 20k 最终 loss / grad / param | 既有 CPU 恢复 | 既有 GPU checkpoint-only 输出 |
| --- | --- | ---: | --- | --- | --- |
| swap S | `pi05_rmbench_swap_blocks_serial_lag30/memory20k_34002dce_nocmdbuf_swap_blocks_s_s0/20000` | 6 | `0.0066 / 0.2260 / 1806.1981` | 56 BF16 leaves，3,353,474,844 elements，6,706,949,688 bytes，finite | actions `[50,14]`；serial memory IDs `[1,3]`，finite |
| cover S | `pi05_rmbench_cover_blocks_serial_lag30/memory20k_34002dce_nocmdbuf_cover_blocks_s_s0/20000` | 7 | `0.0049 / 0.1810 / 1806.5916` | 56 BF16 leaves，3,353,503,528 elements，6,707,007,056 bytes，finite | actions `[50,14]`；serial memory IDs `[1,4]`，finite |

两份固定原件和哈希已重验：

- swap：`validation/final20k_swap_s/swap_s_final20k_receipt.json`，`4b8dde2011c800127eb74b25b65000e2821d42000535e573789d710f8f3f5fc9`。
- cover：`validation/final20k_cover_s/cover_s_final20k_receipt.json`，`da1073d98b5712b4aea843b95ae601458d9b41eacbd6a40d8b5dad25bf5f2a8d`。

两份训练日志均含 `Step 20000`、`Finished saving checkpoint (finalized tmp dir)`、`No errors found in background save thread` 和 `Done waiting for Save Finalize thread`，且未含所查的 traceback、fatal Python error、segmentation fault 或 `Check failed:` marker。顶层仅为 `_CHECKPOINT_METADATA`、`assets`、`metadata`、`params`，无 `train_state`；审计只枚举该层，未进入、复制或重哈希 `params/**`。

这些 loss 仅用于确认记录的训练完成状态，与算法效果、仿真表现或评测结论无关；本审计没有产生任何评测结果。

## 合同与数据 provenance

两条 run 的保存 train config 以 `yaml.compose` 解析（不导入 OpenPI），确认 seed 0、batch 32、H50/K30、20,000 steps、`save_interval=20000`、BF16 model-only、`resume: false`、`memory_config_path: null`，以及从 `/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base/params` 独立初始化并使用 `missing_regex: key_state_token/.*`。过滤后的 formal-start 回执明确写明 `pi05_base (independent new run; not resumed from smoke)`。

- swap 的 serial 字段顺序为 `phase, initial_empty_tray, first_origin_tray`，模型 token cardinalities 为 `[4,4,4]`。
- cover 的字段顺序为 `phase, red_pos, green_pos, blue_pos`，模型 token cardinalities 为 `[6,4,4,4]`。
- 两者均固定 `previous.min = previous.max = 30`、`representation.kind = serial_token`；binding manifest 中 semantic series 为 `current_truth`、availability 为 `availability_at_row`、robot target 为 `action_at_row`，并确认 robot state slice 是 14D。
- checkpoint 内 dataset metadata 均指向相应 `*_demo_clean_state_shared_memory` repo、50 episodes 和 `upstream/dataset_0`。

原 sidecar 内容没有复制到证据包，只重验其 hash；checkpoint 中 copied binding manifest 与 source binding manifest、copied norm 与 source norm 均逐字节相同：

| Run | semantic sidecar | robot-only sidecar | binding manifest | norm |
| --- | --- | --- | --- | --- |
| swap | `ba697b8c93dd3034d93ae2032efce22ea7b496023abb0a6d8dd2e5d8defef5c1` | `3736016dfcc3192134e3af196d30995d1cbbc0c29a5c54ab8217ad2d6c22a0e6` | `777e3cecb7299dd9ac0798e37427caeb489da4610d00b1d91409239cc3119bc0` | `acb30919ff4be931da9c62173959971f9944bfc6d304ee80ab09448d79f6b336` |
| cover | `573b0a5e02aec8f16cf5800348e883ab9951dc5d0f8febeabef931e5e47886ea` | `c006bde76f7fe988090d0d9ab0e7d80b0d63fb8c540990e72377e3f7bfa9013b` | `1b2a189e5c078fec45855ddf4e8be1b9fbe10acd920770ae40b0342cc65f7517` | `ca4cf5ffdf648b61bcfa63e40532ab285b1368ceff728efa53fafa60bd27e551` |

缓存合同也一致：`HF_LEROBOT_HOME` 为 unset，root cache symlink 为 `/mnt/public/xcj/cache`。启动回执和 launcher 记录 `XLA_FLAGS=--xla_gpu_enable_command_buffer=`；checkpoint 的 `command.txt` 因现有 allowlist 未记录该变量，这与回执相符，不构成缺陷。

## checkpoint-only 证据与设备 provenance

记录的 CPU 和 GPU 恢复 JSON 与 final receipt 逐字段一致。GPU 输出均包含 `actions`、`key_state_logits`、`key_state_prediction`、`memory_prediction_ids`、`policy_timing`，并记录为 finite。它们是既有恢复执行的收据，本任务没有重新加载模型、重做多 GB CPU restore 或启动 GPU。

cover 的训练 GPU 是 **7**。cover final receipt 另外记录了 checkpoint-only 验证运行时的 physical GPU **2**、`CUDA_VISIBLE_DEVICES=2`、CUDA/JAX/XLA 环境和 preflight SHA-256 `190c0f4f990368a1fea9716111fa2e5d882a8bf36378d87529ed6e9f71f5fb4f`。这是回执绑定的历史记录；GPU restore JSON 本身没有 physical-GPU 字段，不能把 JSON 单独当作 GPU 2 的设备 provenance。swap 的 final receipt 没有单独的 GPU-validation-runtime 字段，不能据此补写验证 GPU 结论。

两份 validator 当前 byte-identical，SHA-256 为 `efe850fb6a998d568e7dfc69b77df0b9777e69ec06079319b1a333d418d907ac`。静态检查确认其 `sys.addaudithook` 仅处理 `open` event，允许 checkpoint subtree，并拒绝 LeRobot cache、`pi05_base`、训练 data/assets、原 worktree data/assets 和 RMBench memory YAML 的固定路径。冻结源码还显示 checkpoint policy factory 使用保存的 config、checkpoint `params` 和 checkpoint `assets`，调用 `create_data_config(training=False)`；该分支文档说明不读取 source norm、LeRobot dataset、labels 或 sidecars，而 `_load_sidecars` 位于训练 `MemoryLeRobotDataset` 路径。

这说明的是既有 validator 的 source-read guard 边界和冻结源码路径。该 guard 是 Python 审计 hook，不是 filesystem isolation；静态证据和既有日志不替代新的运行时隔离实验。

## MAM 与范围

S 作业快照已保存于证据包：swap `cb3e5246-fa74-40df-8325-0431f9587f73`（GPU 6、PID 2646145）和 cover `081f64c5-ae21-4062-b7ea-1dd281ddaa1f`（GPU 7、PID 2646146），状态均为 `archived`。没有查询或重审 N/J job，也没有归档源任务。

证据阻断项：**无**。保留的范围限制是：不重跑训练、仿真、评测、CPU/GPU restore 或模型加载；不读取 checkpoint 参数内容；不复制原 sidecar 内容；不把训练 loss 或恢复 shape 当作算法性能结论；GPU 设备 provenance 仅按上述已记录字段陈述。
