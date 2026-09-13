# P0诊断记录接口：状态原始输出、动作和RNG的无行为改动采集

## 目标与职责
你使用 gpt-5.6-terra / max，负责实现和验证。Manager 负责论文主张、实验设计和最终裁决。先读 MAM AGENTS、README、.local/README，再 mam task show 本 TASK-ID 和相关库 AGENTS、开发/环境说明。原审计任务 f987cfb5 已归档，其交付现保存于 /root/Documents/task-state-vla-paper/docs/audits/20260913-trace-inventory/；不要使用已删除的旧 workspace。

现有日志缺少原始状态输出、动作与 RNG，无法据此进行同一输入/随机数的状态敏感性诊断。实现默认关闭、显式选择 episode/query 的最小记录接口，提供后续复现所需证据。本次仅代码、CPU 验证和 dry-run 方案；不开展新 GPU rollout、正式评测或训练，不部署到运行中的 C 集群 runtime，不实现状态干预。

## 冻结基线与范围
通过 mam workspace add 建立独立 worktree：OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；robot-bridge f9626636c4776d8eb15f9c556775cb2d12c000e5。必要的启动参数贯通优先在两库完成；确需 RMBench 修改时先报告具体原因并固定既有正式 r3 baseline，不能隐式使用其他开发树。不要修改原运行树、模型、数据和正式结果。

优先沿既有 policy/scheduler trace 路径添加窄接口，不建立通用日志框架。限制记录数量、数组体积和存储范围；完整输入可采用有校验值的独立文件引用，不能仅存无法复现的摘要。

## 记录合同
每次选中 query 记录版本化 schema、checkpoint 与代码身份、episode/env seed/query 链接，实际推理输入（图像、机器人状态、token、memory；区分变换前/后，保证可复现），及下列证据：
- J/T：联合生成的原始 memory 坐标和解码结果，不能称为分类 logits。S：真实 key_state_logits、最终选中的 IDs，以及实际用于 condition action 的状态。
- 原始完整 action chunk、输出变换后的 robot actions，shape/dtype/单位；scheduler 的动作下发/变换关联需说明覆盖到哪一层，未观测的 controller 内部量不作已记录声明。
- policy RNG split 前、实际 sampling key、split 后状态，以及调用方显式提供的 noise（若存在）。不能为了记录额外 split 或生成新 noise。对未显式供给的采样内部噪声，保存足以重现的 key/算法身份，不虚构直接观测。
- scheduler cache 前后、消费的 memory 行、accepted/discarded/terminal progress、planned K 和有观测支持的 actual K。未知为 null；尤其 S 旧 trace 的 actual_k=0 是未填充，不等于未执行。
- wall/monotonic timestamp；已有 infer timing 与新增 logger 开销分开，说明异步设备执行下时间含义，不改变默认同步行为。

记录不允许改变 input、decoder、采样 RNG、数组内容或执行策略。启用记录会有可测 I/O 开销，不声称物理实时轨迹完全等价；默认关闭时维持既有协议/输出，不添加必需字段。读写失败策略明确且有测试，诊断缺失需显式可见，不能悄悄伪造完整证据。S padded logits 含 -inf，JSON 必须严格 finite，原始数组可用支持非有限值的格式并在元数据标注。文件哈希、episode/query/序号跨文件关联可校验。

## 验收和交付
提供最小 CPU tests，验证相同实际输入与相同初始 RNG 下 logging on/off 的动作/状态输出及最终 RNG 相等；多 query、J/T 与 S 路径、显式 noise、默认关闭、写入失败和 -inf roundtrip/严格 JSON、序号文件链接覆盖根据实现组织为有意义的测试。mock sample 必须保留真实 policy 的输入变换/RNG split/输出变换调用链；不能仅测试 serializer 后声称已验证 policy 行为。
发布 report，包含干净 commit、完整 diff 范围、验证命令/结果、示例记录和校验脚本、存储/开销界限、后续最小 GPU smoke 方案与尚未验证的界限。短 CPU smoke 无需登记 job，任何预计超过 30 分钟的程序按 MAM 登记。完成可执行工作后正常结束 turn，不轮询。Manager review 之后才决定 GPU 验收和诊断实验。

## 独立审查 P1 的 Manager 裁决

Reviewer afe0d0ee 已真实复现 J/T execute RPC 非ok后，diagnostic record 被下一retry obs提前关闭。Manager直接核对 SchedulerBase.run_iteration 的失败return不调用after_execute，以及 OpenPiSimulationScheduler._refresh_query_diagnostics 在 requires_execution_progress 且 next_consumption=None 时无accepted判断便close，接受此问题。当前 cb861d38/a2c7f80b 不准入GPU。

请仅修生命周期缺口：未被accepted的candidate不得因没有next_consumption就被当作已完成关闭；execute失败/后续discard必须被明确记录，或正确保留pending直到已知终止。不能记录actualK=0作为未知结果，也不能改变原retry/动作语义。添加保留真实run_iteration和controller非ok路径的回归，覆盖选中J/T、下一retry obs、下一build_act_request discard及terminal/reset时记录不丢失。协调reviewer给精确复现，完成干净commit、窄测试、report再由其续审；其他独立发现一并按具体证据处理，不扩展logger产品范围。

## 追加两项独立发现的裁决

Manager 已直接核对冻结 cb861d38/a2c7f80b 的调用链，接受 reviewer 的另外两项问题，和前项一起修复后续审：

1. 数组上限目前只在 bridge 的 record_policy_response 复制、externalize 后应用；begin_query 已复制 scheduler_input，OpenPI 也在无容量参数的情况下复制多个输入/输出快照并传回 sidecar。这不能限制诊断采集和传输开销。将预算传到实际采集端，在诊断专用复制/设备取回前按 shape/dtype/nbytes 累计预检；超限返回体积受控且明确 incomplete 的记录。明确定义预算涵盖范围及必要元数据开销，不将正常推理必需的输入传输算成诊断新增开销。用真实 Policy 路径和大图像/小上限验证超限时没有先生成巨大的 sidecar，同时保持 input、action、state 与 RNG 语义不变。
2. legacy full-state J/T 的 diagnostic_record_id 仅在 after_execute 才接到 dense candidate；execute 非 ok 后，下一 build_act_request 的 discard 收到 None ID，随后清掉 candidate ID，导致已选中记录永留 pending。需在 candidate 阶段正确关联、记录已知拒绝/丢弃并收尾；actual K 未知仍为 null。回归保留真实 legacy F0/full-state 调用链，覆盖 execute 非 ok、下一观测/重试、supersede 和 episode 结束，不改变控制器 retry 语义。

请与 reviewer 复用其精确复现；本次仍仅 CPU 修复和独立 review，未获 GPU 准入。
