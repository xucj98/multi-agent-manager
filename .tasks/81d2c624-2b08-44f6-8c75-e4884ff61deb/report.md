task_revision: 718aa229393479caa407fcaf9e72f63df463bf40

# Pi0.5 base 与仿真数据恢复记录（进行中）

完成与未完成：完成有界本地/旧集群只读定位，以及两份转换数据的来源和详细子任务边界核验；base 与状态版数据正在按 nx←zx-data 链路直接恢复到共享 cache。未训练、未加载模型、未占 GPU、未修改代码。

已确认来源和字段：

- rearrange 源为 `zx-data:/mnt/public3/xcj/cache/huggingface/lerobot/rearrange_blocks_demo_clean_state_shared_memory/`（4.4G，50 episodes、20,103 frames、50 parquet）；`meta/rmbench/source_data_config.yaml` 明示 `task_config: demo_clean_state` 和 `save_path: ./data/rearrange_blocks/demo_clean_state`，`key_state_config.yaml` 明示 `source_dir: data/rearrange_blocks/demo_clean_state`。它保留 `phase`、`empty_mat_side`、`button_press_status` 的标签/target/mask，以及 `block1_place`、`press_return`、`language_annotation.segment_4` 的边界和 guard offset。
- put-back 源为 `zx-data:/mnt/public3/xcj/cache/huggingface/lerobot/put_back_block_demo_clean_state_shared_memory/`（4.7G，50 episodes、17,588 frames、50 parquet）；对应两份 metadata 分别明示 `task_config: demo_clean_state`、`save_path: ./data/put_back_block/demo_clean_state` 和 `source_dir: data/put_back_block/demo_clean_state`。它保留 `phase`、`origin_mat` 的标签/target/mask，以及 `center_pick`、`center_place`、`button_return` 的边界。
- 两份均有 `meta/info.json`、`meta/rmbench/source_data_config.yaml`、`meta/rmbench/key_state_config.yaml`、50 条 `episodes.jsonl` 和 50 条 `episodes_stats.jsonl`；feature schema 将 key-state 编码同时保存在 `observation.state`/`action` 与 `observation.key_state_*`。无独立 `meta/stats.json`，也不含视频（`total_videos: 0`）。这已建立状态版来源与详细边界的可追溯链；series/events 语义充分性由 dataagent 继续核对，当前未默认复制 raw 视频或其他大 raw 数据。

恢复目标与运行记录：

- Pi0.5 官方 base：`zx-data:/mnt/public3/cache/openpi/openpi-assets/checkpoints/pi05_base/` → `/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base/`，12.44 GB，MAM job `ca979f09-cf4e-4bdc-be19-535901bd762b`，`wuwen-nx-aic` PID `12528`，`--partial --append-verify --bwlimit=10m`。
- rearrange 目标：`/mnt/public/xcj/cache/huggingface/lerobot/rearrange_blocks_demo_clean_state_shared_memory/`；put-back 目标：`/mnt/public/xcj/cache/huggingface/lerobot/put_back_block_demo_clean_state_shared_memory/`。二者以同一条顺序 rsync 链恢复，启动于 `2026-09-10T03:27:48+08:00`，MAM job `08383c80-cf08-4d52-939c-916b6eebdeba`，`wuwen-nx-aic` 实际 wrapper PID `12597`，限速 10 MB/s；其启动晚于 base 超过 60 秒，当前总并发为两条。

待完成验证：传输结束后，对三项执行 source→target `rsync --checksum --dry-run`，检查 base manifest/payload，并复核数据目录、metadata、feature schema、episode/frame 计数；随后归档 nx jobs、清理已归档的本机中转 partial。无代码交付 commit。
