# MAM可停止等待与列表详情接口
# MAM 可停止等待与列表详情

## 范围
实现用户确认的接口，保持标准库、小规模实现，不新增daemon/数据库/通用调度框架。通过mam workspace add创建本任务multi-agent-manager独立worktree，base 312355ce6b2b6db1d12f4f4c3248f4c1f92ce396。读AGENTS/README开发验证；只在独立树修改代码、必要测试和文档，不安装系统版、不修改真实实验进程，不派agent。Manager负责后续独立review、合并和安装。

## 等待
- `mam wait jobs [--task <task-id>] [--timeout <seconds>] [--agent <agent-id>]`：默认等待所有未归档job；按task可缩小范围。已有确定停止但未归档job立即返回；运行中任一job停止则返回；超时返回timeout；没有匹配job立即返回明确empty，避免永久空等。未知探测不能误判停止。不用每轮探测agent状态，只检查必要job。
- 自动等待者ID读取CODEX_THREAD_ID，--agent可显式覆盖；缺失或非法明确报错。先报告自己shell读到的CODEX_THREAD_ID，由Manager与spawn返回ID交叉核对；不能用继承的根CODEX_SESSION_ID猜身份。
- `mam wait list`：有表头，每个当前等待一行，列顺序agent-id、绑定task标题、task-id、等待内容、等待开始时间。等待者通过未归档task的agent绑定关联；未绑定显示未绑定，不伪造manager身份。等待者与被监控job负责人分开。
- `mam wait stop --agent <agent-id>`：只唤醒该agent的等待，返回cancelled。不能向job进程发信号、不能归档job。每agent仅一个活跃等待；无需wait UUID。没有等待时明确返回未在等待。
- 本机共享.local下保存临时等待登记/取消标记，进程身份核对与锁保证并发start/stop/退出清理不误取消后来等待。等待退出清理；异常退出的陈旧登记不得显示为仍在等待或阻止重开。等待轮询由普通Python执行，不依赖LLM；不持有任务锁睡眠、不阻塞其他mam命令。stop响应目标约2秒内，不能被长SSH探测无限拖住。实现采用最小合理办法，若需要显著扩大框架先报告。

## 列表与详情
- task list保留既有筛选，一行五列并新增表头：标题、task状态、UUID、agent、agent状态。移除task list --json；详情走task status，其保存的job观测不做隐式刷新。
- job list保留task/status/attention筛选，默认有表头，一行六列：描述、job状态、开始时间、job-id、task描述、task-id。开始时间用实际进程启动时间，无法转换显示unknown，不用登记时间冒充。未知探测需明确显示unknown/待核实而非冒称running/stopped；attention的不确定项保持可见且区别明确。
- 新增job status <job-id>：完整JSON登记与实时探测结果/checked_at/identity/所属task与agent等必要信息，刷新该job，不扫描无关进程。job list不用新增--json。task show正文/既有--json暂保留，它与列表详情不同，避免无关破坏。
- task/job/wait list即使空也有表头；单元格空白/换行清理保持物理单行，UUID不截断。其他输出格式、task/job存储和发布/归档协议尽量不动。

## 文档与验收
同步更新docs/task-management-design.zh-CN.md（用户明确指定）及README/CLI help的必要差异，中文简洁，列清接口行为；AGENTS仅必要入口改动，避免重复手册。
临时root真实CLI验证：表头/单行/筛选/详情；真实短sleep注册job，wait因job停止返回；另进程stop唤醒且被监控sleep仍活着；两个agent等待互不干扰；重复等待、超时、空集、已有stopped、unknown与陈旧登记。不得用真实MAM根做可变测试，不占GPU。完整标准库单测和diff-check。清理临时root/进程/pycache；提交干净commit和report，包含task_revision、workspace/HEAD、变更文件、验证及明确剩余限制。代码规模保持克制，超过约300行新增生产代码前报告取舍，不以压缩代码凑行数。
## 独立review后的修复裁定

独立review报告8ecd5775172717b4c39b905f2bf2891a95e65c07（任务362daf44-9644-41b7-9ec9-8893bea1abb4）提出两个成立的问题，修复后复验：
1. wait deadline应在每次target探测前检查，单次远端探测timeout不得超过剩余预算；多个remote下不能按每job固定0.5秒逐个超出总deadline。超时允许运行时小幅调度开销，不要求硬实时。
2. job list --attention的needs_verification必须在表格明确标为待核实，包含job已经stopped但agentunknown的情况；不新增列、不把不确定记录展示为普通待处理stopped。

保持其他接口与已验证并发取消/正常远端探测行为；增加对应有意义回归并同步文档措辞如必要。只在原worktree增量修复，不安装、不占GPU、不修改真实job。生产净增336行接受为本轮实现上限附近，不扩框架；优先小修。提交新commit、清理并更新report。源review真实wuwen-1短sleep的0.5秒探测12/12通过，最长0.314秒，不需要为假想网络问题重写异步框架。
