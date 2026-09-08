# MAM三组命令与文档空白review

Review fixed source delivery:
{
  "task": "cb5e5ca6-1562-4355-b815-891b479eab8c",
  "task_revision": "d6afa84cfe80604733fb5d22b6a74e2a120b28f1",
  "report_revision": "db9aa792377fbeb0dba1db7540f05aebcf353d86",
  "commits": {
    "multi-agent-manager": "fa79410c72469974f6462f12adf2467eb9b5b744"
  }
}

Source task:

# MAM 顶层 job 与 workspace 命令

任务UUID cb5e5ca6-1562-4355-b815-891b479eab8c，workspace位于/mnt/public/xcj/Projects/workspace/同UUID。先在稳定管理库/mnt/public/xcj/Projects/multi-agent-manager通过mam task show读取发布任务，再读AGENTS/README。使用mam task workspace add创建自己的multi-agent-manager worktree，base固定151ff2d298c84fb32d4370c7c6e548d09e17cf18。使用gpt-5.6-terra max。

最终命令分为mam task、mam job、mam workspace三组。将mam task job add/list/archive移为mam job add/list/archive，将mam task workspace add移为mam workspace add，保留原参数和状态语义，task status/archive内部进程与工作区处理不变。顶层--root保留原功能及位置。删除旧task job和task workspace入口，不增加兼容别名。更新相关CLI帮助、调用提示与既有测试；仅补必要的入口回归，不扩展进程功能或新增依赖。业务代码净增尽量控制在20行以内，必要超出说明原因。不要修改AGENTS.md、README.md、docs（由Manager完成），不要改历史.tasks，勿安装全局包或动GPU。

交付：自己环境中完整单元测试通过，确认job及workspace子命令帮助、--root分流和两个旧入口拒绝；提交代码，清理本任务临时产物。报告首行task_revision，列完整commit、修改文件、测试和未完成项，用稳定mam task publish发布report，保留clean worktree待Manager归档。后续独立review基于本任务和提交验收。已创建的worktree继续复用，系统安装更新前仍以旧workspace入口创建环境。

Source report:

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
# 空白独立验收要求

任务UUID 58139909-29e3-4894-9a52-7b06e6b76d5b，workspace位于Projects/workspace/同UUID。先用稳定/root/.local/bin/mam task show读取已发布任务，再读稳定管理库AGENTS及README。使用gpt-5.6-terra max、无历史上下文，只读review，不修改实现或文档。

源码固定fa79410c72469974f6462f12adf2467eb9b5b744，文档固定043861a（可用git show读取AGENTS/README/docs/install.md及设计文档）。本轮系统mam仍是旧版，通过mam task workspace add为本任务创建multi-agent-manager独立环境，base为源码固定commit；私有环境使用新mam命令。只需自己的一个worktree，无GPU或远端操作。

审阅下方源任务与固定代码diff，验证顶层mam task/job/workspace、原参数与--root语义，以及两个旧入口被拒绝；独立环境完整单元测试。用新私有mam从/tmp验证帮助与默认根，并用新mam workspace add为你自己的已登记库重复调用确认入口能复用已有worktree，不新建额外任务。已有测试覆盖进程生命周期和删除安全，不重复全局实验。审阅现行AGENTS/README/install及同步设计文档是否清晰、简洁、命令一致；Manager自己的工作无需登记，预计超过1小时的程序需mam job add。用户正在讨论进一步按需阅读的文档结构，本轮仅反馈当前文档的具体问题，不重写或扩大实现范围。

交付简报首行task_revision，列代码commit、文档commit、workspace、验证结论和具体问题，用稳定mam task publish发布。清理本任务临时文件，保留clean worktree供Manager归档。不要改全局pipx、shell配置、其他任务。下面是源任务固定快照供review。
