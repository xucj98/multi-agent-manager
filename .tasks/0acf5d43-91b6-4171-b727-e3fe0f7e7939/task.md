# 高频状态推理与偏差触发replan：复用checkpoint的推理实现

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
