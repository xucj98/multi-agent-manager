task_revision: f9c26e8d8675ec82dc116fb896335a75354120d3

## 完成与未完成

已完成：基于当前已发布实验计划、文献定位、旧稿与审阅意见完成英文论文文字草稿；只读了 paper 库，未修改业务库、未创建环境或 worktree、未启动训练/评测/占用 GPU，也未派发 agent。文本交付，未修改业务库。

未完成：确认性训练、三 seed 配对闭环评测及真机闭环尚在进行，因此草稿不报告或预设任何新结果；Manager 可在结果齐备后将此文字整合进论文库。

workspace、各库交付 commit：无业务库交付 commit；本任务仅发布本 report。

验证结果与成果位置：已逐项核对本任务发布要求及 paper 库的 README、当前实验计划、已核验文献定位、review.md、旧 Introduction 和 Method。英文正文草稿见下节。

主要证据入口：/root/Documents/task-state-vla-paper/README.md；docs/EXPERIMENT_PLAN_20260910.zh-CN.md；docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md；review.md；sections/01_introduction.tex；sections/03_method.tex。

引用限制：相关工作仅沿已核验定位使用 SAGE、action-chunking、TFP v3、SparkVLA 和 EventVLA 的方法层面区分；不新增“首次”、跨论文成本、效果或可比性声明，也不将其报告数字作为本研究基线。

## Paper-facing English Draft

### Suggested title

**When to Supervise and Consume Task Memory in Closed-Loop Action Chunking**

### Motivation and research question

Current-query robot policies can face the same local observation after different task histories while requiring different continuations. In structured procedures, the missing information can sometimes be represented by a small set of task variables, such as progress or a previously observed attribute. This paper studies a narrower empirical question than the construction of a new memory architecture: given the same low-dimensional task-memory content, how should its supervised time target and closed-loop feedback be coupled to an action chunk?

The contribution is an empirical account of that coupling. A common configuration schema fixes the semantic fields and records the target, conditioning, and feedback choices so that comparisons are reproducible. It is an analysis device, not a new finite-state controller or a claim that a low-dimensional representation is sufficient for every task. The motivating full-versus-serial observations remain capability comparisons because representation, action conditioning, and timing change together. The controlled claims instead come from the comparisons below.

### Time axis and design space

Let query n occur at environment time t_n. The policy receives the current observation and the memory available at that query, then predicts an action chunk of horizon H and one predicted memory row for each chunk position. Let K_n be the number of commands actually executed before the next query, so t_(n+1) = t_n + K_n. K_n is execution progress, not merely acceptance of a command by the controller. Let r_n denote the predicted row selected as feedback after that execution. The selected prediction becomes the next-query memory input; it is distinct from the memory that conditions the current action prediction.

For row j, training compares a ground-truth memory label at an explicit reference time, while deployment consumes a predicted row. Thus four time quantities must always be reported: query t_n, predicted horizon H, actual executed length K_n, and both the supervision reference time and selected feedback row r_n. A phase target can be written as phi*(t_n + g(j)), where g specifies the target construction. This notation prevents an off-by-one ambiguity: with one-based rows, consuming row 30 after K = 30 corresponds to the state at t_n + 30; implementation may index that row as j = 29.

The experimental design space separates memory content from protocol. The semantic fields S are held fixed within a controlled comparison. The protocol P specifies the representation and current-action condition, the target map g, loss mask and normalization, H, actual execution K, and feedback selection r. Sharing S does not make two protocols equivalent. Nor does a low-dimensional S imply that it is a sufficient statistic, spans every useful design, or reduces total training cost.

### Q2: the primary target-construction comparison

Q2 asks whether the same next-query phase requirement needs per-frame supervision. It compares two full one-hot models with the same shape, input, action targets, non-phase fields, loss mask and normalization, H, K = 30, and feedback consumption of row 30. The only changed phase target is phi*(t_n + j + 1) for the per-frame arm versus phi*(t_n + 30) for the repeated-endpoint arm. Both arms use the common validity mask requiring that both the row reference and the endpoint exist. The robot supervision and every other field remain unchanged.

Repeated endpoint labels do not require the model to output identical phase predictions at all rows. They define repeated supervision targets for independently predicted rows. Therefore both Q2 arms must consume row 30; changing the repeated-target arm to row 1, an average, or another row would change the intervention. The primary outcome is the paired difference in 100-episode closed-loop success, repeated for each independently trained seed. Row-30 phase error and boundary-stratified offline diagnostics explain possible outcome differences but do not substitute for the closed-loop outcome or establish a particular gradient mechanism.

### Q1 and Q3: paired diagnostics with bounded interpretations

Q1 diagnoses how a fixed per-frame full model is consumed. At fixed H and decoding, it crosses actual execution K in {20, 30, 50} with complete feedback rules that select row K or row K-10. This comparison estimates the effect of the feedback rule in combination with execution length. Selecting an earlier row changes both the semantic age of the state and the prediction lead time, and all memory fields are selected together. The resulting interaction should therefore be reported as a feedback-and-execution result, not as an isolated phase effect or a uniquely identified time-lag mechanism. Q1 does not establish that a repeated-endpoint model follows the same rule.

Q3 asks whether an additional semantic field interacts with the deployment protocol. Same-shape serial models use either the true button slot or a constant button slot; both keep the fixed training lag of 30 and are evaluated at K = 30 and K = 50. The estimand is the difference in the two content conditions across these two execution settings. It does not compare each K with a separately K-matched optimum: K = 50 also changes executed length and the distribution of feedback ages. A replication failure would indicate that earlier serial observations may have involved other jointly changed factors, rather than proving that button content has no value.

### Protocol, evidence, and presentation

All new controlled models use demo_clean_state, 20,000 training steps, batch size 32, and training seeds 0, 1, and 2. Each seed is evaluated on 100 rollouts using the matched initial-condition list for its comparison. The paper should show the three training-seed results separately, paired episode outcomes, paired differences with uncertainty, and the mean and range across seeds. Pooling the 300 rollouts into one model-level sample would erase training variation; an interval containing zero is inconclusive evidence rather than equivalence.

The wash-cup evidence uses the shared S2M/phase schema and all 172 eligible episodes for training. Its fixed five training-episode offline replay is an interface diagnostic only: offline prediction is neither a generalization measurement nor a real-robot success rate. The manuscript should state real-world closed-loop trial counts only after those trials are completed.

Figure 1 should introduce the question with an aliased current observation, the common memory content, and the query-to-feedback timeline. Figure 2 should isolate Q2: a single H-row chunk showing per-frame and repeated-endpoint labels, the shared mask, K = 30, and consumption of row 30. Figure 3 should present the paired Q2 closed-loop results with one point per training seed and a companion row-30/boundary diagnostic. Figure 4 should place Q1 and Q3 as explicitly labelled interactions, rather than as rankings of complete protocols. Table I should list S and the frozen P variables for every arm; Table II should report per-seed paired successes and uncertainty; a compact table or appendix panel can hold offline diagnostics and the fixed wash replay protocol.

Related work should position this study beside semantic state recurrence, chunk-execution analyses, time-aware latent belief updates, joint stopping/chunk selection, and event-timed visual memory. Those lines of work already make broad claims about recurrence, execution length, and time-aware memory inappropriate here. The paper's narrower question is whether a declared semantic state changes learning when only its target time is changed, and how its predicted rows should be consumed under a specified action-chunk protocol.

### Limitations

The study tests a finite set of categorical task memories, two simulation tasks for Q2, and the listed deployment protocols. A common low-dimensional schema makes the target-time intervention interpretable, but it does not establish sufficiency for rich history, continuous geometry, unbounded counts, or changing task vocabularies. Teacher-forced labels at training time and self-fed predictions at deployment can create persistent errors; paired state traces and closed-loop outcomes must reveal that exposure gap. The paper should report actual annotation, compute, and deployment costs before drawing any efficiency conclusion. Until the planned multi-seed evaluations and real-world closed-loop trials finish, this draft makes no directional performance claim.

## 中文裁决说明

未发现需要扩大实验清单的致命解释缺口。Q2的共同 mask、同形状、同输入和 row30 消费使主比较可解释；Q1已限定为反馈规则与执行长度的联合效应，Q3已限定为固定 lag30 训练下的内容与部署协议交互，均不作唯一时间机制或各 K 最优的宣称。
