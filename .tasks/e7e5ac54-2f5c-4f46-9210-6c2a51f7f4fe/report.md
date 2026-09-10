# Memory 20k：远端八路与本机六路

## 9月11日00:32 十四路小时巡检

已读最新任务的项目配置迁移和收尾要求；当前管理仓库分支为project/state-vla，直接使用mam，无--root。按Manager指示沿用其已确认16个job均running的状态，本轮没有重复MAM全量job探测；本任务范围仍为14路，检查其最新日志与必要资源快照。

实际快照 `2026-09-11T00:33:20–21+08:00`：14路日志更新较上次全部前进，最新日志距采样0.7–10.9秒；未见Traceback/CUDA error/OOM/RESOURCE_EXHAUSTED错误，未见20k完成或提前结束迹象。本轮没有触发结束后的清理或归档。

| host/GPU | config / seed | PID | MAM job | 最新 updates | 最新可见 loss@step | s/update | 剩余 ETA |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| wuwen-1/0 | rearrange full t+1 / 0 | 4186829 | `89dcc92f-365e-409a-87d3-e6e82b66adba` | 约 15.7k | 未落盘 | 3.7 | 约 4h30m |
| wuwen-1/1 | rearrange full t+30 / 0 | 4186841 | `db46bdd0-0ec2-41c1-9c98-baca9ffd6f5b` | 约 15.7k | 未落盘 | 3.7 | 约 4h24m |
| wuwen-1/2 | rearrange serial lag30 / 0 | 9003 | `d682fab7-3cbc-4b7e-a31a-b959bbd2695c` | 约 15.6k | 未落盘 | 3.7 | 约 4h34m |
| wuwen-1/3 | rearrange no-memory / 0 | 4186839 | `2774d038-5a23-4184-b16a-92fa1fd88019` | 约 15.5k | 未落盘 | 3.8 | 约 4h45m |
| wuwen-1/4 | put-back full t+1 / 0 | 12435 | `463092be-02b4-4bfa-bf12-8eae2416a244` | 约 14.8k | 0.0009@14700 | 3.8 | 约 5h31m |
| wuwen-1/5 | put-back full t+30 / 0 | 12436 | `6e2601ea-e091-4e63-9c31-e90895ca5ffe` | 约 15.1k | 0.0008@15100 | 3.7 | 约 5h01m |
| wuwen-1/6 | rearrange full t+1 / 1 | 4186835 | `95a88ee3-1a90-4e2e-baa1-50a1cd6f4eb0` | 约 15.9k | 未落盘 | 3.7 | 约 4h08m |
| wuwen-1/7 | rearrange full t+30 / 1 | 4186832 | `fa1d8437-1fb7-48a5-8d37-2233e8e06767` | 约 16.0k | 未落盘 | 3.7 | 约 4h02m |
| 本机/0 | put-back full t+30 / 2 | 2944062 | `dcb7d214-5351-4301-b0cd-1bac56f59de3` | 约 8.12k | 0.0014@8100 | 3.7 | 约 12h03m |
| 本机/1 | put-back full t+1 / 2 | 2918573 | `ee13298c-d10c-4fa4-9be9-875b417fb9a1` | 约 8.44k | 0.0015@8400 | 3.7 | 约 11h56m |
| 本机/4 | rearrange full t+1 / 2 | 2467720 | `b3d46ac6-b2b7-4ea2-b3ad-df74a2bdac7e` | 约 13.3k | 0.0011@13300 | 3.7 | 约 6h50m |
| 本机/5 | rearrange full t+30 / 2 | 2467721 | `0c82949f-f5c6-4772-aea6-1967e9cc2680` | 约 13.2k | 0.0012@13100 | 3.7 | 约 7h04m |
| 本机/6 | put-back full t+1 / 1 | 2467722 | `f04d1b9c-4a77-4034-ac6c-c7240d9b20a8` | 约 13.3k | 0.0009@13300 | 3.7 | 约 6h49m |
| 本机/7 | put-back full t+30 / 1 | 2467723 | `3e67c9de-fc4f-4a94-a2da-7dccbdec9b2e` | 约 13.2k | 0.0011@13200 | 3.7 | 约 7h01m |

kit为日志三位有效数字取整，保留约数；ETA按近期速率估计并四舍五入至分钟，不计最终保存。当前约3.7–3.8秒/update。wuwen-1预计今日04:35–06:04完成更新，当前未见超过中午12:00预留截止时间的风险；本机GPU4–7约07:23–07:37，GPU0/1约12:30–12:36完成更新。

远端GPU4/5各147/151条、本机GPU0/1各81/84条、本机GPU4/5/6/7各133/131/133/132条已落盘loss/grad_norm/param_norm全部有限。最新完整标量：

| host/GPU | Step | loss | grad_norm | param_norm |
| --- | ---: | ---: | ---: | ---: |
| wuwen-1/4 | 14700 | 0.0009 | 0.0344 | 1804.2338 |
| wuwen-1/5 | 15100 | 0.0008 | 0.0347 | 1804.1329 |
| 本机/0 | 8100 | 0.0014 | 0.0404 | 1803.5745 |
| 本机/1 | 8400 | 0.0015 | 0.0397 | 1803.6788 |
| 本机/4 | 13300 | 0.0011 | 0.0410 | 1804.2540 |
| 本机/5 | 13100 | 0.0012 | 0.0399 | 1804.2114 |
| 本机/6 | 13300 | 0.0009 | 0.0328 | 1804.1178 |
| 本机/7 | 13200 | 0.0011 | 0.0374 | 1804.0134 |

以上为已落盘区间均值，不能扩展成每个update原始loss证明。旧远端GPU0/1/2/3/6/7的Step标量仍各为零，有限loss尚未证实；保留stdout缓冲边界，不注入/重启。

两机运行树HEAD均为 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status为空。本轮未更换源码、修改参数、启动新任务或重复smoke。训练尚未完成：结束后核对退出状态、唯一20000 BF16 checkpoint/metadata及完整参数/无optimizer/恢复要求，检查登记进程及子进程退出和显存释放，仅清理确认属于本任务的残留并留痕。wuwen-1自然结束保存释放后整机空闲，不再启动GPU任务；本机八卡可按授权接续，启动前核对资源。

## GPU0 配对项启动（发布 task 的 16:11 授权段）

已读取发布 `7a4f4bcbc54871434f70a43e1be6dd72ee068b97` 的 GPU0 放行要求。实际启动主机时钟为 `2026-09-10T16:10:23+08:00`，启动既定 Q2 put-back full_t_plus_30 seed2，与 GPU1 的 t+1 seed2 配对，不扩展实验清单。

启动前本机 GPU0 已用1 MiB、空闲81,038 MiB、利用率0；MemAvailable=886,691,171 KiB。固定 worktree HEAD=`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status 为空；解释器可执行，put-back norm SHA-256=`7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`。独立日志和 checkpoint exp 目录均未存在，未覆盖或混写。

- host：`is-dcfi2kjdq7g3k6aa-devmachine-0`；GPU0；PID/session ID：`2944062`；start_ticks：`27664648`。
- MAM job：`dcb7d214-5351-4301-b0cd-1bac56f59de3`；16:10:52 登记实时状态 running。
- config：`pi05_rmbench_put_back_block_full_t_plus_30`；seed2；exp_name：`memory20k_e7e5ac54_put_back_full_t_plus_30_s2`。
- 实际日志：`/mnt/public/xcj/Projects/openpi/logs/memory20k_e7e5ac54_put_back_full_t_plus_30_s2.log`。
- 最终 checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s2/20000`。

沿原 d10 配置：单GPU batch32、实际20k updates、同 pi05_base/demo_clean_state/norm、H50/K30，save_full_state=False、save_dtype=bfloat16、save_interval=20000，仅最终模型和metadata；未重跑门禁或改源码。用一次性 subprocess.Popen、start_new_session=True、stdin=DEVNULL、排他创建日志、stderr=STDOUT、close_fds=True 脱离工具会话。实际 command/cwd/env：

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1
unset JAX_PLATFORMS PYTHONPATH
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_30 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_30_s2 --seed=2 --no-wandb-enabled
```

首次检查于 `2026-09-10T16:26:41+08:00` 完成，仅检查新增 GPU0。通过 `mam job status dcb7d214-5351-4301-b0cd-1bac56f59de3` 获取实时 JSON：running、checked_at=16:26:41，原 PID/boot_id/start_ticks 身份匹配；进程状态 R，cwd、实际 command、GPU/env 与登记一致，日志确认 local_batch_size: 32。

首个真实 optimizer update 日志为16:14:59（1 update）；最新16:26:32为135 updates，最近129/132/135 updates均约3.7秒/update，日志剩余ETA为20:13:14（约20h13m，预计9月11日12:40左右完成更新，不计最终保存）。Step100已实际落盘 `grad_norm=1.1468, loss=0.1493, param_norm=1802.3861`，三项均有限；这是区间均值证据。未见Traceback/CUDA/OOM等错误，最新日志距采样8.9秒。

GPU0已用73,405 MiB、空闲7,633 MiB、利用率100%、59°C；MemAvailable=876,849,534 KiB（约836.2 GiB）。HEAD仍为d10cc01完整SHA，git status为空，put-back norm hash保持7a014e42...。本次启动登记与首次真实更新/有限loss检查均完成；原十三路本轮未提前复查，未改源码/参数或重复门禁。该次首次检查约定16:57合并巡检（已完成，见首节）；实时结构化状态继续使用job status，不解析job list表格。

## 15:41 授权的本机 GPU1：put-back t+1 seed2 启动

已读发布 task `a3a5c390b8daac7f74637988edd712142c5c16af` 末节授权，于 `2026-09-10T15:42:52+08:00` 启动既定 Q2 剩余的 put-back full_t_plus_1 seed2。启动前 GPU1 实测已用 1 MiB、空闲 81,038 MiB、利用率 0；MemAvailable=885,382,269 KiB。固定树 HEAD 为 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status 为空，解释器可执行；put-back norm SHA-256 为 `7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`。独立 log/checkpoint exp 路径均未存在。

- host：`is-dcfi2kjdq7g3k6aa-devmachine-0`；GPU1；PID/session ID：`2918573`；start_ticks：`27499635`。
- MAM job：`ee13298c-d10c-4fa4-9be9-875b417fb9a1`，15:43:16 登记实时确认 running。
- config：`pi05_rmbench_put_back_block_full_t_plus_1`；seed2；exp_name：`memory20k_e7e5ac54_put_back_full_t_plus_1_s2`。
- log：`/mnt/public/xcj/Projects/openpi/logs/memory20k_e7e5ac54_put_back_full_t_plus_1_s2.log`。
- 最终 checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s2/20000`。
- 原 config/环境：batch32、实际20k updates、H50/K30、同 pi05_base/demo_clean_state/norm，save_full_state=False、save_dtype=bfloat16、save_interval=20000；未改源码或重复50step。

实际 cwd 为本任务 d10 固定 openpi worktree；通过一次性 subprocess.Popen、start_new_session=True、stdin=DEVNULL、stdout=独占创建的日志、stderr=STDOUT、close_fds=True 脱离短工具会话。实际 command/env：

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1
unset JAX_PLATFORMS PYTHONPATH
CUDA_VISIBLE_DEVICES=1 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_1 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_1_s2 --seed=2 --no-wandb-enabled
```

15:58:21 合并快照首次确认：新路原 PID 身份、cwd/command/env 均匹配，日志确认 local_batch_size: 32，15:58:12 已完成 119 次真实 optimizer update，近期 3.7 秒/update，剩余 ETA 约 20h25m。Step100 实际落盘 grad_norm=1.1383、loss=0.1523、param_norm=1802.3861，三项均有限。GPU1 已用 73,405 MiB、空闲 7,633 MiB、利用率100%、67°C，未见训练错误；未提前轮询原十二路。截至该15:58快照，配对项未获授权；最新GPU0授权/启动见报告首节。

## 本机四路启动留痕（10:39 授权，10:58 已验收）

本机 host=`is-dcfi2kjdq7g3k6aa-devmachine-0`。四路均于 `2026-09-10T10:42:31+08:00` 启动并登记本机 MAM job；全部来自原 Q2 预算。10:40–10:42 启动核验：GPU4–7 各占 1 MiB、空闲 81,038 MiB、利用率 0，RAM MemAvailable=942,653,119 KiB（约 899 GiB）；四组 checkpoint/log 路径均不存在。固定 worktree HEAD=`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status 为空；解释器、两份已验收 norm 沿用原环境。

put-back norm SHA-256=`7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`；rearrange norm SHA-256=`5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b`。本机启动轮次未重跑 50gate、重建环境或变更源码，也未另读远端进度/标量/显存；入口 mam task status 当时会自动探测已登记 PID。本节仅保留已获 Manager 接受的 10:58 本机启动结果；本次十二路最新状态见上表。

`10:58:36+08:00` 首次验证完成：四个原 PID 均存活，`start_ticks=25697503` 与 MAM 登记身份一致，实际 cwd/解释器、GPU 编号、seed 与命令一致；四路日志均确认 batch32。首个 optimizer progress：GPU4=10:48:08，GPU5=10:48:14，GPU6/7=10:47:30。各路均已越过 100 updates，Step 100 的 loss/grad_norm/param_norm 已实际落盘且全部有限。

| 本机 GPU | config / seed | PID | MAM job | 10:58 updates | Step-100 loss | 10:58 稳定 s/update | 10:58 剩余 ETA |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| 4 | rearrange full t+1 / 2 | 2467720 | `b3d46ac6-b2b7-4ea2-b3ad-df74a2bdac7e` | 116 | 0.1497 | 3.706 | 约 20h28m |
| 5 | rearrange full t+30 / 2 | 2467721 | `0c82949f-f5c6-4772-aea6-1967e9cc2680` | 113 | 0.1482 | 3.749 | 约 20h43m |
| 6 | put-back full t+1 / 1 | 2467722 | `f04d1b9c-4a77-4034-ac6c-c7240d9b20a8` | 131 | 0.1521 | 3.703 | 约 20h26m |
| 7 | put-back full t+30 / 1 | 2467723 | `3e67c9de-fc4f-4a94-a2da-7dccbdec9b2e` | 131 | 0.1491 | 3.732 | 约 20h36m |

Step-100 完整标量：GPU4 `grad_norm=0.9720, loss=0.1497, param_norm=1802.3862`；GPU5 `grad_norm=0.9748, loss=0.1482, param_norm=1802.3861`；GPU6 `grad_norm=1.1473, loss=0.1521, param_norm=1802.3861`；GPU7 `grad_norm=1.1548, loss=0.1491, param_norm=1802.3861`。这是四路各自首个已落盘区间均值，未用“没有 nan 文本”替代数值证据。

10:58 启动检查的稳定耗时取 30 updates 以后最近 16 个 progress 间隔的每 update 耗时中位数，ETA=(20000−当前进度)×稳定耗时；未用初始加载/编译阶段外推。预计完成落在 `2026-09-11 07:24–07:42+08:00`，仍以之后稳定吞吐及最终保存为准。10:58 资源：本机四卡各用 73,406 MiB、空闲 7,633 MiB、利用率 100%，温度 60–72°C；MemAvailable=877,748,034 KiB（约 837.1 GiB）。固定树 HEAD 再次核验为 d10，git status 为空。

实际启动采用一次性 `subprocess.Popen`，`start_new_session=True`、`stdin=DEVNULL`、`stdout=各自日志`、`stderr=STDOUT`、`close_fds=True`；日志通过排他 `open('x')` 创建。四 PID 的 session ID 均等于自身 PID，脱离启动工具会话。未创建通用 launcher 文件。以下为实际 command/cwd/env：

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1

CUDA_VISIBLE_DEVICES=4 .venv/bin/python -u -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_1_s2 --seed=2 --no-wandb-enabled
CUDA_VISIBLE_DEVICES=5 .venv/bin/python -u -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_30 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_30_s2 --seed=2 --no-wandb-enabled
CUDA_VISIBLE_DEVICES=6 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_1 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_1_s1 --seed=1 --no-wandb-enabled
CUDA_VISIBLE_DEVICES=7 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_30 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_30_s1 --seed=1 --no-wandb-enabled
```

与原 config 相同：batch32、20,000 optimizer updates、H50/K30、单卡、从 pi05_base 初始化，`save_interval=20000`、`save_full_state=False`、`save_dtype=bfloat16`；只变 seed 与 exp_name。两份 sim 数据仍为 demo_clean_state。

| 本机 GPU | 独立 exp_name | 完成后 checkpoint（相对共享 `/mnt/public/xcj/Projects/openpi/`） |
| --- | --- | --- |
| 4 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s2` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s2/20000` |
| 5 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s2` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s2/20000` |
| 6 | `memory20k_e7e5ac54_put_back_full_t_plus_1_s1` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s1/20000` |
| 7 | `memory20k_e7e5ac54_put_back_full_t_plus_30_s1` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s1/20000` |

四份实际日志为 `/mnt/public/xcj/Projects/openpi/logs/<上表 exp_name>.log`。本节启动时 GPU0/1 分配 F0、GPU2/3 分配 wash；当前分配以本次巡检节的 Manager 更新为准。

## 远端八路启动留痕

八个正式单卡 batch32、20,000-update run 已从本任务独立 worktree/解释器、独立 exp_name 可靠 detach，并登记到 MAM；当前 PID、job 和进度见本次十二路表。CPU firstfull `6a32847`、full/serial GPU50/restore 和 put-back loader 的授权沿发布 task 执行。GPU4/5 于 08:47 使用 `.venv/bin/python -u -B` 启动，旧六路保持实际 `.venv/bin/python -B`。

八项实际使用 `CUDA_VISIBLE_DEVICES=<分配卡>`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`、`HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot`、`OPENPI_DATA_HOME=/mnt/public/cache/openpi`，均从本任务固定 worktree 的独立解释器启动。Manager 已告知主树合入 `a869498` 并获 CPU GO，本运行树继续固定 d10。最新远端八路状态见本次合并巡检表。

## workspace、各库交付 commit

- openpi worktree：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi`
- branch：`task/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe`；HEAD/base：`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，未修改源码。
- `.venv/bin/python scripts/worktree_env_smoke.py` 在本机和 `wuwen-1` 均通过；两端 editable `openpi` / `openpi_client` 都解析到本任务 worktree。远端解释器为该树的 `.venv/bin/python`。

## CPU、数据和 Memory v1 核对

- CPU CLI 已用 `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu` 调用 `scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --help`。确认 `--exp-name`、`--seed`、`--no-wandb-enabled` 可用；本批 config 默认 batch=32、`num_train_steps=20000`、`save_interval=20000`、`save_full_state=False`、`save_dtype=bfloat16`、`fsdp_devices=1`。
- 新 sim 输入没有 fallback 到 `demo_clean`：六个 config 分别绑定 `rearrange_blocks_demo_clean_state_shared_memory` 或 `put_back_block_demo_clean_state_shared_memory`。转换器 `validate_converted_dataset` 会拒绝 `task_config != demo_clean_state`；两份 sidecar 均记录 `task_config: demo_clean_state` 和相应的 `raw_metadata_root`。
- LeRobot 根 `HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot` 在本机和远端均可由 metadata API 打开：rearrange 50 episodes / 20,103 frames，put-back 50 episodes / 17,588 frames。两份 sidecar 在远端可读；其 `M` query / `M+1` series 留痕与任务要求一致。
- 远端 CPU 下六个 config 都可解析并创建 MemoryDataAdapter，sidecar 路径指向本树 `data/memory_v1/rmbench/<repo_id>/episode_memory.json`。rearrange 的 robot-only norm 可读且只含 `state`、`actions`，每个 mean/std/q01/q99 为 14 维；base 参数完成标记可读。

## 00:33:20–21 两机资源快照

| host / GPU | 每卡已用 / 空闲 MiB | 利用率 | 温度 | 主机 MemAvailable |
| --- | --- | --- | --- | --- |
| wuwen-1 / 0–7 | 73,489–73,507 / 7,543–7,561 | 全部100% | 51–68°C | 831,292,467 KiB（约 792.8 GiB） |
| 本机 / 0,1,4–7 | 73,405–73,406 / 各7,633 | GPU7为94%，其余100% | 58–71°C | 876,599,438 KiB（约 836.0 GiB） |

共享/mnt/public可用9,994,901,651,456 bytes（约 9.09 TiB），未见资源压力。本轮无异常扩查，norm沿既有已验收资产。

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

下一检查：`2026-09-11T01:32:00+08:00`，远端八路与本机GPU0/1/4–7合并为十四路巡检，由 Manager 按计划唤醒。若收到 MAM job attention 或异常通知则提前处理。十四路的 20k 完成、唯一 20000 BF16 checkpoint、完整参数/无 optimizer/恢复验证与评测交接仍待训练结束后完成。
