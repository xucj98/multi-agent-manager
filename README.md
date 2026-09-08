# Multi-Agent Manager（MAM）

管理 agent 的任务、workspace 和长任务进程。所有 agent、代码修改和管理命令在本机运行；GPU 作业可通过 SSH 在 `wuwen-1` 运行，由本机查询进程。两端共享 `/mnt/public`，`wuwen-1` 无需安装 MAM。

[安装与更新](docs/install.md)。`mam` 可以从任意目录调用，默认管理资料位置如下；`--root <目录>` 可覆盖管理根目录，日常无需指定。

```text
Projects/multi-agent-manager/
  .tasks/<uuid>/task.md       # 任务要求，进入 Git
  .tasks/<uuid>/report.md     # 结果简报，进入 Git
  .local/tasks/<uuid>.json    # CLI 维护的状态，不进入 Git
Projects/workspace/<uuid>/<repo>/
```

## 最短流程

Manager 为 subagent 创建任务，用编辑工具填写返回路径中的 task.md，再发布要求、启动 agent 并绑定：

```bash
mam task create --title "任务名称"
mam task publish <uuid> --file task
mam task bind <uuid> --agent <agent-id>
```

执行者读取要求，按需创建代码库环境，然后在返回的 worktree 中工作：

```bash
mam task show <uuid>
mam workspace add <uuid> --repo robot-bridge --base <commit>
```

执行者编辑返回路径中的 report.md，首行使用实际依据的任务版本：

```text
task_revision: <show 返回的40位任务 commit>
完成与未完成：……
workspace、各库交付 commit：……
验证结果与成果位置：……
```

```bash
mam task publish <uuid> --file report
mam task status <uuid>
```

所有参数、review、进程登记和归档接口通过帮助查询：

```bash
mam task --help
mam job --help
mam task archive --help
```

## 开发验证

在自己的 MAM worktree 中运行 `.venv/bin/python -B -m unittest discover -s tests -v`。独立环境由 `workspace add` 调用本库 `.local/create_worktree.sh` 创建，安装和软链接规则由各库维护。
