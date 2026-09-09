# Shared memory 的 full/serial 与 Oracle 时序

## 主要来源
experiments 与 eval_result 下 pi05_rearrange_shared_memory_representation、pi05_multitask_shared_memory_representation、pi05_full_key_state_with_prop_history。跨任务非shared serial参考 pi05_multitask_state_token_serial_soft；rearrange早期token/buttons由另一agent主责，不重复深入其组。

## 核心工作
1. 核实shared两个路线哪些memory字段相同，schema哪些内容共用、哪些converter/model/deploy分叉。逐路线列出phase/属性/按钮等字段含义、编码、维度、初始化和可见性来源。
2. 精确还原训练样本：当前/更早input memory，固定lag或[15,50]随机间隔抽样单位，chunk-level/frame-level输出target，动作边界处理，action/state拼接与modelloss。把字段语义、表示编码、时间目标分开。
3. 还原部署：当前query动作是否使用刚预测memory；一次预测H执行K后何时取哪一索引反馈；连续值/argmax解码；full与serial缓存/状态是否同种语义。需要按当时训练/eval各自commit来读，不能按新robot-bridge机制替代历史事实。
4. 逐一审计Oracle run：真值来自什么函数、替换哪一层/哪一时刻、同时影响本次动作条件还是下一轮输入、Oracle是否与训练分布匹配。给出93→82、36→79等记录真实run支撑/冲突，不预设Oracle为上界或预先归因计划时钟。
5. 还原跨任务方法排序（putback/swap/cover/battery）及fixedlag/randomlag差别，区分训练seed与eval seeds；[15,50] serial30.5与同配置历史36的区别写清。
6. 建立统一设计选择表，每行一个实际训练+反馈配置，字段至少 memory_content,input_source/time/lag,output_target_time/granularity,action_target_boundary,conditioning,encoding,H,K,feedback_index/time,oracle_intervention,train/eval_commit,evidence。unknown明确标。每个技术结论有历史源码函数和元数据引用。

## 独占交付
- experiments/history_audit_20260909/shared_memory_timing.zh-CN.md
- experiments/history_audit_20260909/shared_memory_designs.csv
- experiments/history_audit_20260909/oracle_interventions.csv


## 共同要求

本轮仅整理已完成实验的原始结果和历史实现，为论文的实证研究提供可核验事实。用户要求manager负责规划、分工、验收，具体工作由你执行。阅读 MAM AGENTS.md、任务发布要求，再读 RMBench/AGENTS.md 和 docs/guidelines/{code,rmbench,experiments}.md；设计讨论背景只读 /root/Documents/task-state-vla-paper/ROADMAP.zh-CN.md。不要派生subagent。

工作区：mam workspace add <你的task UUID> --repo RMBench --base 681a928e266818bb430674c547b6458793bda227，使用自己登记的worktree/分支和独立环境。以其现有一键脚本创建一次即可。历史源码优先 git show <实际commit>:<path>；确需checkout时，只在自己的干净worktree及MAM登记分支上切换该历史commit，回到交付base再写文档，严禁切换共享主checkout/创建游离worktree或分支。记录converter/train/eval各自commit，不能用当前HEAD推断旧行为。metadata若记录dirty而缺少当时patch，明确证据缺口；现存历史补丁归档在 MAM/.local/archives/3b1cdd78-c7b9-4174-a132-497b485fcfaf/，只按已知线索定向查找。

原始结果现在位于 /mnt/public/xcj/Projects/RMBench/eval_result（/root/Projects是其别名），包含新导入wuwen-11旧实验及本集群三组完成结果。只读所有共享结果/模型/数据；本轮不删除、移动、改写原始metadata，也不修改算法或启动训练、仿真eval/真机任务。只允许必要的小型CPU解析/统计；不重复hash所有视频/模型，不做无目的全盘扫描。旧路径 public3→public 只用作定位候选，并记录原始路径和本地解析路径；找不到的checkpoint不下载大模型。缺失commit先核本地对应repo/对象；确实缺失时报告manager，已有证据工作继续。

证据格式：以相对 eval_result 路径作为run标识；逐run区分训练seed、评测seed、ckpt step、样本数、骨干/LoRA、预测长度H、实际执行K、input lag、memory内容和实现开关。信息缺失填unknown，不猜。成功数/episode数来自实际结果，尽可能对diagnostics核对ID和seed；格式无逐集记录时降级为summary证据。两eval seed均值不等于两个训练seed；重构前后复跑不等于独立训练；相同数据复制不当独立run。同骨干、字段/训练/执行协议相同才能把差异归于单个设计变量。

代码实现事实引用 repo + 完整commit + 文件/函数（可加行号）；配置/命令/diagnostics引用具体文件。清楚区分：源码及产物已证实、日志支持但实现缺失、推测/待核实。区分记忆内容和编码/条件结构/时序；soft/hard按实际代码含义命名；H与K与history间隔分别记录。输出简洁中文，表格为主，避免长篇复述历史对话。旧README事实可引用，但不能作为原始结果和历史代码双重已核实的替代品。

交付只写自己任务分配的 experiments/history_audit_20260909/ 文件，其他主题/原主表及旧README由相应负责人处理。可提交一个必要的短解析脚本（如果确实帮助重建表格），不用构建通用框架。文档小结包括：已经看到的现象、哪些比较有混杂、仍缺哪一个关键证据。不要预设论文结论，不把工程bug自动当科学发现。

完成后提交自己的文档commit、清理临时解析文件，发布 MAM report.md，首行为 task_revision: <最新发布revision>，包含完成/未完成、workspace、commits:块（RMBench: 完整commit）、成果路径、关键发现/缺口；等待manager合入及归档。报告和任务均通过mam task publish发布。中间进度直接commentary，manager可读取，无需探索Codex通信接口。
