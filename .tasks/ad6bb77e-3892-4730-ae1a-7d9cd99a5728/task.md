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
# 用户追加：验证保存精度与现有推理路径等价（12:25）

12:35新增用户要求：还需要将已训练模型转成BF16做真实rollout。因此本次必须以F0使用的完整旧模型 /mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000 为主比较源。数值一致性通过后的BF16副本需保留为正式评测输入，不能按下文临时副本规则删除它。目标固定为 /mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000；创建前检查不存在，不覆盖已有内容。只保留params、assets与完整继承metadata，训练来源metadata不改写成另一场训练；在metadata下保存本次导出实际命令、所调用代码commit、原checkpoint位置及本次dtype转换说明，沿用command/config留痕，不另造大套provenance。metadata需足够让下一owner明确这是同一旧30k模型的导出副本，不是新训练。导出验证完成后优先发出可用路径/bytes/逐值比较结果，Manager另派agent做独立GPU100rollout，你继续负责wash训练。其他临时副本/辅助文件仍清理；导出命令须完整留在metadata便于复现。

用户要求：若实际推理依赖FP32，不能为省空间擅自改成BF16保存。Manager已只读确认原RMBench fork与独立openpi的policy_config均在JAX推理restore时显式dtype=jnp.bfloat16；训练主参数/优化器仍FP32，主干计算混合BF16，部分运算FP32。需要验证“FP32保存→按现有入口加载BF16”与“同一FP32参数先按现有导出函数保存BF16→再加载BF16”恢复权重一致。

本轮只做CPU、临时产物验证，不改任何源码、正常训练进程、config或保存参数；不用GPU、不重复wash50训练。复用你的独立环境，显式JAX_PLATFORMS=cpu。选实际存在、metadata证实FP32的旧checkpoint，可优先用 /mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000 或原pi05_base。如需核对新增serial小head，使用已有旧drawer serial checkpoint或小型有明确数值的head参数补充，不伪造真实模型完成情况。

使用当前_model.restore_params、_cast_floating_params及实际Orbax保存/恢复机制比较全部浮点叶子（键、shape、dtype、逐值一致性及不一致计数，不用宽松allclose隐藏差异）。分别报告原文件dtype、推理恢复dtype，以及两条路径是否相等；若存在差异，先报告具体值/张量/转换路径，不假定不会影响性能。范围是验证当前BF16推理是否引入额外权重变化，不能据此声称与真正FP32推理等价，不能声称BF16导出可恢复FP32训练精度。若只完成参数一致性，不冒充已经跑了动作/rollout对比。

原checkpoint只读；临时导出放本任务workspace的明确新建子目录，验收数值结论写report后删除该临时副本和辅助脚本。无需额外持久provenance框架。CPU耗时预计少于一小时，若实际预计超过则登记job。不要重做本小时训练巡检；13:02仍按已约定时间巡检。发布简短report，保留原训练状态与产物定位。


## MAM 查询更新（2026-09-10）

系统 MAM 已更新：`mam task list` 和 `mam job list` 为带表头的简表，无 --json；完整task信息使用 `mam task status <id>`，实时job结构化详情使用 `mam job status <job-id>`。`mam task show` 仍默认Markdown，保留 --json。`mam task status` 仅显示保存的 job 状态与 checked_at，不刷新进程。按既定频率监控时使用 `mam job list --task ad6bb77e-3892-4730-ae1a-7d9cd99a5728` 获取实时进程状态，再结合已有日志检查进度。训练/评测协议、GPU 分配与检查频率不变。


16:01接口迁移：不要再将job list输出按JSON解析；用task status里的jobs取ID，再逐个job status获取实时结构化结果。既定监控频率不变。新增mam wait jobs/list/stop可按需使用，自动CODEX_THREAD_ID；停止等待不影响实验。


18:22 MAM精简status已安装：task status 的未归档job摘要位于 jobs.unarchived（无jobs时该键可省略），不是旧jobs数组；job status直接提供status/checked_at/error及unknown时last_known信息，不再嵌套probe或identity。实时进程身份仍由工具内部核对。按新JSON读取；保持既定每小时频率，不因接口变更额外复查训练。


## GPU 调度更新（最新用户指令，替代此前预留安排）

wuwen-1 的现有训练自然结束、完成 checkpoint 保存并释放资源后，整机8张GPU保持空闲，不再启动训练、smoke、offline test或正式评测，直到用户另行允许。明天2026-09-11中午12:00前为其他同学预留GPU的要求改由wuwen-1承担。本机GPU0–7均可按原授权继续训练和评测，启动前核对可用性。本机GPU2–7的原预留限制已取消。不要终止现有训练；若wuwen-1训练预计超出截止时间，及时报告Manager裁决。

训练收尾验收：核对退出状态、最终20000 checkpoint及metadata完整性，检查本任务登记进程及子进程是否退出、显存是否释放。对确认属于本任务的残留进程做清理并记录；不得根据显存占用直接终止不明进程（本集群其他开发机GPU进程可能不可见）。wuwen-1释放后保持空闲，检查结果反馈Manager。

## MAM 项目配置迁移完成（2026-09-11）
在/mnt/public/xcj/Projects及其子目录内直接使用mam；已取消--root参数，自动读取项目配置。MAM根目录不变，已发布任务/报告改到project/state-vla，main只用于工具开发。现有task/job/workspace不变；报告仍在原路径编辑，mam task publish正常发布。本轮main已重写历史；后续若开发MAM必须从新的main基线创建worktree，不从旧任务或项目分支合回main。训练与评测业务代码基线不受影响。

## 9月11日07:03 模型目录统一
用户要求OpenPI模型统一位于checkpoints，不再使用user_checkpoints。Manager交47a91a44-4efa-48d7-b162-93d097763376迁移已完成精度验证的BF16副本到openpi/checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000，保留权重和历史原始留痕。此前本任务“原位保留user_checkpoints”改为保留迁移后副本；你不要并发移动或重建旧路径，不改变正在训练的输出。后续简报引用新位置并注明迁移完成状态，以迁移owner报告为准。

07:04用户再次明确：该BF16验证副本实验已完成，应直接清理，不迁入checkpoints。47a91a44负责清理，仅保留源FP32和正式实验/导出留痕。替代上一条迁移安排；不要重建副本，wash训练不变。

## 07:39 训练交付收尾
Manager接受两20k保存/CPU全参数/GPU恢复交付；后续正式offline由b86b3d02使用自己的环境执行，不再依赖本训练workspace。请把有价值的两份20k保存/恢复验收小型报告与实际训练日志留入各自稳定checkpoints/<config>/<run>/下（复用既有位置，保持历史command/metadata原文；不要迁移公共logs或影响其他训练）。报告给出稳定链接，避免唯一证据只在临时workspace。逐个确认后可清理本任务全部已完成技术50 checkpoint、smoke视频/日志、临时cache及辅助自测脚本；e690已有实际20k自身smoke通过，旧full/serial50不再是依赖。只清理本任务拥有的临时内容，不删源模型、正式20k或数据。BF16验证临时副本已由47a91a44清理，无需再操作。
完成后发布最终训练简报并保留干净worktree供Manager归档，不新增训练、不占GPU。用户关于架构缺口正在讨论，不在本任务扩大实施。
