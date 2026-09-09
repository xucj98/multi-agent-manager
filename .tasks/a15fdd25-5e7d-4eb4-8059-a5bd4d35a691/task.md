## F0 smoke匹配与终止query裁定

保留recorder当前完整配置匹配检查。四个row配置分别在自己的100ep之前运行一个2rollout smoke（一video一no-video），然后固定该配置提交开跑；不新增selector白名单，不放宽门禁代码。只允许GPU0，按row30/20/1/50依次执行。先前“只做row30即可覆盖其余三行”的预期不作为当前验收。

你发现terminal trace next_query=false但公共循环仍额外infer的问题已交runtime owner做小修，且交reviewer复核。目标是在OpenPISimulationScheduler现有路径中对terminal跳过真实policy infer，不改SchedulerBase通用循环/真机循环。拿明确修复commit后更新入口固定版本；先继续交准备阶段report，不擅自按fd38513跑正式。

## 恢复执行：F0明确接口与资源裁定

runtime commit已到：robot-bridge fd38513adb5ba171327358f70f55f88059de49d2。使用你本task bridge独立分支合入此commit；openpi可合主库58d6f2155acc3af03017677bb3f536101e6699f4并使用自己的editable环境。接口为OpenPISimulationScheduler.params.legacy_full_feedback_selector，支持{kind: index, value: 0|19|29|49}和{kind: last_executed}。F0保留旧checkpoint原字段/归一化/模型，不强行将其转为新memory_config；该显式selector仅控制旧full反馈行。准备四个固定K30/H50配置和诊断，先row30。独立runtime reviewer正在复核，收到Manager确认F0无阻塞后才运行新入口的一个2rollout smoke，检查一次video/一次no-video和metadata；通过后提交完整正式配置再启动100仍等Manager通知。

资源以本条为准：当前仅分配本机GPU0，GPU1留训练50step smoke，远端训练预留。四个F0可在GPU0依次执行，不因等待第二卡停工。开跑前检查GPU0显存。原文同时GPU0/1安排失效。回复准备就绪commit、smoke实际命令、报告需要的runtime阻塞；不重建已有worktree，不新建任务。

# Memory实验：评测入口、旧full时序锚点与开跑准备

## 下一阶段清单（等待Manager恢复agent并发开跑通知）

论文计划F0已明确：同一个旧rearrange full 30k，H50、K30，所有memory字段统一分别读取row1/20/30/50，共四个100ep run，成对初始seed一致。文中row为1-based，因此schema index.value分别0/19/29/49；last_executed在实际k=30时对应row30。先排row30/20，本机GPU0/1各一个串行100ep，完成后row1/50；正式启动前Manager会重新确认资源。使用同一runtime commit与明确的旧full等价schema/config，不能某一臂悄悄走不同解码/归一化。row50是模型对未来时刻的预测，不读取未来GT。记录实际执行k、所选行和各字段before/after语义；中途终止不伪造下一query。

目前已完成旧入口smoke，仅作加载/产物锚点；新selector/trace代码集成后按同一路径完成必要2rollout（一次video一次no-video）smoke与独立review，固定commit后才能正式跑。这个清单是已授权实验的安排，不是要求当前闭合agent自行开始。RMBench保存两个层级目录及逐步metadata要求不变，50条人工检查偏差>10个百分点并记录，不按成绩丢弃不利run。
# 目标

# 用户最新数据约束

用户明确新仿真训练数据来自demo_clean_state，demo_clean缺metadata/详细子任务标注。后续新checkpoint来源检查遵循此要求。此要求针对训练/转换数据，并不要求擅自改变旧checkpoint评测的场景task_config；P1仍固定已核实的旧评测协议。

准备统一memory首批实验的RMBench评测入口，先用可用的旧shared full checkpoint验证加载、完成进度与反馈时序。GPU实验owner，为后续新20k训练的100ep评测做好入口和留痕。不要重跑全部历史实验。代码/配置成果交Manager审查后正式跑。

# 工作区/代码边界

用MAM创建RMBench worktree base e31d14fe0818235d471b371924ea30c273e75c7a，按需添加robot-bridge b17f6c53ffbc1030972a9820cf592f28b937d501和openpi 71c80db723a242c61cfe429dd6794e9ece3cbcf1；全部在同任务workspace，用独立环境。先读各库AGENTS.md，特别RMBench代码/实验/rmbench guidelines，robot-bridge conventions。写范围RMBench experiments/memory_chunk_20260910/ 的简洁配置/命令/README，必要诊断修改先报Manager；不改三库模型/scheduler核心（其它agent在做）。不修改主checkout。

# 现有checkpoint与关键问题

full：/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000，历史93/100。metadata和params已查可读但未实际load。现有重构900实验/manifest可作运行入口来源；实验索引在RMBench/experiments/history_audit_20260909，计划在 /root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md。

先查最少入口，使用已固定代码和旧checkpoint的原协议做1个smoke包含2个rollout（第1有video，第2无video），验证policy加载、RMBench结果格式、视频可读、config/command+commit+上游metadata。确认执行K30时旧full实际消费哪行，是否现有配置可选择第20/第30行，以及日志是否有实际k。不能只看成功率就声称时间对齐。若缺参数/trace，列出具体缺口交runtime owner 9f5a3889-49a6-4f00-af84-096d8042c3bc，不要临时篡改模型输出来冒充配置实验。

# GPU与正式运行

你独占本机GPU0用于此任务，启动前只检查该卡仍可用；本机GPU1留另一集成任务，GPU2..7已有他人工作，wuwen-1八卡留新训练，不使用。JAX明确限制可见GPU及合理显存分配，仿真+policy共用GPU0，不额外占卡。训练不在本任务范围。

正式eval每run100rollouts单GPU串行，禁止拆分。预备比较为K30 row30 vsrow20，基于同checkpoint/初始条件/固定H50和解码；新入口无阻塞review、2rollout smoke产物确认、代码commit干净后由Manager发正式运行通知（不先行擅自跑100）。到50rollout检查偏差>10个百分点是否协议/基础设施问题，不删除不利episode。预计>1小时的进程用mam job add登记本机真实PID/用途，结束记录结果和清理再archive job。

# 产物与交付

Manager验收反馈：83cbec9的README需按用户长期约定改为中文，具体操作直接写命令，不再要求先export RMBENCH_ROOT/BRIDGE_ROOT/OPENPI_ROOT。可以从明确cwd运行并由脚本默认定位同一workspace下的三库，或提供简洁CLI参数；脚本内部变量不受此限制。README不要说“runner会自动记录>10pp gate”，除非已核实实际代码实现；当前人工50rollout检查要写清由实验负责人执行。路径对外报告用共享主RMBench/eval_result的真实保存位置，worktree别名可以附带，但不能误让用户以为成果留在临时workspace。这次只修正文档/必要入口默认值，不重跑相同GPU smoke，不开100；追加commit和report后等新runtime集成。

eval_result统一RMBench/eval_result/memory_chunk_20260910/<run>；smoke也在本实验组但明确smoke名，不进入主表；正式实验接替后清理。不能在robot-bridge/eval_result产物，不造第三个日志根。继承metadata+config，不复制代码。交付可复跑命令/配置、smoke结果和视频路径、是否可运行P1/剩余缺口、环境实测吞吐粗估，写report与commit发布。保持可继续接评测工作；不自行派agent。
