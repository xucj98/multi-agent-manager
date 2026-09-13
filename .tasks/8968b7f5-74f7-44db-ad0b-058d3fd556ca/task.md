# P0诊断记录接口：状态原始输出、动作和RNG的无行为改动采集

## 当前裁决：补齐已验收的首次 infer 90 秒配置，再做一次有界工程验收

Manager 已核对报告 `2c2996f8fc8b850b4ec68822ec90dc3f255cfc72`、C2 实际 command/scheduler config、policy log，以及 failure receipt 和其中 19 份引用文件的 SHA。接受此次失败是首个 policy RPC 在 30 秒 deadline 前没有返回，记录为 `policy_response_missing`，不构成接口 GPU 准入。旧失败及所有记录保留。已通过的 renderer gate/替代 CUDA smoke 不重跑。

实际 J/S scheduler_config.yaml 都漏了 `params.policy_first_infer_timeout`，因此落回 30 秒；已验收 bridge f962 的这项功能在当前 e147 中仍完整存在，P0 override 调用父类路径。原评估 task e690 的既有独立准入为首个 infer 90 秒、后续 30 秒，并已有冷启动 XLA compile 27.232 秒和成功 smoke 证据。这是此次诊断入口遗漏已接受运行设置；当前 PTX 日志仍不足以证明全部耗时根因。

授权 terra/max 执行者在本机准备本 task 的 v2 配置/launcher，只补 `params.policy_first_infer_timeout: 90.0` 及必要的新输出位置/证据身份，保存相对 v1 的 diff/hash。使用全新 result、diagnostics、manifest/config 副本目录，保留 v1 原件及失败 receipt；不得让新记录覆盖同名 episode/query。三库冻结版本、C2 GPU6/ports、环境/权重、H50/K30、episode 0/1、seed 100000/100001、query 1、2 records/64 MiB 均保持。核实 launcher 实际传入新 config，首个请求日志明确 90 秒，后续仍 30 秒，不额外 infer 预热或改 RNG，不新增 timeout API/依赖/共享 cache 改动。

在资源预检后允许 J 一次新的两集 smoke；完整 J recorded 验收通过后，继续原已授权的 J 同输入/实际 key/noise off/on 配对及 S 两集 smoke/配对，S 也使用相同首次 90 秒设置。各阶段保持原有完整性/行为等价合同。新失败保留首因，不循环增加 timeout 或重跑；实际完成后归档 jobs、发布紧凑报告。预计超过 30 分钟的程序登记 MAM，等待长进程时结束 turn。此次是明确配置修正后的有限恢复，取代此前“J 不重试”的停止边界；不启动 HF、formal100 或机制采样。

## 当前继续：Manager已核实uv软链来源，替换错误路径断言后恢复工程验收

Manager已亲自只读核对C共享部署及稳定installer，确认旧worktree_env_smoke.py以解析后路径含site-packages判来源，与C installer显式--link-mode symlink不兼容。P0 task环境中的nvidia_curobo0.7.8安装在本task venv，geom_cu词法路径在该venv/lib/python3.10/site-packages，真实实体在uv/archive-v0/UYbDTNQF-bGDe1JmV92NN。扩展13,367,808 bytes，SHA256 `874b95cb65d84eeb0a84562482de7551638f7c9974d3323b152142476f8abb01`，与installed RECORD的SHA256以及稳定wheel内同名成员逐字节内容一致。稳定wheel `/mnt/public/xcj/Projects/state-vla/.cache/curobo/wheel/nvidia_curobo-0.7.8-cp310-cp310-linux_x86_64.whl` SHA256 `780a878713cad48043b4537268c860e52393ddeb46709a6377409f9c65f4f988`。原smoke脚本SHA256 `589733e0d89f16880303a6bb02c4573348496e7f53805537def5e1cafaab9b21`。因此这一次路径字符串拒绝是环境检查误报，尚未执行的真实cuRobo CUDA distance仍必须完成，不能把来源核对当成CUDA运算通过。

Manager也已重新计算并匹配总manifest f83efd753546825b3df2a09f006b0674cc1994ee6efeabe0908df5c9fe7ab23f、40-reset receipt f67665446952f080f43e20a8219942d584fe448da55e49f0b66543c0f1d95451及失败log cfe2d0e9f68d4407cc1026968509db89cc0403c8639eeea5c1ce2bc26f8702ba，接受C2 GPU6 renderer gate。此前允许实测选空卡的范围覆盖GPU6，无需回到已占用GPU0。

授权在本机准备本task自有的smoke验证副本，只把上述路径字符串断言换成真实安装归属与内容核验：实际geom_cu.__file__词法位置属于本runtime venv（不要resolve解释器）、distribution安装来源/RECORD匹配、实际扩展与上述已核对稳定wheel成员hash一致；其余SAPIEN render、CUDA get_pose_distance、synchronize、finite与距离阈值完全保持。保存原脚本hash、仅该断言替换的diff和新脚本hash/命令，在C执行冻结副本。不得通过全局关闭assert、修改Path.resolve/重装依赖/改共享cache或源RMBench绕过。该替代检查是Manager对具体误报的裁决，不是将原失败标PASS；原日志/manifest保留，新增独立receipt。

该实际smoke通过后，按之前已批准合同直接继续J/S各2episode诊断smoke和相同输入/key的GPU off/on配对，无需再等一次Manager许可。不重跑40-reset，不扩大模型/episode/cap，不改已review源或HF runtime；若真实CUDA运算或新步骤失败，保留实际首因后报告。沿C2 GPU6/19460,19462核实资源，预计>30min程序登记MAM，完成收尾/归档并发布当前状态置顶report。请把“来源核对通过”“替代smoke实际通过”“模型/诊断验收”分开记账，不能合并成一句GPU全通过。

## 当前执行：P0代码已验收，C2 最小 GPU 验收

Manager 已接受独立 report `2fb0db335606ce18e2590c3be35e002f9f4c8046`，并直接核对 live ingress 集中检查及既有真实J/S路径。代码准入版本：OpenPI `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`、bridge `e147f600dc4329f330a6e2eb0335150b5b3093a3`；本轮不再改功能。此节取代之前CPU-only范围，授权你（terra/max）接续本TASK-ID的最小GPU验收，不派其他agent。

先读 .local/wuwen-4090.md、C稳定根README、相关库AGENTS。C1仅创建本TASK-ID的全新独立部署三树，实际GPU优先 C2 GPU0；若该卡不满足显存/资源要求，可同主机选择实际空闲且满足既有renderer条件的卡，固定映射后执行并记录。不得占用 C1 GPU1/2 的T formal或C3 GPU0的HF工程；C共享文件系统，不能改任何活跃运行树。RMBench沿已验收 `f401f5279c95451eb424ac98b831bab5552b2120`，不混 HF 的3库版本。沿稳定worktree环境/renderer/systemICD，检查C2既有gate证据；不匹配时按既有有界生命周期gate确认，不自行改驱动/依赖。所有代码/配置/验收脚本在本机准备，C仅运行冻结副本。

Manager冻结工程样本为 put_back_block train0 的现有 J(full_t_plus_1) 与 S(serial_lag30) 20000 checkpoint。从eval task e6908de7的已验收路径和C现存清单只读定位，核对metadata/训练来源；不新训练、不改模型、不重传已存在资产。本次只验证记录接口，不用于成功率或机制结论。

每个模型最多一个新的2episode技术smoke，环境种子100000/100001、有/无视频，H50/K30原协议、无HF/reset新协议或状态干预。只对episode_ids [0,1]的query_ids [1]采集、max_records=2、每条64MiB，独立空目录。按真正已接受的episode身份传审计信息，不触发二次环境reset。另在同模型同一实际输入上做logging off/on的有界GPU配对（同初始action key、同显式noise或同采样key），比对actions/state/最终RNG，不能对两个随机执行轨迹只比成功率。允许任务自有小型验收脚本，不扩公共接口或新建框架；无须循环重放或增加episode直到满意。

每条产物运行既有validate_query_diagnostic：要求真正recorded、JSON/NPZ链接和内容验证通过，检查S真实logits/selected/action-condition、J原始坐标/decoded/实际execute slice以及真实生命周期。建立或复用经重算的run-level checkpoint权重内容manifest（不能仅目录/mtime/metadata哈希），链接运行源码/参数/episode/query；权重哈希只做run级，不在query热路径做。记录模型推理与诊断复制/IO延迟、容量峰值、缺失边界，仿真暂停不代表真机实时等价。

结果放本TASK-ID隔离的技术结果组，工程产物保留，不混入原42批正式结果或HF36批。失败只保留证据并报告首因，不自动加大资源上限/重启formal；若需要变更已review源码，先向Manager提供最小复现。预计>30min的部署传输/GPU程序登记MAM真实PID，最终核对owned children/ports退出并归档jobs，发布当前状态置顶的紧凑report与artifacts/hash后结束。完整GPU证据交Manager验收，再另行设计机制采样；这次不启动正式100或写科学结论。

## 当前窄修：live array_ref 的录入与离线状态不一致

独立 report d1fffd76062e9b8b0ec36dd3b9506df9be18b892 已确认 b169 的真实 J/S Policy→recorder→validator 有效、Memory-v1 完整性和 scheduler 预算预检修复。Manager 已直接核对 _Externalizer/sidecar checks 与真实 Policy.capture：reviewer 将 raw action ndarray 手工替换成 array_ref，录入为 recorded、离线缺 NPZ key 后拒绝的现象成立；尚无证据表明当前真实 Policy producer 会生成这种 descriptor。将其按 P2 录入校验一致性窄修处理，不作算法失败或无限硬化依据。

从当前 clean bridge b1695f7f04050836a764c1e85a6db163e3526ada 修：在 live policy sidecar ingress 对预先 externalized array_ref 统一明确拒绝为 incomplete（或等价保证录入的数组与本次 NPZ 实际绑定）；离线已落盘 array_ref 的正常解析继续有效，真实 ndarray/非有限 logits 不受影响。优先少量集中检查，不再增加各字段重复的数百行 validator，不在 Policy 开销路径新增复制/RNG操作，不改 HF。OpenPI bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6 保持不变。

验证本次 raw-action 描述符反例、一个其他必需数组入口、合法真实 serial/joint 及离线完整性；保留此前容量/lifecycle 默认路径结论，无需机械重跑全库。交 clean commit 和紧凑 report 即可，仍不执行 GPU/正式评测/训练。GPU 验收由 Manager 根据完整已验科学路径、离线验证及实际运行合同裁决，不随意把任意人为非法 fixture 定成所有工程工作的 blocker。

## Manager 增量复审裁决：memory 部分完整性仍需窄修

你已交付OpenPI bc7603c5 / bridge fa62a9fe，独立review afe0仍在进行。Reviewer复现：把有效serial sidecar的memory缩成仅{"representation":"serial_token"}，recorder仍返回True、写status=recorded且validate_record通过。Manager直接核对fa62a9fe的_complete_sidecar_error只检查非空representation，并与bc7603c5的真实memory evidence生成器比较，确认遗漏。该生成器还会自然返回metadata_incomplete/missing_key_state_output等不完整状态，不能因为总sidecar写了complete就称完整。

接受为P2，但它阻塞本任务完整证据准入。请只在必要路径按实际representation核验必需memory证据：S的key_state_logits、selected_ids、action_condition_state_ids及condition来源；J/T的raw joint memory坐标、decoded IDs及可读decoded状态/字段合同。数组类型、维度和字段关联按真实wire验证，不用类别坐标伪装logits。明确缺失/unsupported/metadata_incomplete或旧sampler无法独立提供selected IDs时，保留可见的incomplete状态和原因，不虚构值、不改变原动作/RNG。

同一schema规则必须覆盖录入侧与离线validate_record；伪造status=recorded不能绕过。补最小S/J局部缺失/错误维度和有效样本回归，至少一条覆盖真实生成器的incomplete输出。不要全面重写记录器或扩展无关字段，不依赖HF分支、不运行GPU。提交下一组精确clean commits并发布report；reviewer继续检查本轮其他路径，不需等待整个review结束才动这项已确认修复。

Manager已另外直接核对fa62a9fe._attach_query_diagnostic：episode_info/episode_status/provenance在begin_query容量预检前已deepcopy，接受这个顺序遗漏为需窄修的P2。沿现有同步记录路径先做array预算检查再复制；不限制真实正常输入、不扩展记录框架。数组超限应显式小型cap记录，不伪装成写失败。至于action-dispatch预算是否需要Policy侧额外预留，暂待reviewer用本轮合法H50/K30/robot_dim14输入确认，不能把非合同4096行fixture或msgpack容器开销直接作为实质超限结论。

Reviewer对未提交草稿的tuple返回/array_ref、representation none与metadata匹配、ID/label字段关联提示属于已有完整性合同的复查点，尚不是冻结版本独立结论。作者在本轮定稿前自查并一次性提交；reviewer后续只按精确clean commits复核，不以持续观察dirty diff延长本轮。

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

## 完整性 P2 的范围裁决

Manager 核对 status/context-only 判定与 checkpoint provenance 后：将空 sidecar 误称 recorded 的问题纳入最小修复。只验证本 schema 必需的证据分区/版本及缺失语义，让 recorder 和 validate_record 对相同残缺 sidecar 给出一致 incomplete/明确错误；不开发通用 schema 框架。

checkpoint 的 actual_path/step 只是位置身份，当前代码不提供权重内容身份。本轮不新增逐 query 权重哈希或修改既有 provenance 后端；文档/记录显式标注该界限，并要求后续正式诊断的 run 级验收关联已核验的 checkpoint manifest（若现有 manifest 本身没有权重内容哈希，也不得称强内容身份）。没有该外部身份核验时，不能仅凭此 sidecar 宣称完整可复现。此项作为后续诊断准入条件记录，不阻塞当前 CPU 生命周期修复交付。
