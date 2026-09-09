# Memory v1：真机、仿真与offline统一反馈

## 范围、责任和工作区

复用本任务登记的robot-bridge及openpi worktree与独立环境。修改robot-bridge runtime、相关测试和功能文档；openpi只合固定交付依赖，不改训练实现。阅读robot-bridge AGENTS及docs/design/conventions.md。Manager负责跨库接口与验收裁定，训练owner为ad6bb77e，reviewer为0bc5129d。不改主checkout、不使用他人临时PYTHONPATH、不自行派agent。

目标是同一个checkpoint中的memory_config驱动live/offline/simulation的多字段context与UI，同时保留既有真机控制和takeover。旧F0评测独立在已冻结代码上运行；不因后续live修改要求其重跑。

## 已交付与当前优先级

- F0已验收：fd38513→92b365c→bc842036e3735390f35fe1138aa7b19f5ae2f95b。最后版本以build_policy_obs返回None跳过terminal infer/execute，不保留临时client代理。Base不识别仿真字段，正常dict仍按原序执行；terminal前已有reset保持。row30的2rollout GPU smoke已通过，正式100由独立eval owner执行。
- live handoff修复9d2784d143bcc4c4fdd59bc558f0e0a9303d42a5仍有下述两处独立review阻塞。
- 新wire f84edbd6eea81104a00fd85409046eaaa8712e9b已通过runtime半边审查，跨真实OpenPI transform仍待训练commit。
- 优先修两个live问题为独立commit；轻量依赖安装同时补齐；随后用正式训练commit做跨库联通。CPU验证，不触碰真机或启动GPU。

## 当前必须修复的live边界

Pascal报告6eb517df97db65b600dead62e7ba2da6ae762727已由Manager核对：

1. synchronous_rows等待queue剩余0，但X1/X1Pro仅在有after端点时发送before，末行缺handoff evidence，3行只completed2。最小修正末行消费及完成等待；不能把timestamp过期算成完成。验证真实loop/worker（fake SDK）、单行/末行、插值factor>1、terminal/takeover/reset。
2. synchronous drain后live/offline仍按非0 latency跳过新chunk前几行。该iteration的动作起点、future window和反馈映射必须与实际wait语义一致：同步从row0开始，原流水线wait_condition路径保留非0 latency及重叠推理机制。覆盖继承的takeover，不能全局废弃异步行为。

还要保持先前修复：没有成功transport handoff不增加completed；clear_actions清掉所有未处理proposal且不作下一插值anchor；progress由该次返回观察的时间基得到，不能被UI/无图get_obs提前消费。完成计数仅证明发送交接，不证明物理到位，硬件边界在报告中明确。

## 共享schema与wire

依赖轻量openpi-client的memory_config，正式core在58d6f2155acc3af03017677bb3f536101e6699f4（本任务等价7061c94可用）。load_memory_config→ResolvedMemoryConfig→compile_model_spec；to_dict为唯一保存mapping。不复制parser/decoder，不引入训练框架依赖。

新checkpoint有memory_config时：
- 输入为原robot state/images/prompt，加有序memory_input_ids，shape(F,)。scheduler只发语义IDs，具体full/serial编码归policy transforms。
- 输出actions只有robot_dim；memory_prediction_ids为full(H,F)、serial(1,F)。full由policy共享decoder生成；serial必须是实际动作条件化选中的ID，不重新argmax logits。
- context验证layout/shape/range后按schema事件和row维护cache，不从裁掉memory的actions尾部decode。previous由当前request IDs提供，policy不维护显式任务cache。
- F=0不要求预测字段或允许空field维度；旧无memory_config checkpoint保持已验证路径。

scheduler单个robot/policy、维护context；backend透传并提供reset，DM05/Mem-0原内部缓存保留。没有session/get_progress RPC/插件总线。UI从schema有序fields/domain显示和编辑，不硬编码phase、属性数或wash/drawer名字；键盘/UI走同一操作入口。

## 调度与反馈语义

保留WS action chunk、UDP遥操作、execute后wait-condition get_obs，Base只接受既有hook最小None退出。chunk accepted与实际完成区分；pending预测要等相应事件才能更新。支持query_selected/chunk_accepted/chunk_completed及声明row first/index/last_executed/query，按core支持范围校验。没有所需进度的controller启动时报错，不猜已完成K。

取行基于真实model row与实际执行k，不把render/integration substep当policy row。partial、reject、跨chunk、episode终止、takeover/reset及异常不回灌旧pending。每query记录输入/目标参考时刻、计划K、actual k、选行、字段before/after、是否下一query消费，沿既有diagnostics。

首批full：current reference训练、cache推理、目标t+j+1；P2另一臂仅phase目标重复t+30；两者K30完成后均读row30。重复监督不保证实际H行预测相同，不能随意换首行/平均。serial：previous lag30输入、current query目标、train reference/infer selected动作条件、query_selected反馈。默认独立argmax，顺序可变的wash不加入ordered规则。

旧F0固定H50/K30，legacy_full_feedback_selector支持index0/19/29/49和last_executed；保持原字段、归一化和解码，全部字段同选行。row50是未来模型预测，不是真值。F0只用于无新schema旧full模型；终止仍写actual k与next_query=false，不再infer。

## 轻量包安装与部署

新schema需要openpi_client.memory_config，生产部署必须有明确安装路径。接受由独立openpi固定commit构建openpi-client wheel、在新隔离环境安装并实际创建MemoryContext的最小方案。不要假定公开同名旧包已有新模块。中文文档给可复制命令/安装来源，复用现有部署入口；不复制全训练环境，不为了依赖检查重做SDK系统，不连接/改变真机或原环境。先简述选择依据再实现；这一验收不阻塞sim训练。

## 验收与交付

使用实际policy input/output transforms→实际MemoryContext联通：非initial cache改变pi05实际tokenized_prompt；full raw dense输出裁为14维后predicted IDs保留并在K30消费row30；serial反馈ID等于实际动作条件ID；单字段、多字段、no-memory。可以构造原始model输出，不用两份mock字典代替真实transform链。训练正式commit到后在本任务openpi合入，使用自身环境。

CPU测试覆盖以上进度/并发/中断/wire/旧路径/UI；按库规范全tests。GPU与真实硬件验收分开记录，不能将CPU通过写成硬件通过。RMBench recorder负责仿真产物格式，结果归RMBench/eval_result/<exp-group>/<run>，bridge不新建正式结果根。每步继承metadata/config，不复制代码。

报告task_revision、工作区/完整commit、变更规模、实际验证及剩余项；阶段交付及时publish report供review。清理自己的smoke/cache临时文件，保留workspace待Manager归档。

## CPU训练交付与跨库验收版本

openpi训练commit ffa308d5485a2c8222d3e7735b08723c6e93a237已固定，包含所需checkpoint字段、MemoryDataAdapter/transforms及Policy.infer wire；其父链有等价core、sim YAML、checkpoint最终增量。请合入本任务openpi独立树（等价patch按实际文件处理），完成前述真实transforms→MemoryContext联通。你负责此双库测试，Pascal独立复核；Bernoulli继续norm/GPU1保存恢复，Banach审OpenPI模型/训练/加载，不重复创建bridge环境。不要等待GPU50step才检查CPU wire。

## 78e1b4a复核裁定：轨迹进度与同步观察需一致

Pascal实际复核已关闭drain后的latency偏移，真实ffa308d transforms→Context的7项CPU联通也通过。剩余两个live问题由Manager接受，优先小修：

1. 真实get_obs的wait仍只按timestamp队列决定返回；将发送函数用event延迟时，单行已到期、传感器时间已推进，但尚未成功handoff就返回queued=1/completed=0，context又清await并允许下次infer。同步schema应在同一次wait-condition get_obs中等待与返回观察时间相符的handoff进度。保留原异步路径，不新增get_progress RPC或多轮轮询。
2. 实时tick可以跨过中间端点。3个目标1/2/3、间隔20ms，90ms后才启动实际loop/worker，只成功发送3，tracker报completed1/queued2，Context误反馈model row0=1且旧pending永久残留。不要补发过期动作；将进度定义为一次成功handoff确认执行器推进到的轨迹位置/已消费前缀，与policy row映射一致。仅墙钟推进或单纯累加SDK发送次数都不正确。被取消的旧epoch/proposal不贡献新进度；较旧图像snapshot不能被后来的无图请求提前推进。

可沿现有轻量tracker调整成功handoff的前缀语义和wait条件，不需要新状态框架；generic执行能力/等待条件仍归controller，memory语义归scheduler。测试覆盖上述两项真实loop/worker复现、同期正常/跳tick、partial、terminal、takeover/reset。每条命令“被执行器消费”不等于机器人物理到位，在文档/trace命名中准确说明。先交独立commit供Pascal增量复核；不重跑已通过的跨wire或旧F0。
