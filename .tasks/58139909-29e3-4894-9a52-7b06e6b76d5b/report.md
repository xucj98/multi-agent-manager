task_revision: 7075080069b9392b070bc2bdcd761ca180f1bb83

审阅结论：通过；未发现需要修改的代码或文档问题。

固定版本：
- 代码 commit：fa79410c72469974f6462f12adf2467eb9b5b744
- 文档 commit：043861a3f810b719f6b7001bbd5a9d22bb2bebc6
- workspace：/mnt/public/xcj/Projects/workspace/58139909-29e3-4894-9a52-7b06e6b76d5b/multi-agent-manager

验证结论：
- 固定 diff 仅将 `job`、`workspace` 提升为顶层命令组；`task` 保留任务与发布入口。`job add/list/archive`、`workspace add` 的参数和处理函数未变，`task status/archive` 未改动；实现净增 1 行，未引入依赖。
- 私有新 `mam` 从 `/tmp` 的顶层、`task`、`job`、`workspace` 帮助均正常；默认根定位到稳定管理库，`mam --root <root> job list` 与 `mam --root <root> workspace add` 均正常。
- `mam task job --help` 和 `mam task workspace --help` 均以退出码 2 拒绝。以新 `mam workspace add` 对本任务已登记的 `multi-agent-manager` 重复调用返回现有记录，primary checkout 的 Git worktree 登记未增加。
- `.venv/bin/python -B -m unittest discover -s tests -v`：22 项通过。

文档审阅：固定 `AGENTS.md`、`README.md`、`docs/install.md` 与 `docs/task-management-design.zh-CN.md` 的命令均使用 `mam task`、`mam job`、`mam workspace`；旧入口只存在于历史任务快照，未发现现行文档问题。

具体问题：无。
未完成项：无。
