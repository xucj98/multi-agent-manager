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
