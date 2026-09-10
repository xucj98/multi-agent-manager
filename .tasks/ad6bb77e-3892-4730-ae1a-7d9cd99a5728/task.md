# Memory v1：wash GPU验证与正式20k

## 当前状态与职责

此前训练集成、R1–R4、两种实际base GPU50、put-back norm、wash配置与metadata恢复均已验收。wash CPU结论见Banach 1efc1294、57e9c032；代码056bcc887637cc6eda565a8ad7d45c88021d4bcd已合入主库a869498，代码树相同。原详细要求留在本task Git历史，不重复已完成CPU工作。

现在负责本机wash full/serial各50更新GPU验证，通过后各启动正式20k并监控、验收、交接offline。复用当前登记openpi worktree、独立.venv，保持056bcc8和工作树干净。正式运行后冻结源码，不改模型、loader、配置或切换版本；后续缺陷报告Manager另派。不要自行派agent或新建环境。

## 资源与开跑授权（10:43）

Manager于10:37实测本机GPU2–7各1MiB占用、81038MiB空闲、0%利用率。GPU2交本任务full，GPU3交serial；GPU0/1仍F0，GPU4–7由Locke补Q2，远端八路继续。每次启动前复核本任务卡实际显存、CPU RAM，不根据进程不可见判断空闲，不占其他卡。

| GPU | train config | seed |
| --- | --- | ---: |
| 2 | pi05_x1pro_wash_cup_s2m_full_current_feedback | 0 |
| 3 | pi05_x1pro_wash_cup_s2m_serial_lag30 | 0 |

两GPU的50step可并行；各自通过后立即在同GPU从同一pi05_base重新初始化正式20k，无需再次请示，不从50step继续冒充正式训练。每模型单GPU、batch32、实际20000 optimizer更新，仅最终20000 BF16模型权重与assets/metadata，save_full_state=False。优化器默认沿config；新启动均python -u -B。

各次独立exp_name/输出，拒绝已有目录混写；可靠detach，正式进程立即mam job add记录本机host/PID和用途。OOM/非有限loss/恢复失败保留事实报告，不暗改受控batch、数据或混写重试。仅通过本配置GPU门才启动该配置20k，不等另一配置就绪。

## 数据与必要GPU门

共享数据openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_172_15hz_s2m_master_v3_source_frame_aligned，172ep、143698 query、fps15。单phase表示当前子任务，标签1–5各一次且顺序可变；label6/缺标注/不满足计数的episode已整集排除。全172ep训练，offline固定前5ep。当前从臂14维输入、已对齐下一主臂14维动作，offset0，不二次移位。缺GT只mask记忆监督，保留机器人目标。

专用norm为共享assets/memory_v1/x1pro_wash_cup_s2m_robot/norm_stats.json。真实loader、S2M Arx、三相机、15Hz metadata、归一化及无源数据读取的factory已独立CPU通过，不全量重算数据。base为/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base。

每种实际50step核对：optimizer更新到50、落盘loss/梯度有限；完整参数均BF16、model-only，无optimizer，assets/metadata完整；新进程仅checkpoint路径恢复真实模型并infer。robot actions(50,14)，full memory_prediction_ids(50,1)、serial(1,1)，非initial输入与serial选值/动作条件遵守已验收wire。不得以CPU替身冒称GPU模型通过。smoke留本workspace临时目录，与正式共享checkpoints分开。

通过后发布简短gate结果并立即开该正式训练，记录保存/加载实际commit和完整命令。Manager从报告/产物验收，不重复整轮GPU测试。正式首查确认更新推进、batch32、有限标量；之后每小时检查，报告下次检查时间及稳定吞吐ETA。

## 留痕、交付与清理

转换→训练→测试沿现有metadata继承，保留实际command/cwd/commit、resolved config、上游metadata及assets，不复制代码或新增runtime/provenance系统。正式数据、norm、checkpoint留共享原openpi路径。

原rearrange full/serial d10/50仍供e6908de7评测技术验证，暂留原gpu_smoke_checkpoints和必要日志，Manager确认交接完成后清理。当前wash smoke在正式模型替代后清理，不删除活跃依赖，不复制到正式checkpoint树。

20k结束核对更新数、唯一20000、完整shape/BF16/model-only、metadata/assets及checkpoint-only恢复，交Manager/评测owner安排固定5ep offline。未安排前不占其他GPU做offline。记录结果、处理临时产物后mam job archive，最终Manager归档workspace/分支。

report注明最新task_revision、workspace/实际SHA、两配置gate/正式状态、job/PID/输出路径、剩余与下一巡检。详细旧证据以publication/文件指针引用，不重复累积历史段落。
