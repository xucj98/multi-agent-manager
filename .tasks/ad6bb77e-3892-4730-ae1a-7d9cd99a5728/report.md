task_revision: 61bde00c6fb1d1a6f93dd252bac3e4523caeebdf

当前结果：完成14:57恢复后的wash巡检，实际快照2026-09-10 14:58:02 CST。两路原PID均running、更新持续增加、全部可见标量有限，无新增错误或警告。本次仅只读巡检和报告；下一检查2026-09-10 15:57 CST，结束本次巡检。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
实际SHA: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；工作树干净，源码/环境/config/训练进程保持冻结。

| GPU/配置 | progress约数 | 较13:05新增约数 | 可见标量step | loss | grad_norm | param_norm | 秒/更新 | ETA（北京时间） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 / full | 3920 | 1820 | 3900 | 0.0145 | 0.0686 | 1803.5609 | 3.7301 | 2026-09-11 07:38左右 |
| 3 / serial | 3920 | 1820 | 3900 | 0.0698 | 1.8856 | 1803.6606 | 3.7383 | 2026-09-11 07:40左右 |

- 两路各39组落盘loss/grad_norm/param_norm均有限，较上次实际13:05:20快照分别新增19/18组。标量为每100更新区间均值，不代表逐update原始标量；未补称14:02执行过巡检。
- progress按kit取整，3920为约数；精确最近可见标量step均为3900。吞吐窗口约13:58–14:58、progress2960→3920，约965/963 updates每小时；ETA受取整、吞吐波动及最终保存耗时影响。
- 已用mam job list --task实时查询，14:57:19两job均running；未把task status缓存当实时证据。原PID/start_ticks匹配，cwd、python -u -B、batch32/seed0、20000 updates/save_interval20000及GPU2/3环境均一致。
- 全日志无错误或非有限标量，没有新增警告；只有既有启动Tyro警告及full初始XLA rematerialization警告。日志距采样full8.3秒、serial10.2秒。
- GPU2/3占用73406/73408MiB、空闲7633/7631MiB，利用率均100%，温度71/57°C；只查询本任务GPU2/3。主机MemAvailable=888355296KiB。
- 20k及最终恢复验收尚未完成。本次没有启动GPU程序、重启训练、重复BF16导出或旧50验证。

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

本次快照：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_hourly_20260910_1457.json

已接受产物与保留要求：

- wash GPU50与实际恢复已验收，详细证据publication f74959a622e84a294448f967b90576561bfccb3f；本次未重复gate/恢复/dtype验证。
- F0正式BF16评测输入：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000；params/assets/metadata均原位保留。CPU参数验证及交接已获Manager接受，证据publication 04eee7a5cf20b4011406dbddc99bbbb148d7e1b8；后续Carver负责100 rollout，本owner未宣称rollout结果。
- 原d10 full/serial两份50在本workspace/gpu_smoke_checkpoints下，params/assets/metadata均原位存在，继续供e690使用；没有清理/重载。当前wash smoke也保留。

剩余：两路20k继续运行；下一巡检2026-09-10 15:57 CST。完成后按task验收唯一20000、完整shape/BF16/model-only、metadata/assets和checkpoint-only恢复，交Manager安排5ep offline，再处理产物与MAM job收尾。
