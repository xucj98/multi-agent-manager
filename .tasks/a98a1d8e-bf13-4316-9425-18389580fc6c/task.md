## 2026-09-21 新Manager收尾裁决（当前有效）

状态：接受已交付代码/CPU审查结论；训练准入仍未通过。

接受发布报告ae03d59b对OpenPI66d9253/RMBench f402bab/bridge20dae84的代码与五任务CPU输入审查及单卡OOM结论；不是GPU恢复或正式训练准入。作者e34ba9b3后续双卡OOM证据已在交接中记录，本review不冒称已独立验收该新增收据。保留latest手工worktree和evidence，后续先完成证据稳定归档；V资源/合同改动与用户讨论后另行裁决，不自动重试GPU。

本轮依据用户要求先交接并讨论计划，未启动新的训练/评测；不把无job自动解释为科学验收完成。

---

# V工程独立审查
先读AGENTS.md和源任务 e34ba9b3-34e2-4df4-92d8-4cea983b7303 已发布合同/报告。review基线为交付OpenPI96e37e840f196d3b0945994d9a9bb5980d25ca58、RMBencha03fd1c3a40ac89542b7afe80d7188acd3dc2bd9、bridge20dae84e5fc2e48f93e72b5c1b8a0001071fec94；独立worktree，CPU测试，不改实现，不启动GPU。
核对训练与推理初始锚点+最近4查询+当前图像的真实时间对应、去重/mask是否被模型实际使用、无跨episode或未来泄漏、frame retry/reset原子性、三相机顺序与图像增强一致性、H50/K30、14D与pad32、bs32/20k/seed0合同、checkpoint元数据与恢复、旧N/S/J路径兼容、bridge真实reset与额外RPC/缓存风险。尤其检查训练query行筛选是否改变action target/episode尾部；从任意训练行回溯历史是否正确，不只看测试镜像实现。
核查两步technical smoke无法误用为正式模型。空manifest和九行占位不是任务已接入，也不接受空dryrun为运行时准入。评估固定18图mask是否仅屏蔽注意力却仍计算全部图像，资源估计分开理论与实测。重点验证必要边界，不重复无关全库测试。
发布可定位问题及严重度、复现依据/测试，明确代码准入及未验证GPU/实际数据范围；科学设计/资源裁决由Manager负责。不能自行改变history/bs/相机/图像分辨率或任务schema。
