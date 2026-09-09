# 目标

独立只读审阅论文memory配置规格：是否足够明确，能据此实现样本构造/表示/反馈，是否还有自由文本决定执行、歧义、冗余或内部冲突。主要作者是Manager；本任务只提供审阅意见，不修改方案或业务代码。

# 输入与范围

使用mam task status返回的workspace下review/快照；SHA256SUMS固定本次输入。先读docs/MEMORY_CONFIG.zh-CN.md，再读docs/memory_config的schema和五个实例。MEMORY_SCHEMA_SAMPLES与SWAP_T是阅读解释，FRAMEWORK是论文背景。无需继承母对话。

这是文档审阅，已准备独享workspace内快照，无需创建worktree或Python环境。可只读使用 /mnt/public/xcj/Projects/RMBench/.venv/bin/python（已有yaml/jsonschema），禁止安装或改动环境。不得启动GPU/训练/eval，不扫描整个集群。

# 审阅要求

1. 区分JSON Schema结构检查与需要运行器实现的跨字段/运行能力校验，不把后者尚未实现误报为已实现bug。当前任务是定下可落地规格，不是生产接入。
2. 检查五个实例与文字含义一致；尤其lag共采样、常量与时刻、目标布局、mask、首轮锁存、按钮规则依赖、接受/完成事件。
3. 找出会让两个合理实现者产生不同行为的缺口；给最小修复建议。避免泛化到所有未来可能架构。
4. 自行做少量具体时序/解码推演或结构检查，给证据。历史源代码事实优先引用当前快照已链接的审计；如有必要，只读查明确文件，不重复全量历史审计。
5. 意见按阻塞/非阻塞排序；没有问题就明确无阻塞。Manager负责裁定，不要求直接采纳。

# 交付

只编辑本任务report.md，记录task_revision、完成情况、workspace、SHA256SUMS（无代码worktree/commit）、发现与验证；通过mam task publish --file report发布。完成后报告，不自行归档，保持快照待Manager验收。清理自己额外生成的临时文件。
