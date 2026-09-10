# Multi-Agent Manager（MAM）

MAM 提供 `mam task`、`mam workspace`、`mam job`、`mam wait`。本集群统一从本仓库启动 agent；所有 agent、代码修改和管理命令在本机运行，GPU 作业可通过 SSH 在 `wuwen-1` 运行。两端共享 `/mnt/public`，`wuwen-1` 无需安装 MAM。

[安装与更新](docs/install.md)。`mam` 可从任意目录调用，默认管理根目录为 `/mnt/public/xcj/Projects/multi-agent-manager`；全局 `--root <目录>` 可覆盖该位置，日常无需指定。

```text
multi-agent-manager/
  .tasks/<uuid>/task.md       # 任务要求，进入 Git
  .tasks/<uuid>/report.md     # 结果简报，进入 Git
  .local/tasks/<uuid>.json    # CLI 维护的状态，不进入 Git
  .local/waits/*.json         # 当前等待和取消标记，不进入 Git
Projects/workspace/<uuid>/<repo>/
```

## 任务管理

Manager 为每个 subagent 创建任务；每个 subagent 对应一个未归档任务及其 workspace。

```bash
mam task create --title "任务名称"
```

用编辑工具直接填写本管理仓库的 `.tasks/<uuid>/task.md`（`create` 返回的 `task_file`），写好后再发布、启动 agent 并绑定：

```bash
mam task publish <uuid> --file task
mam task bind <uuid> --agent <agent-id>
```

`task.md` 正文写目标、范围、交付和验收要求。UUID 与 workspace 路径由 CLI 提供，无需在正文重复。追加要求必须写入 `task.md`、发布后通知执行者。

Review 通过 `mam task create --title "…" --review <source-uuid>` 固定源任务的要求、简报和代码版本。验收后用 `mam task archive <uuid> --note "…"` 归档，该命令将同时删除任务的 worktree、环境和分支。

## 执行与交付

启动 prompt 提供 task ID。执行者先查询登记的 workspace、各库 worktree 路径，再读取已发布要求与版本：

```bash
mam task status <uuid>
mam task show <uuid>
```

以 CLI 返回的路径和发布要求为准。管理仓库共享 checkout：Manager 编辑 task.md，执行者编辑自己的 report.md；main 为发布版本，工作目录修改为草稿，均通过 `mam task publish` 发布。

完成后，清理任务要求的 smoke 和临时文件，用编辑工具直接填写本管理仓库的 `.tasks/<uuid>/report.md`，内容如下：

```text
task_revision: <mam task show 返回的 revision>
完成与未完成：……
workspace、各库交付 commit：……
验证结果与成果位置：……
```

这两个 Markdown 文件都在共享管理仓库中编辑；`mam task publish` 提交已经写好的文件。用 `mam task publish <uuid> --file report` 发布简报，保留工作区待 Manager 归档。工作记录统一放在本库 `.tasks/`，各业务库保留自己的规范和实验记录。

## 工作区

代码修改和独立 review 使用本任务的 worktree，已有工作区继续复用：

```bash
mam workspace add <uuid> --repo <repo> --base <commit>
```

每个库分别调用；该命令通过各库 `.local/create_worktree.sh` 创建独立环境和共享软链接。讨论、只读调查和监控无需创建代码环境。

## 进程管理

执行者通过 `mam job add <uuid> --note "用途" --host <host> --pid <pid>` 登记自己启动的长进程，同一任务可登记多个 job。

`mam job list` 有表头，每行依次为描述、job 状态、实际进程启动时间、job-id、任务描述、task-id；无法换算启动时间显示 `unknown`，探测失败显示 `unknown/待核实`。`mam job status <job-id>` 只刷新该 job，并以 JSON 输出登记、身份、实时探测、所属任务和 agent。进程停止后，执行者记录结果、处理临时文件，再用 `mam job archive <job-id> --note "处理结论"` 标记已处理。Manager 用 `mam job list --attention` 查找已停止、未处理且执行者已空闲的 job，通知负责人继续收尾。

## 等待

`mam wait jobs [--task <task-id>] [--timeout <seconds>] [--agent <agent-id>]` 等待当前未归档 job：已有确定停止的 job 立即返回 `stopped`，任一运行 job 停止时返回 `stopped`，无匹配返回 `empty`，超时返回 `timeout`。探测为 unknown 时不会当作停止。未给 `--agent` 时只读取 `CODEX_THREAD_ID`，不会从 `CODEX_SESSION_ID` 推测身份；ID 必须是非空单行文本。

`mam wait list` 即使为空也输出表头，列为 agent-id、绑定 task 标题、task-id、等待内容、等待开始时间。关联使用等待者自己的未归档 task 绑定，与其监控 job 的负责人无关；未绑定显示“未绑定”。`mam wait stop --agent <agent-id>` 只写入该等待者的取消标记并唤醒等待，返回 `cancelled` 或 `not_waiting`，不会向 job 进程发信号或归档 job。每个 agent 同时只能有一个等待；异常退出留下的登记会由 PID 启动身份检查清理。

具体参数按需查阅 `mam task --help`、`mam workspace --help`、`mam job --help`、`mam wait --help` 及相应子命令的帮助。

`mam task list` 即使为空也输出表头；每个任务一行，以制表符分隔标题、task 状态、完整 UUID、agent 和 agent 状态。详情使用 `mam task status`，其中保存的 job 观测不会隐式刷新。`task list` 不提供 `--json`。`mam task show` 默认先输出实际发布 revision，再原样输出 Markdown 正文；既有 `--json` 保留。

## 开发验证

MAM 使用 Python 标准库。在自己的 worktree 中运行 `.venv/bin/python -B -m unittest discover -s tests -v`。修改删除操作时，验证共享软链接目标、未提交文件、未登记目录和运行进程得到保护。
