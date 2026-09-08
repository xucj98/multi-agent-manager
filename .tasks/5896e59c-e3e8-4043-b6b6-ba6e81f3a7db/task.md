# MAM打包与仓库改名支持

任务UUID：5896e59c-e3e8-4043-b6b6-ba6e81f3a7db。自己的workspace：/mnt/public/xcj/Projects/workspace/5896e59c-e3e8-4043-b6b6-ba6e81f3a7db。执行者由Manager绑定。先读原管理库AGENTS，并通过已发布CLI show读取本任务及版本。

## 范围

在自己的agent-workflow worktree基于a5e94eefdb4e12d9e7ddf4c915d08cf5096b0a10实施；通过稳定原库 python -B scripts/task.py workspace add创建完整环境。最终项目名multi-agent-manager，命令mam。你负责Python打包、命令结构、相关环境脚本与必要测试。AGENTS/README/设计文档不修改，稳定原库目录迁移和系统pipx安装由Manager执行。

- 将现有标准库核心及job_runtime整理为可安装Python包，提供console script mam。普通安装后可从/tmp等任意cwd直接执行，不依赖当前cwd或包文件在Git仓库中。
- 现有接口统一变为 mam task <原子命令>，例如mam task list、mam task status UUID、mam task workspace add、mam task job list --attention。功能/状态/UUID/发布语义保持，保留--root仅供显式指定管理根/测试；不要新增另一套命令别名或旧scripts/task.py兼容入口。
- 默认管理根为本集群 /mnt/public/xcj/Projects/multi-agent-manager。这是用户明确限定的本机工具，不新增环境变量或配置系统。支持的管理repo名称改为multi-agent-manager；其workspace子目录也同名。历史归档记录只读取展示，不重写历史路径。
- 修改版本化环境入口，使新名的管理库worktree具有独立venv、当前源码可用的mam命令；本地三参数wrapper仍能解析稳定根。可以在开发worktree中editable安装，系统pipx发布安装使用普通非editable方式。无需runtime第三方依赖。
- CLI --help应能独立说明命令作用和参数；帮助保持简短，避免复制完整工作流程。设计文档不作为本次必读或更新对象。
- 保留并适配已有19项核心/runtime测试，补少量有意义的普通安装/任意cwd入口验证。不加数据库/后台服务、远端CLI安装、复杂配置、兼容层或额外provenance。预计净增业务代码/打包声明/入口合计约80–120行，现有代码移动不算新增；发现必要显著超出先向Manager报告原因。

## 迁移期间的交付

原库位置仍为 /mnt/public/xcj/Projects/agent-workflow，当前稳定scripts/task.py负责你的登记和报告发布，调用时用稳定原库的旧CLI，不用尚未迁移的新默认根。提交代码、清理本任务测试产物，在稳定原库本任务report.md写结果并用该旧CLI发布。报告列所依据任务revision、完整交付commit、实际验证及限制。

你不改名原目录、不更新系统pipx、不迁移登记JSON、不修改其他任务或原有GPU实验。Manager会在集成后从旧commit运行CLI归档你的worktree，再移动主目录；这是本次一次性迁移操作，不加入长期兼容代码。随后安排空白agent验证系统安装与新workspace。
