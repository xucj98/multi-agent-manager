task_revision: bca77f60f3100e453aec62f63cc95a396bdae596

最高优先级补核已完成（2026-09-10 04:20前）：

- `/mnt/public/xcj/Projects/RMBench/data/rearrange_blocks/demo_clean_state/` 已恢复50集 scene_info.json、language_annotation.json、seed.txt、metadata/，来源 `zx-data:/mnt/public3/xcj/rmbench/data/rearrange_blocks/demo_clean_state/`；原样metadata 157,107 bytes，checksum dry-run零差异。empty_mat_side、block1_place、press_return、language segment_4 均可读。
- `/mnt/public/xcj/Projects/RMBench/data/put_back_block/demo_clean_state/` 同样恢复50集小标注，源为上述raw根的put_back_block目录；332,576 bytes，checksum dry-run零差异。origin_mat_name、center_pick、center_place、button_return 均可读。
- 两目录各有 `metadata/robot_edge_samples.json`：使用wuwen-11已有h5py 3.12.1，仅只读100个HDF5的 joint_action/{vector,left_arm,left_gripper,right_arm,right_gripper} 首末两行；保留shape/dtype/源路径/文件字节与mtime，未读取或复制图像数组。样本输出分别266,064 / 266,136 bytes，源输出与目标SHA256一致：rearrange `f8a08cf2ebbd9ee68f57d476da3f0c17d55cefb04ee7954f2c125d65a75bf494`；put-back `df0941a6377fe9a139a9a7b375ed6cf514c033e42b0a479b0536f1a013d46464`。
- 与data已发布报告f48bf331逐项对照，100/100集均验证 raw_N=converted_N+1；state[:2,:14]=raw[:2]、action[0,:14]=raw[1]、action[-2:,:14]=raw[-2:]（raw转float32）最大误差全部0。详细逐集结果在各自 `metadata/robot_edge_comparison.json`。raw总帧20,153 / 17,638，converted仍是原20,103 / 17,588，未重复复制或重转converted。
- 优先补核期间暂停了自有battery进程组13148及第一链控制进程13126，保证不启动cover/swap；既有drawer传输可收尾。补核完成后恢复原job。

完成与未完成：四份所需 converted 均已在 zx-data 定位，本地标准 cache 无对应资产，正在经 nx 两条顺序链恢复。未改代码或使用 GPU；尚未完成传输的目录不可用于训练。

来源统一为 `zx-data:/mnt/public3/xcj/cache/huggingface/lerobot/<repo_id>/`，正式目标为 `/mnt/public/xcj/cache/huggingface/lerobot/<repo_id>/`：

| repo_id | 源常规文件总字节 | episodes / frames | metadata 与字段 |
|---|---:|---:|---|
| swap_blocks_demo_clean_state_shared_memory | 10,171,411,893 | 50 / 29,920 | demo_clean_state；phase(4)、initial_empty_tray、first_origin_tray |
| cover_blocks_demo_clean_state_shared_memory | 14,014,462,306 | 50 / 50,904 | demo_clean_state；phase(6)、red_pos、green_pos、blue_pos |
| battery_try_demo_clean_state_shared_memory | 7,936,631,538 | 50 / 32,626 | demo_clean_state；phase(4)，后续 trial 为 optional |
| drawer_sorting_x1pro_shared_memory_s2m_15hz_v2 | 5,820,563,245 | 119 / 333,657 | 15 Hz；state/actions 32维，机器人14维；completed_layers、drawer_target、memory_action_valid；119 parquet+357视频 |

三个仿真目录均含 source_data_config/key_state_config，分别明确 task_config=demo_clean_state、source_dir=data/<task>/demo_clean_state；含32维 observation.state/action 和 key_state input/target/mask、三路内嵌图像。逐集详细数值边界和任务事实另在原始 `scene_info.json`，语言分段在 `language_annotation.json`：已只读确认 `zx-data:/mnt/public3/xcj/rmbench/data/<task>/demo_clean_state/` 下各50集、micro_stages 的 start_frame/end_frame 可读。为完整保留这些小标注，随链只复制上述两JSON、seed.txt及metadata/至 `/mnt/public/xcj/rmbench/data/<task>/demo_clean_state/`，不复制原始视频/HDF5。

drawer：本地两个旧模型 `pi05_x1pro_drawer_sorting_s2m_{full_state,serial_soft}/s2m_{full_state,serial_soft}_v2_seed42/metadata/datasets.json`、train_config.yaml 均引用同一119集 v2 repo_id。前序 source_data_config 和 conversion_audit 记录原始 `/mnt/public3/datasets/x1pro/table_clean`、134 tagged/119 converted/15 skipped、30→15Hz；converted 的 meta/key_state/phase_layout.json 还含逐集 source_episode、annotation_path、数值 intervals。完整 copied metadata 将原样保留。不是本地5集 offline回放素材。

运行：第一链 drawer→cover，nx PID 13126，MAM job 85fa2611-8fcb-4447-9c93-6598c526fd99，2026-09-10 04:06:49+08:00启动；第二链 battery→swap，nx PID 13148，job 82ab0258-2847-416e-8ea3-bf14c36501cb，04:07:54启动，间隔65秒。每链限速 --bwlimit=10m、--partial --append-verify；每项复制后在原链串行执行 checksum dry-run及episode/frame/文件计数，及时报ready。

workspace：/mnt/public/xcj/Projects/workspace/e248b5a1-7d82-49cc-9b80-95e7181563e4；无代码commit。完工将归档job，摘要验证结果后清除此workspace的asset-transfer临时目录。
