# 空白review MAM手册术语及status精简

Review fixed source delivery:
{
  "task": "66743086-e895-4cfe-b2e8-fad92bd0c852",
  "task_revision": "a3336b1117fe433a4ea6673f0daab455b5ea5550",
  "report_revision": "f8a9e972ebeef60547b9a8593cf921c81cada64d",
  "commits": {
    "multi-agent-manager": "b338dbdd4398af307fd070606288101b8c1d2901"
  }
}

Source task:

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

Source report:

task_revision: a3336b1117fe433a4ea6673f0daab455b5ea5550

完成：README 精简为操作手册；统一 TASK-ID、JOB-ID、AGENT-ID 术语与 CLI metavar、help、错误和表头；新增长任务保持 active turn 的 wait 规则；task/job status 改为精简 JSON 展示投影，保留缓存/unknown 语义与归档、review、交付信息。

workspace: /mnt/public/xcj/Projects/workspace/66743086-e895-4cfe-b2e8-fad92bd0c852/multi-agent-manager
commit: b338dbdd4398af307fd070606288101b8c1d2901
改动文件：AGENTS.md、README.md、docs/task-management-design.zh-CN.md、multi_agent_manager/cli.py、tests/test_task.py。

验证：`.venv/bin/python -B -m unittest discover -s tests -v` 通过（32 tests）；递归运行 20 个 `mam` 顶层/子命令 `--help`；`git diff --check` 通过。
# 独立review执行

以本任务固定的source要求/report/commit b338dbdd4398af307fd070606288101b8c1d2901做空白验收。读AGENTS/README，通过mam workspace add创建自己的multi-agent-manager worktree。只读源码，不修改实现、不安装、不占GPU、不派agent。临时root做实际CLI验证；不要用真实MAM任务作可变数据。

先按README实际找常用命令（job list --task、task/job status、wait jobs/list/stop），判断操作手册是否简洁/清晰、没有字段规格冗余。递归help核对TASK-ID/JOB-ID/AGENT-ID统一、metavar不改dest、AGENTS等待规则只在需要保持active turn时适用、不强制每个subagent等。设计文档对应接口与术语一致。

重点status投影：实际临时数据验证正常/unknown（保留具体error及lastknown）/archived/review/requirements_changed/workspace交付版本；task status不触发进程探测，只汇总未归档job、缓存语义清楚；job status仍只刷新目标。不能把最新unknown误写旧running，不丢定位路径/版本/收尾异常。不为正常状态dump内部identity/probe或重复revision。列表/其他命令逻辑保持不变。

结合diff检查，必要回归一次，避免纯文案重复大量测试和遍历。结果GO/NO-GO、具体阻塞与建议、简短命令证据/workspace/commit写report并发布。清理临时root/进程/pycache，留干净worktree供归档。Manager检查实际轨迹，别进行无目的搜索。
# 文档增量复验

原b338dbdd代码/help/status已通过，源要求新revision 2e29129286945eec128f2fd04efe194ec923007c，文档修复commit 9d2a2fc（先用git解析完整ID），交付report publication 89db7af。复用本worktree快进到该commit，只核对你报告的README必要操作说明与workspace措辞、链接/diff；不重跑模型、32测试或全部help。发布最终GO/NO-GO并在report注明最终完整commit与实际source版本。原NO-GO保留历史即可。
