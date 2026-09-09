## 留痕补齐（现有验收要求）

Manager已查新sim sidecar目录只有episode_memory/binding_manifest，未保留command.txt及上游metadata。请在生成产物旁的metadata保存实际生成命令及本次git commit、使用的binding/config、沿既有数据链继承转换/source metadata；只复制metadata/config，不复制代码或dataset/videos/标签矩阵。代码和正式生成命令先固定，重新生成这份小sidecar以留下真实记录（不能事后编造不存在的原始command）。新的wash正确转换同样遵守。使用项目现有布局和简单复制，不新增provenance体系/重复runtime。checkpoint owner已被安排在保存时继承这份metadata；它沿sidecar_path父目录的metadata发现即可，保持训练与RMBench不耦合。

## Sim binding接口收敛（4815273后的Manager裁定）

4815273正确恢复了额外raw最后帧，但新增的manifest.tail_append协议当前训练adapter不支持。不要再实现一套tail_append扩展/解释器。采用既有sidecar绑定：sidecar直接保存等长M+1的series（phase/属性及robot_action_target），机器人前M行逐值拷贝converted action[:14]，第M行重复末动作；availability也M+1。图像/robot state及query仍来自原LeRobot的M行，query范围不变；初末行逐值测试不能省。这里只有低维数组复制，图像和原数据不复制，不会新采样不存在的query。MemoryBindings用source=sidecar指向robot_action_target，semantics=action_at_row、offset0；训练层移除仅允许robot source=column的无必要限制，保留不能绑定observation state与禁止二次移位检查。这样不修改已验收core API，也不新增tail_append schema/第二种补尾配置。

适配器里的账号绝对DEFAULT_LEROBOT_ROOT/RMBENCH_DATA_ROOT/ARTIFACT_ROOT删除；源路径由明确参数传入，输出默认路径若需要则从本openpi项目根构造。相对参数按项目根解析。完整实验命令可写本集群绝对路径。路径检查不依赖作者workspace，shared产物写入原openpi的data软链目标。请data owner以独立增量commit更新，training owner沿既有sidecar reader直接使用。

## 2026-09-10 独立review后的优先级与阻塞修复

先交付examples/rmbench的sim bindings及正式YAML独立commit，让训练与review继续；wash修复可随后推进。James已确认wash master v2的视频与pose/action source索引漂移：ep0 face q23为46对43，q765为1515对1527，q1205为2387对2407，最大20 raw frame。其报告见任务3e78bfec-0cb7-41f4-ab7c-e002adf50c88/report.md。v2不能用于训练。视频、状态、next master action及标注必须共用真实可审计的时间/source mapping；不能仅改offset，亦不能继续复用不同时间轴的视频。保留原始时间与选择依据，先小样本独立核验后完成正确的新输出。提交前在raw/converted逐帧比对两集、多相机、开头/中段/尾部，除了shape还要验证视觉帧与pose/action索引相同。不要为省重编码成本牺牲时间对齐。请报告sim独立commit和wash修复预计耗时。

# Memory v1：数据适配与wash-cup转换

首批八卡所需sim配置除已有四份P2 full外，还包含rearrange serial fixed lag30/current query target和rearrange no-memory。请沿同一sim sidecar/bindings给两份英文可运行YAML；serial时序规则与本任务wash serial一致，但字段使用rearrange三字段，no-memory用memory=[]及空updates。只增加对应配置，模型实现仍归训练owner。不会要求扩其它三个任务后才能先启动这六项。


## 阶段事实后的Manager裁定

文件归属：新sim adapter、其tests和rearrange/put-back运行YAML放examples/rmbench/及其memory_configs/；wash保持examples/x2robot/。不要将RMBench适配代码塞在x2robot目录下。尚未提交的新文件直接移到正确目录并调整import即可，不增加公共框架，也不为搬路径重复转换数据。

首批可运行YAML的协议必须按实验计划核对：当前wash_cup_phase_serial_t_plus_1.yaml使用train/infer均initial、target t+1、空feedback，是另一种辅助任务，不能作首批serial基线。首批wash full：当前reference输入（首次/缺GT用unknown）、infer cache、phase target t+j+1、chunk_completed消费last_executed。首批wash serial：输入同一named previous lag30（train reference t-30，负索引/缺GT才initial）、infer cache；query phase target t（offset0/stride0），current_condition train reference/infer selected，query_selected反馈预测phase供下一query。两者H50/K30、同domain与S2M动作目标，不夹带ordered decoder。serial不套P2未来两个时刻的公共validity；其query当前GT可用就监督，不因t+30缺标注静默屏蔽。P2公共mask只用于计划中rearrange/put-back的两组full受控比较；wash full第一批不需要重复endpoint配置。所有实际基线YAML必须有闭环反馈，initial-input/空feedback只属于明确命名的aux对照。提交前逐项与/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md核对，报告不能仅以YAML可parse为通过。

S2M输出存在阻塞疑点，优先核对/修复：你当前wash_cup_memory_adapter.py注释宣称Drawer S2M只用follower，load_s2m_trajectory却state/action都返回同一follower数组。用户确认的是从臂当前state→主臂action；旧drawer policy metadata也明确slave_state_dim14/master_action_dim14，独立openpi标准converter v5含follow与master两套键。请立即对照旧drawer准确converter commit及X2RobotInputs(mode=s2m)定位实际action切片，不能用名称S2M或shape14代替语义。除非可靠原始接口证据证明另有含义，wash应state取follow_*14维，action取master_*14维并按正确下一对齐帧取值；两者不能共用robot_observation_state序列来构造action。提供同一raw帧对应两套不同数值的逐值对照，修复共享转换metadata/配置，不改raw源。当前all_172_15hz仅是待验收转换产物，不能当训练可用资产；修复时独立新输出目录、保留最小错误说明后清理未使用的错误产物，视频可安全复用而不重复解码。若你认为旧drawer本身确实follow→follow，明确报告与用户S2M要求的冲突供Manager裁定，不自动沿用。训练owner已通知等待修复。

已读172合格/72剔除、13,404行缺phase GT和sim action预移位报告。wash保留全部合格episode的机器人数据；不因full需要未来50行标注而整sample删除，否则造成未声明的采样选择。API owner会增加EpisodeMemoryData可选availability（series key→bool数组，缺省全true）；显式缺GT输入用schema initial，目标逐字段mask/weight=0且dense全0，不能把unknown当已知phase监督。转换保留原始availability，不自行在适配器实现第二套mask/loss算法。

sim直接绑定已转换action的机器人14维、offset=0，以精确复现原有q→q+1标签；P2两臂共用这些目标，不为尾部重新从observation.state生成另一套动作。继续全量内部行级核对，缺raw尾部只列具体缺口，不重复转换已有视频。原始scene_info/language_annotation及每集末尾动作数值的补核将交资产任务恢复；尽量远端只读提取需要的末帧数值/形状/来源，不需先传所有含图像HDF5才推进训练。若现有converted已给全部当前target和input获取边界，则注明哪些原始事件是新schema实际必需，哪些只为额外审计，避免把不用的原始文件作为开跑硬阻塞。
# 目标

# 样本时序验收补充

必须核对已转换LeRobot的action列是否已经表示下一帧关节目标a_t=q(t+1)。若已经移位，不能直接把action列绑定为raw robot_joints并再用offset=1，造成二次移位。应按实际列语义选择key/action时间offset（例如已对齐action用offset0），并用同一个episode/query与旧可靠loader/原始timestamp逐行比较机器人目标；比较P2两臂时这些机器人目标完全一致。memory的current truth也不能从lagged input推断。给绑定列、索引定义和小样本证据，而不是仅凭shape通过。此项是已有数据语义核对，不新增算法。

# API已提交，可开始接入

轻量契约commit：openpi de79cce20e54c612634fdc2598b91cc0ab5034ec（API owner正在精简内部/修复，后续补commit，当前可供开发）。ResolvedMemoryConfig.compile_model_spec(model_config=None)返回MemoryModelSpec；属性为representation、field_names、field_values、initial_ids、encoding、dense_offsets、robot_dim、padded_dim、action_horizon、execution_rows、target_layout、loss_kind/loss_weight、current_condition、decoder_rules、feedback。共享方法encode_dense_ids(ids)、decode_ids(ids)、decode_dense_actions(actions, previous_ids)、decode_token_logits(logits, previous_ids)。训练sample额外给dense_actions/action_loss_mask/action_loss_weights。具体以该commit代码/owner report为准，不做两份切片/解码器。后续由ad6bb77e-3892-4730-ae1a-7d9cd99a5728负责src训练接入，f252只维护轻量package。


# 用户最新数据约束

用户明确指定RMBench训练/转换只用demo_clean_state；demo_clean没有metadata及详细子任务划分，不允许用作fallback。wash-cup原始数据不受此命名约束。已转换仿真数据须沿metadata确认来自demo_clean_state，并核实所需真值/事件完整；来源不明先不训练，不从评测rollout重建标注。

资产owner已定位旧converted源：/mnt/public3/xcj/cache/huggingface/lerobot/{rearrange_blocks,put_back_block}_demo_clean_state_shared_memory，分别50ep/20103frames、50ep/17588frames，正恢复到本集群/mnt/public/xcj/cache/huggingface/lerobot/同名目录。包含action、observation.state、key_state_input/target/mask、index/timestamp；rearrange还有key_state_guard_offset，meta/rmbench保留转换与source/key-state metadata。尚需你检查是否足够绑定series/constants/events和P2当前真值（不能将lagged input误作当前truth），若原始详细边界缺失则精确列出所需raw文件让Manager安排恢复。不要依靠目录名自行宣布来源已核验，也不要为了框架接口重转全部图像。此事与wash-cup转换可并行。

# 已确定共享接口（API owner的先行契约）

openpi-client模块为 openpi_client.memory_config，load_memory_config(path_or_mapping) -> ResolvedMemoryConfig；to_dict()为metadata.memory_config。训练入口 make_training_sample(EpisodeMemoryData(series, constants, events, tail=None), query_index, rng) 返回input_ids/target_ids/逐行target_mask、robot目标索引/有效位和lag_draws；字段顺序为memory列表。model_spec()提供representation、词表/initial IDs、dense offsets或token sizes、loss和显式decoder/反馈。validate_model_dimensions(robot_dim, padded_dim)检查已有模型维度。具体可调用属性以owner首个commit为准，先通过该helper复用契约，不复制parser。

input train/infer显式source=initial可作为辅助监督无递推对照；memory=[]为标准无记忆。正常新schema默认独立argmax，历史规则仅显式配置生效。首批H50/K30；P2两full配置仅phase目标时刻不同，共享mask和固定H分母。跨agent的工作树代码需通过明确commit集成，不能把对方临时workspace长期加入PYTHONPATH。需要伴随openpi代码时在自己MAM任务下增加openpi worktree并接owner提交，或用自身venv安装该commit构建的轻量包，勿改共享环境。


在独立openpi中准备统一schema的数据适配与首批wash-cup转换，支持同一memory字段定义供full/serial训练使用。后续RMBench新训练复用现有真实标注，不新增另一套任务语义。可实施转换，暂不启动正式模型训练。

# 工作区与分工

用mam workspace add --repo openpi --base 71c80db723a242c61cfe429dd6794e9ece3cbcf1创建环境/worktree；读openpi AGENTS.md。写入范围openpi/examples的数据转换器、新数据适配模块/配置和对应定向测试。不要改src/openpi或packages/openpi-client（任务 f252006a-8676-4d10-b6a1-1a791d91c6a6 owner负责）。若需RMBench薄转换入口，用其worktree e31d14fe0818235d471b371924ea30c273e75c7a且先报Manager；不改legacy policy/pi05的算法/转换实现。不要写robot-bridge。

# 数据与语义

1. 原始wash-cup /mnt/public/datasets/x1pro/wash-cup，annotation_layers.json给子任务标注位置。扫描并给确定筛选清单：任何label6、缺标注文件、labels1..5不是各恰好一次都剔除；次序允许变化。其余全部训练，不划分holdout；固定5个合格训练episode做offline并记录IDs。phase是当前子任务，不是已完成到哪步。沿用drawer S2M输入/动作定义、真实时间戳/频率与相机映射，不猜SM2SM。
2. 首轮只一个phase，full与serial使用同一有序domain/标注；顺序可变，不能默认按1到5推进。初始值如何在未知顺序下合法：若第一label并不恒为1，报告事实并设置显式unknown或由可观测的初始化定义，不能在推理偷用训练episode首标签。不要把domain ID和原始label ID混用。
3. 抽取现有drawer/rearrange多字段转换中可复用的sample/time绑定，明确normalized series/constants/events映射。原始数据转换只保存真实标签和可用性，不把每次实验的phase目标策略写死进数据导致重复转换。P2在训练sample阶段从同份标签生成目标/mask，保留t+1 vs t+30和采样边界。
4. 配置唯一解析器由f252任务提供，checkpoint metadata键memory_config；先整理标注适配/读写入口，接口到达再接，不抄第二套schema。无需扫描所有历史实验或另造统一data framework。新数据结果放共享主openpi的gitignored data目录，按明确dataset/run命名，不指向你临时workspace。
5. raw数据只读。转换数据保存命令+commit+resolved配置+源标注路径及筛选统计/IDs等既有metadata链。先小规模转换验证schema/标签/视频同步，再提交代码再正式全量转换；预计超过1小时进程登记mam job。清理成功正式转换替代的临时smoke，不让结果根混乱。

# 验收与交付

报告有效/过滤数和原因、phase次序统计、数据/5ep输出位置、必要空间估算。测试label6/缺标注/重复/缺类/任意顺序、标签边界、S2M shape/时间对齐；读回生成数据验证。代码量先预估，复用优先；新文件名/接口尽早发Manager。未获分配不占GPU，CPU解码可用；不运行模型训练或真机。最终report含task_revision/workspace/commit与验证，发布等待归档，不自行派agent。
