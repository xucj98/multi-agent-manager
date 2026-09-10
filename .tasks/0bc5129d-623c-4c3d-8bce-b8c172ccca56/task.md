# Memory runtime 独立 review

## 目标与工作区

审查任务9f5a3889-49a6-4f00-af84-096d8042c3bc交付的robot-bridge runtime。复用本任务已登记的robot-bridge/openpi worktree和独立环境，读取各库AGENTS及bridge的docs/design/conventions.md。只读审查生产实现，独立验证，不占GPU、不连接真机、不派agent。

bridge ed2f2f34a1eea74e8449d39b889555fdfcc659fc的两项原live问题已由你的ff00b8f关闭，Manager接受。剩余X1非零wait争用SDK锁已交作者最小修复；新commit到后只复核这一回归及零/非零对照，已通过的prefix/cut/epoch不再全部重复。openpi使用已有ffa308d5485a2c8222d3e7735b08723c6e93a237等价树即可。checkpoint模型和loss审查归Banach，full/serial真实GPU50已获Manager验收。

作者另交259行跨库回归29a5638f4a6bdfef2f107d331c2afde9daa03697，复用已注册配置、实际tokenizer/transforms/Context，只替换昂贵模型采样。请合入本任务双库环境中运行这4项并确认没有用mock掩盖输入/输出接线；这用于保留已发现bug的回归，不重开此前7项wire验收。若结构合理且覆盖关键接口，无需为了约200行目标继续压缩。

## 已通过范围

你的报告05ba1a0及此前分项结论已被Manager接受：F0/legacy simulation（冻结bc842036）、新memory实际transforms→Context的7项CPU联通、drain后latency处理、原takeover回归，以及c94f508的全新隔离wheel依赖验证。F0已在独立任务跑正式100，不重开这些gate，也不重复整个训练/数据套件。

## 本轮待关闭的两个live问题

1. 同步get_obs必须等待与返回观察时间相符的实际handoff。此前单行chunk的排期已结束而SDK调用尚未完成时，零剩余wait提前返回，Context允许下一infer。使用真实X1 loop/X1Pro worker、真实execute/get_obs和event延迟SDK返回，验证不会提前放行；放行后的completed/queued必须与观察时间相符。保留同一个带wait_condition的get_obs，非零剩余的原异步流水线继续成立。
2. 实时tick跳过多个目标时，进度必须是成功handoff确认的轨迹前缀/位置。此前3行目标只发送第3行却completed=1，Context误用row1并留下永久pending。复现延迟tick，验证成功发送第3行后Context消费index2、队列可drain；不能为凑计数补发过期动作，也不能只按墙钟声称完成。

两项都检查partial prefix、旧图像/新图像快照、重复事件、cut/reset/接管及旧epoch事件，避免旧proposal被新动作消费。进度表示执行器交接的轨迹位置，不是SDK调用次数、硬件物理到位、渲染帧或仿真积分步。核验必要的锁/子进程事件路径；不能只依赖作者mock结论。修复后的回归按影响选择，不扩成硬件验收。

## 持续成立的接口与结构约束

- 保留SchedulerBase的execute→带wait_condition的get_obs及WS动作chunk/UDP takeover；没有get_progress RPC、session或plugin bus。一个scheduler对应一个robot和一个policy；显式memory context归scheduler，原算法内部cache/reset行为可保留。
- 新schema输入为机器人原state/images/prompt加memory_input_ids(F,)，编码归policy transforms。输出actions仅机器人动作，memory_prediction_ids为full(H,F)或serial(1,F)。serial IDs必须等于实际动作条件selected；Context校验后按事件/行消费，不二次argmax、不读机器人actions尾部。previous来自本query输入，单/多字段和F=0共用机制。
- full逐行预测可不同；H50/K30首批在chunk完成后读row30。query/chunk/部分执行、拒绝、中止、reset均有明确pending生命周期。UI从同一schema字段生成，普通部署不读取训练GT。
- 旧无memory_config checkpoint沿既有路径；F0保留原权重、词表、归一化与解码，rows1/20/30/50为所有字段同一选择行，trace记录actual_k/next_query。terminal通过build_policy_obs返回None跳过infer，Base保留既有顺序。
- 仿真产物归RMBench recorder。三个scheduler共用Context，不复制三套反馈状态机；轻量openpi-client不依赖训练框架。异常/接管/reset回收旧动作、子进程与视频资源。

## 交付

发布简明report，包含task_revision、独立工作区及实际HEAD、本轮两P1是否关闭、复现命令和结果、剩余具体问题与影响。已验收项引用前次报告，不再复制全部历史。区分CPU/fake SDK、GPU和硬件证据。生产及测试的新增规模用于判断必要性，不为压数字删必要验证。清理本任务临时脚本/cache；保留独立worktree待Manager归档。
