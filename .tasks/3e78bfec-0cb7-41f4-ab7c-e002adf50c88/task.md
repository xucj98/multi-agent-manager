当前sim数据增量：openpi `38bf82c1753e6e911e6215a6762cccc2a7bb15bd`，前置 `481527346573b73958dcd81591fc8473e20feaff`。该增量实现下文已确定的M+1 sidecar与路径修正，请以实际提交继续集成/审查。

## 恢复sim增量审查

已交sim commit481527346573b73958dcd81591fc8473e20feaff，请在已有本task openpi树合入，继续review四个full YAML/原始当前truth与P2 mask。其tail_append接口和账号绝对路径是Manager已发现并正在修的问题，不重复提出新框架。作者将很快补增量：sidecar直接保存等长M+1的robot_action_target、memory series和availability，前M机器人行逐值等于converted action[:14]、末行repeat；query仍原LeRobot M行。训练采用现有sidecar绑定、action_at_row/offset0，core API不变。核验raw最终观察确实给第M行memory监督，没有增加不存在的query或二次动作移位；P2 query M-30应有前30个phase有效位置。

另将新增rearrange serial lag30（query当前target/独立argmax/current_condition train reference/infer selected/query_selected feedback）及no-memory配置。收齐增量后给两任务能否进入sim训练的独立结论，先不等wash重转；四P2 YAML除phase time外的所有主动训练变量相同，mask共用。wash仍因视频/pose映射错误禁止训练，收到正确小样本后再复核，不重复全量数据转码。

继续使用已有workspace/环境，CPU审查。最新作者requirements在7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2/task.md；依发布内容，不采纳旧report中已废弃的tail_append方案。

# Memory数据独立review：S2M动作源、标注有效性与sim样本绑定

## 目标与工作区

独立review数据任务7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2，已发布要求可读其task.md（当前482b78a2c7d024a06010c96426a77f51bde17605）。初始代码固定openpi 1528b7b08eb119ede615c0520d6da3e8db6804a4（含S2M修复63f35c8及已验收core58d6f21的cherry-pick），用mam workspace add创建自己的openpi工作树，读AGENTS。核心schema已另行review并合入，不重做全套core审查。你只读review和CPU独立核验，可在自己workspace写临时脚本，不修改交付代码、不跑GPU、不重新转换全数据，不派agent。

作者尚在补交sim bindings和正式YAML修正，Manager会给后续增量commit。先审查已提交converter/S2M/过滤及真实小样本，不等待所有实现齐备才开始。最终结论区分当前可接受部分和仍需复核部分。

## 要验收什么

1. 用户S2M：当前对齐帧follow_*14维输入，下一对齐帧master_*14维动作，保持旧drawer准确converter 3f7086271dbe49100323496218caf0ed69b761b3的布局（可从RMBench主库git show只读核对，不需为只读文本建第二环境）。此前代码错误地follow同时当action，63f35c8应真正修掉。用raw同帧master/follow明显不同的样本复算，不用shape正确/与follower比较误差0作为证明。数值布局为双臂末端position/rotation/gripper，避免把它笼统当关节角改变单位。机器人action已移位后训练绑定offset0，不再q+1。
2. wash-cup /mnt/public/datasets/x1pro/wash-cup：label6/缺subtask标注/非1..5恰各一次的episode全部过滤；顺序可变。已扫244→172合格，次序120个1-2-3-4-5及52个2-1-3-4-5。独立抽取有区分力的有效/非法episode核对文件来源和区间端点约定；确认允许顺序改变，不偷读第一GT作为推理initial。
3. 合格集仍有缺GT帧，raw availability必须保留。missing annotation与有效unknown类别区分；输入缺GT initial、memory损失mask0、机器人保留。不能因full H50有一个目标无GT就删整sample或把这些帧监督为phase unknown。15Hz时间对齐、下一帧action、视频/pose同源索引、episode末尾处理需核对。固定5ep offline来自训练合格集，不划分holdout；若作者可提供正式修复后的输出路径，抽样读回数值/metadata，不使用旧错误all_172_15hz当已修复资产。
4. 新sim训练来源demo_clean_state：rearrange/put-back converted已有current target_ids，input_ids是lag20不可当current truth。原始小标注在主RMBench/data/<task>/demo_clean_state，metadata/robot_edge_samples及comparison独立证明100ep action首尾与raw移位一致。后续binding需正确复原series/constants/events及初始获取mask；完整共享源只读，不覆盖。
5. 实际基线YAML要符合计划，不仅能parse。full当前reference输入、infer cache、t+j+1目标、K30后last_executed；serial输入lag30、current query target offset0、query_selected反馈、train当前条件reference/infer selected、独立argmax；两者H50/K30。initial始终输入/空feedback只属于aux。P2两sim full是t+j+1 vs重复t+30，同一公共mask/fixed H和相同action/norm；wash serial不套P2 future mask。共享one-hot/token domain是同一语义值顺序，不需要另做模型结构。
6. Metadata继承原command/commit/config，转换结果在稳定共享目录。README中文、操作命令不依赖export根变量。不增加重复转换视频或大套兼容/测试脚手架；评估当前实现可否明显精简，但不把必要时序校验删掉凑行数。

## 交付

先把有把握的阻塞发现及时报告Manager，然后report写task_revision、审查commit/工作区、复现命令与结果、按严重性列具体路径/输入/预期与实测；区分作者已知正在修的问题和新发现。独立验证结果不冒充完整train/offline闭环通过。等待后续小增量时可阶段报告，最终清理临时脚本/cache，worktree留待Manager归档。
