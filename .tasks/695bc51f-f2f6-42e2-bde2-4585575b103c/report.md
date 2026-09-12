# put-back B 组 serial/no-memory 基线配置

## 当前可评交接（交 e6908de7-4b02-465a-987b-a19eba7a315a）

更新时间：2026-09-12T19:15+08:00。以下表为当前状态，后文启动/巡检记录为历史。已采用18:35主动唤醒协议：远端no-memory seed1/2两路继续running；serial三个seed均完成并恢复PASS，无待启动训练项；停止后由MAM唤醒执行最终产物验收与e690交接，本轮结束，不维持监控用active等待。

当前可评：no-memory seed0与serial_lag30 seed0/1/2；no-memory seed1/2仍训练，未列为READY。

| config | schema | seed | 当前状态 | checkpoint（绝对路径） |
|---|---|---|---|---|
| pi05_rmbench_put_back_block_no_memory | v1 / joint_dense，robot-only，无memory字段 | 0 | READY：20k保存及独立恢复PASS | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s0/20000 |
| pi05_rmbench_put_back_block_no_memory | v1 / joint_dense，robot-only，无memory字段 | 1 | TRAINING：未交可评 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s1/20000 |
| pi05_rmbench_put_back_block_no_memory | v1 / joint_dense，robot-only，无memory字段 | 2 | TRAINING：未交可评 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s2/20000 |
| pi05_rmbench_put_back_block_serial_lag30 | v1 / serial_token，phase/origin_mat，lag30 | 0 | READY：20k保存及独立恢复PASS | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0/20000 |
| pi05_rmbench_put_back_block_serial_lag30 | v1 / serial_token，phase/origin_mat，lag30 | 1 | READY：20k保存及独立恢复PASS | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s1/20000 |
| pi05_rmbench_put_back_block_serial_lag30 | v1 / serial_token，phase/origin_mat，lag30 | 2 | READY：20k保存及独立恢复PASS | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s2/20000 |

所有行 train commit=`a7f3e07346cee7260cdc3a618eedc38c0702da61`；同 pi05_base、demo_clean_state、put-back 专用14D robot norm、bs32/20k/H50/K30。研究目的：与 put-back full 基线比较显式 memory、串行 lag30 与 robot-only 的同骨干任务能力；seed0/1/2用于独立训练重复。预期检验 memory 表达/条件方式是否改变成功率及失败分布，并报告跨seed变异，不预设优胜模型或成功率；training loss与恢复PASS不替代正式eval结论。

**本次可评：no_memory seed0。** 12:42:50 保存最终20000并完成 Save Finalize，训练PID3996599退出；step20000 grad_norm=0.0237/loss=0.0004/param_norm=1804.4125，200个日志区间全部有限。最终仅params/assets/metadata，无train_state；数据绑定、norm、唯一resolved memory_config核验通过。GPU0新解释器拒绝训练源读取，完整恢复51叶/3,353,433,872元素/BF16/逐shape匹配/全部有限，真实policy inference actions[50,14]有限、无memory输出，gate退出0；GPU0恢复后1MiB/0%。

训练日志：`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s0.log`；恢复证据：`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s0_checkpoint_gate.log`。该gate摘要input_memory_ids=[1,1]是沿用serial日志标签，no-memory实际obs已pop该字段、仅actions/policy_timing输出；检验脚本输出标签已修正，未改模型或重训。

本模型smoke日志已保留至`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s0_artifacts`，smoke临时checkpoint已删除。请e690按自身matching smoke2→100协议接入本READY行并更新实验台账；远端no-memory seed1/2仍训练，不提前列为ready，不自行重复启动eval。


研究目的：为既定 B 组补齐 put-back 的 `serial_lag30` 与 `no_memory` seed0 训练入口，使其与已有 full 三 seed、rearrange serial/no-memory 共享模型、loader 和训练参数，只替换 put-back 的数据、字段 schema、sidecar 与 robot norm。

**新增可评：serial_lag30 seed0。** 12:46:10 完成20000 Save Finalize，PID4009203退出。step20000 grad_norm=0.3490/loss=0.0101/param_norm=1804.7457，200个日志区间全部有限。最终仅params/assets/metadata；数据绑定、norm、resolved config通过。GPU6 checkpoint-only恢复56叶/3,353,466,650元素/BF16/逐shape匹配/全部有限，actions[50,14]及memory_prediction_ids[1,2]通过，gate退出0，恢复后GPU6=1MiB/0%。训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s0.log`；gate证据 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s0_checkpoint_gate.log`。smoke日志含首次失败和retry1已复制到 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s0_artifacts`，本任务两条smoke临时checkpoint均已清理。两个seed0均可独立交e690安排eval，不等seed1/2；训练job验收后归档。

**新增可评：serial_lag30 seed1。** 20k Save Finalize完成、训练进程退出；step20000 grad_norm=0.3689/loss=0.0111/param_norm=1804.6769，200个日志区间全部有限。checkpoint metadata/data binding/norm及仅最终params/assets/metadata协议通过；wuwen-1新解释器拒绝训练源读取，恢复56叶、3,353,466,650元素、BF16、全部有限且逐shape匹配，真实actions[50,14]和memory_prediction_ids[1,2]通过，gate退出0。恢复证据 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s1_checkpoint_gate.log`；训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s1.log`。完整config/schema/seed/commit/绝对checkpoint路径及研究目的见当前表；请e690接入这项独立训练重复，不等no-memory剩余seed。无seed-only smoke临时产物；验证后GPU0=4MiB/0%。训练job已验收并归档。

**新增可评：serial_lag30 seed2。** 20k Save Finalize完成、训练进程退出；step20000 grad_norm=0.3379/loss=0.0096/param_norm=1804.7695，200个日志区间全部有限。checkpoint metadata/data binding/norm及仅最终params/assets/metadata协议通过；wuwen-1新解释器拒绝训练源读取，恢复56叶、3,353,466,650元素、BF16、全部有限且逐shape匹配，真实actions[50,14]和memory_prediction_ids[1,2]通过，gate退出0。恢复证据 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s2_checkpoint_gate.log`；训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s2.log`。完整config/schema/seed/commit/绝对checkpoint路径及研究目的见当前表；请e690接入这项独立训练重复，不等no-memory剩余seed。无seed-only smoke临时产物；验证后GPU2=4MiB/0%。训练job已验收并归档。

## 当前单模型放行状态

- **no-memory seed0：正式20k完成并恢复PASS，已交可评。** 本模型的 50-step 训练、BF16 model-only 保存和 checkpoint-only 恢复已完成。2026-09-11 16:16 +08:00 GPU0 空闲后，以冻结 commit `a7f3e07` 启动 `memory20k_695bc51f_put_back_no_memory_s0`；MAM job `14bad7c3-59cb-45d5-8173-8eb92cb9b90a`、PID `3996599` 已登记为 running。已验证首个 update（16:21:40）、step100 有限 `grad_norm=0.7297, loss=0.0618, param_norm=1802.3864`，以及 step400 有限 `0.1034, 0.0065, 1802.3904`；稳定约 3.7 s/update。
- **serial_lag30 seed0：正式20k完成并恢复PASS，已交可评。** 独立 review、GPU6 的 50-step smoke、BF16 保存和 checkpoint-only policy gate 均已 PASS。2026-09-11 16:40 +08:00 以冻结 commit `a7f3e07` 在 GPU6 启动 `memory20k_695bc51f_put_back_serial_lag30_s0`；MAM job `e087cfa2-04d2-460d-8b6e-974fdd7c7b1a`、PID `4009203` 已登记为 running。已验证首个 update（16:45:07）和 step100 有限 `grad_norm=40.5274, loss=0.5226, param_norm=1802.3909`；稳定约 3.6 s/update。

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
- **初次 gate 与 retry1 留痕：** 初次 gate 已通过 metadata/BF16 参数树阶段，但在真实 policy inference 前因合成测试图像误用 HWC `[224,224,3]`，与 ALOHA policy 的 CHW `[3,224,224]` 外部输入约定不符而在图像 resize 停止；checkpoint、模型和训练进程均未失败。`retry1` 只将合成输入改为 CHW，随后完成相同 checkpoint-only 审计与真实推理并 PASS。初次日志保留于 `/mnt/public/xcj/Projects/openpi/logs/smoke50_695bc51f_put_back_serial_lag30_s0_checkpoint_gate.log`，成功 retry1 日志路径如上。

## GPU smoke 与正式计划

- no-memory 正式运行位于 GPU0，日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s0.log`，仅最终 checkpoint `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s0/20000` 将保留 BF16 `params/assets/metadata`；按小时监控并在完成后归档 job。
- serial 正式运行位于 GPU6，日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s0.log`，MAM job `e087cfa2-04d2-460d-8b6e-974fdd7c7b1a`；仅最终 checkpoint `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0/20000` 将保留 BF16 `params/assets/metadata`，按小时监控并在完成后归档 job。
- 两条 smoke 的 checkpoint、日志与 gate 证据暂留供验收；正式 no-memory 形成最终 checkpoint 后再按任务要求清理本任务 smoke 临时产物。

## 后续四项命令及路径（原 queued，现已于 23:34 在 wuwen-1 启动）

四项均使用冻结 commit `a7f3e07`、单卡 batch32/20k/H50/K30、相同 put-back 数据/sidecar/14D norm/pi05_base，只变 `--seed` 和独立 `--exp-name`。2026-09-11 16:49 +08:00 已核对四个 checkpoint 根目录和日志文件均不存在。每次仅在本机实际空闲 GPU 上启动，先复核 `nvidia-smi` 与本项目其他 task/job；不使用 wuwen-1、不碰占用进程，也不重复 GPU smoke。

1. **running on wuwen-1 — serial_lag30 seed1**
   - checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s1/20000`
   - log：`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s1.log`
   - command：`env CUDA_VISIBLE_DEVICES=<FREE_GPU> XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot OPENPI_DATA_HOME=/mnt/public/cache/openpi .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_serial_lag30 --exp-name=memory20k_695bc51f_put_back_serial_lag30_s1 --seed=1 --no-wandb-enabled`
2. **running on wuwen-1 — no-memory seed1**
   - checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s1/20000`
   - log：`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s1.log`
   - command：`env CUDA_VISIBLE_DEVICES=<FREE_GPU> XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot OPENPI_DATA_HOME=/mnt/public/cache/openpi .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_no_memory --exp-name=memory20k_695bc51f_put_back_no_memory_s1 --seed=1 --no-wandb-enabled`
3. **running on wuwen-1 — serial_lag30 seed2**
   - checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s2/20000`
   - log：`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s2.log`
   - command：`env CUDA_VISIBLE_DEVICES=<FREE_GPU> XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot OPENPI_DATA_HOME=/mnt/public/cache/openpi .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_serial_lag30 --exp-name=memory20k_695bc51f_put_back_serial_lag30_s2 --seed=2 --no-wandb-enabled`
4. **running on wuwen-1 — no-memory seed2**
   - checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s2/20000`
   - log：`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s2.log`
   - command：`env CUDA_VISIBLE_DEVICES=<FREE_GPU> XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot OPENPI_DATA_HOME=/mnt/public/cache/openpi .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_no_memory --exp-name=memory20k_695bc51f_put_back_no_memory_s2 --seed=2 --no-wandb-enabled`

## 2026-09-11 17:13 +08:00 小时巡检

- no-memory seed0：MAM job `14bad7c3-59cb-45d5-8173-8eb92cb9b90a` 为 running；最新 step800 `grad_norm=0.0722, loss=0.0046, param_norm=1802.4214`，全为有限。
- serial_lag30 seed0：MAM job `e087cfa2-04d2-460d-8b6e-974fdd7c7b1a` 为 running；最新 step400 `grad_norm=4.1750, loss=0.0507, param_norm=1802.3975`，全为有限。
- 资源：GPU0/1/2/3/4/5/6/7 均实际占用（17:13 快照分别为 `73405/70515/73407/73407/73405/73405/73407/75121 MiB`，利用率 99–100%）；本项目 2–5 的 7ae 训练仍登记为 running，GPU1 另有 wash job。四项 queued 均未启动，未触碰任何既有作业。
- 按原协议下次约小时巡检或由 Manager 提前唤醒；一旦有实际空卡，按已发布顺序启动 serial seed1 并登记。

独立 review `15254a5f` 已 PASS。本任务不会等待 4090/C 环境；no-memory 与 serial 正式 20k 均已运行。

## 2026-09-11 17:16 +08:00 资源/训练巡检

- no-memory seed0：MAM job `14bad7c3-59cb-45d5-8173-8eb92cb9b90a` 仍为 running；日志已推进至 step843。最近完整指标为 step800：`grad_norm=0.0722, loss=0.0046, param_norm=1802.4214`，均为有限值；当前速率约 3.7 s/update。
- serial_lag30 seed0：MAM job `e087cfa2-04d2-460d-8b6e-974fdd7c7b1a` 仍为 running；日志已推进至 step467。最近完整指标为 step400：`grad_norm=4.1750, loss=0.0507, param_norm=1802.3975`，均为有限值；当前速率约 3.6 s/update。
- 资源复核：GPU0–7 全部实际占用，利用率 98–100%，显存分别为 `73405/70515/73407/73407/73405/73405/73407/80063 MiB`；没有可接用的实际空卡。四项后续训练维持 queued，未触碰其他作业。
- 按既定约小时巡检；若 Manager 提前唤醒或任一实际空卡出现，直接按顺序启动 serial_lag30 seed1、no-memory seed1、serial_lag30 seed2、no-memory seed2，并逐项登记与确认首个有限 update。

## 2026-09-11 18:12 +08:00 资源/训练巡检

- no-memory seed0：MAM job `14bad7c3-59cb-45d5-8173-8eb92cb9b90a` 为 running；日志已推进至约 step1770，最近完整指标为 step1700：`grad_norm=0.0464, loss=0.0030, param_norm=1802.6096`，均为有限值。
- serial_lag30 seed0：MAM job `e087cfa2-04d2-460d-8b6e-974fdd7c7b1a` 为 running；日志已推进至约 step1410，最近完整指标为 step1400：`grad_norm=0.8634, loss=0.0194, param_norm=1802.6012`，均为有限值。
- 资源复核：GPU0–7 均为实际占用，利用率 `100/71/100/100/100/100/100/100%`，显存 `73405/73159/73407/73407/73405/73405/73407/72903 MiB`；没有可接用的实际空卡。四项授权队列仍依次为 serial_lag30 seed1、no-memory seed1、serial_lag30 seed2、no-memory seed2，均未启动。
- 冻结 worktree 仍干净；未修改配置或源码，未触碰任何其他作业。下次资源窗口继续按同一顺序判定并启动首项可用队列。


## 2026-09-11 23:35 +08:00 wuwen-1 四项正式启动

研究目的：补齐 B 组 put-back serial_lag30/no-memory 三 seed 重复，保持相同骨干、数据与训练预算。最新 task 的 wuwen-1 开放授权覆盖先前禁用规定。启动前已核对 MAM、本机 seed0 日志、四项唯一日志/checkpoint 均不存在及远端训练进程；没有重复 seed。两条 seed0 仍 running：serial step6700 loss=0.0105，no-memory step7000 loss=0.0013。

远端 host `wuwen-1`（hostname `is-ddiwvwflq5htlzyz-devmachine-0`），启动前 GPU0–7 均 4 MiB/0%，无 compute PID。依序在 GPU0–3 启动，复用共享冻结 worktree `a7f3e07346cee7260cdc3a618eedc38c0702da61`，工作树干净。单卡 bs32/20k、原 data/norm/base、仅最终 BF16 params/assets/metadata 协议不变。命令及唯一结果目录见上方四项，将 `<FREE_GPU>` 分别落实为 0/1/2/3，使用 `nohup setsid env ... .venv/bin/python -u -B ... > LOG 2>&1 < /dev/null &` 启动，无覆盖或重复 smoke。

| 模型 | seed | GPU | PID | MAM job |
|---|---|---|---|---|
| serial_lag30 | 1 | 0 | 1469044 | 68dde347-ad63-46e6-a35e-08c4ced8eeec |
| no_memory | 1 | 1 | 1469111 | e26bc150-d705-4f9c-9ae0-d8449e11cd0e |
| serial_lag30 | 2 | 2 | 1469115 | 88818158-8a76-4e96-a1a5-5641dd0b47cf |
| no_memory | 2 | 3 | 1469245 | cadcb4ac-ceb3-4a8c-a773-2ee11516f789 |

四条 job 已在本机 MAM 登记 remote host/PID/boot_id/start_ticks，状态 running；首批 updates/有限 loss 已于下方初检确认。GPU4–7 启动前空闲，留给 Manager 排期，不扩展实验清单。启动初检后阶段交付，不建立高频模型巡检。


## 2026-09-11T23:50:19+08:00 四路启动初检完成

四路均已完成至少 100 updates，首个完整 grad_norm/loss/param_norm 均为有限值。启动早期有额外初始化延迟，至 step64–72 时已稳定约 3.5–3.8 s/update。

- serial_lag30 seed1：`Step 100: grad_norm=67.2492, loss=0.5693, param_norm=1802.3906`。日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s1.log`；最终 checkpoint `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s1/20000`。
- no_memory seed1：`Step 100: grad_norm=0.7081, loss=0.0599, param_norm=1802.3864`。日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s1.log`；最终 checkpoint `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s1/20000`。
- serial_lag30 seed2：`Step 100: grad_norm=49.1644, loss=0.5893, param_norm=1802.3906`。日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s2.log`；最终 checkpoint `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s2/20000`。
- no_memory seed2：`Step 100: grad_norm=0.7033, loss=0.0599, param_norm=1802.3864`。日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s2.log`；最终 checkpoint `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s2/20000`。

阶段交付：四项由 queued 全部转为 running，本任务现在共六路正式训练（本机两路 seed0 + wuwen-1 四路 seed1/2）。冻结 a7f3e07/bs32/20k，未重复 seed-only smoke 或扩展实验。远端 GPU4–7 初检仍为 4 MiB/0%，供 Manager 排期。普通有界日志初检脚本已完成退出；本轮不创建周期模型巡检或等待 job，由 Manager 接手后续训练完成、最终 BF16/metadata/assets 核验、独立恢复与归档。

## 2026-09-12 02:51 +08:00 恢复运行期责任

最新 task revision `88555d38` 覆盖此前阶段交付后的监控安排。本次复用原干净 worktree，只读核对六路均 running，均无最终 20000 目录，暂无停止 job 可验收/归档。

| 模型 | seed | 最新完整 step | loss |
|---|---|---|---|
| no_memory | 0 | 10200 | 0.0010 |
| serial_lag30 | 0 | 10000 | 0.0087 |
| no_memory | 1 | 3000 | 0.0020 |
| no_memory | 2 | 2900 | 0.0021 |
| serial_lag30 | 1 | 3200 | 0.0278 |
| serial_lag30 | 2 | 3200 | 0.0253 |

六路最近 grad_norm/loss/param_norm 均有限。继续承担原六路的停止后 20k 产物核验、台账、临时产物清理及 job 归档；不重复训练。现在实际调用新版 `mam wait` 保持 active 等待停止事件，不安排分钟/小时模型训练巡检。
