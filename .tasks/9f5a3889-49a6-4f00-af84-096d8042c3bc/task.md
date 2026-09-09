# Memory v1：真机仿真offline统一反馈
# 目标

# 已确定共享接口（API owner的先行契约）

openpi-client模块为 openpi_client.memory_config，load_memory_config(path_or_mapping) -> ResolvedMemoryConfig；to_dict()为metadata.memory_config。训练入口 make_training_sample(EpisodeMemoryData(series, constants, events, tail=None), query_index, rng) 返回input_ids/target_ids/逐行target_mask、robot目标索引/有效位和lag_draws；字段顺序为memory列表。model_spec()提供representation、词表/initial IDs、dense offsets或token sizes、loss和显式decoder/反馈。validate_model_dimensions(robot_dim, padded_dim)检查已有模型维度。具体可调用属性以owner首个commit为准，先通过该helper复用契约，不复制parser。

input train/infer显式source=initial可作为辅助监督无递推对照；memory=[]为标准无记忆。正常新schema默认独立argmax，历史规则仅显式配置生效。首批H50/K30；P2两full配置仅phase目标时刻不同，共享mask和固定H分母。跨agent的工作树代码需通过明确commit集成，不能把对方临时workspace长期加入PYTHONPATH。需要伴随openpi代码时在自己MAM任务下增加openpi worktree并接owner提交，或用自身venv安装该commit构建的轻量包，勿改共享环境。


接入统一memory_config，使robot-bridge的真机、offline、仿真scheduler按同一份checkpoint配置维护多字段记忆，保持经过验证的通信、takeover和reset。实现与定向CPU验证，不启动正式GPU实验。

# 工作区与写入范围

从robot-bridge b17f6c53ffbc1030972a9820cf592f28b937d501 用mam workspace add创建独立环境/worktree，读AGENTS.md及docs/design/conventions.md。只修改robot-bridge和其相关tests/功能文档。openpi契约owner任务 f252006a-8676-4d10-b6a1-1a791d91c6a6，接口会由Manager发布；不要复制实现第二套parser、不自行修改openpi/RMBench。只读现有规格 /root/Documents/task-state-vla-paper/docs/MEMORY_CONFIG.zh-CN.md，接口调查 .tasks/8584105e-adae-4a96-83f2-af47cece6bf8/report.md。

# 实施约束

1. checkpoint metadata的memory_config（schema_version、memory有序字段、protocol）为事实源。openpi-client将提供轻量validator/字段工具；scheduler不导入训练框架。旧模型仍走现有已验证路径，新schema路径显式运行；不再扩展旧格式兼容。
2. scheduler持有语义memory/context，一个scheduler同时一个robot/policy；backend转发模型结果并提供reset，保留DM05/Mem-0已有内部算法缓存行为。无session、无通用插件总线、无get_progress新RPC。不要重构SchedulerBase的调度循环。
3. 保持execute之后带wait_condition的get_obs；不能把chunk accepted冒充已执行完成。多字段通用处理，field数不是模型/任务专用分支。默认独立argmax，wash-cup顺序可变不施加固定顺序；full和serial共享同一个字段schema。UI从domain显示字段和值，不手写wash/drawer字段。
4. 反馈按声明时刻与选行：query-level serial不依赖动作行；full row选first/index/last_executed，必须使用实际执行进度；前者合法与否取决于目标时间定义，不统一强改成首行。保留pending chunk预测到现有get_obs确认/同步执行返回后再提交需要完成事件的反馈。能力无法提供k时应在启动阶段报明确不支持，不能猜K已全部执行。跨chunk、episode终止、execute失败、takeover中断、reset不回灌错误pending。
5. 解码在动作反归一化后，缓存语义类别然后再次编码；不能把model padding或者动作原始连续尾部当语义ID。输入/feedback/reset的实现由三类scheduler共用，避免每个scheduler一份逻辑。字段/协议由metadata透传，runtime要检查它能支持所声明event/row。
6. 记录每query的目标参考时刻、计划K、实际k、选行/最终反馈、下一次消费，依托现有diagnostics/context；保留episode成功率全部分母。数据引用/Oracle不能进入普通推理。RMBench负责结果格式与目录，统一仍由其recorder写RMBench/eval_result/<exp-group>/<run>，不在robot-bridge产生正式eval_result目录。

# 验收与交付

定向mock/offline CPU tests覆盖单字段、多字段、completion vs accept、partial/takeover/rejection/reset、首行与末执行行、同值的chunk目标两种row等价、无schema既有路径未变；按库规范跑全tests。不触碰真机、不跑GPU；GPU smoke待Manager分配。先报告代码量预估与接口需澄清处，之后提交commit，report记task_revision、workspace、commit、测试/未完成，发布。任务完清理自己的短smoke与临时文件，等待归档；不自行派agent。
