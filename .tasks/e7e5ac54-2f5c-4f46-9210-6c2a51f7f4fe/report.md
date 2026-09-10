task_revision: d85a00d744bc85a82ac08805c3aedf0769191850

# 首批 Memory 20k：CPU 启动准备

## 完成与未完成

- 已完成：按 task 创建独立 openpi worktree、两端独立解释器与 CPU CLI/data/memory 配置核对、demo_clean_state 来源核实、八个无冲突的输出目录和实际启动命令准备完毕。
- 已完成：Manager 的 CPU firstfull `6a32847`、full GPU50 和 serial GPU50/restore 验收已同步到发布版 `d85a00d…`；当前运行树仍固定为 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`。
- 已完成：GPU0/1/2/3/6/7 六个正式 20,000-update run 已用独立 exp_name 启动、可靠 detach，并登记到 MAM；GPU4/5 未启动。
- 已完成：截至 `2026-09-10T08:33:03+08:00`，full/no-memory 五项已到 251–266 updates，serial 到 110 updates。进度日志持续更新且未见 `Traceback`、`ERROR`、`nan` 或 `inf`；六项均稳定约 3.7–3.8 s/update。
- 待补充：当前 `tqdm_loggable` 重定向日志只持久化 progress 行，未写入 `pbar.write` 的 Step-100 标量 loss 行；因此持续观察运行时异常和非有限标记，不重启或改变已放行 run 的 logging/model/data 参数。
- 未完成：`assets/memory_v1/rmbench_put_back_block_robot/norm_stats.json` 当前缺失，GPU4/5 即使获路径放行也必须先重新核对该资产；绝不复用 rearrange norm。

## 正式运行状态

| GPU | config / seed | exp_name | remote PID | MAM job | 启动与当前进度 | 当前 ETA |
| --- | --- | --- | ---: | --- | --- | --- |
| 0 | full t+1 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s0` | 4186829 | `89dcc92f-365e-409a-87d3-e6e82b66adba` | 08:08 启动；254 updates | 约 20h29m |
| 1 | full t+30 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s0` | 4186841 | `db46bdd0-0ec2-41c1-9c98-baca9ffd6f5b` | 08:08 启动；254 updates | 约 20h24m |
| 2 | serial lag30 / 0 | `memory20k_e7e5ac54_rearrange_serial_lag30_s0` | 9003 | `d682fab7-3cbc-4b7e-a31a-b959bbd2695c` | 08:18 启动；110 updates | 约 20h36m |
| 3 | no-memory / 0 | `memory20k_e7e5ac54_rearrange_no_memory_s0` | 4186839 | `2774d038-5a23-4184-b16a-92fa1fd88019` | 08:08 启动；251 updates | 约 20h50m |
| 6 | full t+1 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s1` | 4186835 | `95a88ee3-1a90-4e2e-baa1-50a1cd6f4eb0` | 08:08 启动；266 updates | 约 20h11m |
| 7 | full t+30 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s1` | 4186832 | `fa1d8437-1fb7-48a5-8d37-2233e8e06767` | 08:08 启动；266 updates | 约 20h07m |

所有六项使用 `CUDA_VISIBLE_DEVICES=<分配卡>`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`、`HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot`、`OPENPI_DATA_HOME=/mnt/public/cache/openpi`，从本任务固定 worktree 的独立 `.venv/bin/python -B` 启动。GPU0/1/2/3/6/7 已分别持有约 73.4–73.5 GiB 显存；GPU4/5 保持空闲。

## workspace、各库交付 commit

- openpi worktree：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi`
- branch：`task/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe`；HEAD/base：`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，未修改源码。
- `.venv/bin/python scripts/worktree_env_smoke.py` 在本机和 `wuwen-1` 均通过；两端 editable `openpi` / `openpi_client` 都解析到本任务 worktree。远端解释器为该树的 `.venv/bin/python`。

## CPU、数据和 Memory v1 核对

- CPU CLI 已用 `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu` 调用 `scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --help`。确认 `--exp-name`、`--seed`、`--no-wandb-enabled` 可用；本批 config 默认 batch=32、`num_train_steps=20000`、`save_interval=20000`、`save_full_state=False`、`save_dtype=bfloat16`、`fsdp_devices=1`。
- 新 sim 输入没有 fallback 到 `demo_clean`：六个 config 分别绑定 `rearrange_blocks_demo_clean_state_shared_memory` 或 `put_back_block_demo_clean_state_shared_memory`。转换器 `validate_converted_dataset` 会拒绝 `task_config != demo_clean_state`；两份 sidecar 均记录 `task_config: demo_clean_state` 和相应的 `raw_metadata_root`。
- LeRobot 根 `HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot` 在本机和远端均可由 metadata API 打开：rearrange 50 episodes / 20,103 frames，put-back 50 episodes / 17,588 frames。两份 sidecar 在远端可读；其 `M` query / `M+1` series 留痕与任务要求一致。
- 远端 CPU 下六个 config 都可解析并创建 MemoryDataAdapter，sidecar 路径指向本树 `data/memory_v1/rmbench/<repo_id>/episode_memory.json`。rearrange 的 robot-only norm 可读且只含 `state`、`actions`，每个 mean/std/q01/q99 为 14 维；base 参数完成标记可读。

## 远端资源快照

采样于 `2026-09-10T07:53:19+08:00`，只读检查、未分配 GPU：`wuwen-1` 的 GPU0..7 均为 A100-SXM4-80GB，单卡 `memory.used=4 MiB`、`memory.free=81,046 MiB`、utilization=0。主机可用 RAM 895 GiB，`/mnt/public` 可用 9.2 TiB；`logs/` 可写且 `/usr/bin/setsid` 存在。此为快照，正式每一路启动前仍要重新检查实际显存，且不根据进程列表推断空闲。

## 统一启动上下文（仅在 Manager 单路径放行后执行）

所有命令从 `wuwen-1` 上的固定树执行；不设 `JAX_PLATFORMS=cpu`，不传 `--overwrite` / `--resume`，所以已有目录会拒绝混写。`scripts/train.py` 的现有 checkpoint metadata 会保存实际 command、cwd、commit、resolved TrainConfig、dataset metadata 与 sidecar metadata。

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1
```

每条实际命令用 `nohup setsid` 脱离短 session；启动后记录 shell 返回的真实 PID，并从管理机执行对应的 `mam job add e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe --host wuwen-1 --pid <pid> --note "..."`。

```bash
# GPU0
CUDA_VISIBLE_DEVICES=0 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_1_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0.log 2>&1 &

# GPU1
CUDA_VISIBLE_DEVICES=1 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_30 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_30_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0.log 2>&1 &

# GPU2
CUDA_VISIBLE_DEVICES=2 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_serial_lag30 --exp-name=memory20k_e7e5ac54_rearrange_serial_lag30_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_serial_lag30_s0.log 2>&1 &

# GPU3
CUDA_VISIBLE_DEVICES=3 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_no_memory --exp-name=memory20k_e7e5ac54_rearrange_no_memory_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_no_memory_s0.log 2>&1 &

# GPU4 — additionally requires put-back norm to exist at launch time
CUDA_VISIBLE_DEVICES=4 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_1 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_1_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_put_back_full_t_plus_1_s0.log 2>&1 &

# GPU5 — additionally requires put-back norm to exist at launch time
CUDA_VISIBLE_DEVICES=5 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_30 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_30_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_put_back_full_t_plus_30_s0.log 2>&1 &

# GPU6
CUDA_VISIBLE_DEVICES=6 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_1_s1 --seed=1 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1.log 2>&1 &

# GPU7
CUDA_VISIBLE_DEVICES=7 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_30 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_30_s1 --seed=1 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1.log 2>&1 &
```

## 八个独立输出

所有相对路径以上述 fixed worktree 为根；`checkpoints` 与 `logs` 是共享源树软链接，因此正式产物实际保留在 `/mnt/public/xcj/Projects/openpi/`。远端已逐项确认八个 checkpoint 目录均不存在。

| GPU | config / seed | exp_name | checkpoint（完成后唯一的 20000） | log |
| --- | --- | --- | --- | --- |
| 0 | rearrange full t+1 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0.log` |
| 1 | rearrange full t+30 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0.log` |
| 2 | rearrange serial lag30 / 0 | `memory20k_e7e5ac54_rearrange_serial_lag30_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/memory20k_e7e5ac54_rearrange_serial_lag30_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_serial_lag30_s0.log` |
| 3 | rearrange no-memory / 0 | `memory20k_e7e5ac54_rearrange_no_memory_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_no_memory/memory20k_e7e5ac54_rearrange_no_memory_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_no_memory_s0.log` |
| 4 | put-back full t+1 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000` | `logs/memory20k_e7e5ac54_put_back_full_t_plus_1_s0.log` |
| 5 | put-back full t+30 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_30_s0` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s0/20000` | `logs/memory20k_e7e5ac54_put_back_full_t_plus_30_s0.log` |
| 6 | rearrange full t+1 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s1` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1.log` |
| 7 | rearrange full t+30 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s1` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1.log` |

下一检查时间：约 `2026-09-10T09:33:00+08:00` 做首个小时巡检；任何 MAM job attention、显存异常或 Manager 新路径授权均立即检查。GPU4/5 继续等待 put-back norm / loader 证据，绝不提前启动。
