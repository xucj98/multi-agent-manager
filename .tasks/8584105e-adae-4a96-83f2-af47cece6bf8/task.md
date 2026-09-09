# 目标

为开工讨论提供只读定位：独立openpi、robot-bridge和RMBench怎样以最小改动共用memory配置。Manager负责科研问题与实验优先级，本任务只给具体接口和阻塞事实，不写新架构、不实施。

# 范围

读取 /root/Documents/task-state-vla-paper/docs/MEMORY_CONFIG.zh-CN.md 的约定，及三库AGENTS.md；robot-bridge同时读取docs/design/conventions.md。三个库在 /mnt/public/xcj/Projects/ 下。只调查与以下路径直接相关的代码：训练样本/标签与mask、full/state-token模型路径、checkpoint配置读写、scheduler memory反馈、offline回放及RMBench结果保存。

这是快速定位，复用已有文档和入口，不重复全量review或历史审计。不要调查GPU或checkpoint资产（另有任务）。不修改文件、不创建worktree或环境、不运行训练/eval，不访问远端。Manager不需要大篇源码解说。

# 输出

1. 三库branch、HEAD和是否有未提交修改；不要覆盖或切分支。
2. 一个简短表：职责、现有入口（路径/符号）、能复用的机制、必须改动的最小部分。
3. 当前full/serial是否已经在独立openpi，是否仍依赖RMBench/policy/pi05；明确真实查证与未知。
4. 统一配置在train/infer/offline/scheduler之间传递的建议接入点；保留既有execute后wait-condition get_obs、takeover和算法reset，无session或通用插件总线。
5. 最多3条会阻止开工的事实；不要扩展未来全部可能机制。

# 交付

按MAM流程读取发布要求。只编辑自己的report.md，包含task_revision、完成/未知、workspace（只读无worktree/commit）、关键证据；发布report后结束。无需创建新临时资料；若有自建临时文件，交付前清理。等待Manager归档。

# 开工约束补充

wash-cup外部标注1..5各恰好一次，但顺序可变。请在既有状态选择入口定位时顺带核对：是否把字段0/phase硬编码为只能停留或前进一类。不同任务的phase顺序应由任务协议决定，不能由字段名自动推断。只报告当前代码事实，不实施修复。Manager已确认共享主openpi没有.venv/bin/python，RMBench解释器两机可见；环境准备使用既有worktree入口，暂不创建。
