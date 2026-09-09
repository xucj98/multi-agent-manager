task_revision: 031c9a37ba55eeff6e66513235d6ed8d0ece8d9e

完成与未完成：

- CPU 训练集成已固定：full joint-dense、serial token、F=0 no-memory、真实 M+1 sidecar loader、robot-only norm / identity memory、P2 逐坐标 FM loss、`memory_input_ids` / `memory_prediction_ids` policy wire，以及 BF16 model-only checkpoint metadata 都已接入。
- R1/R2 已由 `d10cc01` 修复并获 Banach final CPU firstfull GO：`TrainConfig.create_data_config(training=False)` 只构造 transforms，不读原训练 norm；policy factory 从 checkpoint `assets/<asset_id>` 加载统计。serial tagged YAML decoder rule 验证已移至完整 YAML 构造后使用处。
- GPU1 full t+1 的实际 base 50-step smoke 已于 2026-09-10 07:43 CST 启动，PID `2156723`，物理 GPU1（`CUDA_VISIBLE_DEVICES=1`）。截至 07:49 已完成 3/50 update，已实际加载 `demo_clean_state` 的 20,103-row rearrange 数据、独立 14 维 robot norm 和 pi05 base。日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_logs/full_tplus1_d10cc01.log`；checkpoint 根：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints`。当前编译后速率预计 full 在约 08:10–08:20 CST 到达 `50` 保存点；完成后立即在同一 GPU1 顺序运行 serial lag30 50-step。
- full/serial 均需验证最终目录为完成 update count `50`、BF16 model-only params、完整 assets/metadata、仅 checkpoint 恢复以及 policy wire。no-memory 不需第三个 GPU smoke。正式 20k 由 Locke 的 `e7e5ac54` 冻结 d10 worktree 负责，本任务不会启动。
- R3（aux source=initial 无 mask）与 R4（非默认 conditional decoder overlap 的 first-match 语义）在 GPU gate 后以独立小提交处理。wash v3 的最终数据检查后，在本树补 full/serial 训练注册与真实 loader/config roundtrip；put-back 正式前另生成 14 维 robot-only norm，不复用 rearrange。

workspace、各库交付 commit：

- workspace: `/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi`
- openpi CPU integration: `ffa308d5485a2c8222d3e7735b08723c6e93a237`
- CLI repair: `5e3bfd6d46f13643c53271c1e3e1bc116dd4ff06`
- R1/R2 repair: `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50` (`fix: make memory checkpoint factories self-contained`)
- checkpoint dependency chain: `489359f -> 3d4fe31 -> cc706e37`; this task does not modify its owner files.

验证结果与成果位置：

- `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu ... .venv/bin/python -B -m pytest -q -p no:cacheprovider src/openpi/training/config_test.py src/openpi/training/memory_data_test.py -k 'checkpoint_inference_factory_skips_source_norm_stats or tagged_serial_memory_checkpoint_roundtrip_waits_for_decoder_mappings or train_config_resolves_memory_once_and_rebuilds_checkpoint_transforms'`：`3 passed, 11 deselected`。
- Banach 的实际复现脚本仅跑 R1/R2：`... combined_review_test.py -k 'real_train_config_metadata_roundtrip or fresh_process_inference_factory_never_reads_training_norm'`：`4 passed, 4 deselected`；其中包含 fresh-process 禁止读取训练 norm/dataset/sidecar/YAML 的检查。
- 本次四个 R1/R2 改动文件的 `ruff check`、`ruff format --check` 和 `git diff --check` 均通过；GPU 启动前工作树在 `d10cc01` 后干净。
- GPU full 已实际建立 `(32,32)` state、`(32,200)` tokenized prompt、`(32,50,32)` action/weight batch，恢复 pi05 base 并开始 optimizer updates；最终 GPU/save/restore/wire 结果待 50-step 完成后追加。
