task_revision: eaf7b6018cfcbe8f974c5c85ef41f286a28092ac
status: complete
workspace: /mnt/public/xcj/Projects/workspace/0a70d0ce-181c-47dc-96b0-f3b1c8d04c10/RMBench
branch: task/0a70d0ce-181c-47dc-96b0-f3b1c8d04c10
commits:
  RMBench: b0dc76f3ea68c56f642d65caab3897be335393a2

成果路径：
- `experiments/history_audit_20260909/shared_memory_timing.zh-CN.md`
- `experiments/history_audit_20260909/shared_memory_designs.csv`
- `experiments/history_audit_20260909/oracle_interventions.csv`

完成：
- 按历史 converter/train/eval 提交还原 full 与 serial 的样本时序、编码、teacher forcing、H=50/K=30 反馈位置及 soft boundary 含义。
- 审计两个 Oracle run：full 为 query 前及每个已执行 action 后的 dense GT cache；serial 同时替换 current action condition 与 next-query token。记录 93/100→82/100 和 36/100→79/100，未将 Oracle 作为上界或单变量因果证据。
- 汇总 shared 四任务 full/serial random 的两 eval-seed 结果、rearrange fixed/random 的不可比点，以及非shared fixed-20 与 prop-history 的参考行；CSV 共 26 个设计行和 2 个 Oracle 干预行。
- 根据最新规则逐文件说明 dirty：`.gitignore` 和 README-only 记录仅限定 provenance；prop-history put_back 的两个 dirty DP 源文件缺 patch，已限定为 DP 路径 unknown，未泛化到已核实的 pi05 converter/eval 路径。

关键缺口：
- 历史 eval worktree 的 git status 未留存；旧 `demo_clean_eval.yml` 不在旧提交中；Oracle 与离线标签没有逐样本分布匹配证据；shared 四任务 fixed-20 尚无完成结果。

验证：CSV 用标准库解析，44 个设计 result run 与 2 个 Oracle run 的 `diagnostics_summary.json` 成功数均逐项核对；提交前已通过 `git diff --cached --check`。
