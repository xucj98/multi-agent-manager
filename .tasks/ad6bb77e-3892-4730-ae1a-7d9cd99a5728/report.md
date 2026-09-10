当前结果：2026-09-11 06:51:15 CST最新检查，两路仍running，精确可见标量step均19400；预计07:27左右完成更新，保存另需耗时。正在按用户要求转入mam wait jobs --task主动等待，任一路训练退出后执行实际20000 checkpoint验收及进程释放收尾。GPU offline等待Manager明确安排。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
冻结代码：056bcc887637cc6eda565a8ad7d45c88021d4bcd；本轮未改源码、环境、配置或训练进程。

| GPU/配置 | 可见标量step | loss | grad_norm | param_norm | 当前日志速率 | ETA |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 2 / full | 19400 | 0.0050 | 0.0426 | 1806.7096 | 约3.7秒/update | 今日07:27左右 |
| 3 / serial | 19400 | 0.0083 | 0.0539 | 1806.7925 | 约3.7秒/update | 今日07:27左右 |

两路各194组落盘loss/grad_norm/param_norm全部有限；无所检Traceback/OOM/RESOURCE_EXHAUSTED/CUDA_ERROR或错误级日志。标量是每100更新的区间均值，ETA是日志估计，不冒称最终训练完成。

06:50:35 job status实时确认两路running。GPU2/3占用73406/73408MiB、空闲7633/7631MiB，利用率均100%，温度68/56°C。未重复smoke或恢复验证。

后续：等待自然结束、保存完成，核对退出状态、唯一20000、完整BF16参数树及metadata/assets、checkpoint-only恢复、本任务进程/子进程退出与显存释放；仅清理明确属于本任务的残留。GPU恢复只在本机空闲卡进行，offline不自行启动。wuwen-1释放后不接续GPU任务。

| GPU/配置 | PID | MAM job |
| --- | ---: | --- |
| 2 / full | 2495460 | bdd0624d-5274-4d10-a35f-4b2626594c72 |
| 3 / serial | 2495529 | 2566a91d-bde8-4602-8e03-a818bbdebd3e |

两路均于2026-09-10 10:53:36 CST在本机is-dcfi2kjdq7g3k6aa-devmachine-0从pi05_base独立初始化；BF16 model-only、save_full_state=False，未改正式保存参数。

full:

- 日志：/mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_full_s0.log
- 最终checkpoint目标：/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000
- 完整command/env/启动记录：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_full_launch.json

serial:

- 日志：/mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_serial_s0.log
- 最终checkpoint目标：/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000
- 完整command/env/启动记录：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_serial_launch.json

本次快照：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_status_20260911_0651.json

已接受产物与保留要求：

- wash GPU50与实际恢复已验收，详细证据publication f74959a622e84a294448f967b90576561bfccb3f；本次未重复gate/恢复/dtype验证。
- F0正式BF16评测输入：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000；params/assets/metadata均原位保留。CPU参数验证及交接已获Manager接受，证据publication 04eee7a5cf20b4011406dbddc99bbbb148d7e1b8；后续Carver负责100 rollout，本owner未宣称rollout结果。
- 原d10 full/serial两份50在本workspace/gpu_smoke_checkpoints下，params/assets/metadata均原位存在，继续供e690使用；没有清理/重载。当前wash smoke也保留。

剩余：两路20k继续运行；接下来使用mam wait jobs --task保持active turn，任一路停止后立即收尾。完成后按task验收唯一20000、完整shape/BF16/model-only、metadata/assets和checkpoint-only恢复，交Manager安排5ep offline，再处理产物与MAM job收尾。
