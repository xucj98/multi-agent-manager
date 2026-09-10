# State-VLA 论文式实验台账

task_revision: `3a953bca393b051fcf497e8b280d3adce12c437a`

## 交付

- 独立 RMBench worktree：`/mnt/public/xcj/Projects/workspace/00107546-75fb-42ae-916d-81b7c3d3c186/RMBench`
- branch：`task/00107546-75fb-42ae-916d-81b7c3d3c186`
- task base：`6ce7290feca710a9b41adb45f8b647853d6bf389`
- 交付 commit：`d4b2e11`（`Document State-VLA experiment ledger`）

仅修改 `experiments/memory_chunk_20260910/README.md` 顶部的统一导航，并新增
`experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`；未改代码、训练树、其他实验说明、
metadata 或结果目录。

## 台账内容

- 以研究问题、预先检验、受控变量、指标、实际结果和结论边界组织 F0、保存精度、drawer offline、
  Q2、能力基线和 wash。
- F0 明确记录 row30/20/1/50 的 92/86/21/38；结论限定为旧 checkpoint、固定协议下的探索。
- BF16 部署验证记录 92 vs 92、14 个配对不一致，并明确两臂沿 BF16 加载路径，未冒充 FP32 计算比较。
  按用户最新确认和 task 47 已发布报告，临时副本已清理，`user_checkpoints` 已移除；原 FP32、正式结果和导出 metadata 链接保留。
- 旧 drawer 两模型各 5 集 offline 只记录 MAE/离线回归，不写作闭环成功率。
- Q2 明确共同 H50/K30/row30、phase `t+j+1` 对 `t+30`、共同 mask 和其他目标不变；强调 full/serial
  不是单变量表示对照。逐行列出 12 个 Q2、2 个能力基线和 2 个 wash 模型的配置、训练 seed、状态、
  训练目录和评测目录。
- 以已发布 owner 报告的 06:32/06:51/06:53 快照区分远端完成并 CPU 验收的 8 个模型与本机仍训练的 8 个模型；
  新模型尚无 GPU smoke/formal 成绩，所有 16 个评测计划路径均显式标为“计划，尚未创建”。Q1/Q3 只链接既定计划。

## 核验

- `git diff --check` 通过；提交后 RMBench worktree 干净。
- 台账逐项核对：4 个 F0 正式结果、16 个新模型行、8 个完成训练状态、8 个训练中状态。
- 已核对现有 checkpoint、结果和 metadata 目标均存在；16 个计划评测目录均不存在，故不会被误读为已完成结果。
- 全程仅做文档和路径只读核对，未启动 GPU、训练、评测或模型加载，未复制运维日志。

Manager 可据此裁定论文叙事；后续实验 owner 应在对应行补充匹配 smoke、formal 结果、配对差异和结论边界。
