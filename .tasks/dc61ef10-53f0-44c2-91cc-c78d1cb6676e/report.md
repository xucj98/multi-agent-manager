task_revision: 05de246207acecabc5ac42e2b0b3432927450aa3

完成与未完成：

- 完成 BF16/FP32 推理参数导出：`save_state` 直接读取 `config.save_dtype`，仅转换拆出的浮点 params 副本，整数和布尔叶子不变，训练内 FP32 params/优化器不变。`save_full_state=False` 的真实 Orbax tiny checkpoint 只含 `params`、`assets`、`metadata`，没有 `train_state`。
- 完成 checkpoint 自包含路径：checkpoint-only loader 先下载再读取 metadata；policy 直接调用训练侧约定的 `create_data_config(training=False)`，并将唯一 `TrainConfig.memory_config` 对象运行时透传到 server metadata。没有复制 memory transform、model spec 或第二份持久化 metadata。
- 修复 Tyro YAML 顶部注释后才出现 `!dataclass` 标签时被误判为 safe YAML 的恢复问题；safe-YAML 的旧模板恢复测试仍通过。
- 已按 Manager 指定 cherry-pick core 修复 `7acff60`。训练 owner 的真实 factory 提交尚未发布，故未把临时 CPU 契约测试冒充为真实链路验收。其合入后需复跑并确认 `Normalize → AttachMemoryAfterNormalize → TokenizePrompt`，输出先 `MemoryOutputs` 再 robot-only `Unnormalize`；不需要也未启动 GPU 或 6B/20k 任务。

workspace、各库交付 commit：

- OpenPI workspace: `/mnt/public/xcj/Projects/workspace/dc61ef10-53f0-44c2-91cc-c78d1cb6676e/openpi`
- 依赖 core 修复: `7acff60d561ac009d2fc57ddb3784c053db15546`
- 本任务交付: `489359f8655c0a0af35447caa71f4db702fefabe`（6 files，318 additions / 7 deletions；仅 checkpoints、checkpoint_metadata、policy_config 及定向 tests）

验证结果与成果位置：

- `JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q src/openpi/training/checkpoints_test.py src/openpi/training/checkpoint_metadata_test.py src/openpi/policies/policy_test.py::test_policy_uses_inference_data_config_and_runtime_memory_metadata src/openpi/policies/policy_test.py::test_runtime_metadata_keeps_legacy_policy_metadata_without_memory_config src/openpi/policies/policy_test.py::test_checkpoint_only_policy_loader_downloads_before_reading_metadata src/openpi/training/config_test.py`：11 passed。
- `JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q packages/openpi-client/src/openpi_client/memory_config_test.py`：18 passed。
- `ruff check`、`ruff format --check` 与 `git diff --check` 通过；worktree 无未提交文件。
