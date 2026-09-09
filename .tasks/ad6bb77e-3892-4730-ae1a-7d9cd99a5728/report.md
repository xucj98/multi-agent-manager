task_revision: ae0a99ff3d24ce9c147973910c82c0b63160b14e

完成与未完成：

- CPU 可审查训练实现已固定：full joint-dense、serial token 和 F=0 no-memory 共用 resolved `TrainConfig.memory_config`、真实 sidecar loader、identity memory normalization、逐坐标 FM 权重、policy 的 `memory_input_ids` / `memory_prediction_ids` wire，以及 checkpoint-only transform factory 均已接入。
- full memory 在 robot Normalize 后、`TokenizePrompt` 前编码；测试以同一 robot/image/prompt 的不同 memory ID 验证 tokenized prompt 不同。dense 输出先解码 memory ID、再裁成 14 维机器人 actions；serial 输出返回实际用于动作条件化的 ID。
- P2 loss 通过真实 `Pi0.compute_loss` 覆盖 lambda=0.25、非单位 valid-mean、padding 和全 invalid 梯度；memory lambda 仅在 dense 坐标乘一次，机器人权重保持 1。
- `scripts/train.py` 已按完成 optimizer update 数保存目录：50 step 为 `50`、20k 为 `20000`，不多训练一步。model-only 保存拒绝 `resume=True`，避免伪装成可恢复 optimizer 的 checkpoint。
- shared rearrange robot-only norm stats 正在本任务独立环境生成；完成后将做 full/serial/no-memory 的非跳过统计真实 loader smoke。随后进行 GPU1 50-step base 加载、BF16 保存、checkpoint-only 恢复和 runtime 跨边界联通；未启动 20k。

workspace、各库交付 commit：

- workspace: `/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi`
- openpi CPU commit: `ffa308d5485a2c8222d3e7735b08723c6e93a237` (`feat: integrate memory v1 training pipeline`)
- commit 基于已接入的 checkpoint 链 `489359f -> 3d4fe31 -> cc706e37`。

验证结果与成果位置：

- `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q src/openpi/training/config_memory_test.py src/openpi/training/memory_data_test.py src/openpi/models/pi0_memory_test.py examples/rmbench/test_rmbench_memory_adapter.py src/openpi/training/checkpoint_metadata_test.py src/openpi/training/checkpoints_test.py src/openpi/policies/policy_test.py -k 'not infer and not broker'`：30 passed，3 deselected。
- `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q scripts/train_test.py`：1 passed；实际保存/恢复目录为 `2`、`4`。
- 固定提交前 `ruff check`、`ruff format --check`（本次文件）和 `git diff --check` 均通过。
- 真实 sim loader 的 `skip_norm_stats=True` smoke 已覆盖 full P2、serial lag30、no-memory，batch=1 的 action/state/weight 均为 `(1, 50, 32)` / `(1, 32)` / `(1, 50, 32)`；serial 额外有 input/target IDs `(1, 3)`。
- 正在生成的共享资产目标为 `assets/memory_v1/rmbench_rearrange_blocks_robot`，仅 state/actions 各 14 维；one-hot memory 不参与统计。
- base 模型参数验收按完整树/shape/dtype 和实际恢复执行：3,353,433,872 个元素，BF16 裸权重约 6.71 GB；不以旧的 12 GB 估算作为固定文件大小目标。

剩余与预计：

- norm stats 完成后约 15 分钟内完成非跳过 loader smoke 和 report 更新；GPU1 50-step smoke 在 CPU/review 之外继续，不阻塞本 CPU commit。
- runtime owner 的新 `MemoryContext` schema 增量到位后，补真实 transform → context 的 K30/multi-field/no-memory CPU 联通；wash 保持暂停，直至数据验收。
