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
