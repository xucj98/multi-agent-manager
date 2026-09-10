# Memory实验：F0反馈行评测

## 当前授权与验收

row30/GPU0已于09:29完成92/100，Manager接受最终协议、视频和退出检查；其job已归档。GPU0接续row1，GPU1的row20继续到100后接row50。两个GPU均已明确交本任务，按匹配2rollout smoke→正式100执行剩余配置，不再次请求许可、不重跑row30。四个run预算均已授权；新schema入口和drawer准备由任务e6908de7负责，本任务只收尾F0。

每个run完整100条在同一GPU串行，sim/policy共卡。使用本任务冻结入口run_f0.py；启动正式进程后登记真实host/PID的mam job，检查服务与首条episode，报告预计50条检查时机。两GPU保持独立端口/输出/缓存。远端八卡留新训练，不使用其他GPU。

## 固定代码与实验协议

复用本任务已登记三库worktree/独立环境，先读各库AGENTS与相关规范。固定：
- RMBench f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi 58d6f2155acc3af03017677bb3f536101e6699f4。

运行期间不修改这三处源码/实验文档，避免source hash漂移；中间结果写ignored run目录或本MAM report。不合入后续live或新memory wire改动。旧F0已独立review通过；不因新训练接口尚未完成而停住F0。

同一checkpoint：/mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000。保留原词表、norm、模型、H50、K30；不注入新memory_config。params.legacy_full_feedback_selector按index.value=0/19/29/49选择row1/20/30/50；所有字段统一选该行。保持demo_clean_eval、起始候选seed100000及已固定成对seed协议。这里是旧评测场景配置，新仿真训练/转换数据必须来自demo_clean_state，不能fallback demo_clean。

每个row对应自己实际GPU/端口/配置的一个2rollout smoke（一video一no-video），通过完整recorder/config/source检查再正式100；不放宽检查、不建白名单。记录真实执行K、所选行、各字段before/after、partial与terminal；终止后无下一query，不伪造执行或GT。row50是模型预测，标明未执行关系。

## 监控与解释

每run到50条检查结果，相对历史93/100偏差超过10个百分点时调查协议/基础设施，并记录失败原因；同seed前50可作辅助。反馈行本身是主动实验变量，差异可以是真实结果，不能为了接近93而改协议或删除不利episode。区分实验效应和运行错误。正式100完成记录结果、失败分布、时序诊断、可复制命令、完整commit及证据路径；处理任务临时产物后archive job。

## 产物、范围与交付

写范围为RMBench experiments/memory_chunk_20260910的F0配置/命令/中文README；模型/runtime由其他owner负责。需要新增核心诊断先报告Manager，不修改主checkout。所有调用本树的正式进程结束后再更新实验文档并交付commit。

结果统一/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/<run>，说明归RMBench/experiments/memory_chunk_20260910；不在bridge保存，不增加日志根。每步完整继承metadata/config/command+commit，不复制代码。README直接命令，不使用root export设置段。正式实验替代的smoke在无需再使用门禁引用后清理。保留正式metadata中的smoke通过结论与原检查摘要即可，依用户要求不保留smoke原始视频/日志，也不将整个smoke压缩包搬入正式run。row30的92/100最终检查已被Manager接受，已生成的row30_smoke_evidence.tar.gz可删除，清理记录注明正式结论与摘要保留。活跃run仍依赖的smoke不提前删除；不改运行源码。

本任务report记录task_revision、workspace、实际三库commit、四run当前状态/结果表、job/PID、成果路径、下一检查时机。保持简报，详细smoke、逐query与旧进度引用已保存的JSON或Git报告版本，不累积复制同一历史段落；下一次发布时整理。运行期间可发布report而不结束责任；约小时巡检加50/完成事件检查，不频繁监控训练。不要自行派agent，不创建游离workspace。
