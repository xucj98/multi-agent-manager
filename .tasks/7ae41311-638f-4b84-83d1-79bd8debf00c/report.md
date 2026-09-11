# 第二批 B 能力基线训练：rearrange 重复及 put-back serial/no-memory

## 四项启动目的

本任务补齐 B 组中 `rearrange_blocks` 的 serial-lag30 与 no-memory 各三个独立随机种子。既有 `e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe` 已完成两种配置的 seed0；本次在本机 GPU2--5 分别运行 serial-lag30 seed1/2 与 no-memory seed1/2，避免将单个 seed 的随机性误认为表示差异。对应 full 的三 seed 已完成；评测仍待 C 验收，本文不预期成功率。

## 启动前事实核对

- OpenPI 独立 worktree：`/mnt/public/xcj/Projects/workspace/7ae41311-638f-4b84-83d1-79bd8debf00c/openpi`，分支 `task/7ae41311-638f-4b84-83d1-79bd8debf00c`，固定 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，工作树干净。
- 已读取源任务的 serial/no-memory seed0 checkpoint artifacts、日志和 closure evidence。原 run 均完成 20,000 updates，保留 BF16 参数、assets、metadata 与有限标量；本任务不重跑旧 GPU 50-step/恢复门禁。
- 新 worktree 的 `scripts/worktree_env_smoke.py` 已通过。两份实际解析配置均为单卡 batch32、20,000 updates、H50/K30、`save_interval=20000`、`save_full_state=False`、`save_dtype=bfloat16`，从 `pi05_base` 加载，并绑定 `rearrange_blocks_demo_clean_state_shared_memory`、专用 `rmbench_rearrange_blocks_robot` norm。
- 启动前本机 GPU2--5 均为 1 MiB 已用、0% 利用率；共享数据包含 50 个已转换 episode 和 memory sidecar。四个本任务 exp 的日志与 checkpoint 路径均不存在。

## 计划输出

| GPU | config | seed | exp_name | final checkpoint |
| --- | --- | ---: | --- | --- |
| 2 | `pi05_rmbench_rearrange_blocks_serial_lag30` | 1 | `memory20k_7ae41311_pi05_rmbench_rearrange_blocks_serial_lag30_s1` | `checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/memory20k_7ae41311_pi05_rmbench_rearrange_blocks_serial_lag30_s1/20000` |
| 3 | `pi05_rmbench_rearrange_blocks_serial_lag30` | 2 | `memory20k_7ae41311_pi05_rmbench_rearrange_blocks_serial_lag30_s2` | `checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/memory20k_7ae41311_pi05_rmbench_rearrange_blocks_serial_lag30_s2/20000` |
| 4 | `pi05_rmbench_rearrange_blocks_no_memory` | 1 | `memory20k_7ae41311_pi05_rmbench_rearrange_blocks_no_memory_s1` | `checkpoints/pi05_rmbench_rearrange_blocks_no_memory/memory20k_7ae41311_pi05_rmbench_rearrange_blocks_no_memory_s1/20000` |
| 5 | `pi05_rmbench_rearrange_blocks_no_memory` | 2 | `memory20k_7ae41311_pi05_rmbench_rearrange_blocks_no_memory_s2` | `checkpoints/pi05_rmbench_rearrange_blocks_no_memory/memory20k_7ae41311_pi05_rmbench_rearrange_blocks_no_memory_s2/20000` |

## 实际启动与登记

所有 run 从本任务固定 worktree 的独立解释器以一次性 `subprocess.Popen(start_new_session=True, stdin=DEVNULL, stdout=排他创建的独立日志, stderr=STDOUT, close_fds=True)` 启动。训练子进程使用 `.venv/bin/python -u -B`；环境固定 `OPENPI_DATA_HOME=/mnt/public/cache/openpi`、`HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`、`PYTHONDONTWRITEBYTECODE=1`，并清除 `JAX_PLATFORMS`、`PYTHONPATH`。未使用 `--overwrite` 或 `--resume`。

| GPU | config / seed | 本机启动时间 | PID / session | MAM job |
| --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | 2026-09-11 14:29:50 +08:00 | `3955954` / `3955954` | `aa6d7690-dbb1-4b6d-8eb2-46ca63059400` |
| 3 | serial-lag30 / 2 | 2026-09-11 14:30:13 +08:00 | `3956200` / `3956200` | `68ecba3b-e570-4dd4-8cd1-4a82249a515d` |
| 4 | no-memory / 1 | 2026-09-11 14:30:39 +08:00 | `3956476` / `3956476` | `d4ccc2ca-d37a-4d13-89eb-cb4c3ea1598a` |
| 5 | no-memory / 2 | 2026-09-11 14:31:04 +08:00 | `3957417` / `3957417` | `b13b2fbd-ce10-4fac-87d0-62761879e057` |

MAM 在每条启动后立即按真实 host、PID、boot identity 和 start ticks 登记，四个 job 当前均为 `running`。首轮日志已分别在 14:30:51、14:31:17、14:31:45、14:32:10 记录 `local_batch_size: 32`，并确认实际加载 `rearrange_blocks_demo_clean_state_shared_memory` 与 `rmbench_rearrange_blocks_robot`。随后快照中 GPU2--5 各占用 73,363 MiB；仍在初始加载/编译，尚未把该阶段误报为 optimizer update。首个有限标量落盘后补充。

## 首批有效 updates / loss 启动简报

`2026-09-11 14:51:32 +08:00` 同一轮快照中，四路均已跨过 step100，且首个 `loss`、`grad_norm`、`param_norm` 全为有限数值；四个 MAM job 和对应 PID 仍为 `running`。当前 GPU2--5 分别占用 73,407、73,407、73,405、73,405 MiB，利用率均为 100%。未见 traceback 或训练异常。

| GPU | config / seed | PID / MAM job | 首个有效标量（step100） | 当前 step / 稳定吞吐 | 剩余 ETA（该时刻外推） |
| --- | --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | `3955954` / `aa6d7690-dbb1-4b6d-8eb2-46ca63059400` | `grad_norm=53.3776, loss=0.4064, param_norm=1802.3915` | 189 / 4.2 s/update | 22:55:40，约 9月12日 13:47 +08:00 |
| 3 | serial-lag30 / 2 | `3956200` / `68ecba3b-e570-4dd4-8cd1-4a82249a515d` | `grad_norm=32.8460, loss=0.5293, param_norm=1802.3915` | 176 / 4.1 s/update | 22:48:16，约 9月12日 13:40 +08:00 |
| 4 | no-memory / 1 | `3956476` / `d4ccc2ca-d37a-4d13-89eb-cb4c3ea1598a` | `grad_norm=0.5585, loss=0.0510, param_norm=1802.3865` | 198 / 3.7 s/update | 20:18:46，约 9月12日 11:10 +08:00 |
| 5 | no-memory / 2 | `3957417` / `b13b2fbd-ce10-4fac-87d0-62761879e057` | `grad_norm=0.5735, loss=0.0517, param_norm=1802.3865` | 179 / 3.7 s/update | 20:35:28，约 9月12日 11:27 +08:00 |

这些 ETA 仅按当前稳定进度行的吞吐估算，最终以 20,000 保存完成为准。后续改为约每小时巡检；任一路停止、报错或完成会立即处理并更新本文。

## 首个小时巡检（2026-09-11 15:46:48 +08:00）

只读取既有 job、进程、GPU 与训练日志，未重跑任何 GPU 门禁、恢复或数据检查。四个 MAM job 逐一实时刷新均为 `running`，原 PID/session 仍匹配；GPU2--5 分别占用 73,407、73,407、73,405、73,405 MiB，均为 100% 利用率。四份日志未匹配 traceback、OOM、exception 或非有限数值。

| GPU | config / seed | 当前进度 / 稳定吞吐 | 最近有限训练标量 | 剩余 ETA |
| --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | 982 / 4.2 s/update | step900：`grad_norm=1.9051, loss=0.0396, param_norm=1802.4556` | 22:05:21 |
| 3 | serial-lag30 / 2 | 976 / 4.1 s/update | step900：`grad_norm=2.4269, loss=0.0550, param_norm=1802.4596` | 21:53:04 |
| 4 | no-memory / 1 | 1.10k / 3.7 s/update | step1000：`grad_norm=0.0465, loss=0.0036, param_norm=1802.4473` | 19:20:37 |
| 5 | no-memory / 2 | 1.06k / 3.7 s/update | step1000：`grad_norm=0.0459, loss=0.0037, param_norm=1802.4462` | 19:40:52 |

当前没有需要干预的异常，四路按原命令和输出目录继续训练；后续保持约小时巡检，任一路提前停止、异常或完成 20,000 会立即处理并发布更新。
