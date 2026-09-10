# MAM操作手册与CLI标识术语统一审计
# 目标与范围

用户要求README定位操作手册，统一task/job/agent ID术语与CLI help，AGENTS增加长任务保持active turn时的等待要求。你实施并自审；Manager另安排空白review后合并安装。读AGENTS/README，通过mam workspace add创建multi-agent-manager独立worktree，base 3f50b7b2b2a0030836ba22cc73b86da08617f47e。不占GPU、不安装系统、不修改真实任务/job，不派agent。

# 具体要求

1. README删去字段顺序、JSON内部内容、unknown转换、文件锁/token/PID/取消标记等实现或输出规格段落；按用户实际操作提供简短说明与常用命令。明确展示mam task list/status/show，mam job list、mam job list --task TASK-ID、mam job status JOB-ID、job archive，mam wait jobs [--task TASK-ID] [--timeout TIMEOUT]、wait list、wait stop --agent AGENT-ID。可执行示例与语法示意区分，必要说明例如stop只停止等待、task status并非实时job探测保持简洁；详细接口规格留设计文档/CLI help，不再重复整套字段表。
2. 全部活跃文档、AGENTS、CLI用户可见help/错误提示/表头/生成模板审计术语：任务标识称TASK-ID，job标识JOB-ID，agent标识AGENT-ID；语法占位统一大写并使用argparse metavar，usage不出现task或TASK指代TASK-ID，不写task UUID/job UUID/source-uuid。review来源参数也用TASK-ID；workspace路径用同一个TASK-ID，不引入workspace-id。普通概念正文可用任务/进程/agent，讨论UUID实现类型确有必要只留内部代码，不重命名uuid库/内部变量/存储字段，不修改历史.tasks正文或旧实验记录。CLI其他参数也统一常规大写metavar（COMMIT/REPO/HOST/PID等），不改变参数名或行为。共享main存储字段和已发布任务历史保持原样。
3. AGENTS新增一句：启动长任务且需要保持active turn时，使用 `mam wait jobs [--task TASK-ID] [--timeout TIMEOUT]` 等待。不要强制所有短程序或纯讨论调用wait，不扩大长job登记范围。
4. 同步docs/task-management-design.zh-CN.md术语/必要操作链接，保留设计文档本身职责；docs/install.md等现行文档一并检查，无需改无关内容。README维持中文、简洁、空白agent能按文档找到task/report并操作，不让其必须读设计文档。

# 验证与交付

这是文案/metavar小修改，控制增量，不新增框架或冗长测试。实际递归跑所有子命令--help，核对placeholder/header/文档常用命令；现有标准库回归按README运行，若断言旧提示仅做必要调整。CLI身份参数dest不能因metavar修改而变动。diff-check及范围检查；无GPU。清理自有pycache与临时输出，干净commit、发布简短report（task_revision/workspace/commit/改动文件/验证）。用户特别要求审计所有help，不能只改两个示例。预计20分钟内交可review版本。
# 17:40 用户追加：精简 status

用户要求同时优化各status输出冗余。仅现有task status/job status，不新增命令或--json/--verbose/详情级别，不改存储与进程探测语义。继续JSON，做小型展示投影而非重构内部模型：
- task status保留id/title/status/agent/workspace、repo路径/分支/状态/交付commit与必要base、发布task/report版本及report依据task版本、drafts/requirements_changed。发布revision每种只出现一次。jobs只列摘要id/note/status/checked_at（这是保存观测，明确cached语义），不嵌套identity/probe/archive长历史。归档job可汇总数量，未归档job摘要用于Manager取ID；task本身归档/出错时保留收尾结论和有用失败原因；review任务保留固定源task/版本/成果引用。空null字段、正常false清理标记、重复source/path等可省略，不丢定位工作区和验收版本的能力。
- job status保留id/note/task/task_title/agent/host/pid/started_at/status/checked_at，刷新目标job一次。正常不重复identity/probe/status/checked_at，隐藏boot_id/start_ticks。探测unknown时status显示unknown并保留error与必要last_known_status/last_known_checked_at；已归档保持archived并保留archive结论。异常身份不匹配可有针对性提供诊断，不一律dump全部对象。
- 状态函数内部返回值被其他调用复用时优先增加轻量render投影，不破坏job归档/等待/其他command输出。更新必要测试验证真实状态不冒充缓存，精简后仍可拿到job IDs与工作区/版本。不改变task show行为。README只写怎么查询，不添加输出字段规格；必要规格进入设计文档。

此项与此前文案一起交付，但可单独commit便于review；当前base task文字中“不改行为”指原功能语义，这里明确授权status展示精简。若此前文案已提交，保留并增量实施。任务预计适度延长，不增加环境/agent。
# 18:10 README必要步骤修复

Manager与独立review均确认精简时误删必要操作信息；状态代码和测试已通过，这轮只恢复简短操作说明，不恢复输出字段规格：
- 管理仓库共享checkout，Manager在其中编辑task.md，执行者在其中编辑自己report.md；main提交内容已发布，工作目录修改是草稿，使用mam task publish发布。
- 途中追加要求先更新task.md并publish，再通知执行者读取新版本。
- 交付后清理任务要求的临时文件，保留worktree供Manager验收归档。
- “讨论/只读调查/监控无需创建workspace”改成“无需创建worktree或代码环境”，因为task create仍自动分配空workspace。

用两三段简短句子放在对应操作附近，避免复述AGENTS/设计文档。不改已通过代码，不重跑全套测试，只核对README链接与diff-check。原worktree提交增量，更新report task_revision；独立review复核文档后集成安装。
