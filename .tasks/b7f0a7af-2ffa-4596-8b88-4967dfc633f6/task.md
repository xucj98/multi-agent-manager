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
