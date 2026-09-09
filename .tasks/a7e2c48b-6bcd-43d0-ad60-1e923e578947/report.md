task_revision: 58dc9d6edb06af2b8641175200d3a6aba940741e

完成：历史总账、原始成功数核验、主表对应和差异清单已提交。复用原 workspace/分支；只改三份分配文件，原始结果只读，无 GPU、无新 task/worktree、无派生 agent。待 manager 验收合入及归档。

workspace: /mnt/public/xcj/Projects/workspace/a7e2c48b-6bcd-43d0-ad60-1e923e578947/RMBench
branch: task/a7e2c48b-6bcd-43d0-ad60-1e923e578947
commits:
  RMBench: 38499ed5ecec1d2f5a2522d968db8d23f7b7074a

成果路径（相对于 RMBench）：
- experiments/history_audit_20260909/run_index.csv
- experiments/history_audit_20260909/inventory.zh-CN.md
- experiments/history_audit_20260909/table_discrepancies.md

覆盖及验证：23 组、184 个唯一规范 _result.txt 叶，排除 132 个 W&B 符号链接镜像入口；全部 184 行的成功数、条数、比率与 eval_log 核对通过，116 叶的 diagnostics ID/seed/成败与日志一致。73 个主表格建立精确逐叶映射，其中两个 DP 格有日志/汇总边界；26 叶没有详细表精确路径引用。CSV 的详细表引用已改为精确反引号路径匹配，防止前缀误关联。git diff --cached --check 通过，commit 后 worktree 干净，临时解析脚本已清理。

关键发现和未补齐的历史证据：
- DP swap_blocks 日志 15/99、缺 episode 50；cover_blocks 0/99、缺 episode 38。历史汇总/README 采用 100-rollout，保留边界，不修改主表数字。
- put-back LoRA 55% 的历史 raw/schema_latch 路径缺失（详细表 67、86、87）；现有 27/50 不可替代。put-back full 68% 可关联 default_full_b32 独立叶。
- 主表 swap_blocks × pi05_full 的 14% 无对应导入 baseline 叶，需补证；Paper/Repro Mem-0 也保持独立来源边界。
- 两条旧 bridge 路径应更新为 unified_runtime_reproduction_20260908 规范叶；“其余七项未完成”叙述过时，九项均完成。
- 五个 m1mix formal_metadata 仍写 running，但 100-episode 产物完整；这是旧状态而非在运行判断。
- dirty 按文件限定：12 叶仅 .gitignore，4 叶仅 experiments/dp_key_state/README.md；注明范围，不据此否定所有机制事实。未把这些文档/忽略规则改动标成未知源码 patch 缺口。
- 同 checkpoint 的 diagnostics/bridge re-eval 不计作独立训练；两个 eval seed 的均值不计作两个训练 seed。机制源码研究由其他执行者负责。

未完成：本任务的三份交付无剩余实施工作；上述缺失原始证据尚未补齐，已明确列入交付待核对项，不自行重跑或替换结果。
