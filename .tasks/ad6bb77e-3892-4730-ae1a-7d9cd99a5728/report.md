task_revision: 230f7a9ade908c6e5d442fdb7fa25a31e6a5fe70

当前结果：完成17:57 wash两路例行巡检，实际快照2026-09-10 17:57:02 CST。两路实时running、更新持续增加，全部可见标量有限，无新增异常；下一检查2026-09-10 18:57 CST。本次仅只读巡检并发布报告，结束本次巡检。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
实际SHA: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；工作树干净，源码/环境/config/训练进程保持冻结。

| GPU/配置 | progress约数 | 较16:59新增约数 | 可见标量step | loss | grad_norm | param_norm | 秒/更新 | ETA（北京时间） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 / full | 6820 | 940 | 6800 | 0.0114 | 0.0628 | 1804.5477 | 3.7022 | 2026-09-11 07:30左右 |
| 3 / serial | 6830 | 950 | 6800 | 0.0326 | 1.5295 | 1804.6931 | 3.6641 | 2026-09-11 07:21左右 |

- 两路各68组已落盘loss/grad_norm/param_norm全部有限，较上次各新增10组。标量为每100更新区间均值，不代表逐update原始标量。
- progress按kit取整；最近精确标量step均6800。吞吐按上次与本次日志时间差及约数增量计算，约972/983 updates每小时。ETA为估算，受取整、吞吐及最终保存耗时影响。
- 当前已安装的job status逐个实时JSON查询在17:56:29确认均running。未依赖尚在review的精简status，也未将缓存当实时证据。两原PID/start_ticks、cwd及python -u -B/batch32/seed0/20000更新/仅最终保存命令均匹配。
- 全日志无所检错误或非有限标量，无新增警告。日志距采样full9.5秒、serial6.0秒。
- GPU2/3占用73406/73408MiB、空闲7633/7631MiB，利用率均100%，温度68/55°C；只查询本任务GPU2/3。
- 未启动GPU程序、重启训练、修改冻结树或重复BF16导出/旧50验证。20k及最终验收尚未完成。

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

本次快照：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_hourly_20260910_1757.json

已接受产物与保留要求：

- wash GPU50与实际恢复已验收，详细证据publication f74959a622e84a294448f967b90576561bfccb3f；本次未重复gate/恢复/dtype验证。
- F0正式BF16评测输入：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000；params/assets/metadata均原位保留。CPU参数验证及交接已获Manager接受，证据publication 04eee7a5cf20b4011406dbddc99bbbb148d7e1b8；后续Carver负责100 rollout，本owner未宣称rollout结果。
- 原d10 full/serial两份50在本workspace/gpu_smoke_checkpoints下，params/assets/metadata均原位存在，继续供e690使用；没有清理/重载。当前wash smoke也保留。

剩余：两路20k继续运行；下一巡检2026-09-10 18:57 CST。完成后按task验收唯一20000、完整shape/BF16/model-only、metadata/assets和checkpoint-only恢复，交Manager安排5ep offline，再处理产物与MAM job收尾。
