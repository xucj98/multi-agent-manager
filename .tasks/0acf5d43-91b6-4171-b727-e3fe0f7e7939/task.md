# 高频状态推理与偏差触发replan：复用checkpoint的推理实现

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
