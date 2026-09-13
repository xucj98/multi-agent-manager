# 论文40批证据版：TeX编译与排版验收（不做科学审稿）
# 论文40批证据版编译与排版验收

你使用gpt-5.6-terra/max，只负责TeX编译和排版/工件核验，不承担论文科学审稿或更改主张。Manager已亲自更新正文、表格和实验合同，冻结论文仓库 `/root/Documents/task-state-vla-paper` commit `8dc182a2db6d8cfbb1db2780dc5ea3814ea5970f`。阅读MAM AGENTS/README任务规范后，用mam workspace add为本任务从此commit建立独立paper worktree，再读适用规范。不要改主workspace未跟踪main.pdf。

本机TeX已经安装。复用现有Makefile `make paper`，不要重新安装或设计构建框架。编译应生成paper.pdf，检查页数、引用/box warnings、Letter和嵌入字体；运行既有submission check并如实说明INTERNAL DRAFT研究未完成标记导致的预期拒绝。逐页渲染目视检查表格溢出、图重叠、空白页和错误断页。当前旧PDF6页，新稿允许自然排版，不能为了保6页删结果或缩小到不可读。若排版需TeX修正，先报告具体位置给Manager，未经裁决不改科学文本。

核对PDF文字含40批/4000次执行/20模型/9个完整三eval，以及新增rearrange J train0 87/87/90=264/300和相同RNG对照的说明；旧图只展示既有固定子集，不要求重新生成。不要把此工作声称为空白GPT-6审稿、新的实验验收或第二轮论文科学PASS。

交付独立worktree中干净commit（仅paper.pdf和必要简洁构建receipt，不提交build/缓存/逐页临时图）；receipt记录source commit、PDF SHA256、页数和实测检查结果。报告写回本MAM任务report.md并publish，给Manager精确产物commit与路径。清理你自己的临时渲染，保留可复核PDF/receipt/必要日志摘要。通常短构建无需job；实际预计>30分钟才登记。完成可执行工作后正常结束，MAM通知Manager。
