task_revision: a32c69c813e7e7f66c4b199859d799bdbccc15f9

# 首批 Memory 20k：八路正式执行

## 完成与未完成

- 已完成：按 task 创建独立 openpi worktree、两端独立解释器与 CPU CLI/data/memory 配置核对、demo_clean_state 来源核实、八个无冲突的输出目录和实际启动命令准备完毕。
- 已完成：Manager 的 CPU firstfull `6a32847`、full GPU50 和 serial GPU50/restore 验收已同步到发布版 `a192a2f…`；当前运行树仍固定为 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`。
- 已完成：GPU0/1/2/3/4/5/6/7 八个正式 20,000-update run 均已用独立 exp_name 启动、可靠 detach，并登记到 MAM。
- 已完成：截至 `2026-09-10T09:01:48+08:00` 的计划内只读巡检，八个 MAM job 均为 `running`；GPU0/1/2/3/4/5/6/7 分别到 713/716/572/707/112/112/737/737 updates，全部持续推进。
- 已完成：只读核对输出通道。非交互式 `tqdm_loggable` 把 progress 交给 logger（落盘行来自 `tqdm_logging.py:145`），而 `scripts/train.py:337` 的标量通过继承的 `tqdm.write` 写到 `sys.stdout`，该方法不强制 flush。六个进程的 fd 1/2 因启动时 `2>&1` 都指向各自 log；目前仅 progress 落盘，符合 stdout 仍缓冲的判断。
- 待补充：现有六路没有从落盘标量取得“loss 为有限数”的证据；日志未出现 `nan`/`inf` 不能替代该证据。保持只读观察，既不重启健康 run，也不向活跃解释器注入代码或变更 logging/model/data 参数。
- 已完成：Manager 于 `08:44` 放行 put-back 两路；远端共享 `assets/memory_v1/rmbench_put_back_block_robot/norm_stats.json` 已只读复核为 SHA-256 `7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`，与发布要求一致。固定树仍为 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`。
- 已完成：GPU4/5 于约 `08:47` 以实际 `.venv/bin/python -u -B` 命令启动。两种 put-back loader 已进入，日志各自确认 `local_batch_size: 32`，GPU4/5 各占约 73.4 GiB。
- 已完成：GPU4/5 均在 `08:52` 通过首次 XLA 编译并实际完成第 1 个 optimizer update；首个 13.2–13.4 s/update 计时包含编译，不用于 ETA。
- 已完成：截至 `08:56:07`，GPU4/5 均已到 22 updates，速率已收敛到约 3.8–3.9 s/update；按当前进度估计剩余约 21h16–21h36。
- 已完成：`-u` 已在 Step 100 落盘有限标量。GPU4 为 `grad_norm=1.1402, loss=0.1549, param_norm=1802.3861`；GPU5 为 `grad_norm=1.1507, loss=0.1521, param_norm=1802.3861`。这只证明新启动的 GPU4/5；六路既有 run 仍保持原先“未取得落盘标量”的边界。
- 待补充：不重启或调整八路的源码、数据、norm 或训练参数；后续按小时只读巡检。

## 正式运行状态

| GPU | config / seed | exp_name | remote PID | MAM job | 启动与当前进度 | 当前 ETA |
| --- | --- | --- | ---: | --- | --- | --- |
| 0 | full t+1 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s0` | 4186829 | `89dcc92f-365e-409a-87d3-e6e82b66adba` | 09:01；713 updates，约 3.8 s/update | 约 20h07m |
| 1 | full t+30 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s0` | 4186841 | `db46bdd0-0ec2-41c1-9c98-baca9ffd6f5b` | 09:01；716 updates，约 3.7 s/update | 约 19h56m |
| 2 | serial lag30 / 0 | `memory20k_e7e5ac54_rearrange_serial_lag30_s0` | 9003 | `d682fab7-3cbc-4b7e-a31a-b959bbd2695c` | 09:01；572 updates，约 3.7 s/update | 约 20h07m |
| 3 | no-memory / 0 | `memory20k_e7e5ac54_rearrange_no_memory_s0` | 4186839 | `2774d038-5a23-4184-b16a-92fa1fd88019` | 09:01；707 updates，约 3.8 s/update | 约 20h17m |
| 4 | put-back full t+1 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` | 12435 | `463092be-02b4-4bfa-bf12-8eae2416a244` | 09:01；112 updates，约 3.8 s/update，Step-100 loss=0.1549 | 约 21h05m |
| 5 | put-back full t+30 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_30_s0` | 12436 | `6e2601ea-e091-4e63-9c31-e90895ca5ffe` | 09:01；112 updates，约 3.7 s/update，Step-100 loss=0.1521 | 约 20h34m |
| 6 | full t+1 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s1` | 4186835 | `95a88ee3-1a90-4e2e-baa1-50a1cd6f4eb0` | 09:01；737 updates，约 3.7 s/update | 约 19h40m |
| 7 | full t+30 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s1` | 4186832 | `fa1d8437-1fb7-48a5-8d37-2233e8e06767` | 09:01；737 updates，约 3.7 s/update | 约 19h33m |

八项实际使用 `CUDA_VISIBLE_DEVICES=<分配卡>`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`、`HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot`、`OPENPI_DATA_HOME=/mnt/public/cache/openpi`，均从本任务固定 worktree 的独立解释器启动。GPU0/1/2/3/6/7 使用原实际 `.venv/bin/python -B`；新放行 GPU4/5 使用实际 `.venv/bin/python -u -B`。09:01 快照八卡均占约 73.49–73.51 GiB、利用率 100%。

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

## 实际启动上下文

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

# GPU4 — 08:47 实际命令，PID 12435
CUDA_VISIBLE_DEVICES=4 nohup setsid .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_1 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_1_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_put_back_full_t_plus_1_s0.log 2>&1 &

# GPU5 — 08:47 实际命令，PID 12436
CUDA_VISIBLE_DEVICES=5 nohup setsid .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_30 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_30_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_put_back_full_t_plus_30_s0.log 2>&1 &

# GPU6
CUDA_VISIBLE_DEVICES=6 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_1_s1 --seed=1 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1.log 2>&1 &

# GPU7
CUDA_VISIBLE_DEVICES=7 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_30 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_30_s1 --seed=1 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1.log 2>&1 &
```

## 八个独立输出

所有相对路径以上述 fixed worktree 为根；`checkpoints` 与 `logs` 是共享源树软链接，因此正式产物实际保留在 `/mnt/public/xcj/Projects/openpi/`。八项已放行 run 均使用下列独立输出；GPU4/5 已在其独立目录启动，不与其他 run 混写。

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

下一检查：约 `2026-09-10T10:02:00+08:00` 做八路小时巡检。任何 MAM job attention 或显存异常均立即检查；不等待 R3/R4/wash。
