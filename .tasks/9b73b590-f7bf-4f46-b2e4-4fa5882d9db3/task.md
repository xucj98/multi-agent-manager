# Memory训练与checkpoint独立review

## 目标与范围

审查ad6bb77e-3892-4730-ae1a-7d9cd99a5728训练集成与dc61ef10-53f0-44c2-91cc-c78d1cb6676e保存/加载的组合，给新20k实验是否可开跑的结论。先通过mam task show读取两任务发布要求；它们发生冲突时向Manager报告，不自行选。core schema已经独立审完并合入58d6f21，不重审parser。数据由独立review负责，但你必须检查其进入真实transform和模型之后的语义。

先在本task用mam workspace add --repo openpi --base 489359f8655c0a0af35447caa71f4db702fefabe创建独立环境并读AGENTS。此commit为已完成保存/加载增量，先审这部分；训练模型增量尚未提交，Manager随后提供固定commit，你在同一task树合入后继续完整review。不得长期引用作者workspace/PYTHONPATH，不修改交付实现或共享环境，不派agent。现阶段CPU，未分配GPU。

## 必须核验

- checkpoint.save_dtype将浮点inference params副本保存BF16或FP32，训练内部参数/整数/布尔不被改写；model-only目录保留必要assets/metadata，不夹带optimizer/state。最终20k且仅一个checkpoint由实际train配置控制，不能只用tiny Orbax测试冒充6B模型保存通过。
- 仅checkpoint路径可创建policy，唯一resolved memory_config来自保存的TrainConfig，原YAML、训练数据/sidecar、旧workspace不需要存在。调用create_data_config(training=False)确实没有隐式读取dataset或训练norm路径；metadata YAML解析不破坏旧checkpoint。
- 训练与推理的full one-hot均在robot Normalize后、实际TokenizePrompt前追加。pi05 discrete_state_input=True时，保持相同robot/prompt/images而改变memory必须改变模型实际消费的token条件；不要只看state数组shape。memory使用identity，robot norm一致，输出剥离/反归一化顺序正确。
- 真实compute_loss逐坐标权重：sum(w*e²)/(B*H*D)，mask仅影响memory，不清robot整行。core weights含mask/reduction但不含lambda；memory lambda只乘一次，padding为0，非单位lambda/valid_mean权重保留。P2两臂phase t+j+1 vs t+30共用mask与robot targets；不能先按维度均值再乘phase mask。
- serial默认各字段独立argmax，仅显式decoder规则生效；head/vocab顺序/当前条件train reference与infer selected一致，不混入旧第一字段递增或button规则。空memory仍是正常无memory基线，aux输入initial不悄悄保留cache反馈。
- robot action已转换q→q+1，绑定offset0，不能双移位；current truth不用旧lag20 input。样本adapter不会因单字段缺GT丢全部机器人sample。sim来源demo_clean_state；wash未修正视频/pose映射前不能进入正式训练。
- 相对路径从项目根；旧模型路径尽量复用；不维护第二份schema/model_spec metadata。检查新增代码的真实必要性与重复逻辑，给可定位问题和后果，避免列主观风格清单。

## 交付

先给489359f范围的阶段结论，后给明确完整review HEAD。CPU定向复现实际输入/索引/梯度/保存加载，和作者原测试区分。报告task_revision、workspace/commit、测试和未验证点、阻塞与非阻塞项。50step+BF16真实模型GPU smoke由作者在GPU1执行，你审其实际命令/日志/产物证据，必要补查先报Manager。完成清理自身smoke/cache临时文件，发布report，等待归档。
