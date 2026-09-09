task_revision: 4da889d1af7db4fb8c917b57e434e6c160d1229a

完成与未完成：
- 已完成 put-back 逐步 key-state 内容/获取窗口与八个 variant 的 run 证据；严格标明未实现 chunk-level target。
- 已完成 cover 的 label-id schema、attribute acquisition/write/latch 时序、每 action rollout 更新和两项正式 eval 的核验。
- 已完成早期 Pi0 LoRA/full、Pi0.5 full/repro、DP 的主要模型/数据/训练/执行条件对照，以及编码与 K 的混杂说明。
- 已完成 swap_T 60–70% 与 count/high-low 定向查找；未找到可核实的正式 pose-memory 或双状态实验记录。
- 未完成且已明确记录：早期 put-back LoRA 的 train/converter commit、resolved train config、seed 与当时 source patch 不在保存 metadata 中。

workspace：
- /mnt/public/xcj/Projects/workspace/c1bc0678-1326-40fb-94db-8cad5278feab/RMBench

commits:
  RMBench: cd56932ce5da6c56c5bdb465ab38a6696b2ddbfc

成果路径：
- experiments/history_audit_20260909/early_state_designs.zh-CN.md
- experiments/history_audit_20260909/early_designs.csv
- experiments/history_audit_20260909/unverified_leads.md

验证结果：
- CSV 36 行均以相对 eval_result 路径定位；逐行复核了对应 eval_log.txt 的 episode 数和 success 数。
- 仅写入上述三份独占 RMBench 文件；原始 eval_result、模型和数据保持只读。

关键发现/缺口：
- put-back 的已保存 LoRA eval 中 default 为 27/50，phase_lag20 为 9/50；这些 variant 同时会改变获取窗口或 input/target 时序，不能简化为纯 memory-bit 对照。
- cover 两个 label-id schema 为 0/100 与 1/100；no-phase run 的 eval seed 集合缺 100004、多 100100，不能据此断言 rich memory 或 phase 的必要性。
- Pi0.5 repro 在同一训练 checkpoint 下 K=15/20/30/50 的均值为 13.5/14.5/43.0/42.0%，是执行 K 敏感性而非独立训练或 memory 对照。
