# Memory实验：评测入口、旧full时序锚点与开跑准备
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

eval_result统一RMBench/eval_result/memory_chunk_20260910/<run>；smoke也在本实验组但明确smoke名，不进入主表；正式实验接替后清理。不能在robot-bridge/eval_result产物，不造第三个日志根。继承metadata+config，不复制代码。交付可复跑命令/配置、smoke结果和视频路径、是否可运行P1/剩余缺口、环境实测吞吐粗估，写report与commit发布。保持可继续接评测工作；不自行派agent。
