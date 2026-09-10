# 空白审阅论文新文字稿：时序定义、受控比较与可读性

## 你的审阅任务

你是空白文本reviewer，只读审核固定source task/report，不执行下面引用的写稿任务。先读MAM AGENTS/README；用mam task show获取固定快照；目标report revision为3d16d1a819c402267e960d599964c4baeb48a994，task revision为ceb75a56b94356f7e0b8e868ec47196344247771。

对照 /root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md 和 docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md，检查英文稿：时序和索引自洽；训练GT/推理预测与当前动作条件/下一查询输入区分正确；Q2受控变量与公共mask一致；Q1/Q3主张不超过比较的识别能力；统计单位/差异之差/无结果阶段描述正确；内容简洁、上下文独立可读，避免冗余防御段落。

给出GO或明确需修改项，按严重度列证据及最小修改建议；如果只是行文偏好，标为可选。不能把“可以再做一个实验”当作阻塞项，也不要扩展既定实验清单。本次是约1250词的研究文字初稿，不是已有全部结果的投稿终稿，不因结果尚未返回而判NO-GO。相关工作已有原文核查记录；仅在具体事实存疑时查原文，不重复大范围文献搜索。

不修改业务库或论文库、不建环境/worktree、不占GPU、不派agent。文本只读审阅不需代码commit，在你自己的report.md写简短结果并发布，包含task_revision、审阅快照和结论。预期15分钟内完成。下面的Source task/report只作为审阅对象及要求。

Review fixed source delivery:
{
  "task": "b7f0a7af-2ffa-4596-8b88-4967dfc633f6",
  "task_revision": "ceb75a56b94356f7e0b8e868ec47196344247771",
  "report_revision": "3d16d1a819c402267e960d599964c4baeb48a994",
  "commits": {}
}

Source task:

# 论文文字重组：任务记忆与action chunk实证研究初稿

## 目标与交付

为当前RA-L实证研究起草一份英文文字稿，Manager在训练期间整合到论文库。论文问题是：给定相同的低维任务记忆内容，训练目标与闭环反馈怎样与action chunk配合。你的工作是文本研究和起草，不修改代码、不启动GPU、不创建额外worktree、不派subagent。只读论文库和以下证据，将草稿直接放在本任务report.md的明确区块内，使用MAM发布report。报告先给简短完成情况，再给不超过约1800英文词的正文草稿。中文裁决说明不超过300字。MAM任务UUID/workspace由CLI查询；不在paper主checkout写文件。

先读MAM AGENTS/README的执行与交付，再读取：
- /root/Documents/task-state-vla-paper/README.md
- docs/EXPERIMENT_PLAN_20260910.zh-CN.md（当前已发布实验问题与边界）
- docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md（已核查原文的引用入口）
- review.md，以及sections/01_introduction.tex和sections/03_method.tex作为旧稿参考。
不递归搜索所有历史文件，不重新审计算法/训练实现。论文库目前未注册MAM环境入口，所以本任务只产出report中的文字；Manager负责集成。

正文包含：建议的一个英文题目；动机与研究问题；最少必要的数学记号与设计空间；Q2主比较和Q1/Q3诊断各自的解释边界；核心图表如何组织；一小段限制。文献事实沿已核验文档，不扩展未经查证的首创/成本/效果声明。必要时读取其官方论文原文核查具体问题，但不新增庞大文献综述。

## 必须保持的研究判断

- 这是实证研究，不能把有限状态机、显式递推或新配置系统包装成新算法；schema是实验分析和复现的工具。
- 时间轴用query t_n、预测H、实际执行K_n、监督参考时刻、反馈选行r表示。区分训练GT和部署预测、next-query输入和当前动作条件；不要将动作被接受视为动作完成。
- 共同语义并不代表协议相同；full/serial原始比较同时变结构/条件/时序，是能力比较。低维表示不等于充分统计量、已实现全部设计空间或必然低训练开销。
- 核心Q2只变phase目标：每行phase(t+j+1)与每行重复phase(t+30)，两组同形状、输入、loss mask/norm/执行K30和消费row30。重复标签不保证预测行相同，因此不能把终点重复组随意改读首行。其他字段/机器人监督保持不变。
- Q1选行改变状态语义年龄也改变预测提前量；先报告完整反馈规则的效果，不能称作识别了唯一时间滞后机制。所有字段一起选行，不声称已隔离phase原因。
- Q3为同形状serial真实按钮槽与常量槽，train lag30固定，eval K30/K50；不能声称比较了各K匹配训练后的最优结果。
- 三个训练seed各100同初始条件评测，分别报告配对结果；不能合并成单模型300条，也不能把不显著写成等价。
- 新训练20k/batch32，demo_clean_state；真机wash两种方法同一S2M/phase schema，全部172合格episode训练，固定5个training episode做offline，offline不是泛化性能或真机成功率。不要承诺未执行的真机闭环试验数量。
- 当前F0旧30k模型row30=92/100、row20=86/100，row1/50尚未完成。初稿不写尚未完成的结果，不用这两个旧weights探索数字充当确认性三seed证据。可以用无数字的机制动机；标明论文结果段待完整新实验，不预写提升。
- 不改变已发布实验优先级、模型/评测数量和训练作业。若发现一个致命实验解释缺口，用中文裁决说明指出；不扩大实验清单。

期望25分钟内提交初稿。report列读取的主要文档和任何引用限制，不需要记录每条读命令。无代码commit，明确写“文本交付，未修改业务库”。Manager裁定后将请空白reviewer审阅文字。

## Manager首轮裁定（11:46）

保留当前篇幅和实验边界，做以下精简修正后重新发布report：
- 时序总述不能说所有policy都输出H行memory；full为H行、serial为一个query状态，当前共同框架需允许二者。
- j始终是0-based预测索引，r为1-based反馈行且r=j+1；不在段落间切换。删除“four time quantities”的错误计数，直接列变量。
- repeated endpoint两组的H行是不同输出位置，不意味着统计独立，删掉“independently predicted rows”。
- demo_clean_state只修饰仿真训练，wash为真机数据。report里的“真机闭环尚在进行”不准确：实际尚未安排设备执行，改为待执行。
- 正文写成可使用的研究叙述，删去开头过密的“not a new…not a claim…”和要求读者如何写稿的措辞，限制与解释边界放在对应比较/末段。相关工作仍使用可核查的明确文献名并列原文链接。
- Q3明确为差异之差；假设结论不预写。
- 建议标题改为 Task Memory in Action-Chunked Policies: A Study of Supervision and Feedback。图表建议控制为一张问题/时序示意、一张主结果图、一张Q1/Q3诊断图、一个协议表；避免正文重复主结果表与主结果图。
这些是文字准确性修订，不追加实验或查新任务。

Source report:

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
