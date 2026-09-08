# 任务管理 CLI 实施

执行者：Ptolemy（gpt-5.6-terra max，agent 01a080d9-44a2-77f3-a185-737341387aaa）。
任务 UUID：f77ef844-83b6-485e-892f-d6c99d6e305e。workspace：/mnt/public/xcj/Projects/workspace/f77ef844-83b6-485e-892f-d6c99d6e305e；代码 worktree：其下 agent-workflow；分支 task/f77ef844-83b6-485e-892f-d6c99d6e305e；目标 main。

## 范围与接口

负责 scripts/task.py、必要辅助模块（除 scripts/job_runtime.py）、核心标准库测试及 agent-workflow 自己的简易环境入口。沿用旧 ws.py 有价值的 Git/路径处理，最终仅交付新接口，不保留 ws.py/旧命令。AGENTS.md、README.md 和接口文档由 Manager 维护。

完整实现接口文档的 create（含 --review）、bind、workspace add、show、publish、list、status、archive，以及 job add/list/archive 的登记/CLI 部分。以最新文档的 --note 为准（用户已在文档统一参数）；不存在 start/accept/cancel/check/code-only/job finish/--agents。task/job UUID 自动生成；分支 task/<task-uuid>。

## 明确行为

- 管理数据在稳定原仓库 .local/tasks/<uuid>.json，task/report 在 .tasks/<uuid>/。从自己的 worktree 执行也定位同一原仓库；允许测试注入临时管理根，不新增环境变量。日常入口 python scripts/task.py，JSON 输出便于 Manager 使用。
- create 先登记 UUID 与 workspace 再创建，错误保留可解释的记录。bind 一对一。workspace add 调对应原仓库三参数 .local/create_worktree.sh，创建前记录本任务 repo/base/branch/path，避免半失败资源游离；重试不误认既有非本任务分支。repo 限定本集群四库及 agent-workflow。既有环境数据不改。
- agent-workflow 的版本化环境入口可用少量 shell，三参数本地 wrapper 委托它，使用共享持久 Python 创建私有 venv，标准库无需安装业务依赖。不要为了它引入包管理框架。
- main 是发布版本。publish 加全局锁，用临时 Git index 提交指定 task.md 或 report.md，并用比较旧 SHA 的 update-ref 更新 main；保留其他文件草稿和共享暂存区，避免丢掉其他发布者提交。共享工作目录不切版本。不能把 --only commit 当成已验证的共享 index 隔离。
- show 输出文件内容与发布 commit。report 首行 task_revision: <40位SHA>；publish report 验证该版本包含本任务已发布说明，保存此关联及登记 worktree 的交付 HEAD；未声明版本时明确报错，不默认为最新。status 比较该 task.md 内容是否变化，不能因其他任务提交而报过期。
- --review 新建普通任务，在 task 草稿写入源任务说明、已发布简报的固定版本及交付 commits；要求未发布的源成果时明确报错。
- archive 按登记的仓库+分支名删除本任务分支，移除登记 worktree、独立环境和空 workspace；保留任务/简报及 job 状态历史。无 accept/review/合入状态等业务 gate；安全删除的路径归属、未提交代码和仍运行的登记进程检查保留。不要强删未提交代码、未知目录或沿软链接删除共享实体。部分失败可重试；结果包含实际移除项。临时 smoke/实验产物清理由执行者负责。
- 删除分支后仅写 SHA 不能永久保留代码；是否保留/合入成果由 Manager 根据任务要求决定，本工具不新增自动备份 tag 或代码快照。
- job 为一个登记进程，存多个 job，每个 job-id 独立；进行中/已停止由查询更新，执行者 --note 归档后保持已归档。--attention 筛选 stopped 且 agent 非 active，未知单列待核实；只读查询绝不自动发送 turn/start。

## 与进程模块的协作契约

另一个执行者仅提供 scripts/job_runtime.py（无需你的存储函数）：
- probe_process(host: str, pid: int, identity: dict | None = None) -> dict，返回 status=running/stopped/unknown, identity, checked_at, error。identity 含主机 boot_id 和 /proc start_ticks。
- probe_agents(agent_ids: list[str], socket_path: str | None = None) -> dict[str, dict]，每项返回 status=active/idle/notLoaded/systemError/unknown, checked_at, error。默认连接本机现有 app-server socket。
所有输出 JSON 可序列化。你负责调用与持久登记；模块负责读取 OS/App Server。不要修改另一个执行者文件。

## 验证

有意义的临时真实 Git 测试：两个任务并发发布互不丢失，其他草稿和 staged 内容保留；版本固定与修改要求后的报告关联；review 引用不漂移；多个 repo 创建、半失败可查/重试；归档删除独占分支且共享 symlink 实体保留；dirty/未登记目录拒绝；无业务 accept gate。测试自己清理。目标核心实现约 650–850 行，测试约 200–350 行；确有必要超过先告知 Manager，不靠机械压行达标。

初始化例外：工具尚不存在，Manager 已手动发布本任务并登记这次实现的 workspace。先把既有 ws.py 工作保存成自己的提交，再基于 main 开发；初次 task/report 发布由 Manager 初始化，后续切换到新 CLI。该例外不做长期兼容功能。

## 共同交付约定

按 main 上发布的本任务和 docs/task-management-design.zh-CN.md 实施。报告写回稳定管理库本任务目录 report.md，首行 task_revision: <所依据任务的完整 commit>，随后写完成/未完成、workspace、各库完整交付 commit、验证结论与成果位置。工具可用后通过 CLI 发布；代码只在自己的 worktree 提交。

先读管理库 AGENTS.md，跨库先读目标库 AGENTS.md 及对应规范。追加要求只以 Manager 发布后的任务文件为准。自身测试产生的文件及进程自行清理，保留待 Manager 归档的工作区。无需 GPU，不修改现用训练/评测环境和进程。没有常驻服务、自动唤醒、额外权限系统、环境 provenance 或旧 CLI 兼容层。

## 归档接口补充裁决

统一 archive 也承接取消任务：允许 Manager 归档尚未绑定执行者或尚未发布 report 的任务；不以简报、验收或合入状态作为代码 gate。安全删除检查仍属于具体操作本身。请覆盖空任务创建后直接归档，以及存在已提交独占分支但无 report 的归档；不要继承旧 ws.py 的交付/接收前置条件。

## 查询契约补充

进程 probe 的 status 是判断依据：stopped 的 error 字段可以说明不存在、zombie、PID身份变化等停止原因，不代表查询失败；只有 unknown 才表示不能确认。核心不得因 stopped 带诊断文本而不更新状态或阻止 job/task archive。远端查询必须区分“进程不存在”和“存在但不可读”：权限/读取失败返回 unknown，不能把单个 -r 检查失败一律当 stopped。

## 发布暂存区修订

Manager 修订此前对共享 index 的过度约束：应保留其他文件的 staged 内容和所有工作目录草稿，但本次已发布文件的 index entry 应同步到发布版本。当前 runtime report 发布后，稳定管理库 git status 同时显示该 report 为 staged 删除与 untracked，后续普通提交可能删除已发布报告。

请修复 publish 的正常与 unchanged 两条路径：只同步本次文件的 index entry，不 reset 整个 index、不覆盖工作目录。追加真实 Git 回归：其他文件 staged 内容保留，并发发布无丢失，发布后正常代码提交不会删除/回退任务文件。已有报告的异常 index 可用修复后的 unchanged publish 定向恢复，不写兼容层。修复完成后通过你的 worktree CLI 发布本任务要求（unchanged）和你的最终报告。Manager 负责其余已发布报告的定向同步及代码合入。
