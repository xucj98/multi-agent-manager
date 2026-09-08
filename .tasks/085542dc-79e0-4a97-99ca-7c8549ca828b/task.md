# 职责与冗余审阅

仅做设计审阅与定点只读核对，不修改业务代码、不创建环境/worktree、不运行GPU或训练。你是无历史上下文的 gpt-5.6-terra max。先按 MAM AGENTS/README 获取任务，读涉及库的 AGENTS。

审阅材料：robot-bridge/docs/design/shared-memory-schema-and-scheduler.zh-CN.md，固定草案 commit 2196483（用 git show 读取）。相关仓库位于 /mnt/public/xcj/Projects/；规范为 robot-bridge/docs/design/conventions.md。

用户约束：同一 schema 描述 memory 语义及初始状态，可分类也可回归；编码/loss/normalization/layout 不属于 schema。wash-cup 一个当前 phase、drawer 两字段、仿真多字段；共享训练/推理/offline/scheduler UI。converter 归 policy 库，原始数据由环境/数据方提供。扩展重点是 scheduler/UI，不能默认给两端server建立插件体系。保留 wait_condition get_obs、action chunk、UDP遥操作、takeover；scheduler持context，policy reset，无session。旧full反馈连续值不得为统一schema擅自量化。只读评估，不把旧agent建议当用户决定。

读源码仅围绕发现的缺口取证，不做全库搜索或重复读取；正文≤300行，应能指导实施。质疑要给出具体失败场景、所在节及最小修正；允许结论为删除一项设计。不要泛泛建议更多抽象/版本机制/参数。汇报要区分阻断实现、可简化、需要用户实验语义选择。报告用任务规定的report.md发布；Manager会逐项裁决，第二轮通过更新任务再次通知。workspace暂留等待复核。

专门审阅：三份配置是否有重复/循环依赖；memory-spec新package是否值得，是否能更简单；policy adapter与scheduler职责是否可实现；schema真机/仿真共用位置；checkpoint自包含与旧格式迁移；新增字段/编码需要改哪些文件；历史drawer converter/offline依赖能否迁出。逐个评估提出的概念/接口是否必要，提出具体删减替代。场景的执行时序细节由另一位reviewer负责，你不用重复完整推演。至少对比现有文件路径/依赖，优先指出最影响实施的5项以内问题，其余压缩记录。

## 第二轮定向复核
固定审阅 robot-bridge commit dfc487d 的同一路径文档。第一轮三项阻断已接受：schema 内容/hash 单向校验；新增由 train config 导出的 inference_config 直接构造模型/transform，不依赖配置注册名；明确旧 drawer converter/backend/replay 迁移范围。接受具体 MemoryContext 与轻量数据契约包；删去无依据 Python 版本要求。
请只检查上述修订是否闭合、是否引入重复配置/实现不可行；尤其检查 schema/representation 与运行 feedback 策略边界：训练不绑定部署环境，采样提交策略在 scheduler run config。最多指出仍阻断实施的三项，或明确通过，避免扩展框架和新范围。将第二轮结论追加到 report，更新 task_revision 并发布；只读固定 commit，不创建环境。

## 用户最新澄清（覆盖冲突要求）
wash-cup 仅保留：存在子任务标注文件、无 label6、标签1–5各出现恰好一次的 episode；顺序不限。Manager 正在核对 full-state target 是 chunk-level 还是 frame-level。不能再把 accepted-first 默认当必须保留的正确算法；请在第二轮结论中标明时序表须以实际训练监督核对后修订。此数据/训练取证由 Manager 负责，不重复调查。其余定向复核继续。
