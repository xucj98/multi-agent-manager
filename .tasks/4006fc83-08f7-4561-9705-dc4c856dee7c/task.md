# 高频状态与replan独立审查：先核对实验合同，后验代码准入

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
