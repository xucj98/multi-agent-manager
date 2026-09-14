# HF-fixed rearrange 三批正式结果独立核验

源任务 0acf5d43-91b6-4171-b727-e3fe0f7e7939，报告 revision 229e70551bd306b9b15b6d28e0149cd9fc8e38c8。按 AGENTS.md 操作，仅 CPU/只读原始证据核查；不得启动 GPU、重跑评测、修改冻结运行树或论文。必要代码分析使用独立 worktree。

独立核对 HF-fixed eval0/1/2 三批各100连续终态、身份/seed/配置/源代码与 checkpoint、matching smoke 门禁、进程正常收尾、原始 rolling evidence 完整性及 HF-fixed 时序：每5完成行更新状态，K30普通动作不被 probe actions 替换，无 event clear/replan，action/probe RNG隔离。不要仅复述执行者收据；复算原始结果及关键合同，并说明检查覆盖范围。已有完整 checkpoint 检查无需重复加载多GB模型。

源报告给出 90/91/87，已接受新协议 matched baseline 86/81/87。从原件按相同 eval/环境seed 配对，提供四格计数（都成功、仅baseline成功、仅fixed成功、都失败）、每eval及总成功率差、失败类型变化和实际probe/普通action计数。配对只控制已记录条件，不把单训练模型结论推广到九任务或宣称重规划有效。

C3 runtime: /mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914，原件位于其 RMBench/eval_result/memory_chunk_20260910；源任务 formal_first_layer_j_20260914/receipts 中有三份 formal_hf_fixed_rearrange_evalseed{0,1,2}_terminal_audit_20260914.json。参考你已完成的基线 review 8274a212-a7de-42af-8b6d-e5cd2670f3d2 和论文 /root/Documents/task-state-vla-paper/docs/analysis/accepted_hf_results_20260914_baseline.json。

交付：发布 concise report、独立核验 JSON/原件哈希及本地留存、配对统计，明确阻断项及准入范围。Manager 最终验收前不能加入已接受结果；原协议52批保持分开。本任务不负责运行中的 HF-event，也不授权后续实验。
