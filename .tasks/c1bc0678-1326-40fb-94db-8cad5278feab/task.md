# 早期状态设计与属性记忆

## 范围
实验组 put_back_block_key_state_ablation、cover_blocks_key_state_design、pi0_key_state_encoding_ablation、pi0_key_state_baseline、pi0_full_key_state、pi05_full_key_state（含repro）、dp_key_state；pi0/pi05 full/lora和DP baselines按模型/数据/训练条件核对主要对照，不重复总账逐run统计。共享memory具体实现和rearrange token/buttons由另两agent负责。

## 工作
1. Put-back：default、mat_first、mat_hash_p50、phase_lag20等实际样本构造差异。属性何时可观察/何时写memory/何时用于动作；已完成per-step与未实现chunk-level建议严格区分。整理这些对照是否同时改变监督、输入lag、动作边界或编码。
2. Cover：实际schema字段/跨观察阶段的记忆获取；状态简化/扩充各variant、phase与属性依赖，不能因为效果差就说必须rich memory。
3. 早期pi0/DP与pi05：骨干、LoRA/full、数据demo数、训练seed/step、字段编码与运行协议是否对齐，哪些主表差异不能直接作为memory效果。encoding one-hot/标量/token按实际commit核查。必要时仅查代表variant代码+有效config。
4. 根据现有文件定向寻找swap_T的初始position/rotation memory模型或评测；用户报告约60–70%目前是待核验线索，找不到正式记录明确说明，不填成结果。也查count/high-low双状态是否存在已完成实验；若仅讨论/方案同样标未验证。
5. 每个结论给出run证据、历史源码commit/函数、时序图或表。优先解释内容/获取窗口和sample构造，不写泛泛FSM科普。

## 独占交付
- experiments/history_audit_20260909/early_state_designs.zh-CN.md
- experiments/history_audit_20260909/early_designs.csv
- experiments/history_audit_20260909/unverified_leads.md（swap_T/count等查找范围、找到/缺失原始证据，不扩大到未授权重跑）


## 共同要求

本轮仅整理已完成实验的原始结果和历史实现，为论文的实证研究提供可核验事实。用户要求manager负责规划、分工、验收，具体工作由你执行。阅读 MAM AGENTS.md、任务发布要求，再读 RMBench/AGENTS.md 和 docs/guidelines/{code,rmbench,experiments}.md；设计讨论背景只读 /root/Documents/task-state-vla-paper/ROADMAP.zh-CN.md。不要派生subagent。

工作区：mam workspace add <你的task UUID> --repo RMBench --base 681a928e266818bb430674c547b6458793bda227，使用自己登记的worktree/分支和独立环境。以其现有一键脚本创建一次即可。历史源码优先 git show <实际commit>:<path>；确需checkout时，只在自己的干净worktree及MAM登记分支上切换该历史commit，回到交付base再写文档，严禁切换共享主checkout/创建游离worktree或分支。记录converter/train/eval各自commit，不能用当前HEAD推断旧行为。metadata若记录dirty而缺少当时patch，明确证据缺口；现存历史补丁归档在 MAM/.local/archives/3b1cdd78-c7b9-4174-a132-497b485fcfaf/，只按已知线索定向查找。

原始结果现在位于 /mnt/public/xcj/Projects/RMBench/eval_result（/root/Projects是其别名），包含新导入wuwen-11旧实验及本集群三组完成结果。只读所有共享结果/模型/数据；本轮不删除、移动、改写原始metadata，也不修改算法或启动训练、仿真eval/真机任务。只允许必要的小型CPU解析/统计；不重复hash所有视频/模型，不做无目的全盘扫描。旧路径 public3→public 只用作定位候选，并记录原始路径和本地解析路径；找不到的checkpoint不下载大模型。缺失commit先核本地对应repo/对象；确实缺失时报告manager，已有证据工作继续。

证据格式：以相对 eval_result 路径作为run标识；逐run区分训练seed、评测seed、ckpt step、样本数、骨干/LoRA、预测长度H、实际执行K、input lag、memory内容和实现开关。信息缺失填unknown，不猜。成功数/episode数来自实际结果，尽可能对diagnostics核对ID和seed；格式无逐集记录时降级为summary证据。两eval seed均值不等于两个训练seed；重构前后复跑不等于独立训练；相同数据复制不当独立run。同骨干、字段/训练/执行协议相同才能把差异归于单个设计变量。

代码实现事实引用 repo + 完整commit + 文件/函数（可加行号）；配置/命令/diagnostics引用具体文件。清楚区分：源码及产物已证实、日志支持但实现缺失、推测/待核实。区分记忆内容和编码/条件结构/时序；soft/hard按实际代码含义命名；H与K与history间隔分别记录。输出简洁中文，表格为主，避免长篇复述历史对话。旧README事实可引用，但不能作为原始结果和历史代码双重已核实的替代品。

交付只写自己任务分配的 experiments/history_audit_20260909/ 文件，其他主题/原主表及旧README由相应负责人处理。可提交一个必要的短解析脚本（如果确实帮助重建表格），不用构建通用框架。文档小结包括：已经看到的现象、哪些比较有混杂、仍缺哪一个关键证据。不要预设论文结论，不把工程bug自动当科学发现。

完成后提交自己的文档commit、清理临时解析文件，发布 MAM report.md，首行为 task_revision: <最新发布revision>，包含完成/未完成、workspace、commits:块（RMBench: 完整commit）、成果路径、关键发现/缺口；等待manager合入及归档。报告和任务均通过mam task publish发布。中间进度直接commentary，manager可读取，无需探索Codex通信接口。
