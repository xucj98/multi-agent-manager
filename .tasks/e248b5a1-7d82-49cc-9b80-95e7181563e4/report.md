task_revision: 005a59f9eb285aff70c11d9e436170be4d9abc13

完成与未完成：四份后续 converted（合计37,943,068,982 bytes）、五任务原始小标注、首批两任务100集HDF5机器人首末行补核全部完成。逐项ready已通报。未改业务代码、未训练、未加载模型、未使用GPU；训练语义由data/train owner验收。

四份 converted 的确切源均为 `zx-data:/mnt/public3/xcj/cache/huggingface/lerobot/<repo_id>/`，正式目标均为 `/mnt/public/xcj/cache/huggingface/lerobot/<repo_id>/`：

| repo_id | 常规文件字节数 | episodes / 实际parquet行 | 开始→checksum ready（2026-09-10，+08:00） |
|---|---:|---:|---|
| drawer_sorting_x1pro_shared_memory_s2m_15hz_v2 | 5,820,563,245 | 119 / 333,657 | 04:06:49→04:19:57 |
| battery_try_demo_clean_state_shared_memory | 7,936,631,538 | 50 / 32,626 | 04:07:54→04:25:13 |
| swap_blocks_demo_clean_state_shared_memory | 10,171,411,893 | 50 / 29,920 | 04:25:13→04:43:02 |
| cover_blocks_demo_clean_state_shared_memory | 14,014,462,306 | 50 / 50,904 | 04:19:57→04:44:51 |

完整性：四项 `rsync -aicn --delete --omit-dir-times` source→target checksum dry-run均退出0、零差异。各集parquet实际行数、列名与info/episodes逐项一致，episode/stat records及文件数一致。仿真各50 parquet、58常规文件、三路内嵌图像；drawer为119 parquet+357视频、486常规文件。episodes_stats.jsonl原样保留，未做模型加载/归一化验证。

来源与字段：

- 三个仿真source_data_config明确task_config=demo_clean_state，key_state_config明确source_dir=data/<task>/demo_clean_state；均含32维observation.state/action及key_state input/target/mask。swap为phase(4)/initial_empty_tray/first_origin_tray；cover为phase(6)/red_pos/green_pos/blue_pos；battery准确任务名battery_try，phase(4)，后续trial可选。未用demo_clean。
- drawer准确repo_id与本地两旧模型 `policy/pi05/checkpoints/pi05_x1pro_drawer_sorting_s2m_{full_state,serial_soft}/s2m_{full_state,serial_soft}_v2_seed42/metadata/datasets.json` 一致。source/key-state config和conversion audit与两模型快照逐字节一致。state/actions为32维，机器人14维；completed_layers/drawer_target及memory_action_valid保留。原始来源/mnt/public3/datasets/x1pro/table_clean，134 tagged/119 converted/15 skipped、30→15Hz；meta/key_state/phase_layout.json有119集source_episode、annotation_path、数值intervals。恢复的是完整119集v2，不是本地5集offline素材。

五任务原始小标注统一在 `/mnt/public/xcj/Projects/RMBench/data/<task>/demo_clean_state/`。源为 `zx-data:/mnt/public3/xcj/rmbench/data/<task>/demo_clean_state/`；只恢复scene_info.json、language_annotation.json、seed.txt、metadata/（各5文件），各有50集并通过源目标checksum。swap/cover/battery小包237,554 / 465,627 / 264,910 bytes，数值micro-stage共700 / 1,415 / 688，采集config/command与对应converted metadata逐字节一致。按最新要求移动了已启动链生成的自有小目录，移动前后SHA256保持、无目标冲突、无重传、未打断rsync，旧空镜像父目录已清理。

首批补核（已由Manager验收）：

- rearrange_blocks小标注157,107 bytes，含empty_mat_side、block1_place、press_return、language segment_4；put_back_block小标注332,576 bytes，含origin_mat_name、center_pick/center_place/button_return。
- 两任务各有 `metadata/robot_edge_samples.json`：wuwen-11现有h5py 3.12.1只读导出50集joint_action/{vector,left_arm,left_gripper,right_arm,right_gripper}的shape/dtype/首末两行/源路径/文件字节/mtime；未传HDF5图像。文件分别266,064 / 266,136 bytes，源输出与落盘SHA256一致：rearrange `f8a08cf2ebbd9ee68f57d476da3f0c17d55cefb04ee7954f2c125d65a75bf494`；put-back `df0941a6377fe9a139a9a7b375ed6cf514c033e42b0a479b0536f1a013d46464`。
- 各自 `metadata/robot_edge_comparison.json` 保存逐集对照。100/100集均raw_N=converted_N+1；state[:2,:14]=raw[:2]、action[0,:14]=raw[1]、action[-2:,:14]=raw[-2:]（raw转float32），最大误差全部0。raw总帧20,153 / 17,638，converted为20,103 / 17,588，未重传或重转首批converted。

传输与收尾：nx两链启动间隔65秒，每链--bwlimit=10m、--partial --append-verify；第二链battery→swap、第一链drawer→cover顺序传输，校验在各自链内串行执行。优先补核期间安全暂停自有控制进程/battery进程组后原PID续跑；rsync记录平均吞吐drawer/battery/swap/cover分别9.68/7.78/9.72/9.57 MB/s。已归档nx真实job/PID：`85fa2611-8fcb-4447-9c93-6598c526fd99` / `13126`，`82ab0258-2847-416e-8ea3-bf14c36501cb` / `13148`。

workspace：`/mnt/public/xcj/Projects/workspace/e248b5a1-7d82-49cc-9b80-95e7181563e4`。关键校验结果已摘要于此；本任务asset-transfer临时脚本/日志/目录已清理，正式共享资产保留，workspace可供Manager归档。无业务库交付commit。
