# 目标

为首批memory实验排期提供资产可用性事实。只读、快速、定向检查；不做完整历史复现或审计，不启动任何训练/eval。

# 调查范围

先读RMBench AGENTS.md和实验规范，以及 experiments/history_audit_20260909 的README和run_index中相关项。仅检查：
1. rearrange shared full seed0 ckpt30k（历史93/100）、shared serial fixed20 seed0 ckpt30k（36/100）及其训练数据/标注/norm stats。先使用已记录路径，若缺失只在已知checkpoints根下定向找同名目录，不全盘扫描。
2. pi05 base初始化权重、本地可用的rearrange/put_back_block原始或转换数据。
3. 两个已知drawer模型 pi05_x1pro_drawer_sorting_s2m_full_state 和 pi05_x1pro_drawer_sorting_s2m_serial_soft，以及对应offline数据路径；/mnt/public3到/mnt/public的历史镜像关系只在真实存在时确认。
4. /mnt/public/datasets/x1pro/wash-cup 的annotation_layers.json和现有数据审计报告。若已有报告直接引用筛选统计，不重新扫描所有episode；没有报告就标unknown。用户过滤规则：出现label6、缺子任务标注、标签1..5不是各恰好一次均剔除，顺序可变；phase表示当前子任务，S2M，全部有效数据训练，5ep offline非holdout评估。

# 边界

各库在 /mnt/public/xcj/Projects/。不下载、不复制大资产、不加载大模型，不查GPU（Manager负责）。不改任何环境/代码，不创建worktree。不推测文件存在等于checkpoint可加载；分清目录存在、必要文件可读、尚未做加载验证。

# 交付

给一个简短资产表：对象、真实路径/软链目标、必要文件与metadata状态、可立即用于哪类试验/缺什么。最多列3个阻塞项。
按MAM先读取发布任务，最终仅编辑report.md，记task_revision、完成/未知、workspace（只读无worktree/commit）、证据并发布。清理自建临时文件，等待Manager归档。
