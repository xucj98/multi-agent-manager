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

## 用户授权更新：现场代码为可丢弃部署副本
用户明确授权：jx-4090-2-via-nx-aic上的openpi和robot-bridge未提交修改均可丢弃，以本地/GitHub为准；现场代码可随时替换。这替代上一条“不能覆盖现场未提交代码”的限制。请按本地已验收精确commit准备并同步远端代码：OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；bridge 124049fb78d29db1d77d13a9fd4a4b698fcfe6e9（若live本任务另有必要小修，需提交/Manager验收再更新）。无需为现场未提交代码另外备份或开审批。
允许清理两库tracked modifications及确认属于代码的untracked文件，删除前核对git status/clean dry-run；保留被ignore的模型/数据/.venv、~/.robot_bridge_env.sh及Policy Manager状态/同步内容。不要git clean -fdx。可用临时git bundle或已有remote取精确commit，验证树与commit一致；勿把本机未提交文件同步进去。使用现场普通部署checkout，不为每个模型引入新架构。
现有PM四个policy实例仍有使用者，不因代码同步擅自stop/restart服务；检查PM是否需重启才能应用必要变化，并把具体影响与最小操作报告Manager。先验证既有环境对新代码CPU导入/metadata加载是否可用，不升级/重装正在运行的共享.venv。环境确有不兼容时给最小依赖差异和影响方案，Manager裁定。没有授权真机动作；模型同步仍由用户已发起PM任务完成，不另传一份模型。
把本授权与实际现场commit/操作写入报告。完成同步后继续live/offline memory一致性及现用x1pro_takeover.sh部署交付，今天不做架构重构。

## offline RPC 修复独立复核
retry1实际运行在首个execute因memory prediction IDs被通用handle_execute转成float32失败，尚无有效执行行。b86负责局部修复，不把memory专有逻辑加入通用机器人base。作者新commit到达后，请独立复核实际WebSocket/codec→RobotServer→handle_execute→offline controller路径：full和serial各完整fake-policy episode，整数ID/row/query身份、执行行数、GT/mask/反馈、尾部/reset及原机器人浮点动作合同。检查修复和CPU集成证据后给GPU2 retry2准入结论，不能只以直接调用execute单测代替RPC验证。你不修改作者写集。

## 独立review裁定与最小启动修复
3b678966已确认live S2M代码CPU PASS，发现runbook错误承诺选定PM URL时policy pane必skip：run_policy_server.sh只看远端RB_POLICY_PORT，与RB_POLICY_URL端口无关。Manager认可问题，但不采用根据任意TCP监听推断托管身份或无监听自动启动的方案。
请在现有x1pro_takeover.sh增加明确CLI选项 --skip-policy：使用已经由Policy Manager部署的policy时，要求有效非空RB_POLICY_URL，policy pane只显示使用外部policy的说明，不调用run_policy_server.sh、不探测/启动/重启policy进程；正常无此选项保留既有手工启动行为。不新增RB_*变量、不改通用remote脚本、不改scheduler/controller。合理处理help/未知参数，明确skip路径无需checkpoint配置；避免tmux持久环境导致旧URL（核查沿现有环境机制正确传入）。复用既有测试方式，CPU fake tmux/ssh检验skip和默认路径，确保目标URL与基准端口不同也不启动policy。更新runbook使用该选项，声明PM child先就绪。
提交后交3b678966 reviewer复核；不擅自更新现场到未验收commit。其余已验收live逻辑不重写，保持今天最小范围。正式wash offline已全部通过并留存retry2，源任务b86已归档。

## 部署代码准入（独立review完成后）
独立review 3b678966确认041405f PASS（launcher全组164passed，live此前PASS），Manager已ff合入本机bridge。允许通过既有SSH将现场bridge同步至精确041405f0b35b2a173ac3461d297a43141d028026，OpenPI保持a869；沿用户授权可丢弃现场代码，保留模型/环境/机器配置及现有PM实例，不重启PM、不发真机动作。CPU导入验证与git identity/clean核对后回报。只读刷新PM实例和GPU资源，给full优先的具体可用GPU/端口及现有PM部署命令/请求（供Manager决定启动），不要擅自停止其他实例。确认是否需在实际scheduler主机同步同一bridge版本，明确仅policy主机更新尚不等于真机scheduler已更新。报告现场剩余步骤和简洁可用入口，完成后清理本task临时产物供归档。

## full Policy Manager 实例启动
GPU1只读确认约24067MiB可用、PM建议8951。Manager允许现在通过已有Policy Manager部署wash full（model_id取实际PM登记值，上节路径），GPU1、端口8951，启动前再核对空闲资源/端口；使用同一已同步bridge041405f/OpenPI a869和现有环境。不替换/停止已有pourtea、不启动机器人或scheduler、不发送机器人动作。验证PM child running、metadata全且匹配14D S2M/15Hz/H50/K30/full schema、模型加载日志无异常，给准确policy URL及PID/GPU/端口。若可用现成policy-only合成观测smoke且不接真机，可以验证一次infer；不要引入新工具框架。若启动失败，保存首因并只清理本次新建实例。服务用于今天真机，需按预计运行时长用mam job add登记进程（host用已确认SSH别名）；这是待现场使用的长服务，不能归档任务时自动停止。回报其状态，保留任务至现场交接。serial尚不启动，先full。

## 现场交接责任确认
用户确认jx-x1pro-m-060及现场WSL由内网同事更新。我们只完成已授权policy主机部署及验证，交付简短说明：bridge041405f、OpenPI a869（policy侧）、PM模型URL、现场x1pro_takeover.sh --skip-policy、现场同commit/CPU导入及phase/reset/takeover检查。不要尝试连接或更新master/WSL，不直接向同事发消息；由用户转交。真实机器人行为由现场验证，明确与已完成offline/CPU/policy-only测试的边界。

## 用户报告8951握手错误：优先定位来源
用户在PM看到8951持续报opening handshake failed / EOF before HTTP request line，示例UTC01:33:19。请优先停止本任务自行添加的任何裸TCP重复探活（如果有，先记录命令/来源），只读追查来源机器/IP/进程：核查本次部署检查命令、仍在运行的PM健康检查实现与旧进程加载版本，并用可用ss/短时抓包证明来源，避免再制造裸TCP探测。不要仅凭EOF堆栈断言来自launcher。区分你的一次性探测与持续周期性探测，给时间间隔和源/目的证据；不重启PM或其他policy实例。先快速回报已知是否本次工具产生，后给确证及最小修复方案。

## 用户更新实际机器人并授权部署
用户确认握手源10.10.2.82是本次主臂，实际从臂10.10.2.96。覆盖旧jx-x1pro-m-060/060拓扑：通过jx-4090-2-via-nx-aic应能SSH这两台，用户明确要求直接安排部署，替代上一条主从设备仅由同事更新的分工；WSL没有新增访问授权。
请先报告已确认握手源证据；随后通过policy主机跳转核查两机hostname/用户/代码路径/现有环境/服务和~/.robot_bridge_env.sh，不猜账号或端口，尽量复用已有SSH配置。允许更新两机部署代码至已验收bridge041405f，保留硬件SDK/.venv/模型/设备配置。现场代码按用户既定原则可丢弃，以本地/GitHub为准；不对ignored目录做clean。不修改正在进行的遥操/机器人控制状态：若有active控制进程或动作必须先报告实际状态和最小替换步骤，Manager裁定。
定位.82的旧探活所属进程/命令，若是本次准备的旧launcher探活，停用该探活而非屏蔽日志。先确认归属，不杀未知控制进程。核查scheduler执行机器为主臂.82，policy使用当前已部署wash full实例（从PM确认URL端口，内网policy地址沿现有配置）。机器人和master server端口沿各机实际配置，更新本次机器私有RB_*环境的拓扑，不提交IP到Git。保留wait-condition/UDP/takeover；只启动不会自动运动的服务和idle scheduler，启动前明确默认模式，不发homing/execute/UDP action或切autonomous。真实运动由现场人员执行。
优先完成SSH/CPU导入/metadata/观测与idle连通，必要依赖差异先报告，不盲升级共享环境。服务预计>1小时用mam job add登记，多个进程分别记录。交付准确两机commit、端口、服务PID/状态、policy URL、待机模式与现场接管/启动步骤，不能将服务器ready等同真机运动验证。

## 用户明确采用更新并重启 launcher
用户判断不必单独处理旧探活，要求更新最新代码并重启launcher。按此执行：在实际.82/.96机器完成当前已验收版本更新，重启本次既有launcher及其需要更新的关联服务，保留配置并指向full PM实例，使用--skip-policy避免额外启动policy。无需另做旧探活修补，也不再为这一已授权launcher重启重复确认。不要重启PM或无关实例，不发homing/execute或进入autonomous；重启前后核对默认待机/接管状态。之后确认8951 EOF周期错误消失、实际scheduler采用14D Memory v1且H50/K30、服务连通和资源归属。若实际运行的launcher并非x1pro_takeover.sh，先读实际入口，沿同一部署机制应用已验收代码，不猜测用错入口。

## 用户指出既有端口skip机制：先核对实际配置
用户指出原run_policy_server已有端口占用则跳过。Manager承认原机制有效，只在远端RB_POLICY_PORT与scheduler RB_POLICY_URL不一致时可能错误。暂不将新增--skip-policy视为现场必需，不为此另改代码或强行改启动方式。请报告当前实际launcher入口、远端RB_POLICY_PORT、scheduler RB_POLICY_URL及相应端口的读取/传递路径，确认是否确有不一致。继续已授权代码更新与原launcher重启，沿现场原有PM共存机制；若已使用新选项如实说明，不为撤销选项立即再重启。先核对事实供Manager与用户讨论是否保留新增选项。

## 用户停止远端部署，改为现场操作指南
用户明确GUI launcher与x1pro_takeover.sh是并列功能入口：前者GUI供非程序员，后者TUI调试；不需要同时使用。立即停止新增远端部署、重启、配置写入，由现场同事执行。不要为撤回再重启/恢复；停止正在筹备的后续写操作，若有已在途操作先核实最终状态。
先快速向Manager报告已实际完成的policy/.82/.96代码变更、机器路径、服务PID和运行状态、哪些尚未完成。记录当前full实例URL和metadata验证、环境依赖实际缺口、机器人是否确实保持idle。只能声称实际观测，未知标注。
据此交付简洁现场操作指南（仓库docs/tutorials/wash-cup-memory.md，本地worktree编辑提交允许），区分GUI launcher与TUI两种入口并建议沿现场惯用入口，不串联启动。既有原端口skip机制事实准确，--skip-policy非必需条件；不要在未核实现场端口差异时要求用户用新选项。列两机实际IP/角色的现场交接信息放任务报告，仓库文档用角色/RB_*变量避免硬编码。注明更新代码精确commit及取得方式、保留本机SDK/环境/配置、policy manager中full模型选择/URL、S2M14D/H50K30/phase、待机和现场受控检查；实际控制命令沿既有机制，不发明快捷键。检查用户能从可访问GitHub取得commit；未push的版本不能给git pull即可的假指令，告知Manager需发布哪个分支（你不要自行push）。完成指南供Manager验收转交，保持现有服务，无SSH写操作。

## 操作指南补全可执行更新步骤
cf7ffdb方向正确，但目前只有应为某commit，缺如何更新/重启。请补短的现场步骤（不远端执行）：现有GUI停止三项服务确保旧tmux子进程不保留旧代码→两机更新bridge→用现有解释器核对CPU依赖→主臂systemctl --user restart rb-launcher.service→GUI检查并启动。说明restart GUI不会自动重启已存在tmux服务，避免更新后继续跑旧scheduler。代码取得可从已更新policy机的Git仓库fetch精确041405f（参数化SSH目标和repo路径），不假设GitHub已有该commit；无需为此推GitHub。只核对已有本地源码/此前只读证据，.96路径/解释器未知则作为需现场确认变量，不能猜值。明确主臂light openpi_client.memory_config/PyYAML等实际新增依赖应如何通过原环境安装入口满足，机器人不需要安装模型权重/完整GPU openpi环境。若不足以写精确安装命令，明确现场CPU import失败的报告点，不编造。保持指南简洁，不另建部署框架，不再SSH。

## 用户最终明确：TUI 调试操作指南
用户要TUI版本，使用scripts/launch/x1pro_takeover.sh。GUI launcher是常驻服务，可以保留；GUI/TUI只是启动robot server/master server/scheduler的并列入口，不需停止GUI后台来用TUI。只需处理已存在的同组子服务，避免重复/继续跑旧代码。上一条GUI操作指南方向撤回，改写为TUI，勿再要求停止GUI常驻服务。
现场操作指南需给：在现场可SSH三机的终端更新所需bridge代码（版本从policy现有Git取得）；主臂scheduler与从臂代码/现有解释器准备；source ~/.robot_bridge_env.sh并设置主臂/从臂/policy/scheduler各SSH和URL变量（角色参数化，实际已知地址放报告）；bash scripts/launch/x1pro_takeover.sh（默认入口），说明本次policy已有PM实例，原run_policy_server端口skip照常，当前远端RB_POLICY_PORT8949已被PM child占用，scheduler另连full8951。不要强制--skip-policy，不将端口不同本身当故障，不改或重启PM。核查实际脚本tmux持久RB_URL传参已正确。
GUI可以一直常驻，TUI用于调试，不能错误写成GUI和TUI程序不能共存。仅启动的三个子服务应在更新代码后按既有停止/重启流程更新，不触碰原生硬件进程。控制UI/idle与phase检查沿已验证机制；命令不远端执行。交付一个简洁可复制的TUI指南、精确版本及未知现场变量，尽快完成，避免继续堆历史说明。

## TUI文档最终核对
默认041405f TUI路径没有--skip-policy分支的URL内联赋值。启动前文档需export实际填写的RB_*；已有tmux server时用tmux set-environment -g刷新所需拓扑变量，避免旧URL继续进入新pane；无tmux server时新进程继承export即可。不修改代码。删除RB_PY自赋值，用git -C rev-parse校验仓库代替要求.git为目录，以兼容worktree。其余仅必要文档修正，不扩范围。

## 用户确定交付流程：WSL checkout → push_code auto → TUI
用户质疑手工wheel，理想流程明确为WSL checkout codex/unified-sim-real-runtime、配置RB_*、scripts/utils/push_code.sh auto、scripts/launch/x1pro_takeover.sh、:8088。不得再要求用户现场手工构建/传输/安装wheel或逐机git checkout。只做本地代码调查先提出最小可实施修复方案：push_code当前仅rsync bridge，不同步/安装scheduler新增的openpi_client.memory_config。说明依赖如何随现有交付自动满足且仍共用一份schema实现、不手拷维护第二份实现、不安装完整OpenPI训练环境、不依赖WSL未声明的openpi邻接仓库。比较已有依赖入口可否用固定轻量包/随发布源码等合理方案，先报告推荐方式和代价给Manager，不擅自大改架构或远端执行。清楚区分一次性环境准备与每次开发循环；测试需覆盖最小WSL仅bridge checkout起步，主臂缺轻量client时，以及已有tmux旧变量/旧服务的问题。指南最终应围绕用户这条短流程，而非堆手动补救命令。新代码方案待Manager裁定。

## 用户授权实施：memory_config.py 归 robot-bridge
用户明确：直接把memory_config.py放到robot-bridge，不再依赖该openpi-client包。替代此前wheel自动交付方案讨论。请在本task独立两库worktree实施：以已交付dfc9e1095badd7f37d9260d3275df3cca2700d90 bridge和a869498f OpenPI为基线；确认本机若有其他新commit勿覆盖。将纯schema模块迁至robot-bridge内合理公开位置，scheduler及offline直接导入，移除机器人安装openpi-client wheel的要求/专用安装脚本及对应过时文档测试。
训练、模型推理及offline仍共用一份schema实现：OpenPI引用bridge中纯模块，避免依赖整个机器人框架/硬件SDK、额外包仓库/插件/动态路径搜索/手工PYTHONPATH。模块只能有原纯Python/NumPy/PyYAML等轻量依赖；不改变schema、模型、样本构造/时序/编码/反馈算法，旧checkpoint原metadata保持可用。OpenPI依赖如何以现有环境管理声明、两库怎样共同安装需明确可靠，不要求机器人安装完整OpenPI。不得保留两个手抄memory_config实现作为未来维护源。如历史openpi import兼容有确实必要，最多重导出而非重复实现，说明理由；不可让机器人继续依赖openpi_client。
保留当前正在运行训练/仿真worktree及环境，不更新它们、不跑GPU、不操作远端。移除wheel手工部署流程，现场指南收敛为用户要求：WSL checkout→配RB_*→push_code.sh auto→x1pro_takeover.sh→8088。GUI后台可常驻，TUI默认路径与既有policy占用skip保持，不强制--skip-policy。
验收：无openpi-client可导入的独立最小bridge环境中，真实checkpoint metadata建立full/serial MemoryContext、live/takeover/offline CPU回归通过；迁移前后schema样本/编码/mask/反馈输出一致，OpenPI相关sample/model-config/metadata CPU测试通过；import纯模块不加载硬件SDK/JAX/Torch；源树代码同步足以提供模块，push_code/TUI已有测试保持。保持测试有实际行为断言，避免只替换import。提交两库代码和必要简明文档，发布report给Manager独立review；不自行合并/push。清理临时产物，保留workspace验收。

## 用户最终简化：两库各留一份，无跨库依赖
用户明确现在先两边各自一份memory_config.py，robot-bridge不依赖openpi，openpi也不依赖robot-bridge。覆盖此前单一实现源和OpenPI改为引用bridge的要求。立即停止跨库安装/依赖声明/环境脚本调整；如本task已做相关OpenPI未提交修改，恢复本task自己引入的改动至原a869，不碰其他人的内容和活跃环境。
最小交付：从原a869纯memory_config.py复制到bridge合理位置，bridge scheduler/offline/相关测试改用本库模块。OpenPI保持原实现和原训练/推理行为，不改包引用。两份暂时一致即可，不引入自动同步/共享包/抽象。删除bridge为memory_config增加的openpi-client安装要求/专用wheel流程，保留与本任务无关的policy服务依赖。
用户问是否可部署，因此优先给当前实际进度、最小阻塞和预计交付；尽快提交bridge修复，CPU最小环境明确没有openpi_client时用真实full/serial metadata建context并完成scheduler/offline必要回归，复制前后算法一致。文档只保留WSL checkout→配置RB→push_code.sh auto→TUI→8088。无需训练重跑、远端部署或新增环境框架。交Manager独立review后合入并push同一分支，给用户精确可部署commit。

## 最小文档回归修正
3906重写短指南误删dfc9的已有tmux set-environment刷新步骤，而默认TUI没有URL内联。请仅恢复该文档片段，避免本次schema迁移引入既有使用步骤回退；不扩TUI代码改造。独立review已通知。
