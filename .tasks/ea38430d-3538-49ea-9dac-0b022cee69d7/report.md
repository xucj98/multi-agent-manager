
# 只读交接审计：RMBench 最新正式结果与 HF 对照

审计日期：2026-09-21。执行 workspace：`/mnt/public/xcj/Projects/workspace/ea38430d-3538-49ea-9dac-0b022cee69d7/RMBench`；branch `task/ea38430d-3538-49ea-9dac-0b022cee69d7`；基线 commit `eb0546a04c857f2ad325d0dc322211ff1f82c393`。worktree 保持 clean，未修改代码、旧任务、共享结果或运行进程；未启动训练/评测。

## 证据边界

我先阅读了本仓库 `AGENTS.md`、`docs/guidelines/experiments.md`、`docs/guidelines/rmbench.md`，并按任务要求建立独立 worktree。原始结果只读检查了 C1/C2/C3 共享路径：

`/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/`

Manager 的独立重算交付（本报告使用但未改写）位于：

`/root/Documents/task-state-vla-paper/docs/handoff/20260921/`

关键收据 SHA-256：

- `manager_hf_raw_recomputation.json`: `3954a9552a414223c1ffc3d8d650f93a97604beec796224d9bd3568336557589`
- `manager_wave1_raw_recomputation.jsonl`: `0f2f69c8aaaaa5f2467abaa7289b0509bbc31f9f5800dd8db43c88c2d4f86725`
- `manager_hf_preflight_comparison.json`: `a6baa1e61624eedeb303a1920629adad05dc53c9dbed414806f4526df0f20f79`
- `manager_hf_first_actions.json`: `0b7142e4eaf8eb0946f28e44b19d698cf8d6766ea0e86cc2952ef86e78fb2e6f`

Manager 的 HF JSON 明确写明范围是 outcome/seed/preflight identity 的只读重算，不替代完整 source/video/rolling acceptance。下面把已核验事实与解释限制分开记录。

## 9 月 15 日后的新 wave1 原协议结果

四个远端 formal leaf 都有 `benchmark.status=completed`、`error=null`、100 条 terminal episode；结果来自 `diagnostics_summary.json` 和 `episode_diagnostics.jsonl` 的原始重算。`accepted` 是 preflight 通过数；拒绝的 seed 不进入 100 episode 分母。

| arm / leaf | accepted seeds | rejected preflights | success | 主要失败 | 状态 |
| --- | --- | ---: | ---: | --- | --- |
| swap N / `c_wave1_swap_blocks_n_trainseed0_evalseed0_100ep_r3` | `100001..100182`（100 个） | 83 | **14/100** | `unspecified_failure` 86 | 完成，正常任务失败 |
| swap J / `c_wave1_swap_blocks_j_trainseed0_evalseed0_100ep_r1` | `100001..100185`（100 个） | 86 | **90/100** | `unspecified_failure` 10 | 完成，正常任务失败 |
| battery N / `c_wave1_battery_try_n_trainseed0_evalseed0_100ep_r1` | `100004..100259`（100 个） | 160 | **23/100** | `unspecified_failure` 77 | 完成，正常任务失败 |
| cover N / `c_wave1_cover_blocks_n_trainseed0_evalseed0_100ep_r2` | `100000..100099`（100 个） | 0 | **0/100** | `unspecified_failure` 100 | 完成，正常任务失败 |

每个 leaf 的 `episode_diagnostics.jsonl` 均有 100 个 unique `episode_id=0..99` 和 100 个 terminal records；summary success 与逐集 success 一致。wave1 N/J 不是同一 accepted seed cohort：swap N/J 的 accepted seed 交集为 99/100（J 多出的末端 seed 与 N 的拒绝位置不同），不能做逐 seed 完全配对。battery 的大量 preflight rejection 也意味着不要从目录 seed 范围推断连续 100 集。

这些是 **原协议** `demo_clean_eval`、train seed 0、eval seed 0、H50/K30、fresh policy server continuous action RNG 的结果；不含 HF episode-reset、probe 或 event replan。matching smoke 不计入成绩。owner 任务报告与新目录分别为：

- `.tasks/f3488141-90fd-4d2c-8998-934614d1b098/report.md`（wave1 N/J 队列；其中旧报告仍有运行中快照，不能替代上述已完成 leaf 的终态复算）；
- `.tasks/39bdb4b8-1f64-4e9c-9f87-8fedf213db93/report.md`（cover N 的完整 owner 验收，包含 formal leaf、100/100 accepted、0/100 success 与 job 收尾）。

`mam job list` 中 swap J 和 battery N 曾显示 `stopped`；本审计没有把 stopped 状态当成成功，而是以结果目录的终态 JSON/summary 为准。

## HF 三臂正式结果

Manager 独立重算覆盖 rearrange 与 put-back 各三臂（matched baseline、HF-fixed、HF-event）× eval seed 0/1/2，共 18 个 100-episode leaf。每个 leaf 都有 100 条 accepted preflight、100 条 terminal episode，summary `completed/error=null`。成功数如下：

| task | matched baseline | HF-fixed | HF-event | 合计说明 |
| --- | ---: | ---: | ---: | --- |
| rearrange | 86 / 81 / 87 | 90 / 91 / 87 | 84 / 88 / 86 | eval0/1/2；各臂 300 集 |
| put-back | 100 / 73 / 61 | 49 / 100 / 82 | 100 / 77 / 100 | eval0/1/2；各臂 300 集 |

按三 eval 合计，rearrange 为 baseline **254/300**、fixed **268/300**、event **258/300**；put-back 为 baseline **234/300**、fixed **231/300**、event **277/300**。这些是描述性结果，不应跨原协议 52 批、旧 30k、20k 新模型或 episode-reset HF 混表，也不能把 put-back 的 300 行当成 300 个独立初始条件（见下一节）。

HF result leaf 命名和原始证据：

`c_hf_j_{matched_baseline,hf_fixed,hf_event}_{rearrange,put_back}_trainseed0_evalseed{0,1,2}_100ep`

每个 HF leaf 的 `rolling_evidence/episode*.jsonl` 已存在；我直接检查了 schema/event 计数。示例：rearrange eval0 fixed 为 1,462 action plans、7,029 probes、8,391 progress/consumption records、100/100 `evidence_complete`; event 为 1,613 plans、7,413 probes、154 trigger records、100/100 complete。put-back eval0 event 为 1,248 plans、6,004 probes、20 trigger records、100/100 complete。HF event trigger 原因记录为冻结的 `phase_window_mismatch_two_of_three_twice`，并记录 clear dropped rows；这证明事件证据存在，但不单独证明科学收益。

## 关键配对限制：put-back 的初始条件塌缩

从 Manager `manager_hf_raw_recomputation.json` 的每集 `diagnostics.task_context`、success 和 `episode_status.logical_step` 复算，put-back 每个 mode/eval 只有四个 `origin_mat` cluster，且同一 cluster 内 outcome 与 episode length 完全恒定。例：

- eval0 baseline：right 20 集 `(success,322)`、back 32 集 `(success,357)`、left 17 集 `(success,361)`、front 31 集 `(success,382)`；
- eval0 fixed：right/front 为 `(fail,500)`，back/left 为 `(success,422/343)`；
- eval0 event：四 cluster 均成功，长度为 `323/359/361/382`。

eval1/2 同样各为四 cluster；所有 mode 在对应 eval 的 cluster 计数相同。这只能说明每个 eval 有四个已观察到的 `origin_mat` 行为分组，且组内 outcome/length 有重复；首动作、结果和步数的重复并不证明完整 RGB、物理初态或全轨迹只有四类，也不能据此计算有效独立样本量或推出最多 12 个独立初始条件。普通独立 Bernoulli 置信区间和按 300 集强调显著性不应直接套用，应考虑组内依赖并报告分组敏感性。Manager 的 pairs 表（如 fixed vs baseline `48/51`、event vs baseline `66/23`）可作为逐 seed 行迁移描述，但不能用作独立样本因果证据。

进一步的 `manager_hf_preflight_comparison.json` 显示 HF 同一 task/eval 各臂 `origin_mat` 和 `initial_block_pose` **100/100 完全相同**；跨臂差异集中在 provenance 的 `final_block_pose`（末态）。因此不能把 HF preflight 差异解释为初始场景重新随机化。`manager_hf_first_actions.json` 的首动作比较还显示：eval0 event 与 baseline 的 first 30 actions 相同 100/100，但 fixed 与 baseline 全部不同；eval1/2 各模式首动作均有差异（最大绝对差约 0.0035–0.00524）。这支持先审计 action/RNG/协议差异，再谨慎解释成功率，不把结果直接归因于 probe 看到的新状态。

## 已验收与待验收边界

已具备最强原始证据的是：四个 wave1 eval0 leaf 的 terminal/seed/summary 复算；HF 18 leaf 的 outcome/seed/preflight/rolling 文件存在性与计数；9 月 14–15 日已有独立 reviewer 报告的 rearrange matched baseline 与 rearrange fixed formal 证据。相关独立 reviewer reports 包括 `.tasks/8274a212-a7de-42af-8b6d-e5cd2670f3d2/report.md` 与 `.tasks/93858e54-40e7-4e1a-ab86-ccf9039ab86f/report.md`。put-back HF-event 的 `.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/report.md` 是 owner 终态审计/验收材料，不是独立 review；本报告也没有完成全部 source/video/rolling 的独立终验。

本任务没有重新解码全部 MP4、没有重哈希多 GB checkpoint params/assets、没有修改共享论文或结果、没有启动新任务。wave1 的 battery/swap owner 报告仍可能保留历史“运行中”快照；终态判断应继续以各 leaf 的 JSON/summary 和后续独立验收为准。新任务 `observe_and_pickup`、`swap_T`、`press_button`、`blocks_ranking_try` 的 J/S schema 审计在 `.tasks/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/report.md` 中明确为 BLOCKED；该任务的 N checkpoint/训练状态不应被误报为 J/S 已可评。

## 建议给 Manager

1. 主结果表保留四个 wave1 原协议结果，但把 accepted seed range、rejected preflight 数和 N/J 非完全配对写入表注释。
2. HF 表按 task × eval seed 展示三臂 success，同时追加 put-back 的四 cluster 结构；不要把 300 行当成 300 个独立随机场景。
3. 在作 HF 机制解释前，先处理首 action 差异与 fixed/event 的 RNG/输入生命周期；至少将“部署协议整体差异”与“中间 probe 的额外信息”分开表述。
4. 继续把 old 30k、new 20k、episode-reset HF、原协议 wave1 分成独立批次；smoke、stopped job、owner 预期目录不进入正式成功率。

## 交付状态

本报告写入 MAM 根 `.tasks/ea38430d-3538-49ea-9dac-0b022cee69d7/report.md`，没有源码 commit。下一步由 Manager 按上述边界决定哪些结果进入论文/主表，以及是否为 wave1 其余 eval seed 安排独立验收。
