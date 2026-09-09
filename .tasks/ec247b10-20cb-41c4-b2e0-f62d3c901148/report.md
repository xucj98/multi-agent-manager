task_revision: 8fe3dd5e1f2848b5339ae1d75346fe139b3e61e2
# 只读实验设计与文献评议

完成与未完成：完成了方案、历史证据边界、原始文献核查及 Manager 初版计划的只读审阅；未写代码、未建环境、未运行训练/评测/GPU，也没有访问 `wuwen-11`。建议先以 P1 的时序审计和 P2 的两臂对照收敛，再决定是否确认 P3。

workspace、各库交付 commit：登记 workspace 为 `/mnt/public/xcj/Projects/workspace/ec247b10-20cb-41c4-b2e0-f62d3c901148`；本任务没有业务库、worktree 或代码 commit。唯一交付为本报告。

验证结果与成果位置：已只读核对论文的 `ROADMAP.zh-CN.md`、`docs/MEMORY_DESIGN_FRAMEWORK.zh-CN.md`、`docs/MEMORY_CONFIG.zh-CN.md`、`docs/EXPERIMENT_PLAN_20260910.zh-CN.md`，以及 `/mnt/public/xcj/Projects/RMBench/experiments/history_audit_20260909/` 的索引、token 和 shared-timing 审计；报告路径为本文件。外部来源见“文献核查”。

## 对 Manager 初版计划的具体修改建议（2026-09-10）

审阅对象为 [实验计划](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:1>)；以下建议用于直接修订该文件，不另起平行计划。

短评：矩阵可执行，且 B/T/F 的复用计数没有训练重复；开跑前必须把 P2 的 B 基线和逐坐标 mask 固定下来。72 训练应作为带闸门的总上限，D150 只能按实测 eval 吞吐释放。这里的补审优先于本报告中较早的独立排期建议，旧内容保留为审阅来由。

1. **给 Q1–Q3 排序并收紧可写结论。** [§1](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:13>) 应明确 Q2 是主问题，Q1 是部署规则诊断，Q3 是条件性内容×K 筛查。Q1 固定 K 时改行会同时改 h 与 d，只能得到“选行规则的整体效应”，不能写成 state-age 的独立因果；它也不能扩写为“为什么 action chunk 有效”。Q2 仅在 rearrange 和 put-back 的三 train seeds 都有同向、可解释的结果时升级为跨任务规律。Q3 的 c0 对照改变标签熵、监督难度和 action condition，只能称有意义字段学习设计的交互，不能称纯内容或纯 memory-off 效应。

2. **把 P2 的复用基线冻结为显式配置。** [§4 的两个 full per-frame 槽位](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:48>) 和 [§5 的 B/T](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:67>) 应命名为 `full-per-frame-p2mask`（仅 rearrange、put-back），并写明它是新的受控基线，不能与历史 full 当严格复现混称。该 checkpoint 可以复用给 F；但 swap/cover/battery 不必被迫改成这个 P2 专用 phase mask。

3. **将 P2 mask 写成可验收的损失定义。** [§6 T](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:86>) 增加 `phase_valid[t,j]=1[t+j+1≤L]·1[t+30≤L]`，其中 L 是转换后该 episode 最后一个可引用的 phase 时刻。两臂都对 phase 的全部坐标乘这个 mask，按 `Σ_j phase_valid·loss_j / H` 归约；零 target 本身绝不能代替 loss mask。保存每样本有效行数 m/H、phase 标签/边界计数和 mask 版本到 metadata，并以单元测试核对两臂相同 t 的 mask 完全一致。

4. **保留固定 H 分母，但准确说明它控制了什么。** 这个公共 mask 加固定 H 分母确实防止尾部时两臂拥有不同的有效位置数或 phase-loss 尺度；它不消除重复终点造成的标签重复、类别频率、边界权重和梯度差异。这些是 T 的有意处理效应，结果只能归因给“目标构造”，不能提前归因给预测难度或某一梯度机制。机器人 tail、其他字段 target/loss、normalization、样本起点和 action condition 必须逐项保持不变；特别检查 full action path 没有从改写后的 phase target 隐式取得 teacher-forcing 条件。

5. **修改 U 的命名和结论。** [§1/§6 U](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:17>) 的 initial-input 方案是合理的“辅助状态监督、无动态记忆输入”对照：它与 no-memory 可检验 state head/loss 的额外价值。它同时改变 I 的训练分布，不能单独识别 cache U 的反馈效应；将标题从“递推与辅助监督”改为这个更窄的含义。若论文需要“feedback 本身有效”的主张，应从 B 的空余扩展名额中保留一个明确的 cache 干预，而不是把 U 的差值过度解释。

6. **把 72 训练改为上限式分层，而非无条件基础承诺。** [B 的 45 项](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:67>) 先只完成 rearrange/put-back 的 18 项；加 T6、U6、C3、R12 后是 45 项的可裁决主链。swap/cover/battery 的 B27 项应在 Q1/Q2 信号通过后入队，或其中 6 项改作 P2 命中后的“仅第30行状态 loss、总权重相同”定位对照（2 任务×3 seed）。这样仍保留 72 的硬上限，却不会在主问题尚未成立时扩展成跨任务排序。

7. **拆开评测计数并给 D 加容量闸门。** [§5 的标题和合计](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:61>) 应写为：96 个核心仿真 100ep run（B45+T6+U6+C9+F30）＋12 个 5ep offline 回放；D 另为最多 150 个可选仿真/诊断 job。F 的 30 和 C 的 9 都是正确的复用计数，但应在表下注明，避免被误读成漏算。两张 eval 卡两周仅有 672 GPUh：按计划的 2–4 GPUh/run，246 个仿真 run 要 492–984 GPUh，后者超过 eval lane。首个有效 100ep run 测得耗时后，令 D 的可排数为剩余 eval-GPUh/实测均值；否则须明确释放 wuwen-1 的空闲训练卡给 eval，不能把 D150 当承诺。

8. **在首批的说明里标出证据状态。** [首批八项](</root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md:42>) 只包含 P2 的两个任务 seed0 筛查，并未测试 c0 或 U，也还没有三 seed 复现；应写成“接口验证＋筛查”，不写成已足以裁决三个问题。首批 full per-frame 同时必须使用上面的 P2 mask，避免稍后为 T 重训所谓可复用基线。

## 结论与证据边界

- 历史结果能支持“完整协议及 K 敏感”：rearrange 的 shared full/serial 同时改变 I/T/C/U，不能称编码因果；旧 button/no-button 也改变了字段数和参数树，两个 eval seed 不是两个 train seed。
- 因此中心贡献应是：**固定低维记忆语义和骨干后，状态目标时间、cache 回灌和执行 K 如何共同影响闭环可靠性**。schema 只用于把变量写清，不能作为贡献本身。
- full/serial 可保留为能力参照和真机配置，但绝不可写成“纯编码效应”。Oracle 需逐一声明替换 I、当前动作条件 C 或下一次 cache U；它不是自动上界。

## 三个可判别的研究问题

| 问题 | 已知 / 尚未知 | 最小比较与固定项 | 正、负结果各支持什么 |
|---|---|---|---|
| RQ1：反馈行的收益是否随 K 改变？ | 同一 checkpoint 的 K 曲线有大差异；未知反馈规则是否有可重复的 K 交互。 | P1：H=50 shared-full checkpoint，K={20,30,50}、d={0,10}，row=K-d；固定 checkpoint、解码、evaluator、100 个配对初始条件。 | 稳定交互支持“反馈行与执行长度须共同选择”；无交互只说明该 checkpoint 的 K 敏感，不能归因给状态年龄。 |
| RQ2：同一消费时刻下，逐帧还是重复终点状态监督更有效？ | 历史 full 是逐帧未来；未知目标构造本身是否有稳定效果。 | P2：phase 的 t+j+1 对 t+30，H=50/K=30；固定 S、I、C、A、U、数据、shape、损失权重、采样和 evaluator。 | 差异跨 seed/任务重复，支持目标构造是设计选择；无差异则不支持以该选择解释 full/serial 差距。 |
| RQ3：按钮语义的收益是否依赖 K？ | 历史结果有 K30/K50 交互，但有字段数、规则和 checkpoint 混杂。 | P3：三字段同形状 serial-soft 的真实 button 对恒定 c0，K={30,50}；固定其余字段、head/embedding、loss、训练和 evaluator。 | 差中之差跨 seed 存在，支持“该字段学习设计与执行协议交互”；无差异则旧交互不足以推广。 |

## P1/P2/P3 评议

**P1 有效，但它是部署诊断而非机制分离。** 固定 K 时从末行改为早 10 行，同时改变预测提前量 h 与消费年龄 d；在 Δ=K 下不能把任何差异写成 d 的独立因果效应。六格可回答规则的整体效果。每 query 必须记录实际完成 k、下一观察和消费时刻；中途终止不伪造下一次反馈。先确认 checkpoint 可读且 `last_executed` 语义正确，否则停止 P1，不以新训练替代这一审计。

**P2 是最接近中心问题的第一训练对照。** 公共 mask `t+j+1≤L 且 t+30≤L` 和固定 H 分母使两臂有相同有效位置数、相同每样本 phase-loss 缩放；它们不新增两臂间的尾部混杂。代价是靠近 episode 尾端时 phase 相对动作的权重变小，这会影响共同的样本加权，应记录有效行数 m/H 的分布。

P2 仍有意改变重复标签、类别/边界权重、预测难度和共享表示梯度；这些正是“目标构造”的作用路径，不应被误称为已控制的机制。必须审计 serial 的 `current_condition`：若它从改写后的 target 取 teacher-forcing 值，T 会暗中改 C，比较失效；动作条件必须显式固定为同一语义时刻。若 P2 有效，再加“只第 30 行有状态 loss、总权重相同”的定位臂，而非首轮三臂全开。

**P3 是合格的内容×执行筛查，尚非纯内容消融。** c0 组保持容量，却改变标签熵、状态 loss 难度和动作条件；所以它回答“有意义的按钮输入/监督/反馈设计是否有益”，不回答同一模型关闭输入后的纯内容效应。历史有规则的 button 模型不能当作新 c0 基线。若筛查命中且 trace 指向标签统计而非行为语义，才追加统计匹配的无关标签；不展开属性锁存、转移 mask、lag 的笛卡尔积。

## 必要但应节制的对照

- **无记忆**：需要一个同骨干能力锚点；若没有同 shape、同 evaluator 的现成 checkpoint，首波做 1 个 dummy-input/no-cache run。它不能代替 P1/P2 的两臂因果比较，也不应在首波多 seed 扩张。
- **辅助状态监督、无递推**：为中心的“闭环反馈”主张所必需。保留同一 state head/loss 和本 query 的既定 action 条件，只禁止 U 写入下一 query cache；这区分表征辅助收益与跨 query 递推收益。它需要在实现规格中写清，不能把“无 state head”冒充它。

## 两周分层矩阵

计数约定：一个 training run 产生一个仅含最终 BF16 权重和 metadata 的 checkpoint；一个 100ep eval run 是某 checkpoint 在一种已固定协议下的 100 个配对初始条件。两个 eval GPU 专用于 smoke、诊断与这些 eval，不将重复 eval 充作训练重复。

| 层级与闸门 | 训练 run / checkpoint | 100ep eval run | 输出或停止条件 |
|---|---:|---:|---|
| P0 + P1（先行） | 0 / 1 个既有可读 checkpoint | 6 | K×d 的六格、时间 trace；若时序/权重不可核，不进入比较。 |
| 首波 P2 筛查 | 4 / 4 | 4 | 逐帧、重复终点各 2 个配对 seed，均 K30。 |
| 首波 P3 筛查 | 2 / 2 | 4 | 真实/c0 共用 1 个 seed，各评 K30、K50；仅筛查交互。 |
| 能力与反馈锚点 | 2 / 2 | 2 | 无记忆、辅助监督无递推各 1 个 seed，均 K30。 |
| 首波合计（8 个单 GPU 名额） | **8 / 8** | **16** | P2 是默认确认候选；P3 只有在 P1/P2 不能解释历史交互时升级。 |
| 确认性补种子 | **6 / 6** | **6** | 对选中的两臂比较各补 3 个共享的 train seeds，K 固定为主比较值。 |

“补 3 个 train seeds”应解释为每个两臂比较共享的 3 组独立 seed，故需要 2×3=6 个原始训练 run；若只给 3 个原始 run，只能做可行性检查，不能称确认性比较。确认时每 seed 每臂各做一次 100ep 配对评测，报告每 seed、配对差和区间；不要用多次 eval 填补缺失 train seed。

扩展只在上述闸门通过后择一：P2 跨 put-back 的 2×3 run/6 checkpoint/6 次 100ep eval，或 P3 的 2×3 run/6 checkpoint/12 次 K30+K50 eval。cover 仅作后续反例检验，不预设失败原因。

## 资源与产物预算

- 所有新训统一单卡、bs32、20k steps，约 18 GPUh/run；只保留最终 BF16 权重与 metadata。首波为 8×18=144 GPUh；选中对照的确认性补种子为 6×18=108 GPUh，基础训练合计 **252 GPUh**。
- 十卡两周理论总量为 10×14×24=3360 GPUh。先锁 2 张 eval 卡的 672 GPUh，并至少留 336 GPUh 给 smoke、开发、失败重跑和数据/接口核验；即使只作算术，200×18=3600 GPUh 也已超过全部容量，不能承诺完成 200 个训练。
- 扩展预算：跨任务或 P3 确认二选一各加 108 GPUh；真机的 wash-cup 与 drawer full/serial 四个 20k 训练再加 72 GPUh。100ep eval 的实际耗时目前未知，先用两 episode smoke 测量并由两张 eval 卡排程，不能虚构精确小时数。
- `wuwen-11` 只记录为未来候选资源：本次不访问、不预约、不计入可用预算。

## 真机安排与可说、不可说的话

- wash-cup 采用 S2M、单一 phase；排除 label 6、缺少子任务标注、或 1–5 未各出现恰好一次的 episode，允许阶段顺序变化。其余所有有效数据训练；随机留 5 个**训练** episode 做 offline 回放检查，并明确它们只是接口/预测诊断。
- drawer 用 phase+attribute；wash-cup 和 drawer 都保留 full/serial。每个设置的真实闭环由人工安排，预先记录任务成功、实际 k、接管和状态 trace；offline replay 绝不能表述为真机闭环成功。
- 真机先复用上述已冻结模拟协议的字段/时序审计，之后再讨论 full/serial 能力差；不要把不同字段数或当前配置差异叫作编码效应。

## 文献核查（仅原论文与作者页面/代码）

| 工作与可核验来源 | 它实际研究什么 | 与本设计空间的关系 |
|---|---|---|
| SAGE — [arXiv 2509.19853](https://arxiv.org/abs/2509.19853)、[arXiv HTML](https://arxiv.org/html/2509.19853v1) | 用当前观察和前一预测状态递推隐状态，以该状态条件化 Diffusion Policy；还研究主动标注与状态转移附近的软标签，并在三类真实多阶段任务评测。论文/arXiv 页未列作者代码；本次精确标题/作者检索未找到可归属仓库，代码状态记为未知。 | 与显式状态递推、状态条件动作和边界标签**部分重合**；所查正文没有在固定 state 语义下系统比较 chunk 内目标时间、反馈行和执行 K。不能据此宣称领域空白，只能定位为更窄的受控问题。 |
| Lazzati et al. — [arXiv 2608.02547](https://arxiv.org/abs/2608.02547)、[作者项目页](https://action-chunking.github.io/) | 在仿真和 Franka 上检验 action chunking，比较 delayed policy 与 randomized-delay ensemble，提出非马尔可夫条件化、减少 compounding error 和隐式集成的解释。作者项目页只列论文/arXiv，未列代码链接。 | 与 H/K、观测/动作的时间关系高度相关，直接否定“宽泛地研究 chunk 为什么有效”的新颖性。它不研究低维语义 state head 的目标时间和 cache 回灌；RQ1/RQ2 应报告为该窄交互。 |
| ACT（唯一额外直接相关工作）— [原论文](https://arxiv.org/abs/2304.13705)、[作者代码](https://github.com/tonyzhaozh/act) | 用条件 VAE 预测动作 chunk，并以 temporal ensembling 执行，面向低成本双臂模仿操作。 | 与 chunk 预测/执行协议重合；未以显式低维任务状态的监督与跨 query 反馈为研究变量。它是执行基线，而不是 RQ2 的对照。 |

文献结论：已有工作已覆盖状态递推（SAGE）与 action-chunk 机制（Lazzati et al./ACT）的相邻部分；本项目只有在同骨干、同语义、可复现的两臂比较给出跨任务结果时，才可主张关于状态目标与反馈的经验规律。
