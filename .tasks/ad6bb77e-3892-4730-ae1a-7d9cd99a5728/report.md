task_revision: db65224a8ca9928f1112b5a198c9ed4c42d6e569

当前结果：完成约定的12:02一次小时巡检，实际资源/日志快照为2026-09-10 12:04:03 CST。wash full/serial两路正式20k均running，更新持续推进，全部已落盘loss/grad_norm/param_norm有限，没有发现新增训练异常。本次仅只读巡检与发布报告，结束本次巡检；下一次检查2026-09-10 13:02 CST。

workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
实际SHA: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；git status --porcelain为空，沿用本任务独立.venv，源码继续冻结。
此前GPU50与真实checkpoint-only恢复已获Manager接受，证据见publication f74959a622e84a294448f967b90576561bfccb3f；11:02首查见de13d49e56a2a30a86645aba6add823de53a5def。此次未重复GPU50、恢复测试或启动任何GPU程序。

| GPU/配置 | 当前progress约数 | 比11:02新增约数 | 最近标量step | loss | grad_norm | param_norm | 秒/更新 | 完成ETA（北京时间） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2 / full | 1110 | 991 | 1100 | 0.0244 | 0.0974 | 1802.5265 | 3.7139 | 2026-09-11 07:33左右 |
| 3 / serial | 1110 | 994 | 1100 | 0.1579 | 3.9523 | 1802.5442 | 3.7107 | 2026-09-11 07:32左右 |

- 两路各11组Step100–1100落盘统计均逐条检查为有限值；统计是每100更新的区间均值。最新loss较首查full 0.0789→0.0244、serial 0.7063→0.1579。
- progress日志在千步后以1.11kit等格式取整，因此表中的progress和新增更新数用约数；Step1100为精确标量记录。吞吐按上次119/116至本次约1110的日志时间差计算，排除首次JIT，当前剩余约19小时29分；ETA会随吞吐变化。
- MAM在12:02:54核验两原job/PID身份均running，本次/proc复核start_ticks、session、cwd与原记录一致；实际命令均python -u -B、seed0、batch32、20000 updates/save_interval20000，环境GPU分别2/3、wash v3数据根一致。
- 全日志检查未发现Traceback、OOM/RESOURCE_EXHAUSTED、CUDA_ERROR、非有限标量或错误级日志。仅保留启动时既有Tyro类型警告和full编译rematerialization警告，未见新增训练异常。
- GPU2：73406MiB占用/7633MiB空闲/100%/70°C；GPU3：73408MiB占用/7631MiB空闲/100%/55°C。主机MemAvailable=880815368KiB（约840GiB）、swap未用，共享盘可用约9.1TiB。只查询本任务GPU2/3。
- full/serial日志距采样分别3.3/4.6秒；正式运行目录尚无数字checkpoint目录，符合仅最终20000保存的配置，当前未完成最终模型验收。

本机host: is-dcfi2kjdq7g3k6aa-devmachine-0。两路均于10:53:36 CST从pi05_base重新初始化，独立exp_name；BF16 model-only/save_full_state=False，优化器与数据沿验收config。

| GPU/配置 | PID | MAM job |
| --- | ---: | --- |
| 2 / full | 2495460 | bdd0624d-5274-4d10-a35f-4b2626594c72 |
| 3 / serial | 2495529 | 2566a91d-bde8-4602-8e03-a818bbdebd3e |

full产物：

- 日志：/mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_full_s0.log
- 最终checkpoint目标：/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000
- 完整command/env/启动记录：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_full_launch.json

serial产物：

- 日志：/mnt/public/xcj/Projects/openpi/logs/memory20k_ad6bb77e_wash_serial_s0.log
- 最终checkpoint目标：/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000
- 完整command/env/启动记录：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_serial_launch.json

本次快照：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/formal_hourly_20260910_1202.json

原d10 full/serial两份50step的params/assets/metadata目录和训练/dtype_restore/restore_wire日志均原位存在，继续保留供e6908de7下一阶段技术smoke；仅检查路径存在性，没有重新加载或清理。当前wash smoke也待正式模型替代后再清理。

剩余：两路20k继续运行；下一巡检2026-09-10 13:02 CST。完成后按task验收唯一20000、完整shape/BF16/model-only、metadata/assets及checkpoint-only恢复，交Manager安排固定5ep offline，再处理产物与归档MAM job。
