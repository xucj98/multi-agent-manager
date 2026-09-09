task_revision: 718aa229393479caa407fcaf9e72f63df463bf40

# Pi0.5 base 与仿真数据恢复完成

完成与未完成：已从 `zx-data` 直接恢复 Pi0.5 base 和两份 `demo_clean_state` LeRobot 数据到共享 cache；未训练、未加载模型、未占 GPU、未修改代码。series/events 的训练语义充分性仍由 dataagent 核对，未默认复制 raw 视频或其他 raw 大数据。

资产与实际路径：

- Pi0.5 base：`zx-data:/mnt/public3/cache/openpi/openpi-assets/checkpoints/pi05_base/` → `/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base/`；12,441,746,507 bytes、21 文件。`params/_CHECKPOINT_METADATA`、`_METADATA`、`_sharding`、`manifest.ocdbt`、`commit_success.txt` 均可读。
- rearrange：`zx-data:/mnt/public3/xcj/cache/huggingface/lerobot/rearrange_blocks_demo_clean_state_shared_memory/` → `/mnt/public/xcj/cache/huggingface/lerobot/rearrange_blocks_demo_clean_state_shared_memory/`；4,621,077,053 bytes、50 episodes、20,103 frames、50 parquet、50 条 episode/stat records。
- put-back：`zx-data:/mnt/public3/xcj/cache/huggingface/lerobot/put_back_block_demo_clean_state_shared_memory/` → `/mnt/public/xcj/cache/huggingface/lerobot/put_back_block_demo_clean_state_shared_memory/`；4,985,910,084 bytes、50 episodes、17,588 frames、50 parquet、50 条 episode/stat records。

状态版来源与边界：两份目标的 `meta/rmbench/source_data_config.yaml` 均明示 `task_config: demo_clean_state`，且对应 `key_state_config.yaml` 的 `source_dir` 指向 `data/<task>/demo_clean_state`，未使用 `demo_clean`。rearrange 保留 `phase`、`empty_mat_side`、`button_press_status`、key-state input/target/mask、guard offset，以及 `block1_place`、`press_return`、`language_annotation.segment_4` 边界；put-back 保留 `phase`、`origin_mat`、key-state input/target/mask，以及 `center_pick`、`center_place`、`button_return` 边界。

完整性验证：三项均执行 `rsync -aicn --delete --omit-dir-times` 的 source→target checksum dry-run，结果均为 `status=0, changes=0`。这同时确认目标不缺文件且无额外差异；目标 metadata、feature schema、episode/frame/parquet 计数亦已复核。

传输与收尾：base 从 `2026-09-10T03:22:45+08:00` 启动，数据链从 `03:27:47+08:00` 启动，间隔 5 分 02 秒；均以 `--partial --append-verify --bwlimit=10m` 运行。base 总耗时 30:56、平均 6.39 MB/s；rearrange 8:54、8.62 MB/s；put-back 15:39、5.29 MB/s。MAM 已归档 `wuwen-nx-aic` 的实际 job/PID：base `ca979f09-cf4e-4bdc-be19-535901bd762b` / `12528`，数据 `08383c80-cf08-4d52-939c-916b6eebdeba` / `12597`。旧本机 1.9 GB partial 已清理，保留传输和校验日志于 workspace 的 `asset-recovery/nx-transfer/`。

workspace、各库交付 commit：无代码修改，无 commit。
