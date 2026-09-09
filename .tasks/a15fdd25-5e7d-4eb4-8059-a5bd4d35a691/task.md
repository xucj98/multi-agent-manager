# Memory实验：F0反馈行评测与新checkpoint评测准备

## 当前授权与验收

Manager已于2026-09-10 06:52验收row30/GPU0的2rollout smoke。依据已发布报告598cd4538b2b9ad293f4274bd01eb862029be53b及smoke_verification.json/video_metadata_verification.json：2个accepted episode，1success/1button_press_insufficient，视频700帧可读/另一集无视频，38个query反馈链、metadata/source匹配、terminal路径和进程收尾通过。RPC抓包不完整仅作辅助；不以smoke成功率推断正式结果。

现在直接启动row30/GPU0正式100，无需等待再次许可。使用本任务RMBench worktree运行：

```bash
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --gpu 0 --mode formal --detach
```

启动后立即登记真实host/PID的mam job，检查服务和第一条episode，报告实际run路径和预计50条检查时机。GPU1仍留训练50step smoke，Manager确认释放后才能用于第二个F0。远端八卡留新训练，不使用。F0四个run的预算均已授权；后续同一卡上row20/1/50各自先通过匹配的2rollout smoke，确认产物后可依次正式100，不需再次等待许可。GPU1释放前按GPU0串行安排。每个run完整100条在同一GPU串行，sim/policy共用该GPU，不拆分。

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

写范围为RMBench experiments/memory_chunk_20260910的配置/命令/中文README；模型/runtime由其他owner负责。需要新增核心诊断先报告Manager，不修改主checkout。新checkpoint评测准备只在其代码/数据验收后推进。

结果统一/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/<run>，说明归RMBench/experiments/memory_chunk_20260910；不在bridge保存，不增加日志根。每步完整继承metadata/config/command+commit，不复制代码。README直接命令，不使用root export设置段。正式实验替代的smoke在无需再使用门禁引用后清理，不删除唯一证据或活跃run依赖。

本任务report记录task_revision、workspace、实际三库commit、完成/剩余、job/PID、成果路径、下一检查时机。运行期间可发布report而不结束责任；无需频繁检查训练，用预定评测中点检查即可。不要自行派agent，不创建游离workspace。
