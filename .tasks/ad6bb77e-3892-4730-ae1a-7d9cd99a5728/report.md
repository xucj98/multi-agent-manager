当前结果：wash full/serial两路均完成实际20000 optimizer更新、唯一20000最终保存，以及CPU完整参数和真实GPU checkpoint-only恢复验收。2026-09-11 07:30 CST完成进程/显存释放检查及两训练job归档。GPU offline尚未启动，等待Manager明确安排；训练小时巡检结束。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
交付/运行源码commit: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；工作树干净，训练源码/环境/config保持冻结。验收辅助脚本及证据在workspace上层wash_gpu_logs内。

| 配置 | 更新数 | step20000 loss | grad_norm | param_norm | 保存完成时间（9月11日CST） |
| --- | ---: | ---: | ---: | ---: | --- |
| full_current_feedback | 20000 | 0.0046 | 0.0423 | 1806.7374 | 07:27:17.400 |
| serial_lag30 | 20000 | 0.0078 | 0.0524 | 1806.8206 | 07:27:11.499 |

两路各200组可见loss/grad_norm/param_norm全部有限，最后一组为step20000。标量为100更新区间均值，不冒充逐update原始值。训练日志确认异步保存finalize完成且后台无错误。各实验只有数字目录20000，无train_state/optimizer保存。训练均从base独立初始化、seed0/batch32、单卡，未从50step续训。

| 验收 | full | serial |
| --- | --- | --- |
| 参数叶子/元素 | 51 / 3353433872 | 56 / 3353454358 |
| BF16逻辑bytes | 6706867744 | 6706908716 |
| params实际磁盘bytes | 5257148357 | 5257142963 |
| 完整参数shape/全部BF16/全部finite | PASS | PASS |
| 真实GPU恢复actions | (50,14)，finite | (50,14)，finite |
| memory_prediction_ids | (50,1)，整数 | (1,1)，整数 |
| CPU/GPU验收进程退出码 | 0 / 0 | 0 / 0 |

metadata/assets验收：resolved TrainConfig可恢复、memory_config仅一次；save_dtype=bfloat16、save_full_state=False、20000/batch32/seed0核对；实际command/cwd/冻结commit留痕完整。datasets.json确认wash v3、172ep、15Hz、state/action14维；继承upstream目录和专用norm存在。CPU通过真实restore_params加载全部叶子，按模型abstract tree逐键/shape比较并检查dtype/finite。GPU在各自训练退出且卡已空闲后，以实际create_trained_policy_from_checkpoint入口、非initial memory_input_ids=[1]和合成三相机/机器人输入进行一次infer。审计钩子拒绝原训练数据、训练norm资产、原memory YAML及base路径读取。该结果为保存/加载与wire验收，不是offline动作精度或rollout性能结论。

资源收尾：mam wait jobs --task保持active turn，07:27:15由serial停止事件唤醒；07:27:35实查两主进程及事前记录的各3个子进程全部已消失。训练主进程被回收前未取得独立数字退出码，故不宣称训练exit=0；以最终保存成功日志、MAM stopped、进程消失及完整恢复作为实际证据。无需终止残留进程。训练退出后和GPU验收退出后，GPU2/3均1MiB占用、81038MiB空闲、0%利用率。本次仅使用本机原GPU2/3，不占训练中的卡，不使用wuwen-1。

正式checkpoint交接：

- full: /mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000
- serial: /mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000
- full训练日志: /mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_full_s0.log
- serial训练日志: /mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_serial_s0.log

验收证据目录：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs

- formal_20000_acceptance.json：两路完整验收、资源释放、清理记录。
- formal_final_training_summary.json：最终200组标量统计、唯一20000及保存完成日志。
- formal_process_tree_before_exit.json / formal_exit_snapshot.json：主/子进程身份及退出核对。
- formal_{full,serial}_20000_{cpu,gpu}.log：实际CPU/GPU结果。
- formal_{full,serial}_20000_validation_command.txt、validate_final_checkpoint.py：实际命令、cwd/commit与可复核脚本；formal_{full,serial}_launch.json保留原启动记录。

MAM归档：full job bdd0624d-5274-4d10-a35f-4b2626594c72（原PID2495460）、serial job2566a91d-bde8-4602-8e03-a818bbdebd3e（原PID2495529）均07:30:41归档，说明中保留退出码范围及证据位置。

清理与保留：

- 两份wash50已被验收后的正式模型替代，按任务清理wash_gpu_smoke_checkpoints下对应50目录，旧gate日志保留；正式20000未改动。
- 原d10 rearrange full/serial50和gpu_smoke_logs继续保留供e690，未清理。
- 按07:04替代要求，F0 BF16验证副本由47a91a44清理，不迁移、不重建；完成状态以其报告为准。原FP32和正式实验/导出留痕保留，历史CPU参数验证证据publication 04eee7a5cf20b4011406dbddc99bbbb148d7e1b8保留。

剩余交接：Manager安排固定5ep GPU offline；通用入口修复由Boole b86b3d02推进，本任务不改冻结训练树、不自行启动offline。wuwen-1现有训练结束保存释放后整机空闲，后续GPU恢复/评测仅使用本机可用卡。本任务无运行中的训练或验证程序，无需继续训练小时巡检。
