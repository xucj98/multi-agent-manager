# Multi-Agent Manager（MAM）

MAM 提供 `mam task`、`mam workspace`、`mam job`。本集群统一从本仓库启动 agent；所有 agent、代码修改和管理命令在本机运行，GPU 作业可通过 SSH 在 `wuwen-1` 运行。两端共享 `/mnt/public`，`wuwen-1` 无需安装 MAM。

[安装与更新](docs/install.md)。`mam` 可从任意目录调用，默认管理根目录为 `/mnt/public/xcj/Projects/multi-agent-manager`；全局 `--root <目录>` 可覆盖该位置，日常无需指定。

```text
multi-agent-manager/
  .tasks/<uuid>/task.md       # 任务要求，进入 Git
  .tasks/<uuid>/report.md     # 结果简报，进入 Git
  .local/tasks/<uuid>.json    # CLI 维护的状态，不进入 Git
Projects/workspace/<uuid>/<repo>/
```

## 任务管理

Manager 为每个 subagent 创建任务，填写返回路径中的 task.md，再发布要求、启动 agent 并绑定；每个 subagent 对应一个未归档任务及其 workspace。

```bash
mam task create --title "任务名称"
mam task publish <uuid> --file task
mam task bind <uuid> --agent <agent-id>
```

任务正文写目标、范围、交付和验收要求。UUID 与 workspace 路径由 CLI 提供，无需在正文重复。追加要求必须写入任务、发布后通知执行者。

Review 通过 `mam task create --title "…" --review <source-uuid>` 固定源任务的要求、简报和代码版本。Manager 验收简报后，用 `mam task archive <uuid> --note "…"` 归档，删除任务的 worktree、环境和分支，保留记录及软链接指向的共享数据。

## 执行与交付

执行者以 `mam task show <uuid>` 返回的已发布要求为准。管理仓库共享 checkout：Manager 编辑 task.md，执行者编辑自己的 report.md；main 为发布版本，工作目录修改为草稿，均通过 `mam task publish` 发布。

完成后，清理任务要求的 smoke 和临时文件，在 report.md 写明：

```text
task_revision: <mam task show 返回的 revision>
完成与未完成：……
workspace、各库交付 commit：……
验证结果与成果位置：……
```

用 `mam task publish <uuid> --file report` 发布简报，保留工作区待 Manager 归档。工作记录统一放在本库 `.tasks/`，各业务库保留自己的规范和实验记录。

## 工作区

代码修改和独立 review 使用本任务的 worktree，已有工作区继续复用：

```bash
mam workspace add <uuid> --repo <repo> --base <commit>
```

每个库分别调用；该命令通过各库 `.local/create_worktree.sh` 创建独立环境和共享软链接。讨论、只读调查和监控无需创建代码环境。

## 进程管理

执行者通过 `mam job add <uuid> --note "用途" --host <host> --pid <pid>` 登记自己启动的长进程，同一任务可登记多个 job。

`mam job list` 查询进程状态。进程停止后，执行者记录结果、处理临时文件，再用 `mam job archive <job-id> --note "处理结论"` 标记已处理。Manager 用 `mam job list --attention` 查找已停止、未处理且执行者已空闲的进程，通知负责人继续收尾。

具体参数按需查阅 `mam task --help`、`mam workspace --help`、`mam job --help` 及相应子命令的帮助。

## 开发验证

MAM 使用 Python 标准库。在自己的 worktree 中运行 `.venv/bin/python -B -m unittest discover -s tests -v`。修改删除操作时，验证共享软链接目标、未提交文件、未登记目录和运行进程得到保护。
