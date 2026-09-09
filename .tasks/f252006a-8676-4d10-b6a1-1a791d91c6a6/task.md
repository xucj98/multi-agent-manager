# Memory v1：统一配置与openpi训练接入
# 目标

# 用户最新数据约束

用户明确RMBench新训练与转换只用demo_clean_state源，demo_clean缺metadata/详细子任务标注，不作为数据fallback。训练接入模板和metadata验收要保留这个来源区别；实际路径由资产/data任务提供。与wash-cup命名无关。

此数据限制只属于本批RMBench实验的来源验收/任务配置，禁止在通用schema parser、模型或TrainConfig中硬编码demo_clean_state目录名、RMBench字符串或允许的数据集清单。通用训练必须仍能接真机及其他仿真，数据内容/所需标签的校验应与路径命名分开。不要把Manager的实验来源约束变成库级限制。

在独立openpi实现首批实验可用的统一memory配置、训练样本与模型接入。用户已经授权施工/开跑；你负责代码，不直接启动正式训练。Manager掌握研究方向和合入，另有agent负责数据转换与robot-bridge。优先最小可审查实现，不构造通用DSL/插件系统。

# 工作区与写入范围

复用已登记的openpi worktree。现在独占packages/openpi-client及其定向tests；src/openpi和scripts训练/模型/metadata改由任务ad6bb77e-3892-4730-ae1a-7d9cd99a5728并行负责，不再修改这些路径。以上训练需求继续作为接口要求，你交付契约/sample/权重后即可完成该任务。不改examples和robot-bridge。论文规格只读。各库AGENTS.md和之前报告仍适用。

# Manager裁定与第一版范围

1. 单一schema事实源放在独立openpi的轻量openpi-client package中，供训练与scheduler共同读取；不另建repo/重依赖、不让robot-bridge导入JAX/torch。checkpoint metadata保存解析后的memory_config字典（含schema_version），训练入口可接YAML。不复制E/record的结果引用到执行配置。数据/机器人维度和normalization沿用模型配置并做一致性检查，不要求用户重复填写。
2. 保留S有序memory字段和P输入、目标、representation、反馈明确分离。首版支持categorical、joint_dense one_hot与serial_token token，以及无memory（memory=[]）；不要把一期未实现的scalar/pose2d/parallel等静默视作可运行。既有模型行为通过显式配置保留，后续扩展能力有实际实现才开放。
3. 不能凭字段位置/类别数推断phase/attribute/button规则。新配置默认独立argmax。历史ordered/latch/conditional若用于旧权重必须显式编译到现有选择机制；wash-cup1..5顺序可变，默认允许任意类别。shared categorical集合/顺序在full和serial两种表示中完全一致。
4. 训练标注来自数据适配器的series/constants/events；单样本命名lag只抽一次，多字段共享。input不读未来。模型尺寸、norm stats、base初始化和任务标签不混入scheduler。
5. 首批P2：H50、执行K30。phase目标两种：t+j+1（j=0..49）与所有行t+30；其他memory字段与robot目标保持同一协议。phase两组公共mask为(t+j+1<=L) AND (t+30<=L)，无效phase槽都置同一零值且loss=0；loss用固定H分母，不按有效项数除。机器人越界取末帧，机器人与其他字段loss不受phase公共mask影响。需要可表达的有限validity/loss-reduction配置，别用全局tail冒充这个控制。不实现任意mask表达式语言。边界、全invalid样本和连续多字段mask用真实训练loss路径验证。
6. 新训练统一单卡bs32、20k steps、仅最后20k checkpoint。用户要求最终BF16模型权重约12GB和metadata，自包含；确认当前JAX/Orbax的save/restore路径能保留BF16，不将优化器/ema/所有step附带保存。优先复用现有参数；如确需增加保存dtype参数，仅一处显式配置。不能声称BF16计算就表示内部参数已BF16。只改当前训练所需路径，不做LoRA/旧smoke格式兼容系统。
7. 新schema checkpoints必须只给路径即可恢复相同模型、字段、norm与输入协议。既有公开/正式旧checkpoint沿现有loader，后续定向同输入比较验证，不为所有旧格式新建兼容层。

# 跨agent契约

新增数据事实与最小契约补充：wash-cup 172合格ep中每集都有内部/尾部未标注区间，15Hz共13,404行无phase GT；unknown是占位不是已知类别事实，不能监督为initial。请给EpisodeMemoryData增加可选availability（按reference的series key映射等长bool数组；缺省代表全部有GT），而非新增schema表达式语言/任务专用分支。现有key不存在仍报错；显式availability=false时输入使用字段initial，target对应位置mask/weight为0、dense编码全0。机器人监督保留，不能为了full H50把整sample或整episode扔掉；reference-mask与availability两者区分。向训练/数据owner明确最终签名，增加有实际数据依据的缺GT测试。若你判断此接口无法在不引入歧义的条件下接入，先给一个明确替代方案供Manager裁定，勿将unknown当GT继续。P2首批sim全标签适用原公共mask；不声称all_in_bounds已表达跨两个候选时间的annotation-availability交集。论文patch同步规范化数据接口的availability及输入fallback/目标loss规则即可。

你是配置/API owner。尽早（先于大实现）报告你准备暴露的轻量helper函数、resolved memory_config结构与数据入口，控制在一屏；Manager会把确定接口发布到其他任务。沿用已给YAML名称，必要精简给理由，不自行大改设计空间。数据agent只改examples/适配器，runtimeagent只改robot-bridge。不要让它们猜接口。

必要对照补充：为区分辅助监督与递推输入，支持字段输入显式使用initial（train/infer均可），部署保持initial而不消费预测；状态目标/loss与同形状full保留。优先通过input source=initial和已有反馈禁用的清晰表示实现，不再加独立aux模型类。memory=[]是标准无记忆baseline，辅助对照仍保留memory字段/目标；两者不能混称。P3任意constant label覆盖不属于第一批阻塞项，可后补。

留痕精简：resolved memory_config只需在checkpoint已有train_config/metadata链中有一个权威可读取位置，不再并行保存一份重复model_spec/字段切片配置。model_spec在加载时推导；backend的metadata透传同一个配置对象。raw YAML路径不是自包含，恢复不得依赖已经清理的worktree。P2的公共phase loss mask必须作用到逐坐标损失上，不是只把target置零；phase有效行比例做数据诊断，不能降低机器人loss权重。

# 验证与交付

环境阻塞修复优先：de79cce新增openpi-client PyYAML依赖却未同步uv.lock，已导致training/runtime两份新worktree的uv lock --check失败。你负责同步最小lock变更（本次允许修改根uv.lock）；不换源、不升级无关包，先提交独立修复commit给依赖方恢复环境，再继续API精简。验证uv lock --check通过，报告锁文件实际差异。

Manager对de79cce的修订要求：模块1480行、合计1838行明显高于450+250预估，先做实质精简再交付，不以减少换行冒充简化。保留已公布runtime/sample接口，减少重复的to_dict/parse对象映射与未使用包装，不要为新API加backward-friendly别名，去掉validate_first_batch_protocol这种通用库硬编码H50/K30的入口。可以复用项目已有结构校验机制，保留必要语义与范围检查；目标轻量模块约800-1000行以内，若合理实现仍超出给逐项原因，不删关键校验凑行数。修复两个具体问题：YAML重复key必须拒绝；invalid memory目标在dense编码中必须是真正全零向量，不是one_hot(ID0)，并同时保持逐坐标loss为0。B/T公共mask对应的时刻、固定H分母和lambda只应用一次须在helper文档/API说明清楚。维度来自现有model/data配置，不能强制重复填写；若load阶段尚未绑定维度，compile/sample时显式绑定而非假定所有机器人14维。首个de79cce供依赖方开发，尚未最终验收。此次只收敛契约/测试，不做src训练接入或GPU smoke。

设计文件同步交付：在你workspace提供一个针对论文 docs/memory_config/memory.schema.yaml 的最小patch（不直接改共享论文库），包含一期实际新增的initial输入、empty memory、target.validity all_in_bounds及loss_reduction等字段，使P2/无memory/aux配置可按类型校验。另给1份P2两臂英文YAML最小差异示例供Manager整合；数据实际绑定由data/train owner承担。只为实际实现同步已有规格，不再发明一个平行schema或第二套执行规则。

示例澄清：上句“两臂”指实验的两个比较组（per-frame vs repeated endpoint），不是左右机械臂。当前p2_two_arm.example.yaml写成left_phase/right_phase且输入initial，是aux对照，不能作为P2示例交付。请提供两份可单独load的英文YAML，单个phase即可，input当前reference（首帧initial）/infer cache、相同H50/K30、同一公共mask和固定H归约、同一机器人target（可绑定已经对齐robot_action offset0），两组只改phase target从offset1/stride1到offset30/stride0；都在chunk完成读取第30行。不要虚构机器人左右独立阶段。论文patch不需加入无任何$ref使用的episode_availability定义：availability是adapter runtime数据接口，在说明文档解释即可，不能让config schema冒充验证了episode数组。

先CPU测试：字段顺序/重复和无memory、单字段wash及多字段drawer/rearrange、可变顺序phase不被限制、公共mask/固定分母、metadata roundtrip。代码量先给预估，再报告新增/删除行；避免大兼容脚手架。GPU短smoke待Manager分配，当前不占GPU。先交可供依赖方使用的契约commit，再完成训练实现commit；全量验证适用部分后report记录commit/测试/不足并发布。不得修改共享checkout或他人环境。过程中需求有歧义及时给Manager具体选项，不阻塞可独立实现部分。长程序若后续获分配超过1小时，用mam job登记。任务完清理自己的smoke/临时文件，不删除正式资产；不自行派agent。
