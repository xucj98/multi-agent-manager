# MAM 操作手册

MAM 管理本集群的任务、workspace、长进程和可停止等待。所有 agent 与管理命令在本机运行；GPU 作业可通过 SSH 在 `wuwen-1` 运行，两端共享 `/mnt/public`。安装与更新见[安装说明](docs/install.md)。

`mam` 可从任意目录调用，默认管理根目录为 `/mnt/public/xcj/Projects/multi-agent-manager`；需要时用全局 `--root ROOT` 覆盖。

语法中的大写词需要替换为实际值，方括号表示可选参数。下面不含大写词的命令可直接执行。MAM 创建 `TASK-ID`；它同时用于任务文件、workspace 和工作分支。`JOB-ID` 标识登记的进程，`AGENT-ID` 标识执行 agent。

```text
.tasks/TASK-ID/task.md
.tasks/TASK-ID/report.md
Projects/workspace/TASK-ID/REPO/
```

## 任务管理

Manager 创建任务、填写任务要求并发布，再绑定执行 agent：

```text
mam task create --title TITLE
mam task create --title TITLE --review TASK-ID
mam task publish TASK-ID --file task
mam task bind TASK-ID --agent AGENT-ID
```

`create` 返回任务草稿路径；在 `.tasks/TASK-ID/task.md` 写明目标、范围、交付和验收要求。Review 的 `--review` 接收源任务的 `TASK-ID`。验收完成后由 Manager 归档：

```text
mam task archive TASK-ID --note NOTE
```

先用这些可执行命令查看已有任务和等待：

```bash
mam task list
mam job list
mam wait list
```

针对一个任务读取登记信息和已发布要求：

```text
mam task status TASK-ID
mam task show TASK-ID
```

`mam task status` 显示已保存的 job 观测，不会实时探测 job。

## 执行与交付

启动 prompt 会提供 `TASK-ID`。先运行 `mam task status TASK-ID` 和 `mam task show TASK-ID`，再为每个需要修改或独立 review 的仓库创建或复用 worktree：

```text
mam workspace add TASK-ID --repo REPO --base COMMIT
```

完成后，在管理仓库的 `.tasks/TASK-ID/report.md` 写结果简报。首行使用 `task_revision: COMMIT`，其中 `COMMIT` 是本次实际依据的已发布任务版本；记录完成项、workspace 与交付 commit、验证结果和成果位置。然后发布简报：

```text
mam task publish TASK-ID --file report
```

## 进程管理

预计运行超过一小时的正式数据生成、训练或评估需要登记；短 smoke 不需要。登记、查询和收尾使用：

```text
mam job add TASK-ID --note NOTE --host HOST --pid PID
mam job list
mam job list --task TASK-ID
mam job status JOB-ID
mam job archive JOB-ID --note NOTE
```

进程结束后，先记录结果并处理任务要求的临时文件，再执行 `mam job archive`。Manager 可用 `mam job list --attention` 查找需要跟进的登记。

## 等待

需要保持 active turn 等待已登记的长任务时使用：

```text
mam wait jobs [--task TASK-ID] [--timeout TIMEOUT]
mam wait list
mam wait stop --agent AGENT-ID
```

`mam wait stop` 只停止对应 agent 的等待，不会停止或归档 job。

## 工作区

代码修改和独立 review 使用本任务的 worktree；讨论、只读调查和监控不需要创建 workspace。每个仓库分别执行一次 `mam workspace add TASK-ID --repo REPO --base COMMIT`，并按任务要求的 base commit 工作。

## 开发验证

修改 MAM 实现时，在自己的 worktree 运行：

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

详细接口、状态语义和归档保护见[任务管理 CLI 接口说明](docs/task-management-design.zh-CN.md)；参数以 `mam task --help`、`mam workspace --help`、`mam job --help`、`mam wait --help` 及相应子命令的帮助为准。
