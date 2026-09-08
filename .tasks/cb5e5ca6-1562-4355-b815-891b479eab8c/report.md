task_revision: d6afa84cfe80604733fb5d22b6a74e2a120b28f1

完成：
- 将 `mam task job add/list/archive` 迁移为 `mam job add/list/archive`，并将 `mam task workspace add` 迁移为 `mam workspace add`。
- 保留各子命令参数、状态语义及 `task status/archive` 的内部处理；顶层 `--root` 仍位于命令组之前。
- 更新根级与分组帮助，移除两个旧入口且未添加兼容别名。

交付 commit：
- multi-agent-manager: fa79410c72469974f6462f12adf2467eb9b5b744
- workspace: /mnt/public/xcj/Projects/workspace/cb5e5ca6-1562-4355-b815-891b479eab8c/multi-agent-manager

修改文件：
- multi_agent_manager/cli.py
- tests/test_task.py

测试：
- `.venv/bin/python -B -m unittest discover -s tests -v`：22 项通过。
- 已确认 `mam job --help`、`mam workspace --help`、`mam --root <root> job list` 和 `mam --root <root> workspace add`；旧 `mam task job`、`mam task workspace` 均以退出码 2 拒绝。

未完成项：无。AGENTS.md、README.md 和 docs 按任务范围未修改，由 Manager 维护。
