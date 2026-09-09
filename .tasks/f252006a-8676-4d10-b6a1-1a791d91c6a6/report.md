task_revision: 18a99cbea563d961481f6f75fb0c03feef0b4e86

阶段交付（可独立 review）：openpi `f6327197459bf830c6b5d0b9ba5d643bc5e0cbd3`（`refactor: slim memory config API`），前置环境解阻 commit 为 `0dc120cf850e13a8fab71974f4f7e29778c13406`（`fix: lock openpi-client PyYAML dependency`）。

`f632719` 仅改 `packages/openpi-client` 的 memory 配置 helper 与定向测试：实现从 de79 的 1,480 行收敛到 961 行，移除重复解析/序列化包装和未使用兼容入口，同时保留 runtime/data 所需的 `load_memory_config`、`ResolvedMemoryConfig.to_dict/make_training_sample/compile_model_spec/validate_model_dimensions`、`EpisodeMemoryData`、`MemoryTrainingSample`、`MemoryModelSpec` 及 model spec 的 encode/decode helpers。新测试直接断言 dense 与 serial 的字段名、类别词表、initial IDs 共享同一 YAML 顺序。

给并行依赖方的签名提醒：`compile_model_spec(model_config=None)` 保留，新增可选关键字 `robot_dim`、`padded_dim`；`make_training_sample` 现在只接收 `EpisodeMemoryData`，不再接受裸 mapping。已删除 `ResolvedMemoryConfig.model_spec`、`validate_first_batch_protocol` 和 `MemoryModelSpec.to_dict/pi0_kwargs`；runtime 应在加载时调用 `compile_model_spec(...)`，checkpoint 只保存 `resolved.to_dict()`。

验证：`python -m pytest -q packages/openpi-client/src/openpi_client/memory_config_test.py` 为 11 passed；Ruff check、Ruff format check、`git diff --check` 均通过。此前 lock commit 只在根 `uv.lock` 的 openpi-client stanza 增加既有 `pyyaml>=6.0` 声明，`uv lock --check --offline` 通过。

仍在进行：论文 schema 最小 patch 与英文 P2 双臂 YAML 示例将作为独立后续 commit；未启动 GPU smoke 或正式训练。
