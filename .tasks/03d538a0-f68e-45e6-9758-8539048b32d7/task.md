# Review C评估首次infer预算修复与实验队列台账

Review source delivery (source TASK-ID: e6908de7-4b02-465a-987b-a19eba7a315a):
{
  "task": "e6908de7-4b02-465a-987b-a19eba7a315a",
  "commits": {
    "RMBench": "3e69b1e665a8eac0104d261b233f1b3339007e00",
    "robot-bridge": "8ea6078543a875b5ae223df16891cdc1fe975c66",
    "openpi": "a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4"
  }
}

Source task requirements:

# Memory v1 新 checkpoint 评测准备

## 目标、范围与工作区

准备新memory_config checkpoint的RMBench评测，使首批20k结束后可立即按“对应smoke2→正式100”开跑。兼顾列清旧drawer两个模型的offline回归入口，当前只做CPU准备；GPU时段由Manager另行分配。不要修改模型、数据转换、controller、scheduler或MAM，不新建通用launcher/队列框架，不派agent。

通过mam workspace add复用各库一键入口，为本任务建立RMBench、robot-bridge、openpi三个独立worktree/环境。bases：RMBench f022badd11228e5763a301339a5d1fe5574962b4；bridge 8ea6078543a875b5ae223df16891cdc1fe975c66（Pascal作最后CPU增量复核，Manager随后告知）；openpi 929e398（主库当前开发分支，代码树等价42011a3）。先由git解析openpi完整SHA再调用MAM。读三库AGENTS、RMBench docs/guidelines下实验规范以及bridge docs/design/conventions.md。

只在本任务RMBench的experiments/memory_chunk_20260910内新增必要的新schema配置/命令/中文说明，保持原F0文件。其它两库用于固定版本依赖和验证。若发现通用入口缺陷，报告具体复现，Manager交相应owner修，不跨写集。

## 已有事实与要复用的接口

新wire已由真实CPU transforms→Context独立验证；full/serial实际50update、BF16完整参数保存和仅checkpoint恢复均通过。语义输入memory_input_ids(F,)；动作输出robot-only，memory_prediction_ids分别full(H,F)/serial(1,F)。新schema由checkpoint metadata决定，不从实验名称猜方法，不注入legacy_full_feedback_selector替代schema。

优先复用现有robot-bridge benchmark入口、RMBench recorder、命令模板与metadata继承，不复制整份runner。先查现有入口是否仅需配置；合理时新增一个简短入口即可。正式eval结果RMBench/eval_result/memory_chunk_20260910/<run>，说明同名experiments组；禁止新建robot-bridge/eval_result。转换→训练→eval的metadata/config/实际command及commit按现成机制完整继承，不复制代码，不新增runtime/provenance框架。

首批模型为rearrange full_t_plus_1/full_t_plus_30各seed0/1、serial_lag30 seed0、no_memory seed0；put_back full两种目标seed0随专用norm验收后启动。训练owner任务e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe的report有准确配置名、输出路径和模型进程；只读获取即可，不反复监控它们。最终checkpoint为config/exp_name/20000，所有新sim训练来自demo_clean_state；评测场景继续原demo_clean_eval。

每个正式run在一个GPU上串行100，sim与infer共卡。初始条件沿既有seed100000起和同任务共同列表；每配置/ checkpoint先一个含video和no-video各一集的smoke，核对产物后从干净commit正式开跑。默认H50/K30，新full按schema在实际完成后取row30/index29；serial query反馈、no-memory空字段。不中途按成绩改配置或弃掉结果。50条检查按既定10个百分点诊断约定。

## 当前CPU交付

1. 给出可复制的新full/serial/no-memory和put-back评测入口/配置，支持明确checkpoint路径、run名和单GPU，不手写模型内部默认参数。证明checkpoint metadata进入真实backend/scheduler配置，没有绕过schema与smoke检查。
2. 用现有50step产物做仅元数据/命令dry-run，不加载GPU模型、不启动仿真。两checkpoint位置：
   - /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50
   - 同根下pi05_rmbench_rearrange_blocks_serial_lag30/serial_lag30_d10cc01/50
   保持其只读；Manager暂留至新评测入口的必要技术验证完成。20k正式run仍需各自匹配smoke。
3. 列清旧drawer full_state和serial_soft各5ep offline回归的命令、数据输入和结果位置。旧模型在RMBench/policy/pi05/checkpoints/pi05_x1pro_drawer_sorting_s2m_full_state与pi05_x1pro_drawer_sorting_s2m_serial_soft，先读取实际目录/metadata，勿猜step子目录。可用数据在/mnt/public/xcj/cache/huggingface/lerobot/drawer_sorting_x1pro_shared_memory_s2m_15hz_v2，119ep；原public3路径在本集群映射public。沿既有offline机制、S2M与多字段配置，不另写drawer专用算法。此项先准备，不占GPU。

需要保留的回归按真实边界选择；不要复制大量schema/factory或重跑全部已验收core/loss测试。代码变动目标为现有入口的少量配置和接线，若预估超过约150行可执行代码先说明原因，不能靠删必要留痕压行数。

## 09:34 Manager对入口范围的裁定

采用本实验组的窄audit/manifest适配器。现有BenchmarkRunner要求静态manifest及checkpoint逐文件evidence，而公共模块只有验证入口；本轮保留满足该既有接口的必要构造，不扩展bridge公共框架。删除重复的detach/队列日志/GPU检查/check-smoke逻辑和drawer shell wrapper，README直接列现有drawer_offline.py命令。资源分配由Manager负责，启动长进程仍登记MAM，正式smoke门复用runner。

同一入口明确支持technical-smoke，用现有50step产物验证新wire；其结果标记技术验证、限smoke两集且不能用于formal门禁。正常smoke和formal仍要求完成的20000 checkpoint，formal须匹配该20k本身的smoke。不能另造runner或放宽正式检查。约150可执行行是控制复杂度的目标，必要审计接线可以略超，但交付应解释保留职责和实际行数，不压缩排版凑数。

生成的manifest/evidence按现有metadata继承机制随run保存；说明临时生成物位置与清理方式，避免在eval_result下留下看似正式run的输入缓存目录。先完成CPU交付，GPU授权另给。

## 当前依赖版本与交付

09:59 openpi主开发分支已合入独立review通过的wash与metadata恢复修复，HEAD a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，代码树等价056bcc8。你的openpi尚无活跃GPU任务，请在原登记分支上快进到该HEAD，更新本入口runtime固定SHA；不新建worktree/环境。沿已有dry-run核对d10 full/serial metadata仍进入Context即可，CPU旧路径已有Banach57e9c032独立GO，不重做完整模型测试。bridge继续8ea6078、RMBench继续原base上写本任务增量。Maxwell/Locke冻结运行树保持各自版本。

10:23 Manager接受498cc4c所列公共接口缺口与必要适配范围，但正式审计输入也应使用本任务RMBench/.local/memory_schema_eval下的临时目录，不能写入<checkpoint>/eval_inputs。原因是评测需可读取不允许写入的checkpoint，同一模型也会被多个实验/工作区使用；评测配置归执行run，其已有config_source继承已验证可以保留输入快照。请统一技术/正式临时存放机制，继续通过既有recorder复制到run，保持checkpoint所有文件不变，说明run完成后清理路径；只做这一处小修和相应CPU验证，不扩大runner框架或新造持久缓存。若公共接口确有必须写checkpoint的约束，先给具体代码证据。正式结果仍只在RMBench/eval_result/<group>/<run>。

先提交CPU准备commit并发布简短report，注明task_revision、三库实际SHA/workspace、命令dry-run与metadata检查、GPU待办和预计耗时。Manager验收后分配GPU进行新schema必要smoke或正式模型评测；未分配前不占本机GPU0/1或远端八卡，它们已有任务。超过1小时的正式进程用mam job add登记。

任务自己的smoke和临时文件自行清理，正式产物留共享主repo。正式运行期间冻结所有被调用worktree；结束、处理job并完成交付后由Manager归档环境/分支。

## 12:11 Manager文档修正（本轮仍不占GPU）

CPU实现7378904及空白review95ece0eb已经验收，主库已合入。此次只修改 README_memory_schema.zh-CN.md：
- 新20k训练实际保存在 /mnt/public/xcj/Projects/openpi/checkpoints/<config>/<exp_name>/20000；README目前表格/示例的policy/pi05/checkpoints路径不成立。主RMBench此目录是真实独立目录，只供旧模型；不要通过搬checkpoint或补软链来让错命令成立，修正文档即可。按训练owner最新report列实际路径，full的seed已含0/1/2与put-back的0/1；旧drawer仍用原RMBench checkpoint路径。
- README是操作说明，不需复述CPU review人名/旧版本等待和“未获GPU授权”等瞬时对话。简要说明调用入口和checkpoint自身smoke→formal约束，再给可复制命令。
- 删除 CHECKPOINT=... 以及后续 $CHECKPOINT；具体路径直接写入参数。不用 $PWD 或拼接继承的PYTHONPATH占位来猜工作目录。确有必要的进程环境设置可用具体值放在对应命令前，不建立export变量准备区；技术/正式模板明确指定实际worktree解释器、checkpoint路径与GPU0。
- 保留只读checkpoint、技术50不能替代20k门禁、逐步metadata与清理规则，但避免重复同一说明。暂不改可执行代码、配置或公共框架。
只需核对文字命令与现有CLI/路径、diff-check，不重复CPU模型与GPU检查。提交文档小修并发布report。F0 row1预计约12:50释放GPU0，Manager另通知你开始真实技术smoke及drawer offline；本轮不先启动GPU程序。

12:38资源调整：用户追加BF16导出模型的真实100rollout验证（任务35c9e781-7d2e-49a1-bb4c-25d77b865b3a），本机GPU0在F0 row1完成后优先交给该验证。你的GPU技术smoke与drawer offline顺延到下一张释放的卡，预计F0 row50的GPU1；具体分配由Manager检查后发布。本任务CPU和文档交付均已验收并合入，现阶段继续保留三树，不启动GPU。后续实际命令按分配卡调整，README的GPU0是可复制示例，不代表已经占有该卡。


## MAM 查询更新（2026-09-10）

系统 MAM 已更新：`mam task list` 和 `mam job list` 为带表头的简表，无 --json；完整task信息使用 `mam task status <id>`，实时job结构化详情使用 `mam job status <job-id>`。`mam task show` 仍默认Markdown，保留 --json。`mam task status` 仅显示保存的 job 状态与 checked_at，不刷新进程。按既定频率监控时使用 `mam job list --task e6908de7-4b02-465a-987b-a19eba7a315a` 获取实时进程状态，再结合已有日志检查进度。训练/评测协议、GPU 分配与检查频率不变。

## 15:06 GPU1移交与执行

F0负责人15:01确认GPU1所有自有进程退出、端口19310/19312释放、job已归档。现在授权本任务使用本机GPU1，sim和policy共卡；GPU0仍属于BF16正式100，不占用。复用已验收三库worktree，不创建新环境、不切换正在调用的代码版本。按前述范围依次执行：d10 step50 full/serial各一个technical smoke（各含video/no-video两条），然后旧drawer full/serial各固定5ep offline。实际参数用GPU1和已确认空闲的独立端口，留痕记录真实命令。技术模型效果不作20k模型性能判断；不以技术smoke替代各正式20k匹配smoke。预计超过1小时的程序按MAM登记。发现具体接线bug先报告，禁止绕过schema/gate掩盖问题。结束核对产物与进程、释放GPU1供后续Q2 seed2训练，发布简报。


16:01接口迁移：不要再将job list输出按JSON解析；用task status里的jobs取ID，再逐个job status获取实时结构化结果。既定监控频率不变。新增mam wait jobs/list/stop可按需使用，自动CODEX_THREAD_ID；停止等待不影响实验。
## 16:05 已验收结果文档收尾

Manager接受8eab15f1技术链路与drawer10ep offline交付，GPU1已转交训练。现在在原RMBench worktree的README_memory_schema.zh-CN.md简短记录实际技术PASS的含义、drawer两模型各5ep结果表和真实目录drawer_s2m_v2_regression_5ep_gpu1_20260910，避免读者把旧示例路径当此次实际结果；不把offline MAE写成闭环成功率。保留20k后续命令和每checkpoint自身smoke要求。只改文档，diff-check，不重跑模型。

本任务两份technical_rearrange_*_gpu1_20260910原始smoke已完成技术验收且不能用于正式门禁，可清理；已发布report是技术结论留痕，不另打包全量smoke。正式drawer产物保留。清理自有pycache等临时缓存，不跨清理ad6的step50checkpoint（其owner统一处理）。提交文档并发布report后保留三树，供明日20k评测继续复用。


18:22 MAM精简status已安装：task status 的未归档job摘要位于 jobs.unarchived（无jobs时该键可省略），不是旧jobs数组；job status直接提供status/checked_at/error及unknown时last_known信息，不再嵌套probe或identity。实时进程身份仍由工具内部核对。按新JSON读取；保持既定每小时频率，不因接口变更额外复查训练。


## GPU 调度更新（最新用户指令，替代此前预留安排）

wuwen-1 的现有训练自然结束、完成 checkpoint 保存并释放资源后，整机8张GPU保持空闲，不再启动训练、smoke、offline test或正式评测，直到用户另行允许。明天2026-09-11中午12:00前为其他同学预留GPU的要求改由wuwen-1承担。本机GPU0–7均可按原授权继续训练和评测，启动前核对可用性。本机GPU2–7的原预留限制已取消。不要终止现有训练；若wuwen-1训练预计超出截止时间，及时报告Manager裁决。

## MAM 项目配置迁移完成（2026-09-11）
在/mnt/public/xcj/Projects及其子目录内直接使用mam；已取消--root参数，自动读取项目配置。MAM根目录不变，已发布任务/报告改到project/state-vla，main只用于工具开发。现有task/job/workspace不变；报告仍在原路径编辑，mam task publish正常发布。本轮main已重写历史；后续若开发MAM必须从新的main基线创建worktree，不从旧任务或项目分支合回main。训练与评测业务代码基线不受影响。

## 9月11日04:32 正式评测排期准备（暂不占GPU）
复用保留的三个worktree，读取两个训练owner最新报告，为14个仿真20k模型（12个Q2受控重复+rearrange serial/no-memory基线）列出对应checkpoint、单GPU smoke2/formal100 run名和先后顺序。优先rearrange/put-back per-frame与repeated-endpoint按训练seed成对进入队列，不按中途成绩筛选。每模型先自身smoke（同一run两条rollout，一条video一条无video），核对产物/现有门禁后才能正式100；每run在一张卡串行执行，第50次做正常诊断。产物统一RMBench/eval_result/memory_chunk_20260910/<run>及对应experiments记录。
同时核对wash full/serial新20k的固定5ep offline入口与数据，必须复用已验证的通用memory/S2M机制；读取wash owner已固定的5ep，不另选episode。只准备命令及必要配置，不因脚本名drawer而另写wash专用实现。若接口存在实际缺口，给代码证据和最小修复建议交Manager裁决。
当前本机8卡全在训练，wuwen-1结束后全部停用。现阶段只做CPU/元数据/命令准备，不加载GPU模型、不重新运行已验收的technical smoke或旧drawer回归。预计07:20以后本机4–7先释放供仿真；wash GPU2/3预计07:27后优先完成其checkpoint恢复及5ep offline，再转仿真，具体授权由Manager确认。报告清楚“已准备”和“已运行”的边界；可在现有实验说明补紧凑队列，不新增调度框架。完成准备后报告即可，等待Manager分配卡。

## 9月11日06:53 正式仿真执行安排
本机GPU4–7由训练owner e7e5ac54确认各自训练保存/进程退出并发布释放后，授权本任务依次接用已释放卡；启动前再核对显存，不能抢占尚未结束的卡。GPU0/1仍训练，GPU2/3留给wash offline，wuwen-1停用。本任务负责14个既定模型的各自smoke2与正式100，沿上面已验收入口及固定队列，不修改公共backend/controller/scheduler。先在GPU4/6可用后分别运行rearrange full t+1/t+30 seed0，GPU5/7释放后运行put-back两变体seed0；后续按既定seed配对队列填充。每卡一次一个run，每个run100条串行，sim与policy同卡。为每个并行run使用独立端口、输出路径和必要的进程cache。
必须先确认该20k保存和训练owner CPU门禁完成；实际GPU恢复由本模型匹配smoke覆盖，不另重复整套技术smoke。每个checkpoint的smoke是同一run的2条rollout（视频开/关各一次），核对结果文件、视频可读、metadata及进程退出，再从已提交干净版本进入正式100。若入口或算法有问题，报告首因及最小修复建议，不用变更参数绕过门禁。
正式运行预计超1小时均mam job add，任务内多个job分别登记。50条时对照真正可比的旧实验，偏差超过10个百分点开始诊断；新训练未有可比基准时明确说明，不能强行引用不同配置成功率。保留正常失败与全部100条结果，不能按中途表现重新抽样。完成后更新本组实验说明，按协议清理自己的smoke/临时产物，保留正式结果及smoke门禁必要摘要；进程退出核验并archive job。保持active turn，使用mam wait jobs --task等待并结合日志做50条中检。报告阶段结果，不把CPU准备或smoke替代正式实验。

## 07:52 资源与实验台账补充
wash训练owner已验收并释放GPU2/3、归档任务。正式wash offline只使用GPU2串行两模型，因此GPU3现授权本任务接用（先核对实际显存/端口），按既定队列启动rearrange t+1 seed1自身smoke→formal；与其配对t+30 seed1保留优先队列，下一张释放卡执行，不按成绩挑选。GPU0/1仍训练，本任务不使用GPU2。4–7原分配不变，wuwen-1停用。
用户今天暂停统一架构重构，所有实验继续冻结源码。后续文档结果应更新本组EXPERIMENT_LEDGER.zh-CN.md对应模型行：已合入RMBench主xcj-dev（bc43568及整合commit），包含研究动机/假设和固定模型路径。勿在正在被formal使用的源码树中merge/修改文档；先完成这轮运行，后续安全整合文档并更新结果/实际eval链接，保持快照时间准确。重点继续50条诊断与完整100结果，不把training loss或smoke当正式成绩。

## 集群C迁移排期与对照交接
用户要求C评估环境验收通过后，后续新eval优先放C；当前已启动本机run继续收尾，不中途移动。环境task5773b6ec负责人Banach正在三库环境/三机smoke/一个100对照验收，暂不扩MAM。请交一个已完整收尾、可直接复现的本机100基线，给成功数、真实失败类型是否影响可比、三库冻结commit、ckpt及数据/seed/命令和必要资源清单；Manager将裁定C正式对照。不要为迁移修改active worktree。C未准入前不自行在C启动正式run；准入后会为后续任务发布C根README与手工workspace/TASK-ID要求。
同时本轮已完成的100run及时更新稳定实验记录，按原协议记录50检查/最终成功率与模型seed，不仅留在MAM报告。给Manager当前已完成结果、还在运行/排队清单和异常裁定需求，避免准备迁移时漏掉结果收尾。

## 9月11日第二批训练并行与台账
Manager已安排7ae41311训练rearrange serial/no-memory各seed1/2（GPU2–5）；695bc51f准备put-back serial/no-memory seed0（GPU6/7，配置门禁后正式）。补齐既定B组，不依赖C或Q2结果；不要占本机GPU或wuwen-1。请复用/安全创建本task文档worktree更新EXPERIMENT_LEDGER，区分已派发/准备/实际训练中，只有读到job及updates才能写运行中，后续正式目录由owner提供后链接。加入各项目的（B组训练seed重复及put-back同骨干能力基线）、预期检验而非预设成功率、checkpoint/eval待办。引用两个新task报告核对，交文档commit由Manager集成；不改冻结eval代码树。4个旧abort继续保留证据，8未启动仍待C验收，2完整结果保留。

## Manager待办清理与恢复责任
恢复后续评测准备。C任务2a879870已三机smoke通过，renderer修复17b55bf/创建优化9c71a3e已独立review；正式100正在运行，首50为34/50对本机35/50，尚未完成5pp验收。先在现有任务整理剩余14模型清单、已完成/不完整/待跑状态和准确模型目录，确定迁移C的最小批次，不重复跑成功项。C最终验收之前不启动新GPU评估，准备完给Manager阶段report；不要为了active伪造job。原先get_obs修复已有378da0ac/ae463958后续报告，应先核对已修状态，不重开已解决问题。

## C准入期间接续实际模型准备
Manager接受14行队列状态(2完整保留、12待评)。现在提前传输12个待评模型到集群C，属于既定eval准备，不需等待最终100准入。先读C:/mnt/public/xcj/Projects/state-vla/README.md及2a879870已用checkpoint传输记录，沿既有稳定openpi/checkpoints布局，复用已有模型不重传，不覆盖活跃模型/环境。源只读20000 params/assets/metadata，使用本集群wuwen-nx-aic与C wuwen-4090-aic高速路径；最多两条并发，错开至少60s。先核实两侧磁盘/源目标对应，不复制训练数据或cache。真实rsync进程在本机登记mam job，完成后核对文件/metadata完整性和传输结果，失败不写ready。开始第一批后使用mam wait实际保持active（不能仅后台wait后final）；不逐分钟模型轮询。优先put_back_full_t_plus_30_s0与rearrange_full_t_plus_30_s0，后续按表序推进其余10个。此阶段不跑新GPU评估。你提交13192bb文档需先由Manager集成后再清理docs临时树；原三库树暂留供队列准备。

## 集群C最终准入，放行既定12项评估
Manager核对2a879870最终证据：C100/100固定seed、70成功，本机69，19checks通过，255文件回传hash一致。现放行已整理12待评项，不重复2完整项。按C README在C workspace/本TASK-ID建自有三库worktree/环境，运行版本沿已验收RMBench17b55bf、bridge8ea6078、openpia869498，固定GPU映射和ICD；如某variant缺能力/入口需要修复先交Manager，不随意换算法。每模型完成自身2rollout有/无video smoke+产物检查，再固定源码同GPU串行100。模型到达即启动，不必等12个全传完；首批优先已指定两s0，先一机一run(C1/2/3实际空卡任选)，首批健康后可每机最多两run但每GPU仅一run，端口/cache独立，先报告实际资源不抢他人。每run前50比较可比历史/查基础设施，完整结果独立exp-group/run记录，不拼旧partial。真实job登记、本机MAM运行，等待使用mam wait。后续回传到本机RMBench同exp-group，保留旧两完整baseline。不要依赖2a879870或5773远端临时worktree/venv，它们将收尾清理；需shared stable cache/assets/model可继续用。你13192bb文档已合本机f58ac38，文档树可自行清理。

## 后续评估与台账、首次infer超时裁定
继续负责现有已完成模型队列和新增完成训练的接入。用户明确：已跑完训练要安排eval，eval后整理实验台账。核对695bc51f与7ae41311的最新report，只有最终20k产物完整且训练成功退出后接入；未完成的不要当作可评。现有有效100结果不重复。

针对已报告两个smoke在首次infer 30秒超时：授权在自己独立bridge worktree调查并做最小基础设施修复。先用失败日志/单模型串行有界诊断验证是否JAX首次编译超过预算，不预设首因。若证实首次编译，可只为首次infer提供合理有界预算或明确warmup；后续infer预算保持，不能修改算法/seed/horizon/memory或把超时当成功。代码需CPU有意义验证并提交，先报告commit与证据供Manager独立review，准入后再同模型smoke2→正式100。不在失败原因未明时重复并发smoke。传输继续按既定两路上限与间隔。

实验台账统一RMBench/experiments/<exp-group>，结果RMBench/eval_result/<exp-group>/<run>。逐run记录研究问题、设计变量/控制变量、预期结论、train commit/config/schema/seed、训练及checkpoint路径、eval commit/config/路径、实际成功率和失败分类、与基线差异及限制。现在先建立完整待评清单与状态，正式结果到达后更新，不等全部完成才记账。前50与已有可比结果差超过10个百分点先排查；固定100同GPU串行，单个smoke含2rollout(1video/1无video)，产物检查通过才formal。实验代码与台账交付提交，清理短smoke等临时产物但保留必要故障证据。

不用无变化等待进度写report或commentary；mam wait挂起时不做几十秒一次轮询。完成实际可执行工作后再等待事件。

Source report:

## C 迁移评测准备（2026-09-12 03:02 CST）

文档提交 `13192bb5ee4be7c18fe149996a17b18772826811`，在既有安全 docs tree
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`
的 `codex/e6908de7-b-training-docs` 分支，仅更新
`experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md`。它将过期的“14项均未运行”表替换为准确的 C 候选清单：2项完整100保留不重跑、4项历史不完整须从seed100000全新100、6项未GPU启动、2项能力基线待跑；最终准入后的最小批次为12项，14个20000 checkpoint链接均实读存在。

已读取 C 任务 `2a879870-8dda-4613-a684-0ad48a5e86be` 最新发布报告及两个实时 job status。三机 candidate smoke 已通过；put-back full t+1 seed0 的 C 严格100在本次核对仍为running，已记录前50为34/50、本机为35/50，尚未完成100或5pp最终验收。因此未启动任何新GPU评测、未登记本任务job，也没有对外部C job调用wait；本任务没有可等待的活跃job，按要求发布准备阶段报告。

已核对归档任务 `378da0ac` 与独立复查 `ae463958`：状态/diagnostic边界修复已归档，历史partial证据继续保留；没有重开RPC诊断、改变协议或把旧partial拼入新分母。迁移条目要求C owner使用独立结果leaf、每checkpoint自身video/no-video smoke2→formal100，不覆盖本机既有正式目录；C最终准入后再由Manager排期及指定运行树。

验证：`git diff --check`通过，C候选表恰14行、14个checkpoint路径存在；docs tree及原RMBench、robot-bridge、openpi冻结运行树均干净。未占GPU、未停止现场PM服务、未修改机器人或冻结eval树。待Manager集成文档commit，并等待C最终验收后恢复实际评测排期。

## put-back 状态增量（2026-09-11 16:40 CST）

文档commit `81f6aafa37e44e99bd0cb5de68066ccb508f8f86`，复用原docs树。按695bc51f最新发布report及Manager放行更新两行：no-memory GPU0正式step100，补真实输出/日志链接；serial自身gate通过、已放行，实际启动证据待owner，正式目录仍标计划。仅同步相邻快照及总数，保留四路repeat原快照。diff-check、实际链接检查通过，提交后干净；未占GPU、未改冻结eval树。

## 第二批 B 实际状态更新（2026-09-11）

文档交付 `25d57eb4aef881347ed881d0bb56408efce2be33`，复用原 `RMBench-ledger` / `codex/e6908de7-b-training-docs`，仅改实验台账。依据7ae41311已发布15:46:48小时巡检，四项repeat更新为训练中，记录有效进度、快照剩余ETA、共享输出目录及冻结训练SHA；依据695bc51f已发布15:47报告，no-memory记为CPU review/GPU50/恢复通过且已放行、等空卡未正式启动，serial记为配置review通过、待自身GPU门禁。两个put-back正式目录明确标计划，50step独立链接。

已删除过期“无published report”解释及重复MAM细节。diff-check和新增实际链接检查通过，docs tree提交后干净；未占GPU、未修改冻结eval三树或已有run，原2完整/4失败/8待启动边界保留。待Manager集成。

## 2026-09-11 第二批 B 文档交付

文档 commit：`f6dbff8a243d0ac67ff7c7a4cade99845f524272`，基于主 RMBench `d6a438857a04bb5778fa8d0d24344d4c6dbc81ed`，待 Manager 集成。
安全 docs tree：`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`，分支 `codex/e6908de7-b-training-docs`。仅修改 `experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`，没有重建环境。

14:29 CST 已核对 7ae41311 和 695bc51f 的最新发布 task、report 接口和 task status：两个 report 均未发布，只有草稿；无 job 摘要或已发布 updates。因此四项 rearrange serial/no-memory seed1/2 写“已派发、未确认启动”，两项 put-back seed0 写“配置准备、正式训练待门禁及 Manager 放行”。没有把 task working 当作训练中，没有读取草稿推断进度。

新增六行写明 B 组动机、预期检验、checkpoint/CPU交接及自身smoke2→formal100待办，并引用两个owner报告核对入口和发布task版本。未猜put-back注册名或真实产物目录，待owner发布后补链接。六项与首批14/14准备完成统计分开；原2完整结果、4失败证据、8未启动及公共RPC文档校正保留。

验证：diff-check通过；新增两处report路径存在（不视为已发布证据）；提交仅1个文档，docs tree干净。原三树均干净且冻结SHA仍为RMBench `3e69b1e665a8eac0104d261b233f1b3339007e00`、bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。未占GPU、未启动或重试模型；后续eval等待C准入和公共故障裁定。保留docs tree供集成，原运行三树继续保留。

## 14/14 CPU准备验收后的清理

Manager已验收14/14 CPU准备并将5dab24fd ff合入主RMBench。已核对主库包含该提交、文档树干净，删除额外RMBench-ledger worktree及codex/e6908de7-seed2-docs分支。原三库运行树和冻结SHA均保留、干净，四失败证据原位保留。

已核对自有schema Warp缓存目录不存在，实验入口目录无残留__pycache__。worktree的warp-cache入口实际指向共享主库，剩余F0/旧smoke缓存属于其它实验，未跨清理。保留C迁移所需14组CPU审计/dry-run及inputs材料，它们是可复核准备输入，不作为GPU运行结果或新持久缓存。此次未启动GPU，task无活跃job；后续仍等待C准入与公共RPC裁定，不重试失败项。上文新文档worktree/分支路径现仅作交付历史。

---

## 2026-09-11 最后两项seed2 CPU准备完成：14/14就绪

已读取稳定训练manifest `/mnt/public/xcj/Projects/openpi/checkpoints/memory20k_e7e5ac54_manifest.json`（14项），并核对最后put-back seed2两项closure-audit.json/closure-evidence.md与manifest哈希一致。owner已完成参数读回/BF16/finite/shape CPU门禁，本task未重复恢复完整模型。

原三库固定运行树复用，只使用现有run_memory_schema_eval.py，显式CUDA_VISIBLE_DEVICES为空、JAX_PLATFORMS=cpu、PYTHONDONTWRITEBYTECODE=1。两模型各执行prepare-audit、smoke dry-run、formal dry-run，共6步exit0；checkpoint metadata进入MemoryContext，字段phase/origin_mat、H50/K30、demo_clean_state来源及各自t+1/t+30 schema通过。checkpoint文件集合/大小/mtime前后未变。

| variant / train seed | 稳定checkpoint | 预定run（未GPU启动） |
| --- | --- | --- |
| put_back_full_t_plus_1 / 2 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s2/20000 | put_back_full_t_plus_1_s2_20k_smoke2 → put_back_full_t_plus_1_s2_20k_100ep |
| put_back_full_t_plus_30 / 2 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s2/20000 | put_back_full_t_plus_30_s2_20k_smoke2 → put_back_full_t_plus_30_s2_20k_100ep |

日志在原RMBench `.local/memory_schema_eval/cpu_20k_20260911/put_back_full_t_plus_{1,30}_s2_20k_{audit,smoke_dry,formal_dry}.log`；汇总含实际命令/cwd对应位置与只读/隔离验证：同目录 `put_back_seed2_preparation.json`。两项临时audit/manifest仍位于既有inputs/<variant>--<checkpoint路径hash>，后续随config_source复制到正式run。未创建任何上述eval结果目录、未启动GPU/服务或MAM job；模板GPU5/7及端口仅用于dry-run，后续按C准入实际资源重新配置并完成自身smoke，不能作为GPU分配凭据。

稳定实验台账提交 **5dab24fdb1a1fcab742fc47dcb6a5fcd1a2339db**（base f2ec2cf，分支codex/e6908de7-seed2-docs）。仅文档临时worktree `/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`，未安装环境；只改EXPERIMENT_LEDGER.zh-CN.md的训练/CPU状态、最后两项20000链接与manifest证据，明确14项/12项Q2口径。diff-check、结果路径隔离和14组CPU日志检查通过，提交与原三库均干净；原运行SHA和四失败证据不变。该新文档提交尚待Manager合入，旧已合并临时分支的清理事实仍成立。

当前仍为2完整100、4基础设施失败、8项未GPU启动、0项运行；训练/CPU准备升级为14/14，不等同于GPU评测完成。继续等待C环境准入和Aquinas/task378da0ac公共RPC修复裁定，不自行重试失败或启动GPU。

---

## 已验收后的临时文档树清理

Manager已验收两份正式100及台账f2ec2cf，并ff主RMBench。已核对主xcj-dev包含该提交、额外文档树干净，删除本task的RMBench-ledger临时worktree及codex/e6908de7-ledger分支。原RMBench/robot-bridge/openpi三个运行树及冻结SHA不变，四个失败run及各自smoke/诊断证据均保留。上文额外文档worktree路径仅作交付历史，不再存在。

C的69/100对照基线已获批准；RPC问题交Aquinas/task378da0ac。后续eval等待C准入与公共故障修复裁定，不自行重试四失败或接续GPU任务。

# 2026-09-11 11:38 本机正式评测阶段收尾

14项仿真队列当前：**2份完整100已验收、4份基础设施失败已归档、8项尚未启动、0项运行**。本task无活跃GPU进程；GPU3/4/5/6/7各自退出时已核对显存释放与端口无监听。没有重复启动已有run，也未改变失败项timeout/seed/参数。

## 已完成正式结果

| 模型 / train seed | 前50检查 | 正式100 | 失败边界 | 正式目录 |
| --- | --- | --- | --- | --- |
| put-back full t+1 / seed0 | 35/50，检查通过 | **69/100（69%）** | 31正常任务失败；0 runtime_error | put_back_full_t_plus_1_s0_20k_100ep |
| rearrange full t+30 / seed1 | 45/50，检查通过 | **92/100（92%）** | 8正常任务失败；0 runtime_error | rearrange_full_t_plus_30_s1_20k_100ep |

真实结果根：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/`。

两项均按episode0–99/seed100000–100099原顺序完整执行；各有100份episode JSON、100条视频检查，前5集视频完整解码、其余无视频。config_source里的audit/manifest逐字节继承一致，100个scheduler exit0，policy/robot正常shutdown -15，全部登记子进程退出。`midpoint_review.json`保存逐query最终trace/反馈行检查；`final_review.json`保存最终验收与清理事实；`launch.json`、`command.txt`、`config.yaml`和checkpoint_metadata保存实际命令与来源。无匹配旧20k训练/config基准，不强行与旧F0算10pp偏差；两份完成结果也不是同任务/seed配对，不能推导Q2目标差异。

put-back正常失败：button_not_pressed_after_center18、button_press_insufficient13；五视频帧数500/500/359/444/355。GPU5收尾1MiB/0%，19450/19452无监听，job a58e56cc-2281-4d88-89af-53bdee13a768已归档。
rearrange正常失败：button_not_pressed3、button_press_insufficient4、block2_not_moved_to_middle1；五视频392/406/411/402/385帧。GPU7收尾1MiB/0%，19470/19472无监听，job48930d29-9e3c-430c-8f8a-e93671f08333已归档。

已清理这两份完成run对应的自有smoke及GPU5/7 Warp缓存；正式目录保留smoke_verification摘要与全部正式结果。其它失败smoke/原始证据保留用于公共故障诊断。CPU准备输入/dry-run仍供剩余队列复用，未写checkpoint；不新增持久缓存/API。

## 稳定实验台账提交

仅文档分支 `codex/e6908de7-ledger`，从主库6139577建立未安装环境的临时worktree：
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`。

- `66f0a255a8c7878816ae1db1a42985f8990b3e04`：登记69/100完整基线、四失败边界、各模型真实状态及C对照入口。
- `f2ec2cfe14d4a721a12d19ae9971af5c0e1777ff`：补rearrange seed1正式92/100与全部运行收尾。

只改 `experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`。新增结果链接与CPU准备证据已核对，diff-check通过，文档树干净；可由Manager将以上两commit合入主库。没有将文档合入运行树改变source身份。原三个任务环境保留复用。

## 集群C对照基线交接

提名已收尾put-back full t+1训练seed0，**69/100**；31条均为正常任务失败，不因基础设施错误缺失episode。C准入的≤5pp对应64–74/100，须新环境自身smoke后完整100，不能复用已清理的本机smoke。

运行冻结SHA（不是上述文档提交）：
- RMBench `3e69b1e665a8eac0104d261b233f1b3339007e00`
- robot-bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`
- openpi `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`

Checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000`，完整params/assets/metadata只读使用。
训练原始数据：`/mnt/public/xcj/Projects/RMBench/data/put_back_block/demo_clean_state`；转换集：`/mnt/public/xcj/cache/huggingface/lerobot/put_back_block_demo_clean_state_shared_memory`。
实际评测为在线仿真put_back_block/demo_clean_eval，eval seed0、100000–100099，H50/K30、full last_executed、500步上限、instruction_generation_num100、前5集视频。

原命令/cwd在该正式run的launch.json，展开服务命令在command.txt。沿现有run_memory_schema_eval.py：variant put_back_full_t_plus_1，指定上述checkpoint、独立run名和分配GPU，prepare-audit→自身smoke2（video/no-video各1集）→引用自身smoke的formal100。
资源：单卡串行、sim/policy同卡；原A100、XLA_PYTHON_CLIENT_MEM_FRACTION=0.4；两独立端口、可写结果/临时Warp缓存、三库环境、RMBench共享assets及机器人/渲染资源、PaliGemma tokenizer缓存。4090显存配置需由其自身smoke确认，不能预设0.4足够。无需重训或复制全部训练原始数据用于在线rollout，但须保留checkpoint完整溯源及所需仿真资源。

## 四个基础设施失败与裁定需求

| run（均后缀_20k_100ep） | 正常完成条数 | 首次异常episode/seed | 结束CST | job（已归档） |
| --- | ---: | --- | --- | --- |
| put_back_full_t_plus_30_s0 | 16 | 16 / 100016 | 08:23:34 | 1803ad5f-b94a-4b64-bdc1-2c7f8ed9339c |
| rearrange_full_t_plus_1_s1 | 17 | 17 / 100017 | 08:45:35 | 7a618537-3350-45cc-bb45-d3d8fe62f722 |
| rearrange_full_t_plus_30_s0 | 32 | 32 / 100032 | 08:45:37 | 1e72397f-0602-4018-bc7c-4e112ad7501a |
| rearrange_full_t_plus_1_s0 | 67 | 67 / 100067 | 09:50:04 | af7dd7c9-682c-4a78-9e6e-946cbf47672f |

各run另含一条异常记录，不是完整100，未用不完整分母给正式分数。均在某集第一次get_obs、logical_step0遇到30秒transport超时；前三项runner报robot_status_transport_error，最后项报scheduler_exited_before_terminal，scheduler底层同为TimeoutError。原trace/metadata/视频/全部记录和smoke保留，各目录failure_review.json记录退出及GPU释放。GPU3与GPU6故障仅差2秒，跨模型/seed/卡，不能归因于某一target目标；慢首帧与底层卡死的根因尚未证实。

公共代码证据（bridge8ea）：benchmark/runner.py:418外层状态RPC timeout=30、430–434失败即终止；scheduler/base.py:120–121使用WebSocketClient默认30秒（transport/websocket.py:113）；robot/controllers/rmbench_simulation.py:129–131同一锁串行worker RPC，本次内部rpc_timeout=600。首次get_obs可使状态查询等待同一锁，存在内外有界预算不匹配的可能，但不是已证实根因。

最小建议：公共owner先确认首次get_obs慢/阻塞点，若证实预算问题，在既有RPC边界协调有界timeout；不改memory/动作协议、不全局无界等待、不另建runner。失败项如何重试/形成完整100由Manager裁定。本task没有修改公共源码或参数绕过门禁。此前一次进度快照只看episode_status漏报GPU3 runtime错误，已在efc7b696报告更正；后续始终同时读取runtime_error、summary与MAM退出状态。

## 后续队列与暂停边界

8项尚未GPU启动：put-back seed1 t+1/t+30、rearrange seed2 t+1/t+30、put-back seed2 t+1/t+30、rearrange serial_lag30 seed0/no_memory seed0。14项均已完成20k保存/owner CPU交接及本入口CPU audit、smoke dry、formal dry；最后两项增量见本文最新CPU交付。

已读集群C迁移新条款：C未准入前不自行启动C正式run，已启动本机run均原位收尾；后续新eval在C准入与根README/workspace要求发布后优先排C。当前无可等待的活跃job；等待C准入及四失败的公共处置/重试裁定，未自行接续空卡新任务。任务整体14模型队列尚未完成，不标记全任务完成。

## C checkpoint 传输进度（2026-09-12 03:39 CST）

按最新条款仅传 12 个待评 `20000` checkpoint，不传训练数据、cache、环境或评测结果，未启动任何 GPU 评测。C 目标统一为 `/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/<config>/<exp>/20000`；每项先确认源端 `params/assets/metadata/_CHECKPOINT_METADATA` 和 C 端目标不存在，实际传输在 `wuwen-nx-aic → wuwen-4090-aic` 上以 `rsync -a --partial --append-verify --bwlimit=10m` 执行，完成后以 `rsync -aicn --delete --omit-dir-times` 复核。

已完成并归档 3 项，均在 C 端得到零差异校验、相同文件清单 hash 和 `_CHECKPOINT_METADATA` SHA-256：

- `put_back_full_t_plus_30 / s0`（job `07f340e8-19a8-4992-ae11-e91bb484c435`）；
- `rearrange_full_t_plus_30 / s0`（job `5de7d82e-cc15-4f11-a2e3-9b99a628c4c7`）；
- `rearrange_full_t_plus_1 / s0`（job `c72d46f9-9255-4044-b83d-b1df8fb31b0f`）。

传输日志及只用于本轮运行的窄 worker 位于 `/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c_checkpoint_transfer/`；待全部传输收尾、日志保留后清理 worker，不在 checkpoint 或冻结评测树写入任何文件。

当前两条真实 rsync 均已登记且未超过两路并发：`rearrange_full_t_plus_1 / s1`（job `ae1eecd7-380c-4b22-b70e-2fb0af53c1e8`）和 `put_back_full_t_plus_1 / s1`（job `0964e0d6-999c-4ca6-9cda-bf63792e9072`）。它们的启动相隔远超过 60 秒；我正使用 `mam wait` 接收停止事件，停止并不自动视为成功，仍须逐项 checksum/metadata 收尾和归档。C 的最终 GPU 准入尚未改变，本任务不会在 C 或本机启动新的 GPU eval。

## C 最终准入后的首批执行（2026-09-12 03:59 CST）

Manager 已验收 C 对照为 70/100，对本机完整基线 69/100 相差 1pp，放行本任务 12 项待评模型逐项 C smoke2→formal100；2 份既有完整本机结果仍不重跑。按 C 操作手册，我没有引用 `2a879870` 或 `5773b6ec` 的临时 worktree/venv，而是在 C1 创建本任务自己的共享三库 worktree：`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval/`。创建日志、失败 attempt 1（C1 缺少 `/usr/bin/time`，安装器尚未被调用）和 attempt 2 的完整 stdout/stderr、耗时、git status、非跟随软链统计均在其 `records/`；attempt 2 通过稳定 `.local/create_worktree.sh` 完成，SHA 为 RMBench `17b55bff1c79a0c5a836d1da089765934cb3a5b0`、bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`、openpi `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。

首批使用已先行抵达并已 checksum 验收的 s0：put-back full t+30 和 rearrange full t+30。两个 checkpoint 的 C worktree `prepare-audit` 都通过，metadata 经 `load_train_config → _runtime_metadata → MemoryContext` 进入实际 scheduler 配置，字段、H50/K30、`demo_clean_state` 和 `last_executed` feedback 均已留在 records。dry-run 生成的实际 smoke/formal 命令使用固定 `memory_chunk_20260910` experiment group（冻结入口 config 所定）和新的 C 专属 leaf，不会覆盖本机 baseline：

- C3 GPU0：`c_put_back_full_t_plus_30_s0_20k_smoke2_20260912` → `c_put_back_full_t_plus_30_s0_20k_100ep_seed0_20260912`；端口 19400/19402；
- C3 GPU1：`c_rearrange_full_t_plus_30_s0_20k_smoke2_20260912` → `c_rearrange_full_t_plus_30_s0_20k_100ep_seed0_20260912`；端口 19410/19412。

03:59 CST 的实际 C3 preflight 已保存：GPU0/1 都是 1 MiB/0%、无 compute app、上述四端口无监听，两个结果 leaf 均不存在；NVIDIA EGL ICD 固定为 `/usr/share/glvnd/egl_vendor.d/10_nvidia.json`（SHA-256 `9e6f14af…b2ddaf76`）。每项只在 matching video/no-video smoke2 成功、产物/退出/三库 clean 核对后登记并启动同 GPU formal100；第50条按可比历史和基础设施状态留快照。当前传输已完成 5/12、两条 s2 rsync 正在登记运行；C eval 放行不等于传输完成，模型到达后按队列接续。

## C 首批 smoke 基础设施超时（2026-09-12 04:13 CST）

首批两项已抵达的 s0 都完成本任务 C worktree 的 `prepare-audit` 与命令 dry-run，但真实 smoke2 均在 episode0 / seed100000 的第一次 policy `infer` 前后停止，未产生可用 smoke 门禁，**没有启动任何 formal100，也没有重试或改参数**：

- put-back full t+30 s0，C3 GPU0，job `e4b77207-6da7-4aa2-9cd0-6da61d273254`，leaf `c_put_back_full_t_plus_30_s0_20k_smoke2_20260912`；
- rearrange full t+30 s0，C3 GPU1，job `b7eedf3b-936c-483a-99e8-62c0fcf33487`，leaf `c_rearrange_full_t_plus_30_s0_20k_smoke2_20260912`。

两条证据相同：policy server 已从各自只读20k checkpoint恢复 params、norm stats和新schema metadata，scheduler 已连通 robot/policy；随后 `processes/002-scheduler.stdout.log` 在 `WebSocketClient.call()` 收到 `TimeoutError: timed out in 30.0s`，runner 将 policy/robot 以 `runner_shutdown` / `-15` 收尾。policy 日志没有自身 traceback，故目前只能确定“首次 infer 在30秒预算内未返回”，不能把冷启动编译、服务阻塞或模型行为中的任一项当作已证实首因；`_result.txt` 仅记录 `scheduler_exited_before_terminal`，不能算作0分结果。

公共边界证据在本任务冻结 bridge `8ea6078`：`robot_bridge/benchmark/runner.py:418` 以 `timeout=30.0` 构造 policy client，`robot_bridge/transport/websocket.py:149-167` 将其作为单次回包预算。请 Manager/公共 owner 裁定该既有 runner 是否需要一个有界、可审计的首次 infer 预热或 timeout 修复；本 task 不自行改 bridge、算法、checkpoint、seed 或绕过 matching-smoke gate。两个 failure leaf、worker/scheduler/policy日志、processes.jsonl 和 C3 资源快照均保留。04:13 CST 复核 C3 GPU0/1 各1 MiB/0%、无compute app、19400/19402/19410/19412无监听，三库 clean。

checkpoint 传输继续，不占 C GPU：现有8/12日志已有 `verified_at` 与零差异校验；刚收尾的 rearrange full t+30 s2（job `a6138b49-067b-488f-906a-4a46631bee61`）另行实读确认 `_CHECKPOINT_METADATA` SHA-256 两端均为 `5ca58395751d2ca07bdfd66f91dbbbb151fdc8a8393717bc2b520cac1693d73e`。put-back full t+1 s2（job `de532b30-cad1-4ff4-95d6-ef0f086d716f`）与 t+30 s2（job `c00832c4-5292-46b9-8de0-be4e501079c8`）是仅有两条活跃 rsync；完成后仍须逐项复核再归档。其余 C GPU eval 等该基础设施裁定，不因模型已到达而并发启动。

## 2026-09-12 C 首次 infer 诊断与最小修复（待独立 review）

保留的 C smoke leaf `c_put_back_full_t_plus_30_s0_20k_smoke2_20260912` 和
`c_rearrange_full_t_plus_30_s0_20k_smoke2_20260912` 都在 checkpoint/norm/schema metadata
恢复、robot/policy 连接成功后，于首个 scheduler `infer` 的既有 30 秒 WebSocket receive
预算退出；policy server 没有 traceback，未启动任何 formal100。真正的执行预算来自
`robot_bridge/scheduler/base.py` 的 policy client `call`，`runner.py:418` 只是 service/metadata
探测，不是这次失败的首因。

单一、有界、串行的 `JAX_LOG_COMPILES=1` 诊断使用同一 put-back checkpoint 和默认 30 秒预算，
从 `04:38:01` 到 `04:42:37` exit 0、2/2 成功；policy 首个 `jit(fun)` XLA compilation 记录为
`27.232250690s`。它与两份失败 leaf 的 30.0 秒 traceback 共同表明冷启动首次 infer 的编译窗口
已贴近预算，原来的并发冷启动会越界。完整证据在 C 自有 worktree
`c-eval/records/first_infer_diagnosis_20260912.md`，两份原始 failure leaf 保留且不计入成绩。

基于此证据，在 C 自有 bridge worktree 提交
`f9626636c4776d8eb15f9c556775cb2d12c000e5`（`Allow a bounded cold-start policy inference budget`）：
新增正且有限的 `policy_first_infer_timeout`，默认仍为既有 30 秒；只有显式配置时才把预算给一个
scheduler process 的首个 infer，之后调用保持 client 默认 30 秒。它只经
`OpenPiSimulationScheduler` 暴露，没有改算法、seed、horizon、checkpoint 或 memory schema。
CPU 验证在 C 闭包中通过：`tests/scheduler` + `tests/transport/test_websocket.py` 为
**101 passed, 1 skipped**。该 commit 现**待独立 review**；未更新 runtime pin 或 scheduler config，
review 前不重启这两项 smoke，也不启动其他 C smoke/formal。

12 个原始待评 20k checkpoint 的传输现已全部完成：每条
`c_checkpoint_transfer/*.log` 均有 `verified_at`，且使用 `rsync -aicn --delete --omit-dir-times`
零差异校验；worker 仍保留以供审计，日志不清理。新增训练仍不能接入：695bc51f 的 6 条 put-back
训练在其 `02:51` 已发布快照中均 running、无 `20000`；7ae41311 的 4 条 rearrange 训练在其
`04:29` 发布快照中均 running、无 `20000`。论文台账的 C 已评/12项待评/10项训练中清单正在安全
RMBench docs tree 更新；没有把训练中的路径写成 eval-ready。

## 2026-09-12 C 队列与论文台账提交

安全 docs worktree 从当前 RMBench `xcj-dev` `a7e94204715cccddf82674293b8b6fa0c51e9851`
建立分支 `task/e6908de7-c-eval-ledger-20260912`，提交
`564024207898fef1d5cabee48550a8aebf233529`，仅更新
`experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`。它登记了：

- 两份仅有的完整结果（put-back full t+1/s0 `69/100`，rearrange full t+30/s1 `92/100`）及其
  train/eval commit、failure 分类与不可比较边界；
- 12 个已传 C 的 `d10cc01` checkpoint 的精确相对路径、schema/seed、传输验收状态；两个已有
  C smoke leaf 明确为 `scheduler_first_infer_timeout` 基础设施失败、无成绩且无 formal；
- 695bc51f 的 6 条 put-back 与 7ae41311 的 4 条 rearrange B 组训练的 config/schema/seed、
  train commit 与预期输出路径，均标为训练中不可评，不预设结果或建立传输项；
- 固定 smoke2→formal100、100条分母、50条检查和等待独立 review 的边界。

文档 diff-check 通过；C 端实读 12/12 checkpoint 的 `_CHECKPOINT_METADATA`、`params`、`assets`、
`metadata` 均存在；本机实读新增 B 组预期的十个 `20000` 目录均不存在，与 owner 已发布快照一致。
未修改 C 冻结 eval tree、未启动 GPU、未停止服务或机器人。该 docs commit 待 Manager 集成；bridge
`f962663` 仍待独立 review，review 通过前队列保持停止而非重试。


## 本次实际交付（覆盖自动附带的旧运行commit）
源report最后两节实际交付：bridge f9626636c4776d8eb15f9c556775cb2d12c000e5，当前在C:/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval/robot-bridge；RMBench台账564024207898fef1d5cabee48550a8aebf233529在本机源任务docs worktree，主repo对象应可直接解析。
独立review重点：首次policy infer预算为可配置正有限数、默认不改，只对首个真实infer生效，后续30s及异常恢复语义正确；不让metadata探测吃掉首个预算，不改policy动作或memory、不掩盖超时。先读报告/代码，检查27.23s串行编译证据是否足以支持有界首次预算，不能宣称并发根因已严格证实。验证相关scheduler/transport测试及新行为，给出正式smoke准入和建议预算（上限合理且非无限）。
在本机独立worktree做代码review/CPU验证；如commit不在本机，可经SSH只读导出git bundle到本任务workspace导入，保留精确commit。不要在C编辑代码或跑GPU，不停止服务。读各AGENTS和bridge conventions。台账抽核模型路径、状态、成功率及不可比较边界。发布简报后结束turn，明确通过或实质阻塞。
