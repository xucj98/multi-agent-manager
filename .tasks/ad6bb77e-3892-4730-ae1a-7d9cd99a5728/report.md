训练交付及07:39收尾已完成，worktree可由Manager归档。两路wash实际20000保存、CPU完整参数及真实GPU checkpoint-only恢复已获Manager接受；本次仅留存证据和清理临时产物，无新增GPU工作。正式offline由b86b3d02使用自己的环境执行，不依赖本workspace。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
交付/运行源码commit: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；工作树干净，独立.venv及worktree保留供Manager归档。

| 配置 | 实际更新 | 最终loss | 参数叶子/元素 | 保存完成（9月11日CST） |
| --- | ---: | ---: | --- | --- |
| full_current_feedback | 20000 | 0.0046 | 51 / 3353433872 | 07:27:17.400 |
| serial_lag30 | 20000 | 0.0078 | 56 / 3353454358 | 07:27:11.499 |

两路各200组可见loss/grad_norm/param_norm全部有限；标量为100更新区间均值。均为从base独立初始化、seed0/batch32、单卡、唯一数字目录20000、BF16 model-only，无optimizer/train_state。CPU逐键/shape与完整模型树比对通过，全部BF16/finite。metadata/assets、唯一resolved memory_config、实际command/cwd/commit、wash v3的172ep/15Hz/14维state-action核对通过。

真实GPU恢复通过：actions均(50,14)且finite，full memory_prediction_ids(50,1)、serial(1,1)；使用非initial输入[1]，审计钩子拒绝原训练数据、norm资产、memory YAML及base读取。该结果为checkpoint恢复/wire验收，不是offline或rollout性能结果。CPU/GPU验证进程exit均0；原训练数字退出码在进程回收前未捕获，不宣称训练exit=0。保存finalize成功、MAM stopped、两主进程及事前记录的各3子进程均消失；训练及GPU恢复结束后GPU2/3均1MiB、0%利用率。

稳定交付路径（不依赖临时workspace）：

- full [正式20000](/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000)、[训练日志](/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/train.log)、[验收证据目录](/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/training_acceptance)。
- serial [正式20000](/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000)、[训练日志](/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/train.log)、[验收证据目录](/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/training_acceptance)。

各training_acceptance包含完整验收JSON、对应CPU/GPU日志、原启动记录和验证command原文、最终标量/保存摘要、主/子进程退出快照。validation_source.txt仅保留当时辅助脚本的文本留痕；历史命令中的旧workspace路径不代表当前依赖。full目录的prior_cpu_evidence另保存有价值的norm/config及精度验证小型历史记录。

日志和证据逐文件SHA256与原件一致，详见各目录evidence_copy_check.json；原20000/metadata全部文件及params/_METADATA校验未变。原公共logs仅复制，未迁移或删除，正式params未移动或改写。

07:39:47完成清理，详见各training_acceptance/workspace_cleanup.json：

- 删除本任务旧d10 full/serial技术50、wash smoke空目录及已完成smoke/临时日志、辅助自测脚本；原e690依赖已按最新task解除。
- 删除本任务worktree内pytest/ruff/__pycache__缓存；不跟随共享目录符号链接，不动共享数据、源模型、正式20000或其他任务文件。
- 清理临时文件逻辑大小10517351996 bytes，约9.80GiB（不等同于物理磁盘释放量）。
- BF16验证副本由47a91a44负责清理，本任务未再次操作或重建。

MAM训练job已于07:30:41归档：full bdd0624d-5274-4d10-a35f-4b2626594c72（原PID2495460），serial 2566a91d-bde8-4602-8e03-a818bbdebd3e（原PID2495529）。无本任务运行中的训练或验证程序，无需继续小时巡检。wuwen-1结束后不接续GPU任务；后续offline交Manager/b86安排，本训练任务无剩余实施项。
