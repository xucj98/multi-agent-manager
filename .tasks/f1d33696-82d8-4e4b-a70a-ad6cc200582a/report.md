# HF 工程阶段剩余三叶的独立证据审查

审查源任务为 0acf5d43-91b6-4171-b727-e3fe0f7e7939，读取的最终已发布源报告 revision 为 f4be7d6e8aa2a970d92197e74d2984b1168a03f9。本审查只读；没有运行 GPU、模型、仿真、helper 或新测试，没有改动三库、运行时、checkpoint、阈值、seed、源报告或视频。

三个已结束叶子的已记录工程合同均未发现具体阻断。它们的 stage、trace、review、execution 及各 review 引用的八个结果原件均与声明 SHA-256 一致；两个已先完成叶子的 rolling JSONL 已独立重算，最终 rearrange event 叶子也在本审查中按原始 JSONL 重算完成。最终叶子的 source job def61eba-a703-480b-b431-eae84eb80ee1 已归档。

| leaf | 两集原始轨迹重算 | 独立结论与未来候选边界 |
| --- | --- | --- |
| c_hf_j_hf_event_put_back_trainseed0_evalseed0_smoke2 | 两集均 seed 100000/100001、334 completed rows、12 ordinary action、55 probe、66 consumption；末计划的 26 行是 terminal discard。唯一高偏差在 u=125、reference=120、d=5、3/3 mismatch、streak=1。 | 可保留为 HF-event 的工程 / matching-smoke 候选；未达到 min-prefix 且不连续，因此没有真实 trigger、clear 或 normal replan 覆盖。 |
| c_hf_j_hf_fixed_rearrange_trainseed0_evalseed0_smoke2 | episode 0/1 分别为 392/402 completed rows、14 action、65/67 probe、78/80 consumption；terminal discard 为 28/18。 | 可保留为 HF-fixed 的工程 / matching-smoke 候选。fixed 模式不启用 event replan，且没有 clear 或 ordinary-action replan。 |
| c_hf_j_hf_event_rearrange_trainseed0_evalseed0_smoke2 | episode 0/1 分别为 392/404 completed rows、14 action、65/67 probe、78/80 consumption；terminal discard 为 28/16。 | 可保留为 HF-event 的工程 / matching-smoke 候选；高偏差仅为 u=230、reference=210、d=20、2/3 和 u=255、reference=240、d=15、3/3，均 streak=1，未观察到 trigger→clear→normal replan。 |

所有复算都以 source_step + completed_rows、forecast consumption.current_step 和 episode_status 重建时刻，不把滞后一轮的顶层 logical_step 当作观测时刻。每个 action plan 均为 queued K=30、14 维执行动作，保存的 state forecast 有 50 行；probe 位于完成后的 +5/+10/+15/+20/+25，未在 K30 边界或 terminal 后执行。每条 consumption 的 model_index、绝对 target、selected IDs，以及 probe 和下一 normal action 的 memory 输入都能回链至正确 forecast。phase comparison 按 checkpoint field order 的 phase 第 0 列、旧 action-plan reference 的 d:d+3 与新 probe 的 0:3 重算。

最终 rearrange event 叶子额外直接验证了 22 个哈希标签：stage、trace、review、execution、两份 raw JSONL，以及 review 和 trace 所引用的两组八份结果原件。两个 episode 的 event_index 连续；action/probe wire call 分别为 1–14 与 1–65/67；132 条 comparison、158 条 consumption、132 条 probe 输入连接和 26 条后续 normal-action 输入连接全部成立。两个 terminal suffix 与 clear 明确分开，原始记录中没有 plan_triggered 或 clear 事件。

冻结 C3 runtime 的 helper SHA-256 为 dcf93891de82adaf21e676c55ee30901309f9c9a6097841ff4be4c7ba7f29c87。三库均为 clean，HEAD 分别为 OpenPI 0ce566bd34f99cb4775422f012ab67c16aa53885、robot-bridge ffa122494c19e1c0154e877010f7b470967ccfc6、RMBench 6abebf08d084d0be43aa56ebe158dc8395fa58e4。checkpoint 身份与任务相符：put-back 使用 pi05_rmbench_put_back_block_full_t_plus_1/.../memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000；两个 rearrange 叶子使用 pi05_rmbench_rearrange_blocks_full_t_plus_1/.../memory20k_e7e5ac54_rearrange_full_t_plus_1_s0/20000。保存的训练配置为 train seed 0、20,000 steps、action horizon 50；运行合同为 monitor interval 5、maximum K 30、random_light=false、crazy_random_light_rate=0。

我也只读审阅了冻结 bridge 的实现和既有 CPU 证据。robot_bridge/scheduler/openpi_simulation.py 中的 _rolling_probe（1366）、_rolling_start_plan（1613）、_rolling_trigger_replan（1757）和 _run_rolling_iteration_impl（1807）按所述顺序比较、只 clear 当前未执行 suffix、再经 normal action infer 重规划。tests/scheduler/test_openpi_rolling.py 的 test_hf_event_clears_only_the_current_suffix_then_never_completes_that_old_forecast（546）及 test_rolling_evidence_survives_scheduler_exit_with_trigger_discard_and_terminal_prefix（586）覆盖人工触发、clear suffix、旧 forecast 不回写和 terminal evidence。源任务报告的 26 项 lifecycle CPU 回归及 524 passed、2 skipped 全量 bridge CPU 回归未由本审查重新运行。

这些 CPU fixture 使用 fake robot/policy，不能代替真实环境的自然触发、get_obs/渲染副作用或算法效果验证。两条 event 轨迹都没有触发，因此 CPU fixture 只能支持代码路径的有限证据，不能把现场 clear→replan 写成已通过。保存的 action/probe stream 与 call 是 wire 可见元数据，不是内部 sampler PRNG key；视频仅依赖已哈希的 owner video-check 原件，未在本审查中重解码。

因此，本报告不作 formal 准入、科学效果、环境完全等价或论文结论。Manager 仍需单独决定 matching-smoke 的准入定义，并为 HF-event 的真实 trigger→clear→normal replan 路径决定是否需要有界的补充证据。机器可读明细见 receipt.json。
