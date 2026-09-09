task_revision: 8914a4d2aa3c43ad5e995a527aa76cf0152e2f44

# 阶段结论：489359f checkpoint 保存/加载增量

结论：**阻塞，当前不能批准新 20k 实验开跑。** `489359f8655c0a0af35447caa71f4db702fefabe` 的参数副本 cast、model-only Orbax 目录和 metadata YAML 小型 CPU 覆盖均可通过；但它已无条件依赖尚未送达的训练接口。真实 `TrainConfig` 不含 `save_dtype`、`memory_config` 或 `create_data_config`，所以实际保存和 checkpoint-only policy 加载都立即失败。该依赖与任务约定的“训练增量随后固定提交”一致；固定 commit 合入本 reviewer worktree 后必须作为完整 review 的首项复验。

完成与未完成：

- 已完成：只读审查 `489359f` 的 `checkpoints.py`、`checkpoint_metadata.py`、`policy_config.py` 及新增测试。`_cast_floating_params` 对浮点 inference params 生成 BF16/FP32 副本，整数/布尔叶子保持 dtype；`save_full_state=False` 的 tiny Orbax 产物含 `params`、norm assets、metadata，且无 `train_state`。实际 `tyro` metadata roundtrip 得到 `debug/FakeDataConfig/Pi0Config`；旧 safe-YAML 覆盖仍通过。
- 阻塞 B1（跨增量接口未接入）：`src/openpi/training/checkpoints.py:100` 无条件读取 `config.save_dtype`，而当前 `TrainConfig` 定义中没有此字段。以真实 `config.get_config("debug")` 调用 `save_state` 的结果为 `AttributeError: 'TrainConfig' object has no attribute 'save_dtype'`，训练首次保存会失败。
- 阻塞 B2（跨增量接口未接入）：`src/openpi/policies/policy_config.py:59,115` 读取 `create_data_config(training=False)` 和 `memory_config`，当前真实 `TrainConfig` 均未提供。以真实配置和 stubbed model 调用 policy loader 的结果为 `AttributeError: 'TrainConfig' object has no attribute 'create_data_config'`，仅给 checkpoint 路径不能恢复 policy。
- 待完整 review：新增 metadata 测试仍把 resolved config 放在 `policy_metadata["memory_config"]`，未验证任务要求的 `TrainConfig.memory_config` 单一权威副本；新增保存测试使用 `_SaveConfig` 并 monkeypatch metadata 保存，未覆盖真实训练配置、真实 data-config factory 或 checkpoint-only policy 恢复。训练增量合入后需验证保存 YAML 不含原路径依赖、`create_data_config(training=False)` 不读 dataset/sidecar、runtime metadata 只透传该唯一对象。
- 待完整 review：最终训练的 `save_interval`、`keep_period`、`resume` 和 `save_full_state` 配置尚未送达。尤其 model-only checkpoint 没有 `train_state`，因此不能把该目录作为可恢复训练状态；需核对正式配置仅保存最终 20k，并且不会以 `resume=True` 尝试恢复它。
- 未运行 GPU/正式训练/6B 保存。手工标记的 policy inference/broker 测试不作为本 CPU 阶段的验收；误启动的 CPU-only pytest 已终止，确认无遗留 pytest、训练或服务进程。

workspace、各库交付 commit：

- openpi reviewer worktree：`/mnt/public/xcj/Projects/workspace/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/openpi`
- review HEAD：`489359f8655c0a0af35447caa71f4db702fefabe`
- reviewer 未修改 openpi，实现交付 commit：无。

验证结果与成果位置：

- `env CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/worktree_env_smoke.py`：通过；editable `openpi` 和 `openpi-client` 均指向本 task worktree。
- `env CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider src/openpi/training/checkpoints_test.py src/openpi/training/checkpoint_metadata_test.py src/openpi/training/config_test.py`：`8 passed`。
- `env CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider src/openpi/policies/policy_test.py -k 'not test_infer and not test_broker'`：`3 passed, 2 deselected`。
- `.venv/bin/ruff check` 与 `.venv/bin/ruff format --check`（上述 6 个变更文件）：均通过。
- 本阶段 smoke 的 worktree `.pytest_cache` 和源码 bytecode cache 已移出；未留下运行进程或实现修改。

下一步：等待 Manager 提供训练/模型增量的固定 commit；在同一 worktree 合入后，继续检查真实 transform/token 条件、loss/mask/索引、metadata 自包含恢复和作者 GPU 50-step/BF16 产物证据，再更新本报告为完整 HEAD 结论。
