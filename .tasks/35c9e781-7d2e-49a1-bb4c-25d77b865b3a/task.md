# FP32与BF16文件存储对照：旧full30k模型100rollout验证

## 目标

用户要求将已训练的FP32模型转存BF16，实际比较rollout。你负责独立评测，CPU导出与参数逐值一致性由ad6bb77e-3892-4730-ae1a-7d9cd99a5728负责。问题是“同一个模型，仅改变权重文件dtype，沿原本就将权重加载为BF16的推理入口，是否改变闭环表现”；不是比较真正FP32与BF16推理，不重新训练，不改变模型/解码/采样/控制代码。

先读MAM AGENTS与任务/工作区/进程说明；用mam workspace add为RMBench、robot-bridge、openpi建立独立worktree，严格基于F0对照的版本：
- RMBench f022badd11228e5763a301339a5d1fe5574962b4
- robot-bridge bc842036e3735390f35fe1138aa7b19f5ae2f95b
- openpi 58d6f2155acc3af03017677bb3f536101e6699f4
阅读三库AGENTS、RMBench docs/guidelines实验规范、bridge docs/design/conventions.md。不要切换或改写其他任务的运行树。所有新增源码修改先报告必要性，优先通过现有runner/manifest/命令完成；不新增通用launcher或兼容框架。

## 配对参照与输入

FP32源checkpoint：/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000。
已完成参照run：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0，92/100。读取其config.yaml、command.txt与final_review_0100.json来固定实际运行协议，不从名字猜默认参数。
导出目标：/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000；目前可能尚未完成。先做CPU准备，读取ad6最新发布report确认导出完成/原metadata继承/实际dtype与逐值比较后再使用。原FP32模型和导出模型均只读，不自行复制或再转换一份。若数值验证不一致先报告，不把性能退化当随机性忽略。

固定rearrange_blocks、demo_clean_eval、H50/K30、所有memory字段选row30/index29、同一个旧模型/原norm、原策略随机种子和采样默认值、accepted seeds100000–100099、前5个正式视频。同GPU上的sim/infer；保留视频逐步渲染、无视频既有加速。只允许权重文件dtype及对应文件hash/位置、独立run名发生预期改变；导出metadata新增记录属于留痕，不改变模型语义。继承原始转换/训练metadata及导出command/commit，不能把导出伪装成一次新训练。

新模型没有memory_config，复用F0的legacy loader/feedback selector及底层BenchmarkRunner，不调用限制20k新schema的run_memory_schema_eval.py。原run_f0.py若固定了checkpoint路径，可直接复用其生成的底层runner命令，并在任务.local下派生只替换checkpoint/audit路径的manifest；逐项列差异供Manager核对。不要修改或绕过既有audit/metadata/smoke匹配验证，所有派生输入由现有config_source继承进run。

## 资源与步骤

GPU0预留给本对照，从Manager确认F0 row1结束并移交后生效；当前GPU0/1仍有F0、2–7和远端八卡都在训练。当前只允许CPU准备，不提前占GPU。GPU释放后，同一张本机GPU0串行：
1. BF16模型自己的smoke共两次rollout，一次视频、一次无视频，检查模型真实加载、协议/选行、结果、视频帧数、全部metadata/退出与GPU实际归属。不能借用FP32模型的smoke。正常任务失败不等于基础设施失败。
2. 通过后沿干净且固定版本启动正式100；不拆分、不与其他run共卡。预计超过1小时的runner必须可靠detach并立即mam job add登记实际host/PID。相同代码无需人为提交空commit。
3. 到50条检查与FP32源参照的可比结果，超过10个百分点就核查协议/异常，继续保留原run失败结果；100后逐seed配对统计，给成功数、两方向discordant数量和失败类别。不能单凭一组100ep的相近成功率宣称统计等价；结合参数逐值证据说明验证边界。

产物RMBench/eval_result/memory_chunk_20260910/precision_rearrange_full_row30_bf16_100ep_seed0，smoke独立同组leaf。不要输出到robot-bridge/eval_result。Formal完成并核验继承副本后清理自己smoke、.local临时输入和无用日志；BF16导出checkpoint是有价值成果，保留。处理job后发报告，工作区待Manager归档。

先交CPU准备简报，列三个SHA、底层命令/manifest预期差异、导出依赖状态、预计GPU时间；不重复已有模型50step训练/大范围CPU测试。正式完成后只在本RMBench的experiments/memory_chunk_20260910/README_precision_validation.zh-CN.md写结果说明，避免与F0 owner修改同一README。报告含task_revision、真实产物、完成/未完成与commit。保持简洁，不另造provenance系统、不派agent。

## 12:55 CPU交付裁定

三库版本、BF16路径/hash与模型协议准备可接受，启动前补齐两项manifest/留痕细节：
- 当前派生run.baseline仍引用历史93/100及55.1ep/h，本次主配对参照应是已完成F0 row30的92/100，配置、命令与诊断路径也应明确来自该run；原历史参照可保留为继承背景，但不能在最终报告或中点比较中冒充此次FP32对照。更新这一诊断/来源字段不改变policy协议。近期实际F0吞吐约38–39ep/h，资源预算先约3小时，后续用自己实测更新，不沿旧55.1排2小时。
- 私有manifest/evidence最终必须随run留下完整文件。当前config_source仍指历史单个config.yaml，不保证新增hash-evidence随现有recorder继承。参考已验收的新schema入口的Audit别名+config_source目录做法，用任务私有输入目录作为来源，并在其中保留本次FP32参照的config/command小型metadata副本。通过既有inherit_metadata做一次CPU实际复制检查，确认新manifest/evidence及基线config/command均进入lineage；不更改公共runner，不仅凭hash摘要就删去唯一输入文件。正式smoke时再次确认真实输出继承。不要把私有目录放到checkpoint内。
修正后给短报告/差异确认即可，不重复权重全量数值比较。GPU0仍待Manager移交。

13:04 GPU0已正式移交：F0 row1于12:55:46完成100，最终all_owned_processes_absent=true，GPU0/19300/19302释放证据gpu0_handoff_verification.json已由Manager核对（F0 report0e41481b）。你的任务获得本机GPU0使用权；GPU1仍为F0 row50，其余卡仍训练。完成上节CPU来源/继承修正和检查后，可以开始BF16自己的两集smoke；按既定门禁通过后自主启动正式100并登记MAM job，报告实际启动和首条检查。不要等待新的用户许可；遇到实质协议/产物错误先定位报告。正式整个run冻结三库及私有输入。50条/完成时做事件检查，普通监控约小时。


## MAM 查询更新（2026-09-10）

系统 MAM 已更新：`mam task list` 和 `mam job list` 为带表头的简表，无 --json；完整task信息使用 `mam task status <id>`，实时job结构化详情使用 `mam job status <job-id>`。`mam task show` 仍默认Markdown，保留 --json。`mam task status` 仅显示保存的 job 状态与 checked_at，不刷新进程。按既定频率监控时使用 `mam job list --task 35c9e781-7d2e-49a1-bb4c-25d77b865b3a` 获取实时进程状态，再结合已有日志检查进度。训练/评测协议、GPU 分配与检查频率不变。


16:01接口迁移：不要再将job list输出按JSON解析；用task status里的jobs取ID，再逐个job status获取实时结构化结果。既定监控频率不变。新增mam wait jobs/list/stop可按需使用，自动CODEX_THREAD_ID；停止等待不影响实验。
