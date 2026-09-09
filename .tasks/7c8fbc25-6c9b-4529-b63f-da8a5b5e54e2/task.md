# Memory v1：数据适配与wash-cup转换

## 范围与当前状态

复用本任务openpi worktree及独立环境，阅读openpi AGENTS。负责examples/rmbench的数据适配、YAML、中文操作说明及定向测试，和examples/x2robot的wash转换/标注/配置/测试。不改src/openpi、packages/openpi-client、robot-bridge或主checkout，不自行派agent。新图像/低维产物归主openpi的gitignored data共享路径，不能依赖临时workspace。

sim两任务数据/配置已由James独立review通过（100ep、4500 P2 sample、1250 serial/no-memory query）。当前sim最终commit63319ac984492cd8bfd8a71158200220a6e14e38，其metadata收敛增量由review补核。wash修复commit773d177b93b6a6d8569a6761ae74118bef5d4adc、配置a75d1737539d5497b2e8d3569756ef0dc67d5ed2已送James。现在优先提供修正后两集三相机的实际小样本及证据，独立验收后立即全172转换；sim不得等待wash。未获分配不使用GPU，不启动模型训练或真机。

## 数据来源与sim约定

所有新仿真转换/训练使用demo_clean_state，不能fallback demo_clean；沿metadata确认来源和详细标注，不能仅看目录名。评测场景配置不由此自动改变。

恢复的LeRobot数据在/mnt/public/xcj/cache/huggingface/lerobot/<task>_demo_clean_state_shared_memory；rearrange50ep/20103rows、put-back50ep/17588rows。raw scene/language/seed/metadata在主RMBench/data/<task>/demo_clean_state。旧converted action[:14]已为raw q(t+1)，绑定offset0，不能再移位或改用observation state构造动作。原始首尾100ep对照已通过，无需重新转换图像。

sidecar放主openpi/data/memory_v1/rmbench/<repo_id>/，直接保存每集等长M+1 series与availability：机器人前M行逐值等于converted action[:14]，第M行重复末action；memory最后行来自核实的raw末观察标签。原LeRobot图像/state/query仍是M行，不采样不存在的query。绑定用sidecar robot_action_target、semantics=action_at_row、offset0；不增加tail_append配置或解释框架。

current memory truth来自已转换current target/原始事件，不能用旧lag20 input列冒充。字段参考series/constants/events和availability只保存真实标签，目标时序由同一core sample helper生成，不为不同实验重复转换数据。

## 首批英文配置

同一轻量openpi_client.memory_config解析器（主库58d6f21）：load_memory_config、compile_model_spec、make_training_sample(EpisodeMemoryData)、to_dict；具体沿实际API，不复制parser/mask/decoder。缺GT availability按series key逐项提供，缺省全true；缺GT input用initial，目标mask/weight/dense为0，机器人样本保留。

- rearrange/put-back两种full：H50/K30；current reference训练、cache推理；phase目标t+j+1与重复t+30。两臂公共phase mask=(t+j+1<=L)&(t+30<=L)，L为sidecar最终索引；phase固定H归约，机器人及其他字段/norm相同。chunk_completed/last_executed均读row30。重复监督不保证H行预测相等。
- rearrange serial：previous named lag30训练reference、推理cache；target当前query t；train reference/infer selected动作条件；query_selected/query反馈。不使用P2未来mask。默认独立argmax，不继承旧phase/button规则。
- rearrange no-memory：memory=[]与空updates；使用时bindings只保留robot target、availability={}。
- wash full：current reference/推理cache、t+j+1、chunk_completed/last_executed；首批不需repeated endpoint。
- wash serial：previous lag30/current t target/selected query反馈，与sim serial同机制。full/serial共用单phase语义、S2M目标。initial-input无反馈仅属于明确aux配置，不能当闭环基线。

## wash-cup筛选与时间对齐

原始数据/mnt/public/datasets/x1pro/wash-cup只读，annotation_layers.json定位子任务标注。label6、没有子任务标注、不是1..5恰好各一次的episode整集排除；顺序允许变化。已核实244集→172合格/72剔除，原因可重叠：16缺标注、28label6、56非各一次。合格120集1→2→3→4→5，52集2→1→3→4→5。全部172用于训练，不划holdout；固定5个训练episode给offline并保存ID。

phase表示当前子任务。未知时使用显式unknown，不读取episode首GT初始化部署，也不假定先抓杯。domain ID与原始label ID明确区分。15Hz有效query共142609，13404行缺phase GT，mask该字段而不删机器人行。

S2M沿已核实drawer协议：当前follow_* EE pose+gripper14维输入→下一对齐帧master_*14维action。两套数值不能混用；不从follow observation q+1代替master action。数据/标注/视频共用唯一实际source-frame映射，保留JSON timestamps及selected source index。

旧all_172_15hz错误follow→follow；master_v2虽修动作，视频仍按MP4 PTS重采样而pose按JSON索引，抽样漂移20 raw frame约0.67秒，均不得训练或复用其视频。新v3由JSON选帧映射驱动每个相机decoded frame选择。验证raw decoded n确实对应JSON帧，逐帧比对两集三相机开头/中段/尾部及原漂移点；不能只校验总帧数。记录current follow、next master、标注和视频选择的共同映射，raw尾与query数关系清楚。

小样本及固定代码先独立验收，通过后正式全量转换；预计超过1小时用mam job add登记真实host/PID。正式结果替代后清理错误/临时产物，仅保留本MAM简短错误说明；不删除raw或未验收的唯一证据。

## 留痕与路径

每个转换/sidecar在metadata保存command.txt（实际命令、cwd、commit注释头）、实际binding/config、上游meta/metadata及scene/language/seed。只复制metadata/config，不复制代码、图像、标签矩阵进metadata。meta/metadata目录完整继承；不要新增runtime/provenance系统、独立git_commit.txt，或将所有候选训练YAML复制进去。最终训练选定memory_config由TrainConfig唯一保存。原69生成metadata收敛后用633真实重生成，不事后伪造命令。

脚本无账号绝对DEFAULT源路径；必要source-root/dataset-root参数明确传入，相对路径从openpi项目根解析，输出通过data共享软链保留。中文README具体命令可写本集群完整绝对路径，不用export root设置段。

## 验收与交付

测试筛选、合法逆序、缺GT/边界、S2M真实值与时间索引、视频帧映射、M+1尾行及P2公共mask。已独立通过部分只复核增量，不重复无关全数据测试。代码与正式生成命令先commit，再运行；报告完整git SHA由git读取。

及时发布阶段report：task_revision、workspace/commit、完成/未完成、实际数据/5ep/sample位置、验证、真实转换命令及所需耗时/空间。数据GO与模型GO分开；不要用配置可parse宣称训练已联通。全量转换完成读回核对并清理被替代smoke/错误数据，archive job后保留workspace待Manager验收归档。

## wash v3视频验收通过，补齐真实末帧标签

James报告7f4d74e已独立核对两集三相机60个位置、2725行pose/action、原漂移点及采集转换契约，Manager接受773d177的视频修复与a75d173的闭环配置。sim633 metadata增量也接受。

剩余wash小修：EpisodeMemoryAnnotation目前仅对indices[:-1]生成phase/availability，丢掉真实M+1末帧。ep0 M1216的raw2408仍在label5区间[1710,2409)，末query首目标应有效；ep1末raw2989超出label5[1440,2970)，应unknown/false。请用完整selected mapping生成低维memory series与availability，robot_action_target前M行保持converted actions，末行重复；query/state/动作M行不变，offset0。复用现有sidecar形式，不改core/不增加tail_append。定向回归这两个相反边界，然后给James增量commit和更新后的低维sample；已验收视频不需要因低维修复重编码。

代码固定及低维增量review通过后直接启动全部172转换、记录metadata/job；这属于原授权，不必再次请求许可。视频/pose时间轴已经通过的范围不再重复整轮检查，最终正式产物仍需读回数量/格式/metadata和首尾低维检查。

sim阶段已集成到独立openpi开发分支codex/unified-sim-real-runtime，主库HEAD216cf2e（481→38→2c→69→633等价cherry-pick）。examples/rmbench与已审633逐文件零差异。主checkout没有可用.venv，Manager未改共享环境；采用独立review通过及集成文件同一性验收，不宣称主库pytest已运行。后续任务继续原独立环境，不需要重建。wash与中文操作文档仍待最终交付，整个task未归档。
