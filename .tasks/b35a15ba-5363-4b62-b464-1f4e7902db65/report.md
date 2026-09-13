# swap / battery / cover J/S Memory-v1 独立代码审查

## 结论

审查候选 OpenPI `afb7a4d0ac20f2cba3c6bb0d5a25c96f792479c3`（相对父提交
`6ae7056c5bab346d6865742ee503d15f82f239f7`）未发现 P1/P2 或其他会阻止
swap_blocks、battery_try、cover_blocks 生成 semantic sidecar、随后分别开展真实
50-step save/restore gate 的代码缺陷。

这是新增六条 J/S schema、adapter、训练配置的代码准入结论。它不替代使用真实
sidecar 的 loader/multi-worker 验证、50-step save/restore、或 checkpoint-only
policy restore；这些仍是每条运行路径在正式 20k 前必须完成的后续 gate。三条 N
不在本 review 范围内，也不受本结论约束。

独立审查树保持干净：

- `/mnt/public/xcj/Projects/workspace/b35a15ba-5363-4b62-b464-1f4e7902db65/openpi`
- branch `task/b35a15ba-5363-4b62-b464-1f4e7902db65`
- HEAD `afb7a4d0ac20f2cba3c6bb0d5a25c96f792479c3`

## 审查判断

- Adapter 将 `observation.key_state_target_ids` / `_mask` 作为转换列的
  current-truth 校验输入，并从 `demo_clean_state` 原始 metadata 重建 sidecar
  的事实；`observation.key_state_input_ids` 被显式保留为不可绑定的 legacy
  lag-20 列。见 `examples/rmbench/rmbench_memory_adapter.py:37-41`、
  `332-377`、`423-480`、`618-687`。因此没有把 legacy 输入误作当前 GT。
- swap 使用四个 phase 和两个 4 类 tray 属性，并验证三个 tray fact 是
  left/middle/right permutation；battery 只含四个实际 phase，未把 attempted set
  伪造为 memory；cover 使用六个 phase 和 red/green/blue 三个 4 类位置，保持
  `14 + 6 + 4 + 4 + 4 = 32`，initial 是已裁决的 `cover_left_position`。
- Full schema 使用未来 `t+j+1` phase target、共同 row-30 validity 和
  `fixed_horizon`，50-step chunk 的 feedback 取已执行的最后一行。属性字段保留
  `valid_mean`，与既有模式一致。Serial schema 使用固定 lag 30、query current
  target、`current_condition {train: reference, infer: selected}` 和
  query-selected feedback。
- 六个 builder 都绑定对应 `demo_clean_state_shared_memory` 数据、14-D robot
  state、32-D/H50、batch 32、20k/save-20k、model-only BF16 与对应 robot-only
  norm asset；serial 另有 token head 的 `missing_regex`。`TrainConfig` 会将 YAML
  解析后的 mapping 固化在 `memory_config`，使 checkpoint inference 不依赖原 YAML。

## 独立验证

在上述 review tree 执行，未设置 `HF_LEROBOT_HOME`，且未使用 GPU、训练、sidecar
生成或 rollout：

```text
JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q \
  examples/rmbench/test_rmbench_memory_adapter.py \
  src/openpi/training/config_memory_test.py \
  src/openpi/training/config_test.py
# 54 passed, 1 warning in 79.26s
```

该 warning 是 `ml_collections` 的 invalid escape sequence 弃用警告，不是候选
失败。

另对下列六个 config 逐一执行了：`get_config`、`create_data_config(training=False)`、
写入 checkpoint metadata、重新加载、再次建立 inference transform；六者的 resolved
`memory_config` 及 `MemoryModelSpec` 均一致：

```text
pi05_rmbench_swap_blocks_full_t_plus_1
pi05_rmbench_swap_blocks_serial_lag30
pi05_rmbench_battery_try_full_t_plus_1
pi05_rmbench_battery_try_serial_lag30
pi05_rmbench_cover_blocks_full_t_plus_1
pi05_rmbench_cover_blocks_serial_lag30
```

本次还独立重跑了只读 source validation，以 review tree 的 candidate adapter
导入、`PYTHONPATH=.`、`HF_LEROBOT_HOME` unset。它只读取三个真实
`demo_clean_state` 数据集的数值列和原始 metadata，不解码相机列：

```text
swap_blocks:    50 episodes, 29,920 query rows
battery_try:    50 episodes, 32,626 query rows
cover_blocks:   50 episodes, 50,904 query rows
```

三任务均验证了 robot/state finite、字段 vocabulary 与阶段覆盖，以及每个 episode
M+1 最后一行重复最终 action。可复核脚本和候选原始收据位于：

- `/mnt/public/xcj/Projects/openpi/assets/memory_v1/js_validation/validate_semantic_sources.py`
- `/mnt/public/xcj/Projects/openpi/assets/memory_v1/js_validation/afb7a4d0ac20f2cba3c6bb0d5a25c96f792479c3/receipt.txt`
- `/mnt/public/xcj/Projects/openpi/assets/memory_v1/js_validation/afb7a4d0ac20f2cba3c6bb0d5a25c96f792479c3/validate_semantic_sources.stdout.log`

附加静态质量检查也通过：`git diff --check`、对四个改动 Python 文件的
`ruff check`、`ruff format --check`。审查树在结束时无未提交改动。

## 尚未覆盖的运行 gate

候选提交本身没有生成 semantic sidecar，本 review 也按任务约束没有生成全量
sidecar。因此尚未验证：

1. 新 sidecar 在真实 `MemoryLeRobotDataset` 中的随机 batch 和 2-worker 行为；
2. 六条 J/S 路径各自的真实 50-step finite-loss、save/restore；
3. checkpoint-only policy restore 的输出 shape、BF16 和 finite。

这些不是当前 diff 的已知缺陷。sidecar 生成后，可按每个任务/表示独立完成上述 gate，
无需把已通过代码审查的其他路径绑在一起等待。
