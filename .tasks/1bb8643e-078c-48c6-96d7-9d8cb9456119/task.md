# 独立论文审稿

你是独立论文审稿人，模型必须为GPT-6 ultra。本任务使用空白上下文创建，不继承作者/Manager的讨论。先阅读MAM AGENTS.md、README核心原则/任务管理/执行与交付及.local说明，再mam task show本TASK-ID。只阅读此任务提供的冻结审稿材料，不阅读Manager对论文定位的讨论、其他agent对论文的评价或会话日志。你可以自主核对主要文献与原始证据。

## 材料
本任务workspace下review_packet/提供paper.pdf、LaTeX源码、references.bib、evidence/accepted_results_20260913.json及历史结果的审计文件，另有packet_manifest.json记录材料哈希。材料是单独冻结副本，无需修改/构建业务repo；不修改作者主树。如需临时分析，写在本任务workspace。把审稿范围、稿件PDF SHA256和证据检查范围写入report。

## 审稿要求
先以RA-L审稿视角独立阅读PDF，再按需查source/supplement/主要文献。不要预设接受、拒绝或作者希望的结论。给：
1. 你理解的论文问题和实际贡献，论文应按方法类还是实证类评价，当前新意是否成立。
2. 有依据的优点、主要/次要问题、结论与证据的对应，定位具体页/节/表。区分已观察现象、可能解释、因果证据、尚未完成的计划；检查训练seed/eval seed/失败分母/统计单位。
3. 当前稿件的整体建议与置信度；对于进行中研究，除指出缺失结果，还判断哪些已有推断有价值/不成立，哪项缺口最关键。
4. 按信息价值排序的最小补充实验清单；说明什么相反结果会推翻解释、哪些实验可以删减，不仅建议扩大所有样本或堆更多模型。
5. 写清哪些问题可通过论文修订解决，哪些必须新增实验。独立判断所提改进是否足够受控、有无遗漏的混杂。

不要改论文，不发外部消息。提交中文详细review到本任务workspace/review.zh-CN.md；MAM_ROOT/.tasks/TASK-ID/report.md写摘要与路径，并mam task publish --file report。完成当前工作后正常结束turn，不轮询等待Manager。你无需创建子agent。

## Manager验收与保存（2026-09-13）
独立审稿已完成，原始review未修改并保存到论文docs/reviews/20260913-independent-review.zh-CN.md；Manager逐项裁决与正文修订在14993b9。原5页审稿PDF和当前6页修订稿分开标识，未声称获得重新审稿通过。整个冻结packet+原review+算术核验共32文件已保存到/root/Documents/task-state-vla-paper/docs/reviews/20260913-frozen-review-materials.tar.gz，SHA256 4276c2a7e09cf62ced40aa9681995abc7a5bbd99d336e78e7b7035ff60e0768f；Manager逐文件读取tar并校验与源相同，可清理task workspace后归档。GPT-6 ultra仅完成此独立审稿，后续工程仍terra max。
