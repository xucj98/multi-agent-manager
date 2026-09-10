task_revision: ceb75a56b94356f7e0b8e868ec47196344247771

## 完成与未完成

已完成：按 Manager 首轮裁定修订英文草稿，纠正 full/serial 输出、索引、数据来源及真机进度表述，明确 Q3 差异之差，精简叙述为三图一表并补齐既有文献原文链接。文本交付，未修改业务库。

待补证据：确认性新实验结果尚未齐备；真机闭环尚未安排设备执行，状态为待执行。正文保留无方向性的结果占位，不预设提升。

workspace、各库交付 commit：`/mnt/public/xcj/Projects/workspace/b7f0a7af-2ffa-4596-8b88-4967dfc633f6`；无业务库交付 commit，仅发布本 report。本轮未扩实验、修改代码、创建环境/worktree、占用 GPU 或派发 agent。

验证结果与成果位置：已逐项核对最新 task 的首轮裁定，并只读复核当前实验计划和已核验文献定位；英文草稿见下节。

主要文档（本任务累计读取）：[README](/root/Documents/task-state-vla-paper/README.md)、[当前实验计划](/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md)、[已核验文献定位](/root/Documents/task-state-vla-paper/docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md)、[旧稿审阅](/root/Documents/task-state-vla-paper/review.md)、[旧 Introduction](/root/Documents/task-state-vla-paper/sections/01_introduction.tex)、[旧 Method](/root/Documents/task-state-vla-paper/sections/03_method.tex)。

引用限制：下文五篇文献的名称、版本链接及方法事实均沿已核验定位文档，本轮未新增查新或复现。其报告数字不作为本研究的匹配基线；无首创、跨论文成本或效果声明。

## Paper-facing English Draft

### Suggested title

**Task Memory in Action-Chunked Policies: A Study of Supervision and Feedback**

### Motivation and research question

Visually similar scenes can require different actions because of task history. In structured procedures, progress or a previously observed attribute can provide useful memory for these decisions. Action chunking introduces a temporal choice: a policy predicts several commands at one query but may execute only a prefix before querying again. We study how the supervision and feedback of a fixed set of low-dimensional task-memory fields interact with this execution protocol.

The study centers on three empirical questions. Q2 tests phase-target construction under the same next-query consumption rule. Q1 examines feedback selection and execution length for a fixed model. Q3 tests the interaction of an additional semantic field with execution length under a fixed training protocol. A shared schema records field semantics and protocol choices for analysis and reproducibility.

[SAGE](https://arxiv.org/html/2509.19853v1) estimates stages from current observations and previous predictions, then conditions actions on stages. [Why Does Action Chunking Improve Behavioral Cloning Performance in Robotic Control?](https://arxiv.org/html/2608.02547v1) studies chunking through delayed policies and random-delay ensembles. [TFP v3](https://arxiv.org/html/2607.08283v3) studies continuous-time latent beliefs and measured query intervals; [SparkVLA](https://arxiv.org/html/2608.16172v1) jointly ranks subtask stopping and action-prefix length. [EventVLA](https://arxiv.org/html/2606.20092v1) predicts future keyframe probabilities and stores observed images when the corresponding steps execute. Our comparisons focus on the target times and consumption of supervised semantic memory within a shared backbone and dataset.

### Time axis and design space

Let query \(n\) occur at control-step index \(t_n\), with current observations and input memory \(m_n\). The policy predicts an action chunk of horizon \(H\). The full representation produces \(H\) memory rows, whereas serial produces one query state. Let \(K_n\) count commands actually executed before the next query, giving \(t_{n+1}=t_n+K_n\) in this discrete time axis. Controller acceptance alone does not establish execution; completed commands also do not certify an uncertain physical outcome.

For full, \(j\in\{0,\ldots,H-1\}\) is always a zero-based prediction index; the corresponding feedback row \(r=j+1\) is one-based. After execution, selecting row \(r_n\) supplies its decoded prediction to the next-query input \(m_{n+1}\). Serial feeds back its single query-state prediction. Next-query feedback and current-action conditioning are separate protocol choices: serial uses a query state to condition its current chunk, while the selected full output row is consumed at the next query.

Where labels are available, recurrent variants train with ground-truth input memory at the protocol's declared reference time and annotated targets; deployment uses initialized memory followed by recursive predictions. For full phase targets, write \(\phi^*(\tau_{n,j})\), where \(\tau_{n,j}\) identifies the supervision reference time. The recorded protocol includes \(t_n\), \(H\), \(K_n\), target reference times, feedback row \(r_n\) where applicable, and consumption time. Semantic fields \(S\) specify content; protocol \(P\) specifies input source, representation, action conditioning, targets, loss weighting, normalization, decoding, and feedback. The original full/serial comparison changes structure, conditioning, and timing together, so it measures complete-protocol capability despite shared field semantics.

### Q2: the primary target-construction comparison

Q2 compares per-frame and repeated-endpoint phase supervision on rearrange and put-back. Both full one-hot models have the same shape and inputs, \(H=50\), execution \(K=30\), and feedback \(r=30\). Only the phase target changes: \(\phi^*(t_n+j+1)\) versus \(\phi^*(t_n+30)\) at every output position. For an episode whose last observation index is \(L\), both arms apply the common phase mask \((t_n+j+1\le L)\land(t_n+30\le L)\), with fixed-\(H\) loss reduction. Loss weights, normalization, sample starts, robot supervision, and all other field targets and losses remain identical.

Repeated labels supervise distinct output positions and allow different predictions across rows. Both arms consume row \(r=30\), corresponding to \(j=29\); both consumed targets refer to \(t_n+30\). Reading another row or averaging predictions would alter this comparison. The primary outcome is repeated-endpoint minus per-frame closed-loop success. Row-30 classification error provides an explanatory diagnostic on fixed demonstration samples grouped by phase boundaries within \((0,30]\), only within \((30,50]\), or neither. These offline groups describe demonstration timing; their errors neither replace closed-loop success nor identify a unique gradient mechanism.

### Q1 and Q3: paired diagnostics with bounded interpretations

Q1 holds each per-frame full checkpoint, \(H=50\), and decoder fixed, crossing execution \(K\in\{20,30,50\}\) with feedback \(r=K\) or \(r=K-10\). All fields follow the same row-selection rule. The comparison estimates the interaction of the complete feedback rule with execution length: selecting an earlier row changes both semantic age at consumption and prediction lead time. It therefore leaves phase-specific causes and a unique time-lag mechanism unresolved, and its scope is per-frame models. Actual execution is recorded at each query; terminal episodes remain in the success denominator even when no subsequent feedback is consumed.

Q3 compares same-shape serial models with true button labels or a constant label in the same three-category slot. The constant applies to training inputs, targets, and current-action conditioning; deployment retains prediction and feedback. Training uses previous-state lag 30 in both arms, with evaluation at \(K=30\) and \(K=50\). For each training seed, let \(p_c(K)\) denote the success rate under content condition \(c\). The estimand is the difference-in-differences

\[
\Delta_{Q3}=[p_{\mathrm{true}}(50)-p_{\mathrm{constant}}(50)]
             -[p_{\mathrm{true}}(30)-p_{\mathrm{constant}}(30)].
\]

This measures content-condition by deployment-\(K\) interaction under fixed lag-30 training. At \(K=50\), execution length and feedback-age distribution change together; the comparison does not estimate optima from separately \(K\)-matched training. Interaction uncertainty is evaluated directly, rather than inferred from separate significance decisions at each \(K\).

### Protocol, evidence, and presentation

New training uses the same \(\pi_{0.5}\) base initialization, 20,000 steps, and batch size 32. Simulation training uses demo_clean_state. The confirmatory simulation protocol has training seeds 0, 1, and 2, each evaluated on 100 rollouts from matched initial-condition lists. Analysis retains each seed's success counts, discordant episode counts, and paired difference with uncertainty, alongside the mean and range across training seeds. Trajectories may diverge after initialization. The three models remain separate statistical units; an interval containing zero leaves the comparison unresolved rather than establishing equivalence.

The established controls retain a no-memory capability baseline and a full model with identical output supervision but memory inputs fixed to initial values in both training and deployment. The latter examines recurrent input together with its training distribution. Q3 remains the planned second stage after all twelve Q2 evaluations and timing checks, irrespective of their outcomes.

Wash-cup uses real-robot demonstrations: full and serial share the S2M/phase schema and train on all 172 eligible episodes. Phase denotes the current subtask and permits the observed order variations. Offline replay uses five fixed training episodes for an interface and prediction diagnostic. It measures neither held-out generalization nor real-robot task success. Physical closed-loop trials await execution.

[RESULTS PENDING: complete new multi-seed paired outcomes and timing verification.]

### Figure and table layout

The proposed layout contains three figures and one protocol table. Figure 1 combines the aliased-decision example and time axis, showing full versus serial outputs and Q2's two target sequences with their shared mask and row-30 consumption. Figure 2 holds the Q2 main results: per-seed paired success differences and uncertainty, success/discordance counts, and a companion boundary diagnostic with sample counts. Figure 3 contains separate Q1 and Q3 interaction panels, each with training-seed estimates. Table I records field semantics, data sources, and fixed or varied protocol choices. This assigns the main outcome evidence to Figure 2 without a duplicate results table.

### Limitations

The study covers categorical task memory, two simulation tasks for Q2, and the specified protocols. Field compactness alone establishes neither statistical sufficiency nor low training cost; annotation, compute, and deployment costs require measurement. The schema organizes implemented comparisons without establishing coverage of the full design space. Teacher forcing and recursive deployment can produce persistent errors, while offline state accuracy alone cannot quantify their closed-loop consequences. Conclusions remain conditional on tasks and protocols supported by completed experiments; physical closed-loop performance remains unmeasured.

## 中文裁决说明

首轮裁定已逐项落实：区分 full/serial 输出，统一 j/r 索引，去除输出独立性暗示，分开仿真与真机数据，真机闭环改为待执行；正文改为研究叙述，保留五篇既有文献链接及三图一表。Q3明确为固定 lag30 下的差异之差。未发现需扩大实验的致命解释缺口，未预写结果方向。
