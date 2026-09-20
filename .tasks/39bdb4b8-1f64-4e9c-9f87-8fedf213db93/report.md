# cover_blocks N eval0 formal100 已完成（2026-09-20）

已在 C1 `wuwen-4090-1` 完成冻结的 Memory-v1 `cover_blocks` no-memory checkpoint 的独立 eval0。正式运行并非因 stopped 状态直接判定：终态产物显示 `benchmark.status=completed`、`error=null`、target `100`，并已逐项核对 accepted episode、seed、视频、进程账本、checkpoint metadata 与固定 runtime 身份。

## 固定输入与运行身份

- checkpoint：`/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z/pi05_rmbench_cover_blocks_no_memory/memory20k_5835fa0_nocmdbuf_cover_blocks_n_s0/20000`
- 执行 worktree：`/mnt/public/xcj/Projects/state-vla/workspace/39bdb4b8-1f64-4e9c-9f87-8fedf213db93/cover-n`
- 固定 commits：RMBench `ad7f9d6ba9acd16c31243ad4811e0dfa31cef514`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；结束时三库均 clean。
- 合同：`cover_blocks` / `demo_clean_eval`，train seed 0、eval seed 0，H50/K30，fresh policy server RNG key 0，首个 infer 90 秒、后续 30 秒。
- task-local runtime overlay 只提供 Python import bootstrap；没有修改公共仓库源文件。
- input manifest SHA-256：`b21b569d18c53d75cf2260597e4253069fb6dbab76db531d3132dd6ecaec0a8d`；input audit SHA-256：`e833f83294407a242212200399dc01964bb54c706000ae877612aba7e8e87b88`。

## matching smoke

`c_wave1_cover_blocks_n_trainseed0_evalseed0_smoke2_r2` 位于：

`/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_wave1_cover_blocks_n_trainseed0_evalseed0_smoke2_r2`

它有 2/2 accepted rollout（seed `100000..100001`），终态 `completed` / `error=null`，结果 0/2 success。episode 0 的 1500 帧视频和 episode 1 的关闭视频证据均通过。其 config SHA-256 为 `24c259bc9d19afc7a99edd8e7cecc97b9b203976df35cd9b3d68a97704a1708e`；正式启动前再次实际调用 `validate_smoke_run()`，其返回同一 bridge commit 与该 config hash，且 smoke/formal 的 bridge content SHA-256 均为 `ddff9953348b07dd13392a1c43929e033fbdb148cb444cfe49ebffe6637ae2b7`。

## formal100 结果

| 项目 | 值 |
| --- | --- |
| formal leaf | `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_wave1_cover_blocks_n_trainseed0_evalseed0_100ep_r2` |
| GPU / ports | GPU4 / `19440`, `19442` |
| outer PID / MAM job | `2628825` / `72dfd53a-f56a-427c-ad30-fd2cbab95a9d` |
| accepted episode | **100/100**，ID `0..99` |
| 环境 seed | `100000..100099`，100 个 preflight 均 accepted |
| 成功数 | **0/100**（0.0%） |
| 普通终态 | 100 个 `step_limit_reached`；无导致运行中止的 runtime gate / RPC / renderer / 身份 / 路径 / 协议错误 |
| scheduler | 100 starts、100 exits，所有 returncode `0` |
| 服务收尾 | policy 与 robot 均为 runner 正常 `runner_shutdown` / `-15`；PID、端口和 GPU4 已释放 |
| 视频 | 5 个 enabled MP4 均通过（每个 1500 帧）；95 个 disabled-video records 均通过 |

50 与 100 accepted episode 的中点检查均已写入；历史完整 baseline 不可用，因此没有主要比较或触发项。100 个 episode context、100 个 scheduler log、100 个诊断行和 100 个 preflight 行都保留在 formal leaf。模型在该冻结条件下的任务失败完整保留，未删去或重跑不利 episode。

关键 formal 产物 SHA-256：

- `diagnostics_summary.json`：`6c76a9c30aa55c099d8c3b6b5e9dda8646a35e80942f7e5387a0da0d4feef102`
- `episode_diagnostics.jsonl`：`389aa00c152dbc93f85c9aac4a695bf44e1c308bcba57d9737c1203c0e96d7d7`
- `seed_preflight.jsonl`：`478cc6058bd3eb3de8de5bd798ab1fe1b606f53340dc2f6c03cabc4f1abef527`
- `processes.jsonl`：`5b9507e0993856c1ab2d9df33721c0b96a49a4b86b8f663a276d7abaf5b1204c`
- `video_checks.jsonl`：`bb700d96cb0d32e5d323b3b680907eacd35a514d157671414d8e120b9fb6d116`
- `command.txt`：`d8cce5be5dff9b81167539860bf5dfe416a0f7a550ec18de7822a73b3a22ab89`
- `config.yaml`：`39c145cd0a198afcecac0c3e47b2c8cf46a9b2d7cf8027fb643297475f99adab`

checkpoint metadata 副本也已保留：`train_config.yaml` SHA-256 `7f6476af11d52e49b2f480c4fe21ff7948e0f25e61c310f5739ce88bde7069ab`、`datasets.json` `2a865394cfd54a2158b8d5e3483e2eb15485aa38c6d4ac474805f86599dfa217`、`inheritance.json` `15b5af4213d3739b235322665ff16d95299151e8bc78f90b501c62a8a3643b04`。

正式 job 已在验收后归档：`72dfd53a-f56a-427c-ad30-fd2cbab95a9d`。没有修改评测协议、公共源码或已有结果。
