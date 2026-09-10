task_revision: a32c69c813e7e7f66c4b199859d799bdbccc15f9

# 首批 Memory 20k：八路正式执行

## 完成与未完成

- 已完成：八个正式单卡 batch32、20,000-update run 已通过独立 worktree/解释器、独立 exp_name 可靠 detach，并登记到 MAM。CPU firstfull `6a32847`、full/serial GPU50/restore 和 put-back loader 的授权沿发布 task 执行。
- 本次为计划中 `10:02` 小时巡检：MAM 于 `2026-09-10T10:02:11–12+08:00` 核验八个原 PID/进程身份均为 `running`；日志、资源与 `/proc` 只读快照采样于 `10:03:15+08:00`。八路 progress 较 09:01 全部增加，最新日志距采样 2.3–10.6 秒，未见 Traceback/CUDA/OOM 错误行。
- GPU4 最新落盘 `Step 1000: grad_norm=0.0779, loss=0.0059, param_norm=1802.4484`；GPU5 最新落盘 `Step 1100: grad_norm=0.0743, loss=0.0051, param_norm=1802.4668`。逐条解析 GPU4 的 10 条（100–1000）、GPU5 的 11 条（100–1100）标量，数值均有限；这是已落盘的区间均值证据，不扩展成每个 update 的原始 loss 证明。
- 旧 GPU0/1/2/3/6/7 的 Step 标量计数仍全部为零：optimizer progress 已前进，有限 loss 尚未由落盘标量证实。此前只读核对的 stdout 缓冲解释仍适用：`tqdm.write` 默认 stdout 且不强制 flush，progress 交给 logger；无 nan/inf 文本不能替代有限 loss 证据。
- 冻结核验：远端 HEAD=`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，`git diff --name-status HEAD` 与 `git status --porcelain=v1 --untracked-files=normal` 输出均为空。八 PID 的 cwd 均为本任务固定树，实际命令/分配 GPU/HF 与数据根一致，未设置外部 PYTHONPATH。
- put-back norm SHA-256 再次核验为 `7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`。GPU4/5 于 `08:47` 使用 `.venv/bin/python -u -B` 启动，旧六路保持原 `-B`。Manager 本轮告知主树已合入 `a869498` 并获 CPU GO，本运行树继续固定 d10。
- 未完成：八路 20k、最终唯一 20000 checkpoint、完整参数/BF16/无 optimizer 与 checkpoint-only 恢复验收、评测交接。此次仅巡检与发布报告，无注入、重启或额外训练。

## 正式运行状态

| GPU | config / seed | exp_name | remote PID | MAM job | 启动与当前进度 | 当前 ETA |
| --- | --- | --- | ---: | --- | --- | --- |
| 0 | full t+1 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s0` | 4186829 | `89dcc92f-365e-409a-87d3-e6e82b66adba` | 10:03；约 1.70k updates，3.7 s/update；标量未落盘 | 约 18h59m |
| 1 | full t+30 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s0` | 4186841 | `db46bdd0-0ec2-41c1-9c98-baca9ffd6f5b` | 10:03；约 1.71k updates，3.7 s/update；标量未落盘 | 约 18h54m |
| 2 | serial lag30 / 0 | `memory20k_e7e5ac54_rearrange_serial_lag30_s0` | 9003 | `d682fab7-3cbc-4b7e-a31a-b959bbd2695c` | 10:03；约 1.56k updates，3.7 s/update；标量未落盘 | 约 19h07m |
| 3 | no-memory / 0 | `memory20k_e7e5ac54_rearrange_no_memory_s0` | 4186839 | `2774d038-5a23-4184-b16a-92fa1fd88019` | 10:03；约 1.68k updates，3.8 s/update；标量未落盘 | 约 19h15m |
| 4 | put-back full t+1 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` | 12435 | `463092be-02b4-4bfa-bf12-8eae2416a244` | 10:03；约 1.08k updates，3.8 s/update；loss=0.0059@1000 | 约 20h02m |
| 5 | put-back full t+30 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_30_s0` | 12436 | `6e2601ea-e091-4e63-9c31-e90895ca5ffe` | 10:03；约 1.10k updates，3.8 s/update；loss=0.0051@1100 | 约 19h51m |
| 6 | full t+1 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s1` | 4186835 | `95a88ee3-1a90-4e2e-baa1-50a1cd6f4eb0` | 10:03；约 1.74k updates，3.7 s/update；标量未落盘 | 约 18h38m |
| 7 | full t+30 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s1` | 4186832 | `fa1d8437-1fb7-48a5-8d37-2233e8e06767` | 10:03；约 1.75k updates，3.6 s/update；标量未落盘 | 约 18h30m |

progress 的 `kit` 为日志三位有效数字取整，表中保留约数；ETA 取日志按近期稳定速率计算的剩余时间并四舍五入到分钟，瞬时会有波动。旧六路当前约 1.56k–1.75k，相较 09:01 的 572–737 updates 已持续前进。

八项实际使用 `CUDA_VISIBLE_DEVICES=<分配卡>`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`、`HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot`、`OPENPI_DATA_HOME=/mnt/public/cache/openpi`，均从本任务固定 worktree 的独立解释器启动。GPU0/1/2/3/6/7 使用原实际 `.venv/bin/python -B`；GPU4/5 使用实际 `.venv/bin/python -u -B`。

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

`2026-09-10T10:03:15+08:00`：八卡各有且仅有对应已登记训练 PID，GPU 内存使用 73,489–73,507 MiB（约 71.8 GiB；更正此前把 MiB/1000 标为 GiB 的单位），空闲 7,543–7,561 MiB；八卡利用率均 100%，温度 51–68°C。主机 MemAvailable=831,395,431 KiB（约 792.9 GiB），无 swap；`/mnt/public` 可用 10,014,271,995,904 bytes（约 9.11 TiB）。资源未见压力异常。

历史准备快照：

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

下一检查：计划 `2026-09-10T11:02:00+08:00` 做八路小时巡检，由 Manager 按计划唤醒；如收到 MAM job attention 或异常通知则提前处理。
