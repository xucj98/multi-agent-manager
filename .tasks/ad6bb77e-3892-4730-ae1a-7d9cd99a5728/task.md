# Memory v1：openpi训练模型与checkpoint集成
# 目标

# 样本时序验收补充

必须核对已转换LeRobot的action列是否已经表示下一帧关节目标a_t=q(t+1)。若已经移位，不能直接把action列绑定为raw robot_joints并再用offset=1，造成二次移位。应按实际列语义选择key/action时间offset（例如已对齐action用offset0），并用同一个episode/query与旧可靠loader/原始timestamp逐行比较机器人目标；比较P2两臂时这些机器人目标完全一致。memory的current truth也不能从lagged input推断。给绑定列、索引定义和小样本证据，而不是仅凭shape通过。此项是已有数据语义核对，不新增算法。

把已经提交的memory_config轻量契约实际接入独立openpi的训练数据/模型/metadata，让同一schema可以训练full、serial、no-memory和辅助监督无递推对照。用户已授权实施及实验，Manager负责审阅合入/正式任务排程。你负责训练代码和短smoke，暂不启动20k正式run。

# 工作区与边界

保存/恢复写集已拆出：dc61ef10-53f0-44c2-91cc-c78d1cb6676e负责training/checkpoints.py、checkpoint_metadata.py、policies/policy_config.py及对应tests。你不再改这三文件；继续独占config.py、scripts/train.py、data_loader、memory_data、models/transforms及训练tests。请在TrainConfig增加save_dtype: Literal['bfloat16','float32']|None（默认None，首批配置bfloat16），供checkpoint owner使用。最终20k唯一保存由你配置。当前norm裁定：机器人使用同一shared stats，one-hot memory在Normalize后identity追加，不进入stats。给Manager/保存owner明确resolved memory_config唯一保存位置及加载时所用transforms接口，避免彼此猜schema新入口。普通checkpoint推理不能依赖训练dataset存在，此边界由保存owner保障、你提供不读数据的transform工厂。无需等待保存owner才能先完成实际数据/模型loss CPU检查；最终GPU smoke合入其commit后一次完成。

环境恢复裁定：de79新增PyYAML但缺lock更新，独立修复commit为0dc120c（uv.lock两行）。已有登记worktree不反复调用workspace add；在自己树cherry-pick修复后，沿受版本管理scripts/worktree_env/create_worktree_env.sh第268行以后的lock检查、独立uv venv、sync frozen/hardlink、import验证恢复，不复用他人环境。通过后报告证据，Manager修复本task的MAM failed状态记录；不扩展MAM实现。

用mam workspace add --repo openpi --base de79cce20e54c612634fdc2598b91cc0ab5034ec，读取AGENTS.md。只修改src/openpi、scripts训练/norm/checkpoint相关入口及其tests/训练文档；packages/openpi-client由f252006a-8676-4d10-b6a1-1a791d91c6a6负责，examples/converter由7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2负责，不能重复修改。不要动legacy RMBench/policy/pi05或robot-bridge。后续API修订按明确commit cherrypick到自己的worktree，不能PYTHONPATH挂他人临时树。

# 契约与必须达到的行为

wash转换待修复：Manager发现当前adapter的state/action都取follow_*，与已确认S2M slave状态→master动作不一致，data owner正核对准确旧drawer实现并修复。现有all_172_15hz不可作为已验收训练资产；wash应绑定独立robot_action序列及正确offset，不能以robot_observation_state下一帧代替master action。sim已确认的action14维offset0路径可以先集成/smoke，勿等待wash修复停工。

wash实际合格172ep，15Hz有13,404行无phase GT。保留机器人样本，不能用unknown/initial做缺标注的phase target监督，不能因H50任一行缺GT就整sample删除。API owner被要求增加EpisodeMemoryData可选availability（series key→bool数组，缺省全true），缺GT输入回退initial、目标逐字段loss0且dense全0；你复用helper权重，不另写一套缺GT采样规则。sim action已确认预移位q→q+1，首批绑定其14维offset0，别再从obs q+1重建末尾动作。数据owner将提供精确episode binding。

读f252任务已发布task/report及实际openpi_client.memory_config代码。load_memory_config -> ResolvedMemoryConfig，make_training_sample(EpisodeMemoryData, query_index, rng) -> ordered input/target IDs、dense_actions、逐坐标action_loss_mask/action_loss_weights；compile_model_spec(model_config)给编码/decoder/Pi0 kwargs。API owner正在精简内部及修复重复YAML key/invalid dense零向量；公开接口大体保持，准确以修订commit为准。你不重写parser/one-hot切片。

1. TrainConfig可配置YAML/path，运行时解析一次；数据adapter绑定series/constants/events，不从目录名推断任务或phase语义。RMBench这批使用demo_clean_state源、明确metadata，不把这项实验来源限制硬编码到通用train/model。wash-cup真机同入口。全部相对路径按openpi项目根解析。
2. token新schema默认每字段独立argmax。必须避开现有_select_key_state默认第0字段递增/3字段button特例，新config仅按显式decoder_rules选类；历史checkpoint没memory_config保留既有行为。full/serial词表顺序一致。序列化head schema、条件路径和推理入口必须一致，不能训练了新头但保存后loader走另一模板。
3. P2两臂full H50/K30：phase(t+j+1) vs重复phase(t+30)，公共逐坐标mask由两时刻均有效决定；phase固定H分母，不按valid-count重新归约。robot目标/其余字段不受phase mask影响。masked目标数值全0仍需要loss mask，不能只改target。逐坐标weight应在flow-matching误差按维度归约前应用一次，不能bool化抹去H/valid_count权重。loss中的模型padding、坐标平均和memory lambda写清并固定，不重复乘lambda。用真实compute_loss的测试验证invalid phase梯度/机器人权重、全invalid末尾、两臂同有效位置。
4. no memory=空字段；辅助监督控制仍有字段/head/loss，但train/infer输入均initial、无递推消费。复用现有模型类，不增加aux专用架构。新schema表示仅categorical joint_dense one_hot/serial token，未实现类型显式拒绝。
5. 规范化使用现有pipeline/norm stats，memory编码和反归一化的先后与部署一致。新memory是否参与norm必须明确，不能把机器人14维norm广播到memory。首批两臂机器人norm/fields完全相同。转换数据不需因目标时刻不同重转视频；从当前真实标签生成目标/lag，勿将旧lagged输入当当前truth。
6. checkpoint已有train_config/metadata中嵌入resolved memory_config一次，不另保存重复model_spec。checkpoint仅给路径应能恢复模型、memory fields/协议、norm；不能依赖临时worktree或原YAML路径仍存在，不要求推理加载训练labels/data。
7. 新训练单卡batch32、20k，只保留最终20k模型BF16权重约12GB与必要metadata，不保存优化器/ema/多步checkpoint。核对JAX/Orbax实际保存/恢复，只在缺少现有参数时增加一个保存dtype选项；BF16计算不等于参数已BF16。不能用full-state训练状态包冒充model-only。正式run唯一目录，已存在拒绝混写或明确resume，但不为历史错误写兼容。

# 验证/资源/交付

Manager已经把P2确切标量loss公式固定到 /root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md 第6节：L_dense=sum(w*逐坐标FM误差平方)/(B*H*D)，D为相同padded维度；phase权重公共mask×lambda一次、padding0、机器人clamp保持1。其他字段若valid_mean用mask×H/max(valid_count,1)。helper产生的action_loss_weights必须在坐标归约前数值乘法应用。旧MEMORY_CONFIG统一valid-mean表述已由Manager修正；以新实验公式/配置为准。不能为了复用旧分支在masked phase时将整行robot loss清零。

先给代码量预估；优先复用既有transform/model/metadata。CPU针对无memory、单字段wash、多字段drawer/rearrange、动态phase顺序、mask/loss、metadata roundtrip；适用旧tests通过。你可独占本机GPU1进行短训练/保存加载smoke（先核对该卡实际空闲，只设置CUDA_VISIBLE_DEVICES=1且不占他卡）。base由资产任务恢复到/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base，data路径由Manager同步，不用随机参数smoke冒充base加载通过。完整50步train smoke+最终BF16保存/只checkpoint恢复测试有资产后开展，缺资产时CPU工作继续。只有短smoke授权，20k另行派发。

保存需要的检查结果和大小/张量dtype/模型输出对齐证据；代码固定commit后给Manager准备独立review。报告task_revision/workspace/commit、测试、未完成与可复跑命令，发布；自己清理smoke/临时文件，不动正式资产或共享环境。预计>1小时程序登记mam job；不自行派agent。
