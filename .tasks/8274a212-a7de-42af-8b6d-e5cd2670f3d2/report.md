# rearrange J matched-baseline 三批 formal100 独立核验

任务 revision：`ad7f6bb42ee02481e4a14c205a650894888ce01a`。本次只读核验源任务 `0acf5d43-91b6-4171-b727-e3fe0f7e7939` 的三条已结束结果；未运行 GPU、模型、仿真、owner helper 或 RMBench helper，未触碰正在运行的 HF-fixed/event，也没有修改运行时、论文、checkpoint、阈值或 seed。

结论：三条新协议的 matched-baseline formal100 没有工程性或证据完整性缺口阻止分别计为已完成的 formal100。这个结论只覆盖工程身份、协议和终态证据；科学解释、论文采用及是否扩展实验由 Manager 裁决。它们采用 `episode_reset_key0_independent_probe_v1`，不能与历史 legacy-continuous RNG baseline 混合或并入原协议的 52 批。

## 结果与终态

| eval seed / GPU | 环境 seed | Success / Fail | 正常失败分类 |
|---:|---|---:|---|
| 0 / 0 | 100000–100099 | 86 / 14 | block2 middle 4；button 未按 6；按压不足 2；多次按压 2 |
| 1 / 1 | 200000–200099 | 81 / 19 | block2 middle 6；button 未按 8；按压不足 2；多次按压 3 |
| 2 / 2 | 300000–300099 | 87 / 13 | block2 middle 5；button 未按 5；多次按压 3 |

每叶均有连续 100 条 accepted preflight、连续 episode id 和 seed、100 条 `Success`/`Fail` terminal diagnostics，`runtime_error=null`；summary、`eval_log.txt` 的 100 条终态行和失败分类全部重算一致。每叶 process ledger 都是 102 start / 102 exit，100 scheduler exit code 为 0，robot/policy 均以 `runner_shutdown` / `-15` 受控退出；C3 上记录的 PID 和 outer PID 都已不存在。视频策略是 episode 0–4 开启且 frames 非零、5–99 禁用且 `ok=true`；只核对 owner 已解码收据和 `video_checks`，没有重新解码或哈希 MP4。

## 身份、正式链与 smoke

远端 C3 runtime 三库均 clean，HEAD 为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。三叶共同的 bridge content SHA 为 `7669d954…c86c2cec`，scheduler SHA 为 `f270500d…71a2443`；冻结 scheduler 精确为 baseline、`reset_episode_rng=true`、`move_steps=30`、`monitor_interval=5`、`rolling_max_k=null`，并要求 rolling evidence。

每条 formal command、manifest、input audit、preflight/started receipt、run config 和 result-side scheduler 都交叉一致。checkpoint 路径固定为 J train-seed 0 的 `.../20000`；记录的 tree digest `bf49af7f…b71bddd4` 和 metadata digest `d111ca3…25ecf1002` 经 config/manifest/input-audit 链相互验证。本次没有重哈希多 GB checkpoint。

三个 matching smoke config 哈希分别为 `c8735018…dd417b`、`d2b3d4b…2a61a6`、`77565dc4…7aa559`；formal 的 smoke link、`launch`、robot/policy metadata、profile 和 run identity 全部相同。每条 smoke 的两份 rolling envelope 都是 header → complete `episode_finished`，且 post-smoke quiescence receipt 为 `ready`、无遗留 owned child。

源码只读核查也支持这个边界：冻结 bridge 仅在 baseline 加 `reset_episode_rng=true` 时进入 matched-baseline 协议，未 opt-in 的历史 baseline 保持 `legacy_continuous`。其完成记录在 terminal observation 后发出并返回 `None`，所以结果 JSONL 的 `episode_finished.outcome=scheduler_stopped`、`episode_terminal=false` 不是不完整证据：全部 300 条 embedded `episode_status.terminal=true` 与 diagnostics terminal status 一致。RMBench 的 evidence checker 也以 header/identity、无 truncation 和 complete `episode_finished` 为完整性合同。

## rolling 原件独立重算

我在 C3 直接解析并重哈希 300 份 rolling JSONL，未调用 owner audit 或 recorder helper。三叶各 100 份文件均和 owner 的逐文件 SHA 一致，重新计算 aggregate SHA 后也一致：

| eval seed | query 数 | query/episode min–max | aggregate SHA-256 |
|---:|---:|---:|---|
| 0 | 1,504 | 13–24 | `018c976ba9d7f0e7efd19aa61dd923c65e12e3f43fc8feda723107d6a633567d` |
| 1 | 1,555 | 13–24 | `d56a114ecc6e77fc736a940256c589167bc52a00b1d7c0372c05ae246f424e83` |
| 2 | 1,502 | 13–24 | `5523ad36750e21a6e300696b9d69cdd9cff90e5a2205655802d838d26f7039a3` |

逐集验证 header 的 lane identity 和 baseline protocol、第一条且唯一的 `policy_rng_reset`、连续 event index、严格 `query → queued → completed` 三元组、50×14 action、50×3 `memory_prediction_ids`、K=30 queue、completed 时序和 final complete。300 集均没有 probe、clear 或 trigger record。query 的 `action_rng.stream/call` 按 `action/1..N` 连续，只是 wire metadata，不作为内部 PRNG key 解释。

## 可复算证据

- [独立重算程序](evidence/independent_recomputation.py)，SHA-256 `680940e89a3b8f0976b8ff4c79dd8bb8271bed43441b554a042a009a9a233cc0`。
- [独立重算输出](evidence/independent_recomputation.json)，SHA-256 `a333fd032bf11c6799593a74730130e379c98ab2cf6f28a5c02c6063f9c2535b`，包含所有 300 个 rolling hash 和逐 lane 检查结果。
- [复制的 raw 原件清单](evidence/raw_artifacts_manifest.json)，SHA-256 `a8d396e7b596988f8c4faaab4e771d00222330d2e6daa8268ebc055e7db3c1d7`；42 个小型 config、diagnostics、preflight、process、video-check、command/manifest/audit/receipt 原件共 4,698,941 bytes，均与独立重算 hash 一致。没有复制 checkpoint、MP4 或 300 份 rolling 原件。
- [本地 receipt](receipt.json) 汇总判断与边界。owner terminal receipt 和 owner tool 已分别重哈希为任务给定的 `361cfbb8…403407c1`、`99985367…8138a3e5`。

本地只读 review worktree 也保持 clean：`workspace/8274a212-a7de-42af-8b6d-e5cd2670f3d2/{openpi,robot-bridge,RMBench}`，对应上述三个冻结 commit；没有交付代码 commit。
