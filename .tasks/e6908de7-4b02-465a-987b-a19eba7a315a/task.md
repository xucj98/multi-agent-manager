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
