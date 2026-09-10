task_revision: 2e29129286945eec128f2fd04efe194ec923007c

完成：README 精简为操作手册；统一 TASK-ID、JOB-ID、AGENT-ID 术语与 CLI metavar、help、错误和表头；新增长任务保持 active turn 的 wait 规则；task/job status 改为精简 JSON 展示投影，保留缓存/unknown 语义与归档、review、交付信息。

workspace: /mnt/public/xcj/Projects/workspace/66743086-e895-4cfe-b2e8-fad92bd0c852/multi-agent-manager
commit: 9d2a2fca5764a97b5df09e21d019a093f98bf202
改动文件：AGENTS.md、README.md、docs/task-management-design.zh-CN.md、multi_agent_manager/cli.py、tests/test_task.py。

前次代码验证（b338dbdd4398af307fd070606288101b8c1d2901）：`.venv/bin/python -B -m unittest discover -s tests -v` 通过（32 tests）；递归运行 20 个 `mam` 顶层/子命令 `--help`；`git diff --check` 通过。

18:10 修复：本次增量仅 README.md（5 行新增、1 行删除），恢复共享 checkout 中的编辑分工、草稿发布、途中要求先发布再通知、交付清理并保留 worktree 的操作说明；修正只读工作无需创建 worktree 或代码环境的措辞。已核对 README 链接及章节锚点、diff-check 和变更范围；未重跑测试，未修改状态代码。worktree 干净，保留供 Manager 验收归档。
