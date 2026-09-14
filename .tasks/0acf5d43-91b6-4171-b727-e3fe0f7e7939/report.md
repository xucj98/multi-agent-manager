# 置顶：第一层 J rearrange HF-event 三个 eval formal100 终态与同 seed 配对审计（2026-09-14）

三个授权的 HF-event formal100 均已完成并通过终态、身份、rolling evidence 与 trigger 审计；结果来自每条连续 100 个 accepted episode。它们是冻结原件的描述性记录，不将发生 trigger 的 episode 成功或失败解释为 trigger 的因果效果。

| Eval | 环境 seed | HF-event | matched baseline | HF-fixed | event vs baseline `E+ B- / E- B+` | event vs fixed `E+ F- / E- F+` |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `100000..100099` | 84/100 | 86/100 | 90/100 | 9 / 11 | 7 / 13 |
| 1 | `200000..200099` | 88/100 | 81/100 | 91/100 | 16 / 9 | 7 / 10 |
| 2 | `300000..300099` | 86/100 | 87/100 | 87/100 | 2 / 3 | 10 / 11 |
| 合计 | 三个各 100 集 lane | 258/300 | 254/300 | 268/300 | 27 / 23 | 24 / 34 |

每个 pairing 均先核验三臂 episode ID `0..99` 与对应环境 seed 完全相同；专门收据保存完整四格 outcome 表（含 both-success / both-fail），不以仅有的成功数差额替代配对。汇总收据为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/formal_first_layer_j_20260914/receipts/formal_hf_event_rearrange_three_eval_seed_paired_summary_20260914.json`，SHA-256 `e779275ba49c7c587173bf6aa93db852736fb76550f8c36967ef3558f083e905`。

三个 event terminal receipt 分别为 eval0 `formal_hf_event_rearrange_evalseed0_terminal_audit_20260914.json`（`9f33589e01c6b53a64b6f323b1859dddcbd87121cb1aa50af755d4b0f68d373b`）、eval1 `formal_hf_event_rearrange_evalseed1_terminal_audit_20260914.json`（`eaceed71183a7d76357346cac3c524b324e5871cb2bbcc17866b4885346a0711`）和 eval2 `formal_hf_event_rearrange_evalseed2_terminal_audit_20260914.json`（`23f0beb2e109e8b80c5560ba9ac866b026c0a3af436b679bf4971a8953c21e85`）。三条都实际调用 `validate_smoke_run()` 和每集 `check_rolling_evidence(..., required=True)`，核对 100 个 accepted preflight/terminal、5 个 MP4 的 `ffprobe`/`ffmpeg` 解码、102 start/102 exit、100 scheduler exit 0，以及 robot/policy 的受控 `-15` shutdown；所有记录 PID 已退出。

`plan_triggered` 原件和逐事件详情保留在上述 terminal receipts，并由汇总收据保存每个 eval 的触发次数与 episode map：eval0 **154** 次、39 个 episode（`14,15,16,21,22,24,26,27,28,29,31,32,33,34,35,38,39,41,45,51,52,55,59,60,63,64,65,71,73,74,75,77,84,86,87,93,95,97,99`）；eval1 **125** 次、32 个 episode（`1,3,4,6,8,14,18,19,21,24,25,26,28,33,37,41,42,48,51,56,64,66,68,71,72,79,86,88,91,93,95,96`）；eval2 **200** 次、41 个 episode（`2,4,6,7,11,12,16,19,21,22,27,28,32,33,35,36,38,41,45,48,52,53,55,56,61,63,65,67,69,70,72,74,75,80,81,84,88,90,92,98,99`）。合计为 **479** 个 trigger、112 个 eval–episode pair；这只描述执行中的触发暴露，不能用于解释成功因果。

终态审计后，MAM jobs `380ad209-d5c5-432e-9718-247c2cced46a`（eval0）、`9776cd89-0dad-447b-a772-ceba29ff1539`（eval1）和 `a79b70de-9c74-4d72-977f-7eb2060dabc5`（eval2）均已归档。task-private state commit：`8e4b3d0f60b3a27d0ddbeab830f10ce4475c123a`（包含 eval1/2 审计器扩展、两个终态 receipt 与三 eval 配对收据）。未启动、重跑或调整任何后续 event batch、阈值、seed 或冻结输入。

# 置顶：第一层 J rearrange HF-event eval0 formal100 终态审计与首个自然 trigger（2026-09-14）

C3 GPU0 outer PID `2112144` 已停止。终态审计将其归类为**自然正常完成**：`BenchmarkRunner` 的结构化 summary 为 `completed`、`error=null`、target `100`；100 个 scheduler 均 exit 0，robot/policy 为 runner 受控 `-15` shutdown，outer 中早期连接重试没有覆盖这一终态结论。连续 accepted seed 为 `100000..100099`，结果为 **84/100**（16 个普通任务失败：`block2_not_moved_to_middle=7`、`button_not_pressed=7`、`button_pressed_multiple_times=2`）。这是冻结原件的描述性结果，不作科学结论。

终态收据为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/formal_first_layer_j_20260914/receipts/formal_hf_event_rearrange_evalseed0_terminal_audit_20260914.json`，SHA-256 `9f33589e01c6b53a64b6f323b1859dddcbd87121cb1aa50af755d4b0f68d373b`；审计器 `tools/audit_formal_hf_event.py` SHA-256 `530176353be9455b1f9eb04bb9cfa505b2acc90418030e31fc2573a3d67f0d6e`。它实际调用 recorder 的 `validate_smoke_run()` 和每集 `check_rolling_evidence(..., required=True)`，核对 matching smoke identity、formal preflight/quiescence/formal-start、100 个 reset 与 terminal、5 个 MP4 的 `ffprobe`/`ffmpeg` 解码、102 starts / 102 exits、以及所有 rolling plan 生命周期。冻结 runtime 仍为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`，均 clean。

本批有 **154** 个自然 `plan_triggered`，分布于 39 个 episode；首个在 episode 14 / seed `100014`（该 episode terminal Success）。专门原始收据为 `receipts/formal_hf_event_rearrange_evalseed0_first_natural_trigger_20260914.json`，SHA-256 `332c0aa3d6fe7ab371153e6789f451c53541fa6ed201b66fcd9973eef3a0f862`；逐字节 raw excerpt 为同名 `.raw.jsonl`，SHA-256 `d1c345f9933ac574105c6bf5f3b78fde29140cad9e3ad875eeca1a7d3894dfb5`。它复制原 `rolling_evidence/episode14.jsonl`（SHA-256 `fcaf7a080932d302aa5379ff8afc7e207176a8a7fc8225b501d048bf1bd76466`）的 174–186 行。

首个 trigger 的时序为：plan 10 / source `270` 的普通 action query 10 已执行 prefix `15`，剩余 queue `15`；d=10 的 probe call/RNG 47 为 2/3 phase mismatch、streak 1，d=15 的 probe call/RNG 48 为 3/3 mismatch、streak 2，满足冻结判据。`plan_triggered` 原始行记录 clear `dropped=15`，与剩余后缀精确相等；下一条即为 plan 11 / source `285` 的 `start_reason=event_trigger`、`request_type=infer_audited` 的正常 action infer，使用 action RNG call 11（不是 probe RNG），输入与触发 probe 输入相同，后续记录证明新 plan 已执行 5 行、queue 为 25。收据还记录旧/新 queued actions 的 SHA-256，且 clear 与下一 plan 之间没有旧 plan record。此证据已保留供 Manager 独立裁决；未经裁决不会启动任何后续新的 event batch。

state 提交：`d3018f0`（`audit: record HF-event eval0 terminal and trigger evidence`）。

对应 MAM long-running job `380ad209-d5c5-432e-9718-247c2cced46a` 已于 `2026-09-14T12:18:45Z` 在终态审计后归档；归档注记记录了 84/100、matching smoke 与逐集 rolling evidence 通过，以及首个自然 trigger 收据。

# 置顶：第一层 J rearrange HF-fixed formal100 终态审计（2026-09-14）

三条已授权 HF-fixed formal100 均已完成并通过终态审计；每条均为连续的 100 个 accepted episode，不以 smoke 或运行中日志推断结果：

| Eval | 环境 seed | 成功 | 成功率 |
| --- | --- | ---: | ---: |
| 0 | `100000..100099` | 90/100 | 0.90 |
| 1 | `200000..200099` | 91/100 | 0.91 |
| 2 | `300000..300099` | 87/100 | 0.87 |

终态收据位于 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/formal_first_layer_j_20260914/receipts/`：eval0 `formal_hf_fixed_rearrange_evalseed0_terminal_audit_20260914.json`（SHA-256 `015228318456f60f56bd88c4417297f037edf57746305f75684d3afc0b96957b`）、eval1 `formal_hf_fixed_rearrange_evalseed1_terminal_audit_20260914.json`（`843ad93c85c12b79a388a35840c79d15a7b47c96a291ee036658fbb38572a40c`）、eval2 `formal_hf_fixed_rearrange_evalseed2_terminal_audit_20260914.json`（`41ed0610524275bc9d68c9c2b0142e16e5917ee9ada266b93ef3c5ed931cb1e5`）。审计器为同目录 `tools/audit_formal_hf_fixed.py`，state 提交 `a4b9063`。

审计实际调用 `check_rolling_evidence(..., required=True)` 与 `validate_smoke_run()`，并核对每条的 100 个连续 seed、preflight/terminal、完整 rolling-plan lifecycle、前 5 个 MP4 的 `ffprobe`/`ffmpeg` 解码、以及 102 starts / 102 exits（100 scheduler 均 exit 0；robot/policy 为受控 `runner_shutdown` / `-15`，无仍存活 PID）。三库仍为冻结 clean HEAD：OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。

HF-fixed 原始计数合计为 268/300；matched-baseline 为 254/300，差值为 +14 successes（+4.67pp）。这只是冻结原件的描述性计数，尚非科学结论。停止的 fixed MAM jobs `236c12af-448f-486d-bae2-39229981ac6f`、`5bf35bb8-50b0-41a4-8caf-c5a439c14818`、`ea9bc114-9b5f-4d11-92fd-bf290273b661` 已在终态审计后归档。

# 置顶：第一层 J rearrange HF-event formal100 已启动（2026-09-14）

C3 在启动前确认 GPU0/1/2 都满足冻结资源门槛（`free>=20000MiB`、`used<=256MiB`、`util<=10%`），且 `19400/19402`、`19410/19412`、`19420/19422` 均无 listener。三个 detached outer 均以冻结入口 `$RUN_ROOT/RMBench/.venv/bin/python $STATE/tools/launch_first_layer.py lane --formal-run <formal-run>` 启动；两秒后仍存活，随后立即登记为 MAM long-running jobs。

| GPU / 端口 | formal run | outer PID | MAM job |
| --- | --- | ---: | --- |
| GPU0 / `19400,19402` | `c_hf_j_hf_event_rearrange_trainseed0_evalseed0_100ep` | `2112144` | `380ad209-d5c5-432e-9718-247c2cced46a` |
| GPU1 / `19410,19412` | `c_hf_j_hf_event_rearrange_trainseed0_evalseed1_100ep` | `2112145` | `9776cd89-0dad-447b-a772-ceba29ff1539` |
| GPU2 / `19420,19422` | `c_hf_j_hf_event_rearrange_trainseed0_evalseed2_100ep` | `2112146` | `a79b70de-9c74-4d72-977f-7eb2060dabc5` |

写一次启动收据为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/formal_first_layer_j_20260914/receipts/rearrange_j_hf_event_lanes_started_20260914.json`；各 outer log 位于同一 state 根的 `logs/<formal-run>.lane.outer.log`。eval0 仅通过 launcher 的既有 accepted engineering smoke identity/smoke gate 复用 matching smoke；eval1/2 将各自运行 strict smoke2、完成 quiescence handoff 后进入 formal。未运行 `prelaunch_static_validation.py`，也未删除 engineering smoke 或修改冻结输入。此处只记录启动状态，不从运行中过程推断正式结果。

# 置顶：第一层 J rearrange matched-baseline formal100 终态审计（2026-09-14）

三条已授权 formal100 都通过终态审计，结果来自各自连续的 100 个 accepted episode，而非 smoke 或日志推断：

| Eval | 环境 seed | 成功 | 成功率 | 普通失败数 |
| --- | --- | ---: | ---: | ---: |
| 0 | `100000..100099` | 86/100 | 0.86 | 14 |
| 1 | `200000..200099` | 81/100 | 0.81 | 19 |
| 2 | `300000..300099` | 87/100 | 0.87 | 13 |

终态收据为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/formal_first_layer_j_20260914/receipts/formal_matched_baseline_rearrange_terminal_audit_20260914.json`，SHA-256 `361cfbb8a2cc2c5484bfd32419bace5b37d07be77c3f7de636668e060340f7c1`；审计器为同目录 `tools/audit_formal_matched_baseline.py`，SHA-256 `999853679a607ab91c530265dfb0b2ee7ff04476809aedb0b92874fb8138a3e5`，提交 `34f3323` / `acf03bc`。

收据实际调用 recorder 的 `check_rolling_evidence(..., required=True)` 和 `validate_smoke_run()`；逐条核对 300 个连续终态和 preflight reset、300 份完整 baseline rolling evidence（每集一次 `policy_rng_reset`、无 probe、常规 infer-audited query/queue/completed 路径）、15 个启用 MP4 的 `ffprobe`/`ffmpeg` 解码、以及每 run 102 个 start 和 102 个 exit（100 scheduler=0，robot/policy=`runner_shutdown` / `-15`）。三个冻结 runtime 源仍为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`，且均 clean。

停止的 baseline MAM job `09912433-20ef-45ac-9ead-853e51c97cce`、`9b596267-568b-4096-84de-fd163450944e`、`f95b92ad-5c62-4f51-a1f8-df3201cd5210` 已附终态审计注记归档。原始 outer teardown 日志保留；它们的连接重试没有覆盖结构化完成结论。

# 置顶：第一层 J rearrange matched-baseline 正式启动与 smoke→formal 交接修复（2026-09-14）

三条新 strict matching smoke 均已完整结束并通过实际 `eval_diagnostics.validate_smoke_run` 门禁；随后原 outer 在 formal 资源预检前停止，**没有创建任何 formal leaf、formal-start 收据或正式 episode**。这不是模型、仿真或任务结果失败。

初始 outer 的首因是 task-private launcher 在 smoke 返回后立即执行其严格 GPU gate。GPU0/1/2 当时分别观察到 `memory_used_mib=3099/2005/3067`，因其 `used<=256MiB` 条件被拒绝；三个 smoke 的 runner-owned robot、policy 和 scheduler 均有完整 exit 记录，当前对应 PID、端口和四卡占用均已消退。现有账本不能把瞬态占用可靠归因于自有 teardown 或其他 VM，因此没有放宽任何阈值。旧 MAM jobs `53dbce3f-987e-43fd-bcba-fbd403e839a9`、`a4fe4550-fbe4-401b-8f63-65b0a32b9c50`、`172faecb-ea53-48fc-a055-41e1b58ec85f` 已在原件审计后归档。

task-private state 修复 commit `71866bdec4a738fae56e41d3ab85f504e102776f` 在 formal 前增加有上限的 smoke→formal 静默等待：必须同时满足 recorder 的自有子进程 exit ledger 完整、记录 PID 不再存在、端口释放，以及原有的 `free>=20000MiB`、`used<=256MiB`、`util<=10%`。它每 2 秒取样，180 秒超时仍写不可变收据并拒绝 formal；不改变三库、checkpoint、manifest、scheduler、RNG、命令 argv 或冻结阈值。模拟 ready/timeout 路径、Python 编译和 diff 检查通过；验证收据 commit `1469bf787be106315c228c4f4b7d013a93d15d9d`。

原始拒绝审计收据：`/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/formal_first_layer_j_20260914/receipts/smoke_to_formal_resource_handoff_rejection_20260914.json`，SHA-256 `4f43273496b433f59bc4755bca5d70b3a77d9bf9c65d930b3902b377599dc965`。修复验证收据：`/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/formal_first_layer_j_20260914/receipts/smoke_to_formal_handoff_repair_validation_20260914.json`，SHA-256 `ab7b391cce8a15ad8dd4c8b60b2e4114a4f378107ac79d28c20189f2f2ab1e18`。

三条 formal 均在 `2026-09-14T02:19:55Z` 写入 `formal100_started=true`，使用已验证的原 matching smoke，不重跑 smoke：

| GPU / 端口 | formal run | 新 outer PID | MAM job | handoff receipt SHA-256 | formal-start receipt SHA-256 |
| --- | --- | ---: | --- | --- | --- |
| GPU0 / 19400,19402 | `c_hf_j_matched_baseline_rearrange_trainseed0_evalseed0_100ep` | `1405062` | `09912433-20ef-45ac-9ead-853e51c97cce` | `2d4e27f5a0d001af686d570d921cbc5712e21728f5dfafe6024c6d9c975eb80d` | `4376a28fc5fcbcaec9230fb6b943c9fbd835e48ca0e32fa8b9ebfa734813e2f7` |
| GPU1 / 19410,19412 | `c_hf_j_matched_baseline_rearrange_trainseed0_evalseed1_100ep` | `1405063` | `9b596267-568b-4096-84de-fd163450944e` | `36d3cbdbe45156ebd49f3caf4818ace0f251221eb20a626e09e6bf2f8e6bb2d2` | `8035c9abcda4922dd576776314e94d9b3e914c704ff889bde768b380c2099f33` |
| GPU2 / 19420,19422 | `c_hf_j_matched_baseline_rearrange_trainseed0_evalseed2_100ep` | `1405064` | `f95b92ad-5c62-4f51-a1f8-df3201cd5210` | `7cac9385f620ce7455ce8847754e2a040e97dd21afca8b6c6c27ce68cac1289a` | `0d4954aa31e114051a10ee2cce847d39147ed94bd346eba9e9cf48fd13311ad6` |

运行时 handoff/formal-start/preflight 原件均在同一 `formal_first_layer_j_20260914/receipts/` 目录。预检记录启动时四卡均为 `1MiB used / 24080MiB free / 0%`，对应端口空闲，三库仍为冻结 clean HEAD：OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。当前只报告 formal 已启动；不从 smoke 或运行中状态推断正式分数。

## 最终工程阶段收尾（2026-09-14；五个 profile / 10 个已授权 episode）

本轮已授权的工程轨迹预算已用尽：五个 profile 各恰好两个 accepted episode，共 **10/10**；没有增加 seed、episode、重试、调参或诊断，`formal100_started=false`。以下是工程运行、基础设施和轨迹合同证据，**不构成科学效果比较，也不构成 formal 准入结论**；任务层的科学裁决仍由 Manager 完成。

最后一个叶子 `c_hf_j_hf_event_rearrange_trainseed0_evalseed0_smoke2` 已完成并归档：episode 0 / seed `100000` 与 episode 1 / seed `100001` 都是 Success，logical step 分别为 392 / 404，普通 action 调用各 14 次、probe 分别为 65 / 67 次，实执行 K 分布为 `{30: 13, 2: 1}` 与 `{30: 13, 14: 1}`。逐条以 `source_step + completed_rows` 重建完成时刻，并核验 probe source/target、forecast 消费、后续普通 action 输入、JSONL header/终态、视频和受控进程退出；`trace_contract_validation.json` 全部通过。两集各只有一次高偏差（episode 0：`u=230,d=20,2/3`；episode 1：`u=255,d=15,3/3`），均未连续两次，因此 `trigger_eligible_count=0`、`trigger_count=0`、`clear_count=0`，没有观察到真实 **trigger → clear → normal replan** 路径。没有为了制造该覆盖而改变冻结阈值或增加样本。

| Profile | 两集普通任务结果 | ordinary action / probe 调用 | 覆盖状态 |
| --- | --- | --- | --- |
| `j_shadow_rs30_degradation_rearrange` | Success / Fail | 14/0；24/0 | `r_s=30` 工程退化控制，无中途 probe；不覆盖 event 路径 |
| `j_hf_fixed_put_back` | Fail / Fail | 17/83；17/83 | 两个 Fail 都是普通任务的 `step_limit_reached`，不是 runtime 或基础设施错误；HF-fixed 不启用 event clear/replan |
| `j_hf_event_put_back` | Success / Success | 12/55；12/55 | 两集均未满足冻结的连续触发判据；未覆盖 trigger→clear→replan |
| `j_hf_fixed_rearrange` | Success / Success | 14/65；14/67 | HF-fixed 不启用 event clear/replan |
| `j_hf_event_rearrange` | Success / Success | 14/65；14/67 | 两集均未满足冻结的连续触发判据；未覆盖 trigger→clear→replan |

五个 leaf 均已完成各自的基础设施和轨迹/合同验收：恰好两个连续 accepted seed、完整终态/JSONL evidence、关闭随机光照、视频策略和受控服务收尾均已核对。合计记录 152 次 ordinary action 调用和 540 次 probe；全局 `trigger_count=0`、`clear_count=0`、普通 action replan 数为 0。HF-event 的两条未覆盖路径是明确的证据缺口，不以运行是否 Success/Fail 填补。

最终 event leaf 的完成收据为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/hf_trajectory_engineering_20260914/c_hf_j_hf_event_rearrange_trainseed0_evalseed0_smoke2/stage_receipt.json`，SHA-256 `38a29085a787e70c3a23ef0f213b5731f5300d4e0d325b9e78bf741eb2ae3a1e`；其 trace validation / official audit / execution / review SHA-256 分别为 `4ca29736c9bc907eec214b67d9a0b8fa2259df6d25405e2797c36b9a2c956c86`、`d3ed9582fec4e56156432bb1c90c0231d80a4030acb35a76b9f1f808ef92fe43`、`ab51f7d222c6a8b2b1d835a5934d2b564589db944de193a3ef7837ea19e4a0b6`、`2d220d44fea2af4467854f3f3c6cc735f34caaa7ca2697d8d4d77099f5ebfa3d`。审计后端口 `19400/19402` 无 listener，C3 GPU0 空闲；OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4` 均 clean。MAM job `def61eba-a703-480b-b431-eae84eb80ee1` 已在该验收后归档。

任务私有的五 profile 汇总为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/hf_trajectory_engineering_20260914/five_profile_summary.json`，SHA-256 `33b38af07acc100e81a540c236392f6cf492e930d5b2091ddbec9396103a274e`。本节覆盖并取代下方各叶子段落中“下一项运行”的历史提示；本工程阶段不再启动任何 GPU 工作或 formal。

## 最新工程轨迹状态（2026-09-14；C3 rearrange J HF-fixed）

授权队列的第四个两集 leaf `c_hf_j_hf_fixed_rearrange_trainseed0_evalseed0_smoke2` 已完成、通过逐条 rolling 合同验证和原工具单 leaf audit，且其 stopped MAM job 已在资源释放后归档。它仍是 **engineering candidate / matching-smoke-only** 证据：`formal100_started=false`，两集 Success 不构成 formal 准入或效果结论。

- 冻结 C3 运行树、GPU0、端口 `19400/19402`、checkpoint 和三库身份保持不变。execution return code 为 0、`ports_released_after=true`；审计后两端口无 listener，OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4` 均 clean。`hf_engineering.py` SHA-256 为 `dcf93891de82adaf21e676c55ee30901309f9c9a6097841ff4be4c7ba7f29c87`。
- 恰有两个连续 accepted seed：episode 0 / `100000` 与 episode 1 / `100001`。benchmark `completed`、`error=null`、target episodes 为 2；两集都以 `episode_terminal`、scheduler return code 0 和 Success 结束，logical step 分别为 392 与 402。video 策略正确：episode 0 启用、392 frames、检查通过；episode 1 禁用、检查通过。robot 与 policy 以受控 `runner_shutdown` / `-15` 收尾。
- 实际完成 action rows 分别为 392 与 402：各 14 次 ordinary action，probe 分别为 65 与 67 次，实执行 K 分布为 `{30: 13, 2: 1}` 与 `{30: 13, 12: 1}`。最终未执行的 28/18 行来自 terminal 后缀，不计为 clear。每集都有一个保存的 `policy_rng_reset`；action/probe 只报告 wire 可见的 `stream`/`call`（action 1–14，probe 1–65/67），不把它们称为内部 sampler key。
- J rolling 合同逐条复算通过：每个 progress 的完成时刻由 `source_step + completed_rows` 重建；消费行使用 `u - forecast_source_step - 1`，并同时核对到保存 forecast 的 selected IDs、下一 probe 输入和下一 K30 boundary 的 ordinary-action 输入。probe 只发生在已完成的 `+5/+10/+15/+20/+25`，不发生在 K30 boundary 或 terminal 后；phase comparison 使用当前 action plan 的 reference、old `d:d+3`、new `0:3` 和 absolute targets `[u+1,u+2,u+3]`。HF-fixed 的两集均 `trigger_count=0`、`clear_count=0`、ordinary action replan 为 0；少量高偏差均只形成最大 streak 1，未改变队列。
- task-private trace contract 为 `trace_contract_validation.json`，SHA-256 `649bf10718a99346ce453c167e8384c5383a19167db8d2558c06bc4dbf8e42c2`，`all_pass=true`。execution SHA-256 为 `fa86ec8fea4524aff5f44fd79557160c6fdea13872aa008853d3f2b007d9010a`；官方 `audit --profile` stdout SHA-256 为 `e9405aa952cd283db9c2d64902876cb551ab48f939d08a878a12bc7405dd6a13`，review SHA-256 为 `2f95b8c50f94194aa62fcbca701efa9e2b01f8cd0876b7373e0f474a40a6e046`。完成的 stage receipt SHA-256 为 `831120a90e00f72563197cc87d591bedb8e0dc3a37b13d965093d44caa9c0912`；MAM job `7767615d-80d9-43e5-abd3-4404b31cb7ea` 已归档。

下一项仅按已授权顺序运行 `c_hf_j_hf_event_rearrange_trainseed0_evalseed0_smoke2` 的两集；仍不调整参数、seed、checkpoint、runtime 或工具，也不启动 formal。

# 交付报告

## 最新工程轨迹状态（2026-09-14；C3 put-back J HF-event）

授权队列的第三个两集工程 leaf `c_hf_j_hf_event_put_back_trainseed0_evalseed0_smoke2` 已完成、通过离线轨迹合同和原工具单 leaf audit，并在归档前确认 C3 GPU0 端口释放。它仍是 **engineering candidate / matching-smoke-only** 证据：`formal100_started=false`，不自动获得 formal 准入。两集的实际 benchmark 结果都是 Success，但这不是效果结论或 trigger 覆盖结论。

- 冻结 C3 运行树、GPU0、端口 `19400/19402`、checkpoint 与三库身份保持不变。execution return code 为 0、`ports_released_after=true`；审计后两端口均无 listener，OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4` 都 clean。
- 原 `hf_engineering.py` SHA-256 为 `dcf93891de82adaf21e676c55ee30901309f9c9a6097841ff4be4c7ba7f29c87`。execution SHA-256 为 `1e9744587bb708780531b5c1903164eaecc9c9b270aa10a718666ffba5720d70`；`audit --profile` exit 0，stdout SHA-256 为 `3c22d5f5b0e4688d98198b6f14c01ce281c38b78947b882cdf952dd3ac8d8559`，review SHA-256 为 `7285dea5822bcc1f67f3943ac1af1830796d3305d832e14b6c90f90195ebf9b9`，无 observability gaps。
- 恰有两个连续 accepted seed：episode 0 / `100000` 和 episode 1 / `100001`。benchmark `completed`、`error=null`、target episodes 为 2；两集都以 `episode_terminal`、scheduler return code 0 和 `Success` 结束，logical step 为 334。video 策略正确：episode 0 启用、334 frames、检查通过；episode 1 禁用、检查通过。robot 与 policy 正常以 `-15` shutdown 记录收尾。
- 每集实际完成 334 action rows，12 次 ordinary action 和 55 次 probe；实执行 K 分布为 `{30: 11, 4: 1}`。前 11 个 plan 逐个完成 30 行；最终 plan 的 source 为 330，完成 4 行、丢弃 26 行，终态逻辑步由 `source_step + completed_rows` 和 `episode_status.logical_step` 交叉核对，而未误用 `plan_progress`/`plan_terminal` 的顶层 `logical_step`。
- J rolling 合同逐条重算通过。55 个 comparison 均从保存 forecast field order `[“phase”, “origin_mat”]` 的 column 0 重算，使用当前 action plan 为 reference、old indices `d:d+3`、new indices `0:3` 和 absolute targets `[u+1,u+2,u+3]`；无 gap、stale、invalid、probe error、exception 或越界。每个 probe 的输入等于刚消费的 state，后续 ordinary action 的 memory input 等于前一 K30 boundary 的消费 state。
- 每集恰有一个 `policy_rng_reset`；保存的 action / probe `stream`、`call` 仅是 wire metadata（action 1–12、probe 1–55），不称作内部 key。唯一高偏差是 source step 125、`d=5`、3/3 phase mismatch、streak 1；它低于 `min_prefix=10` 且不连续。两集均为 `trigger_eligible_count=0`、`trigger_count=0`、`clear_count=0`，因此真实 **trigger → clear → normal replan** 路径未被观察到；没有为制造覆盖修改阈值或增加 episode。
- 离线合同收据位于 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/hf_trajectory_engineering_20260914/c_hf_j_hf_event_put_back_trainseed0_evalseed0_smoke2/trace_contract_validation.json`，SHA-256 `2ee5b6e3f51fbd9770ae96d94f57c17a40ff4dddda7ef04d6a40571a132c3cec`。两个 episode 的 action-input、probe-input、consumption canonical SHA 分别相同：`b49efa9d1e46d5fb3431bff594aaa5d545be5d3ac61f3d2d34711fdd9fc969ca`、`ca1056ff3a99a0066634f59425da97f84bc2649b0eb51aad206cb988b8c8fbdf`、`454310333cd2b80f49bd4713b43646ed369386811097984605f0d13cd6a4dd96`。rolling evidence SHA-256 为 episode 0 `42696aba7f73b843c87e43cb72e1e2c6989adb6c11f81e452de37ff48714bbc6`、episode 1 `dba9ff91cfa76eb65619f02c7bac3fcdb91e5d4f2ffa624be1865e07cb635f61`。
- 完整 stage receipt 位于 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/hf_trajectory_engineering_20260914/c_hf_j_hf_event_put_back_trainseed0_evalseed0_smoke2/stage_receipt.json`，SHA-256 `eff848ff7cd3f09cc14ab27c086cdde48ba740cde52f25e4e884c2210d2873db`。MAM job `e56a6dc1-3c15-43cf-94f0-1741c88f8880` 已在审计和资源释放后归档。

下一项仅按已授权顺序运行 `c_hf_j_hf_fixed_rearrange_trainseed0_evalseed0_smoke2` 的两集；仍不调整参数、seed、checkpoint、runtime 或工具，也不启动 formal。
## 最新工程轨迹状态（2026-09-14；C3 put-back J HF-fixed）

授权队列的第二个两集工程 leaf `c_hf_j_hf_fixed_put_back_trainseed0_evalseed0_smoke2` 已完成并通过基础设施、原工具 audit 与逐条 rolling 合同验收。它仍是 **engineering candidate / matching-smoke-only** 证据，`formal100_started=false`，不会自动启动 formal；两集的实际任务结果均为 Fail，不能写成控制成功。

- 冻结 C3 运行树、GPU0、端口 19400/19402、checkpoint 与三库身份均保持授权状态。execution return code 为 0、`ports_released_after=true`；完成后四张 GPU 均为 `1 MiB / 24564 MiB / 0%`，两个端口无监听，OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4` 均 clean。
- 原工具 `hf_engineering.py`（SHA-256 `dcf93891de82adaf21e676c55ee30901309f9c9a6097841ff4be4c7ba7f29c87）使用已保存的 prepare/input-audit/manifest/scheduler/dry-run 输入执行该单 profile。execution SHA-256 为 `593196af4b14bf5d537bf4f3cc4c7d39286bb167d6d242d0631d93aa6c2ec393`；原 `audit --profile` exit 0，review SHA-256 为 `efd2a6d9e00c5cba72d37901bb44f8bcd784ab788cc5a2ad081e949f58fa00dd`，无 observability gaps。
- 恰有两个连续 accepted seed：episode 0 / `100000` 与 episode 1 / `100001`。两者均正常以 `episode_terminal`、scheduler return code 0 结束，rolling evidence 完整而未截断；video 策略为 episode 0 启用且 500 帧、episode 1 关闭且检查通过。两集均在 logical step 500 以 `step_limit_reached` 终止，diagnostics 的普通任务首因均为 `button_not_pressed_after_center`；这不是 runtime 或基础设施失败。
- 每集实际完成 500 action rows：17 次普通 action、83 次 probe，实执行 K 分布为 `{30: 16, 20: 1}`。16 个完整 plan 只在已完成的 K30 边界开始，最终 plan 从 source 480 实际完成 20 行并丢弃 10 行；所有 action execute 均 queued 30。没有 `plan_triggered`、clear、probe error、invalid monitor、exception 或中途 action replan。
- J rolling 逐条复算通过：99 次 `forecast_consumed` 均以当前 plan source 加实际 completed rows 重建，probe 实际时刻为每个完整 plan 的 `+5/+10/+15/+20/+25`，末 plan 为 485/490/495。83 个 comparison 均满足 absolute targets `[u+1,u+2,u+3]`、reference source 为当前 action plan，old indices `d:d+3`、new indices `0:3`，并从保存的 forecast phase column 重算；没有末端越界。probe 的输入逐条等于刚消费的 forecast state，下一普通 action 的 state 输入逐条等于前一 K30 边界的消费结果。
- 每集恰有一个 `policy_rng_reset`；action 和 probe 的保存 `stream`/`call` 是 wire metadata，分别为 action 1–17、probe 1–83，不声称捕获内部 key。HF-fixed 仍可记录非触发偏差 streak（最大 4），但所有 `trigger=false` 且 clear count 为 0，因此它没有发生事件重规划。
- 离线合同收据为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/hf_trajectory_engineering_20260914/c_hf_j_hf_fixed_put_back_trainseed0_evalseed0_smoke2/trace_contract_validation.json`，SHA-256 `7483ffca1dc661a84ef30e0b6db967731c12025be84f375f7eb1386ac6673a9b`。其中 action/probe 输入 canonical JSON SHA 分别为 `672ec0cea4b4eaf5cb2da005e1103de28e13f94c845188142936488e92ead3cf` 与 `a71ad0eeb8accbd683b8803fcc35bb43091e1508c7bb65709f27b3965267e981`；rolling evidence SHA 分别为 episode 0 `56432735be91341e5792a2012e3ecaf3a6285286031ba4c6834698fee4bfc603`、episode 1 `4ac88ef952486f227f9962a6608a0182c816d12ebcb3386bbc16bd174696cd64`。
- 完整阶段收据为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/hf_trajectory_engineering_20260914/c_hf_j_hf_fixed_put_back_trainseed0_evalseed0_smoke2/stage_receipt.json`，SHA-256 `2bd6cf0cdd6384b0923bf39f8a884067c7f7d7551d244846ee15807b9f21e875`。MAM job `64f96ff5-df5e-4709-b836-c4941b9c32c4` 已在审计和资源释放后归档。

在这一 leaf 归档后，下一项仅为已授权的 put-back J HF-event 两集；仍不得因本工程结果启动 formal 或改变阈值、样本、seed、runtime、checkpoint 或工具。

## 最新工程轨迹状态（2026-09-14；C3 rearrange J r_s30）

授权队列的首个两集工程 leaf 已完成并通过基础设施、证据和 r_s30 合同验收：`c_hf_j_shadow_rs30_degradation_rearrange_trainseed0_eval0_2ep`。它是 **engineering-only degradation control**，不会作为 matching smoke 或 formal 的准入依据；其余四个 J HF profile 仍须各自验收，且不会自动启动 formal。

- 使用 C3 `wuwen-4090-3` 的 GPU0、端口 19400/19402 和冻结运行树；执行前 GPU0 为 `1 MiB / 24080 MiB free / 0%`，完成后四卡均为 `1 MiB / 24564 MiB / 0%`，端口已释放。冻结 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4` 在运行后仍 clean；没有修改工具、三库、checkpoint 或已有 leaf。
- 原 `hf_engineering.py`（SHA-256 `dcf93891de82adaf21e676c55ee30901309f9c9a6097841ff4be4c7ba7f29c87）先完成 task-private `prepare` 和 `dry-run`，再运行该一个 profile。外层 return code 为 0，`formal100_started=false`；原单-leaf `audit --profile` 通过，review SHA-256 为 `b5d4066880ca4adef101171a05dce475d9571dbd2c830eb69680566268881afb`。
- 两个连续 accepted seed 为 episode 0 / `100000` 和 episode 1 / `100001`；两者 scheduler 均以 `episode_terminal`、return code 0 退出，rolling JSONL 的 header 身份、最终 `episode_finished`、`evidence_complete=true` 和无 `truncated` 均成立。video 策略为 episode 0 启用且 `393` 帧、episode 1 禁用且检查通过。结果为 Success / Fail；后者的普通任务失败原因为 `step_limit_reached`，不是 runtime/infrastructure error，因此按授权保留原件并继续队列。
- r_s30 合同实际成立：两个 episode 都是 `mode=shadow`、`monitor_interval=30`、legacy continuous action RNG lifecycle；probe count、trigger count 和 clear count 均为 0。只报告 wire 可观察的 action stream/call 元数据：episode 0 共 14 次普通 action（calls 1–14），episode 1 共 24 次（calls 15–38）；不把它们称为模型内部 key。
- 实际完成 action rows 为 `393` 与 `700`。执行 K 分布依次为 `{30: 13, 3: 1}` 和 `{30: 23, 10: 1}`；终态分别丢弃 27 与 20 个未执行后缀。每次 action 的保存状态输入均有记录（首个 memory IDs `[0,0,0]`，末个分别 `[3,2,0]` / `[3,1,0]`）；没有 probe source/target 或 probe action 可消费。记录的 action inference 时间为：episode 0 共 14 次、总 `27704.763 ms`、均值 `1978.912 ms`（含首次加载）；episode 1 共 24 次、总 `1435.361 ms`、均值 `59.807 ms`。
- 结果 leaf 位于 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914/RMBench/eval_result/memory_chunk_20260910_hf_engineering/c_hf_j_shadow_rs30_degradation_rearrange_trainseed0_eval0_2ep`。rolling evidence SHA-256 为 episode 0 `832ffd5bd62b9202e6e690828108eee8c29e1ba0c2c9c774ba4b1a53a2cd4fb2`、episode 1 `4890a34500b800e2f2754bf964b7c02c182ffa39ba166f5c236c4358968808b9`；完整阶段收据为 task-private `hf_trajectory_engineering_20260914/.../stage_receipt.json`，SHA-256 `e37be9274ed9368d73b771f241e7ae1614b8ab97a7f23389c4b9bab5d99f321d`。
- MAM job `e2190cb8-4c10-465a-b46a-bcc1e4d17861` 已在停止、审计和资源释放后归档。独立工程审阅 `9c7622d0` 已验收且没有新的阻断；它不建立完整环境等价或 formal 科学结论。

接续顺序保持为 put-back J HF-fixed、put-back J HF-event、rearrange J HF-fixed、rearrange J HF-event；每个 profile 只运行其授权的两集，并在前一 leaf 完整验收后才启动。

## 先前执行结果（2026-09-14；C3 GPU0 授权的单实例 C0/C1/P 检查）

**结论：通过。** 已在 C3 的 `GPU0` 只执行一次授权的 `--execute`：一个真实 backend 实例依次完成 C0、C1 和 P；receipt 的 `decision` 为 `pass`。这只说明固定保存输入在同一已加载实例内，五次 forecast probe 未改变后续普通 action 的软件可观察结果或 action RNG 状态；它不证明环境推进、五帧新观测、完整 rollout、HF 效果或 formal 准入。

### 执行与运行身份

- C3 实际 hostname 为 `is-ddj72jhhjdy7hiyj-devmachine-0`；GPU0 为 NVIDIA GeForce RTX 4090。执行前 GPU0 是 `1 / 24564 MiB, 0%`，结束后复查仍为 `1 / 24564 MiB, 0%`；外层 PID `1361565`、launcher `1361567`、工具 Python `1361577` 均已退出。
- 外层启动于 `2026-09-13T22:39:01Z`、结束于 `2026-09-13T22:40:15Z`，退出码 `0`。`stderr.log` 只有 hwloc topology 警告与 XLA 找不到 `ptxas` 后交给 driver PTX compilation 的警告，没有终止异常；`stdout.log` 指向 receipt。
- 实际命令、cwd、解释器、CUDA/JAX/XLA/cache 环境与冻结三库身份在 `execution_20260914_c0_c1_p_v1/launch_metadata.json` 中保存。运行值为 `CUDA_VISIBLE_DEVICES=0`、`SAPIEN_RENDER_DEVICE=cuda:0`、`VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.40`，以及指定 checkpoint 的 `RB_OPENPI_POLICY_DIR` 与冻结 bridge/openpi-client `PYTHONPATH`。没有环境 reset、simulator、policy server、warmup、重试、第二 backend/episode 或正式评测。
- receipt 确认冻结运行树 clean：OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。工具、tests 和冻结源码均未改动。

### 预算、收尾与对照

- `budget` 为普通 action `3/3`、joint forecast probe `5/5`、总 sampler calls `8/8`，`retry_policy` 为 none；receipt 中正好有 3 条 `ordinary_action` 和 5 条 `forecast_probe`。调用顺序是 C0 action、C1 action、P probe 1–5、P action；C0/C1 精确对照通过后才进入 P。
- `stop_reason=null`、`error=null`、`cleanup_errors=null`、`serialization_errors=null`，`policy_state_restored=true`。工具结束前的临时 rolling state 已恢复为工具调用前状态。
- C0 与 C1 的 reset/final action/probe keys、序号和所有普通非 timing 输出均精确相同。P 的最终普通 action 同 C1 也精确相同；比较字段为 `actions`、`memory_prediction`、`memory_prediction_ids`、`memory_raw_actions`、`policy_rng`，唯一排除的是 `policy_timing`。三次普通 action 的同一非 timing 树 SHA-256 是 `4edc1afd8518085f8943ba8dde7eb28caa676d3cf40fd5089193c15bc5943581`，因此没有触发“输出不同”时才允许进行的离线元素差异计算。
- P reset 时 action key 为 `[0, 0]`、probe key 为 `[1099583820, 1938652209]`，两个序号都是 0。五个 probe 均保持 action key `[0, 0]` 和 action 序号 0，只推进 probe key/序号：

  | probe | probe key（调用后） | probe 序号（调用后） |
  | --- | --- | --- |
  | 1 | `[3671460393, 3925137291]` | 1 |
  | 2 | `[2114279338, 2039787051]` | 2 |
  | 3 | `[891150875, 1373214049]` | 3 |
  | 4 | `[1391925822, 3050319562]` | 4 |
  | 5 | `[3086767906, 2453882555]` | 5 |

  P 最终普通 action 后 action key 为 `[1797259609, 2579123966]`、action 序号为 1；probe key/序号仍为 `[3086767906, 2453882555]` / 5。每条调用的输入前后语义 SHA 均为 `a489f7d1f871ea4667d404f82a6cdd229e9081e523b041bbaaab50d1ffe5034e`，receipt 记录没有调用修改输入。

### 实际输出与完整性

P 的完整普通输出保存为 `outputs/P_ordinary_output.pkl`：`actions` 为 `float32[50,14]`（数据 SHA `b56eb60ce8d5317e804a72bc8907a1a28e00eba111e1211c65937b07f1cd20a6`），`memory_prediction` 为 50×2，`memory_prediction_ids` 为 `int32[50,2]`（`8f3c38e64c3232a66d1bdc6035bd3a15735d917d3a193039e0ea8213292f6b28`），`memory_raw_actions` 为 `float32[50,32]`（`7f13cb5dbb9fc4ef3b66bdf969cdd72e0b085a7e05235def0048c2b9f88b1e80`），并含 `policy_rng` 与 `policy_timing`。前四项及 `policy_rng` 同 C0/C1 精确相等；完整 artifact 的二进制 SHA 会因 timing 内容不同而不同。

receipt 的 artifact writer 尝试并成功写入全部 9 个预期 pickle。实际路径都在 C3：`/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/run_20260914_c0_c1_p_v1`。

| artifact | SHA-256 |
| --- | --- |
| `inputs/stripped_observation.pkl` | `63e13ce343e048ec9f3ba3d7ee7d5cbe4dfd6381e0091a4b3d136f212ba3d34e` |
| `outputs/C0_ordinary_output.pkl` | `c00aa5b9c78fa328e1db2d461401382b0ee67eb26feca8be40fd14dfa1104efb` |
| `outputs/C1_ordinary_output.pkl` | `494c26d25f59630908a8414c77ed8b9d81c5fed6989fcfe3001b1895319fd7b5` |
| `outputs/P_probe_01_output.pkl` | `ecd551b4d198ef80ff9fdc4d587b637747f67826019930e1b4313b9ede3a8591` |
| `outputs/P_probe_02_output.pkl` | `b31b9486cce417ca4f123a9b798e5303d52a9bb81736146069e57f94df706708` |
| `outputs/P_probe_03_output.pkl` | `daa046ac0182833700095852281edc97baedd29e5a413eaad8878700f86ba9e0` |
| `outputs/P_probe_04_output.pkl` | `0fbff7e9a137515ad13b3a3d6bd72f942638b42bf3ce819057092441a2f71b39` |
| `outputs/P_probe_05_output.pkl` | `02b65fcc85e27ad6f485e045530ed60202f2e7ebff7a35168dd9dea46e6ee175` |
| `outputs/P_ordinary_output.pkl` | `ecb30324e686a598e69ace4c38b76ddc4155ebe03709187affde245a574c3f72` |

输入、工具和结果身份如下：request SHA-256 `8e642b353b0a2bfd6e7569f1f4c52aa9490aad92df4102ffda73ecf47091ac48`；已验收 source plan v4 SHA-256 `4408a8732f3fa259f5224de6dfe7c40add97e40e5a7fc511a076f8f4fb5a9916`；实际 execute `plan.json` SHA-256 `dbeb43c9b87b78ad3a52f70afe14979e6d1780190988308db89bcb03948fbbd7`；工具 SHA-256 `6edd0ba2ce04c6ba70c9efa239cd5f603e9097ad7079f10dce013a660850491c`；receipt SHA-256 `14f2a9a771387f4703c84226d852c82f9442650f42d9ba8b331139fbb2641983`；launch metadata SHA-256 `72909a6edd4ade56bd8591458f0bce8da9de264ed83cc8ad64bbbc326af84b79`。

本次实际时长约 74 秒，结束后才尝试依据先前等待记录登记 MAM job；`mam job add` 复查 PID 时已发现它停止，因而拒绝创建 job。没有本次运行可归档的 job，也没有触碰任何其他进程。

## 上一修订（执行前 CPU 准备；2026-09-14）

已修复 Manager 复核指出的两处 CPU 控制缺口；**没有**以 `--execute` 运行检查，没有构造真实 `OpenPiBackend`、加载 checkpoint/model/GPU、发送 sampler request、环境 reset、仿真轨迹或 formal。历史正常 action 诊断预算仍为 **8/8**，本节未改变其记账或结论。

- 工具现在在每个 action/probe 调用前只保存实际 JAX key 的不可变对象引用与 Python sequence；对应 backend 调用正常或异常返回后，先保存完整输出，再物化调用前/后的 key 数据。它不在 reset 与第一个 action/probe 之间读取 key 数组。P reset 到 probe 1 前只比较 key 对象身份和序号；probe 1 返回后立即物化并严格比较 P reset 与 C0/C1 的实际 action/probe/initial key 内容，任何失败均在下一个 probe/action 前停止。
- `run()` 的 protected finalization 会在内存中先捕获 `policy_state_before_restore`，然后独立尝试恢复 policy 状态；只有 `run()` 返回后，外层才序列化并写磁盘 receipt。因此 `policy_state_before_restore` 表示恢复前的内存状态，不能表述为“收据写入后恢复”。post-call key 物化、finalization、restore 和 artifact serialization 的次要错误分开记录，绝不覆盖已存在的首因、调用账本或已完成 artifact。
- `execute()` 保留已构造 checker 的 calls、budget、record 和 artifacts；即使末次 key 物化或清理失败，也不会回退成新的 `0 action + 0 probe` precheck receipt。artifact writer 会独立尝试每一个已完成 pickle，并把单个写入失败写入 `serialization_errors`；若此前没有首因，该序列化失败成为 receipt 的首因，已有首因绝不被替换。
- CPU seam tests 现为 `11 passed`：原有控制/预算/输入隔离/plan tests 之外，新增了拒绝 sampler 返回前任何 key 读取且验证旧 key 引用不会被后续 reassignment 覆盖的时序 seam；通过注入 checker factory 的 `execute()` 末次 key 物化失败 seam，验证最终 receipt 仍为 `3 action + 5 probe` 且 C0/C1/P/五个 probe outputs 保留；以及单个 pickle 失败后继续写其他 artifact 的 seam。Ruff 与 Python compile 通过。
- [检查说明](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/README.md)、[源码审计](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/source_audit.md)、[工具](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/tools/probe_side_effect_check.py) 和 [CPU tests](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/tools/test_probe_side_effect_check.py) 已同步到 C3 task-private 根 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check`。工具、tests、说明、审计 SHA-256 分别为 `6edd0ba2ce04c6ba70c9efa239cd5f603e9097ad7079f10dce013a660850491c`、`fb1d7a84cc9ae6b88a36fa9521bc676abad5c0d75d45c44dee314fda31db6e8b`、`7ae2d57856fb0db3302a530cde8cd9c3d8cd00a65fd4beb26c450b6b0c1933c8`、`b879680aedb7655e1299079f15d4e80173ecf8fcf7422de643e29f78d85c3abc`，本机与 C3 一致。旧 `plan_20260914_v2/plan.json` 和中间 `v3` 均保留；新 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/plan_20260914_v4/plan.json` 已在默认模式写入，SHA-256 `4408a8732f3fa259f5224de6dfe7c40add97e40e5a7fc511a076f8f4fb5a9916`。其 `mode=plan` 明确记录未构造 backend/model/GPU/server/environment reset 或 sampler，并确认冻结 OpenPI / bridge / RMBench 为 `0ce566bd` / `ffa12249` / `6abebf08` 且 clean。

源码审计结论仍是可实施性而非实验结果：`Policy.probe_forecast` 使用独立 `_probe_rng`，而 `infer_audited` 消耗 `_rng`；backend 对两者均是直接转发，显式 `reset_episode_rng` 初始化/复位 rolling state。现有 WebSocket RPC 不暴露或设置实际 key，因此单独 RPC 无法做该精确对照，必须使用本工具的同进程 backend helper。controller 方面只证实 worker deque 将同一输入 action rows 按顺序逐项传给 `env.take_action`；`get_obs` 仍会 render/camera，环境 `take_action` 有 TOPP/physics/可能 light RNG，故不声称 30-row 与分次 5-row drain 的完整环境推进等价。

本节交付后等待 Manager 验收和未来明确 GPU 授权；不能据 CPU seam pass、plan 或源码审计把 probe 副作用检查写成 PASS，更不能解冻 HF/matching/formal。

## 此前状态（2026-09-14；覆盖下方历史样本预算）

已完成 Manager 授权的 `put_back_block` / train seed 0 / env seed `100000` 修正来源路径 matched shadow：它只发出 **1** 次正常 action request，并以预期的诊断截停 `exit 70` 结束。收据确认唯一 accepted reset 为 episode 0 / seed `100000`，恰有一次 `infer_audited` 与一次 execute；原 iteration 后 clear，非 drain status 为 `queued=30`、`dropped=30`、`logical_step=0`。没有第二 query、episode、replay、warmup 或 probe。

旧 shadow 失败原件仍保持不变（`64ee0c7c9f4e4d77a99e20af55ed830bc06b42455cbe820ca34e98ceb0a89d21`）：它因 `MemoryCheckpoint` source root 缺少 `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` 层而在 service/reset/action 前停止，未消耗 sample。修正版只改用正确 source root、全新 result/capture 路径和 run 名；没有修改冻结工具或三库源码。

- 正常 action sample 总预算现为 **8/8**，剩余 **0**。不得 retry、重跑 baseline，或启动 matching/formal smoke、完整轨迹或 formal 评测；formal 仍冻结。
- 两臂完整实际 policy-request leaf fields 完全相同：`$.cmd`、`$.images.cam_high`、`$.images.cam_left_wrist`、`$.images.cam_right_wrist`、`$.memory_input_ids`、`$.prompt`、`$.state`。`policy_call_kwargs`、正常 policy/robot commands、runner environment、policy metadata、checkpoint verification 与 metadata verification 也相同。
- 每臂自身 H50 `float32[50,14]` 的前 30 行均精确等于实际 K30 `float32[30,14]`。跨臂仍有数值差异：H50 为 `532/700` 个元素不同，max abs `0.0036021433770656586`、RMSE `0.0006788336719106482`；K30 为 `314/420` 个元素不同，max abs `0.002218961715698242`、RMSE `0.0006341486370427415`；首差均在 `[0,1]`（baseline `0.0005527432076632977`，shadow `-0.001193587202578783`）。
- 版本化配对分析同时归一化共享 result root 与冻结运行树 result root。归一化后 preflight/episode context 仅余六个 `task_facts.final_block_pose` 标量差异；它们不在捕获到的实际 policy request 中。既有源码证据表明该 task-fact probe 不是有效的首 query 输入身份，因此这些值不能被当作实际输入不一致的证明。
- 没有可直接捕获的模型侧实际 PRNG key；响应中的 `policy_rng` 只是 stream/call 元数据，未据此推断 key。

本对照仅是有界诊断，不是 matching smoke 或 formal 证据；一组首 query 的相同或不同都不解冻正式评测，也不建立历史差异的因果解释。

证据根为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914`。关键完整性哈希如下：

- 修正 launcher `launch_shadow_fixed_source_root.sh`：`171d33f1068074bbcb5551da27263adb1315ae223f51aed2765a9884cd6af6e6`；三处最小 diff：`plans/matched_shadow_fixed_source_root.launcher.diff`，`e4f8faeb5359162b8171217e952d308161c57cba251e9a8ce7926180957f5071`；repair record：`dd337fdab6022ec196c64ff6831f15ccf5b7b37ad07506e0dde16f81bcd0da31`。
- plan `67788b1eabfdd70af3464dc93443e8375c974eea3b1d62d8c6197f2436159666`；preflight tool `c8be70cb403df3951038c0c42861b9aaa58aba872d20ae1d465ceee7810fe412`，preflight result `4adefcb45e34d41f2ed49878978f5a743fe0fe0d82cf1a4f501ec1cde2be3d69`。
- 修正 shadow runner receipt `a31cb6e3810fdf39b8a85c047d4579d6ca66b036c9c237a949dee9a47586a6e5`；episode receipt `474ac041805e6c68a7405cf957320243535846eeeb1344ff32fa313be880b752`；v2 validation `a1625cd5048bbc9be1a2569a490ce116932258bc174ea93355c48af686c92ac6`。
- v2 analyzer `tools/analyze_fixed_shadow_pair_v2.py`：`fb62a01b35c460b18bd9357dae9a96ae55b53ce46b8b83ad2357ea75cdc52d4b`；analysis JSON `be1382272b3cbae2454b17e3bcedaf2656c6693da88fffdfccbde3bf6473c5c7`；Markdown `14d0e508b787019dcbcd4e05519ac223a6117b3fac1e1b7f9868ce666cdb5cfa`。用临时输出重跑后，三份 v2 输出逐字节 hash 均一致。


## 历史：原入口首 query 准备（当时仅 CPU，尚未执行）

已在任务私有目录准备保持原 `BenchmarkRunner` 启动、metadata、reset/preflight 和首 query 路线的有界诊断入口：[runner](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/original_entry_first_query_runner.py)（SHA-256 `376dd1fd087a5e79a9cbda4e83d1ff5b8534dc9c59429a60acbdf8ed2a0abf34`）仅替换其生成的 scheduler child；[scheduler](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/original_entry_first_query_scheduler.py)（`0561e295e644bee882c7abaee9d08e856b9e5ad00aeafbb4ed480ad7f3179ae2`）在首个同步 RPC 返回后才于 RAM 深拷贝完整 request/response，并在原 `run_iteration()`、`after_execute`、clear 和无 drain status 后写入收据。完整行为、边界和 8 MiB 单数组上限见[说明](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/original_entry_first_query.md)（`c11656f94b8d2ef043964465d8ecca9a0d83575fc7ff25bf1c5e3499f2d9d6db`）。

[CPU seam tests](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/test_original_entry_first_query.py)（`3f9653c70525febdf2b7167696539cc9e3c535f728974bef214dd48bdf756a5c`）当前复跑为 `11 passed`，并通过 Python 编译；覆盖一次 infer 上限、post-send ambiguity 不重试、预检拒绝不进入 seed `100001`、execute 后 clear/status 顺序和诊断 child 的 episode-0 failure leaf。默认 launcher 只打印计划，未执行 `--execute`，因此本次准备没有启动 GPU、正常 policy server、真实 reset、replay、warmup 或完整轨迹，也没有消耗剩余 action samples。

该捕获是 `WebSocketClient.call()` 返回后的对象观察，不能称作原始 wire bytes；真实 PRNG key 仍不可得。任何诊断 receipt 都是独立失败/有界收据，不能用作 matching smoke 或 formal 成功证据；当前正式评测仍暂停，生产源码树保持只读。

## 当前增量修复

已按 Manager 对复审 `27b16d899cf0220986a7531ad04989b227270f61` 的裁决，完成 rolling evidence 的 formal 准入链窄修；未改算法、默认 baseline、OpenPI、P0 logger、训练或运行中的 C 环境。

- RMBench 增加单一 `check_rolling_evidence()`：仅当 bridge 从已解析的显式 rolling/matched 配置传入 `rolling_evidence_required: true` 时，逐 episode 校验 artifact 文件、JSONL、schema v1、header `episode_id`/`seed`、最终 `episode_finished`、`evidence_complete: true` 以及无 `truncated`。
- `validate_smoke_run()` 复用该检查。缺引用、缺文件、坏 JSONL、身份错、无终态、`truncated` 或 `complete=false` 均拒绝 matching smoke；普通 baseline 不要求 evidence。
- bridge 将这一“是否需要”的配置事实传给 formal gate，并在每个显式协议 episode 收尾调用同一检查。正常 child 退出但 artifact 缺终态或不完整时，episode 记为 evidence/infrastructure failure，正式 run 不会把它当作正常完整结果或拼接 partial。
- 未创建文件时 episode record 不再留下普通 `rolling_evidence_path`；以 `rolling_evidence.state: missing` 或 `unavailable` 保存。已写部分文件保留其路径并标记 `incomplete`/`invalid`；已有 scheduler failure reason 与 error message 原样保留。
- 更新 [rolling evidence 文档](/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge/docs/reference/rolling-evidence.md)，说明 matching smoke/formal 的同一完整性合同。

上一轮已修复的真实 recorder path/reference、child header identity 和单次 benchmark reset 仍保留：`RMBenchResultRecorder` 按 episode 分配 `rolling_evidence/episodeN.jsonl`，显式 child 只接收审计 identity，不会据此发起第二次环境 reset。

## 验证

- RMBench recorder/validator CPU 回归：
  `.venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`
  → `5 passed`（既有 SAPIEN/Vulkan 资源警告，无测试失败）。
  - 使用实际 recorder 留存 normal、terminal、scheduler error 的 evidence 状态。
  - matching gate 接受完整 artifact，拒绝缺引用、缺文件、坏 JSONL、身份错、无终态、truncated 和 `evidence_complete=false`。
- bridge lifecycle CPU 回归：
  `PYTHONPATH=/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi/packages/openpi-client/src .venv/bin/pytest tests/benchmark/test_stage3.py tests/benchmark/test_runner.py -q`
  → `26 passed`。
  - 真实 RMBench recorder + child 覆盖 writer 前直接失败、writer 后异常、正常完整、default 无 evidence；保留每 smoke episode 一次 reset。
  - formal-mode CPU fixture 覆盖 child 正常退出但 evidence 无最终记录时，runner 以 `accepted_infrastructure_failure` 拒绝并把 episode 写为 Fail。
- bridge 全量 CPU 回归：同一 `PYTHONPATH` 下 `.venv/bin/pytest -q` → `524 passed, 2 skipped`。
- bridge 变更文件通过 Ruff、Python 编译与 `git diff --check`；RMBench 变更文件通过 Python 编译与 `git diff --check`。

## 精确提交与基线

- OpenPI（本轮未改）：`0ce566bd34f99cb4775422f012ab67c16aa53885`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi`
- robot-bridge：上一候选 `552ea78f73e62fddc747d5d26e7e6c365fa00339` 之上的当前候选
  `ffa122494c19e1c0154e877010f7b470967ccfc6` (`fix: enforce rolling evidence at benchmark close`)
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge`
- RMBench：正式 `f401f5279c95451eb424ac98b831bab5552b2120`，上一候选 `c99ec6a2c6df96ec8705b106b125935fce862052` 之上的当前候选
  `6abebf08d084d0be43aa56ebe158dc8395fa58e4`（`验证 rolling evidence 的 smoke 完整性`）
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/RMBench`
  - 已核对 `2e9677c..f401f52` 仅是 `memory_schema_eval.yaml` 的 17 行 N/S 配置新增，当前 candidate 保留完整 f401 祖先。

三个 worktree 均 clean；没有登记中的本任务 job。

## 首 query 有界诊断（C3 GPU0）

本轮仅诊断 `put_back_block`、train seed 0、环境 seed `100000` 的 matched baseline/shadow 首个真实 policy query；冻结运行树只读，未改生产源码、checkpoint、共享 cache、阈值或算法。冻结根为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 分别为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`；checkpoint 为 `pi05_rmbench_put_back_block_full_t_plus_1/.../20000`。实际导入的 `openpi/policies/policy.py`、OpenPi backend 和 simulation scheduler SHA-256 分别为 `1c4636db0e5fb97a8e5a4332de047d79d9ad5c63ea6880179d7606b41fa65563`、`a49f45fe5923723afc8982be2ff88d8b483c8bd6aba225838d4c92c7cad7ce5c`、`c6f9eeb9442153f5231b5a1be268ad1f1f04dfe83626caddf68b517839c0ca5b`。

- 真实入口分别为 `matched_baseline._call_policy_infer` 和 `shadow._call_rolling_action_infer`。两者的 scheduler pre-RPC 完整输入树（3 张 RGB、state、memory IDs、prompt）相同，SHA-256 为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`；Policy transform 后树为 `df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`。
- 实际 action RNG 完全一致：split 前 `[0, 0]`，采样 key `[928981903, 3453687069]`，split 后 `[1797259609, 2579123966]`。`implicit_noise_derived_from_sampling_key`、raw model H50、post-transform H50、实际 queued K30 的树哈希依次为 `127e5ee9a8777cfb6f05401c832f45f422efffe52a27bbf0b7b77396e9619c80`、`035baf5219a0e838d404ab4ca56a82063fc64cf7dfd79a508e5317e77268f90d`、`baa84c42691b0aa0e87d0fdb55f4a7c96897ac2a8e19dd45004bcd5e8fb9a096`、`cdcbecf0e6339267b95eccd58529ab6f076adf845d86410f7021661dd6a8e491`，baseline/shadow 均相等。前者是用捕获到的真实 sampling key 按冻结 `jax.random.normal` 表达式离线重建，不是 GPU sampler 内部 noise 的直接捕获。
- 每侧一次真实 action query 加两次同输入/同 key replay，共消耗 `6 / 8` 个正常 action samples。以冻结 backend 的 wire cast `np.asarray(actions, dtype=np.float32)` 比较后，所有 H50 replay、跨入口 replay 和 H50 前 30 行对实际 K30 都为逐元素相等；两个队列均在逻辑步 0 立即清除 `30` 行，未执行轨迹动作。两个保留的失败目录均发生在 query 前，未计入样本。
- Policy transform 的原始 action 是 float64，而 frozen OpenPI backend 在线路上转为 float32；直接比较 pre-cast 值仅有该转换舍入（最大绝对差约 `5.93e-08`），不是推理差异。

结论：这一受控的新首 query 样本没有发现输入、transform、捕获到的真实 PRNG key、离线重建 noise、模型输出、队列或固定输入/key GPU replay 的分歧，因此不支持把历史不一致简单归因为 policy sampling 非确定性。它不撤销既有历史动作前 30×14 不一致审计（离线 queued-action 审计工具 SHA `1be44b9bd3cd02235833707e40022d0690361efae60b131dcbeb287daeb02151`，重算 SHA `bc30cf2ee8bfe7130cc68c1f8eff2862928e5baee1564b6841ffb29d0187d1fb`）：新捕获只说明该次重建的首 query 未复现差异。诊断 wrapper 在 transform 周围做同步 host copy/`fsync`，并暂时 monkey-patch 全局 `jax.random.split`；它保持预期的随机调用语义，但改变了 timing/JIT 条件，所以新样本相等也不能排除未插桩运行时的 timing/numerical effect。仍未确认的条件包括先前 run 的初始环境/完整输入状态或其他生命周期差异；现有证据不支持生产修复或解除正式评测暂停。

证据位于 C3 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic`：[`analysis.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.md) 与 [`analysis.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.json)，后者 SHA-256 为 `c14af95aac92df5cefbfd3958de0100f1efef780d28a7031e8f59435a4500db1`。诊断分析器 SHA-256 为 `71952d10f8050689fe57143448ad5162e12c0edc9a015d68a1006db9d9f02912`；调度 wrapper 记录了上述插入点，SHA-256 为 `318ac87ca3f7b963aff059a101f6c78cfa860735b28b04450b9beaf005050c4f`。

## 离线历史首 query 对齐

未增加 GPU 采样、reset、replay、完整轨迹或生产源码改动。任务私有离线读取器 [`align_historical_first_query.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/align_historical_first_query.py) 以冻结 wire 合同 `np.asarray(actions, dtype=np.float32)`（`openpi.py:349-356`）读取旧 put-back matched artifacts 和新有界 capture；读取器 SHA-256 `94b3a1cbc209b0b1c58f670a74b0a61f4c2a9940a1f2a4fef7c88530dc7b5d58`。结果为 [`historical_alignment.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.json)（`4de3f6edc1af02fec61015439393f5d287da70bea0dd55732a0bf91c35ca2b1b`）和 [`historical_alignment.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.md)（`ffa48e8682d927b544b56664a117861afef1607dd9a0697e425b4394d5231bd6`）。

- 新 H50 的 wire SHA 为 `adf97a1dadeee7df55ab60d7bfe54f9d141cffd7b15c13dd114a222306a2d68a`，K30 为 `f0dcb3163e0723c363e9477faa873a499baba78e4bbba7a2ef7188724ac25fa4`。旧 baseline 的两集 H50 完全相同（SHA `4c69052f6e46e601de388993f3cb1ddc108617e8ded37230cdb758f21b854431`）；旧 shadow 只留第一 `action_plan.queued_actions` K30、两集也相同（SHA `0799a79aea6a7d860b7859f2a7ce988d1b3229f3b6ac2e6b0389cbbc4d405a40`），没有可回溯的 shadow H50 tail。
- 新 H50 对旧 baseline H50 有 `511/700` 个 float32 元素不同，max abs `0.0034926608204841614`、RMSE `0.0006454789071132261`，首差 `[0,0]` 为新 `-1.459865779906977e-05`、旧 `0.00032710886443965137`。新 K30 对旧 baseline H50 前缀为 `296/420`、max `0.0027747450512833893`、RMSE `0.0005912740981828194`；对旧 shadow K30 为 `301/420`、max `0.003492661053314805`、RMSE `0.000688904451176663`。历史 baseline 前缀对 shadow K30 仍为 `299/420` 个不同。新 K30 的 164 个元素同时不同于两边，其余类别也不组成任一旧数组，因此新 capture 精确等于旧 baseline 和旧 shadow 的结论均为 false。
- reset request 仅去掉 run-specific `video.output_path` 后完全相同（canonical SHA `789feb2835dae80d4415c21141594e8b913153374f2a8df9b0b714d160c1679d`）：`task_overrides={}`、`instruction_type=unseen`、`test_num=100`。instruction 精确相同（SHA `8537a6997ea8ad918e3237b6642490ded7c9204d9bd78075b1d6a88ec46f81bf`）；去掉 `eval_video_save_dir` 后 preflight task args 和相机配置也相同。旧/新保存的 `memory_input_ids=[0,0]`、state 均相同（int32/float32 raw SHA 分别为 `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc`、`aed9607efe0f26286bd388129c3f8720abc4de43b417ae34e0a12dfec2d25747`）。
- 这只证明配置与已留存字段相同：旧 rolling evidence 首 query 输入只有 state/memory，未保存 RGB、完整 prompt/token/transform tree、实际 PRNG key、sampler-internal noise；旧 shadow 也未保存 H50 tail。新 baseline/shadow 的 scheduler pre-RPC tree（含 3 张 RGB）和 post-transform tree 分别同为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`、`df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`，但这不能倒推旧全输入或旧真实随机状态相同。`episode_info.info.task_facts.final_block_pose` 也不能当作首 query 输入身份：`rmbench_sim_worker.py:135-149` 的 probe env 会 `play_once()`，`put_back_block.py:106-140` 随后记录该 pose，而 worker 在 `:155-179` 重建实际 episode env 后仍返回前者。
- 已确认入口差异：旧 `BenchmarkRunner.run` 在 metadata handshake 前连续启动 robot/policy（`runner.py:750-771`）；新 launcher 先启动并握手 robot，后启动 policy（`run_first_query_diagnostic.py:355-379`）。旧流程是正常 `run_policy_server.py`/`scripts/run_scheduler.py`，新流程是 task-private policy/scheduler wrapper，并新增 JAX/WARP/CUDA cache 路径（旧 receipt 未保存其值）。新 scheduler 仍加载相同 config、调用冻结 `apply_episode_prompt`，再 `_startup(); run_iteration()`；这与 `SchedulerBase.run()` 的名义首 action route（`base.py:614-648`）在构造后相同，但不能抹去 wrapper 或启动顺序差异。
- 建议但未执行的最后两样本方案：baseline、shadow 各一次，保留旧 `BenchmarkRunner` 的启动顺序与 reset flow；只在真实 execute request 之后的 scheduler 侧采集 post-wire K30，并在 logical step 0 clear queue。不得包装 `Policy.infer`、transform 或 `jax.random.split`。这样可区分差异是否由本次 diagnostic wrapper/startup path 引入；若未获授权额外观测，仍不能回建旧 RGB/实际 key。

## 原入口有界首 query 执行（C3 GPU0，2026-09-14）

Manager 授权的后续执行只使用了 matched baseline 的 **1** 次真实 action request；matched shadow 在来源校验阶段停止，使用 **0** 次。冻结运行树为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。结果 leaf 为 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910_hf_engineering/c_hf_j_matched_baseline_original_entry_first_query_env100000`；MAM job `ff3b2531-1b01-4685-b5d8-f23037d63253` 已归档。外层 exit `70` 是预期的诊断截停，保留了 episode-0 failure leaf，不能视为 benchmark 成功。

baseline 的实际 policy 身份不是仅由外层环境变量推断。结果 `config.yaml:750` 记录了 policy `get_metadata.policy_dir` 为 `/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000`；冻结 `BenchmarkRunner` 将 policy `get_metadata` RPC 返回值保存为 `run_context["policy_metadata"]`，拒绝与 manifest-resolved checkpoint 不同的 `policy_dir`，再写入 result config。该 config 的 `metadata_verification.actual_path`（行 442）和 `checkpoint_verification.actual_path`（行 535）分别解析到该目录的 metadata 与 checkpoint，校验 digest 分别为 `3b5d9b56a6d9abcaad95c6fc4824b2cd4e2b80bfc5d59ef7380f0d12f08622a4`、`d29535bfbe13776d3f006639b450cb85701647772414034fd01484838da940de`。policy stdout 还直接记录从该 checkpoint 加载 train metadata、恢复 `params`、并从 `assets/rmbench_put_back_block_robot` 加载 norm stats。

任务私有离线提取器 [`extract_baseline_identity.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/tools/extract_baseline_identity.py)（SHA-256 `f0640fadfd6be64fb6007ab4e7b490174c2172cc5862ea36cc9e1e04973593e1`）重读 runner、policy server、backend、recorder、launch、manifest、result config 和 policy log，输出 [`baseline_identity.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/analysis/baseline_identity.json)（`25f89ee7c4f8ba56e2976f8e4657b66af95df3c2a54e462800e065df916269e9`）。其 baseline 身份链检查全部为真。baseline 的 `MemoryCheckpoint` source-root 与旧 baseline command 一致，解析 `MemoryCheckpoint/20000/metadata` 存在；shadow 的 `--source-root MemoryCheckpoint=...` 少了 `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` 这一层，解析后的 checkpoint 和 metadata 都不存在。虽然 shadow launcher 的 `RB_OPENPI_POLICY_DIR` 值未被使用到，runner 在 metadata source 校验时即以 `InputNotReady: checkpoint_metadata` 停止：无 reset、policy startup、scheduler child、action RPC、result leaf 或 retry。

baseline scheduler receipt SHA-256 为 `f56e3438c911ce76232b9e69b0928b3860f2df8d5e03f607c3959b3ae8a4e252`，runner receipt 为 `d8988c7035fb3b554e1ed43d711eaf54a55835e37ac7ea4597d00ad9a1bdcfea`，验证摘要为 `b421a3b2f088043238fa6288e5bd968c9d023989206e77c797b0c837f86861ec`；shadow failure receipt 为 `64ee0c7c9f4e4d77a99e20af55ed830bc06b42455cbe820ca34e98ceb0a89d21`，其验证摘要为 `ee366342b9c58ebf36a2249f0e12404c021c321d2acc9ffcbc762fda5d9b8fbb`。baseline 完整保存 RGB/state/memory/prompt/request/response pickle，首个 `infer_audited` 与真实 execute 各一次；H50 为 float32 `50×14`、K30 为 float32 `30×14`，`queued=30`、`dropped=30`、`logical_step=0`。唯一 accepted reset 是 episode 0 / seed `100000` / `put_back_block`；无第二 inference、seed `100001`、replay、warmup 或 probe。事件顺序为 RPC 返回后的 RAM copy、原 `run_iteration`/`after_execute`、clear、无 drain status、持久化。

修正并重跑 [`analyze_original_entry_alignment.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/tools/analyze_original_entry_alignment.py)（`221f6e640dec1649f49f3153a799f72bb40aa63f2e57e02c613dc045a26540af`）后，provenance wording 与其实际 `source_root_matches_original=true` 一致。新 [`original_entry_alignment.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/analysis/original_entry_alignment.json)（`b96be2c03c9298785b767ad751037df9680a40178df920c9f6c8e6b816610530`）确认本次 H50 前 30 行与本次实际 K30 完全相等；与旧 baseline H50 有 `499/700` 个 float32 元素不同（max abs `0.004009723663330078`，RMSE `0.000707095339374057`），本次 K30 与旧 baseline H50 前缀有 `298/420` 个不同、与旧 shadow K30 有 `301/420` 个不同。它同时保留了旧 evidence 缺完整 RGB、完整 request、真实 PRNG key、wire bytes 和旧 shadow H50 的边界；因此不能从这一次有界、替换 scheduler child 且非终态的诊断得出历史差异的因果结论。

本节是有界诊断收据，从不构成 matching smoke 或 formal。shadow 不会自动重试；先前 6 个与本节 baseline 1 个正常 action samples 合计已使用 `7/8`，剩余 **1** 个未经 Manager 再授权不得使用。HF formal 继续冻结。

## 历史：修正 shadow 前的未执行项

此前的源码修复验证仍是 CPU-only；早先 C3 有界诊断已完成 6 次首 query 采样，本报告的“原入口有界首 query 执行”节另记录随后授权的 baseline 1 次真实 action request。未启动新的完整轨迹、matching smoke、formal 100、`r_s=30` 或 HF 效果试验，未训练、未改 checkpoint、未部署，也没有新增生产源码提交。累计已使用 `7/8` 个正常 action samples；剩余 1 个仅可在 Manager 对新的有界假设明确授权后使用。
