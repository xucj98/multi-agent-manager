task_revision: 14974320cbd3669d043d71ceeca8db383fd2facf

正式BF16评测副本已交付（按12:35追加要求保留，不能清理）：

- 可用路径：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000
- 原模型：/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000。这是F0同一旧full30k模型的dtype导出副本，没有重新训练。CPU-only执行，沿本任务独立.venv与冻结056bcc887637cc6eda565a8ad7d45c88021d4bcd代码；原checkpoint只读，wash正常训练未变，本轮没有重复小时巡检或占用GPU。
- 原文件metadata为51个FP32叶子；调用当前restore_params保留FP32、_cast_floating_params('bfloat16')、实际Orbax PyTreeSave导出。固定目录创建前确认不存在，未覆盖已有内容；最终仅params/assets/metadata。
- 对此实际持久副本重新执行两条恢复路径全量比较：原FP32文件→restore BF16，与导出BF16文件→restore BF16；全部51叶子/3353433872元素键、shape、dtype均一致，逐值不一致0、uint16位模式不一致0，全部有限。不是仅复用上一轮临时导出的结果。
- BF16参数逻辑大小6706867744字节；params文件实际合计5257190352字节（Orbax存储大小，不等同未压缩参数大小）；当前整个副本文件合计5257233544字节。
- 原assets和全部metadata完整复制并逐文件SHA256核对，共7个原文件一致。原metadata/command.txt、train_config.yaml仍描述原30k训练，没有改写为新训练。
- 本次可复现实际CPU导出命令/完整Python代码、导出commit/cwd/时间、原checkpoint位置和dtype说明：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000/metadata/export_command.txt。
- 全部逐叶数值/shape/dtype/位模式比较与继承文件hash证据：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000/metadata/export_validation.json。执行日志：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/cpu_norm_logs/f0_bf16_export_20260910.log。
- 此固定副本作为正式100-rollout评测输入保留，交Manager/另一agent执行；本owner未运行或宣称动作/rollout结果。参数一致性只说明当前BF16恢复路径对该checkpoint没有额外权重变化，不等价于FP32推理、也不能恢复FP32训练精度。
- 没有留下临时辅助脚本（本次直接以python -u -B -c执行，完整命令留在上述metadata）；上一轮临时副本及辅助脚本已清理。本正式副本、原d10两份50和wash产物均继续保留。

以下为上一轮CPU参数验证及既有训练巡检状态，保留原训练job/PID/产物定位；下一小时巡检仍为13:02 CST。

CPU追加验证：FP32保存与BF16导出在当前BF16恢复入口下的参数一致性（非新一轮巡检）。

- 真实输入只读：/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000/params。Orbax metadata证实全部51浮点叶子为FP32，共3353433872元素；不是将BF16文件上转FP32伪造来源。
- 执行环境为本任务056bcc8独立.venv，CUDA_VISIBLE_DEVICES=''、JAX_PLATFORMS=cpu，实际设备仅CpuDevice(id=0)。耗时37.00秒，退出码0，没有GPU调用、训练/源码/config修改或本小时重复巡检。
- 路径A：当前openpi.models.model.restore_params(原FP32 checkpoint, dtype=jnp.bfloat16)，默认恢复为JAX数组，与现有policy入口的restore调用相同。
- 路径B：同一原checkpoint经restore_params保留FP32 → 当前training.checkpoints._cast_floating_params(params, 'bfloat16') → 实际Orbax PyTreeCheckpointer/PyTreeSave落盘 → 当前restore_params(临时BF16 checkpoint, dtype=jnp.bfloat16)。临时导出metadata确认51叶子全部BF16；不是仅比较两个内存cast，也未替换导出函数实现。
- 全部51叶子的键、shape、恢复dtype相同；全部3353433872元素逐值不一致数0、uint16位模式不一致数0，没有使用宽松allclose。原FP32全部有限。
- BF16对原FP32并非无损：有3352332446个元素在FP32→BF16→FP32后数值改变，最大绝对舍入差0.5948486328125（张量PaliGemma/img/pos_embedding）；此项是权重舍入量，不是动作误差或性能下降量。
- 结论仅限这份真实FP32 checkpoint的完整参数：先导出BF16再按BF16恢复，相比现有“FP32文件→BF16恢复”没有额外权重差异。不能据此宣称与真正FP32推理等价、可恢复原FP32训练精度或保证rollout性能不变；未运行动作/rollout对照，也未覆盖新增serial head。原RMBench与独立openpi的policy_config均已核对显式restore dtype=jnp.bfloat16，但此次实际执行使用本任务独立openpi的restore实现。
- 完整逐叶证据：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/cpu_norm_logs/fp32_bf16_equivalence_20260910.json；执行日志：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/cpu_norm_logs/fp32_bf16_equivalence_20260910.log。
- 临时副本及辅助脚本清理：结果写入本report后，已删除本任务新建fp32_bf16_cpu_check_sqgrpml9整个目录（含BF16导出、辅助脚本），并确认路径不存在；原checkpoint和既有d10/wash smoke不在清理范围。

以下保留原12:02巡检状态和训练产物定位；本轮没有重新采样训练进度。下一小时检查仍为2026-09-10 13:02 CST。

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
