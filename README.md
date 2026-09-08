# 本集群的 agent 工作区管理

这里集中管理任务分工、workspace 和工作日志。各代码库维护自己的开发规范、worktree 脚本和实验记录。

## 当前集群

本机与 `wuwen-1` 共享 `/mnt/public` 文件系统。`/mnt/public/xcj/Projects` 下的代码、数据、缓存和环境在两台机器上使用相同路径；修改共享文件会同时影响两边。

两台机器的进程和 GPU 使用情况分别检查。进程在启动它的机器上查询，本开发机不一定能看到其他开发机占用 GPU 的进程。

```text
/mnt/public/xcj/Projects/
  agent-workflow/
    AGENTS.md
    README.md
    .worklogs/              # Git 管理的工作日志
    .local/tasks/          # Git 忽略的任务登记
  workspace/
    <task-id>/
      RMBench/             # 只建立任务需要的库
      openpi/
      opendm/
      robot-bridge/
  RMBench/
  openpi/
  opendm/
  robot-bridge/
```

本仓库只服务当前集群。各库 `.local/create_worktree.sh` 固定本集群所需路径，两台机器共用；每个 worktree 仍有自己的 `.venv` 和 editable 安装。

## 分工与阅读规范

Manager 为每个分配的任务确定唯一 `<task-id>`，workspace 目录和工作日志使用同一名称。分配时填写以下内容：

```text
目标与交付物：
负责人：
涉及的库、base commit、新建工作分支、合入分支、允许修改的范围：
workspace：
必读规范：
验证要求：
实验组、run、结果路径、GPU、监控负责人（实验任务填写）：
```

开始在一个库工作前先读它的 `AGENTS.md`，再按任务阅读其中列出的规范。读过且没有变化的内容无需重复阅读。跨库协作规则由 Manager 在分工时提供，不依赖相邻目录自动加载。

讨论、只读调查和状态监控直接读取已有资料。代码修改和独立代码 review 使用自己的 worktree；文档修改只需代码 worktree。只有需要执行项目代码时，才准备该库独立环境。

## 创建工作区

原仓库是 `/mnt/public/xcj/Projects` 下的 `RMBench`、`openpi`、`opendm` 和 `robot-bridge`，不在 `workspace` 下。在相应原仓库根目录调用三个参数的本地入口：

```bash
bash .local/create_worktree.sh <base-commit> <new-branch-name> <workspace-root>
```

第三个参数为 `/mnt/public/xcj/Projects/workspace/<task-id>`，脚本创建其下的本库目录。需要多个库时分别调用各库入口，传入同一个 workspace 根目录。目标目录或分支已存在时停止，先确认是否已有相应工作区。

`.local/create_worktree.sh` 不进 Git，只填写固定的 uv、cache、Python、wheel 等路径并转发参数。各库受 Git 管理的脚本负责创建 worktree、建立本库共享软链接和安装环境。公共工具负责登记与回收。

只需代码时使用 `git worktree add`，无需安装环境。创建后由 Manager 通过本仓库管理工具登记任务与目录；同一任务的修复、后续检查继续使用已有 workspace。

数据、checkpoint 和正式结果实体留在稳定源目录，worktree 中按本库规则建立软链接。环境安装后的基础检查由库脚本定义，实验 smoke 按所属库的要求执行。

## 管理工具

以下命令从 `/mnt/public/xcj/Projects/agent-workflow` 执行，使用系统 Python，不需要创建环境。

```bash
python3 scripts/ws.py register <task-id> --owner <agent-id> --workspace /mnt/public/xcj/Projects/workspace/<task-id>
python3 scripts/ws.py status
python3 scripts/ws.py status <task-id>
```

登记已有 workspace 中各库的 worktree。`status` 不传任务编号时列出全部登记任务。状态保存在原管理仓库 `.local/tasks/`，从管理仓库的 worktree 调用时也使用同一处登记。

运行训练、评测或常驻服务前，为其登记一条占用记录；负责人确认任务结束后解除。`--pin` 填写主机与能识别该次进程的描述，工具不根据 PID 自动判断进程是否结束。

```bash
python3 scripts/ws.py job start <task-id> <job-name> --pin 'wuwen-1:进程PID及启动时间'
python3 scripts/ws.py job finish <task-id> <job-name> --by <agent-id>
python3 scripts/ws.py handoff <task-id> --from <old-agent-id> --to <new-agent-id>
```

交付时记录各 worktree 当前 HEAD。Manager 接收后为每个库明确提供对应的交付 commit，再执行回收。这里填写 worktree 的交付 commit，不是 cherry-pick 后生成的合入 commit。

```bash
python3 scripts/ws.py deliver <task-id> --by <agent-id>
python3 scripts/ws.py accept <task-id> --manager <manager-id> --commit <repo-name>=<delivery-commit>
python3 scripts/ws.py close <task-id>
```

涉及多个库时重复 `--commit`，例如 `--commit RMBench=<sha> --commit openpi=<sha>`。仍有占用记录、未验收成果或未处理文件时，回收会停止并说明原因。按提示处理后重试，不直接强制删除整个目录。

## 交付与清理

负责人交付代码 commit、验证结论和正式成果位置，Manager 接收后回收 workspace。待验收目录需有明确负责人和后续安排。

smoke 检查通过后，在工作日志中保留简短结论与必要复跑信息，正式实验前处理临时视频、测试 checkpoint 和调试文件。正式实验需要的记录保存到正式产物中，后续步骤不依赖已经清理的 smoke 目录。

回收前确认代码改动已经提交并接收、临时文件已经处理、运行任务已经结束。工具只处理登记的工作区，移除 Git worktree 和独立环境后清理外层目录；软链接指向的共享实体继续保留。

存在未提交改动、未知文件或仍在使用的目录时，先由负责人处理并说明保留原因。agent 异常退出时，由 Manager 接管；agent 停止不代表训练或评测进程已经结束。

## 长任务与交接

登记运行任务的主机、进程身份、结果目录和所依赖的 worktree。任务交接时同时转交监控责任；远端不可达视为状态未知。

常规检查每两小时一次，完成、失败和实验规定的中间检查点由负责人处理。监控读取已有结果，不创建新 workspace。

自动唤醒 agent 需要实际可用并经过验证的调度入口；本工具只登记任务和回收目录，不负责定时启动 agent。

## 工作日志

后续所有任务的工作日志集中在 `.worklogs/<task-id>.md`，每项任务更新同一份文件，记录决定、问题结论、交付和清理情况。各库已有历史工作日志保留原位，新任务从这里开始记录。

实验所属库继续保存正式命令、配置、metadata、结果及实验说明，工作日志通过链接引用。环境创建不额外记录安装参数或依赖清单。

`.local/tasks/` 只保存管理工具需要的负责人、目录、交付和运行依赖信息，不进入 Git。
