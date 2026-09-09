# Memory v1：统一配置与openpi训练接入
# 目标

在独立openpi实现首批实验可用的统一memory配置、训练样本与模型接入。用户已经授权施工/开跑；你负责代码，不直接启动正式训练。Manager掌握研究方向和合入，另有agent负责数据转换与robot-bridge。优先最小可审查实现，不构造通用DSL/插件系统。

# 工作区与写入范围

从 openpi 71c80db723a242c61cfe429dd6794e9ece3cbcf1 用 mam workspace add 创建独立worktree/环境，先读该库AGENTS.md。独占 packages/openpi-client（共享轻量契约）、src/openpi（训练/模型/metadata）、相关定向tests；不改examples数据转换器和robot-bridge。论文规格只读：/root/Documents/task-state-vla-paper/docs/MEMORY_CONFIG.zh-CN.md 与 memory_config/*.yaml。你上个只读报告为 .tasks/8584105e-adae-4a96-83f2-af47cece6bf8/report.md。

# Manager裁定与第一版范围

1. 单一schema事实源放在独立openpi的轻量openpi-client package中，供训练与scheduler共同读取；不另建repo/重依赖、不让robot-bridge导入JAX/torch。checkpoint metadata保存解析后的memory_config字典（含schema_version），训练入口可接YAML。不复制E/record的结果引用到执行配置。数据/机器人维度和normalization沿用模型配置并做一致性检查，不要求用户重复填写。
2. 保留S有序memory字段和P输入、目标、representation、反馈明确分离。首版支持categorical、joint_dense one_hot与serial_token token，以及无memory（memory=[]）；不要把一期未实现的scalar/pose2d/parallel等静默视作可运行。既有模型行为通过显式配置保留，后续扩展能力有实际实现才开放。
3. 不能凭字段位置/类别数推断phase/attribute/button规则。新配置默认独立argmax。历史ordered/latch/conditional若用于旧权重必须显式编译到现有选择机制；wash-cup1..5顺序可变，默认允许任意类别。shared categorical集合/顺序在full和serial两种表示中完全一致。
4. 训练标注来自数据适配器的series/constants/events；单样本命名lag只抽一次，多字段共享。input不读未来。模型尺寸、norm stats、base初始化和任务标签不混入scheduler。
5. 首批P2：H50、执行K30。phase目标两种：t+j+1（j=0..49）与所有行t+30；其他memory字段与robot目标保持同一协议。phase两组公共mask为(t+j+1<=L) AND (t+30<=L)，无效phase槽都置同一零值且loss=0；loss用固定H分母，不按有效项数除。机器人越界取末帧，机器人与其他字段loss不受phase公共mask影响。需要可表达的有限validity/loss-reduction配置，别用全局tail冒充这个控制。不实现任意mask表达式语言。边界、全invalid样本和连续多字段mask用真实训练loss路径验证。
6. 新训练统一单卡bs32、20k steps、仅最后20k checkpoint。用户要求最终BF16模型权重约12GB和metadata，自包含；确认当前JAX/Orbax的save/restore路径能保留BF16，不将优化器/ema/所有step附带保存。优先复用现有参数；如确需增加保存dtype参数，仅一处显式配置。不能声称BF16计算就表示内部参数已BF16。只改当前训练所需路径，不做LoRA/旧smoke格式兼容系统。
7. 新schema checkpoints必须只给路径即可恢复相同模型、字段、norm与输入协议。既有公开/正式旧checkpoint沿现有loader，后续定向同输入比较验证，不为所有旧格式新建兼容层。

# 跨agent契约

你是配置/API owner。尽早（先于大实现）报告你准备暴露的轻量helper函数、resolved memory_config结构与数据入口，控制在一屏；Manager会把确定接口发布到其他任务。沿用已给YAML名称，必要精简给理由，不自行大改设计空间。数据agent只改examples/适配器，runtimeagent只改robot-bridge。不要让它们猜接口。

# 验证与交付

先CPU测试：字段顺序/重复和无memory、单字段wash及多字段drawer/rearrange、可变顺序phase不被限制、公共mask/固定分母、metadata roundtrip。代码量先给预估，再报告新增/删除行；避免大兼容脚手架。GPU短smoke待Manager分配，当前不占GPU。先交可供依赖方使用的契约commit，再完成训练实现commit；全量验证适用部分后report记录commit/测试/不足并发布。不得修改共享checkout或他人环境。过程中需求有歧义及时给Manager具体选项，不阻塞可独立实现部分。长程序若后续获分配超过1小时，用mam job登记。任务完清理自己的smoke/临时文件，不删除正式资产；不自行派agent。
