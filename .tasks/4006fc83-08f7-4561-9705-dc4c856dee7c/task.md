# 高频状态与replan独立审查：先核对实验合同，后验代码准入

## 当前增量复审：真实 recorder 与 child 身份修复已冻结（取代下文旧候选）

源 report `aac1cbd563f7a7aaf83fc0b161ee3dc4463f2959` 已发布；Manager 已核对作者三树 clean、准确 HEAD 和正式 f401 祖先，并直接检查 recorder/CLI 窄改。现在恢复独立增量复审：

- OpenPI 不变：`0ce566bd34f99cb4775422f012ab67c16aa53885`。
- robot-bridge：`a0f1d5035d77cea7cb300eb511ceb5cf3fd1a93d` → `552ea78f73e62fddc747d5d26e7e6c365fa00339`。
- RMBench：实际正式基线 `f401f5279c95451eb424ac98b831bab5552b2120` → `c99ec6a2c6df96ec8705b106b125935fce862052`。

复用本任务已有 OpenPI/bridge review worktree，clean 后只快进 bridge；用 mam workspace add 为本任务创建独立 RMBench review worktree，固定 c99ec6a2。源 workspace 创建时的 base 元数据为 2e，但最终 c99 确实包含 f401；按实际 commit 图审查，不把创建元数据当最终基线。无需重跑未变 OpenPI 全库，也不要合入 P0 logger。

复核上一报告 7d153938 的剩余 P1：真实 RMBenchResultRecorder 支持 rolling_evidence 路径、episode_diagnostics 保留文件引用；benchmark 已接受的 episode_id/seed 穿过真实 child CLI 到 writer header；身份只用于记录，不进入 reset_args，不增加第二次环境 reset。检查正常/异常 child 收尾实际留档、episode 引用可解析、header 与 accepted identity 一致，以及默认关闭不生成文件/新增开销。作者 seam 使用真实 recorder 加 child，独立检查其覆盖与边界，不以 fake recorder 或测试数量代替结论。

保留已通过的 RNG/时序/队列合同判断，按本次窄改核对回归。作者 bridge 522 passed/2 skipped、RMBench 4 passed 并非独立 PASS。证据仍须包含 truncated/incomplete 与最终收尾，完整性不足不能进入正式统计。最终报告列三库精确版本、独立验证、剩余限制及能否准入有限 GPU 工程 smoke。发现实质缺陷及时报 Manager；完成发布报告并结束，不追逐 dirty diff 或活跃等待。未经 Manager 裁决，不启动 GPU/部署/正式评测。

正式设计维持两任务 train0、H50/K30、interval5、0 训练；每 episode action 初始 key0 的 matched baseline12 加 HF24，共36个正式100批。旧 baseline/shadow 保持历史默认，不能将旧成绩当新 reset 协议直接对照；每 arm/环境 eval seed 有自身 matching smoke2。下文旧24批计划已被此36批合同取代。

## 当前轮次：修复已交付，按新精确版本增量复审

Manager已直接核对真实recorder与runner，接受新增P1：rolling_evidence kind不被真实RMBenchResultRecorder支持，调用在accepted episode try外；你复现的episode引用字段丢失也须修。已发布源任务要求最小真实接口接线及真实recorder seam测试，必要时许可独立RMBench f401f527窄改。继续其他增量审查，最终报告明确所有冻结库版本；作者下一clean提交到达再复核此项，不读取dirty diff替代正式结论。

Manager已接受你报告7d153938中新增的child episode_id/seed遗漏，作者必须建立记录身份而不增加环境reset；真实seam应检查benchmark reset一次、child不额外reset且header身份与episode record相符。另Manager直接SSH确认2e9677c..正式f401f527只有17行memory_schema_eval.yaml配置增量、recorder不变，故你对真实recorder的不兼容发现适用于正式路径，但最终报告仍需以实际冻结f401→候选身份/文件核对，不能把eb0546a整库称为已部署版本。作者获准取回缺失f401对象并保留该基线配置。

Manager已核对两作者树clean，新的准确交付为：OpenPI `4529a91c1f49a50c8710a7182e31ca5a32dfa05a` → `0ce566bd34f99cb4775422f012ab67c16aa53885`；robot-bridge `53f853aa71b80a7eadd9fb3092abe39c64df1149` → `a0f1d5035d77cea7cb300eb511ceb5cf3fd1a93d`。源报告ebbde890已发布。复用你现有独立review worktree，clean后将review分支快进至候选；不要重建重复树，不混P0 logger实现。

优先验证之前两个已接受P1及新matched协议：普通baseline真实infer/reset默认字段与跨episode action RNG保持旧行为；显式reset_episode_rng配置的baseline保持原SchedulerBase/MemoryContext/K30且不做probe，matched shadow不改cache/动作、独立probe RNG，与matched baseline多episode实际action/key相同。HF始终显式reset与正式合同一致，T拒绝维持，不拿新baseline/shadow互比代替旧默认兼容性。

新增持久化穿过benchmark→run_scheduler→episode writer：核对实际result目录/path引用、进程退出后可解析、raw/decoded/target/current-input/key/action/progress/trigger/clear/terminal/exception证据、frame/plan关联。容量4096事件的truncated+最终incomplete必须真实可见，正式验收不得把它视为完整；不能只凭样例JSON或get_status证明落盘。与作者沟通最小必要样例/解析即可，不建立记录框架。确认普通路径没有额外持久化开销；显式fsync延迟与仿真暂停边界如实说明。

作者报告bridge519+2skip，probe7，wire2+8deselected；这不是独立PASS。围绕增量风险做有意义窄CPU/实际文件路径验证，保留之前已通过合同结论，不机械重跑全库。代码通过只准入有限GPU工程smoke，正式eval还需Manager裁决及自身matching门禁。发现问题即报Manager；完成发布报告并正常结束。

## 职责与范围
你以gpt-5.6-terra/max独立核对源工程0acf5d43-91b6-4171-b727-e3fe0f7e7939的已发布算法合同及之后代码，不设计论文主张；Manager亲自裁决。源工程仍在写代码，暂未发布report，因此本任务先创建独立审查准备，不伪造已存在代码review快照。先读AGENTS、mam task show源task最新c2818247及eval task e6908de7最新da1715e8；已有S/J/T baseline为OpenPI a869498、bridge f962，按需独立worktree固定对象。

现在可独立做：检查高频J rolling的绝对target时刻和当前cache消费、fresh row0 vsold rowd窗口、trigger时动作RNG与probe RNG、原动作queue实际前缀/清后缀、S重复同帧状态递推及lag变化、T endpoint拒绝、额外get_obs光照/RNG/提示副作用、shadow等价和正式baseline可复用条件。指出实质bug、无法支持的科学归因或缺少的最小对照；不要仅因S lag变化要求重训，用户明确只做推理变体且报告分布变化。

第一轮两任务J HF-fixed/HF-event优先12正式批，再S HF-fixed6和J HF-periodicK10 6，默认3eval×100，0训练。只读检查是否有错误时间标签、未来值提前入cache、用类别编号做距离、伪造confidence、把采样差异当物理事件、动作probe影响baseline等风险；不要代替Manager凭偏好改变阈值/研究范围。

源owner交付干净commit后，由Manager通知准确diff再做独立代码复审。可先交合同级发现给Manager与作者，不等待源码或高频poll；代码未到时正常结束turn，后续nativefollowup续办。最终report分别列合同审查与代码审查对象/结论，代码PASS只代表准入GPU smoke，不冒称eval完成。不得改作者树、运行GPU/正式eval、训练、部署生产。若独立验证修改仓库用mam workspace add，读对应AGENTS。预计>30分钟程序登记MAM。

Manager接受你提出的pending旧forecast覆盖/旧chunk取消后误完成、invalid/gap打断streak及duplicate必须probe前短路等问题，已将其写入源task准入要求。RNG隔离原合同已要求，仍是独立复核项。另已采纳eval owner事实：900000工程seed取消，直接沿现有eval0 smoke100000/100001、独立工程目录且不据分数调参，正式按每配置/seed匹配门禁；避免无必要新增CLI。后续按更新后的源task验代码。

## 代码已交付：进入精确版本独立复审

源报告 83c8f2e20ad1f6ca40fc548e3159404a500c64a5 已发布。Manager 已核对作者两树 clean 且 HEAD 精确为：

- OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 → 4529a91c1f49a50c8710a7182e31ca5a32dfa05a。
- robot-bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 → 53f853aa71b80a7eadd9fb3092abe39c64df1149。

在本任务 workspace 为两库按以上交付建立独立 review worktree，读取各库 AGENTS 和开发规范。作者报告 bridge502passed/2skipped，OpenPI probe6+wire2通过；这不是独立验收结论。无需机械重跑所有无关测试，重点以真实 Policy transform/sampling、Scheduler run_iteration 和队列/进度合同验证关键风险，必要时补独立反例。

逐项核对源 task 最新7009b32c冻结合同：J绝对target与边界row4、固定原Z_a参照/2次偏差、trigger后仅弃未执行队列且正常动作RNG重规划；标准pending隔离；S prefix-only与边界单次递推；duplicate/stale/invalid/gap在probe前处理；T/混合target启动拒绝；simulation暂停与video/no-video观测副作用、raw/decoded/RNG证据真实且有界。

Manager 初读发现需优先核查默认关闭等价：Policy.reset 新增无条件回到 initial action RNG，而旧 Policy 没有 reset override；infer 对所有J请求新增 raw action copy/sidecar，对所有JAX请求新增policy_rng。请沿实际 backend/server reset 与多episode runner 调用链确认是否改变原 baseline 的随机流/协议/开销，不能只比“新代码baseline”与“新代码shadow”便宣称等价。此为待复现问题，不预设修复或PASS。RNG留痕目前 stream/call 是否足以关联实际采样key也需明确。

交付独立报告：精确commits、发现及严重级别/复现、通过和未覆盖边界、是否准入有限GPU smoke。任何实质问题及时发Manager和作者，先由Manager裁决再修，不修改作者源码，不启动GPU、不部署。可执行审查完成后发布report并正常结束，不活跃等待。

## Manager 已确认 P1 与正式对照裁决

默认reset改变跨episode action RNG的P1已由Manager真实Policy路径复现并接受，作者正在窄修。Manager另直接确认benchmark在100集循环外启动policy server，历史action RNG连续消费；故HF逐episode reset不能直接使用历史baseline成绩。按源task最新裁决，普通baseline/shadow保持历史默认行为；显式matched baseline/shadow使用与HF完全相同的每episode initial key0重置协议，probe流独立。新对照J/S各两任务×3eval共12批，总量从24增至36正式批、0训练，旧结果不失效但不作为新协议的直接对照。

增量复审最小显式配置：baseline仍原K30/MemoryContext，不引入中间状态消费；matched baseline无probe，matched shadow probe不改cache/动作；普通默认与旧版本、matched baseline与matched shadow分别做跨episode action key/动作等价。标清eval环境种子与固定policy初始key的区别。不要反复复现已接受的P1或因新配置等待而停止其他冻结代码审查；最后针对作者精确新commits给代码准入结论。

Manager已直接核对源53f853a及benchmark._wait/_record，接受你b55c30e的P1-2：rolling trace仅内存/get_status，episode scheduler退出后无法事后审计。已发布源task要求窄修持久化；不能仅末尾保存64条，须逐计划/事件保留完整前缀、trigger清后缀及terminal/异常，容量超限明确incomplete。待作者新精确commits，再做文件实际落盘可解析与跨进程收尾的增量复核；无需重复整库测试或现在空等。保留冻结报告作为未准入记录。
