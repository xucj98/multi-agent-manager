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

## 第二个小时巡检（2026-09-11 16:42:52 +08:00）

本轮只刷新四个 MAM job、读取 GPU/进程状态及既有日志；未改配置、命令、输出目录或数据，也未重跑任何门禁。四个 PID/session 与登记身份一致、job 均为 `running`。GPU2--5 各维持约 73.4 GiB 显存、100% 利用率；日志未匹配 traceback、OOM、exception 或非有限数值。

| GPU | config / seed | 当前进度 / 稳定吞吐 | 最近有限训练标量 | 剩余 ETA |
| --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | 1.79k / 4.2 s/update | step1700：`grad_norm=0.7894, loss=0.0289, param_norm=1802.6827` | 21:03:43 |
| 3 | serial-lag30 / 2 | 1.79k / 4.1 s/update | step1700：`grad_norm=1.0433, loss=0.0260, param_norm=1802.6938` | 20:53:55 |
| 4 | no-memory / 1 | 2.01k / 3.7 s/update | step2000：`grad_norm=0.0365, loss=0.0022, param_norm=1802.6407` | 18:22:56 |
| 5 | no-memory / 2 | 1.96k / 3.7 s/update | step1900：`grad_norm=0.0356, loss=0.0024, param_norm=1802.6219` | 18:46:18 |

四路无异常，按原训练继续；下一个约小时巡检窗口再刷新进度，任一路停止、异常或完成 20,000 会立即处理并发布更新。

## 第三个小时巡检（2026-09-11 17:44:05 +08:00）

本轮仍只读刷新 MAM job、PID/session、GPU 与现有日志；训练配置、命令、数据和输出树均保持冻结，未重跑任何门禁。四个 job 实时状态均为 `running`，GPU2--5 各保持约 73.4 GiB 显存与 100% 利用率，日志未出现 traceback、OOM、exception 或非有限数值。

| GPU | config / seed | 当前进度 / 稳定吞吐 | 最近有限训练标量 | 剩余 ETA |
| --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | 2.67k / 4.2 s/update | step2600：`grad_norm=1.7851, loss=0.0226, param_norm=1802.9341` | 20:02:45 |
| 3 | serial-lag30 / 2 | 2.68k / 4.1 s/update | step2600：`grad_norm=3.8949, loss=0.0313, param_norm=1802.9760` | 19:53:34 |
| 4 | no-memory / 1 | 3.01k / 3.6 s/update | step3000：`grad_norm=0.0335, loss=0.0018, param_norm=1802.8184` | 17:12:45 |
| 5 | no-memory / 2 | 2.95k / 3.7 s/update | step2900：`grad_norm=0.0322, loss=0.0018, param_norm=1802.7966` | 17:41:54 |

四路继续原训练，不作配置或门禁变更；后续约小时巡检，提前停止、异常或完成 20,000 时立即处理并发布结果。


## 第四个小时巡检（2026-09-11 17:47:12 +08:00）

本轮在 17:46 窗口只读刷新四个 MAM job、PID/session、GPU 与现有训练日志。四个 MAM job 于 17:46:49 实时检查均为 running；四个原 PID 与独立 session 仍存在且一致。17:47:05--17:47:09 的日志进度仍在推进，GPU2--5 分别占用 73,407、73,407、73,405、73,405 MiB，利用率均为 100%。日志未匹配 traceback、OOM、未处理 exception、NaN 或非有限训练值。

| GPU | config / seed | 当前进度 / 稳定吞吐 | 最近有限训练标量 | 剩余 ETA（日志估算） | 预计完成时间 |
| --- | --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | 2.71k / 4.2 s/update | step2700：grad_norm=1.0222, loss=0.0263, param_norm=1802.9661 | 19:57:37 | 9月12日 13:44:49 +08:00 |
| 3 | serial-lag30 / 2 | 2.72k / 4.1 s/update | step2700：grad_norm=3.4223, loss=0.0337, param_norm=1803.0096 | 19:51:24 | 9月12日 13:38:36 +08:00 |
| 4 | no-memory / 1 | 3.06k / 3.7 s/update | step3000：grad_norm=0.0335, loss=0.0018, param_norm=1802.8184 | 17:20:05 | 9月12日 11:07:17 +08:00 |
| 5 | no-memory / 2 | 3.00k / 3.7 s/update | step2900：grad_norm=0.0322, loss=0.0018, param_norm=1802.7966 | 17:39:59 | 9月12日 11:27:11 +08:00 |

当前无异常，也未触及完成条件。四路继续按原命令、原配置、原数据和原输出目录训练；不改配置、不重跑门禁。后续保持约小时巡检，若任一路提前停止、异常或完成 20,000，则立即处理并发布。


## 第五个小时巡检（2026-09-11 18:47:22 +08:00）

本轮在 18:46 窗口只读刷新四个 MAM job、PID/session、实际 GPU 归属和现有训练日志。四个 MAM job 于 18:47:22 实时检查均为 running；原 PID、独立 session 与训练命令仍一致，且各 PID 分别仍实际运行在 GPU2--5。18:47:11--18:47:19 的日志均持续推进。GPU2--5 分别占用 73,407、73,407、73,405、73,405 MiB，利用率均为 100%。日志未匹配 traceback、OOM、未处理 exception、NaN 或非有限训练值。

| GPU | config / seed | 当前进度 / 稳定吞吐 | 最近有限训练标量 | 剩余 ETA（日志估算） | 预计完成时间 |
| --- | --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | 3.58k / 4.2 s/update | step3500：grad_norm=0.5066, loss=0.0201, param_norm=1803.1715 | 19:01:13 | 9月12日 13:48:35 +08:00 |
| 3 | serial-lag30 / 2 | 3.59k / 4.1 s/update | step3500：grad_norm=0.4173, loss=0.0185, param_norm=1803.2412 | 18:53:51 | 9月12日 13:41:13 +08:00 |
| 4 | no-memory / 1 | 4.04k / 3.7 s/update | step4000：grad_norm=0.0308, loss=0.0016, param_norm=1802.9790 | 16:18:31 | 9月12日 11:05:53 +08:00 |
| 5 | no-memory / 2 | 3.96k / 3.7 s/update | step3900：grad_norm=0.0287, loss=0.0015, param_norm=1802.9578 | 16:39:46 | 9月12日 11:27:08 +08:00 |

当前无异常，也未触及完成条件。四路继续按原命令、原配置、原数据和原输出目录训练；不改配置、不重跑门禁。后续保持约小时巡检，若任一路提前停止、异常或完成 20,000，则立即处理并发布。


## 恢复核对（2026-09-12 02:58:12 +08:00）

按最新 Manager 待办恢复现有四路训练责任；复用原 OpenPI worktree，未新建任务或 worktree。只读刷新四个 job、PID/session、实际 GPU 归属、训练日志及预期的 20000 输出目录。四个 MAM job 均为 running，原 PID/session 仍在，且各 PID 仍实际对应 GPU2--5；原 worktree 保持干净并固定在 d10cc01d44c10e5ed0cd8c228d9409dd6cabac50。四个预期 20000 checkpoint 目录均尚不存在，因此没有完成项可验收或归档。

| GPU | config / seed | 当前进度 / 吞吐 | 最近有限训练标量 | 剩余 ETA（日志估算） | 预计完成时间 |
| --- | --- | --- | --- | --- | --- |
| 2 | serial-lag30 / 1 | 10.6k / 4.2 s/update | step10600：grad_norm=0.4015, loss=0.0141, param_norm=1804.6017 | 10:50:27 | 9月12日 13:48:39 +08:00 |
| 3 | serial-lag30 / 2 | 10.7k / 4.1 s/update | step10700：grad_norm=0.3384, loss=0.0131, param_norm=1804.8307 | 10:38:13 | 9月12日 13:36:25 +08:00 |
| 4 | no-memory / 1 | 12.0k / 3.7 s/update | step12000：grad_norm=0.0249, loss=0.0008, param_norm=1803.9204 | 8:08:13 | 9月12日 11:06:25 +08:00 |
| 5 | no-memory / 2 | 11.8k / 3.7 s/update | step11800：grad_norm=0.0227, loss=0.0008, param_norm=1803.8953 | 8:27:16 | 9月12日 11:25:28 +08:00 |

GPU2--5 分别占用 73,407、73,407、73,405、73,405 MiB，利用率均为 100%；日志仍推进，未匹配 traceback、OOM、未处理 exception、NaN 或非有限训练值。未停止现场 PM 服务、未修改机器人或训练配置，也未重跑旧门禁。后续使用新版 mam wait 保持 active 等待停止事件；任一路结束后再逐项进行 20000、BF16/有限参数、metadata/assets、单独恢复及资源释放验收，并按要求归档对应 job。


## 临时交接：Manager 接管完成事件（2026-09-12 04:29:44 +08:00）

按 Manager 临时释放 U 组实施名额的安排，本执行者结束 active 等待并交接完成事件。最后一次实际核对在 04:29:44 +08:00：四个登记训练 job 均为 running，四个原 20000 checkpoint 目录均不存在。因此当前没有完成模型可做最终验收、归档或交给 e6908de7 评估队列；本条只交接真实未完成状态，不重复发布无变化巡检。

Manager 接管后续完成事件。训练进程、配置、数据、现场 PM 服务和机器人均未修改或停止；本执行者仅取消自己的 mam wait，不影响四路训练。


## GPU4 no-memory seed1：20000 验收与 e6908de7 评估交接

GPU4 的 MAM wait 停止事件对应 job d4ccc2ca-d37a-4d13-89eb-cb4c3ea1598a。该训练自然结束并已按下列证据验收、归档；未启动任何评测。

### 可评模型清单：交 e6908de7 评估队列

| 字段 | 已核对值 |
| --- | --- |
| config / schema / seed | pi05_rmbench_rearrange_blocks_no_memory / rearrange_blocks_no_memory schema v1 / seed1 |
| 训练 commit | d10cc01d44c10e5ed0cd8c228d9409dd6cabac50，command 记录 clean worktree |
| 绝对 checkpoint | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_no_memory/memory20k_7ae41311_pi05_rmbench_rearrange_blocks_no_memory_s1/20000 |
| 固定训练条件 | Pi0.5 base、batch32、20,000 updates、H50/K30、BF16 final-only；rearrange_blocks_demo_clean_state_shared_memory，rmbench_rearrange_blocks_robot norm |
| 研究目的 | 补齐 B 组 rearrange no-memory 的独立 seed，检验同骨干、同数据和同训练协议下的 seed 级稳定性，避免把 seed0 随机性误判为记忆表示差异。 |
| 评测应检验的结论 | 将其作为 no-memory 可复现基线，与同协议 memory 变体及其它 seed 比较表示差异和方差；不预设或声称闭环成功率。 |

该模型现可由 e6908de7 按其既定“自身 smoke2 后正式 100”队列接入；本任务不重复启动 eval。

### 20000 产物与恢复验收

- 日志明确记录 Step20000：grad_norm=0.0240、loss=0.0004、param_norm=1804.2548；100 至 20000 共 200 条落盘标量均有限，未匹配 traceback、OOM、未处理 exception、NaN 或非有限错误。
- 最终保存已原子提交：checkpoint metadata 含 commit timestamp，父目录仅含 20000；item 仅 params、assets、metadata，无 train_state 或 optimizer。
- checkpoint metadata 中 config、dataset、command 和 norm 证据均可解析：数据为 50 episodes 的 rearrange_blocks_demo_clean_state_shared_memory，norm SHA-256 为 5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b；9 个 JSON、6 个 JSONL、5 个普通 YAML 与带标签 train config 均通过解析。
- 显式 CPU-only 核验（CUDA_VISIBLE_DEVICES 空、JAX cpu）实际读回 51 个参数叶、3,353,433,872 个元素，全部 BF16、全部有限，路径和 shape 与注册模型逐项一致；checkpoint-only standalone Policy 恢复成功。
- 完整审计 JSON：/mnt/public/xcj/Projects/workspace/7ae41311-638f-4b84-83d1-79bd8debf00c/closure/memory20k_7ae41311_rearrange_no_memory_s1.json。
- MAM 复查为 stopped，原 PID 3956476 已不存在且不再占用本任务 GPU4；对应 job 已归档。

同一轮 MAM 实时刷新时 GPU2 serial seed1、GPU3 serial seed2、GPU5 no-memory seed2 仍为 running；它们保持原训练，继续等待各自结束事件。


## GPU5 no-memory seed2：20000 验收与 e6908de7 评估交接

GPU5 的 MAM job `b13b2fbd-ce10-4fac-87d0-62761879e057` 已自然停止。最终 20000 checkpoint 已按下列证据验收并归档；本任务未启动评测。

### 可评模型清单：交 e6908de7 评估队列

| 字段 | 已核对值 |
| --- | --- |
| config / schema / seed | pi05_rmbench_rearrange_blocks_no_memory / rearrange_blocks_no_memory schema v1 / seed2 |
| 训练 commit | d10cc01d44c10e5ed0cd8c228d9409dd6cabac50，command 记录 clean worktree |
| 绝对 checkpoint | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_no_memory/memory20k_7ae41311_pi05_rmbench_rearrange_blocks_no_memory_s2/20000 |
| 固定训练条件 | Pi0.5 base、batch32、20,000 updates、H50/K30、BF16 final-only；rearrange_blocks_demo_clean_state_shared_memory，rmbench_rearrange_blocks_robot norm |
| 研究目的 | 补齐 B 组 rearrange no-memory 的独立 seed，检验同骨干、同数据和同训练协议下的 seed 级稳定性，避免把 seed0 随机性误判为记忆表示差异。 |
| 评测应检验的结论 | 将其作为 no-memory 可复现基线，与同协议 memory 变体及其它 seed 比较表示差异和方差；不预设或声称闭环成功率。 |

该模型现可由 e6908de7-4b02-465a-987b-a19eba7a315a 按其既定“自身 smoke2 后正式 100”队列接入；本任务不重复启动 eval。

### 20000 产物与恢复验收

- 日志明确记录 Step20000：grad_norm=0.0198、loss=0.0004、param_norm=1804.2385；100 至 20000 共 200 条落盘标量均有限，未匹配 traceback、OOM、未处理 exception、NaN 或非有限错误。
- 最终保存已原子提交：checkpoint metadata 含 commit timestamp，父目录仅含 20000；item 仅 params、assets、metadata，无 train_state 或 optimizer。
- checkpoint metadata 中 config、dataset、command 和 norm 证据均可解析：数据为 50 episodes 的 rearrange_blocks_demo_clean_state_shared_memory，norm SHA-256 为 5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b；9 个 JSON、6 个 JSONL、5 个普通 YAML 与带标签 train config 均通过解析。
- 显式 CPU-only 核验（CUDA_VISIBLE_DEVICES 空、JAX cpu）实际读回 51 个参数叶、3,353,433,872 个元素，全部 BF16、全部有限，路径和 shape 与注册模型逐项一致；checkpoint-only standalone Policy 恢复成功。
- 完整审计 JSON：/mnt/public/xcj/Projects/workspace/7ae41311-638f-4b84-83d1-79bd8debf00c/closure/memory20k_7ae41311_rearrange_no_memory_s2.json。
- MAM 复查为 stopped，原 PID 3957417 已不存在且不再占用本任务 GPU5；对应 job 已归档。


## GPU3 serial-lag30 seed2：20000 验收与 e6908de7 评估交接

GPU3 的 MAM wait 停止事件对应 job `68ecba3b-e570-4dd4-8cd1-4a82249a515d`。该训练自然结束并已按下列证据验收、归档；本任务未启动任何评测。

### 可评模型清单：交 e6908de7 评估队列

| 字段 | 已核对值 |
| --- | --- |
| config / schema / seed | pi05_rmbench_rearrange_blocks_serial_lag30 / rearrange_blocks_serial_lag30 schema v1 / seed2 |
| 训练 commit | d10cc01d44c10e5ed0cd8c228d9409dd6cabac50，command 记录 clean worktree |
| 绝对 checkpoint | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/memory20k_7ae41311_pi05_rmbench_rearrange_blocks_serial_lag30_s2/20000 |
| 固定训练条件 | Pi0.5 base、batch32、20,000 updates、H50/K30、BF16 final-only；rearrange_blocks_demo_clean_state_shared_memory，rmbench_rearrange_blocks_robot norm |
| 研究目的 | 补齐 B 组 rearrange serial-lag30 的独立 seed，检验同骨干、同数据和同训练协议下的 seed 级稳定性，避免把 seed0 随机性误判为记忆表示差异。 |
| 评测应检验的结论 | 将其作为 serial-lag30 可复现基线，与同协议 full/no-memory 变体及其它 seed 比较表示差异和方差；不预设或声称闭环成功率。 |

该模型现可由 e6908de7-4b02-465a-987b-a19eba7a315a 按其既定“自身 smoke2 后正式 100”队列接入；本任务不重复启动 eval。

### 20000 产物与恢复验收

- 日志明确记录 Step20000：grad_norm=0.4465、loss=0.0149、param_norm=1805.5968；100 至 20000 共 200 条落盘标量均有限，未匹配 traceback、OOM、未处理 exception、NaN 或非有限错误。
- 最终保存已原子提交：checkpoint metadata 含 commit timestamp，父目录仅含 20000；item 仅 params、assets、metadata，无 train_state 或 optimizer。
- checkpoint metadata 中 config、dataset、command 和 norm 证据均可解析：数据为 50 episodes 的 rearrange_blocks_demo_clean_state_shared_memory，norm SHA-256 为 5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b；9 个 JSON、6 个 JSONL、5 个普通 YAML 与带标签 train config 均通过解析。
- 显式 CPU-only 核验（CUDA_VISIBLE_DEVICES 空、JAX cpu）实际读回 56 个参数叶、3,353,474,844 个元素，全部 BF16、全部有限，路径和 shape 与注册 serial 模型逐项一致；checkpoint-only standalone Policy 恢复成功。
- 完整审计 JSON：/mnt/public/xcj/Projects/workspace/7ae41311-638f-4b84-83d1-79bd8debf00c/closure/memory20k_7ae41311_rearrange_serial_lag30_s2.json。
- MAM 复查为 stopped，原 PID 3956200 已不存在且不再占用本任务 GPU3；对应 job 已归档。
