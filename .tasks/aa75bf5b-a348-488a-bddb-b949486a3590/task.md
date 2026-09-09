# 目标

对Memory配置规格作空白终审，判断是否可以作为后续代码实现的明确依据。要求内容清晰、简洁、无矛盾，现有实例的执行含义可唯一确定。此时尚未接入生产训练或scheduler；不要将未实施事项误报为运行代码bug。

# 输入

使用mam task status返回workspace下review_v3/的只读快照；SHA256SUMS固定本次输入。先读docs/MEMORY_CONFIG.zh-CN.md，再读docs/memory_config/memory.schema.yaml与五个实例。两个SAMPLES/SWAP_T文档是解释，FRAMEWORK是研究背景。不要读取其他review任务的报告或母对话。

这是文档终审，已提供独享快照；无需代码worktree或新环境。仅需只读文件和少量CPU推演。可用 /mnt/public/xcj/Projects/RMBench/.venv/bin/python 中现有yaml/jsonschema。禁止修改文件、依赖环境、启动GPU实验或扩大扫描范围。

# 验收与交付

核查结构约束与语义约定是否匹配，配置引用能否被确定读取；时间/边界/编码/归一化顺序/条件选值/反馈事件是否存在影响实例或已开放组合的歧义。给出有明确例子的阻塞问题；非阻塞意见至多3条，不为可能的无限未来扩展增添复杂设计。Manager最终裁定。

完成后只编辑自己的report.md，记录task_revision、完成与未完成、workspace（无代码worktree/commit）、快照哈希核验、审阅结论与具体证据，并用mam task publish --file report发布。不要自行归档。清理自己额外产生的临时文件，保留输入快照给Manager收尾。

# 本次追加

review_v2替代review作为交付基准；仅MEMORY_CONFIG第7节新增按阶段做能力检查：普通推理无需训练标签，显式reference路径才要求在线GT，UI无需加载模型。其余文件未变。已完成的核验可复用，只追加核对这段，再依据最新task_revision发布report。

# 终审意见修订后的定向复核

review_v3为最终基准。Manager采纳两条意见：target_time在结构层要求offset>=0并禁止lag，覆盖memory目标与robot_target；online_time在结构层禁止lag，覆盖reference输入与反馈。只有训练输入可带lag。在线reference使用输入越界规则，固定历史offset仍允许。仅MEMORY_CONFIG与memory.schema.yaml变化，五实例不变。请定向复核这两处修复及五实例仍通过，其他已完成核验复用，不再扩展新功能。按最新task_revision更新report保留原发现与修复结论，然后发布。
