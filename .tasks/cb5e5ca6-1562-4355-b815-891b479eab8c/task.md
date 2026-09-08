# MAM 顶层 job 与 workspace 命令

任务UUID cb5e5ca6-1562-4355-b815-891b479eab8c，workspace位于/mnt/public/xcj/Projects/workspace/同UUID。先在稳定管理库/mnt/public/xcj/Projects/multi-agent-manager通过mam task show读取发布任务，再读AGENTS/README。使用mam task workspace add创建自己的multi-agent-manager worktree，base固定151ff2d298c84fb32d4370c7c6e548d09e17cf18。使用gpt-5.6-terra max。

最终命令分为mam task、mam job、mam workspace三组。将mam task job add/list/archive移为mam job add/list/archive，将mam task workspace add移为mam workspace add，保留原参数和状态语义，task status/archive内部进程与工作区处理不变。顶层--root保留原功能及位置。删除旧task job和task workspace入口，不增加兼容别名。更新相关CLI帮助、调用提示与既有测试；仅补必要的入口回归，不扩展进程功能或新增依赖。业务代码净增尽量控制在20行以内，必要超出说明原因。不要修改AGENTS.md、README.md、docs（由Manager完成），不要改历史.tasks，勿安装全局包或动GPU。

交付：自己环境中完整单元测试通过，确认job及workspace子命令帮助、--root分流和两个旧入口拒绝；提交代码，清理本任务临时产物。报告首行task_revision，列完整commit、修改文件、测试和未完成项，用稳定mam task publish发布report，保留clean worktree待Manager归档。后续独立review基于本任务和提交验收。已创建的worktree继续复用，系统安装更新前仍以旧workspace入口创建环境。
