# U 组 full-initial 对照：门禁完成，申请独立 review

本任务只使用 `cbbba844-d96a-45d5-9b2f-c8a3c6f393b1` 的三库 worktree；未使用已归档 2a/C
路径，未启动 C eval，也未启动任何 20k 正式训练或登记正式 job。

## 交付提交与受控变量

| 仓库 | worktree 分支提交 | 交付 |
| --- | --- | --- |
| OpenPI | `906f27c`、`6266bd8` | 两份 `*_full_initial` schema、两条训练 config；JAX policy 输出转 NumPy 后显式可写，供既有 `AbsoluteActions` 变换使用 |
| robot-bridge | `e43275a` | full-initial runtime Context 与真实 policy-transform 合约测试 |
| RMBench | `d4b32b8`、`0d9f38d` | 两个 eval variant、U 独立说明、实际 GPU 门禁记录 |

所有 worktree 现均干净。基线分别为 OpenPI `a869498`、bridge `d49f616`、RMBench
`a7e9420`。唯一实验变量是 train 和 infer 的每个 memory input 均为 `{source: initial}`；仍保留
原 full `t+j+1` memory target、mask、14D robot target、joint-dense 32D loss、norm、sidecar
binding、feedback/reset、`demo_clean_state`、Pi0.5 初始化、batch32、H50/K30、seed 和采样。
初始字段在 runtime transform 中覆盖 scheduler cache；bridge 仍可记录 selected prediction，
但该 cache 不进入模型。

## CPU 和跨库验收

- OpenPI adapter 12 项、policy mutable-output 1 项、Pi0 weighted-loss 1 项、initial-input 与
  checkpoint metadata 2 项均通过；bridge policy-transform 合约 6 项、Context 15 项通过。
- 真实 `demo_clean_state` loader 的两个任务各取一批得到 action `[1,50,32]`、loss weights
  `[1,50,32]`、state `[1,32]`。rearrange 的 input 是 `[0,0,0]`（同一行 t+1 基线 `[1,1,0]`），
  put-back 是 `[0,0]`（基线 `[1,3]`）；robot actions、memory targets、weights 保持相同。
- metadata round-trip 保留单一 resolved initial schema 和 BF16 model-only 设置。

## 本机 GPU1 真实 50-step save/restore gate

两条均使用本任务的独立 `gpu_smoke_checkpoints/`，GPU1 顺序执行，seed0、batch32、H50/K30、
`--num-train-steps=50 --save-interval=50`。训练和 checkpoint 均 exit 0。

| smoke | 训练有限 loss | CPU checkpoint-only restore | GPU checkpoint-only policy restore |
| --- | --- | --- | --- |
| `rearrange_blocks_full_initial` | step10/20/30/40/50: 0.3862/0.3110/0.2271/0.1596/0.1166 | 51 leaves、6,706,867,744 bytes、完整 shape、全部 BF16/finite | action `[50,14]`、memory IDs `[50,3]`、13.76 s |
| `put_back_block_full_initial` | step10/40/50: 0.3873/0.1642/0.1320 | 51 leaves、6,706,867,744 bytes、完整 shape、全部 BF16/finite | action `[50,14]`、memory IDs `[50,2]`、13.53 s |

两次 restore 都仅允许 checkpoint 自带的 params/assets/metadata，且拒绝 dataset、base checkpoint、
source memory YAML 和 worktree assets 读取。二者都核对干净 `6266bd8bbfa5f3e451f7253c476d1108e1ff5e1e`
提交、batch32、seed0、H50、32D、BF16 model-only 和 train/infer 全字段 `{source: initial}`。

第一次 rearrange GPU restore 暴露 task-local 验证器把 Aloha dummy image 写成 HWC 的错误；Aloha
外部合同是 CHW。训练 checkpoint、模型和 initial-input 路径均未失败。修正该测试输入后 retry
通过；初次失败日志和 retry 日志均保留。

原始命令日志、验证器和失败/重试证据在
`/mnt/public/xcj/Projects/workspace/cbbba844-d96a-45d5-9b2f-c8a3c6f393b1/validation/`。已删除
9.8 GB task-local smoke checkpoint，仅留下约 108 KB 的脚本和日志；正式路径从未写入。

请按上述提交、initial-input 不变量、checkpoint-only restore 与任务边界做独立 review。review
PASS 前不会启动六条 20k；通过后按既定映射启动本机 GPU1/7 的 rearrange seed0/1，wuwen-1
GPU4 的 rearrange seed2，GPU5/6/7 的 put-back seed0/1/2，并逐条登记 MAM job。


## Manager 准入后的六条正式训练启动状态（2026-09-12 06:35 +0800）

独立 review `f6293543` 通过且 Manager 正式准入后，六条均以冻结 OpenPI
`6266bd8bbfa5f3e451f7253c476d1108e1ff5e1e` 启动：batch32、20,000 updates、H50/K30、
BF16 model-only、`--save-interval=20000`，没有覆盖既有路径。所有 run 通过 step100 有限
loss；这只证明启动健康，不是训练完成或评测结果。

| run | host / GPU / PID | MAM job | step100 loss | 最终 checkpoint 路径 |
| --- | --- | --- | --- | --- |
| rearrange s0 | localhost GPU1 / `238898` | `d87b16e1-77a5-483b-acda-461fa32c1137` | `0.1568` | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_initial/memory20k_cbbba844_rearrange_full_initial_s0/20000` |
| rearrange s1 | localhost GPU7 / `238890` | `a1137b5b-dbe8-4a6b-9aa0-125bec11fa65` | `0.1543` | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_initial/memory20k_cbbba844_rearrange_full_initial_s1/20000` |
| rearrange s2 | wuwen-1 GPU4 / `1605770` | `6ab90156-3094-46fa-ba3c-39e4e3d4e03f` | `0.1562` | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_initial/memory20k_cbbba844_rearrange_full_initial_s2/20000` |
| put-back s0 | wuwen-1 GPU5 / `1605750` | `2520a158-85e3-4a4a-afe8-24f01aa13bd2` | `0.1582` | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_initial/memory20k_cbbba844_put_back_full_initial_s0/20000` |
| put-back s1 | wuwen-1 GPU6 / `1605774` | `b669c403-a702-4383-811d-06aa400cf46d` | `0.1547` | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_initial/memory20k_cbbba844_put_back_full_initial_s1/20000` |
| put-back s2 | wuwen-1 GPU7 / `1605766` | `315d9224-0562-472d-b1c3-0cd678e2abe6` | `0.1557` | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_initial/memory20k_cbbba844_put_back_full_initial_s2/20000` |

实际 GPU UUID/PID 复核通过：local GPU1 `GPU-b72526e2-ac45-3452-8e77-1de83963ae85`→`238898`，
GPU7 `GPU-d005e95a-93d5-94b7-30ca-02f49f5af15a`→`238890`；wuwen-1 GPU4/5/6/7 分别对应
`1605770/1605750/1605774/1605766`。当前速度约 3.7–3.9 s/step，若稳定，预计在
2026-09-13 03:00–04:00 +0800 左右完成。

本机最初两个 `nohup` wrapper 在进入 Python 前被本地执行器回收，留下空日志、没有 checkpoint，
且未登记 job；改为独立 `setsid` 会话后才启动并登记上表 local GPU1/7 正式 run。该事件未改变
模型、seed、动作协议或训练路径。六条当前均为 running；未启动 C eval。运行日志在
`/mnt/public/xcj/Projects/workspace/cbbba844-d96a-45d5-9b2f-c8a3c6f393b1/training_logs/`，台账更新为
RMBench `a7e851b`。

## MAM 主动唤醒迁移后的实际状态（2026-09-12 18:37 +0800）

已阅读任务 18:35 的主动唤醒迁移节。`mam task status` 在 18:37 +0800 成功重新解析本任务的全部
6 个已登记 job：rearrange s0/s1/s2 与 put-back s0/s1/s2 均为 `running`，没有本任务已停止而未验收、
未归档的 job，也没有最终 `/20000` checkpoint 可在此刻验收或交给 e690。训练进程、GPU 映射、模型、
seed、动作协议和路径均未改动，未启动任何 eval。

此前两次旧式 `mam wait` 分别在 wuwen-1 GPU7 与 GPU4 的状态查询遇到 SSH 超时；它们没有报告训练
停止。上述成功的 MAM 状态查询已将对应四条远端训练以及两条本地训练均确认回 `running`。按新机制，
此处结束 active turn；MAM 会在任一已登记且未归档的训练停止时重新唤醒执行者，届时再执行最终 checkpoint
验收、资源释放/job 归档和 e690 可评清单交接。

## 当前执行者交接后的单次运行快照（2026-09-13 01:35 +0800）

Manager 已将任务换绑到 `01a096ab-e5f3-7672-8ff3-36328d3fcfb7`，原 workspace、三库提交和六个
MAM job 均原样继承。本次只读实际检查确认六个登记 PID 均仍存在并占用预定 GPU，末尾日志均为有限
loss；六个预期的最终 `/20000` checkpoint 目录目前均不存在。

| run | 实际最新日志 | 最终 checkpoint |
| --- | --- | --- |
| rearrange s0 / local GPU1 | step 18500, loss 0.0008 | 未就绪 |
| rearrange s1 / local GPU7 | step 18400, loss 0.0008 | 未就绪 |
| rearrange s2 / wuwen-1 GPU4 | step 18000, loss 0.0006 | 未就绪 |
| put-back s0 / wuwen-1 GPU5 | step 18500, loss 0.0010 | 未就绪 |
| put-back s1 / wuwen-1 GPU6 | step 18700, loss 0.0009 | 未就绪 |
| put-back s2 / wuwen-1 GPU7 | step 18000, loss 0.0008 | 未就绪 |

没有 stopped job，故本次没有 checkpoint 验收、job 归档、重启、重复登记或 C eval。后续由 MAM 在任一
登记 job 停止时唤醒当前执行者，再进行最终产物验收和 e690 可评清单交接。
