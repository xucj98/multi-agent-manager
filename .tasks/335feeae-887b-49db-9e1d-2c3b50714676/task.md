# 旧实验整理的独立复核与综合证据索引

## 目标
用户委托manager安排subagent整理wuwen-11导入旧实验，恢复历史实现细节，为action-chunk VLA低维记忆论文提供事实。你负责独立review和综合索引，manager负责裁决与最终集成。先审已交付token专题，后续其余三组正式输入由manager追加到本任务并发布；最终交付必须覆盖全部四组，不能把首组review当整体完成。

先读MAM/AGENTS.md与README任务/交付/工作区规则、RMBench/AGENTS.md及docs/guidelines/{code,rmbench,experiments}.md。研究背景只读 /root/Documents/task-state-vla-paper/ROADMAP.zh-CN.md。不要派生agent。

## 工作区
mam workspace add 335feeae-887b-49db-9e1d-2c3b50714676 --repo RMBench --base 9faa19d4fa03d66619cc09ce70b2803c35b499e1
沿用登记分支。后续在自己的worktree用git merge --no-edit合入本任务明确给出的其他三组交付commit，保留原作者提交可追溯；不要切共享主checkout，也不要修改别人worktree。独立核对原始eval文件和历史git show；本轮不启动GPU/训练/正式评测，不修改原始结果/metadata/模型或算法。

## 已冻结输入
- Token专题：MAM task 9265c564-bbd5-4076-be45-163cf6fa6bc9；requirements 8da86ef2b2675840491c98fd5e7ae6a847237347；report 0f8bc1ad871e5777982f28058335e2dc365ee2e6；RMBench commit 9faa19d4fa03d66619cc09ce70b2803c35b499e1。
- 总账：task a7e2c48b-6bcd-43d0-ad60-1e923e578947；requirements 58dc9d6edb06af2b8641175200d3a6aba940741e；report 81d65f9d4b2580589bed48d9244ac8ea0807037f；RMBench commit 38499ed5ecec1d2f5a2522d968db8d23f7b7074a（23组184叶、73格主表映射）。请在自己的worktree合入该commit并纳入独立核验。
- Shared时序：task 0a70d0ce-181c-47dc-96b0-f3b1c8d04c10，待追加。
- 早期设计：task c1bc0678-1326-40fb-94db-8cad5278feab；requirements 4da889d1af7db4fb8c917b57e434e6c160d1229a；report e3c067c5ea06193ae585f28c058bb2b561abc3c0；RMBench commit cd56932ce5da6c56c5bdb465ab38a6696b2ddbfc。请在自己的worktree合入并纳入独立核验。

原始结果 /mnt/public/xcj/Projects/RMBench/eval_result；当前初查23组184个含_result的叶（你须根据最终总账判断覆盖，勿把这个初查数字写成验收结论）。

## Review要求
1. 按每个源task已发布要求验收成果。检查关键数字能否追到run及原始_result/diagnostics/eval_log；检查聚合均值分母、eval seed与train seed、复制结果和独立实验的区分。不要重复hash视频/模型。对核心比较独立算数字/核ID即可。
2. 技术结论须可追到converter/train/deploy各自真实commit/config；不能把当前HEAD当历史代码。dirty按具体受影响文件分析，缺失数据采集commit不自动否定clean训练/部署实现。反过来也不能用clean提交证明dirty eval未记录的行为。
3. 优先复核按钮有无×K、serial/parallel与soft/hard实际含义、full/serial目标时间与反馈索引、Oracle替换位置、跨任务排序和属性获取窗口。区分语义内容、表示/条件路径、训练时序、H/K与闭环反馈；编码可包括归一化/解码，查关键不一致是否影响结论。
4. 失败诊断明确类别定义、分母和覆盖范围；日志标签不能被提升成已经证实的因果机制。仅调整同checkpoint K与重训练不同方案要分开。某些早期0%因实现bug受污染必须限定具体run，不一概归因所有失败。
5. shared不同eval seeds来自同一个训练seed，不算独立训练；非shared seed42与shared seed0不能当单因素对照。Oracle不默认上界，下降不自动证明计划时钟。
6. swap_T 60–70%、count/high-low若无原始实验，明确未找到和查找范围，不补写预设结论。
7. 不追求表格全是已确认；unknown、缺失checkpoint/版本和不可比项应保留。对scope有分歧报manager裁决。
8. 可在自己worktree对文档/CSV作证据明确的小修正，记录来源；大问题先反馈manager，不能默默换研究目标。最终检查CSV结构和本地结果引用存在性，对历史/public3路径单独标原址。

## 综合交付
所有成果在 experiments/history_audit_20260909/：
- 合入四组专题成果，写 README.md（尽量200行内）：索引、覆盖/证据口径、统一的设计维度、最多三条“已确认现象—可能解释—还缺的最小对照”。清楚标哪些只支持实现敏感性、哪些已形成受控比较，不强凑统一科学结论。
- 写 review.zh-CN.md：review范围与固定版本、发现/修正/待核实表、验收结论。避免重复贴整份专题。
- experiments/README.md 只添加新审计入口，并修正“重构其余七项未完成”的过时文字（九项均已完成且记录在unified_runtime组）；本轮不未经裁决改主表历史成功率，矛盾进入既有table_discrepancies。
不修改论文库稿件或roadmap，不实施新memory schema。

先完成token独立review；若其余输入尚未到，简短报告阶段结果后等manager追加，不要通过猜测完成其他组。全部四组完毕后提交最终commit，发布report.md（首行 task_revision: 最新revision，包含commits块RMBench完整commit，完成/未完成、workspace/成果/关键问题）。清理自用临时文件，保留工作区待manager集成归档。


Review fixed source delivery:
{
  "task": "9265c564-bbd5-4076-be45-163cf6fa6bc9",
  "task_revision": "8da86ef2b2675840491c98fd5e7ae6a847237347",
  "report_revision": "0f8bc1ad871e5777982f28058335e2dc365ee2e6",
  "commits": {
    "RMBench": "9faa19d4fa03d66619cc09ce70b2803c35b499e1"
  }
}

Source task:

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

Source report:

task_revision: 8da86ef2b2675840491c98fd5e7ae6a847237347

完成：已完成 Rearrange 的按钮字段、state token 与动作边界历史实现审计；未启动训练、评测或真机任务，原始 `eval_result`、checkpoint 与数据均保持只读。

workspace: `/mnt/public/xcj/Projects/workspace/9265c564-bbd5-4076-be45-163cf6fa6bc9/RMBench`

commits:
- RMBench: `9faa19d4fa03d66619cc09ce70b2803c35b499e1` (`docs: 整理 Rearrange 状态 token 历史审计`)

成果：
- `experiments/history_audit_20260909/rearrange_tokens.zh-CN.md`
- `experiments/history_audit_20260909/rearrange_token_designs.csv`
- `experiments/history_audit_20260909/rearrange_failure_evidence.csv`

关键发现：converter/训练的共享实现 `f40d3d02244fca2551e4c3fb97ea76647b3f3841` 和无按钮训练实现 `a3e91e87d1d96f159b7289cd87a0401372d616d0` 均为 clean。state 输入滞后固定 20 帧、H=50；Hard 是训练目标在 guard offset 后的 repeat-last holding，非 stop head、mask、可变长度或运行时重查询。serial 训练用 GT 当前 state token、推理用 masked argmax；部署在执行 K 个动作前缓存预测 state，故下一次查询时实际 memory 年龄为 K。按钮有无是 3-field 与 2-field 参数树的独立重训练，K=30 为 145/200 对 78/200，K=50 为 92/200 对 75/200，不能解释为同 checkpoint 输入开关。

证据边界/缺口：原始数据 metadata 记载 clean 的 `a4d318ca456d75de4e2c85d0ed80b4160e2e55a3`，但本地缺少该 Git object；这仅构成 source-data collection code 缺口，不影响已由其余 clean 历史 commit 和产物支持的实现事实。eval metadata 未记录 `git_status`，因此其 clean/dirty 状态为 unknown；未发现与本机制相关的 dirty metadata 或缺失 patch。诊断只定义了有效 press 与浅下压阈值，已按仍下降、抬升/回程失败、未按直接离开均未单列，计数按 unknown 报告。

验证：提交前 `git diff --cached --check` 通过；两份 CSV 的引用字段数检查通过；提交后 `git show --stat` 与 `git status --short` 核对通过，工作树干净。
