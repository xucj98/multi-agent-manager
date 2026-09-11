# OpenPI symlink transformers 覆盖定向复核

独立审阅 OpenPI `958eeaedc4c841e2f1b31c51572ddecc449ba5cb`，基于父提交的增量。先按 MAM 入口创建本机独立 OpenPI worktree，再读库 AGENTS。源任务 5773b6ec-6584-42db-9d0d-9ef5d40f7c31 正在 C 安装，之前三库 link-mode 增量已有 review，本次只核查新增修复。

核查 transformers 覆盖在 uv 文件级 symlink 布局下写入 venv 私有文件、不修改共享 cache，默认 hardlink 行为正确，smoke 确认真实覆盖路径且不会误判。检查原子替换与路径边界，使用必要的本机 CPU 小 fixture 复现，不需要全量安装或 GPU。可以只读 C 上 wrapper/patch 检查兼容性，不得写 C、重跑安装或干扰作者。

交付简洁 PASS/问题与证据，写并发布 report.md，注明 workspace/commit/验证范围。遇到阻塞问题直接报告 Manager，由作者修复；不改业务代码。清理自己的 fixture/cache，worktree 保留由 Manager 归档。真实三机 smoke/C100 由源任务负责，本次不宣称环境已验收。
