# 论文文献定位与材料盘点（只读）

核查日期：2026-09-13。本文只提供文献事实、与现有实现的重叠/差异、主张边界、RA-L 官方要求和材料分类；不替 Manager 选择中心主张、研究路线、实验取舍或最终运行清单。未启动训练、评测或长进程；未编辑 `/root/Documents/task-state-vla-paper`。

## 1. 先要分开的两套论文材料

2026-09-13 后，仓库有一套 Manager 明确裁定的活动程序、一套仍有实现/审计价值的 2026-09-10 中间程序，以及旧 STSM 稿。三者不能当作同一证据链。

| 程序 | 可作为该程序权威入口的材料 | 实际研究对象与证据状态 |
| --- | --- | --- |
| 当前 2026-09-13 Manager 程序 | [`EXPERIMENT_PLAN.zh-CN.md`](/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md)、[`RESEARCH_POSITIONING.zh-CN.md`](/root/Documents/task-state-vla-paper/docs/RESEARCH_POSITIONING.zh-CN.md) | 以 RMBench 九任务的可复核能力为主线；C1/C2/C3 分别要求跨任务能力、递推输入与语义字段的作用、以及 target/feedback 协议的受控证据。该计划明确替代 20260910 plan 与旧 roadmap，但不是新增 GPU 作业授权。 |
| 2026-09-10 target/feedback 程序（实现与审计来源） | [`README.md`](/root/Documents/task-state-vla-paper/README.md)、[`EXPERIMENT_PLAN_20260910.zh-CN.md`](/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md)、[`PAPER_NARRATIVE_20260910.md`](/root/Documents/task-state-vla-paper/docs/PAPER_NARRATIVE_20260910.md)、[`RELATED_WORK_POSITIONING_20260910.zh-CN.md`](/root/Documents/task-state-vla-paper/docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md) | 固定相同低维任务记忆，研究状态目标、动作 chunk 的实际执行前缀和下一查询反馈如何配合。它保留 Q1/Q2/Q3 的精确时序定义和已有 checkpoint 的解释边界；不再单独决定当前论文路线。 |
| 旧 STSM/归纳偏置程序 | [`main.tex`](/root/Documents/task-state-vla-paper/main.tex)、[`sections/`](/root/Documents/task-state-vla-paper/sections)、[`tables/`](/root/Documents/task-state-vla-paper/tables)、[`paper.pdf`](/root/Documents/task-state-vla-paper/paper.pdf)、[`STORY_AND_CLAIMS.md`](/root/Documents/task-state-vla-paper/docs/STORY_AND_CLAIMS.md) | 将“结构化候选状态作为强归纳偏置”、示范量 `{5,10,25,50}`、oracle ceiling、schema boundary、rich-memory/NativeMEM 对照和 Tea/Cup 真机作为主证据。现有 ledger 也明确其中多数为 pilot 或 TBD。 |

因此，旧稿的“示范效率、常数大小状态优于 rich memory、oracle/边界、真机”叙事不能替代当前九任务/递推/协议证据；反过来，当前 Q1/Q2/Q3 也尚未构成旧稿要求的 matched scaling、NativeMEM、oracle 或真机证据。

### 当前实现的事实边界

- 当前文字把一次 query 记为 `t_n`，预测 horizon `H`；full 产生 `H` 个状态行，serial 产生一个 query state。实际执行前缀为 `K_n`，下一 query 的 full feedback 由输出行 `r_n` 消费。训练的 recurrent 输入是相应参考时刻的 GT memory，部署时是初始化后递归预测。
- Q2 是最干净的同形状 target 构造比较：两个 full one-hot 模型都有 `H=50`、`K=30`、`r=30`，动作目标、字段、loss、mask 和输入相同；只比较逐行 `phi(t_n+j+1)` 与在每行重复 `phi(t_n+30)`。Q1 仅在既有 per-frame full checkpoint 上改变 `K` 与反馈行；Q3 才比较真实 button field 和相同槽位中的常量 field。full/serial 历史结果同时改变表示、条件路径和时间，不能归为单一“表示”变量。
- 外部的 [`RMBench 实验台账`](/mnt/public/xcj/Projects/RMBench/experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md) 的 2026-09-12 快照记录：12 个 Q2 20k checkpoint 的每个训练 seed 已有一次 `eval_seed0` 100-rollout 正式评测；台账同时标为 `eval_seed1/2` 的新入口仍待独立审阅、未部署。这是结果台账状态，尚未同步进上述论文仓库的“RESULTS PENDING”叙事；本文不据此作出效果方向或论文结论。
- [`U auxiliary-initial 控制`](/mnt/public/xcj/Projects/RMBench/experiments/memory_chunk_20260910/README_u_auxiliary_initial_input.zh-CN.md) 的最后记录时间为 2026-09-12 06:35：六个 20k 模型已启动、通过 step-100 finite-loss 门槛，但没有完成 checkpoint 或闭环结果。U 保留相同 action/state target、loss、shape 和 feedback metadata，却在训练和部署都固定 memory input 为 `initial`；预测可记录但不被下次输入消费。它隔离“递归输入”与“附加状态监督”，不是 no-memory 网络。未见随后可核验产物前，不能称其完成或把它当成机制证据。
- [`EVIDENCE_LEDGER.md`](/root/Documents/task-state-vla-paper/docs/EVIDENCE_LEDGER.md) 中的旧 STSM/key-state 数字主要是一训练 seed、100 rollout 的历史/pilot 记录，且并非同一 stack 的完整 matrix；公开 RMBench 或 Mem-0 数字也不是本项目的配对比较。

## 2. Primary-source 文献矩阵

下表的“当前差异”只陈述实现与论文的事实，不把不同骨干、数据、训练、评测协议的论文数字当作可直接比较的 baseline。

| 工作与原始来源 | 记忆如何预测/消费，如何与动作相连 | 与当前实现真正重叠和不同之处；可用边界 |
| --- | --- | --- |
| [RMBench / Mem-0](https://arxiv.org/html/2603.01229) | RMBench 有 9 个任务：5 个 `M(1)`（Observe and Pick Up、Rearrange Blocks、Put Back Block、Swap Blocks、Swap T）与 4 个 `M(n)`（Battery Try、Blocks Ranking Try、Cover Blocks、Press Button）。论文的 Table 1 对每个策略使用 50 synthesized demos、100 rollouts。Mem-0 用 completed-subtask/end-image 的 planning memory，执行端用 anchor/sliding visual memory，二者由 subtask-end classifier 连接。 | 与本项目共享 benchmark 与 memory-dependent manipulation 问题；Mem-0 不是 typed task-state row、`H/K/r` target/feedback 协议。现有本地 Mem-0 数字只能作系统能力上下文，不是同 stack 的因果对照。论文没有规定训练 seed 的标准。 |
| [SAGE](https://arxiv.org/html/2509.19853) | 将阶段作为有监督的 categorical hidden state；当前 observation 和上一预测状态用于估计状态，预测 state 再条件化 Diffusion Policy 的动作。论文还涉及主动标注与软 transition 标签。 | 已覆盖“显式递归状态”“阶段监督”“state-conditioned action”。当前实现的差异是多字段语义、action chunk 的 future row targets 与下一 query 的明确行消费；SAGE 没有测试 full-row/per-frame/repeated-endpoint 的本协议。不能写成这些广义概念的首次提出。 |
| [NativeMEM 论文](https://arxiv.org/html/2607.06678)；[官方代码](https://github.com/OpenDriveLab/NativeMEM) | 每个历史 frame-view 压为一个 token，跨时间和视角追加到 VLA input；先做 frozen-VLA 的 generic tokenizer alignment，再 task-specific finetune。它在三个 RMBench 任务报告 10/25/50-demo scaling。官方 code repo 已公开，但 README 明示仍为 work-in-progress，要求使用者自己训练 Stage-1 tokenizer、缓存 `mem_token`，然后 Stage-2 finetune。 | 与当前项目同属 `pi_0.5` 家族的长时记忆比较语境，但它是随保留历史增长的 visual token sequence，不是固定 typed field。核查时官方 [Releases](https://github.com/OpenDriveLab/NativeMEM/releases) 页没有任何 release，README/官网也未提供作者训练好的 tokenizer 或 task checkpoint 下载；现成 config 只显式列出部分 RMBench 风格 task-id，尚不建立九任务可直接运行的事实。因此代码可用于工程复现，不能把作者权重或公布结果称为可直接复现；tokenizer 的额外数据、训练和版本必须单列，当前没有可写的 same-stack 相对结论。 |
| [Why Does Action Chunking Improve Behavioral Cloning Performance in Robotic Control?](https://arxiv.org/html/2608.02547) | 研究 chunk 的延迟策略表达、compounding error 与 implicit ensemble；作者显示由 chunk policy 诱导的 random-delay ensemble 可匹配多个设置中的 action chunking。 | 已覆盖“chunk / 部分执行 / query freshness 会影响性能”的一般命题。当前 Q2 固定机器人动作目标，改变有监督语义 memory 的 target time；它不能凭结果宣称验证该论文的 delayed-ensemble 机制，也不能把随机旧 state lag 等同于 random delay。 |
| [TFP](https://arxiv.org/html/2607.08283v3) | 连续时间 latent belief（LTC）直接条件化动作；在相同 adaptive receding-horizon executor 下，用实测 query elapsed interval 对比 constant step，并报告 recurrent training 的代价。 | 已覆盖“非均匀 query 间隔应进入记忆更新”和“recurrent memory 影响 action chunk”。当前工作可区别为有监督语义字段的 target reference time 与 feedback row，而不是 latent continuous-time belief；不能声称首次研究 time-consistent/query-interval memory。 |
| [SparkVLA](https://arxiv.org/html/2608.16172) | 用 cached subtask anchor/history 和当前特征，联合给 Stop 与所有 action-prefix 长度打分，选择执行 prefix 后再观察。 | 已覆盖 stop/阶段边界与 prefix length 的联合处理。当前计划没有其 adaptive selector；其可区分对象是固定协议下 semantic memory 的监督/消费时刻，不能宣称最先发现执行长度与子任务边界的交互。 |
| [EventVLA](https://arxiv.org/html/2606.20092) | 从 action-conditioned VLA hidden states 预测整个 future chunk 的 keyframe probabilities；超过阈值时，在实际执行到该步后把 raw image 写入 sparse visual buffer，随后与 anchors/current observation 一起条件化动作。 | 已覆盖 memory 写入时刻、future-chunk head 与 chunk-size 消融。当前方案的不同点是消费 typed semantic fields 而非原始图像；不能写成 memory 系统此前没有 target-time/write-time 问题。 |
| [StaKe](https://arxiv.org/html/2606.26801) | 从 demonstration gripper states 自动取得 stage 与 next-transition keyframe 辅助标签；辅助 heads 只用于训练，base VLA inference loop 不变。论文也比较 event-driven target 与 fixed-horizon target。 | 已覆盖“stage/keyframe auxiliary supervision 可改善 VLA fine-tuning”这一方法族及 target construction 的邻近问题。U 的 initial-input 控制正是区分状态损失与部署递归 feedback 的必要事实工具；U 未完成时，不能把收益归因于递归或把 auxiliary supervision 写成新颖本身。 |

补充说明：这些来源大多是论文作者的 arXiv primary source，列出的是其方法和所报告的协议事实，并不等同于对每个公开实现进行复现或 version audit。

## 3. 需要避免或保留证据门槛的表述

以下不是论文路线选择，而是文献和当前实现所给出的负面边界。

1. 不可用“首次显式状态递归、首次阶段监督、首次 state-conditioned control”描述工作，SAGE 已具备这些成分。
2. 不可用“首次发现 action chunk/执行前缀/停止与性能有关”或“首次处理非均匀 query interval”描述工作；Action Chunking、SparkVLA 与 TFP 已覆盖相应一般问题。
3. 不可用“首次研究 future target 或 memory write timing”描述工作；EventVLA 和 StaKe 都有 future-horizon / keyframe-target 设计与消融。
4. “低维 typed state 相对 rich visual memory 的示范效率、延迟、token 或总成本优势”目前没有被当前程序的 Q1/Q2/Q3 证据覆盖；旧稿需要的 scaling、matched NativeMEM/one-token visual memory、tokenizer data/compute 账目及 cost metric 都仍缺失。
5. 不能把 `full` 对 `serial` 或历史 pilot 的排序解释成单一表示、监督、反馈或时间机制；现行叙事已正确记录它们改变了多项协议。也不能从单个 `K`、`r` 扫描推出一般最优 `K` 或独立的 memory-age 因果效应。
6. 不能把 state auxiliary loss 本身当作新颖性，或在没有 U 结果时把 any success gap 归因于 recursive feedback。U 是“同输出监督、输入永远 initial”的控制，不能被误写成 no-memory baseline。
7. 不能把 offline state accuracy、短 replay 或真机训练内 offline 回放写成 closed-loop task success；新版叙事已区分这些量。也不能把“当前未区分差异”写成 statistical equivalence。

## 4. RA-L：本次复核的官方事实

| 项目 | 官方事实与来源 |
| --- | --- |
| 范围与页数 | RA-L 面向简洁、及时的创新研究想法和结果。Letter 是 6 页，最多 2 页付费附加页；图、表、参考文献和附录都计入 8 页上限，不能用 multimedia 绕过正文页数。[Information for Authors](https://www.ieee-ras.org/publications/ra-l/ra-l-information-for-authors/) |
| 初次投稿格式 | 初稿是 US-Letter、双栏 conference style；LaTeX 使用 `\\documentclass[letterpaper, 10 pt, conference]{ieeeconf}`。不加 cover page；保留 byline 空间但不放作者信息。[Information for Authors](https://www.ieee-ras.org/publications/ra-l/ra-l-information-for-authors/) |
| PaperPlaza 元数据和附件 | title + abstract 不超过 1200 characters；2–5 个 keywords，前两个来自 RA-L controlled list。PDF 上限 5 MB；可选 single ZIP multimedia 上限 50 MB，含 `ReadMe.txt` 与 `Summary.txt`。[Submission Procedures](https://www.ieee-ras.org/publications/ra-l/submission-procedures/) |
| 双盲 | 稿件、appendix、supplement 不含姓名/单位；acknowledgments 仅 acceptance 后加入；删去图/视频中的人名、单位、logo，blur faces，移除身份性 metadata 和泄露身份的外链。必要时机器人本体可出现。[Double-Anonymous Rules](https://www.ieee-ras.org/publications/rules-for-the-double-anonymous-review-process/) |
| 评审所问 | Reviewer 指南直接问 contribution、significance、写作/组织、目的、related work 是否相关完整、technical soundness。[Reviewer Guidance](https://www.ieee-ras.org/publications/ra-l/ra-l-information-for-reviewers/) |
| 生成式 AI | AI 生成的 text/figure/image/code 须在 acknowledgments 披露系统、涉及 section 和使用程度；作者仍对内容负责，不能伪造/操纵数据、代码、图或其他研究产物。该披露要求与双盲阶段不得放 acknowledgments 的要求需要在正式投稿前按官方流程协调，不能默认为已解决。[Generative-AI Guidelines](https://www.ieee-ras.org/publications/guidelines-for-generative-ai-usage/) |

官方页面没有规定固定数量的 training seeds、任务数或真机 trials，也没有接受保证。RMBench 的“50 demos + 100 rollouts”是该 benchmark 论文的实验协议，不是 RA-L 规则；Action Chunking 论文在部分分析中使用三个 policy seeds，也只是该作者组的估计选择。不能把“三个 seed”表述为期刊硬性投稿门槛，证据规模须与最终声明范围和方差相匹配。

## 5. 旧材料盘点和清理建议（不执行删除）

| 分类 | 文件/目录 | 处理含义 |
| --- | --- | --- |
| 当前研究与实现事实：保留 | `docs/EXPERIMENT_PLAN.zh-CN.md`；`docs/RESEARCH_POSITIONING.zh-CN.md`；`docs/MEMORY_DESIGN_FRAMEWORK.zh-CN.md`；`docs/MEMORY_CONFIG.zh-CN.md`；`docs/memory_config/`；`docs/MEMORY_SCHEMA_SWAP_T.zh-CN.md` | 20260913 的前两份是当前路线和主张边界的权威入口；其余为时序、S/P/E 描述和配置语义来源。Swap-T 目前只是连续初始位姿候选 schema，文档本身也写明没有可核验正式结果，不能登记为覆盖证据。 |
| 前期方案/实现与审计来源：保留后标明 superseded | `README.md`；`docs/EXPERIMENT_PLAN_20260910.zh-CN.md`；`docs/PAPER_NARRATIVE_20260910.md`；`docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md`；`ROADMAP.zh-CN.md`；`docs/MEMORY_SCHEMA_SAMPLES.zh-CN.md`；`docs/RAL_REQUIREMENTS.md` | 20260910 文档仍提供 Q1/Q2/Q3 的精确定义和代码审计背景，但不能与 20260913 主计划争夺权威。Roadmap 是规划历史；samples 是历史 S/P/E 审计辅助；RA-L 文件应保留但每次投稿前按官方页面更新日期。 |
| 审计与可追溯性：保留，不作当期主结果 | `docs/EVIDENCE_LEDGER.md`；RMBench 的 `experiments/history_audit_20260909/`、`experiments/memory_chunk_20260910/` | 保留 pilot、checkpoint、产物与协议来历。它们应明确标成 historical/audit 或 current external ledger，不能用不同 revision 的数字填进新论文正文。 |
| 旧论文程序：建议在 replacement manuscript 和结果 ledger 稳定后整体归档 | `main.tex`、`config.tex`、`sections/`、`tables/`、`figures/overview.pdf`、`figures/simulation_evidence.pdf`、`figures/real_world_suite.pdf`、`figures/real_robot_protocol.pdf`、`paper.pdf`；`docs/STORY_AND_CLAIMS.md`、`docs/EXPERIMENT_TODO.md`、`docs/REVIEW_2026-08-04_INDUCTIVE_BIAS.md`、`docs/REVIEW_ROUND2_2026-08-04.md`、`docs/REVIEW_ROUND3_2026-08-04.md`、`docs/REVIEW_ROUND4_2026-08-04_TITLE_AND_THESIS.md`、`docs/REVIEW_RESPONSE.md`、`review.md`、`claude/plan.md`、`claude/review.md` | 这些围绕 STSM/data-efficiency/oracle/boundary/Tea-Cup 旧证据链。建议移入有日期的 `archive/` 或 `historical/`，不删除；frames 和 source 图应随该历史材料保留，避免丢失 pilot 可追溯性。 |

核查时保留了论文仓库已有未跟踪材料，未作写入或移动：`ROADMAP.zh-CN.md`、`docs/MEMORY_CONFIG.zh-CN.md`、`docs/MEMORY_DESIGN_FRAMEWORK.zh-CN.md`、`docs/MEMORY_SCHEMA_SAMPLES.zh-CN.md`、`docs/MEMORY_SCHEMA_SWAP_T.zh-CN.md`、`docs/memory_config/`。

## 6. 交付记录

- 只读检查的论文源：`/root/Documents/task-state-vla-paper`；它在 MAM project root 外，且本任务要求不修改，因此未建立会改变其 worktree metadata 的 worktree，也没有提交。
- 交付副本：[`literature_positioning_20260913.zh-CN.md`](/mnt/public/xcj/Projects/workspace/6a56a3e8-0dba-482b-980a-d3e819563c5d/literature_positioning_20260913.zh-CN.md)。
- Primary-source 链接和 IEEE RAS 官方页均已在线复核；未将公开论文结果冒充为本项目实验结果。
