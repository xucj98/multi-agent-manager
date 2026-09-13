# 高频状态与replan独立审查：先核对实验合同，后验代码准入

## 职责与范围
你以gpt-5.6-terra/max独立核对源工程0acf5d43-91b6-4171-b727-e3fe0f7e7939的已发布算法合同及之后代码，不设计论文主张；Manager亲自裁决。源工程仍在写代码，暂未发布report，因此本任务先创建独立审查准备，不伪造已存在代码review快照。先读AGENTS、mam task show源task最新c2818247及eval task e6908de7最新da1715e8；已有S/J/T baseline为OpenPI a869498、bridge f962，按需独立worktree固定对象。

现在可独立做：检查高频J rolling的绝对target时刻和当前cache消费、fresh row0 vsold rowd窗口、trigger时动作RNG与probe RNG、原动作queue实际前缀/清后缀、S重复同帧状态递推及lag变化、T endpoint拒绝、额外get_obs光照/RNG/提示副作用、shadow等价和正式baseline可复用条件。指出实质bug、无法支持的科学归因或缺少的最小对照；不要仅因S lag变化要求重训，用户明确只做推理变体且报告分布变化。

第一轮两任务J HF-fixed/HF-event优先12正式批，再S HF-fixed6和J HF-periodicK10 6，默认3eval×100，0训练。只读检查是否有错误时间标签、未来值提前入cache、用类别编号做距离、伪造confidence、把采样差异当物理事件、动作probe影响baseline等风险；不要代替Manager凭偏好改变阈值/研究范围。

源owner交付干净commit后，由Manager通知准确diff再做独立代码复审。可先交合同级发现给Manager与作者，不等待源码或高频poll；代码未到时正常结束turn，后续nativefollowup续办。最终report分别列合同审查与代码审查对象/结论，代码PASS只代表准入GPU smoke，不冒称eval完成。不得改作者树、运行GPU/正式eval、训练、部署生产。若独立验证修改仓库用mam workspace add，读对应AGENTS。预计>30分钟程序登记MAM。

Manager接受你提出的pending旧forecast覆盖/旧chunk取消后误完成、invalid/gap打断streak及duplicate必须probe前短路等问题，已将其写入源task准入要求。RNG隔离原合同已要求，仍是独立复核项。另已采纳eval owner事实：900000工程seed取消，直接沿现有eval0 smoke100000/100001、独立工程目录且不据分数调参，正式按每配置/seed匹配门禁；避免无必要新增CLI。后续按更新后的源task验代码。
