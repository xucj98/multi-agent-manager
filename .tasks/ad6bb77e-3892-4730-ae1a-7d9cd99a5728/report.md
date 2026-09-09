task_revision: 74e7d082839b0e00674bb9a76b580b18708c6f5f

完成与未完成：

- CPU 训练集成已固定：full joint-dense、serial token、F=0 no-memory、真实 M+1 sidecar loader、robot-only norm / identity memory、P2 逐坐标 FM loss、`memory_input_ids` / `memory_prediction_ids` policy wire，以及 BF16 model-only checkpoint metadata 都已接入。
- R1/R2 已由本次独立小提交修复。`TrainConfig.create_data_config(training=False)` 现在只构造 transforms，不读取原训练 norm；policy factory 随后从 checkpoint `assets/<asset_id>` 加载统计。serial tagged YAML 的 decoder rule 完整性验证已移到完整 YAML 构造后的 runtime factory / model create，真实 serial checkpoint metadata roundtrip 成功。
- Banach 的其余 CPU review 已在 `fb9c495` 报告通过真实 data 窗口、serial 实际条件/wire 与 50/20k update 计数；Pascal 的真实跨 wire 检查 7 项通过。R3（aux initial mask）与 R4（非默认 conditional decoder overlap 的 first-match 语义）均不阻塞首批 default-argmax full/serial。
- 尚未启动 GPU1 训练。下一步按顺序运行 full t+1、serial lag30 各 50 update，验证实际 base 加载、BF16 model-only 保存到完成计数目录 `50`、checkpoint-only 恢复与各自 wire keys/shapes；no-memory 无需第三次 50-step。正式 20k 仍等待 Manager 通知。
- put-back 的 14 维 robot-only norm 不复用 rearrange；在其正式 run 前生成并以真实归一化 loader 验证。wash 继续暂停至数据验收。

workspace、各库交付 commit：

- workspace: `/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi`
- openpi CPU integration: `ffa308d5485a2c8222d3e7735b08723c6e93a237`
- CLI repair: `5e3bfd6d46f13643c53271c1e3e1bc116dd4ff06`
- R1/R2 repair: `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50` (`fix: make memory checkpoint factories self-contained`)
- checkpoint dependency chain remains `489359f -> 3d4fe31 -> cc706e37`; this patch does not modify its owner files.

验证结果与成果位置：

- `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu ... .venv/bin/python -B -m pytest -q -p no:cacheprovider src/openpi/training/config_test.py src/openpi/training/memory_data_test.py -k 'checkpoint_inference_factory_skips_source_norm_stats or tagged_serial_memory_checkpoint_roundtrip_waits_for_decoder_mappings or train_config_resolves_memory_once_and_rebuilds_checkpoint_transforms'`：`3 passed, 11 deselected`。
- Banach 的同一实际复现脚本仅跑 R1/R2：`... combined_review_test.py -k 'real_train_config_metadata_roundtrip or fresh_process_inference_factory_never_reads_training_norm'`：`4 passed, 4 deselected`；其中包含 fresh-process 禁止读取训练 norm/dataset/sidecar/YAML 的检查。
- 本次四个改动文件的 `ruff check`、`ruff format --check` 和 `git diff --check` 均通过；工作树在 `d10cc01` 后干净。
- 已有 CPU 固定阶段的真实 tokenizer 条件、P2 loss/gradient、metadata 完整继承、sim loader smoke 与 `scripts/train_test.py` 结果保持有效；本次未重复无关 tokenizer/P2 测试。
