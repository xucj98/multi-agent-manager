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
