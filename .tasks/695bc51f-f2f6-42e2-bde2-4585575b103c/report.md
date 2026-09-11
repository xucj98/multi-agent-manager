# put-back B 组 serial/no-memory 基线配置

研究目的：为既定 B 组补齐 put-back 的 `serial_lag30` 与 `no_memory` seed0 训练入口，使其与已有 full 三 seed、rearrange serial/no-memory 共享模型、loader 和训练参数，只替换 put-back 的数据、字段 schema、sidecar 与 robot norm。

## 当前单模型放行状态

- **no-memory / GPU7：已获 Manager 单独放行，但当前等待 GPU7 释放。** 本模型的 50-step 训练、BF16 model-only 保存和 checkpoint-only 恢复均已完成；恢复证据及可复核路径见下文。2026-09-11 15:44 +08:00 启动前复核显示 GPU7 为 `16223 MiB / 87%`，且本 VM 没有可见 PID，属于外部 VM 作业；依任务的空闲启动条件，未并发启动、未登记 job。GPU7 空闲后将立即以已核对的冻结树启动正式 20k。
- **serial_lag30 / GPU6：尚不可放行。** GPU6 为他人占用，按最新安排未探测性使用、未启动 smoke；待资源由 Manager 另行安排后才做本模型自身的训练和恢复 gate。

## 已交付，待快速验收

- worktree：`/mnt/public/xcj/Projects/workspace/695bc51f-f2f6-42e2-bde2-4585575b103c/openpi`，分支 `task/695bc51f-f2f6-42e2-bde2-4585575b103c`，基点 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
- 配置 commit：`a7f3e07346cee7260cdc3a618eedc38c0702da61`（`feat: add put-back serial and no-memory configs`），工作树干净。
- 新注册：`pi05_rmbench_put_back_block_serial_lag30`、`pi05_rmbench_put_back_block_no_memory`；新增对应 YAML、RMBench 配置说明及绑定回归测试。没有改模型、loader 或 schema 算法。
- 两条路径均固定 `put_back_block_demo_clean_state_shared_memory`、`data/memory_v1/rmbench/put_back_block_demo_clean_state_shared_memory/episode_memory.json`、`rmbench_put_back_block_robot`；state/action norm 均为 14D，未使用 rearrange norm 或 `demo_clean`。
- serial 使用 `phase`（4 类）和 `origin_mat`（5 类）的固定 lag30 输入、当前 query token 监督、`train: reference / infer: selected` 与 teacher forcing；no-memory 只有 sidecar `robot_action_target`，无 key-state 字段。

## CPU 验收

- `.venv/bin/python scripts/worktree_env_smoke.py`：通过。
- `JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q src/openpi/training/memory_data_test.py::test_rmbench_put_back_serial_and_no_memory_configs_keep_task_specific_assets src/openpi/training/config_memory_test.py::test_train_cli_can_materialize_memory_templates`：`2 passed in 60.11s`。
- 显式 `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu` 的真实 loader 首 batch 验收（验收进程仅以 `dataclasses.replace(..., num_workers=0)` 避免 stdin 多进程启动限制，训练配置未变）：两路径均 batch32，state/action/action-loss-weight shape 均为 `[32,32]` / `[32,50,32]` / `[32,50,32]`；14D robot 坐标有有效权重，padding 坐标权重全为零。serial 的 input/target/mask 均为 `[32,2]`，64 个有效 token target；no-memory 三者均为 `None`。与 rearrange 同类基线比较，batch32、20k、H50、`save_interval=20000`、BF16 model-only、pi05_base loader 和 repack transforms 全部一致。
- `ruff check` 通过；新增测试文件已格式化。`config.py` 的全文件 format check 仅报告基点已有的第 2766 行差异，未混入本提交。

## GPU7 no-memory smoke 与 checkpoint-only 恢复（已完成，供单独放行）

- 实际训练命令：`CUDA_VISIBLE_DEVICES=7 ... .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_no_memory --exp-name=smoke50_695bc51f_put_back_no_memory_s0 --seed=0 --num-train-steps=50 --save-interval=50 --log-interval=10 --no-wandb-enabled`；PID `3969693`，启动前 GPU7=1 MiB/0%，训练后 PID 退出、GPU7=1 MiB/0%。
- 实际 50 updates 完成且五个日志区间均有限：step10 `grad_norm=2.4749, loss=0.1804, param_norm=1802.3866`；step20 `1.7631, 0.1241, 1802.3866`；step30 `0.7074, 0.0766, 1802.3866`；step40 `0.4225, 0.0537, 1802.3866`；step50 `0.3406, 0.0442, 1802.3866`。
- 唯一 smoke checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/smoke50_695bc51f_put_back_no_memory_s0/50`，原子 Save Finalize 完成，仅含 `params/assets/metadata`，没有 `train_state`；metadata 中仅一份 resolved `memory_config`。
- 同一 GPU7 的新解释器 checkpoint-only gate 通过。audit hook 拒绝任何训练数据、sidecar、源 norm/YAML、pi05_base 参数读取；从 checkpoint 自身恢复 51 个叶、3,353,433,872 个元素、6,706,867,744 bytes，全部 BF16、有限、逐 shape 匹配。真实 policy factory/inference 返回有限 `actions` shape `[50,14]`，输出为 `actions`/`policy_timing`，符合 no-memory 不应产生 memory prediction 的接口。
- smoke checkpoint 与日志暂留供本次单模型验收；正式 no-memory 20k 必须获得单独放行后才启动，随后按任务要求清理本任务 smoke 临时产物。

## GPU smoke 与正式计划

- 本机预检：提交时 GPU6/7 均为 1 MiB、0%；提交后复查 GPU6 已出现 20023 MiB/55% 且本 VM 无可见 PID，按要求不占用/不清理他人资源。GPU7 仍为 1 MiB/0%。
- 按 Manager 最新安排，GPU6 的外部占用不触碰；serial 的 50-step/BF16/checkpoint-only gate 暂未启动。短 smoke 不登记 MAM job。
- 待 Manager 快速验收 `a7f3e07` 并放行后，正式 20k 才启动：GPU6 `pi05_rmbench_put_back_block_serial_lag30` seed0，GPU7 `pi05_rmbench_put_back_block_no_memory` seed0；分别使用独立 `exp_name` `memory20k_695bc51f_put_back_serial_lag30_s0` / `memory20k_695bc51f_put_back_no_memory_s0`，`nohup setsid .venv/bin/python -u -B` 启动，登记 `mam job`，只保留最终 `20000` 的 BF16 `params/assets/metadata`。
- 预期正式结果目录：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0/20000` 与 `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s0/20000`。

独立 review 已由 Manager 派发 `15254a5f`。本任务不会等待 4090/C 环境；no-memory 恢复证据已可供单独验收/放行，serial 保持等待而不触碰 GPU6。
