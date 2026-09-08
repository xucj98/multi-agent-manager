# 空白验收：任务 CLI、独立环境与文档

你是没有历史对话上下文的 gpt-5.6-terra max 执行者，任务 UUID 3b25605b-5f5c-4e38-baef-89409a9b2bb5。自己的 workspace 为 /mnt/public/xcj/Projects/workspace/3b25605b-5f5c-4e38-baef-89409a9b2bb5。目标是独立验收已集成成果，报告缺陷与证据；实现和文档改动由原作者及 Manager 处理。

## 固定输入与范围

先读稳定管理库 AGENTS.md、README.md 和 docs/task-management-design.zh-CN.md，再使用 CLI show 读取本任务的已发布版本。文档应让首次接触的人理解并独立操作；重点检查简洁、清晰、歧义和相互冲突，尤其各业务库 AGENTS 不包含公共任务管理或集中日志路径，不会因为读取入口就无条件创建环境和跑实验。

- agent-workflow 集成验收 base：48d188b0da406c150e07033e61235095bcc1e06f（已含核心72c0547、runtime d408bda、最终文档e74b330）。
- robot-bridge base：0095a3f4b2830ef9cc09cd77befff199e4391eba。
- 另外只读审阅原库文档固定提交：RMBench e0bcc0c02d957d51bb1b073410447fc3213c7126，opendm 5a4ee39d7416565f7d59004558460bc7219850d7，openpi 71c80db723a242c61cfe429dd6794e9ece3cbcf1。用 git show 读取，不切换原库版本。
- 同时核对源任务 f77ef844-83b6-485e-892f-d6c99d6e305e 和 runtime 91ba98dd-3356-493a-98e9-a5e9ea94f04b 的已发布要求与报告；下方为创建review时固定的源材料，只用于比较交付，不继承作者的修改职责。

## 独立验证

用户最新追加：管理库 .worklogs 已删除，README已移除保留旧日志的说明。源码验收仍固定48d188b；文档额外读取 main 上最新README及删除提交，不必为这一纯文档变更重新安装环境或重跑已通过代码测试。验证现行管理入口统一使用.tasks。报告注明实际依据的最新本任务发布版本。

1. 从文档出发，通过 task workspace add 在自己的UUID目录分别创建 agent-workflow 和 robot-bridge 两库完整环境；不复用作者工作区。固定输入 base 如上，使用各库三参数本地入口。记录安装结果、解释器真实可用、editable及共享软链接归属。
2. 在自己的管理库worktree跑完整标准库测试。在本机和 ssh wuwen-1 使用同一共享 .venv 执行管理CLI帮助/只读查询及 robot-bridge CPU基础smoke。无GPU，不操作现用正式实验、现用环境或数据实体。
3. 只启动自己的短时CPU测试进程，本机和wuwen-1各一个，实际通过CLI job add登记到本任务，验证running→stopped→archived；真实App Server查询自己的agent状态。测试停止/清理后记录结果并归档job。不要用新server或伪造agent状态冒充现场验证。
4. 独立review源码及真实Git测试，核对发布不会丢失他人草稿/暂存、不回退main任务；show固定版本及report关联；多库归档按登记分支而非任意当前分支、保留共享目标、dirty和活跃进程保护、失败可继续。测试使用自清理临时Git fixture。可通过本轮任务的最终Manager归档再次核对真实多库删除；你先发布报告并保留workspace待验收。
5. 本任务自行清理smoke产物/pycache/测试进程，发布report：首行实际任务revision，完成/未完成、两库workspace及完整HEAD、验证命令与结果、问题列表（严重度、证据和必要性）。有阻塞就报告具体问题，不擅自扩大功能或修改公共文档。报告必须区分通过、未覆盖、限制，不用“暂未发现”冒称验证。

最终交付给Manager简短结论。附录的源任务与报告是历史固定输入。

---

# 空白验收任务CLI与五库文档

Review fixed source delivery:
{
  "task": "f77ef844-83b6-485e-892f-d6c99d6e305e",
  "task_revision": "e8df35f74df2df27e3a6f2c5814fedc71031839e",
  "report_revision": "8ea98ac84002f85964e910f76e456f716aa09050",
  "commits": {
    "agent-workflow": "72c05473542ddb15a7c101c70e417f0bf8028d1f"
  }
}

Source task:

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

Source report:

task_revision: e8df35f74df2df27e3a6f2c5814fedc71031839e

# 任务管理 CLI 交付简报

已完成核心 CLI、标准库测试、agent-workflow 简易环境入口，以及本次“发布暂存区修订”。workspace：`/mnt/public/xcj/Projects/workspace/f77ef844-83b6-485e-892f-d6c99d6e305e`；唯一代码 worktree：其下 `agent-workflow`；分支：`task/f77ef844-83b6-485e-892f-d6c99d6e305e`。

完整交付 commit：`72c05473542ddb15a7c101c70e417f0bf8028d1f`。本次修复只修改 `scripts/task.py` 和 `tests/test_task.py`，基于此前交付 `5c460b1ab3a3e6c885b76560f8de234ee10a3fd6`。公共文档、其他任务及业务库未修改。

## 本次修复

`publish` 继续用临时 index 创建指定任务文件的提交，并通过比较旧 SHA 的 update-ref 更新 main。正常发布完成后，仅把本次文件的共享 index entry 更新为实际发布的 blob；`unchanged` 路径执行相同的定向同步，恢复 staged 删除或旧 blob 的异常状态。

其他文件的 staged 内容保持原样。所有工作目录草稿保持原样；发布过程中对本次文件产生的新编辑仍为未暂存草稿，不会被误发布或覆盖。修订后的约束是“保留其他文件的 index entry”，不再要求整个 index 文件字节不变。

新增回归先在旧实现上复现缺失/过期 index entry，修复后通过。测试覆盖 task/report 两种文件、删除/旧内容两类异常、unchanged 不产生新发布 commit、其他 staged 内容与草稿保留、并发发布，以及后续普通代码提交不会删除或回退已发布文件。

## 整体接口与行为

- `create --title TITLE [--review UUID]`；`bind UUID --agent ID`；`workspace add UUID --repo REPO --base COMMIT`。
- `show UUID [--file task|report] [--revision COMMIT]`；`publish UUID --file task|report`；`list [--archived|--all]`；`status UUID`。
- `archive UUID --note TEXT`；`job add UUID --note TEXT --host HOST --pid PID`；`job list [--task UUID] [--status running|stopped|archived|all] [--attention]`；`job archive JOB_UUID --note TEXT`。

统一入口为 `python scripts/task.py`，可用全局 `--root ROOT` 注入测试管理根。UUID 自动生成，linked worktree 与稳定主库使用相同状态目录。创建前记录资源意图，部分失败可查询与重试，review 固定源任务、报告和交付 commits，报告必须明确 task_revision。

统一 archive 包含取消任务：无报告、绑定、验收或合入状态 gate。全库预检保护 dirty/untracked、未知 ignored 实体和外层目录，允许独立 .venv 和 gitignored 共享软链接；移除登记 worktree 及对应任务分支，保留任务和 job 历史。进程查询以 status 为准，stopped 携带诊断仍可归档，unknown 保留上次确认状态和时间。

环境入口为 `scripts/create_worktree.sh`，三参数 wrapper 模板为 `scripts/local_create_worktree.sh`，已安装到稳定库 `.local/create_worktree.sh`；使用共享持久 CPython 3.10.19 创建私有 venv，不安装业务依赖。旧 ws 接口已删除。

## 本次验证

在上述代码 worktree 根目录执行：

```bash
python3 -B -m unittest discover -s tests -p test_task.py -k 'publish' -v
python3 -B -m unittest discover -s tests -p test_task.py -k 'parallel' -v
git diff --check
```

两项定向测试通过（随后又新增了发布期间编辑草稿的回归），空白检查通过。最终完整核心套件运行命令为：

```bash
python3 -B - <<'PY'
import sys
import unittest
sys.path.insert(0, '/mnt/public/xcj/Projects/agent-workflow/scripts')
suite = unittest.defaultTestLoader.discover('tests', pattern='test_task.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
PY
```

结果：12 项，11 项通过、1 项跳过，耗时 7.309 秒。跳过项为真实进程契约测试：运行时稳定库尚未集成并行交付的 `job_runtime.py`。发布相关三个测试及原有版本/review、多库/部分失败重试、归档安全、真实私有 venv smoke 等测试全部通过。此前已只读对接 Erdos 工作树，验证两个自建进程 running → stopped → archived，现有 App Server 查询返回 active；本次未扩展进程模块验证。

实现 582 行，核心测试 337 行。测试数据由 TemporaryDirectory 清理；本次未留下测试进程、临时文件或环境。代码工作树在提交后干净，保留待 Manager review 和归档。

## 发布与剩余事项

已通过本 worktree CLI 执行 `publish f77ef844-83b6-485e-892f-d6c99d6e305e --file task`，返回 `unchanged: true`，版本仍为 `e8df35f74df2df27e3a6f2c5814fedc71031839e`，只恢复本任务说明的 index entry。本报告随后通过同一入口发布。

本次修复无未完成项。`job_runtime.py` 的代码集成、其他任务历史报告的定向 index 同步由 Manager 负责；本分支未复制或修改该模块。部分环境恢复仍由各库本地入口负责，未知临时产物由执行者处理。任务分支归档后仅保存 SHA，不建立备份引用，成果保留与集成由 Manager 决定。
