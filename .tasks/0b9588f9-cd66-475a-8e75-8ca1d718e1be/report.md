# 九任务覆盖与 seed 差异证据审计：交付简报

已完成只读事实审计，对应已发布 task revision `0e4ce2152921b430bef51dcd60f6dd755c6565fb`。

完整证据在：

`/mnt/public/xcj/Projects/workspace/0b9588f9-cd66-475a-8e75-8ca1d718e1be/evidence.md`

交付内容包括：

- RMBench 官方九任务、TMC 分类及本地 task-code 对照；
- 每任务 `demo_clean_state`、converted cache、Memory-v1 binding/sidecar/builder、新 20k checkpoint 的就绪度与缺口；
- `swap_T` 连续 pose/rotation、`press_button` 计数等任务特有 schema 缺口；
- 当前可加载 Memory-v1、legacy Pi0.5、Mem-0、DM05 模型资产与不可直接横比的边界；
- 完整 100-episode、固定 eval seed 0 的 s0/s1/s2 原始结果路径、均值/范围/sample SD 与逐 episode paired 计数；
- 三 eval seed（300 episode）完成度：full 组均未齐；no-memory 仅 train s1/s2 完整，s0 不可混入 300-episode 比较。

核验读取了官方主来源 <https://arxiv.org/html/2603.01229v3>、`RMBench/envs/`、`RMBench/helper/auto_eval_dp.sh`、`RMBench/data/`、LeRobot cache、`openpi/examples/rmbench/`、`openpi/checkpoints/`、`RMBench/eval_result/memory_chunk_20260910/` 和 `history_audit_20260909/`。100-episode结果以每 leaf 的 `diagnostics_summary.json` 和 `episode_diagnostics.jsonl` 交叉复算；cache 的 `meta/info.json` 复核 episode/frame 总数。

本轮没有修改代码、数据、模型、台账或既有评测结果；未创建 worktree，未启动训练、评测、下载或长进程。
