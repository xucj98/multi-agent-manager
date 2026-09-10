task_revision: db65224a8ca9928f1112b5a198c9ed4c42d6e569

当前结果：wash full/serial 各真实50更新GPU gate全部通过；2026-09-10 10:53:36 CST 已在各自GPU2/3从pi05_base重新初始化正式20k，已可靠detach并立即MAM本机job登记。当前进行正式首查，尚未宣称20k完成。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
实际保存/恢复/正式启动SHA: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；工作树干净、独立.venv，自启动起冻结。此前CPU独立GO与旧阶段证据见report publication 1ab252db0d2a97ad2e47f79e98833ea1071ffd59。

本轮GPU50证据：

- full: 50次更新，Step50 loss=0.0698 / grad_norm=0.2750；完整51叶子、3353433872元素、6706867744字节，均BF16且有限、shape/key完整匹配模型，无optimizer。
- serial: 50次更新，Step50 loss=0.4892 / grad_norm=35.4966；完整56叶子、3353454358元素、6706908716字节，均BF16且有限、shape/key完整匹配模型，无optimizer。
- 两路均在各自新Python进程、cwd=/tmp、HF_LEROBOT_HOME=/unavailable-training-data下通过实际GPU checkpoint-only factory/infer；导入前audit hook拒绝源YAML、训练dataset/sidecar、原norm和base的读取。实际模型按checkpoint assets归一化，非initial memory_input_ids=[1]。机器人actions均(50,14)，full memory_prediction_ids=(50,1)，serial=(1,1)且等于同次action-conditioned key_state_prediction；full不同memory改变实际tokenized_prompt。
- 完整metadata/asset验证：仅最终50目录，resolved memory_config一次，runtime字段不保存，dataset fps15/172ep/v3正确，上游meta/info.json存在。两份完整参数均实际从磁盘恢复核验。
- gate执行脚本（非冻结源码，位于MAM任务记录）：/root/Projects/multi-agent-manager/.tasks/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_checkpoint_gate.py

正式运行：单卡batch32/seed0/20000 optimizer updates/save_interval20000/save_full_state=False/save_dtype=bfloat16；optimizer等沿既有config默认；无resume/overwrite、不从50step继续。每次启动前GPU各1MiB，MemAvailable约855GiB。host=is-dcfi2kjdq7g3k6aa-devmachine-0。

| GPU/配置 | PID | MAM job |
| --- | ---: | --- |
| 2 / full | 2495460 | bdd0624d-5274-4d10-a35f-4b2626594c72 |
| 3 / serial | 2495529 | 2566a91d-bde8-4602-8e03-a818bbdebd3e |

实际cwd为上述worktree；环境共同为JAX_PLATFORMS=cuda、XLA_PYTHON_CLIENT_MEM_FRACTION=0.90、HF_LEROBOT_HOME=/mnt/public/xcj/Projects/openpi/data/lerobot、OPENPI_DATA_HOME=/mnt/public/cache/openpi，CUDA_VISIBLE_DEVICES分别2/3。

full:

- command: `.venv/bin/python -u -B scripts/train.py pi05_x1pro_wash_cup_s2m_full_current_feedback --exp-name=memory20k_ad6bb77e_wash_full_s0 --checkpoint-base-dir=/mnt/public/xcj/Projects/openpi/checkpoints --seed=0 --batch-size=32 --num-train-steps=20000 --save-interval=20000 --log-interval=100 --no-wandb-enabled`
- 正式日志：/mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_full_s0.log
- 正式最终checkpoint目标：/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000
- gate日志：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/wash_full_smoke50_seed0_056bcc8_gate.log
- gate checkpoint：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_smoke_checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/wash_full_smoke50_seed0_056bcc8/50
- 完整启动记录：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_full_launch.json

serial:

- command: `.venv/bin/python -u -B scripts/train.py pi05_x1pro_wash_cup_s2m_serial_lag30 --exp-name=memory20k_ad6bb77e_wash_serial_s0 --checkpoint-base-dir=/mnt/public/xcj/Projects/openpi/checkpoints --seed=0 --batch-size=32 --num-train-steps=20000 --save-interval=20000 --log-interval=100 --no-wandb-enabled`
- 正式日志：/mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_serial_s0.log
- 正式最终checkpoint目标：/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000
- gate日志：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/wash_serial_smoke50_seed0_056bcc8_gate.log
- gate checkpoint：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_smoke_checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/wash_serial_smoke50_seed0_056bcc8/50
- 完整启动记录：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_serial_launch.json

剩余：正式首查等待Step100有限标量（日志间隔100）并确认持续更新；预计11:01前后完成首查，再给基于稳定吞吐的ETA与下一小时巡检时间。20k结束验收唯一20000、完整BF16/shape/model-only/metadata/assets和checkpoint-only恢复，交Manager安排5ep offline并收尾MAM job。

旧rearrange d10/50两份与必要日志继续留给e6908de7；当前wash smoke待正式模型替代后再清理。未占用GPU0/1或4–7。
