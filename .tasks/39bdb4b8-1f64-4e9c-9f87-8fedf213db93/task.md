# 九任务新增并行评测：cover_blocks N eval0

Manager 已授权新增第三个并行 turn，目标是优先完成九任务主线，不开展机制/HF/V 实验。

## 目标

在集群 C 的 `wuwen-4090-1` 上对已有 `cover_blocks N` seed0/20k checkpoint 执行一批独立的 `eval0`：先 matching smoke2，成功后 formal100。使用原 Memory-v1 RMBench 协议，不训练新模型。

## 固定合同

- checkpoint：`/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z/pi05_rmbench_cover_blocks_no_memory/memory20k_5835fa0_nocmdbuf_cover_blocks_n_s0/20000`
- train seed 0，eval seed 0；H50/K30；首 infer 90s，后续 30s；连续 action RNG；每个 formal 使用自己的 matching smoke。
- 评测 seed 使用原协议 eval0 列表，不带入 HF 的 reset/事件逻辑，不改标签、不改算法。
- 先实际核对 checkpoint、源码、manifest、overlay、GPU 和端口；不得覆盖已有结果，不得抢占 GPU2/GPU3 当前的 swap J / battery N formal。
- 优先使用 C1 空闲 GPU4（若实时核对不可用，选择空闲 GPU1/5/7），登记预计超过30分钟的 smoke/formal job。

## 执行要求

1. 先读本项目 `AGENTS.md`、MAM README/.local、任务涉及仓库的 `AGENTS.md`，再运行 `mam task show 39bdb4b8-1f64-4e9c-9f87-8fedf213db93`。
2. 使用独立 workspace/worktree；不得修改当前 f348 评测运行树和其他任务产物。
3. 先做 2 集 matching smoke；只有身份、路径、协议和 runtime gate 通过才启动 formal100。正常 episode 失败不等于基础设施失败；若出现 RPC、renderer、身份、路径或协议错误，立即停止并报告。
4. 保存 command、PID、端口、manifest、smoke/formal 结果、失败原因和 hash；完成后归档 job，发布 report，说明是否达到 100 accepted 以及真实成功数。
5. 若 checkpoint 或入口存在阻断，停止 GPU 启动，报告证据和最小修复建议；不要擅自改公共代码或降低门禁。
