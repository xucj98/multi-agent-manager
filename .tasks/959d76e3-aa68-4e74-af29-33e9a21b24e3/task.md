# 管理交接审计（2026-09-21）
用户要求先理解论文与当前实验，和用户梳理后再推进后续。模型固定 GPT 5.6-terra，reasoning max。
先读 MAM AGENTS/README 核心与任务管理/.local/README，再 mam task show 本 959d76e3-aa68-4e74-af29-33e9a21b24e3。创建自己的 RMBench worktree：mam workspace add 959d76e3-aa68-4e74-af29-33e9a21b24e3 --repo RMBench --base HEAD；阅读 AGENTS 及实验规范。仅只读审计旧任务、结果、模型、远端状态，不启动训练/评测，不终止进程、不删除文件、不改旧任务或共享论文。报告写自己 .tasks/959d76e3-aa68-4e74-af29-33e9a21b24e3/report.md 并 mam task publish --file report，支持资料写自己的 workspace。可通过 SSH 只读访问集群，但先读 .local 对应集群说明。避免递归遍历巨型模型/视频目录，优先最新 report 与 JSON/日志定位。
明确区分计划、owner 声称、原始证据核验、Manager 已验收；按固定训练模型与评测批次分开计数，旧30k/新20k/episode-reset HF不混表。给精确路径、关键数字、状态差异及建议。尽早反馈最关键发现；无需改代码或大规模重跑验收。不要再派 subagent。

## 范围：科学评估
完整阅读 /root/Documents/task-state-vla-paper 论文源文件与 docs/EXPERIMENT_PLAN、RESEARCH_POSITIONING、RESULT_ANALYSIS_AND_FOLLOWUPS、STATE_PREDICTION_FREQUENCY、reviews/20260915-plan-independent-review；查看最新MAM cba8b004科学审稿报告及用户研究决策记录。独立判断：核心主张、先前实验如何回答问题、已支持/尚不支持的假设、哪些计划保留/降级/应补最小区分实验；特别单seed、S/J整套协议混杂、HF固定vs边界刷新LR、J forecast≠已发生状态、V成本。不要外网扩展文献或新跑实验。交付简洁科学裁决建议和关键风险；最新数由另一个agent核查，不重复原始数据遍历。

## 2026-09-21 Manager必修项：算术与证据边界

不做新扫描/实验，只修订report并发布后结束：
1. pooled成功数差误写成pp：rearrange fixed-baseline +14/300=+4.67pp，event-baseline +4/300=+1.33pp，event-fixed -10/300=-3.33pp；put-back分别-3/300=-1.00pp、+43/300=+14.33pp、+46/300=+15.33pp。全文所有+43pp/+4pp等相同错误一起纠正（逐eval分母100的pp保持）。
2. 删除“只有四类重复轨迹/100 seed只是四种初态/信息量接近4”等过强推断。已证明的是origin分组内首动作、结果、步数重复，不证明完整RGB/物理初态或全轨迹等同，不能由此算有效独立样本数；报告依赖性与需分层即可。
3. cover N 0/100正常completed和unspecified_failure不证明adapter错误，也不能说不是科学null。它是有效观察到的零成功、诊断分类不足。保留cover为预定验证任务；HF扩展依赖其J入口及整体HF可比性，不能仅因N为0新增必须过的故障门槛或暂停正常J/S覆盖评测。
4. 初态字段核对一致而expert final pose不同，是provenance差异，不等于完整初态已经发现不一致；将“未核对完整RGB/内部RNG”与“已核对相同初始pose”区分。最直接的新证据是干预之前first actions已不同，请以它作为协议可比性的优先诊断依据。
5. 不建议用结果去重删除正式评测episode或改变分母；保留全量，新增分组描述与独立运行设计。
