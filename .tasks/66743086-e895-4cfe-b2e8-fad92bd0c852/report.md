task_revision: a3336b1117fe433a4ea6673f0daab455b5ea5550

完成：README 精简为操作手册；统一 TASK-ID、JOB-ID、AGENT-ID 术语与 CLI metavar、help、错误和表头；新增长任务保持 active turn 的 wait 规则；task/job status 改为精简 JSON 展示投影，保留缓存/unknown 语义与归档、review、交付信息。

workspace: /mnt/public/xcj/Projects/workspace/66743086-e895-4cfe-b2e8-fad92bd0c852/multi-agent-manager
commit: b338dbdd4398af307fd070606288101b8c1d2901
改动文件：AGENTS.md、README.md、docs/task-management-design.zh-CN.md、multi_agent_manager/cli.py、tests/test_task.py。

验证：`.venv/bin/python -B -m unittest discover -s tests -v` 通过（32 tests）；递归运行 20 个 `mam` 顶层/子命令 `--help`；`git diff --check` 通过。
