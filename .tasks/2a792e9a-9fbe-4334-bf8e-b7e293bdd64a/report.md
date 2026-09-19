# press_button / blocks_ranking_try 数据与 N 接入进度

## 代码与来源合同

- RMBench worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/RMBench`，当前提交 `74db6317bb4b690abc7b49258c5a2d402861f1f0`。
- OpenPI worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/openpi`，当前提交 `2bcf3a1551445d73777a959d5050872a4333f5af`。
- 来源与标签合同草案：`RMBench/docs/press_button_blocks_ranking_source_contract_draft.zh-CN.md`。N 只使用当前图像、14D robot state 和 raw `q(t+1)` action；scene、事件、候选答案和 hidden ranking 不进入 N rows。S/J 字段、目标时间和连续表示仍由 Manager 裁决。
- RMBench 编译检查和 OpenPI converter/config 测试已通过（OpenPI `12 passed`，`git diff --check` clean）。

## press_button：数据、转换和正式 N 已完成

canonical source：`RMBench/data/press_button/demo_clean_state/`。

- `metadata/acceptance_audit.json` 为 PASS：50 selected planning/replay episodes，seeds `410000..410049`，26,029 raw HDF5 observation rows，三路同步 RGB，physical press 均由 qpos threshold event 确认，保留评测 seed 区间不存在。
- N LeRobot repo：`/mnt/public/xcj/cache/huggingface/lerobot/press_button_demo_clean_state_no_memory`。验收为 50 episodes、25,979 query rows、14D state/action、三路 RGB、memory absent、source scene labels 不复制到 rows。
- norm stats：`/mnt/public/xcj/Projects/openpi/assets/pi05_rmbench_no_memory/press_button_demo_clean_state_no_memory/norm_stats.json`，sha256 `1690aec41ac1a07ff4ea6913463429c943cefb5df83ea23ce1c04e921128f9f0`。
- 真实 CPU loader batch 证据：`RMBench/data/press_button/demo_clean_state/metadata/no_memory_cpu_loader_batch.json`，batch 32，state `[32,32]`，action `[32,50,32]`，三路 `[32,224,224,3]`，均 finite，key-state/memory fields absent。
- 50-step N smoke 已通过：`/mnt/public/xcj/Projects/openpi/checkpoints/press_button_n_smoke_2bcf3a1_20260915/.../50`；50/50 optimizer steps finite，checkpoint-only CPU restore PASS。
- 正式 N seed0、bs32、H50/K30、20k 已完成并 finalized：`/mnt/public/xcj/Projects/openpi/checkpoints/press_button_n_formal_2bcf3a1_20260915/pi05_rmbench_no_memory/memory20k_2bcf3a1_press_button_n_s0/20000`。CPU restore 证据 `.../checkpoint-transfer-20260920/press_cpu_restore.json`：51 leaves、3,353,433,872 elements、BF16、finite、shape complete、source reads rejected。MAM job `275739b6-d6f2-498c-a67f-1fc02beadca6` 已归档。

## blocks_ranking_try：canonical 数据审计 PASS，N 转换仍在运行

canonical source：`RMBench/data/blocks_ranking_try/demo_clean_state/`。

- 独立审计证据：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/checkpoint-transfer-20260920/blocks_ranking_dataset_audit.json`，状态 PASS。
- 50 planning successes、50 successful replays；deterministic seed stream `420000..420049`，68,083 raw HDF5 rows，186 physical button events，186 terminal feedback events；reserved eval seed absent；`hidden_permutation_or_target_ranking: not_recorded`。
- N conversion 已在 `wuwen-1` CPU 启动，MAM job `8c8cebda-18ba-4b0a-a4a9-033ef598a327`，PID `2987214`，命令使用 `convert_rmbench_no_memory_to_lerobot.py --episode-count 50`，目标 repo `blocks_ranking_try_demo_clean_state_no_memory`。截至本报告更新，进程仍运行、manifest 尚未写完；不得读取中间目录作为完成数据，也未启动 ranking 正式训练。

## 转换完成后的受控步骤

1. 确认 conversion 进程退出且 `meta/rmbench_no_memory/conversion_manifest.json` 完整，回读 50 episodes、每集 state/action 与 source HDF5 对齐、三路 RGB 解码、memory absent 和 provenance 不进 rows。
2. 按 `examples/rmbench/README.md` 用 CPU 生成 ranking norm stats，并运行真实 CPU batch/data-loader gate（batch 32、H50、model action dim 32、无 memory fields）。
3. 通过 gate 后，仅在 `wuwen-1` 空闲单卡做 50-step N smoke；保存 receipt、loss/grad finite 和 checkpoint-only recovery 证据。
4. smoke 通过后才可启动 ranking N seed0、bs32、H50/K30、20k；启动前登记新的 MAM job，保存独立 formal root、日志和启动收据。

当前没有新增训练 seed、没有把 hidden ranking 注入策略，也没有启动 blocks 正式训练。
