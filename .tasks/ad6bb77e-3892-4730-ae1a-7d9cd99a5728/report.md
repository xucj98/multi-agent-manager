task_revision: 14974320cbd3669d043d71ceeca8db383fd2facf

当前结果：完成13:02约定的一次wash小时巡检；用户13:03发起，实际快照2026-09-10 13:05:20 CST。两路原PID均running、更新持续增加、全部可见标量有限，无新增错误或警告。本次仅只读巡检和报告，结束本次巡检；下一检查2026-09-10 14:02 CST。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
实际SHA: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；工作树干净，源码/环境/config/训练进程保持冻结。

| GPU/配置 | progress约数 | 较上次新增约数 | 可见标量step | loss | grad_norm | param_norm | 秒/更新 | ETA（北京时间） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 / full | 2100 | 990 | 2000 | 0.0195 | 0.0776 | 1802.8528 | 3.7034 | 2026-09-11 07:30左右 |
| 3 / serial | 2100 | 990 | 2100 | 0.1087 | 2.5933 | 1802.9497 | 3.714 | 2026-09-11 07:33左右 |

- full共20组Step100–2000、serial共21组Step100–2100落盘loss/grad_norm/param_norm逐条检查均有限；较上次分别新增9/10组。这里是每100更新区间均值证据，不冒充逐update原始标量。
- progress在千步后按kit取整，约2100不等于精确已完成2100；因此full最近可见标量仍记2000。吞吐按12:04前次快照与本次日志时间差计算，受progress取整和吞吐波动影响，ETA为估算。
- MAM在13:04:24核验两原job身份running；/proc start_ticks匹配、cwd为本任务树，命令保持python -u -B、batch32/seed0、20000 updates/save_interval20000，CUDA_VISIBLE_DEVICES仅分别2/3，wash v3数据根一致。
- 全日志未见Traceback、OOM/RESOURCE_EXHAUSTED、CUDA_ERROR、错误级日志或非有限标量，较上次没有新增警告；仅存在既有启动Tyro/编译警告。日志距采样full13.4秒、serial4.2秒。
- GPU2/3占用73406/73408MiB、空闲7633/7631MiB，利用率均100%，温度70/57°C；只读取本任务GPU2/3状态，没有启动GPU程序或检查Carver GPU0。主机MemAvailable=887032203KiB。
- 正式目录尚无数字checkpoint子目录，符合仅最终20000保存；20k及最终恢复验收尚未完成。

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

本次快照：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_hourly_20260910_1302.json

已接受产物与保留要求：

- wash GPU50与实际恢复已验收，详细证据publication f74959a622e84a294448f967b90576561bfccb3f；本次未重复gate/恢复/dtype验证。
- F0正式BF16评测输入：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000；params/assets/metadata均原位保留。CPU参数验证及交接已获Manager接受，证据publication 04eee7a5cf20b4011406dbddc99bbbb148d7e1b8；后续Carver负责100 rollout，本owner未宣称rollout结果。
- 原d10 full/serial两份50在本workspace/gpu_smoke_checkpoints下，params/assets/metadata均原位存在，继续供e690使用；没有清理/重载。当前wash smoke也保留。

剩余：两路20k继续运行；下一巡检2026-09-10 14:02 CST。完成后按task验收唯一20000、完整shape/BF16/model-only、metadata/assets和checkpoint-only恢复，交Manager安排5ep offline，再处理产物与MAM job收尾。
