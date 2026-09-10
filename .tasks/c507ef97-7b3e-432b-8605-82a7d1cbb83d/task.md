# 空白上下文独立验收
你是新加入该项目的agent，未参与实现。请仅根据MAM入口规范和 `/mnt/public/xcj/Projects/table-1000/table-1000` 仓库内AGENTS/README/环境文档，从头为本TASK创建独立worktree与环境，并执行文档中的验证。base使用canonical当前main（先记录精确commit）。不要借用其他任务的venv，不修改文档或脚本去绕过失败；如遇缺失说明/环境问题，记录原始错误及你从文档能否自行恢复并报告manager。
# 验收与交付
先回报CODEX_THREAD_ID用于绑定。确认文档的一键命令可从新任务使用，首次创建耗时/新venv实际磁盘占用/包文件复用目标明确；每task有独立venv，editable导入本worktree源码，资产和outputs链接正确，主repo顶层没有业务软链。按文档执行真实资产/CPU/场景和可用GPU smoke及其测试，禁止正式训练和长数据生成；记录实际退出码与结果。复用包仓库是预期设计，不得clean/prune它。依文档做交付前清理，保留worktree给manager验收/归档，产物放文档规定位置。发布MAM report，记录精确命令、耗时、路径、证据及任何文档歧义。不派发下级agent。
