# U 组 full-initial 独立 review：PASS，准入 6 条 20k

结论：**PASS，无阻塞项。**源任务可按已冻结的六个 run、GPU 映射和 checkpoint 路径启动
20k 训练；启动时仍须逐卡复查空闲/进程归属，并为每条正式训练登记 MAM job。本 review 未启动
训练、GPU smoke、C eval 或正式 job。

## 独立范围

按 review 固定提交创建并检查了三套独立 worktree，均保持干净：

| 仓库 | review worktree | HEAD |
| --- | --- | --- |
| OpenPI | `/mnt/public/xcj/Projects/workspace/f6293543-412d-43c1-b59d-f06d525ef785/openpi` | `6266bd8bbfa5f3e451f7253c476d1108e1ff5e1e` |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/f6293543-412d-43c1-b59d-f06d525ef785/robot-bridge` | `e43275a19c81c8db35dd20d0ce200f86c11431aa` |
| RMBench | `/mnt/public/xcj/Projects/workspace/f6293543-412d-43c1-b59d-f06d525ef785/RMBench` | `0d9f38d7dc11c442f8bb046c54305ba55f1682e5` |

## 受控变量与 CPU 复核

- 对 `*_full_t_plus_1` 与 `*_full_initial` 的 resolved TrainConfig 和 YAML 做了逐项对照。除
  config/schema 名称、随名称记录的 `policy_metadata.batch_id`、以及 schema 的
  `protocol.input` 外，其余训练字段完全相同。后者在 U 的 train/infer 中每个字段均为
  `{source: initial}`；target、action、joint-dense representation、公共 phase mask、loss
  权重、feedback/reset、bindings、Pi0.5 初始化、sampler、`demo_clean_state` repo 和 robot-only
  norm 均一致。
- 两个 U config 均核对为 H50、32D、batch 32、20,000 steps、`save_interval=20000`、
  `save_full_state=false`、BF16 model-only。rearrange 使用
  `rearrange_blocks_demo_clean_state_shared_memory` 与 `rmbench_rearrange_blocks_robot`；put-back
  使用 `put_back_block_demo_clean_state_shared_memory` 与 `rmbench_put_back_block_robot`。
- 在 `JAX_PLATFORMS=cpu`、空 `CUDA_VISIBLE_DEVICES` 下从真实共享数据各抽一批。rearrange 的
  baseline 输入 IDs 为 `[1,1,0]`、U 为 `[0,0,0]`；put-back 为 `[2,3]`、U 为 `[0,0]`。
  两组均为 action `[1,50,32]`、loss weights `[1,50,32]`、state `[1,32]`，且同一行的完整 action
  （含 memory target）、loss weights 与 robot-state 前 14 维逐元素一致且有限。
- OpenPI adapter 12 项、U pipeline/metadata/binding 3 项、Pi0 加权 loss 1 项、checkpoint
  metadata 4 项、memory-config CLI 3 项的同序汇总复跑为 **23 passed**；bridge `MemoryContext`
  15 项、跨库真实 policy-transform 6 项均通过。三个 worktree 的 CPU 环境 smoke 也通过。
- 对两份真实 U schema 的 lifecycle 做了独立 CPU probe：prediction feedback 确实更新 cache，
  但 feedback 后、手动/takeover 覆盖后和 reset 后的下一次输入仍分别为 initial IDs。live
  scheduler、offline scheduler 和 RMBench simulation 都通过同一个 `MemoryContext.add_inputs()`
  边界提供 `memory_input_ids`，因此不另外存在一条能消费 cache 的输入路径。

## JAX 输出修复与 50-step 证据

`6266bd8` 仅将通用 JAX policy 边界的 host 输出从只读 view 改为显式可写 NumPy copy；它不读取
U config、不改变模型、loss 或输入协议，因此同样适用于 B 基线。独立 CPU probe 用原地 action
transform 验证了可写性和数值结果。

已审计源任务保留的
`/mnt/public/xcj/Projects/workspace/cbbba844-d96a-45d5-9b2f-c8a3c6f393b1/validation/`：

- 两条 GPU1 50-step 训练都保存成功且 loss 有限；rearrange step 50 为 `0.1166`，put-back 为
  `0.1320`。
- 两份 checkpoint-only CPU restore 都报告 51 leaves、6,706,867,744 bytes、完整 shape、全部
  BF16/finite，并拒绝 dataset、base checkpoint、source YAML 与 worktree assets 的读取。
- GPU policy restore 的最终证据分别为 action `[50,14]` 与 memory IDs `[50,3]` / `[50,2]`。
  rearrange 的第一次 restore 仅因验证器把 Aloha dummy image 写成 HWC 而失败；修为 CHW 后 retry
  通过。没有重复运行任何 GPU smoke 或 restore。
- `gpu_smoke_checkpoints/` 已不存在，保留的 validation 目录为 108 KB；正式 checkpoint、正式
  job 和匹配的训练进程均不存在。

## 准入的六条正式训练

| run | config | GPU | 最终 checkpoint |
| --- | --- | --- | --- |
| rearrange seed0 | `pi05_rmbench_rearrange_blocks_full_initial` | local GPU1 | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_initial/memory20k_cbbba844_rearrange_full_initial_s0/20000` |
| rearrange seed1 | 同上 | local GPU7 | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_initial/memory20k_cbbba844_rearrange_full_initial_s1/20000` |
| rearrange seed2 | 同上 | wuwen-1 GPU4 | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_initial/memory20k_cbbba844_rearrange_full_initial_s2/20000` |
| put-back seed0 | `pi05_rmbench_put_back_block_full_initial` | wuwen-1 GPU5 | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_initial/memory20k_cbbba844_put_back_full_initial_s0/20000` |
| put-back seed1 | 同上 | wuwen-1 GPU6 | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_initial/memory20k_cbbba844_put_back_full_initial_s1/20000` |
| put-back seed2 | 同上 | wuwen-1 GPU7 | `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_initial/memory20k_cbbba844_put_back_full_initial_s2/20000` |

六个 `exp_name`、seed、GPU 和 checkpoint leaf 互不重复。正式训练仅保留最终 `20000` 的 BF16
checkpoint、metadata 与必要 assets；评测继续交由 e690 按既定 C 集群 smoke2→100 协议执行。

本 review 产生的 `.pytest_cache` 已清除，三库 worktree 无源码改动或缓存残留，可供 Manager
验收和归档。
