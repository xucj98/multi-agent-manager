# 职责与冗余审阅

仅做设计审阅与定点只读核对，不修改业务代码、不创建环境/worktree、不运行GPU或训练。你是无历史上下文的 gpt-5.6-terra max。先按 MAM AGENTS/README 获取任务，读涉及库的 AGENTS。

审阅材料：robot-bridge/docs/design/shared-memory-schema-and-scheduler.zh-CN.md，固定草案 commit 2196483（用 git show 读取）。相关仓库位于 /mnt/public/xcj/Projects/；规范为 robot-bridge/docs/design/conventions.md。

用户约束：同一 schema 描述 memory 语义及初始状态，可分类也可回归；编码/loss/normalization/layout 不属于 schema。wash-cup 一个当前 phase、drawer 两字段、仿真多字段；共享训练/推理/offline/scheduler UI。converter 归 policy 库，原始数据由环境/数据方提供。扩展重点是 scheduler/UI，不能默认给两端server建立插件体系。保留 wait_condition get_obs、action chunk、UDP遥操作、takeover；scheduler持context，policy reset，无session。旧full反馈连续值不得为统一schema擅自量化。只读评估，不把旧agent建议当用户决定。

读源码仅围绕发现的缺口取证，不做全库搜索或重复读取；正文≤300行，应能指导实施。质疑要给出具体失败场景、所在节及最小修正；允许结论为删除一项设计。不要泛泛建议更多抽象/版本机制/参数。汇报要区分阻断实现、可简化、需要用户实验语义选择。报告用任务规定的report.md发布；Manager会逐项裁决，第二轮通过更新任务再次通知。workspace暂留等待复核。

专门审阅：三份配置是否有重复/循环依赖；memory-spec新package是否值得，是否能更简单；policy adapter与scheduler职责是否可实现；schema真机/仿真共用位置；checkpoint自包含与旧格式迁移；新增字段/编码需要改哪些文件；历史drawer converter/offline依赖能否迁出。逐个评估提出的概念/接口是否必要，提出具体删减替代。场景的执行时序细节由另一位reviewer负责，你不用重复完整推演。至少对比现有文件路径/依赖，优先指出最影响实施的5项以内问题，其余压缩记录。
