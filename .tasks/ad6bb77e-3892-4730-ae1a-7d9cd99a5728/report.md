task_revision: eb1c04d8b86a45825123ae32799598802fff5296

完成与未完成：

- CPU 训练集成已固定：full joint-dense、serial token、F=0 no-memory、真实 M+1 sidecar loader、robot-only norm / identity memory、P2 逐坐标 FM loss、`memory_input_ids` / `memory_prediction_ids` policy wire，以及 BF16 model-only checkpoint metadata 都已接入。Banach final CPU firstfull GO 已关闭 R1/R2。
- GPU1 full t+1 实际 base smoke 已通过：50/50 optimizer updates，最终保存目录按完成 update count 为 `50`。完整参数树从磁盘恢复为 51 个 BF16 叶子、3,353,433,872 个元素、6,706,867,744 字节；assets、metadata、params 完整。checkpoint-only policy factory 对非 initial `memory_input_ids=[1,2,2]` 成功恢复，输出机器人 `actions (50,14)` 与 `memory_prediction_ids (50,3)`。
- GPU1 serial lag30 实际 base smoke 已通过：50/50 optimizer updates，独立 serial-token/key-state head 目录同样为完成计数 `50`。完整参数树为 56 个 BF16 叶子、3,353,474,844 个元素、6,706,949,688 字节。checkpoint-only policy factory 对同一非 initial 输入输出 `actions (50,14)`、`memory_prediction_ids (1,3)`，且 `key_state_prediction (3,)` 与 action-conditioned serial head 同次调用返回。
- 两个实际训练均读取 `rearrange_blocks_demo_clean_state_shared_memory`，没有使用或 fallback `demo_clean`。GPU1 全部 smoke 和恢复已结束，可释放；Locke 已按 full gate 自行获准启动冻结 worktree 的正式 20k，本任务不会启动正式训练。
- put-back 已解除 GPU4/5 的唯一数据门：专用 `rmbench_put_back_block_robot` norm 已从 `put_back_block_demo_clean_state_shared_memory` 生成。两个 full 实际 loader（t+1、t+30）均读取该 asset，state/actions stats 都是 14 维；批次 state `(32,32)`、actions/weights `(32,50,32)`，末尾 padding weights 为零。两臂没有复用 rearrange stats。
- R3/R4 已独立固定为 `d49c1a1`：`source=initial` 不再要求不存在的 train mask，推理也不会消费非 initial cache；conditional decoder 保持公共 schema 的 first-match case 语义。
- wash full/serial 注册、全量 robot-only norm、真实 loader 与 checkpoint metadata roundtrip 已完成。Banach 对 `062d12a + 7a62920` 的增量复核发现旧 d10 tagged metadata 含已变为 `init=False` 的 runtime 字段；最小通用修复已固定为 `056bcc8`，等待同一 reviewer 增量复验。不会修改 Locke 的冻结运行树或自行启动 20k。

workspace、各库交付 commit：

- workspace: `/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi`
- openpi CPU integration: `ffa308d5485a2c8222d3e7735b08723c6e93a237`
- CLI repair: `5e3bfd6d46f13643c53271c1e3e1bc116dd4ff06`
- R1/R2 repair: `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50` (`fix: make memory checkpoint factories self-contained`)
- R3/R4 repair: `d49c1a1` (`fix: honor initial memory inputs and decoder case order`)；wash templates: `062d12a`；prior YAML boundary: `7a629204b4ab6d3cd113443c538837f8fb5f08d4`；当前 HEAD: `056bcc8`（旧 tagged/safe metadata 的 `init=False` runtime 字段通用恢复）。
- checkpoint dependency chain: `489359f -> 3d4fe31 -> cc706e37`; 此次按任务明确授权仅修改 `checkpoint_metadata.py` 的通用反序列化路径及配置回归测试。

验证结果与成果位置：

- R1/R2 定向测试：`3 passed, 11 deselected`；Banach fresh-process 复现：`4 passed, 4 deselected`。R1/R2 改动的 `ruff check`、`ruff format --check`、`git diff --check` 全部通过。
- full 训练日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_logs/full_tplus1_d10cc01.log`；full BF16 restore：`.../full_tplus1_d10cc01_dtype_restore.log`；full checkpoint-only wire：`.../full_tplus1_d10cc01_restore_wire.log`。
- full checkpoint：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50`。
- serial 训练日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_logs/serial_lag30_d10cc01.log`；serial BF16 restore：`.../serial_lag30_d10cc01_dtype_restore.log`；serial checkpoint-only wire：`.../serial_lag30_d10cc01_restore_wire.log`。
- serial checkpoint：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/serial_lag30_d10cc01/50`。
- put-back norm 命令：`CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -B scripts/compute_norm_stats.py --config-name=pi05_rmbench_put_back_block_full_t_plus_1`；产物：[norm_stats.json](/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi/assets/memory_v1/rmbench_put_back_block_robot/norm_stats.json)。两臂真实 loader 以本 task `.venv`、`num_workers=0` 各取一批并完成上述 shape/weight 断言。
- R3/R4 定向验证：`2 passed, 11 deselected`；Banach R4 重叠 case 复现：`1 passed, 7 deselected`；`ruff check`、`ruff format --check`、`git diff --check` 通过。

阶段更新（7a62920）：

- `7a629204b4ab6d3cd113443c538837f8fb5f08d4` 固定 checkpoint YAML 边界：`DataConfig.memory_adapter` 与 `memory_model_spec` 为运行时注入字段，不进入 YAML；真实 wash serial metadata roundtrip 验证 resolved `memory_config` 只保存一次。相关 `arx_policy/config/config_memory/memory_data` 回归共 `23 passed`。
- put-back 在当前 HEAD 以实际共享根 `HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot` 重新取样。t+1/t+30 各一批：asset `rmbench_put_back_block_robot`、robot_dim 14、state `(32,32)`、actions/weights `(32,50,32)`，已用 memory 宽度为 23，尾部 padding 的非零 weight 数均为 0。简短日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_logs/put_back_block_loader_smoke_7a62920.log`。GPU4/5 可据此放行。
- wash v3 全量 robot-only norm 已成功完成并归档 MAM job `396366a5-71b0-4185-82ee-a3963b4b004b`：4,490 batches、约 5 分钟、CPU-only。日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/cpu_norm_logs/wash_cup_s2m_robot_norm_7a62920.log`；产物：`assets/memory_v1/x1pro_wash_cup_s2m_robot/norm_stats.json`，state/actions 的 mean/std/q01/q99 均为 14 维。
- 遵照 e6908de7 的短期交接，两个已验收的 50-step checkpoint 与其日志仍留在本 task workspace，仅供新 schema metadata/入口核验，未清理、未复制、未占用 GPU。

阶段更新（wash v3 实际联通）：

- 以 `HF_LEROBOT_HOME=/mnt/public/xcj/Projects/openpi/data/lerobot`、本 task `.venv` 和 `num_workers=0` 从已保存的 checkpoint metadata 恢复两个配置后，各取真实第一批。两臂均来自 `wash_cup_x1pro_s2m_memory_v1/all_172_15hz_s2m_master_v3_source_frame_aligned`，robot-only norm 宽度为 14，完整模型 batch 的 state `(32,32)`、actions/weights `(32,50,32)`。
- full (`joint_dense`) 的 memory 终止宽度为 20，padding weight 非零数为 0；首批有 212 个 memory-zero 时间格，212 个同格仍有 robot loss，验证缺 phase GT 只屏蔽 memory 监督。
- serial (`serial_token`) 的 `key_state_input_ids` 和 target IDs 都是 `(32,1)`；首批 8 条 target mask 为 false，8 条仍有 robot loss；非机器人 action weight 非零数为 0，memory supervision 走 token head。
- 两个实际 `checkpoint_metadata.save → load_train_config → create_data_config(training=False)` roundtrip 都只写一份 `memory_config`，不写 `memory_adapter`/`memory_model_spec`，且 inference factory 未读取训练 norm stats。完整可复核日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/cpu_norm_logs/wash_cup_loader_roundtrip_7a62920.log`。
- 两份 50-step checkpoint 及简短日志仍按 e6908de7 交接要求保留；未占用 GPU，等待 Manager 确认后统一清理。

阶段更新（09:35 metadata P1 修复，`056bcc8`）：

- Banach `1efc1294` 复现的两个 d10 50-step metadata 都含 `DataConfig.memory_adapter: null` 和 `memory_model_spec: null`，而当前 dataclass 已将二者设为 `init=False`，原 `tyro.extras.from_yaml` 因此直接报 `unexpected keyword argument 'memory_adapter'`。
- `checkpoint_metadata.load_train_config` 现在按当前配置 dataclass 的 `field.init` 自动清除 tagged YAML 对应节点中的非构造字段；safe-YAML 的 template 恢复同样跳过 `init=False` 字段。没有按 checkpoint 版本或字段名分支；runtime adapter/spec 仍由 `create_data_config` 从唯一 resolved `TrainConfig.memory_config` 重建。
- fresh Python process 已只读验证旧 full checkpoint `.../gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50`（`joint_dense`）及旧 serial checkpoint `.../pi05_rmbench_rearrange_blocks_serial_lag30/serial_lag30_d10cc01/50`（`serial_token`）：均重建 14-dim robot / 32-dim padded runtime adapter、inference norm 仍为 `None`，并断言源 YAML byte 内容未改变。新 wash full/serial 均完成真实 `checkpoint_metadata.save -> load_train_config -> create_data_config(training=False)` roundtrip，YAML 只含一份 resolved `memory_config`，不含 runtime 字段。日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/cpu_norm_logs/checkpoint_metadata_compat_fresh_eb1c04d.log`。
- 验证：`ruff check`、`ruff format --check`、`git diff --check` 通过；`pytest -q src/openpi/policies/arx_policy_test.py src/openpi/training/config_test.py src/openpi/training/config_memory_test.py src/openpi/training/memory_data_test.py src/openpi/training/checkpoint_metadata_test.py` 为 `29 passed in 72.34s`。日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/cpu_norm_logs/checkpoint_metadata_regression_eb1c04d.log`。
- 未改写两份已有 checkpoint/metadata，未改八路正式运行的冻结源码，未占用 GPU；两份 50-step checkpoint/日志继续为 e6908de7 保留。剩余仅为 Banach 的增量复验。
