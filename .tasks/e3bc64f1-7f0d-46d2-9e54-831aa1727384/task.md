# 九任务覆盖第一波：wuwen-1 seed0

用户已批准Manager的/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md实施，先用wuwen-1的8卡A100，不等待MAM兼容性排查。你负责具体实现/验证/运行，科学主张/实验取舍归Manager。回CODEX_THREAD_ID用于绑定；读MAM AGENTS、README、.local说明和OpenPI/RMBench AGENTS、worktree环境文档。

## 当前已分配资源与精确矩阵
wuwen-1在2026-09-13 09:35 CST八卡均4MiB/0%空闲，GPU0 swap_blocks N(no-memory)；1 swap J(full per-frame)；2 battery_try N；3 battery J；4 cover_blocks N；5 cover J；6 swap S(serial lag30)；7 cover S。所有train seed0、同pi05_base、50条匹配demo_clean_state、batch32、20k、H50/K30、save_interval20k、BF16 model-only，命名与元数据沿当前规范。下一波battery S不在本批八卡内，不补任何training seed1/2。

## 实现与验证
已有五任务转换资产，swap/battery/cover 50集数据和legacy字段可用，但当前Memory-v1 binding、sidecar、YAML/config builder仅前两任务现成。创建独立OpenPI worktree从884e62b（先确认本地commit）开始，其他需要改的库也建独立树，保持运行树不动。扩展三任务current-truth adapter，严禁把legacy lagged input当current truth、demo_clean替代demo_clean_state、或重用不匹配mask旧30k权重。优先推进三条N训练所需的robot-only sidecar/norm/config，验证通过后逐条开跑；并行补J/S，不必等所有实现一次齐才使用空卡。

J动态phase与T计划共用未来逐行+row30尾mask、固定H loss归约；当前same field目标/获取/反馈规则按已审计legacy语义迁移，并检查来源metadata。swap字段phase/initial_empty_tray/first_origin_tray；cover phase/red_pos/green_pos/blue_pos；battery目前仅phase，不能声称已经完整表达已尝试集合。遇到必须改变语义的情况把事实和可选明确实现发Manager裁决，不自行选测试结果更有利方案。Memory使用从past可获知的语义，正常推理不能送GT。

复用现有训练入口、sidecar/norm tools、metadata和恢复验收。按改动运行有意义的CPU/真实批次测试，每种新路径做50step save/restore/finite验证（可在各自预留卡，记录smoke而非正式）。N验证和可复核diff先快速发Manager；Manager会及时审核解锁正式训练，无需用户再次批准。正式启动固定干净commit，每项先确认GPU未被他人占用。禁止覆盖既有checkpoint/result路径；每条预计>30min进程立即mam job add登记host真实PID，确认step100有限loss和实际GPU占用后发布receipt。尽早报告已启动/尚待验收的具体卡，不把计划当running。

完成训练验收完整params/metadata/shape/BF16/finite和独立恢复，再归档job并交可评清单给Manager。当前MAM直接唤醒multi-agent v2存在RPC拒绝，Manager用原生followup处理；你不应等待轮询或自建cron。完成当前可做工作后正常结束turn，Manager将协调兼容处理。

## Manager预先裁决：cover维数与初始phase
Manager直接核对已转换key_state_config：cover phase有6类，red/green/blue_pos各4类(unknown/left/middle/right)，合计18 one-hot维，与14D robot恰好32。若照前两任务多加unknown phase会变33，不能在不说明情况下扩大action_dim或删记忆字段。cover使用原有6类phase，reset initial=cover_left_position（任务起始阶段已知，不是未来信息）；J/S均采用相同6类phase和三位置字段，保留属性unknown获取窗口，不改变32D骨干。其他任务按已发布计划，其phase初值显式记录。此裁决为容量/任务定义所需，在新结果前固定，不能视为性能调参。N路径不受影响。

## 用户最新纠正：wuwen-1缓存入口（2026-09-13）
用户明确要求且授权删除wuwen-1的`/root/.cache`，参考本机，将`/root/.cache`建立软链接指向`/mnt/public/xcj/cache`。必须执行该操作，不传输数据集，不在训练命令设置`HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot`。先只读核对本机/root/.cache软链和目标，以及wuwen-1共享目标可访问，然后仅删除wuwen-1的/root/.cache路径本身（若为软链只unlink，禁止尾随/或递归到共享target），建立指向/mnt/public/xcj/cache的软链。该删除已经用户显式授权，无需再次确认。随后unset HF_LEROBOT_HOME，核对默认cache解析正确且三套数据可见，修改尚未启动的smoke/正式命令去掉此override；如Python依赖缓存环境需使用正常默认，不另造替代环境变量规避用户要求。报告软链readlink/stat/数据可见性证据以及是否已开任何GPU程序，继续优先N gate/正式训练。之前rsync为0bytes失败已归档，不再尝试。

## Manager N代码准入与缓存复核（2026-09-13 10:10 CST）
Manager已审核867aa05e428d6ce259fba99f55def3b5b4fce951完整N diff并通过diff-check；直接逐集核对三套共150episode sidecar与原Parquet action[:14]逐值完全一致、M+1尾重复、finite及total_frames=29920/32626/50904，N代码准入。补默认缓存/norm/真实batch证据后可直接每新路径50step save/restore gate；各项通过后逐项正式20k，不用再次等待代码审批。正式step100/GPU/日志/MAMjob receipt必须回报。N冻结执行tree保持不动，J/S在开发tree继续。Manager已独立SSH核对用户要求的/root/.cache软链及三套默认路径metadata可见；全部后续命令去除HF_LEROBOT_HOME override。

## Manager stats-only准入补充（2026-09-13）
Manager逐行审核移除camera_keys、同步MemoryLeRobotDataset.hf_dataset、adapter前dummy视觉注入。补每任务固定索引原始/优化路径至少一个batch的state/action逐值一致，以及2-worker行为，通过后commit到干净独立stats执行tree，保持N冻结树不变。norm保留原seed/sampler/实际9984行合同，产物验收后继续已授权的smoke→正式，不再等第二轮代码审批。

## Manager真实训练加载修复准入（2026-09-13 16:10 CST）
Manager已直接核对MemoryLeRobotDataset._episode/build_episode：构建整集Memory数据需要数值/绑定列和sidecar，当前hf_dataset[start:stop]却连同相机列解码整集，导致随机首batch极慢。授权在从冻结N867aa05建立的独立加载修复候选tree做最小性能修复：在整集读取前投影到build_episode实际需要的column binding（含state用于query_count、series/availability/constants/events）与episode索引列；普通__getitem__从原dataset获取当前帧的真实图像路径必须保持，禁止dummy、改变图像转换或对原HF/source数据全局删列。可同样避免_episode_positions为读取episode_index解码首帧图像。

不改数据、sampler/seed/次序、norm、targets/mask/loss/输入语义；原冻结树保持不动。补证明整集cache不触发图像解码的回归、原始/新路径实际样本的图像与数值/标签/权重逐值一致（至少三任务与一个现有memory J/S路径），处理列投影后原hf reference同步及stats-only兼容。实际random32batch/2worker速度与finite确认；同源原始对照可用固定contiguous batch避免无界慢profile。代码diff和结果交Manager快速review后，以新干净commit继续原50-step保存恢复→正式；不需再咨询是否可以修这个明确瓶颈。优先解除N启动，J/S继续已有语义接入，禁止把新实验指标调优混入性能修复。
