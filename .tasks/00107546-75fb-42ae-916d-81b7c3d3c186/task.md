# State-VLA 实验台账

用户要求有一个论文式入口，读者能知道每组实验为什么做、预期检验什么、实际结果是什么，并点到训练和eval目录；覆盖本轮运行中与已完成的实验。当前信息分散，不要把MAM运维日志当作实验解释。Manager会裁定研究表述。

## 工作范围
创建本task独立RMBench worktree，base 6ce7290feca710a9b41adb45f8b647853d6bf389。读其AGENTS与docs/guidelines/experiments.md。仅修改experiments/memory_chunk_20260910/README.md（顶部简短统一导航）和新增EXPERIMENT_LEDGER.zh-CN.md。README原F0证据保留；不要改README_memory_schema.zh-CN.md（eval owner维护）或README_precision_validation.zh-CN.md（清理owner维护）。不改代码、不占GPU、不移动结果、不改原metadata。

## 证据
论文/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md固定Q1/Q2/Q3及统一协议。组内README/F0、README_memory_schema、README_precision_validation给已完成结果；本MAM训练owner e7e5ac54、ad6bb77e最新发布report及eval owner e6908de7报告给状态与精确产物路径。必要读结果小型final_review/汇总/config，不扫描全部视频/大模型。若引用本机外目录只读，不另建paper worktree。

## 必须呈现
以实验组解释加紧凑逐run表组织，而非复制运行日志。每组：研究问题/为什么做、预先假设或探索性质、关键受控变量和比较、指标、实际结果与能支持/不能支持的结论。运行中的结果留待评测，不能用training loss当闭环成功率。假设不写成结论，不因结果挑选实验。
覆盖F0已完成4run（同旧权重row30/20/1/50分别92/86/21/38）、BF16存储验证92vs92及14配对不一致（沿BF16加载路径，不是FP32计算比较）、旧drawer两模型各5ep offline（不是成功率）、Q2两任务×两目标×3训练seed=12模型及首批serial/no-memory两个能力基线、wash full/serial两个20k单phase模型。合计本轮16个新训练模型，区分8远端训练已完成与本机仍训练的8份，状态取发布时实际证据。
明确Q2共同H50/K30/row30，不同phase标签per-frame(t+j+1) vs repeated endpoint(t+30)，相同公共mask，机器人目标和其他字段不变。serial/full不是单变量表示对照。Q1反馈×执行、Q3按钮内容交互是后续计划，简单链接既定计划，不假装已运行。
每个正式run/模型表给配置、train seed、训练状态、eval状态/结果、训练输出目录链接和eval目录链接。20k尚不存在时链接训练run父目录并标待保存；eval未启动时标计划路径（非已存在）。使用主仓库共享稳定路径，不以workspace当永久成果位置。链接精确到各模型，不用只给统一根目录让读者猜。BF16副本用户已要求验收后删除，不再写保留；源FP32、导出metadata和正式结果保留，状态以清理owner47a91a44报告为准。

无需引入新的数据库/schema、自动生成器或重复raw metrics。给出更新时间和证据入口即可。交付前核对计数、数值和链接存在性，计划路径明确区分，git diff --check，提交文档发布report。目标20–30分钟。后续结果更新由实验owner对该台账对应行负责，Manager统一审阅整合。

## 07:28 Manager文稿审阅修正
整体结构可用。修正“新20k训练共同条件demo_clean_state”：该数据约束仅仿真，wash来自已筛选172集真机数据，不可写成全部16模型同一数据源。wash中“full使用current feedback，serial使用lag30”混淆输入样本定义和运行反馈：按真实schema分别写清full训练memory输入参考当前t、full输出目标与执行后取行；serial训练输入lag30、当前query目标/反馈，H/K说明保持简洁，别从配置名猜语义。状态按你07:16快照保留即可，不需要追着每分钟更新。其余已完成结果和链接保留。提交小修并发布，不增加新文档。
