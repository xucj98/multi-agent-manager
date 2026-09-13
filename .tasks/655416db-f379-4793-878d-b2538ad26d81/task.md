# HF首query差异：两样本验证方案独立核查

Review source delivery (source TASK-ID: 0acf5d43-91b6-4171-b727-e3fe0f7e7939):
{
  "task": "0acf5d43-91b6-4171-b727-e3fe0f7e7939",
  "commits": {
    "openpi": "0ce566bd34f99cb4775422f012ab67c16aa53885",
    "robot-bridge": "ffa122494c19e1c0154e877010f7b470967ccfc6",
    "RMBench": "6abebf08d084d0be43aa56ebe158dc8395fa58e4"
  }
}

Source task requirements:

# 高频状态推理与偏差触发replan：复用checkpoint的推理实现

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

Source report:

# 交付报告

## 当前增量修复

已按 Manager 对复审 `27b16d899cf0220986a7531ad04989b227270f61` 的裁决，完成 rolling evidence 的 formal 准入链窄修；未改算法、默认 baseline、OpenPI、P0 logger、训练或运行中的 C 环境。

- RMBench 增加单一 `check_rolling_evidence()`：仅当 bridge 从已解析的显式 rolling/matched 配置传入 `rolling_evidence_required: true` 时，逐 episode 校验 artifact 文件、JSONL、schema v1、header `episode_id`/`seed`、最终 `episode_finished`、`evidence_complete: true` 以及无 `truncated`。
- `validate_smoke_run()` 复用该检查。缺引用、缺文件、坏 JSONL、身份错、无终态、`truncated` 或 `complete=false` 均拒绝 matching smoke；普通 baseline 不要求 evidence。
- bridge 将这一“是否需要”的配置事实传给 formal gate，并在每个显式协议 episode 收尾调用同一检查。正常 child 退出但 artifact 缺终态或不完整时，episode 记为 evidence/infrastructure failure，正式 run 不会把它当作正常完整结果或拼接 partial。
- 未创建文件时 episode record 不再留下普通 `rolling_evidence_path`；以 `rolling_evidence.state: missing` 或 `unavailable` 保存。已写部分文件保留其路径并标记 `incomplete`/`invalid`；已有 scheduler failure reason 与 error message 原样保留。
- 更新 [rolling evidence 文档](/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge/docs/reference/rolling-evidence.md)，说明 matching smoke/formal 的同一完整性合同。

上一轮已修复的真实 recorder path/reference、child header identity 和单次 benchmark reset 仍保留：`RMBenchResultRecorder` 按 episode 分配 `rolling_evidence/episodeN.jsonl`，显式 child 只接收审计 identity，不会据此发起第二次环境 reset。

## 验证

- RMBench recorder/validator CPU 回归：
  `.venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`
  → `5 passed`（既有 SAPIEN/Vulkan 资源警告，无测试失败）。
  - 使用实际 recorder 留存 normal、terminal、scheduler error 的 evidence 状态。
  - matching gate 接受完整 artifact，拒绝缺引用、缺文件、坏 JSONL、身份错、无终态、truncated 和 `evidence_complete=false`。
- bridge lifecycle CPU 回归：
  `PYTHONPATH=/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi/packages/openpi-client/src .venv/bin/pytest tests/benchmark/test_stage3.py tests/benchmark/test_runner.py -q`
  → `26 passed`。
  - 真实 RMBench recorder + child 覆盖 writer 前直接失败、writer 后异常、正常完整、default 无 evidence；保留每 smoke episode 一次 reset。
  - formal-mode CPU fixture 覆盖 child 正常退出但 evidence 无最终记录时，runner 以 `accepted_infrastructure_failure` 拒绝并把 episode 写为 Fail。
- bridge 全量 CPU 回归：同一 `PYTHONPATH` 下 `.venv/bin/pytest -q` → `524 passed, 2 skipped`。
- bridge 变更文件通过 Ruff、Python 编译与 `git diff --check`；RMBench 变更文件通过 Python 编译与 `git diff --check`。

## 精确提交与基线

- OpenPI（本轮未改）：`0ce566bd34f99cb4775422f012ab67c16aa53885`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi`
- robot-bridge：上一候选 `552ea78f73e62fddc747d5d26e7e6c365fa00339` 之上的当前候选
  `ffa122494c19e1c0154e877010f7b470967ccfc6` (`fix: enforce rolling evidence at benchmark close`)
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge`
- RMBench：正式 `f401f5279c95451eb424ac98b831bab5552b2120`，上一候选 `c99ec6a2c6df96ec8705b106b125935fce862052` 之上的当前候选
  `6abebf08d084d0be43aa56ebe158dc8395fa58e4`（`验证 rolling evidence 的 smoke 完整性`）
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/RMBench`
  - 已核对 `2e9677c..f401f52` 仅是 `memory_schema_eval.yaml` 的 17 行 N/S 配置新增，当前 candidate 保留完整 f401 祖先。

三个 worktree 均 clean；没有登记中的本任务 job。

## 首 query 有界诊断（C3 GPU0）

本轮仅诊断 `put_back_block`、train seed 0、环境 seed `100000` 的 matched baseline/shadow 首个真实 policy query；冻结运行树只读，未改生产源码、checkpoint、共享 cache、阈值或算法。冻结根为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 分别为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`；checkpoint 为 `pi05_rmbench_put_back_block_full_t_plus_1/.../20000`。实际导入的 `openpi/policies/policy.py`、OpenPi backend 和 simulation scheduler SHA-256 分别为 `1c4636db0e5fb97a8e5a4332de047d79d9ad5c63ea6880179d7606b41fa65563`、`a49f45fe5923723afc8982be2ff88d8b483c8bd6aba225838d4c92c7cad7ce5c`、`c6f9eeb9442153f5231b5a1be268ad1f1f04dfe83626caddf68b517839c0ca5b`。

- 真实入口分别为 `matched_baseline._call_policy_infer` 和 `shadow._call_rolling_action_infer`。两者的 scheduler pre-RPC 完整输入树（3 张 RGB、state、memory IDs、prompt）相同，SHA-256 为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`；Policy transform 后树为 `df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`。
- 实际 action RNG 完全一致：split 前 `[0, 0]`，采样 key `[928981903, 3453687069]`，split 后 `[1797259609, 2579123966]`。`implicit_noise_derived_from_sampling_key`、raw model H50、post-transform H50、实际 queued K30 的树哈希依次为 `127e5ee9a8777cfb6f05401c832f45f422efffe52a27bbf0b7b77396e9619c80`、`035baf5219a0e838d404ab4ca56a82063fc64cf7dfd79a508e5317e77268f90d`、`baa84c42691b0aa0e87d0fdb55f4a7c96897ac2a8e19dd45004bcd5e8fb9a096`、`cdcbecf0e6339267b95eccd58529ab6f076adf845d86410f7021661dd6a8e491`，baseline/shadow 均相等。前者是用捕获到的真实 sampling key 按冻结 `jax.random.normal` 表达式离线重建，不是 GPU sampler 内部 noise 的直接捕获。
- 每侧一次真实 action query 加两次同输入/同 key replay，共消耗 `6 / 8` 个正常 action samples。以冻结 backend 的 wire cast `np.asarray(actions, dtype=np.float32)` 比较后，所有 H50 replay、跨入口 replay 和 H50 前 30 行对实际 K30 都为逐元素相等；两个队列均在逻辑步 0 立即清除 `30` 行，未执行轨迹动作。两个保留的失败目录均发生在 query 前，未计入样本。
- Policy transform 的原始 action 是 float64，而 frozen OpenPI backend 在线路上转为 float32；直接比较 pre-cast 值仅有该转换舍入（最大绝对差约 `5.93e-08`），不是推理差异。

结论：这一受控的新首 query 样本没有发现输入、transform、捕获到的真实 PRNG key、离线重建 noise、模型输出、队列或固定输入/key GPU replay 的分歧，因此不支持把历史不一致简单归因为 policy sampling 非确定性。它不撤销既有历史动作前 30×14 不一致审计（离线 queued-action 审计工具 SHA `1be44b9bd3cd02235833707e40022d0690361efae60b131dcbeb287daeb02151`，重算 SHA `bc30cf2ee8bfe7130cc68c1f8eff2862928e5baee1564b6841ffb29d0187d1fb`）：新捕获只说明该次重建的首 query 未复现差异。诊断 wrapper 在 transform 周围做同步 host copy/`fsync`，并暂时 monkey-patch 全局 `jax.random.split`；它保持预期的随机调用语义，但改变了 timing/JIT 条件，所以新样本相等也不能排除未插桩运行时的 timing/numerical effect。仍未确认的条件包括先前 run 的初始环境/完整输入状态或其他生命周期差异；现有证据不支持生产修复或解除正式评测暂停。

证据位于 C3 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic`：[`analysis.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.md) 与 [`analysis.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.json)，后者 SHA-256 为 `c14af95aac92df5cefbfd3958de0100f1efef780d28a7031e8f59435a4500db1`。诊断分析器 SHA-256 为 `71952d10f8050689fe57143448ad5162e12c0edc9a015d68a1006db9d9f02912`；调度 wrapper 记录了上述插入点，SHA-256 为 `318ac87ca3f7b963aff059a101f6c78cfa860735b28b04450b9beaf005050c4f`。

## 离线历史首 query 对齐

未增加 GPU 采样、reset、replay、完整轨迹或生产源码改动。任务私有离线读取器 [`align_historical_first_query.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/align_historical_first_query.py) 以冻结 wire 合同 `np.asarray(actions, dtype=np.float32)`（`openpi.py:349-356`）读取旧 put-back matched artifacts 和新有界 capture；读取器 SHA-256 `94b3a1cbc209b0b1c58f670a74b0a61f4c2a9940a1f2a4fef7c88530dc7b5d58`。结果为 [`historical_alignment.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.json)（`4de3f6edc1af02fec61015439393f5d287da70bea0dd55732a0bf91c35ca2b1b`）和 [`historical_alignment.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.md)（`ffa48e8682d927b544b56664a117861afef1607dd9a0697e425b4394d5231bd6`）。

- 新 H50 的 wire SHA 为 `adf97a1dadeee7df55ab60d7bfe54f9d141cffd7b15c13dd114a222306a2d68a`，K30 为 `f0dcb3163e0723c363e9477faa873a499baba78e4bbba7a2ef7188724ac25fa4`。旧 baseline 的两集 H50 完全相同（SHA `4c69052f6e46e601de388993f3cb1ddc108617e8ded37230cdb758f21b854431`）；旧 shadow 只留第一 `action_plan.queued_actions` K30、两集也相同（SHA `0799a79aea6a7d860b7859f2a7ce988d1b3229f3b6ac2e6b0389cbbc4d405a40`），没有可回溯的 shadow H50 tail。
- 新 H50 对旧 baseline H50 有 `511/700` 个 float32 元素不同，max abs `0.0034926608204841614`、RMSE `0.0006454789071132261`，首差 `[0,0]` 为新 `-1.459865779906977e-05`、旧 `0.00032710886443965137`。新 K30 对旧 baseline H50 前缀为 `296/420`、max `0.0027747450512833893`、RMSE `0.0005912740981828194`；对旧 shadow K30 为 `301/420`、max `0.003492661053314805`、RMSE `0.000688904451176663`。历史 baseline 前缀对 shadow K30 仍为 `299/420` 个不同。新 K30 的 164 个元素同时不同于两边，其余类别也不组成任一旧数组，因此新 capture 精确等于旧 baseline 和旧 shadow 的结论均为 false。
- reset request 仅去掉 run-specific `video.output_path` 后完全相同（canonical SHA `789feb2835dae80d4415c21141594e8b913153374f2a8df9b0b714d160c1679d`）：`task_overrides={}`、`instruction_type=unseen`、`test_num=100`。instruction 精确相同（SHA `8537a6997ea8ad918e3237b6642490ded7c9204d9bd78075b1d6a88ec46f81bf`）；去掉 `eval_video_save_dir` 后 preflight task args 和相机配置也相同。旧/新保存的 `memory_input_ids=[0,0]`、state 均相同（int32/float32 raw SHA 分别为 `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc`、`aed9607efe0f26286bd388129c3f8720abc4de43b417ae34e0a12dfec2d25747`）。
- 这只证明配置与已留存字段相同：旧 rolling evidence 首 query 输入只有 state/memory，未保存 RGB、完整 prompt/token/transform tree、实际 PRNG key、sampler-internal noise；旧 shadow 也未保存 H50 tail。新 baseline/shadow 的 scheduler pre-RPC tree（含 3 张 RGB）和 post-transform tree 分别同为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`、`df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`，但这不能倒推旧全输入或旧真实随机状态相同。`episode_info.info.task_facts.final_block_pose` 也不能当作首 query 输入身份：`rmbench_sim_worker.py:135-149` 的 probe env 会 `play_once()`，`put_back_block.py:106-140` 随后记录该 pose，而 worker 在 `:155-179` 重建实际 episode env 后仍返回前者。
- 已确认入口差异：旧 `BenchmarkRunner.run` 在 metadata handshake 前连续启动 robot/policy（`runner.py:750-771`）；新 launcher 先启动并握手 robot，后启动 policy（`run_first_query_diagnostic.py:355-379`）。旧流程是正常 `run_policy_server.py`/`scripts/run_scheduler.py`，新流程是 task-private policy/scheduler wrapper，并新增 JAX/WARP/CUDA cache 路径（旧 receipt 未保存其值）。新 scheduler 仍加载相同 config、调用冻结 `apply_episode_prompt`，再 `_startup(); run_iteration()`；这与 `SchedulerBase.run()` 的名义首 action route（`base.py:614-648`）在构造后相同，但不能抹去 wrapper 或启动顺序差异。
- 建议但未执行的最后两样本方案：baseline、shadow 各一次，保留旧 `BenchmarkRunner` 的启动顺序与 reset flow；只在真实 execute request 之后的 scheduler 侧采集 post-wire K30，并在 logical step 0 clear queue。不得包装 `Policy.infer`、transform 或 `jax.random.split`。这样可区分差异是否由本次 diagnostic wrapper/startup path 引入；若未获授权额外观测，仍不能回建旧 RGB/实际 key。

## 未执行项

此前的源码修复验证仍是 CPU-only；本轮例外是在 C3 GPU0 完成上述 6 次有界首 query 采样。未启动新的完整轨迹、matching smoke、formal 100、`r_s=30` 或 HF 效果试验，未训练、未改 checkpoint、未部署，也没有新增生产源码提交。剩余 2 个 action samples 保留，除非 Manager 提出新的有界假设，否则不再使用。
# HF 首 query：两样本诊断方案的独立工程核查

你以 gpt-5.6-terra / max 做有界工程核查，Manager 负责实验设计与裁决。先读 MAM AGENTS/README/.local 说明，读取源 TASK-ID 0acf5d43-91b6-4171-b727-e3fe0f7e7939 的最新 task 和 report 240caf91cdab0aa8fc91b198424495bf00237969。只读核对，不运行 GPU、模型、reset 或轨迹，不改作者工作树。证据检查无需另建源码 worktree；如确需独立代码实验，按 MAM 为涉及库建立精确冻结版本的 worktree。

背景：旧 baseline/shadow put-back 首 query K30 数值不同；新重插桩首 query 两侧精确相同但不等于任一旧侧。旧证据缺 RGB、真实 key。作者建议剩余两次 action samples 沿旧 BenchmarkRunner、无 Policy/transform/JAX 插桩，仅 scheduler 在真实 execute 后保留 K30 并 step0 clear。Manager 担忧：这只验证旧入口能否重现差异，不能单独识别 wrapper、启动顺序、缓存/JIT、真实图像输入等原因；若仍不保存完整输入，可能浪费最后两样本。

并行有界任务：
1. 从冻结源码和任务私有 launcher 确认最小可行接入点：能否保留 scheduler 实际发出的完整 policy 请求（RGB/state/memory/prompt及实际请求选项），在 infer RPC 返回之后才复制/写盘，避免在模型内部插桩，且不额外 get_obs/reset/infer？指出参数是否被异步复用/修改及只保留引用的风险。
2. 核对 execute/clear 在 logical step0 的真实安全语义，以及沿原 BenchmarkRunner 将两臂各限一次 query、避免第二 episode或重试/额外 warmup 的最小办法。明确原调用顺序能保留到什么程度。
3. 评估这两个样本能支持的结论与不能支持的归因；最多列关键阻塞，不扩大为框架开发或通用审查。若保留输入需改变 pre-RPC 工作，明确变化及取舍。无需独立获取真实 key，此次禁止碰模型/JAX；不能将 stream/call 计数称为真实 key。

C3 SSH wuwen-4090-3，只读 runtime：/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914，OpenPI 0ce566bd34f99cb4775422f012ab67c16aa53885、bridge ffa122494c19e1c0154e877010f7b470967ccfc6、RMBench 6abebf08d084d0be43aa56ebe158dc8395fa58e4。作者证据与工具：/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/{tools,alignment,captures}。本机对应作者源码树 /mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/{openpi,robot-bridge,RMBench}。

尽快给出紧凑报告与源行号，发布 report 后结束 turn，由 Manager 制定最终实施合同；不等待 GPU 或做科学审稿。
