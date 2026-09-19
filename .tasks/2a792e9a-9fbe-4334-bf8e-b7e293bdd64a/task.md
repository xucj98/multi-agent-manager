# 九任务优先补齐执行合同
Manager负责科学设计与最终裁决；本任务负责 press_button、blocks_ranking_try 的数据与工程实现。先读AGENTS.md、涉及仓库AGENTS.md，以及论文docs/EXPERIMENT_PLAN.zh-CN.md、ASSET_AUDIT.zh-CN.md（旧缺口必须实查）。创建独立worktree，禁止修改既有运行树。
立即检查现有可复用资产与生成入口；缺少demo_clean_state时执行必要代码适配、短smoke，然后生成每任务50条成功且完整的训练示范。固定确定性生成seed序列并保存所有尝试/失败/筛选记录；不得用正式eval种子100000..100099、200000..200099、300000..300099做训练数据。遵循benchmark原demo生成成功筛选规则，不改环境成功判据。原始轨迹须保存足够状态/事件/动作与来源，以便之后定义标签；生成时不要将未来/隐藏答案注入在线策略。
允许立即进行数据生成和N路径转换/配置实现，不必等schema全部完成。GPU使用wuwen-1的实际空闲卡；同组最初最多2卡，不抢占其他进程，和另一数据负责人协调卡号。每任务先2条生成smoke检验完整性再扩到50条，预计超过30分钟登记MAM job，失败保留证据；不要长轮询。共享cache规范 /root/.cache -> /mnt/public/xcj/cache，HF_LEROBOT_HOME unset，不复制数据集到wuwen-1。
press_button依据可见目标数字及实际按压事件累计计数，不以已发命令替代物理事件；ranking只保留过去尝试与可观察反馈，不能把隐藏正确排序输入策略。
N使用14D机器人state+当前图像，无任务memory，pi05_base新初始化、seed0、bs32、20k、H50/K30；J固定joint逐行状态、上一chunk末执行行反馈。提交确切schema草案（字段、可获得时刻、目标时间、初值/unknown编码、连续归一化、source路径）由Manager裁决，先实现通用采集/N转换及必要接口，不能自行把草案当最终科学合同。S共用同任务字段，连续接口不支持须明确实现缺口，禁止偷换表示。
交付不是只读调研：发布可运行生成入口、实际smoke/生成进度、数据来源清单与下一步可执行命令；每个数据集就绪即发布，不等另一个任务。正式20k训练前提交数据完整性、来源/标签合同、CPU测试与短恢复候选供Manager验收，禁止未验收开正式训练。不要新增训练seed，不改论文主张，不接管HF工作。

## 2026-09-20 Manager 追加：新任务 J/S schema 缺口审计

在 `blocks_ranking_try N` smoke/正式训练进入稳定状态后，追加一份只读 schema 缺口清单，覆盖 `observe_and_pickup`、`swap_T`、`blocks_ranking_try`、`press_button`：

- 列出 J/S 所需字段、字段的可获得时刻、监督目标时刻、初值/unknown 编码和连续归一化方式；
- 核对现有 raw state/event/provenance/trace 是否足以无歧义重建这些字段；
- 明确哪些字段已有证据、哪些字段缺失、哪些字段需要 Manager 决策；
- 只做审计和建议，不自行冻结科学合同，不启动 J/S 正式训练，不修改已有 N 数据或评测结果；
- 将结果写入 report 并发布，供 Manager 裁决后再安排实现。
