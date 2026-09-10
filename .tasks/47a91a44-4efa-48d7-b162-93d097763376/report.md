# 已完成：BF16验证临时副本清理

## 清理

- 已删除、未迁移：`/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000`（清理前约 4.9GB）。
- 目标是普通目录，删除前没有任何登记 worktree 的 `user_checkpoints` 专用软链接或其他软链接解析到该目录；`mam job list --attention` 为空。
- 删除后仅以 `rmdir` 依次移除了空的 `rearrange_full_key_state_30k_bf16`、`precision_validation` 和 `user_checkpoints` 父目录；没有遇到或删除其他内容。

## 留存核验

- 源 FP32 checkpoint 仍在：`/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000`，已核验 `_CHECKPOINT_METADATA` 和 `metadata/command.txt`。
- 正式 BF16 结果仍在：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/precision_rearrange_full_row30_bf16_100ep_seed0`，已核验 `final_review_0100.json` 与 `paired_seed_results.json`。
- 导出留痕仍在上述正式结果的 `checkpoint_metadata/`，已核验 `export_command.txt`、`export_validation.json` 和 `inheritance.json`；历史运行 command/metadata 均未改动。

## 文档交付

- workspace：`/mnt/public/xcj/Projects/workspace/47a91a44-4efa-48d7-b162-93d097763376/RMBench`
- branch：`task/47a91a44-4efa-48d7-b162-93d097763376`
- base：`6ce7290feca710a9b41adb45f8b647853d6bf389`
- commit：`c10ecbb9d8f1e5641402c000c54f6149299bd53e`（记录已验收清理及 FP32/导出 metadata 留痕位置）

## 验证

- 全程未启动训练、评测或 GPU 进程，也未修改 OpenPI 训练树或现有环境。
- 已检查 OpenPI 已跟踪代码：没有 `user_checkpoints` 引用；checkpoint 管理仅操作调用方显式传入的目录，因此未因假想重建风险修改脚本。
- RMBench 文档 diff 通过 `git diff --check`，提交后 worktree 干净。
