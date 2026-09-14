# HF-fixed rearrange 三批 formal100 独立核验

任务 revision：`d4af09802f34575c870fe04cdcbc649fd114ea45`。本次在 `wuwen-4090-3` 上仅作 CPU、只读的 JSON/YAML/哈希/PID 存活检查；没有运行 GPU、模型、仿真、评测器、owner audit/recorder helper 或视频解码，也没有修改 C3 runtime、结果、checkpoint 或论文。

结论：三条 HF-fixed J rearrange formal100 的工程身份、终态、rolling 证据、matching-smoke 链和受控进程收尾均通过独立复算，核查范围内没有发现阻断其作为三条已完成 formal100 的工程/证据缺口。Manager 仍须决定最终准入、论文采用和任何科学解释；本结果只覆盖 train-seed 0 的这一项任务，不可同历史 continuous-RNG baseline 或原协议 52 批合并。

| eval seed / GPU | 环境 seed | fixed | accepted matched baseline | 差值 | 都成功 / 仅 baseline / 仅 fixed / 都失败 |
|---:|---|---:|---:|---:|---:|
| 0 / 0 | 100000–100099 | 90/100 | 86/100 | +4.0pp | 79 / 7 / 11 / 3 |
| 1 / 1 | 200000–200099 | 91/100 | 81/100 | +10.0pp | 74 / 7 / 17 / 2 |
| 2 / 2 | 300000–300099 | 87/100 | 87/100 | +0.0pp | 78 / 9 / 9 / 4 |
| total | 300 exact joined seed | 268/300 | 254/300 | +4.67pp | 231 / 23 / 37 / 9 |

四格和失败迁移都直接从两侧原始 `episode_diagnostics.jsonl` 按相同环境 seed join 得出。baseline 失败转 fixed 成功共 37：`block2_not_moved_to_middle` 14、`button_not_pressed` 15、`button_press_insufficient` 3、`button_pressed_multiple_times` 5。baseline 成功转 fixed 失败共 23：block2-middle 9、button-not-pressed 8、block2-not-released 1、multiple-press 5。两侧都失败的 9 条为 block2→block2 1、not-pressed→not-pressed 3、not-pressed→multiple-press 1、insufficient→not-pressed 1、multiple-press→block2 2、multiple-press→pressed-after-block2-moved 1。逐 eval 的完整迁移表保存在 [paired_outcomes.json](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/93858e54-40e7-4e1a-ab86-ccf9039ab86f/evidence/paired_outcomes.json)。

三条 C3 runtime worktree 都是 clean，HEAD 分别为 OpenPI `0ce566b…53885`、robot-bridge `ffa1224…ccfc6`、RMBench `6abebf0…e4`。每条 command、manifest、input audit、scheduler、formal preflight/started receipt、result config 和记录的 checkpoint/metadata digest 交叉一致；checkpoint 是固定的 `...rearrange_full_t_plus_1_s0/20000`，记录 tree digest `bf49af7f…b71bddd4`、metadata digest `d111ca3…25ecf1002`。本次没有重哈希多 GB checkpoint。

三份 owner terminal receipt 和 `audit_formal_hf_fixed.py` 都已重哈希为给定值；进一步重哈希了各 receipt 引用的 48 个核心正式/烟测 artifact，零 mismatch。每条都有 100 条 accepted preflight、连续 `episode_id=0..99` 与环境 seed、100 条正常 `Success`/`Fail` terminal diagnostics、`runtime_error=null`，并与 diagnostics summary、`eval_log.txt`、`_result.txt` 链接一致。三条 matching smoke 均有两个 accepted terminal、完整 rolling envelope，且 post-smoke quiescence receipt 为 `ready`、无遗留 owned child。

300 份 HF-fixed rolling JSONL 逐份解析并重哈希，header 的 identity/protocol、v1 schema、连续 event index、最后的 complete `episode_finished` 和无 `truncated` 均通过。每条 action plan 都是 `infer_audited` 的 30×14 ordinary K30 队列；每个非 terminal 的 5 行完成边界都记录 state consumption，K30 boundary 继续创建 ordinary completed-boundary action plan。没有 clear、trigger 或 replan record；terminal suffix 的 `plan_terminal` 与诊断 logical step 一致。action/probe wire stream/call 均逐 episode 自 1 连续且分别为 `action` / `probe`；这些是记录的 wire metadata，不当作内部 PRNG key。

| eval seed | ordinary action calls | probe calls | 五行 state refresh | 已完成动作行 |
|---:|---:|---:|---:|---:|
| 0 | 1,462 | 7,029 | 8,391 | 42,246 |
| 1 | 1,439 | 6,937 | 8,276 | 41,663 |
| 2 | 1,496 | 7,205 | 8,601 | 43,285 |
| total | 4,397 | 21,171 | 25,268 | 127,194 |

每条 formal process ledger 都是 102 start / 102 exit，100 scheduler 均 exit 0，robot/policy 都为 `runner_shutdown` / `-15`；三个 outer PID 和所有记录 PID 在 C3 均已不存在。视频 policy 仅启用 episode 0–4；每条 `video_checks` 都正确，且五个启用视频对应 owner 的既有 ffprobe/ffmpeg decode receipt。这里没有再次解码或哈希 MP4。

冻结 source 的只读检查也解释了上述合同：[OpenPI policy.py](/mnt/public/xcj/Projects/workspace/93858e54-40e7-4e1a-ab86-ccf9039ab86f/openpi/src/openpi/policies/policy.py:219) 将 probe 使用独立 stream 并在 episode reset 恢复 action/probe 状态；[scheduler](/mnt/public/xcj/Projects/workspace/93858e54-40e7-4e1a-ab86-ccf9039ab86f/robot-bridge/robot_bridge/scheduler/openpi_simulation.py:1301) 强制每个 monitor interval 的完成进度和剩余队列，[其 rolling loop](/mnt/public/xcj/Projects/workspace/93858e54-40e7-4e1a-ab86-ccf9039ab86f/robot-bridge/robot_bridge/scheduler/openpi_simulation.py:1798) 只有 `hf_event` trigger 才走 clear/replan；[RMBench checker](/mnt/public/xcj/Projects/workspace/93858e54-40e7-4e1a-ab86-ccf9039ab86f/RMBench/script/eval_diagnostics.py:675) 要求 header identity、无 truncation 和 complete final record。逐行引用与本地/远端文件哈希见 [source_contracts.json](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/93858e54-40e7-4e1a-ab86-ccf9039ab86f/evidence/source_contracts.json)。

可复算交付：

- [独立重算程序](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/93858e54-40e7-4e1a-ab86-ccf9039ab86f/evidence/independent_hf_fixed_recomputation.py)，SHA-256 `e2fd0094939a0749df9dd3d1db0e8d99e6e41057bf8c54a8c03343edd0ebde93`。
- [独立重算输出](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/93858e54-40e7-4e1a-ab86-ccf9039ab86f/evidence/independent_hf_fixed_recomputation.json)，SHA-256 `9382506343ee40688190bce9d341fc92f383eadc7fdd358573d4b0f3019c47ab`，包含全部 300 个 fixed rolling hash 和逐 lane 检查。
- [小型 raw artifact 镜像清单](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/93858e54-40e7-4e1a-ab86-ccf9039ab86f/evidence/raw_artifacts_manifest.json)，SHA-256 `317aa3574e36eb32942a4b08360a9e78f43d372c8b2e52a7b3af3721de1b2fd3`；56 件、6,561,462 bytes，全部匹配。没有复制 checkpoint、MP4 或 rolling JSONL。
- [本地 receipt](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/93858e54-40e7-4e1a-ab86-ccf9039ab86f/receipt.json)，SHA-256 `fb47fdd289308e128e276190eac73f69a4d4201b6aaa802bf26ae28d5a2edf58`，汇总核验边界、准入范围和限制。

三个 review worktree 都保持 clean，没有交付代码 commit。
