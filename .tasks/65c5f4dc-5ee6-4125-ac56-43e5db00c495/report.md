task_revision: 4a361aad54b1227584800736402c8e07ecb98492

# 正式 eval 结果归并与清理交付

## 完成与未完成

已完成：将正式评测结果归并为 RMBench 下恰好三组、5+9+1 个 formal run；清理
RMBench 旧 eval/smoke/重复入口和 `robot-bridge/eval_result`；更新三份实验 README。
没有未完成的 formal run，也没有重新评测或占用 GPU。

三个最终绝对路径：

```text
/mnt/public/xcj/Projects/RMBench/eval_result/mem0_official_m1mix_sdpa_reproduction
/mnt/public/xcj/Projects/RMBench/eval_result/unified_runtime_reproduction_20260908
/mnt/public/xcj/Projects/RMBench/eval_result/mem0_swap_blocks_single_final_eval_20260908
```

每个最终 leaf 都有 100 条 diagnostics、唯一且连续的 episode ID 0–99；summary 和
`_result.txt` 的成功数/成功率一致。旧 recorder 格式的官方 5 项和单任务 1 项没有逐
episode JSON，但其完整 diagnostics 是对应的真实 episode 记录。

| group | run | success |
| --- | --- | ---: |
| 官方 m1mix SDPA | `observe_and_pickup_rollout100_wuwen1_gpu1` | 6/100 |
| 官方 m1mix SDPA | `rearrange_blocks_rollout100_wuwen1_gpu4_retry2` | 84/100 |
| 官方 m1mix SDPA | `put_back_block_rollout100_wuwen1_gpu2_retry2` | 100/100 |
| 官方 m1mix SDPA | `swap_blocks_rollout100_wuwen1_gpu5_retry2` | 80/100 |
| 官方 m1mix SDPA | `swap_T_rollout100_wuwen1_gpu0_retry2` | 8/100 |
| 统一 runtime | `pi05_rearrange_full_formal_20260908` | 92/100 |
| 统一 runtime | `pi05_rearrange_serial_formal_20260908`（f2） | 34/100 |
| 统一 runtime | `dm05_swap_blocks_history_exact_r5_formal_20260908` | 16/100 |
| 统一 runtime | `dm05_swap_blocks_nohistory_f1_formal_20260908` | 12/100 |
| 统一 runtime | `mem0_put_back_block_formal_20260908`（template） | 100/100 |
| 统一 runtime | `mem0_observe_and_pickup_formal_20260908` | 5/100 |
| 统一 runtime | `mem0_rearrange_blocks_formal_20260908` | 86/100 |
| 统一 runtime | `mem0_swap_T_formal_20260908` | 11/100 |
| 统一 runtime | `mem0_swap_blocks_formal_20260908` | 77/100 |
| 单任务 Mem-0 | `swap_blocks_step30000_fa2_formal_20260908T052504Z` | 47/100 |

## workspace、各库交付 commit

- MAM workspace：`/mnt/public/xcj/Projects/workspace/65c5f4dc-5ee6-4125-ac56-43e5db00c495`
- RMBench worktree：`/mnt/public/xcj/Projects/workspace/65c5f4dc-5ee6-4125-ac56-43e5db00c495/RMBench`
- RMBench branch/commit：`task/65c5f4dc-5ee6-4125-ac56-43e5db00c495` /
  `8be4ec9982304edb52f2895f845e1d74aa0c1791`（`记录正式评测结果归并`）
- robot-bridge 没有代码或 Git 文档修改；共享 `eval_result` 的原地迁移已由任务授权。

## 文件完整性与迁移映射

迁移前在任务 workspace 的 `result_migration_audit/pre_migration_manifest.json` 记录了
15 个 formal leaf 和所需共享 provenance 的每个常规文件路径、大小、SHA-256。迁移使用
同一设备上的 rename；manager 独立重新读取 **2,209 个文件（含 71 个视频）**，SHA-256
零差异。`post_migration_manifest.json`、`post_migration_validation.json`、
`post_migration_link_recheck.json` 和 `final_cleanup_validation.json` 记录了对应比较、
100-episode 交叉验证和清理后结构。

- 官方组将共享批次资料收进 `_provenance/source_batch_context/`；5 个 `stdout.log`
  都改为本组内有效链接，旧 `mem0_official_m1mix_sdpa_formal100_4827_20260907`
  日志入口已不再被引用。
- 统一 runtime 从 robot-bridge rename 的映射为：DM05 history exact-r5、DM05 no-history
  f1、Mem-0 rearrange、swap_T、swap_blocks 分别迁至上表五个新增 canonical leaf；Pi0.5
  full/serial、Mem-0 putback/observe 保留原 canonical leaf。
- 单任务 leaf 从
  `mem0_swap_blocks_single_20260907/swap_blocks_step30000_fa2_formal_20260908T052504Z`
  迁至 `mem0_swap_blocks_single_final_eval_20260908/`；组级 training metadata 位于新组
  `_provenance/`。历史 metadata 的绝对路径文字未改写。

清理后 `RMBench/eval_result` 仅有上述三组，formal directory 计数为 5、9、1。所有
软链接中只剩 5 条官方组内 `stdout.log` 链接，均有效且不解析到旧 eval 目录或旧 worktree。
manager 已确认本机与 wuwen-1 没有训练/评测进程。

## 删除项与遗留项

已删除：RMBench 的 `dm05_bf16_20260905T184500Z`、`dm05_formal_20260906`、
`dm05_metadata_20260905T174500Z`、`dm05_swap_blocks_native_allrows_v2_20260905_smoke`、
`mem0_official_m1mix_sdpa_formal100_4827_20260907`、三个旧 m1mix symlink 入口、
`mem0_swap_blocks_single_20260907` symlink、`pi05_drawer_offline_replay_20260908`、
`pi05_rearrange_shared_memory_representation`，以及统一组的
`pi05_rearrange_full_recorder_smoke_20260908T053908Z`；`robot-bridge/eval_result` 已删除。
删除回执在 `result_migration_audit/cleanup_receipt.json`。

未由本任务删除：旧 worktree 和源树本身、模型和数据。它们的结果目录依赖已解除；cleanup
agent 已完成模型/data/assets 持久化并收到 manager 的旧树清理通知。任务 workspace 中的
manifest/validation JSON 依据 manager 指令保留至其集成和归档，再统一清理。
