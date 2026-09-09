# Rearrange 的按钮字段、state token 与动作边界

## 重点问题
- 为什么按按钮需要区分按下/回程？定位有/无button字段的真实设计、标注和输入输出时刻，不能把用户回忆当已证实结论。
- serial/parallel 的因果条件图是什么，soft/hard在旧代码里究竟约束什么？是否动作chunk跨状态边界、mask/truncation/holding，不先解释成soft/hard memory。
- 预测chunk长度H、实际执行K=15/20/30/50、状态回灌索引是否分别变化？按钮字段收益与K的交互能否构成受控比较？

## 主要来源
experiments/ 与 eval_result/ 下 pi05_rearrange_state_token_boundary_ablation、rearrange_blocks_eval_diagnostics；同组中 serial_soft_no_button 的run和checkpoint（checkpoint可能放不同训练组）。补充 pi05_multitask_state_token_serial_soft 的非shared执行实现，只为确认算法定义，不深入跨任务结果（交另一agent）。旧pi05 fork主要在RMBench/policy/pi05；实际commit归属以metadata查验。

## 工作与验收
1. 对每个实际实现variant，沿converter→sampler→state target/action target→model条件关系→部署feedback还原事实，记录字段及默认值/有效override；核查行为来自训练代码还是evaloverride。
2. 按训练checkpoint归组K和eval seed，使用具体run给按钮有无×K小表，区分同checkpoint推理干预与重训练。保留各seed的结果和样本数。
3. 读取已有失败诊断统计，给出按压未到位/已按仍下降/抬升/未按直接离开等标签的实际定义及计数。诊断不能覆盖的失败标unknown；不要逐视频主观打标签凑机制结论。可少量查看最有代表性的已有诊断/trace，引用episode id/seed文件。若存在失败分析阈值或只针对失败集选择的统计，写清分母。
4. 用一张时间表或简短公式表达旧实现输入memory的语义时刻、输出target时刻、feedback使用哪项动作后更新。哪些比较有多个变因同时变化，明确列出来。
5. 结论限于有证据的现象。最多提出2个待检验解释和各自缺的最小对照。

## 独占交付
- experiments/history_audit_20260909/rearrange_tokens.zh-CN.md
- experiments/history_audit_20260909/rearrange_token_designs.csv（实现variant级，包含code/config引用及事实）
- experiments/history_audit_20260909/rearrange_failure_evidence.csv（有诊断的run/类别/分母/计数/来源；没有就明确记录缺失，勿虚构）


## 共同要求

本轮仅整理已完成实验的原始结果和历史实现，为论文的实证研究提供可核验事实。用户要求manager负责规划、分工、验收，具体工作由你执行。阅读 MAM AGENTS.md、任务发布要求，再读 RMBench/AGENTS.md 和 docs/guidelines/{code,rmbench,experiments}.md；设计讨论背景只读 /root/Documents/task-state-vla-paper/ROADMAP.zh-CN.md。不要派生subagent。

工作区：mam workspace add <你的task UUID> --repo RMBench --base 681a928e266818bb430674c547b6458793bda227，使用自己登记的worktree/分支和独立环境。以其现有一键脚本创建一次即可。历史源码优先 git show <实际commit>:<path>；确需checkout时，只在自己的干净worktree及MAM登记分支上切换该历史commit，回到交付base再写文档，严禁切换共享主checkout/创建游离worktree或分支。记录converter/train/eval各自commit，不能用当前HEAD推断旧行为。metadata记录dirty时按具体改动文件判断证据边界；未知源码改动缺少当时patch时标注缺口，经核对仅.gitignore等且与所研究机制无关的改动只注明范围，不据此否定所有实现事实；现存历史补丁归档在 MAM/.local/archives/3b1cdd78-c7b9-4174-a132-497b485fcfaf/，只按已知线索定向查找。

原始结果现在位于 /mnt/public/xcj/Projects/RMBench/eval_result（/root/Projects是其别名），包含新导入wuwen-11旧实验及本集群三组完成结果。只读所有共享结果/模型/数据；本轮不删除、移动、改写原始metadata，也不修改算法或启动训练、仿真eval/真机任务。只允许必要的小型CPU解析/统计；不重复hash所有视频/模型，不做无目的全盘扫描。旧路径 public3→public 只用作定位候选，并记录原始路径和本地解析路径；找不到的checkpoint不下载大模型。缺失commit先核本地对应repo/对象；确实缺失时报告manager，已有证据工作继续。

证据格式：以相对 eval_result 路径作为run标识；逐run区分训练seed、评测seed、ckpt step、样本数、骨干/LoRA、预测长度H、实际执行K、input lag、memory内容和实现开关。信息缺失填unknown，不猜。成功数/episode数来自实际结果，尽可能对diagnostics核对ID和seed；格式无逐集记录时降级为summary证据。两eval seed均值不等于两个训练seed；重构前后复跑不等于独立训练；相同数据复制不当独立run。同骨干、字段/训练/执行协议相同才能把差异归于单个设计变量。

代码实现事实引用 repo + 完整commit + 文件/函数（可加行号）；配置/命令/diagnostics引用具体文件。清楚区分：源码及产物已证实、日志支持但实现缺失、推测/待核实。区分记忆内容和编码/条件结构/时序；soft/hard按实际代码含义命名；H与K与history间隔分别记录。输出简洁中文，表格为主，避免长篇复述历史对话。旧README事实可引用，但不能作为原始结果和历史代码双重已核实的替代品。

交付只写自己任务分配的 experiments/history_audit_20260909/ 文件，其他主题/原主表及旧README由相应负责人处理。可提交一个必要的短解析脚本（如果确实帮助重建表格），不用构建通用框架。文档小结包括：已经看到的现象、哪些比较有混杂、仍缺哪一个关键证据。不要预设论文结论，不把工程bug自动当科学发现。

完成后提交自己的文档commit、清理临时解析文件，发布 MAM report.md，首行为 task_revision: <最新发布revision>，包含完成/未完成、workspace、commits:块（RMBench: 完整commit）、成果路径、关键发现/缺口；等待manager合入及归档。报告和任务均通过mam task publish发布。中间进度直接commentary，manager可读取，无需探索Codex通信接口。
