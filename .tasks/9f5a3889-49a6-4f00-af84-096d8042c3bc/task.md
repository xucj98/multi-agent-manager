## terminal修复的结构裁定（替代“不改Base任何代码”的过严限制）

92b365c通过每轮替换_policy_client为代理来跳过terminal infer，功能方向正确，但新增临时client身份/包装器没有必要。Manager此前要求“不改Base”过严；应保留已有执行顺序与通信机制，不必禁止最小退出契约。

请删除_TerminalInferenceSkippingClient和sim的run_iteration包装，采用已有build_policy_obs hook返回None表示这轮不调用policy；Base在该hook后作None检查并返回skip，文档/类型同步。simulation仍先处理terminal observation的真实执行进度/trace，之后返回None；其_loop_step会按_episode_terminal结束。Base不读取仿真字段、不加新RPC、session或调度循环；live/offline正常dict返回行为不变。保留并复核actual run_iteration的infer_count=0、execute=0、terminal actual_k/next_query，以及非terminal/reset/takeover原路径。此小修单独commit，以其作为F0正式候选。

## F0额外小修：terminal不再调用policy

Eval owner在RMBench commit9e8fccbd2fa004f18a3cbcc301e7387b02edaccf报告：terminal观测的trace写next_query=false，但基类循环仍实际infer后才跳过action。请在OpenPISimulationScheduler现有边界最小修正terminal时跳过真正policy调用，保留SchedulerBase/真机循环；定向测试同时计policy.infer调用数和trace。请作为独立小commit先交F0review，不必等live三个P1一起交付。

## 独立review裁定：真机完成进度必须修正

Pascal起始审查在0bc5129d-623c-4c3d-8bce-b8c172ccca56/report.md给出三个P1复现，Manager确认其是新memory反馈的真实阻塞，不能用445 tests通过覆盖掉：
1. tracker按入队timestamp越过观察时间计completed，但x1/x1pro执行线程未实际发送也会completed=1（合法单行chunk可发送0次）。完成证据需对应实际执行线程处理及本chunk/行映射，不能以时间到期冒充执行。
2. clear_actions的cut只按timestamp筛除，滞后worker可能保留未执行旧proposal作为下一插值anchor。保留已验证控制循环与通信方式，最小修正清除语义，不能接管后继续执行尚未处理的旧proposal；不要大改控制频率/插值算法。
3. tracker.observe是全局累进值，无图get_obs可先推进计数，较旧图像对齐get_obs随后也返回已推进进度。反馈证据必须绑定本次返回观察的时间基，不能被UI或其他请求提前消费。

请复现并给最小修复commit及实际线程/队列测试。若涉及真实硬件行为仍不能证明，用精确未验证边界报告，不宣称硬件通过。mock/sim的同步take_action计数可以独立验收，故本修复不要阻塞已提交F0仿真路径的独立review/smoke。完整scheduler commit fd38513已交Pascal继续审；新修复请单独commit便于追踪。完成或部分进度直接写report并发布。

# Memory v1：真机仿真offline统一反馈

## 环境恢复裁定

de79新增PyYAML但缺lock更新，独立修复commit为0dc120c（uv.lock两行）。已有登记openpi worktree不反复调用workspace add；在自己树cherry-pick修复后，沿受版本管理scripts/worktree_env/create_worktree_env.sh第268行以后的lock检查、独立uv venv、sync frozen/hardlink、import验证恢复，不复用他人环境。通过后报告证据，Manager修复本task的MAM failed状态记录；不扩展MAM实现。
# 目标

# API已提交，可开始接入

轻量契约commit：openpi de79cce20e54c612634fdc2598b91cc0ab5034ec（API owner正在精简内部/修复，后续补commit，当前可供开发）。ResolvedMemoryConfig.compile_model_spec(model_config=None)返回MemoryModelSpec；属性为representation、field_names、field_values、initial_ids、encoding、dense_offsets、robot_dim、padded_dim、action_horizon、execution_rows、target_layout、loss_kind/loss_weight、current_condition、decoder_rules、feedback。共享方法encode_dense_ids(ids)、decode_ids(ids)、decode_dense_actions(actions, previous_ids)、decode_token_logits(logits, previous_ids)。训练sample额外给dense_actions/action_loss_mask/action_loss_weights。具体以该commit代码/owner report为准，不做两份切片/解码器。后续由ad6bb77e-3892-4730-ae1a-7d9cd99a5728负责src训练接入，f252只维护轻量package。


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

P2补充：full的“重复终点”是H行监督label相同，实际预测H行仍可能不同；两臂统一读取第30行。只有模型实际输出完全相同的值时两种取行才等价，不能把重复训练目标当作首行/末行/均值随便替换的依据。query-level单输出是另一个结构，不在P2中混用。

旧full时序锚点已实测：任务a15fdd25的83cbec9入口通过2rollout smoke，旧scheduler是get_obs取得logical_step advance后反馈末已执行行，K30完整执行取row30。当前缺独立row20 selector与逐query trace，所以P1 K30/row20尚不可运行。请在新schema反馈配置路径支持row index及trace（本任务原要求），并说明如何为该旧full checkpoint显式提供等价schema来做这项诊断；只用其真实字段/归一化信息，不发明全历史兼容转换器。基线row30必须先核对同输入输出/反馈一致，再开始row20。旧checkpoint无schema路径继续保留。

定向mock/offline CPU tests覆盖单字段、多字段、completion vs accept、partial/takeover/rejection/reset、首行与末执行行、同值的chunk目标两种row等价、无schema既有路径未变；按库规范跑全tests。不触碰真机、不跑GPU；GPU smoke待Manager分配。先报告代码量预估与接口需澄清处，之后提交commit，report记task_revision、workspace、commit、测试/未完成，发布。任务完清理自己的短smoke与临时文件，等待归档；不自行派agent。
