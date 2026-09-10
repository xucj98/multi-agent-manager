task_revision: db65224a8ca9928f1112b5a198c9ed4c42d6e569

当前结果：wash full/serial 各真实50更新GPU gate全部通过；2026-09-10 10:53:36 CST 已在各自GPU2/3从pi05_base重新初始化正式20k，已可靠detach并立即MAM本机job登记。11:02:42 CST 正式首查通过，两路均持续更新且Step100落盘标量有限；20k仍在运行。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
实际保存/恢复/正式启动SHA: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；工作树干净、独立.venv，自启动起冻结。此前CPU独立GO与旧阶段证据见report publication 1ab252db0d2a97ad2e47f79e98833ea1071ffd59。

本轮GPU50已获Manager接受（用户2026-09-10本轮消息）：full/serial各50更新、完整BF16/shape/finite/model-only、fresh-process真实checkpoint-only GPU infer及wire全部通过。详细数据、脚本与日志指针见report publication f74959a622e84a294448f967b90576561bfccb3f，下列gate产物继续保留。此次首查没有重跑gate或修改冻结源码。

11:02:42 CST 正式首查：

| GPU/配置 | 已记录progress | 最近标量step | loss | grad_norm | 稳定秒/更新 | 完成ETA（北京时间） |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2 / full | 119 | 100 | 0.0789 | 0.4979 | 3.7122 | 2026-09-11 07:33左右 |
| 3 / serial | 116 | 100 | 0.7063 | 71.2657 | 3.7128 | 2026-09-11 07:33左右 |

- 两路Step100的loss/grad_norm/param_norm均为有限值。这是现有日志每100更新的区间均值证据；full param_norm=1802.3861，serial=1802.3893。
- 稳定吞吐排除初始JIT，按full更新20–119、serial更新20–116之间真实progress时间差计算；约3.713秒/更新，剩余约20小时30分。近期最后几条日志约3.6秒/更新，ETA随吞吐波动，以上使用窗口均值。
- MAM于11:02:42再次验证两原PID/start_ticks均running；session ID分别等于各自PID，cwd均为本任务冻结worktree。日志明确batch32及从pi05_base/params重新恢复；无resume/overwrite，没有接续50step。
- GPU2/3分别占73406/73408MiB，空闲7633/7631MiB，利用率均100%；主机MemAvailable=879805818KiB。日志距采样2.2/11.5秒，未见Traceback/RESOURCE_EXHAUSTED/CUDA_ERROR。HEAD仍056bcc8，git status干净。
- 可复核首查快照：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_first_check.json
- 下一巡检：2026-09-10 12:02 CST，之后按小时检查原PID身份、progress/日志有限标量、资源与ETA。

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

剩余：两路20k继续运行并按小时巡检；完成后验收唯一20000、完整BF16/shape/model-only/metadata/assets和checkpoint-only恢复，交Manager安排5ep offline并收尾MAM job。

旧rearrange d10/50两份与必要日志继续留给e6908de7；当前wash smoke待正式模型替代后再清理。未占用GPU0/1或4–7。
