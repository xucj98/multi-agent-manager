task_revision: 2be46de7c7c336b70d10af75e041e1f589766ca3

# 资产可用性调查

完成与未完成：完成了已记录路径的只读、定向检查；未加载模型、未扫描全部数据 episode、未查 GPU、未实施或启动训练。历史索引中 full 为 93/100、serial-soft 为 36/100；serial checkpoint 的训练 metadata 为 `query_stride: 20`，该条历史评测记录的 `K_execution` 为 30。

workspace、各库交付 commit：`/mnt/public/xcj/Projects/workspace/320c8c68-c21c-4189-8f56-4d217ad071b4` 仅只读，无 worktree、代码改动或交付 commit；RMBench、openpi、robot-bridge 均只读取规范、配置与 metadata。

验证结果与成果位置：

| 对象 | 可用性与证据 | 可立即用于 |
| --- | --- | --- |
| Rearrange full / serial 30k | `/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000` 与 `/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_rearrange_state_token_boundary_ablation/shared_memory_serial_soft_seed0/30000` 均存在；`_CHECKPOINT_METADATA`、训练/转换/source metadata、`params` manifest/sharding、非空 payload 和 norm stats 均可读，params 无不可读普通文件。full norm stats 为 `assets/rearrange_blocks_demo_clean_state_shared_memory/norm_stats.json`，serial 为 `assets/rearrange_blocks_state_token/norm_stats.json`。 | 已训 checkpoint 的路径/metadata 引用和后续 eval 准备；未做加载验证。 |
| Pi0.5 base 初始化 | 训练配置引用 `gs://openpi-assets/checkpoints/pi05_base/params`；已知本地缓存 `/root/.cache/openpi/openpi-assets/checkpoints/pi05_base/{params,assets}` 不存在。 | 不可直接启动新的 Pi0.5 训练。 |
| Rearrange / put_back 训练数据 | 记录的原始目录 `/mnt/public/xcj/Projects/RMBench/data/rearrange_blocks/demo_clean_state`、`/mnt/public/xcj/Projects/RMBench/data/put_back_block/demo_clean_state` 均不存在；`/root/.cache/huggingface/lerobot/rearrange_blocks_demo_clean_state_shared_memory` 与 `/root/.cache/huggingface/lerobot/put_back_block_demo_clean_state_shared_memory` 也不存在。checkpoint metadata 仍保留 source/key-state schema 与 norm stats。未扩大搜索范围。 | 不能据当前本机已知路径重训；需要恢复原始或转换数据。 |
| Drawer S2M v2 | 两个 30k checkpoint 均存在：`/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_x1pro_drawer_sorting_s2m_full_state/s2m_full_state_v2_seed42/30000`、`/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_x1pro_drawer_sorting_s2m_serial_soft/s2m_serial_soft_v2_seed42/30000`；params、metadata、各自 norm stats 可读。两份 `metadata/datasets.json` 都记录 repo `drawer_sorting_x1pro_shared_memory_s2m_15hz_v2`、119 episode、root `/root/.cache/huggingface/lerobot/drawer_sorting_x1pro_shared_memory_s2m_15hz_v2`，但该 converted cache 不存在。原始对应目录 `/mnt/public/datasets/x1pro/table_clean` 存在，离线 replay 指定的 5 个 episode 的 tags/sort、轨迹 JSON 和三路视频均可读。 | checkpoint 可供后续加载验证；5-episode offline replay 仍需恢复/转换该 LeRobot cache 或调整输入路径。 |
| wash-cup 标注 | `/mnt/public/datasets/x1pro/wash-cup/annotation_layers.json` 存在、可读、JSON 合法（顶层 `layers`）。已检查数据根的常见 report 名称和现有项目文档，未发现可引用的筛选统计报告；未重新扫描 episode，故有效数为 unknown。 | 可作为筛选规则输入；尚不能据本调查给出训练/5ep offline 的有效样本数。 |

阻塞项（最多 3 个）：

1. Pi0.5 base 的已知本地初始化缓存缺失。
2. Rearrange 与 put_back 的已记录原始/converted 训练数据路径均缺失。
3. Drawer 的 converted cache 缺失；`/mnt/public3` 根目录也不存在，不能确认文档所述 `/mnt/public3 -> /mnt/public` 历史镜像。wash-cup 暂无可引用审计统计。

证据：`RMBench/experiments/history_audit_20260909/run_index.csv`、两套 checkpoint 的 `metadata/` 与 `assets/`、`RMBench/docs/x1pro_drawer_sorting_state_transition_design.md`、`robot-bridge` 的 unified-runtime manifest；以上均为本次只读检查。
