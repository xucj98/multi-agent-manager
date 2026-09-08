# 本集群的 agent 任务管理

用文件和 CLI 管理任务要求、结果简报、workspace 和长任务进程。`task.md`、`report.md` 随 Git 保存；任务状态、agent 绑定和进程登记放在被 Git 忽略的 `.local/tasks/`。完整参数见 [CLI 说明](docs/task-management-design.zh-CN.md)。

## 集群与目录

本机和 `wuwen-1` 共享 `/mnt/public` 下的代码、数据、解释器及缓存。环境只需创建一次，两端可使用同一个 worktree 的 `.venv`；查询进程时须指定实际运行主机。

```text
/mnt/public/xcj/Projects/
  agent-workflow/
    .tasks/<uuid>/task.md       # Manager 编写的任务要求
    .tasks/<uuid>/report.md     # 执行者编写的结果简报
    .local/tasks/<uuid>.json    # CLI 维护的状态
  workspace/<uuid>/
    <repo>/                    # 分支 task/<uuid>，含独立 .venv
```

repo 可选 `RMBench`、`opendm`、`openpi`、`robot-bridge`、`agent-workflow`。各库保留自己的安装脚本和软链接规则；本地 `.local/create_worktree.sh` 提供本集群路径。任务要求和工作记录统一写入 `.tasks/`。

## 创建和执行任务

以下命令从管理仓库执行，使用系统 Python 标准库，无需安装额外依赖。`<uuid>`、`<agent-id>`、`<commit>` 替换为实际值；输出为 JSON。

```bash
cd /mnt/public/xcj/Projects/agent-workflow
python -B scripts/task.py create --title "任务名称"
```

Manager 用编辑工具填写返回路径中的 task.md：目标、涉及库及 base commit、工作范围、验证和交付要求。发布后启动 subagent，将任务 UUID 和管理仓库路径交给它，再登记返回的 agent ID：

```bash
python -B scripts/task.py publish <uuid> --file task
python -B scripts/task.py bind <uuid> --agent <agent-id>
```

执行者先读取发布要求，再按任务需要添加各库 worktree；无需在共享管理目录切换分支：

```bash
python -B scripts/task.py show <uuid>
python -B scripts/task.py workspace add <uuid> --repo robot-bridge --base <commit>
```

workspace add 调用所选库的 `.local/create_worktree.sh <base-commit> task/<uuid> <workspace-root>`，创建源码、独立环境及共享链接。之后在返回的 worktree 内工作。各库环境说明列出基础检查命令，验证范围由任务决定。

## 发布简报与 review

大家在共享管理目录编辑各自负责的文件。`main` 上的版本是已发布内容，未发布的编辑是草稿。发布只提交指定文件，并保留其他文件的草稿和暂存内容；任务要求变化后，Manager 重新发布并通知执行者。

report.md 首行必须填写实际依据的任务 commit，正文可按以下格式编写：

```text
task_revision: <show 返回的40位任务 commit>

完成：……
未完成：……
workspace：……
交付：每个库的完整 commit、成果位置。
验证：实际执行的检查、结果及限制。
```

```bash
python -B scripts/task.py publish <uuid> --file report
python -B scripts/task.py show <uuid> --file report
python -B scripts/task.py status <uuid>
```

发布报告后任务为 `pending`（待验收）；`status` 显示报告依据的要求是否已变化。工具同时记录登记 worktree 的 HEAD，正文中的交付 commit 应与其一致。

Manager 创建 review 任务时，可固定源任务已发布的要求、简报和代码引用：

```bash
python -B scripts/task.py create --title "独立验收" --review <source-uuid>
```

在新任务中补充验收要求并发布，绑定另一名执行者。review 使用自己的 UUID workspace，交付方式与其他任务相同。

## 长任务进程

job 是执行者登记的一个进程，可为同一任务登记多个。CLI 查询进程和 agent 状态；进程启动、通知执行者继续工作由调用方完成。

```bash
python -B scripts/task.py job add <uuid> --note "正式评测" --host wuwen-1 --pid <pid>
python -B scripts/task.py job list --task <uuid>
python -B scripts/task.py job list --attention
python -B scripts/task.py job archive <job-id> --note "已记录结果并清理临时文件"
```

job 状态为 `running`（进行中）、`stopped`（已停止，待处理）、`archived`（已归档）。查询使用主机、PID 和启动身份判断；查询失败会显示错误并保留上次确认结果。`--attention` 返回已停止、未归档且执行者不再 active 的 job，未知状态放在 `needs_verification` 中。执行者仍 active 时由其自行处理。

agent 状态通过现有 Codex App Server 的 `/root/.codex/app-server-control/app-server-control.sock` 只读查询。工具按调用时查询，无后台轮询或自动唤醒。

## 查看与归档

```bash
python -B scripts/task.py list
python -B scripts/task.py list --archived
python -B scripts/task.py archive <uuid> --note "验收通过，成果已合入"
```

默认列表显示未归档任务：`working`（进行中）或 `pending`（待验收）；归档后为 `archived`。Manager 用同一个 archive 接口记录完成或取消的结论。工具移除登记的各库 worktree、独立环境、`task/<uuid>` 本地分支和空 workspace；保留任务文件、报告、job 历史及软链接目标。

存在未提交文件、未登记目录或仍在运行／无法确认的登记进程时，工具返回具体原因；部分清理失败可再次调用同一命令继续。临时文件按任务处理。历史任务的要求和报告始终可用 `show --revision <commit>` 读取。
