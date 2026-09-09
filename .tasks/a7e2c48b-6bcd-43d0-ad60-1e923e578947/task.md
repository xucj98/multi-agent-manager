# 历史实验总账与结果核验

## 目标和分工
你负责所有导入旧实验的run总账、metadata定位和与主表的对应关系；另外三个执行者分别研究token/buttons、shared-memory时序、早期状态内容实现。你不需要深入重做其源码研究。

## 工作
1. 遍历当前 eval_result 的实验组和真实run（可识别旧多层目录）；记录范围/缺组/重复入口/同run副本/smoke和debug，但不清理。先发简短目录覆盖与run计数。
2. 建立 run_index.csv：至少 run_path,exp_group,task,variant,checkpoint_original,checkpoint_local,checkpoint_step,train_commit,eval_commit,train_seed,eval_seed,episodes,successes,success_rate,evidence_level,source_files,notes；若有太多异构字段保持最小列并unknown。查验_result/summary/diagnostics间一致性，记录缺文件、未完成和旧running标记（别凭旧状态判还在运行）。视频只记录数量及位置，不全量解码。
3. 核对 experiments/README.md 主表及详细行与真实run。建立一格→哪些run（例如均值两个seed）映射，明确Paper/Repro/本集群m1mix/重构后是不同来源。首轮不改原主表数字，任何矛盾写入table_discrepancies.md。三组本集群结果已完成验收，做关联就好；指出原主表描述仍称其余7项未完成的文字过时。
4. 关注文档缺run、产物有run但未入索引，swap_T相关线索、rearrange_blocks_eval_diagnostics、eval_diagnostics_smoke、pi05_full_key_state_repro这些非标准组。正式/探索/调试标清，不能删除。

## 独占交付文件
- experiments/history_audit_20260909/run_index.csv
- experiments/history_audit_20260909/inventory.zh-CN.md（短述覆盖、数据质量和使用方式）
- experiments/history_audit_20260909/table_discrepancies.md（主表引用行/当前值/原始证据/建议，含待核对项）

基于原始文件计算成功率，合理处理不同记录格式；无需把不含metadata的每个视频当独立run。预计优先完成核心正式组，再补长尾；发现信息缺口尽早告知。

## 共同要求

本轮仅整理已完成实验的原始结果和历史实现，为论文的实证研究提供可核验事实。用户要求manager负责规划、分工、验收，具体工作由你执行。阅读 MAM AGENTS.md、任务发布要求，再读 RMBench/AGENTS.md 和 docs/guidelines/{code,rmbench,experiments}.md；设计讨论背景只读 /root/Documents/task-state-vla-paper/ROADMAP.zh-CN.md。不要派生subagent。

工作区：mam workspace add <你的task UUID> --repo RMBench --base 681a928e266818bb430674c547b6458793bda227，使用自己登记的worktree/分支和独立环境。以其现有一键脚本创建一次即可。历史源码优先 git show <实际commit>:<path>；确需checkout时，只在自己的干净worktree及MAM登记分支上切换该历史commit，回到交付base再写文档，严禁切换共享主checkout/创建游离worktree或分支。记录converter/train/eval各自commit，不能用当前HEAD推断旧行为。metadata若记录dirty而缺少当时patch，明确证据缺口；现存历史补丁归档在 MAM/.local/archives/3b1cdd78-c7b9-4174-a132-497b485fcfaf/，只按已知线索定向查找。

原始结果现在位于 /mnt/public/xcj/Projects/RMBench/eval_result（/root/Projects是其别名），包含新导入wuwen-11旧实验及本集群三组完成结果。只读所有共享结果/模型/数据；本轮不删除、移动、改写原始metadata，也不修改算法或启动训练、仿真eval/真机任务。只允许必要的小型CPU解析/统计；不重复hash所有视频/模型，不做无目的全盘扫描。旧路径 public3→public 只用作定位候选，并记录原始路径和本地解析路径；找不到的checkpoint不下载大模型。缺失commit先核本地对应repo/对象；确实缺失时报告manager，已有证据工作继续。

证据格式：以相对 eval_result 路径作为run标识；逐run区分训练seed、评测seed、ckpt step、样本数、骨干/LoRA、预测长度H、实际执行K、input lag、memory内容和实现开关。信息缺失填unknown，不猜。成功数/episode数来自实际结果，尽可能对diagnostics核对ID和seed；格式无逐集记录时降级为summary证据。两eval seed均值不等于两个训练seed；重构前后复跑不等于独立训练；相同数据复制不当独立run。同骨干、字段/训练/执行协议相同才能把差异归于单个设计变量。

代码实现事实引用 repo + 完整commit + 文件/函数（可加行号）；配置/命令/diagnostics引用具体文件。清楚区分：源码及产物已证实、日志支持但实现缺失、推测/待核实。区分记忆内容和编码/条件结构/时序；soft/hard按实际代码含义命名；H与K与history间隔分别记录。输出简洁中文，表格为主，避免长篇复述历史对话。旧README事实可引用，但不能作为原始结果和历史代码双重已核实的替代品。

交付只写自己任务分配的 experiments/history_audit_20260909/ 文件，其他主题/原主表及旧README由相应负责人处理。可提交一个必要的短解析脚本（如果确实帮助重建表格），不用构建通用框架。文档小结包括：已经看到的现象、哪些比较有混杂、仍缺哪一个关键证据。不要预设论文结论，不把工程bug自动当科学发现。

完成后提交自己的文档commit、清理临时解析文件，发布 MAM report.md，首行为 task_revision: <最新发布revision>，包含完成/未完成、workspace、commits:块（RMBench: 完整commit）、成果路径、关键发现/缺口；等待manager合入及归档。报告和任务均通过mam task publish发布。中间进度直接commentary，manager可读取，无需探索Codex通信接口。
