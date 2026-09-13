# 论文40批证据版：TeX编译与排版验收（不做科学审稿）
# 论文40批证据版编译与排版验收

你使用gpt-5.6-terra/max，只负责TeX编译和排版/工件核验，不承担论文科学审稿或更改主张。Manager已亲自更新正文、表格和实验合同，冻结论文仓库 `/root/Documents/task-state-vla-paper` commit `8dc182a2db6d8cfbb1db2780dc5ea3814ea5970f`。阅读MAM AGENTS/README任务规范后，用mam workspace add为本任务从此commit建立独立paper worktree，再读适用规范。不要改主workspace未跟踪main.pdf。

本机TeX已经安装。复用现有Makefile `make paper`，不要重新安装或设计构建框架。编译应生成paper.pdf，检查页数、引用/box warnings、Letter和嵌入字体；运行既有submission check并如实说明INTERNAL DRAFT研究未完成标记导致的预期拒绝。逐页渲染目视检查表格溢出、图重叠、空白页和错误断页。当前旧PDF6页，新稿允许自然排版，不能为了保6页删结果或缩小到不可读。若排版需TeX修正，先报告具体位置给Manager，未经裁决不改科学文本。

核对PDF文字含40批/4000次执行/20模型/9个完整三eval，以及新增rearrange J train0 87/87/90=264/300和相同RNG对照的说明；旧图只展示既有固定子集，不要求重新生成。不要把此工作声称为空白GPT-6审稿、新的实验验收或第二轮论文科学PASS。

交付独立worktree中干净commit（仅paper.pdf和必要简洁构建receipt，不提交build/缓存/逐页临时图）；receipt记录source commit、PDF SHA256、页数和实测检查结果。报告写回本MAM任务report.md并publish，给Manager精确产物commit与路径。清理你自己的临时渲染，保留可复核PDF/receipt/必要日志摘要。通常短构建无需job；实际预计>30分钟才登记。完成可执行工作后正常结束，MAM通知Manager。

## Manager 确认论文仓库入口不适配，批准本任务一次性回退

Manager已核对MAM的PROJECT_ROOT=/mnt/public/xcj/Projects，而论文源在/root/Documents/task-state-vla-paper；源树没有MAM强制要求的.local/create_worktree.sh。此为已授权构建的本地实现障碍，无需用户额外批准，也不为此扩展MAM功能。

本任务允许用标准git worktree add，从既定8dc182a创建 `/mnt/public/xcj/Projects/workspace/4fa0a008-aa9d-4eaa-ab23-b05c7f20d8c7/task-state-vla-paper`，使用唯一分支`task/4fa0a008-aa9d-4eaa-ab23-b05c7f20d8c7`。若已有目录/分支先核实而不覆盖。其余编译/验证/发布要求不变，不改MAM配置/数据库、不伪造repos登记、不往主仓库添加无关环境脚本。报告中明确这是手动创建的独立worktree，给出git common-dir、源commit及路径，供Manager验收后按git worktree流程清理；仍通过当前MAM task发布报告。

## Manager 排版裁决

收到你报告冻结稿第7页只有最后一条参考文献。批准在独立worktree做最小纯排版调整，优先浮动图表放置或合理局部间距，消除孤立参考页；不改科学文字/数字/文献、不删除结果，不改变IEEE字号、栏宽、页边距或强行侵入底边。现有图中文字必须保持可读。若这些约束内不能合理解决，保留7页并报告具体候选，Manager再调整文字，不必反复尝试全局压缩。

交付可包含该窄TeX diff及相应PDF/receipt；报告原7页现象与最终调整、完整复编译和逐页检查结论。不能把已有全部检查原样套到新PDF。
