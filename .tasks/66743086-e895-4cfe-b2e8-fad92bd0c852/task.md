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
