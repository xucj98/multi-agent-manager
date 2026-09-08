# 场景与时序推演

仅做设计审阅与定点只读核对，不修改业务代码、不创建环境/worktree、不运行GPU或训练。你是无历史上下文的 gpt-5.6-terra max。先按 MAM AGENTS/README 获取任务，读涉及库的 AGENTS。

审阅材料：robot-bridge/docs/design/shared-memory-schema-and-scheduler.zh-CN.md，固定草案 commit 2196483（用 git show 读取）。相关仓库位于 /mnt/public/xcj/Projects/；规范为 robot-bridge/docs/design/conventions.md。

用户约束：同一 schema 描述 memory 语义及初始状态，可分类也可回归；编码/loss/normalization/layout 不属于 schema。wash-cup 一个当前 phase、drawer 两字段、仿真多字段；共享训练/推理/offline/scheduler UI。converter 归 policy 库，原始数据由环境/数据方提供。扩展重点是 scheduler/UI，不能默认给两端server建立插件体系。保留 wait_condition get_obs、action chunk、UDP遥操作、takeover；scheduler持context，policy reset，无session。旧full反馈连续值不得为统一schema擅自量化。只读评估，不把旧agent建议当用户决定。

读源码仅围绕发现的缺口取证，不做全库搜索或重复读取；正文≤300行，应能指导实施。质疑要给出具体失败场景、所在节及最小修正；允许结论为删除一项设计。不要泛泛建议更多抽象/版本机制/参数。汇报要区分阻断实现、可简化、需要用户实验语义选择。报告用任务规定的report.md发布；Manager会逐项裁决，第二轮通过更新任务再次通知。workspace暂留等待复核。

专门推演四例：wash-cup单phase（标注空白/label6）、drawer双字段、RMBench多字段、连续position/rotation。每例贯穿转换→训练→ckpt→infer→feedback→offline/UI，明确数据类型与时刻。重点检验full逐步与serial逐query的差异；人工修改其中一字段不破坏其他连续context；异步延迟/部分执行/takeover/reset；真值不泄露给普通推理；初始未知值编码；mask/训练head梯度。必要时定点查看robot_bridge/scheduler/openpi.py、openpi_offline.py、openpi_simulation.py和OpenPI模型/数据转换代码。不要只核对文档关键词，给出可以执行的具体反例与最小修正。职责/依赖删减由另一位reviewer负责。用简短场景表列通过或缺口，阻断项优先最多5项。

## 第二轮定向复核
固定审阅 robot-bridge commit dfc487d 的同一路径文档。Manager 裁决：
- 接受时序必须明确，但不将真机改成按执行位置反馈；保留 real/drawer offline accepted-first，sim 执行位置反馈，serial accepted-query，并列具体表。复用现有执行证据，不新增真机 get_progress/回执要求。反馈策略属于 scheduler run config，模型 cadence/监督时点属于 representation。
- 接受独立 mask、因果填充、known/valid、loss 分母及旋转等价要求，已补充。wash 空白/顺序为待用户确认的数据默认。
- 字段 lock 采用 infer request 的 locked_fields 子集；adapter 仅修补输出中锁定字段并生成同源显示 values。一次性 override 只作用输入，同 epoch 第一次反馈后消费；锁定/解锁/修改均使旧 epoch 失效。无需额外 merge RPC 或 scheduler 编解码。
- 接受普通 replay model context 与 oracle 明确隔离，补充真值扰动测试。
请具体检查三种时序、锁定部分字段和空白监督是否还存在阻断（至多三项）。以保留历史算法行为为目标，不能把更改真实执行机制作为本轮默认修复。追加第二轮报告，更新 task_revision 并发布；纯只读，不创建环境。
