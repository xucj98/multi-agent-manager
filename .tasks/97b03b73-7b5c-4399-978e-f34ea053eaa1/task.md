# 独立审阅 manager wait stop 与本地README链接

Review source delivery (source TASK-ID: 6da83d0f-1996-4e15-a229-62729846018a):
{
  "task": "6da83d0f-1996-4e15-a229-62729846018a",
  "commits": {
    "multi-agent-manager": "963f619f2356822ce628682cdb073f4a46417582"
  }
}

Source task requirements:

# Manager wait 快捷停止

从 MAM main 9f2ebe1b489054886e7bcfdb22dcf39703d5eb06 创建独立worktree。当前生产MAM根 /mnt/public/xcj/Projects/multi-agent-manager，项目发布分支project/state-vla，任务/报告在生产根编辑发布。实现提交只基于main；不要把项目分支合回main。

## 实施
1. 增加 `mam wait stop manager`，保留 `mam wait stop --agent AGENT-ID`。二者互斥且必须选一种。按当前MAM中有效wait记录及当前未归档task绑定，识别未绑定task的等待agent，恰好一个则停止该等待。无候选或多个均明确报错，不需要用户先wait list。不能把wait的--task过滤参数误当成agent绑定。若身份无法确认不能默默选另一个。复用现有PID/identity/token/锁保护，处理检查后wait已结束的正常竞争，不误停替换后的新等待。不引入manager注册表/daemon或外部agent查询；不停止任何被监控job。
2. scripts/create_worktree.sh 为新MAM worktree可选地建立 .local/README.md 单文件软链接，指向源MAM根的本地README（存在时）；不共享整个.local。缺失时允许创建，不覆盖已有冲突文件。保持MAM上下文隔离及归档安全：验证这个受控软链不会让正常mam task archive失败；必要时最小调整认可方式，不放宽未知文件/任务数据保护。

## 范围与验收
实现/脚本/测试/设计文档由你负责，README/AGENTS由Manager负责（用户刚修改了生产README，不碰它）。完整测试，覆盖唯一manager、零/多候选、绑定执行者排除、身份不明/结束竞争、只停止等待不停止jobs、两项目隔离，及本地README链接/缺失/冲突与归档。实际短进程验证stop manager快速返回且job仍运行，不用GPU。不增加大量镜像测试或重复验证。

## 交付
提交代码，发布报告记录commit、改动文件、验证与限制。清理短测试产物/缓存，保留worktree待review。不要自行合并安装。

Source report:

# 交付简报

代码交付：`963f619f2356822ce628682cdb073f4a46417582`（`task/6da83d0f-1996-4e15-a229-62729846018a`）

完成内容：

- 增加 `mam wait stop manager`。它只从当前未归档 task 未绑定的有效等待中选择唯一目标；零个、多个或身份无法确认都会明确报错。`--task` 仅作为监控过滤，不参与绑定判断；保留 `mam wait stop --agent AGENT-ID`，且两种目标必须二选一。
- manager 模式复用现有 agent 锁、PID、identity 与 token。选中后重新核对记录；原等待结束或被替换时返回 `not_waiting`，不会取消替换后的等待，也不会向被监控 job 发信号或归档 job。
- `scripts/create_worktree.sh` 在源 MAM 根存在 `.local/README.md` 时，只在新 worktree 建立该单文件软链接；源文件缺失或目标冲突时继续创建且不覆盖。归档只认可这个精确、目录内唯一的受控链接，未知 `.local` 内容仍会拒绝归档。
- 更新任务管理设计文档和测试；未修改 Manager 维护的 `README.md`。

改动文件：

- `multi_agent_manager/cli.py`
- `scripts/create_worktree.sh`
- `tests/test_task.py`
- `docs/task-management-design.zh-CN.md`

验证：

- `.venv/bin/python -B -m unittest discover -s tests -v`：41 项通过。
- 真实本地短进程 smoke：`mam wait stop manager` 在 2 秒内返回；对应等待被取消，绑定执行者等待和被监控 job 保持运行。
- 集成测试覆盖两个项目配置隔离、唯一/零/多候选、绑定排除、身份未知、结束与替换竞态，以及本地 README 的链接、缺失、冲突和归档保护。

限制：manager 模式只使用当前 MAM 根的本地 wait/task 记录，不查询外部 agent，也不管理 job 生命周期。

成果位置：`/mnt/public/xcj/Projects/workspace/6da83d0f-1996-4e15-a229-62729846018a/multi-agent-manager`

## Manager 独立验收要求
你是新建空白reviewer，读取源任务最新要求及报告，独立worktree审阅963f619f2356822ce628682cdb073f4a46417582。作者额外建立55fc871a review任务但未绑定独立agent，Manager不采信其“独立”结论；不要复用该任务的工作区和结论。
复验manager唯一选择/错误/绑定task与过滤差异、等待竞争/PID/token、只取消等待而job仍运行，及local README精确软链与归档边界。完整测试加实际短进程独立验证；不占GPU。README/AGENTS由Manager维护不修改；根据最新main的dce696a文档核对无冲突。无问题给GO及证据；有问题先报告Manager裁决。代码报告需给交付commit和自己的实际workspace。清理临时缓存，保留工作区待归档，不自行合并安装，也不再创建review任务。
