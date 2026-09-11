# put-back B 组 serial/no-memory 基线配置

研究目的：为既定 B 组补齐 put-back 的 `serial_lag30` 与 `no_memory` seed0 训练入口，使其与已有 full 三 seed、rearrange serial/no-memory 共享模型、loader 和训练参数，只替换 put-back 的数据、字段 schema、sidecar 与 robot norm。

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

## GPU smoke 与正式计划

- 本机预检：提交时 GPU6/7 均为 1 MiB、0%；提交后复查 GPU6 已出现 20023 MiB/55% 且本 VM 无可见 PID，按要求不占用/不清理他人资源。GPU7 仍为 1 MiB/0%。
- GPU6 空闲后：serial 50-step + BF16 model-only 保存 + checkpoint-only 恢复；GPU7：no-memory 同样 smoke。短 smoke 不登记 MAM job，临时产物完成后清理。
- 待 Manager 快速验收 `a7f3e07` 并放行后，正式 20k 才启动：GPU6 `pi05_rmbench_put_back_block_serial_lag30` seed0，GPU7 `pi05_rmbench_put_back_block_no_memory` seed0；分别使用独立 `exp_name` `memory20k_695bc51f_put_back_serial_lag30_s0` / `memory20k_695bc51f_put_back_no_memory_s0`，`nohup setsid .venv/bin/python -u -B` 启动，登记 `mam job`，只保留最终 `20000` 的 BF16 `params/assets/metadata`。
- 预期正式结果目录：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0/20000` 与 `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s0/20000`。

请 Manager 安排独立 review 并快速验收本 commit；本任务不会等待 4090/C 环境。GPU smoke 继续在本机可用的 GPU6/7 上进行，正式训练严格等待放行。
