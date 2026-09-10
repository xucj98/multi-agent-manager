# 独立review MAM等待停止与简表接口

Review fixed source delivery:
{
  "task": "706acdff-5946-4533-9c46-3c5a575b450e",
  "task_revision": "9f56caad79d2bb55a5ecb16829dfe60301456d9c",
  "report_revision": "b6aede5206c16772124767634daeea0da0fe426c",
  "commits": {
    "multi-agent-manager": "1b8f4265dde093736dff2e0d77d185d9e640a6a8"
  }
}

Source task:

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

Source report:

task_revision: 9f56caad79d2bb55a5ecb16829dfe60301456d9c

完成与未完成：
- 完成 `mam wait jobs/list/stop`：以 `CODEX_THREAD_ID` 自动识别等待者，支持显式覆盖、超时、空集、已停止、取消、陈旧登记清理和每 agent 单活跃等待。
- 完成 task/job/wait 三类表格输出、`job status <job-id>` 的单 job 实时 JSON 查询，以及真实进程启动时间记录与 unknown/待核实显示。
- 更新 README 和 `docs/task-management-design.zh-CN.md`；未修改 AGENTS、真实 job、系统安装或 GPU 配置，也未派发 agent。
- 未完成项：无。

workspace、各库交付 commit：
- `/mnt/public/xcj/Projects/workspace/706acdff-5946-4533-9c46-3c5a575b450e/multi-agent-manager`
- `multi-agent-manager`：`1b8f4265dde093736dff2e0d77d185d9e640a6a8` (`Add stoppable job waits and list details`)

变更文件：
- `multi_agent_manager/cli.py`、`multi_agent_manager/job_runtime.py`
- `tests/test_task.py`
- `README.md`、`docs/task-management-design.zh-CN.md`

验证结果与成果位置：
- `.venv/bin/python -B -m unittest discover -s tests -v`：30 项通过；测试使用临时 root 和短 sleep，覆盖表头/单行/筛选/详情、停止不影响被监控进程、双等待者隔离、重复等待、超时、空集、已停止、unknown 与陈旧登记。
- `git diff --check`、语法编译和 CLI help 检查通过；临时 root、测试进程和项目 `__pycache__` 已清理。

剩余限制与取舍：
- 等待使用 `.local/waits` 的文件锁、PID 启动身份和 token，不引入 daemon、数据库或调度框架；远端等待探测限制为 0.5 秒，保证 stop 不会被长 SSH 查询无限阻塞。
- 为同时实现并发取消防串扰、陈旧清理、短超时远端探测、实际启动时间和新接口测试，生产代码 diff 为新增约 361 行、删除 25 行（净增约 336 行），略超过约 300 行的规模提示；未新增第三方依赖或独立框架。
# 独立验收要求

阅读本任务固定引用的源task/report，不继承实现者对正确性的结论。通过mam workspace add为本任务创建multi-agent-manager独立worktree，base 1b8f4265dde093736dff2e0d77d185d9e640a6a8。只读review，临时root真实CLI测试，不改源码、不安装系统、不占GPU、不派agent。先读AGENTS/README开发验证。

核心验收：三个list表头/物理单行及空集；job status只探测目标并保持未知状态诚实；task list取消--json且status仍完整；wait的自动agent身份（你的shell CODEX_THREAD_ID与MAM绑定交叉核对）、同agent重复、双agent隔离、stop不终止job、stop/start竞态与异常残留、timeout/empty/已有stopped/远端unknown。真实多进程测试stop响应，不仅mock。关注等待对多个SSH job是否可实际工作，0.5秒远端超时不能使正常本集群wuwen-1永远unknown；可用wuwen-1的自己短sleep做非GPU验证，但不得触碰既有实验或MAM真实job。没有权限/条件则明确未验。

检查实现必要性与简洁性（净增336生产行略超预算，指出具体可删冗余而非为了行数压缩）；中文README/指定设计文档/CLI帮助一致，无歧义。完整单测和diff-check只跑一遍除非发现问题。发布简短GO/NO-GO report，具体问题分阻塞与建议，含复现步骤、task_revision、workspace/commit、验证。清理自己的临时数据/进程/pycache再交付。Manager另检查实际工具轨迹。
