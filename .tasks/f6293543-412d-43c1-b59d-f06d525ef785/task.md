# Review U组initial输入对照与6训练开跑门禁

Review source delivery (source TASK-ID: cbbba844-d96a-45d5-9b2f-c8a3c6f393b1):
{
  "task": "cbbba844-d96a-45d5-9b2f-c8a3c6f393b1",
  "commits": {
    "openpi": "6266bd8bbfa5f3e451f7253c476d1108e1ff5e1e",
    "robot-bridge": "e43275a19c81c8db35dd20d0ce200f86c11431aa",
    "RMBench": "0d9f38d7dc11c442f8bb046c54305ba55f1682e5"
  }
}

Source task requirements:

# U辅助监督对照：6个20k训练

## 研究目的与既定设计
读取/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md，执行已计划U组：rearrange_blocks和put_back_block，各seed0/1/2。检验性能收益来自递推记忆输入还是仅来自额外状态监督。与各任务Q2/B full per-frame t+j+1基线保持同形状、同字段、同输出目标、loss/mask/归约、norm、数据、初始化及采样；唯一处理为训练和部署memory输入始终为字段initial，不消费预测反馈。仍训练原memory输出及状态损失。不能只在推理清空输入，也不能变成no-memory网络。保留假设可被推翻的表述，不预填成绩。

## 工作与资源
用本任务独立OpenPI及需要的robot-bridge/RMBench worktree，读各AGENTS；不要修改现有活跃训练树。先核对已完成/运行训练，确保U对照未重复。复用已验收demo_clean_state转换、base和norm，不重转数据。以已验收新schema训练实现为基线，优先使用现有schema/config表示initial；若能力未接入，最小补充train和memory context一致路径，OpenPI和bridge两份memory_config保持语义一致，不引入跨库依赖。明确实际参考基线commit/config及逐项差异。

授权资源：本机GPU1/7，wuwen-1 GPU4/5/6/7。启动前复查实际空闲和进程归属，已有占用不抢。规划本机1/7为rearrange seed0/1，wuwen-1 GPU4为rearrange seed2、GPU5/6/7为put-back seed0/1/2。每卡单训练，bs32、20k、H50/K30，最终只存一个20k BF16 checkpoint及必要资产/metadata，独立非现有路径。源数据必须demo_clean_state。

## 开跑门禁
先完成真实训练sample/模型loss/Context反馈的CPU验收，证明memory输入全部initial且GT memory targets、权重、robot输入输出未被误改；reset/takeover/offline/live均不消费反馈。必要50step训练保存恢复smoke用本机GPU1，复用合理已有验证但不能跳过新行为；清理自有smoke产物，提交干净commit。把具体配置、diff、测试和smoke提交Manager，独立review通过后才启动6个正式训练。不要因卡空闲直接跑未review的新语义。

## 台账及交接
在RMBench/experiments/memory_chunk_20260910新增独立U组说明（避免与e690主台账写冲突），先写研究问题、变量、预期结论、每run train/ckpt及计划eval路径。正式启动后登记mam job，检查初始有限loss与GPU映射，完成后验收最终checkpoint、资源释放和训练job归档，给e690评估负责人可评清单。评估用C集群和smoke2→100既定协议，你不重复启动eval。完整任务要求及报告统一MAM .tasks，交付commit、路径、测试、运行job。事件等待用mam wait；不要无变化轮询/心跳/每次超时写report；实际工作完成后结束turn。

Source report:

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

## Review重点与边界
独立本机三库worktree固定上列commit，读取源任务与完整report/验证证据。核对U组对比B full-per-frame唯一实验变量为所有memory输入initial；模型形状、target、phase公共mask、其他字段weights、robot动作/归一化、data、sampler、初始化均保持；runtime真实transform覆盖cache，不漏GT，不把监督清零。训练/部署/offline路径遵循相同配置。特别核查6266bd8的JAX输出可写修复是否数值保持且不会引入U组独有的算法差异；它是基础设施修复应能同样用于基线。
独立跑必要CPU行为测试，抽查真实batch和已留存50step/BF16 checkpoint-only恢复证据。两条smoke已结束删除，除发现具体不足不要重跑GPU训练或恢复，绝不占未授权卡。确认6条20k命令配置/seed/路径不重复及最终只保存20k。给出可启动6训练的明确结论和阻塞项，不以泛化建议拖延。
review报告发布后结束turn，清理自己的pytest/ruff/__pycache__，保留源码worktree供Manager归档；不修改生产源码、登记或运行实验。
