# Memory 训练与 checkpoint 独立 review

## 范围与当前状态

复用本任务已登记openpi worktree及独立环境，读openpi AGENTS。只审任务ad6bb77e-3892-4730-ae1a-7d9cd99a5728的新交付；不修改生产实现、不占GPU、不派agent、不创建新环境。

你此前6a32847报告的d10cc01 CPU GO已被Manager接受。真实tokenizer条件、P2损失/梯度、LeRobot/sidecar窗口、serial条件与wire、更新计数、R1/R2自包含恢复、metadata继承均已通过。Manager后续验收了full/serial各50次实际GPU更新、完整BF16保存和checkpoint-only恢复。put-back专用14维norm及两种full实际归一化loader也已验收。首批八路正式20k已放行，运行树固定d10；这些已通过范围不重测或暂停。

当前候选：d49c1a1c5cb141283cb10634cfb31903624ed761，父级含已合并的42011a3数据/文档。只复核R3/R4修复，交阶段CPU结论。wash full/serial训练注册尚在作者实现，届时另给确切commit和增量范围；未交付的wash不是当前候选缺陷。

## 本轮两项

1. R3：合法train source=initial没有mask键，adapter必须正常构造和采样；infer source=initial应遵守字段声明initial，不消费请求中的非initial cache。核对全initial和部分initial/其余cache的实际transform路径；不能只检查helper样本或依赖scheduler恰巧先清零。保持机器人归一化/动作监督与没有递推的aux定义，缺GT不丢机器人sample。
2. R4：显式conditional decoder重叠case时，Pi0必须与公共schema一样first-match，实际动作condition、统一wire选中值一致。复用你此前remaining_review_test.py的实际Pi0复现，确认没有破坏默认argmax、无匹配fallback或按字段顺序读取selected；无需重审整个parser和昂贵模型计算。

修复不应改变首批默认cache/argmax训练协议，也不需要给正在跑的八路更新源码。遇到具体回归，报告输入、实际行为和影响范围，别把未用的扩展配置问题捆绑成首批训练阻塞。

## 持续契约与验收边界

memory_config是唯一resolved schema；普通推理只依赖checkpoint assets/metadata，不读原YAML/dataset/sidecar/norm。新wire为输入语义memory_input_ids与输出robot-only actions、full(H,F)/serial(1,F)的memory_prediction_ids；serial输出等于实际动作条件，previous取本次请求。one-hot在robot Normalize后、TokenizePrompt前追加，输出剥离memory后只反归一化机器人。单/多字段及空memory共用机制。

P2仅改变phase目标t+j+1对重复t+30；公共mask/机器人目标/归约与lambda保持已验收定义。机器人target已是next frame，sidecar offset0，不二次移位。输入source与目标availability分别处理。新sim只用demo_clean_state。50/20000是实际optimizer更新计数，model-only保存最终BF16，不复制代码，metadata完整逐步继承。

这些是判断增量回归的边界，不要求你全部再跑。CPU小模型/替身的范围如实说明，不冒称GPU/硬件验收；runtime跨库和live已有独立Pascal结论，不再使用本task额外bridge环境做重复工作。

## 交付

简短report注明最新task_revision、真实review HEAD/工作区、R3/R4结论和独立测试命令/输出；已通过历史项引用6a32847，不复制完整旧报告。阶段完成后可结束，Manager在wash候选到达时唤醒同一任务。归档前清理本task的临时review脚本以及两worktree源码里的非共享、非tracked .pytest_cache/.ruff_cache/__pycache__，不跟随共享软链接。正式数据/资产保留，环境与分支由Manager归档。
