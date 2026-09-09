task_revision: b1e9ac8d5651033a6659a0b33d1e20bc63e43e66

完成：已在独立 MAM worktree 合入并独立验收 token、总账、早期状态设计和 shared 时序四个冻结交付；新增综合索引与 review，更新 `experiments/README.md` 中过时的 bridge 完成状态。未启动 GPU、训练、仿真/真机评测，未改写原始 `eval_result`、metadata、模型或算法。

未完成：无本任务约定的文档交付项。下列历史证据仍按 unknown/待补证保留，而非作为本轮缺交付：DP 两个 99 条日志、缺导入的旧 put-back 55% 原叶、Paper/Repro Mem-0 原始叶、token source-data collection commit、早期 put-back LoRA 训练 provenance、shared 四任务 fixed-20，以及 swap_T/count-high-low 的正式实验记录。

workspace: `/mnt/public/xcj/Projects/workspace/335feeae-887b-49db-9e1d-2c3b50714676/RMBench`

commits:
- RMBench: `e31d14fe0818235d471b371924ea30c273e75c7a` (`docs: add consolidated history audit review`)

合入的固定专题版本：token `9faa19d4fa03d66619cc09ce70b2803c35b499e1`；总账 `38499ed5ecec1d2f5a2522d968db8d23f7b7074a`；早期设计 `cd56932ce5da6c56c5bdb465ab38a6696b2ddbfc`；shared 时序 `b0dc76f3ea68c56f642d65caab3897be335393a2`。

成果：
- `experiments/history_audit_20260909/README.md`
- `experiments/history_audit_20260909/review.zh-CN.md`
- 四个专题及其 CSV：总账、Rearrange token、早期状态设计、shared 时序/Oracle。

验证：解析六份 CSV（184/5/30/36/26/2 行）；总账 184 行与排除 `wandb/` 镜像后的 184 个规范 `_result.txt` 叶逐一对应，所有 `source_files` 存在；36 个早期、44 个 shared、4 个 Oracle/baseline 与 30 个失败诊断引用均可定位。`git diff --cached --check`、新增 Markdown 本地链接检查通过；四个固定交付 commit 均为最终 commit 的祖先，RMBench worktree 提交后干净。

关键边界：button 有/无是不同参数树的重训练，两个 eval seeds 不等于两个 train seeds；K 同时影响执行间隔和 feedback 年龄。Oracle build/替换位置不一致，不能作为单变量上界。历史 eval 的 clean/dirty 未记录时保持 unknown；未找到 swap_T 60–70% 或 count/high-low 的正式证据。
