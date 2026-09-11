# wash-cup 今日真机交付验收

## 目标与边界
用户已明确今天不做统一架构重构，明天再讨论。今天优先让wash-cup full/serial可供现场真机测试。旧offline/live路径已验证过，本轮只针对新增memory检查一致性和交付现用入口。你负责独立验收、部署说明及必要的小范围接线修复，不改SchedulerBase循环，不合并多个scheduler、不引入plugin/session，不触碰正在跑的实验工作树。

## 工作区与证据
在本task workspace用mam创建robot-bridge worktree(base fda269c1f333dabdb5628c083a4dba3db0938333)、openpi(base a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4)。读各AGENTS和bridge docs/design/conventions.md。
模型/数据来源读ad6bb77e最新已发布report：两20000已通过完整参数/GPU恢复，S2M单phase，15Hz/H50/K30，全172合格ep训练。固定5ep offline由b86b3d02负责（自己的GPU2/代码树）；你不重复其完整offline、不占GPU、不操作真实机械臂。原offline独立review报告65a3已归档可读。首次真实offline失败产物在RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep，源/解释器握手通过后因顶层query_stride=None拒绝，作者正在仅修launcher并测试实际metadata，Manager会交新commit给你定向复查。

## 核对与交付
1. 比较当前OpenPiScheduler/Takeover与OpenPiOfflineScheduler：同一真实checkpoint metadata和相同观测/预测序列，在对应execute completion时刻构造相同policy输入、选择相同动作与memory反馈。full(t输入,t+j+1输出,K30末执行行反馈)和serial(lag30训练输入,当前query预测反馈)分别检查；不要只验证MemoryContext孤立对象。
2. 用真实两checkpoint metadata和CPU fake transport/policy做有意义的直接scheduler回归。覆盖接受未完成时不提前提交、完成后反馈、reset/手动切换/takeover丢弃pending、原wait-condition取观测和已有UDP接管行为。不要对硬件SDK做猜测；声明CPU验证与实际现场验证边界。已测试的老功能无需全重跑。
3. 只在发现实证接线差异时提出/实施最小修补，写集限定live openpi.py/openpi_takeover.py及必要测试、启动配置/操作说明；不改offline launcher/controller/scheduler（b86负责），如需跨写集先报告Manager。代码改动给Manager审阅和独立复核，不自行合并。
4. 复用现有真机启动脚本，写一个简短wash部署说明（docs/tutorials/wash-cup-memory.md或现有适合位置），列full优先/serial随后、精确checkpoint路径、配置/运行commit、沿既有RB_*环境的启动方式、phase UI/reset/takeover使用和检查方式。只增加有实际需要的配置，不写新启动框架。现场机器/现用脚本Manager已向用户询问，未知项明确标待提供；先完成不依赖现场信息的工作。不发送机械臂动作。
5. 作者launcher新commit到达后独立检查metadata.query_stride缺失与schema execution.rows的真实兼容行为，只把对应含义一致的字段校验，不混淆训练采样与执行K。用真实失败served_metadata反例与旧drawermetadata验证，给出可重试准入结论。

先30分钟内报告关键阻塞和最小方案；能完成则直接提交有用交付。简报写任务完成项、workspace/两库commit、测试和可复制入口、真实部署未验收项，发布report。清理自己的测试缓存/临时文件，保留worktree供验收归档。全程不占GPU，保持与b86写集分离。

## 07:51 现场入口与优先复核
用户确认现用启动入口scripts/launch/x1pro_takeover.sh，环境由现场WSL的~/.robot_bridge_env.sh加载；当前训练服务器及用户均不在内网。policy为jx-4090-2，robot为jx-x1pro-060，master/scheduler为jx-x1pro-m-060。内网URL在用户消息，文档不硬编码这些地址，也不从此服务器探测连接；跳板机由用户确认，内网同事最终执行。部署说明沿原RB_POLICY_SSH/URL、RB_ROBOT_SSH/URL、RB_MASTER_SSH/URL、RB_SCHEDULER_SSH机制，说明哪些是现场既有值、哪些模型相关值要换。先交付可供同事执行的现有入口，不新建跨网框架，不发送真实动作。

offline修复commit已到124049fb78d29db1d77d13a9fd4a4b698fcfe6e9（作者report已发布）：只改launcher和测试。请优先在自己的分支推进到该commit，对真实缺顶层query_stride的served_metadata/新schema K校验做约5–10分钟定向复核并先报告准入结论，让offline GPU2尽快重试；随后继续live/offline一致性与部署文档。重点确认数据采样stride与执行K不被混同、实际source/clean gate保留、legacy drawer不回归。你尚无业务实现修改时直接ff即可；若有自己修改先妥善保存，不丢代码。后续若改live文件，与作者launcher写集仍分离。

## 08:05 Policy Server已可达（只读核对）
用户已配置ssh jx-4090-2-via-nx-aic通达policy server，Policy Manager本机8100，已由用户添加wuwen-nx-aic源并同步两个模型。不要重复传输、取消或重启用户同步。
Manager已只读确认：远端/home/xucuijie/Projects/openpi HEAD673038f77fe8245a1309d32c4e1701e748915ba3且checkpoint_metadata.py有未提交修改，新openpi_client/memory_config.py不存在。bridge根/home/xucuijie/Projects/robot-bridge HEAD68b70367104045bee1e9f540187fe5d45d920e7b，有多处同事修改（launcher/scheduler等）。Policy Manager PID3646使用openpi/.venv/bin/python，从bridge cwd启动。8950已有pourtea实例；8949/8951/8952也在运行。GPU0约315MiB free、GPU1约7150MiB free，不能擅自停服务或改现场checkout/环境。
允许你通过该SSH别名只读研究Policy Manager既有部署参数、backend配置是否能为wash选择独立bridge/openpi源码及解释器，并给出最小部署方案/具体兼容缺口，先不要写远端或改共享环境。现用Manager JSON WebSocket ws://127.0.0.1:8100，cmd=status为只读；远端openpi/.venv有websockets.sync.client（连接时proxy=None）。避免输出无关模型完整metadata，筛选wash同步与必要拓扑。远端不是本集群共享文件系统，模型落点由Policy Manager管理。
此调查与live/offline检查并行顺序自行安排，但先发offline准入让GPU2恢复（Manager已根据你的报告准入）。不占远端GPU、不发robot动作；有用结论写简报供Manager决定安装/部署动作。
