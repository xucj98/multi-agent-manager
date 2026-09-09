# Memory v1：openpi训练、模型与checkpoint集成

## 目标与当前范围

在独立openpi以同一memory_config支持full、serial、no-memory、无递推辅助监督；将真实样本、模型条件/loss、BF16保存和仅checkpoint恢复联通。先交可独立review的CPU实现commit，再做本机GPU1的50step实际base训练/保存/恢复smoke。20k正式训练已获用户授权，但本实现任务待Manager验收并发开跑通知；现在不自行开20k。

## 工作区、文件归属与依赖

复用本MAM task现有openpi worktree及独立.venv，读取openpi AGENTS。你负责models、training/config.py/data_loader.py/memory_data.py、transforms、scripts/train.py/compute_norm_stats.py及相应tests。新wire统一字段允许修改policies/policy.py。checkpoint_metadata.py/checkpoints.py/policies/policy_config.py由dc61ef10任务交付，合入其commit，不重复越写集。examples/converter/config YAML归7c8fbc25任务；client core归已验收f252任务，勿再扩公共schema。禁止把他人临时worktree加入PYTHONPATH；跨库测试使用本task登记的明确代码版本和自己的环境。

当前交付版本（相同patch的本地cherry-pick可继续使用，记录实际HEAD）：
- client core：主库58d6f2155acc3af03017677bb3f536101e6699f4，已独立验收；包含精简API、缺GT availability、clamp边界与row.index范围修复。
- sim data：481527346573b73958dcd81591fc8473e20feaff→38bf82c1753e6e911e6215a6762cccc2a7bb15bd；serial/no-memory YAML为2c91f9aff8275b42285c93da094302800ec65f4e。metadata生成69ca148后有63319ac收敛修正。数据独立review任务3e78bfec已确认两任务100ep、4500 P2 sample、serial/no-memory真实query的数据层通过。
- 保存/恢复：489359f8655c0a0af35447caa71f4db702fefabe→3d4fe31d0efef5e3dd8cdb30a3dc9d9050ecf2c5→cc706e37fb5c2190281789affce0095569a781af。最后一项完整继承meta/metadata，修复按名称漏文件问题。
- 完整独立review owner为9b73b590-f7bf-4f46-b2e4-4fa5882d9db3；runtime owner为9f5a3889-49a6-4f00-af84-096d8042c3bc。两侧wire契约见下文。

## 数据与第一批协议

仿真使用demo_clean_state来源，不能fallback demo_clean。该限制属于实验数据配置，不能硬编码进通用model。首批sim有rearrange的full per-frame/full repeated-endpoint/serial/no-memory，以及put-back两种full；wash两项待正确数据验收，不能阻塞sim。

恢复数据在/mnt/public/xcj/cache/huggingface/lerobot/<task>_demo_clean_state_shared_memory；sidecar在主openpi/data/memory_v1/rmbench/<repo_id>/。原LeRobot每集M个实际观察query，sidecar是等长M+1的机器人target、memory series和availability；最后一行是已核对的raw最终观察memory，机器人重复converted末动作。query仍只采样0..M-1。无需tail_append框架。

robot_action_target前M行逐值等于converted action[:14]，已经是raw q(t+1)，source=sidecar/action_at_row/offset0，不能再移位。current truth来自target标签/原始事件，不用旧lag20 input列。no-memory绑定只保留robot_action_target，availability={}，不能把完整三字段manifest原样传给空memory。

- H50、K30。full输入训练current reference（首次/缺GT用initial），推理cache；phase per-frame目标t+j+1。full反馈chunk_completed/last_executed。
- P2两任务另一个full将phase改为全H行重复t+30；其余主动变量完全相同，共用phase mask=(t+j+1<=L)&(t+30<=L)，L为最终有效源索引（上述sidecar中L=M）。例如query M-30的前30个phase目标有效，后20无效；query M-29的phase全部无效但机器人继续监督。机器人和其他字段目标/norm不因本臂改变。
- serial输入named previous lag30的真实t-30，负索引/缺GT用initial；推理cache；target是当前query t，current_condition为train reference/infer selected，query_selected/query反馈。默认每字段独立argmax，不继承旧phase递增/button特例，不套P2未来mask。
- 空memory是无记忆基线；aux保留相同字段/head/监督，但train/infer输入initial、无反馈。
- wash为S2M：当前follow14→下一对齐master14，EE pose+gripper；phase当前子任务且顺序可变。172合格episode全部训练，5个训练episode offline，缺GT字段逐项mask、不丢整个机器人sample。旧all_172_15hz及master_v2有已知S2M/视频pose映射问题，未验收不可训练。

## 模型、样本与损失

只复用已支持的categorical/full one-hot/serial token；unsupported类型明确报错，不造新模型族。load_memory_config→ResolvedMemoryConfig，compile_model_spec(model_config或robot_dim/padded_dim)，make_training_sample(EpisodeMemoryData, query_index, rng)。helper给input/target IDs、robot/dense targets、数值mask/reduction weights；具体以已验收API为准，不复制parser/decoder。

机器人state/action用同一robot-only norm。one-hot memory使用identity，必须在robot Normalize之后、TokenizePrompt之前追加；不能只在Pad之前加，因为pi05的discrete_state_input=True已经在tokenize时消费state。用真实transform链证明同robot/images/prompt而不同memory会改变tokenized_prompt。训练和推理顺序一致。

实际flow-matching loss为sum(w*e²)/(B*H*D)，D是相同padded action维度。helper权重含mask/reduction但不含memory lambda；仅memory坐标乘一次spec.loss_weight，机器人保持1，padding为0。phase fixed_horizon用公共mask×lambda；其他valid_mean字段为mask×H/max(valid_count,1)×lambda，零有效项0。必须先对逐坐标误差乘数值权重，不能先平均坐标再用phase mask清整行动作。actions与weights成对pad。

缺GT input用initial；target的ID/mask/dense/weight按helper处理，无效dense全0，机器人仍监督。保留输入mask、目标mask和公共validity的区别。真实compute_loss测试覆盖非1 lambda（如0.25）、非单位valid_mean、全invalid、padding和P2两臂相同有效位置；不能只检查helper输出形状。

## 新memory的训练/部署wire契约

新policy输入为原机器人state/images/prompt加memory_input_ids，shape(F,)；scheduler只发语义IDs，full/serial具体编码由policy transform完成。旧checkpoint无memory_config保持既有路径。

输出actions只含robot动作；另给memory_prediction_ids：full (H,F)，serial (1,F)。full复用MemoryOutputs的schema decoder；serial复用实际动作条件化所用key_state_prediction，不由scheduler再argmax另选一份。previous由本query输入IDs给出，policy不维护跨query任务cache；scheduler按schema事件/row维护context。旧diagnostics可保留兼容。F=0可不要求预测字段或使用空字段维度。

MemoryContext只检查预测layout/shape/类别范围并反馈，不从裁掉memory的actions尾部解码，不在state里预写one-hot。输出先decode/剥离identity memory再robot-only Unnormalize。通过实际input/output transforms→真实MemoryContext验证非initial缓存确实进tokenizer，raw dense输出被裁为14维后预测IDs仍按K30消费row30；serial用的条件ID与反馈候选一致。不要用两份各自mock字典冒充联通。

## checkpoint、自包含与留痕

唯一权威字段是TrainConfig.memory_config的resolved mapping；memory_config_path仅新训练入口使用，解析后清空，不再保存model_spec或第二份schema。TrainConfig.create_data_config(*, training:bool)仅构造transforms：普通推理不读训练rows、labels、sidecar或原YAML，norm从checkpoint assets恢复。

特别检查模块级_CONFIGS不因初始化无关训练模板而读取原memory YAML。训练模板读取应在选中/构造新训练时发生；checkpoint-only需在全新进程且原YAML/dataset/sidecar不可用的情况下恢复，不能只先import再rename。

新训练默认配置为单GPU、batch32、20,000次optimizer update；只保留最终模型BF16权重、assets与metadata。save_dtype支持bfloat16/float32/None（默认None，新实验显式bf16），内部FP32参数不改变，save_full_state=False。新run拒绝混写已有目录，不用model-only结果假装可恢复optimizer训练状态。检查scripts/train.py现有循环用零基step保存：新最终目录应反映完成的20,000次更新（50step smoke同理），不要把19999目录误记成训练计数20k或用20,001次更新凑名。

base参数形状统计为3,353,433,872个元素，全BF16裸权重约6.71GB。此前6B/12GB估算已更正；按完整参数树/shape/dtype/恢复验收，不以固定文件大小验收。新head据实增加。

checkpoint_metadata.save保留实际command/cwd/git commit、train config和上游data/sidecar metadata/config；不复制代码、图像或label矩阵。meta/metadata目录完整继承，不按少量文件名丢掉stats/tasks/provenance等。相对路径从项目根；已使用的数据定位env也写在command中，不建重复runtime/provenance系统。

## 验收、资源与交付

先CPU阶段固定commit送review，可与后续GPU smoke并行。适用旧tests及上述真实条件/loss/自包含联通检查通过后，在本机GPU1跑实际base的50step训练、保存、仅checkpoint恢复，并核对返回wire keys/shapes。base在/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base。先检查GPU1实际显存；只占GPU1，本机GPU0跑F0，远端八卡留正式单卡训练。未核验路径不要填卡凑数。

报告当前commit、task_revision、workspace、CPU/GPU实际命令/结果/产物及剩余项/耗时预估。先发布CPU交付，不必等整个GPU链路才送review。GPU1释放时通知Manager以便F0并行。自己清理被正式实验替代的smoke和临时文件；长于1小时的进程登记MAM job。不自行派agent。

## 首批正式训练调度补充

论文计划06a3139已明确：若wash-cup数据在sim可开跑时仍未通过验收，远端GPU6/7先执行rearrange full per-frame/repeated-endpoint配对seed1。这是已有Q2重复，不增加实验数；wash验收后优先安排下一批空闲卡。初始六个seed0 sim不受wash或live修复阻塞。正式训练仍在CPU独立review与GPU1实际50step链路通过、Manager发开跑通知后启动。

## CPU交付后的分工

ffa308d5485a2c8222d3e7735b08723c6e93a237已送Banach独立review。真实transforms→MemoryContext联通由已有双库workspace的Einstein负责、Pascal复核；你继续共享norm、实际loader与GPU1的真实base50step保存恢复，检查policy wire keys/shape，不为这项测试再创建bridge环境或等待live小修。完整schema规范不变；任何发现及时固定小commit给review。

## GPU验收覆盖两条实际模型路径

新joint-dense与serial-token改变了不同模型路径（后者有新head/动作条件选择），单个full smoke不能证明serial实际base加载/JIT/保存/恢复可运行。请在同一GPU1顺序完成full和serial各50 optimizer updates，均验证最终BF16 model-only/仅checkpoint恢复及各自wire；no-memory沿已通过loader与共享模型路径，不要求额外50step。复用同一robot norm统计，两个smoke独立输出；不同时占额外GPU。full完成即可报告，serial可与CPU独立review并行。GPU1全部结束释放时通知Manager。

正式20k启动后运行worktree需要固定，不应继续改该树的模型/loader/config。先准备所有将运行的配置；若wash还需实施，告诉Manager剩余配置写集，Manager会安排与正式训练冻结树分开处理，不让长训练读取途中变动的源码。

## CPU独立review当前发现与优先级

Banach已在等价ffa308d的63be08c发布具体复现（本MAM 9b73b590/report.md与combined_review_test.py），Manager裁定以下需要最小修正：
1. R1：training=False factory仍先读原训练norm，再由policy加载checkpoint assets；仅checkpoint路径恢复必须完全不读取原norm/dataset/sidecar/YAML。原norm缺失/损坏/不可读也不应影响有效checkpoint。保留现有factory和checkpoint资产机制，不新增第二配置框架。
2. R2：serial真实TrainConfig YAML roundtrip时Pi0Config.__post_init__过早校验尚未填充完成的nested decoder mapping，导致load失败。把必要校验放在完整构造后且使用前，保持唯一resolved schema与默认独立argmax，不为每种历史格式另加兼容层。
3. R3只阻塞aux：合法train source=initial没有mask键，adapter不能无条件索引mask；infer source=initial也要遵守配置而不消费传入非initial cache。full/serial正常闭环不因aux未验收停工。

先R1/R2固定小commit送复核，R3可独立增量。已通过真实tokenizer条件、P2数值loss/梯度与metadata继承不重跑无关检查。GPU50step若已运行且修复仅涉及加载factory/YAML时机，不需要再训练同一50步；用明确修复commit重做checkpoint恢复并记录保存/加载各自版本即可。不要把新增读取阻塞误报成模型训练数值问题。

## CPU review其余范围完成

Banach报告fb9c495确认真实data窗口、serial实际选中条件/wire和50/20k更新计数通过。R4仅显式conditional decoder：Pi0逐case覆盖取last-match，而公共schema为first-match；应做小修使消费者遵守同一已保存规则，补一个重叠case对照。此项与aux R3不阻塞当前默认argmax首批，优先完成R1/R2和实际GPU。

put-back独立adapter窗口已通过，但其专用robot-only norm尚未生成/实测，请在首批put-back正式开跑前生成并验证真实归一化loader，不能借用rearrange stats。无需再跑第三个50step模型smoke。
