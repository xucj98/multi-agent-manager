# 高频状态推理与偏差触发replan：复用checkpoint的推理实现

## 当前执行授权：原入口两次首 query 验证

Manager 已验收准备 report32da353ec1da3b386cfd6fe8e1b1b67806fb4d60，亲自阅读两个工具及依赖，重算runner SHA376dd1fd087a5e79a9cbda4e83d1ff5b8534dc9c59429a60acbdf8ed2a0abf34、scheduler SHA0561e295e644bee882c7abaee9d08e856b9e5ad00aeafbb4ed480ad7f3179ae2、capture_common SHAf6e80912a2d40f9298bf0060e92c7e5126d5a476d94c6a3e6c33eeed2265cc2f；在真实冻结bridge依赖上独立复跑11个CPU seam tests全部通过。结合先前独立方案核查88976c0，现明确授权同一terra/max执行者运行，不再等待另一轮许可。

将上述精确工具的小型冻结副本部署到本TASK-ID C3证据目录，复用旧C3 HF工程runtime只读源。固定C3GPU0、put_back_block J train0/20000、env100000、matched baseline和matched shadow各一次正常action request，两臂顺序执行，最多使用剩余2/8样本，无warmup/replay/probe/第二episode。核对GPU及原独占端口空闲、三库精确HEAD/clean、实际checkpoint、工具hash；根据旧工程manifest/config/command构成原入口CLI，先保存其无--execute的plan并核对旧reset/语言/配置/环境可确认部分，再在同一参数上添加--execute。不能把本次未记录或旧不可观测条件声称已相同，不新增cache/JAX/renderer override，不重装/重传模型或复制整套runtime。

每臂独立全新result与diagnostic root，max array bytes保持8MiB/每snapshot。工具保持原完整iteration/after_execute后clear和status，完成step0、queued30/dropped30且只一次infer；exit70是明确的诊断截停，必须与完整收据及原failed benchmark leaf一起验，不能单凭exit70认成功。第一臂完整有界捕获成功才进入第二臂；失败或sample-ambiguous停止，禁止自动重试/补样本。完成后检查两臂完整request各字段、H50/K30，以及与旧两侧/之前插桩捕获的精确数组差异；K30对本次H50前30需独立比较（工具只检查shape/type）。留全量输入/调用参数/输出/身份、失败叶及哈希，不把诊断当smoke成功，不解冻HF formal、不调容差。

若预计>30min登记MAM实际长进程，正常结束turn由MAM唤醒；否则完成两样本、归档已有job、资源收尾并发布紧凑report。本次只准入该明确两样本，源算法/阈值/其他任务不变。

## Manager 已接受独立方案核查：补齐两个停止边界后交工具验收

独立工程核查 report 88976c0165e29956838f62d50df7e55f0ecce66e 已完成。Manager 亲自核对冻结 transport/codec、worker execute/clear、runner _wait/_loop 源码，接受其可行性和以下增量要求；这是设计准入，**尚不是未交付工具的 GPU 准入**。作者继续准备，不扩大工作范围。

- 同步 policy RPC 返回后立即在 RAM 深拷贝完整 actual request、call kwargs 与 post-wire H50，再把未修改的原 result 还给 scheduler。磁盘文件/hash/fsync 放到完整首轮 run_iteration 和 after_execute 完成、queue clear 后，不在模型前增加 I/O。不得后台持有原数组引用；metadata/reset RPC 原样透传，不算 action sample。
- 在发送前拒绝第二次 infer/infer_audited。首个 RPC 若发生 post-send transport/capture 异常，记 sample-ambiguous 并停止，不能自动 retry；每臂最多一次发送，剩余两样本不能因错误重置计数。
- **固定 env100000 的预检拒绝必须停止。** Runner 默认 accepted=false 会 seed+=1 并再次 reset；必须在任务私有外层保留首个原始 preflight 事件后，在其进入该分支前终止。仅允许 episode0/seed100000 的一次 reset；拒绝、身份错、缺 accepted、意外 terminal 或 reset传输异常都保留失败证据并停止，不以 seed100001替代。可在原 preflight 事件发出后的窄 hook 实现，勿重写整个 runner。
- 真实 execute 后须等原 run_iteration 完成再 clear，随后仅用无 drain 的 get_episode_status 验证 logical_step0；明确 queued30/dropped30/queue空。保留原 runner 的失败处理：诊断 child 明确截停，使其在 ep0记录 scheduler_exited_before_terminal/runtime error 后终止，不进入ep1。不要把 writer 的 evidence_complete=true 当正常episode；失败 leaf 加独立 bounded_first_query 收据，永不作为 matching smoke/formal入口。

CPU 准备检查补上 accepted=false 不二次reset、不发infer；post-send异常不重试；第二infer在发送前阻止。保持之前完整输入/请求返回值不变、原执行/after_execute/clear顺序检查。交工具实际路径、最小diff/hash、CPU结果后由Manager核查并通知运行。没有新增训练或正式评测授权，不更改之前的两样本结论范围。

## 当前接续：准备原入口两样本验证，先完成 CPU/源代码核对

Manager 已独立验收 report 240caf91cdab0aa8fc91b198424495bf00237969 的离线数值部分：重哈希其 34 个引用文件，逐项重读两集旧 baseline H50 / shadow K30 和新 NPZ，确认新 H50 vs 旧 baseline 为 511/700 不同，历史 K30 为 299/420 不同，报告数值准确。接受“新结果不等于任一旧侧”；**不接受仅凭下一组两样本便能区分 wrapper、启动顺序等具体原因的表述**。同时改变入口/缓存/插桩后一次复现或不复现只能给有边界的证据，不能独立作因果归因。

Manager 的下一步设计：保留旧 BenchmarkRunner 启动/metadata/reset/episode prompt/首 query 路线、正常 policy server、冻结源码和 checkpoint。put-back train0 / env100000，matched baseline、matched shadow 各一次 action infer，共用剩余 2/8 的预算。**本次通知只授权任务私有工具准备及 CPU 检查，GPU 待 Manager 审阅独立工程核查后明确通知。** 不等待 reviewer 才开始准备。

与此前建议的区别：必须保存本次实际 policy 请求的完整 RGB/state/memory/prompt/请求选项、post-wire H50 响应、真实 execute K30 和 reset/命令/环境身份。优先在 scheduler 的同步 policy RPC 返回后、将结果交回原逻辑之前才复制/写盘请求和响应；请求可沿原 call 参数取得，禁止新增 get_obs/reset/infer、模型/transform/JAX wrapper 或 pre-infer host copy/fsync。Manager 已读 WebSocketClient.call：packb→同步 send/recv→unpackb，本身不修改请求；仍请核对实际 scheduler 请求/返回值的后续复用。保留正常 execute 请求后，在下一次会推进队列的 get_obs 之前 step0 clear，记录 queued=30、dropped=30、完成步数0。实际请求仅引用到 RPC 返回后取值的局限如实说明，不伪称直接截取实际 wire bytes。

沿原 robot/policy 启动及握手、reset 请求；正常 policy server 不使用前次 diagnostic_policy_server.py，不改 Policy.infer/input transforms/random.split，不追加 replay/warmup。保留原环境可确认部分并完整记录当前 JAX/WARP/CUDA/XLA/缓存配置，不新建一套 runtime/模型/通用日志框架，不人为声称旧未记录环境已相同。本次可保留新的 scheduler 小型 wrapper及第一 query 后截停；若沿原 runner 必须通过明确的 diagnostic stop / 非零 child 退出避免第二集，保留原异常语义和 failure leaf，另写诊断完成收据，不能把截停伪装为 successful smoke。

CPU/源码检查应证明：一次 infer 上限且不重试，不开始第二 episode；返回后才捕获输入/响应；execute 后 clear 不推进动作；完整请求字段留存且不修改原值。预先列明最小 hook/命令差异、停止与失败资源释放路径、新产物路径和字节上限。比较本次两臂完整输入、H50/K30，以及旧两侧和前次新捕获；未观测到的真实 PRNG key仍写 unavailable，不能拿 stream/call 当 key。无论相等与否，均不凭两次首 query 自动解除全轨迹匹配/HF formal 暂停，也不调容差。

独立核查 TASK-ID 655416db-f379-4793-878d-b2538ad26d81 正与 Manager 并行核对上述接入点；你先准备小型工具并发布准备报告，保持原 source trees只读。无需改生产源码或重新 review 整个算法。

## 当前接续：旧工程与新首query捕获的离线差异定位

已收到报告18f786b49c3461fb2b2fc766b2afa8febe234e26：新捕获6次正常action sample没有复现历史差异。Manager正在独立核验wrapper与原始数组。请与Manager并行做下面的离线定位，不增加GPU采样、reset、完整轨迹或修改生产源码，剩余2次采样暂保留。

1. 把这次新捕获的首query完整H50/queuedK30，与旧matched baseline/shadow的put-back episode0及episode1真实对应动作逐项比较，给出新结果究竟等于旧哪一侧，或两边均不同。保留float32 wire合同，列真实差值，不把哈希不一致本身当输入已不同的证据。
2. 逐项对比旧hf_engineering.py执行入口与新run_first_query_diagnostic.py：实际robot/policy环境/命令、checkpoint/metadata、reset config overrides、instruction获取与设置、相机/图像预处理、scheduler初始化与reset顺序、第一次get_obs及动作key初始化路径。用源行号和旧command/config/preflight/episode artifact指出已确认差异，特别核对本次从profile组装的reset是否遗漏旧runner的task_overrides或语言指令。不要继续笼统列“可能环境/生命周期”。
3. 若旧轨迹没有保存的字段无法回溯，明确最小不可观测缺口；给出能只用剩余两次action samples区分具体假设的最小方案供Manager裁决，但本次先不执行。不要重复八leaf长轨迹、扩日志框架或调阈值。

交紧凑离线报告与派生artifact/hash。当前已确认旧前缀数值差异不是50/30形状误差；新的控制样本相等也不自动撤销旧失败或证明所有运行确定。停止点是具体差异/最小有界验证方案，完成后正常结束turn。

## 当前任务：HF GPU成对差异的首query窄诊断，正式评测继续暂停

C3工程report `1b0006941651c958d7ece0b217034c33634a2bd0` 已发布，8个2episode leaf正常退出，但matched两任务未通过动作等价。Manager已亲自核对原始failure文件SHA `c6519c947782001a07295daf7aeed4a6a1d2295669c17ececd8acb537e2c26f4`、精确source与比较脚本，作如下裁决：

- evaluator脚本将matched baseline的50×14完整预测和shadow的30×14实际queued_actions直接比较，是审计口径错误；已交eval owner修自己的离线比较。不能仅修shape便宣称PASS。
- Manager直接重算相同前30×14：rearrange episode0/1分别284/292个数值不同，max_abs 0.0038730204/0.0038729906，RMSE0.0007002742/0.0007253131；put-back两个episode各299个不同，max_abs0.0034926604，RMSE0.0006326193。因此同一执行前缀仍确有差异，不凭形状错误撤销工程暂停，也不擅自放宽容差。
- 第一动作发生于source_step0，早于任何中途probe，不能归因于之后probe消耗RNG。当前recorded input只有robot_state/memory_input_ids，没有图像或完整语言输入。Manager又直接核对OpenPI0ce: policy_rng只有stream/call，无实际PRNG key；“计数相同”不证明采样key相同。不得称完整输入/真实随机状态已相同。

请复用本task已有源码树，先只读查配置/命令/模型/权重身份、实际import来源、Policy初始化/reset及首query观测路径，排查是否为记录口径、不同初始visual/language/transform输入、实际key、固定输入下GPU采样差异；不预设原因、不改变算法/阈值/模型/动作执行频率。原准入commit仍OpenPI0ce566bd34f99cb4775422f012ab67c16aa53885/bridgeffa122494c19e1c0154e877010f7b470967ccfc6/RMBench6abebf08d084d0be43aa56ebe158dc8395fa58e4。

可直接使用已释放的C3 GPU0做有界诊断，但先核对资源与独占端口，复用eval owner精确冻结runtime作为只读源，任务自有工具/证据写到本TASK-ID，不能在eval owner运行树改源码或共享cache。优先put-back train0 / env100000的matched baseline和shadow，各只捕获首个真实policy query的完整输入及实际action PRNG split前/采样/split后key、输入transform前后image/state/memory/prompt/token的shape/dtype/hash（必要完整数组只保留这个query、有界），以及输出完整H50/实际K30。捕获wrapper只用于工程诊断并保存source/hash/插入点，不额外split RNG或调用模型，不把新instrumentation冒充原始证据。不要再跑完整16episode对照。

然后在同一实际完整输入与同初始key/同noise下，做最小GPU重复/两条入口交叉调用，区分输入不一致与推理不一致；总正常action采样最多8次，首轮不执行新长轨迹，不做正式100、r_s30或HF效果试验。实际PRNG可在task私有诊断wrapper观测；生产wire是否需补真实key由证据与Manager随后裁决，当前不无目的扩日志框架。若用P0工具只复用测试思路，不合入另一个未完成GPU验收分支。

交紧凑报告：已确认与未确认原因、首个真正差异位置、实际来源/full input/key/action证据及hash、最小必要修复方案；需改生产代码时先交具体原因，由Manager裁决后干净提交并另审。上游算法已通过CPU的部分不机械重做。预计>30min诊断登记MAM真实PID；完成或遇确定需裁决点正常结束，不轮询。root负责解释和裁决，仍terra/max执行。

## 当前修复：Manager 对复审 27b16d899 的裁决

Manager 已直接读取冻结 bridge552ea 的 _formal_gate/_accepted_episode/_record、writer，以及 RMBenchc99 的 validate_smoke_run，确认下列遗漏。上一轮真实 recorder 接线、child identity 和单次 reset 已通过，不重做算法/RNG改动。候选基线仍 OpenPI0ce566bd34f99cb4775422f012ab67c16aa53885（保持不变）、bridge552ea78f73e62fddc747d5d26e7e6c365fa00339、RMBenchc99ec6a2c6df96ec8705b106b125935fce862052（保留 f401 祖先）。复用已有独立树。

1. 接受 formal smoke gate 缺证据校验为 P1：既有 validator 根本未消费 rolling evidence，缺文件或 evidence_complete=false 仍能被当作 matching smoke。请在现有 recorder/validator 中加入可复用的窄验证，runner 根据实际显式 rolling/matched 协议传递“需要 evidence”，不能以 record 是否恰好带 path 决定是否需要，否则缺整个字段仍绕过。逐 episode 校验引用、实际文件/可解析 JSONL、支持的 schema、header episode_id/seed、最终 episode_finished/evidence_complete 严格 true；存在 truncated、缺终态、身份错或不可解析均拒绝。默认 baseline 仍不要求 evidence，既有标准 source/manifest/video/process门禁不弱化。
2. 初始化失败的悬空引用接受为 P2 可用性问题：已有 terminal_scheduler_error/runtime_error 会判 run 失败，故此项本身并不证明失败被计成成功，但文件状态仍不诚实。采用最小明确 unavailable/missing/incomplete 状态即可，不要求为未执行推理伪造事件/重开 writer。未创建文件不能写成普通可用引用；已写部分文件保留并明确 incomplete/原始错误，原 failure reason 和 traceback 留存。不要覆盖已存在 artifact。
3. 不仅 smoke，正式100各 episode 收尾也必须使用同一证据检查规则，成功退出但日志截断不能静默标为正常完整 run。证据异常按基础设施/证据失效保留失败 leaf，不当算法失败混入成功率，不拼 partial；无须另造验收框架或将全部科学时序解释塞进通用 validator。

必要 CPU 验证：真实 recorder + child 在 writer 前直接失败、writer 后异常、正常完整和默认关闭；matching gate 接受完整并拒绝缺引用/文件、坏 JSONL、身份错、无终态、truncated、complete=false；至少一例正常 child 退出但 evidence 不完整的正式收尾拒绝。保留既有默认行为与一次 reset 检查。先完成该冻结链的窄修并提交 clean 新版本、更新简短文档/report；不要继续任意 edge-case 硬化，不修改 P0 logger、训练、阈值或源码运行树。仍 CPU only、未准入 HF GPU；作者测试不能代替独立复审和 Manager 最终裁决。完成后 publish report 并结束。

## Manager 当前增量裁决：真实 RMBench recorder 接口不匹配

新OpenPI0ce566b/bridgea0f1d50进入独立review后发现P1。Manager直接核对runner._accepted_episode和既有RMBenchResultRecorder.path_for：前者请求rolling_evidence，而真实recorder只接受episode_video/process_log，未知kind抛RuntimeError；调用又在try外，故显式HF/matched运行会在scheduler启动前失败，不能按fake recorder测试PASS准入。

Reviewer还确认真实event('episode')未保留runner传入的rolling_evidence_path。请与真实已验收RMBench recorder对齐最小路径分配及episode结果引用，测试真实recorder和runner的seam，覆盖normal/terminal/error与引用实际存在。可优先使用既有支持接口；若必须改RMBench，批准在本任务独立worktree中从已验收正式f401f5279c95451eb424ac98b831bab5552b2120做窄artifact/path/reference接线及测试，先核实commit可用性，不改共享活跃C runtime，不新建通用框架。交付所有实际修改库的精确clean commits及样例，交原reviewer增量复核，GPU仍不准入。

新增同一链路的身份遗漏已由Manager源码核对并接受：a0f1d50 child CLI只传episode_file/evidence_file，未传episode_id/env seed，writer从_reset_args取得null。请从已接受的benchmark episode身份建立明确的记录上下文，JSONL header与episode record双向一致；不能通过给scheduler新增环境reset来取得身份，benchmark已reset一次，修复后不能二次reset、消耗额外场景随机数或覆盖实际身份。

Manager已查本机缺f401对象且你当前RMBench tree基于2e9677c；同时SSH核对C的2e9677c..f401仅memory_schema_eval.yaml新增17行N/S配置，真实recorder文件不变。为避免后续部署缺配置，最终交付仍须保留f401完整基线。可以从已授权C只读源 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-highfreq-base/RMBench` 用SSH git fetch或小bundle引入f401到本机，然后在自己的worktree保存/接续补丁到该基线上；不丢弃自己未提交修改、不改远端runtime。MAM创建记录base仍2e不影响报告写明最终实际f401→候选diff与完整HEAD，不能把旧base元数据当最终验收版本。

论文作者与代码reviewer职责不变。其余增量审查继续，不因这项已确认阻塞等待整体report才开始修；原冻结算法、RNG与36批正式合同不变。

## 目标与职责
用户已明确授权：只改推理、复用现有checkpoint，实施高频状态更新和偏差触发提前replan，并在4090集群评测。不新增训练，不改模型参数/训练代码/标签，不改变已在跑任务。你以 gpt-5.6-terra/max 负责工程实现，Manager亲自决定科学设计和验收。先读AGENTS、mam task show及各库规范；独立worktree由mam workspace add创建。

基线 OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，robot-bridge f9626636c4776d8eb15f9c556775cb2d12c000e5。RMBench如需窄入口接线，选已验收2e9677ce8ec9f623395184f63f32ddafa66e5e44及C renderer运行合同，先解析该commit可用性；不要修改共享活跃runtime。与285d审计及8968记录接口owner交流事实，但不要等待其整个任务完成或扩大耦合，独立实现本任务所需最小记录。

## 先行可执行实现
1. 加默认关闭的推理模式：baseline、仅高频状态更新且固定K、相同更新加状态偏差触发replan。动作仍H50，正常最大执行K30；monitor间隔先5个已完成policy rows，可配1/30用于控制。保持默认关闭时行为/RNG/调用次数相同。显式参数开启、失败拒绝不支持合同。
2. S现有prefix阶段直接产生当前状态：抽取可复用状态专用调用，保留同权重/transform/decoder，跳过不必要action diffusion。与原完整推理状态结果在同输入下精确对齐，不创建新head。probe不推进动作RNG。旧S lag30只是本轮推理分布变化的记录项，不以此阻塞不重训实验。
3. J逐行输出是t+j+1未来状态，T是重复t+30；不能把J row0声称为当前t、不能将T row0当当前状态。先实现可返回metadata确认target offset的只读probe接口和forecast对齐辅助：原chunk起点t0，已完成d行，新J probe row0目标t0+d+1，对齐原J row d（不是d-1）。这一路是新旧预测一致性，不是已实现独立当前状态测量。正确的状态递推/消费规则由Manager稍后补充；不要擅自将未来值写为当前状态。先推进接口、执行前缀与进度/RNG测试。
4. scheduler独立保存原计划的动作/状态forecast、monitor状态、实际完成前缀。在已完成边界取得真实新观测，默认继续原动作后缀，禁止每次probe隐式替换动作。在明确trigger后才丢弃尚未执行后缀，重新从当前观测生成动作；必须复用现有安全执行/清队列/进度机制，不能清掉别的任务或已执行动作。仿真分段发送不得改变同一原chunk的逐行控制内容和TOPP语义；给真实源码证据与基线分段等价测试。若controller一次阻塞执行整个chunk，明确最小可用分段路径和暂停仿真计时局限，不声称异步实时。
5. monitor原始结果与沿schema规则选择后的值都留痕；字段类别不相减当距离，不将J raw坐标softmax伪装成校准置信度。threshold、debounce、min-prefix由Manager冻结。T/S无同时间逐行forecast时拒绝frame-deviation trigger，不能用终点/当前值硬造轨迹；可用单独命名的已识别状态变化trigger，待Manager明确后实现。

## 验证与交付
先用CPU/模拟controller验证：关闭等价；固定K开monitor但不更新时相同动作流和动作RNG；多次probe不覆盖执行队列；early trigger实际只执行前缀、取消后缀且新chunk正确接续；terminal/停止/不足K/重复或过期观测/执行失败和episode reset；index0/29/边界错位；不支持T和无状态checkpoint明确失败。状态路径对齐检查需真实model函数结构测试，必要小模型参数CPU，不只mockserializer。

记录每次动作/probe调用类型、实际row/target时刻、输入状态、raw/decoded输出、原forecast、偏差与trigger原因、K实际执行/丢弃、动作及状态RNG身份、观测与计算时长；输出有界，逐run配置/commit/checkpoint哈希留痕。短smoke模板与正式评测交给独立owner，在独立review通过前不自己部署C或跑正式。尽快先发关键接口可行性/准确偏移结论，继续代码实现；完成commit并发布report。任何>30分钟程序按MAM登记，不高频轮询。

## Manager冻结首轮算法合同（本节覆盖先前待定项）

**只改推理，新增训练数0。** 支持现有新20k Memory-v1 categorical J（各字段target query+1+row）与S（query+0）。T的phase为query+30，首轮只保留原baseline，不进入rolling或frame-deviation模式；不能按输出shape或名称猜支持性，要核实canonical target refs。unsupported混合target需在启动前解释错误。

**执行路径**：仿真优先一次提交原K actions到既有队列；get_obs使用remaining=K-d逐次_drain_to，只让真实完成d增长；保留原后缀，trigger明确clear剩余后再新推理。终止时不probe/不replan。server不解释task语义，scheduler决定更新和触发，controller保持现有逐row执行。新功能仅simulation，不把真机插值路径一并改造。逐episode独立重置monitor、计数、RNG、forecast。检查任务get_obs副作用/全局RNG，shadow对照不等价时先修必要读观测副作用或报告，不能算算法收益。

**J高频rolling**：动作边界a生成原计划A_a,Z_a；monitor forecast初始等于Z_a，source a。每次实际完成到u时，先从最近monitor forecast的row(u-source-1)读取target恰为u的各字段，按原schema编码/保留规则形成新query输入m_u；不消费未来行。r_s=5，probe在u=a+5,10,15,20,25（非terminal）读取新观测，用当前m_u及独立probe RNG完整joint采样，动作丢弃，新forecast保存source=u。在原K边界u=a+30不多做一个probe，按最近forecast对应target=u的row取m_u，进入正常动作infer。例probe@a+25的row4输入a+30。r_s=30退化为原K30反馈，r_s=1仅工程/吞吐可配置。新probe forecast联合生成但未采用的动作不等于实际已执行动作，记录其为“刷新预测与递推的部署变体”，不能宣称独立当前状态测量或预测被实际接触确认。

**J事件触发**：始终比较当前动作计划最初Z_a与新probe Z_u，不能偷偷把参照换成上一次probe。d=u-a；phase字段的old rows[d:d+3]与new rows[0:3]对应相同绝对target u+1..u+3。先对每行按实际categorical argmax/原decoder后的IDs作不等指示，D=3行平均；D>=2/3为本次偏差大。连续2个有效probe均偏差大，且d>=10且d<Kmax30才trigger；任何一致probe清连续计数，重复/过期观测不增加，无法对齐/越界/缺phase/非法ID不能触发并明确报错。unknown也是模型合法预测类别，首轮不通过忽略unknown压低误报。不使用phase编号差、不用未经校准softmax置信度、阈值不按新成功率调。
trigger时当前m_u已按上一forecast对齐到u，新probe仍只用于偏差；clear仅尚未执行的队列，记录丢弃数量；用同一最新观测和m_u经**正常action RNG**重规划，不能直接取probe生成的actions。新动作计划成为后续比较参照，计数清0，重新至少执行10行。非trigger继续原actions，新probe保存作rolling forecast。默认max K30保留，无“正常phase变化就必重规划”的隐式条件。

**S固定K高频**：动作边界调用原完整infer，它已经预测当前状态并条件化动作，存为monitor状态；执行中每5行只做prefix state probe，输入上一monitor状态并保存新selected，原动作queue不变。下一action边界仅做一次完整infer（不可probe后又在同帧递推一次），输入最近probe状态。S训练lag30→部署较短lag如实记为推理协议改变，不重训。chunk级current output也可后续用稳定phase-change触发，但首轮不实现/不把它叫forecast-deviation。

**首轮模式和工程门槛**：J baseline K30；J shadow(r_s5、不改cache/动作)作工程等价；J HF-fixed(r_s5,K30)；J HF-event(r_s5,Kmax30,window3,threshold2/3,consecutive2,minprefix10)；S baseline/HF-fixed。另支持J HF-periodic K10/r_s5作为后置频繁重规划控制，显式runtime max-K覆盖留痕，stored metadata不改。K10不是事件臂平均调用数的严格匹配对照，不做该声称。正式先rearrange/put-back train0同现有checkpoint；其他9task扩展待对应checkpoint和target合同验收。

每个probe有单独可重现RNG流，动作RNG只由动作infer消费。shadow多probe后同动作输入/RNG须输出一致；J采样导致的预测波动通过固定随机流/窗口/连续判据记录，不能由触发次数声称物理异常次数。需要测试固定观测/输入的重复probe波动，报告但不据此调整正式阈值。

## Manager接受独立合同审查后的补充
Reviewer4006确认时间公式正确，并指出必须验证的P1：标准MemoryContext pending chunk不能在a+30把旧Z_a row29覆盖rolling新值，early clear后也不能用下一chunk的completed把已取消的旧pending“补完成”。HF-J须隔离标准pending反馈或在同一明确生命周期内正确结清/废弃，原动作plan id/source/actual prefix及丢弃后缀显式关联。probe不是被执行chunk，不能伪造accept或完成证据；默认路径维持原Context行为。

任何invalid/stale/duplicate/gap观测都打断偏差连续计数；旧/重复u必须在probe前短路，不消耗probe RNG、不替换forecast。非terminal出现非预期进度跳跃、超过计划K或target越界，明确失败该诊断执行，不跨缺口累积“连续”。测试高@5/invalid@10/高@15不触发、clear后新plan进度不结清旧pending、完整K边界不回写旧forecast。

评测owner核实正式门禁固定eval_seed0/1/2→100000/200000/300000，且逐臂matching smoke source/manifest严格相等。撤销900000工程seed要求，不为此增加新CLI：baseline/shadow成对工程smoke沿既有eval0 seeds100000/100001，独立run目录/工程标签，不据分数调已冻结阈值；正式每配置/每eval seed仍自身matching smoke2→formal100。工程shadow不得冒充HF-fixed/event的matching smoke。派生新配置明确random_light=false、crazy_random_light_rate=0并留痕；若原baseline未满足，不能无声改变环境后沿用旧结果，需报告并统一新对照。

## Manager 初验 P1：默认关闭的跨 episode 动作 RNG 改变

4529a91/53f853a 已交付并进入独立 review4006。Manager 用真实旧/新 Policy 类（仅以固定 CPU 模型替代采样器、保留实际 transform/split/output 调用链）亲自复现：infer→reset→infer，首个动作一致，第二个动作不一致，新版重复了第一次动作。旧 action RNG 两次推理后的 key_data 为 [4165894930,804218099]，新版重置后为 [1797259609,2579123966]。同时直接核对旧 OpenPiBackend.reset 为 no-op，新版无条件调用 Policy.reset；真实 SchedulerBase 初始及 ep_init 都发送 reset，所以此差异会进入默认 baseline。

此问题接受为 P1，当前不准入 GPU。请窄修确保未显式启用高频协议的请求保持原 action RNG 生命周期、响应字段和诊断开销；当前 infer 对所有 J 无条件复制 memory_raw_actions、对所有 JAX 返回 policy_rng 也应移到明确开启的审计/高频请求路径。不能只以新baseline对新shadow便证明旧默认行为不变。

原冻结合同中的高频逐episode reset 应作为明确启用的高频实验协议，不能改写公共 baseline。请提供最小显式接线方案并与 reviewer 对齐：默认模式维持旧行为；高频的 action/probe episode reset 与留痕仅影响明确开启的请求/会话；shadow 对照必须与用于比较的baseline采用相同动作RNG生命周期。若高频协议与历史baseline在此不等价，应向Manager明确列出需要重评的matched baseline，不能静默复用旧成功率或据此调阈值。新训练仍为0；是否补matched baseline由Manager根据证据决定。

作者可先修此已确认问题并提交新的干净commit；reviewer继续冻结版本的其他检查，最终只对新精确commits给准入结论。保留infer→reset→infer默认关闭、显式开启、probe不影响action流和baseline/shadow跨episode比较的有意义回归。

## Manager 正式 RNG 对照裁决

Manager 已直接核对 BenchmarkRunner：policy server 在整个100集 run外创建，只有scheduler按episode重建；历史action key在同一run内连续消费。create_trained_policy未传rng，初始值为jax.random.key(0)。因此显式HF逐episode回到initial key与历史baseline确实不同，不只是无影响的reset接口变动。

保留HF逐episode reset合同，新增同协议matched baseline，不直接拿历史baseline作为HF效应的分母。请以最小显式配置把已有reset_episode_rng RPC接到baseline与shadow；普通baseline和普通shadow仍默认历史no-op，不能默默改变默认。无需新建第二套baseline执行算法，也不改变原MemoryContext/K30反馈或额外插入状态更新。显式matched baseline无中途probe；matched shadow有probe但不更新cache/动作，与matched baseline同一action key生命周期。必要审计字段仍显式开启，普通infer输出/开销保持原合同。

所有本轮HF、matched baseline、matched shadow：action初始key0，每episode恢复同一初始key；probe流fold_in(initial,0x50524F42)，每episode恢复且独立于action。这不是3个policy sampling seeds，eval seed0/1/2仍是三个环境列表。matched baseline/shadow在多episode中必须保持相同action采样key和实际执行动作；HF-event的额外正常infer允许改变该episode内后续action query消耗，不能宣称所有臂每物理时刻使用同一噪声。

额外matched baseline由Manager批准：J两任务×3eval=6批先与核心J12批一起开展；S两任务×3eval=6批随后与S HF-fixed6批开展。原24部署批次加12对照=36批/3600正式执行，新增训练仍0；工程smoke另记，阈值/任务/频率均不变。旧结果保持有效且留在九任务原协议证据中，不与新reset协议跨批拼成300。实际配置名、默认值、RNG身份及两种baseline用途写入作者交付说明，精确commit交独立review后才可GPU准入。

## Manager 接受 review P1-2：rolling 证据必须随 episode 留存

独立冻结报告b55c30e指出rolling trace只有scheduler的64条deque/get_status。Manager已亲自核对53f853a：_rolling_start_plan/_rolling_probe/_rolling_trigger_replan更新内存而不输出rolling日志；benchmark._wait等scheduler退出后仅读robot get_obs诊断，_record不收scheduler状态。因此成功率即使可保存，关键raw/decoded、RNG、consumption和trigger/clear证据会随进程丢失，接受为GPU准入P1。

请在本任务内窄修持久化，优先沿现有每episode scheduler日志或已登记result路径输出有版本的结构化记录，不创建通用记录框架、不等待独立P0 logger。记录须能离线关联episode/plan/query、输入/forecast target、原始和解码状态、实际采样key、执行动作及已完成/丢弃前缀、probe、边界与terminal/异常原因。可增量事件或阶段快照，避免每次全量复制历史；不传输额外RGB或巨量旁路数据。普通默认路径保持原开销。

不能只在get_status或正常退出时输出最后64条：700行/K10可能超过64个plan，且错误退出也要保留已完成证据。日志容量应明确、有界、超限标记incomplete，不得静默截断后通过正式验收。新增有意义验证：episode子进程退出后实际文件可解析、trigger旧计划丢弃和新计划接续完整、终态最后已执行前缀、异常/截断明确，默认关闭无新增输出。作者交付样例文件/解析命令/最小schema，由reviewer独立复核。若某个指标仍无可复核来源如实列出，不能只凭内存状态称已满足留痕。
