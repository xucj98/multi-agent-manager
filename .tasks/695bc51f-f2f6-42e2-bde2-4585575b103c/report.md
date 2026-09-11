# put-back B 组 serial/no-memory 基线配置

研究目的：为既定 B 组补齐 put-back 的 `serial_lag30` 与 `no_memory` seed0 训练入口，使其与已有 full 三 seed、rearrange serial/no-memory 共享模型、loader 和训练参数，只替换 put-back 的数据、字段 schema、sidecar 与 robot norm。

## 当前单模型放行状态

- **no-memory：正式 20k 运行中。** 本模型的 50-step 训练、BF16 model-only 保存和 checkpoint-only 恢复已完成。2026-09-11 16:16 +08:00 GPU0 空闲后，以冻结 commit `a7f3e07` 启动 `memory20k_695bc51f_put_back_no_memory_s0`；MAM job `14bad7c3-59cb-45d5-8173-8eb92cb9b90a`、PID `3996599` 已登记为 running。已验证首个 update（16:21:40）以及 step100 有限 `grad_norm=0.7297, loss=0.0618, param_norm=1802.3864`；稳定约 3.7 s/update。
- **serial_lag30：自身 smoke/恢复均已 PASS，可单独放行正式 20k。** 独立 review 已 PASS。GPU6 的 `smoke50_695bc51f_put_back_serial_lag30_s0` 完成 50 updates、最终有限 loss `0.3052`、BF16 保存和 checkpoint-only policy gate；正式 serial 尚未启动，等待 Manager 单独放行。

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

## GPU6 serial_lag30 smoke 与 checkpoint-only 恢复（已完成，供单独放行）

- 实际训练命令：`CUDA_VISIBLE_DEVICES=6 ... .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_serial_lag30 --exp-name=smoke50_695bc51f_put_back_serial_lag30_s0 --seed=0 --num-train-steps=50 --save-interval=50 --log-interval=10 --no-wandb-enabled`；PID `3996877`，启动前 GPU6=1 MiB/0%，完成后退出、GPU6=1 MiB/0%。
- 50 updates 完成且五个日志区间均有限：step10 `grad_norm=87.0352, loss=1.6721, param_norm=1802.3909`；step20 `64.3239, 1.1431, 1802.3909`；step30 `53.7398, 0.6960, 1802.3909`；step40 `45.6514, 0.4851, 1802.3909`；step50 `30.7210, 0.3052, 1802.3909`。
- checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/smoke50_695bc51f_put_back_serial_lag30_s0/50`，原子 Save Finalize 完成，仅含 `params/assets/metadata`，无 `train_state`。
- GPU6 新解释器 checkpoint-only gate 通过：audit hook 拒绝训练数据、sidecar、源 norm/YAML 和 pi05_base 读取；从 checkpoint 恢复 56 个叶、3,353,466,650 个元素、6,706,933,300 bytes，全部 BF16、有限且逐 shape 匹配。真实 policy factory/inference 返回有限 `actions` `[50,14]`、serial `memory_prediction_ids` `[1,2]`，输出含 `key_state_prediction` 与 `policy_timing`。成功 gate 日志：`/mnt/public/xcj/Projects/openpi/logs/smoke50_695bc51f_put_back_serial_lag30_s0_checkpoint_gate_retry1.log`。

## GPU smoke 与正式计划

- no-memory 正式运行位于 GPU0，日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s0.log`，仅最终 checkpoint `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s0/20000` 将保留 BF16 `params/assets/metadata`；按小时监控并在完成后归档 job。
- serial 的正式计划保持独立 `exp_name` `memory20k_695bc51f_put_back_serial_lag30_s0`，仅在 Manager 单独放行后才启动并登记 MAM job；预期最终路径 `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0/20000`。
- 两条 smoke 的 checkpoint、日志与 gate 证据暂留供验收；正式 no-memory 形成最终 checkpoint 后再按任务要求清理本任务 smoke 临时产物。

独立 review `15254a5f` 已 PASS。本任务不会等待 4090/C 环境；no-memory 正式 20k 已运行，serial 恢复证据已可供单独验收/放行。
