# 本集群的 agent 任务管理

这里集中保存任务说明与结果简报，查看任务状态，并在任务归档时移除 workspace。各代码库维护自己的开发规范、worktree 脚本和实验记录。

## 当前集群

本机与 `wuwen-1` 共享 `/mnt/public` 文件系统。`/mnt/public/xcj/Projects` 下的代码、数据、缓存和环境在两台机器上使用相同路径；修改共享文件会同时影响两边。

进程和 GPU 使用情况分别在对应机器上检查。本开发机不一定能看到其他开发机占用 GPU 的进程。

```text
/mnt/public/xcj/Projects/
  agent-workflow/
    .worklogs/
      <task-id>/
        task.md            # Manager 维护的当前任务要求
        report.md          # 执行 agent 提交的结果简报
    .local/tasks/          # Git 忽略的管理状态
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

本仓库只服务当前集群。四库 `.local/create_worktree.sh` 提供各自固定路径的本地入口，两台机器共用；每个 worktree 有自己的 `.venv` 和 editable 安装。

## 任务说明

Manager 分配唯一的 `<task-id>`，先写 `.worklogs/<task-id>/task.md`，再通知 subagent 开工。文件进入 Git，至少包含：

```text
目标与交付要求
负责人
涉及的库、base commit、新建工作分支、合入分支
允许修改的范围
独享 workspace
必读规范
验证与清理要求
实验组、run、结果位置、GPU、监控责任（实验任务填写）
```

追加或修改要求时，Manager 先更新并提交任务文件，再通知 agent 阅读。当前要求保留在任务正文，历史变化通过 Git 查看；对话用于通知和讨论。

每个 agent 开工前读取自己的任务说明，进入某个库前读取该库的 `AGENTS.md` 及相关规范。已经读过且没有变化的内容无需重复阅读。

## 工作区

讨论、只读调查和状态监控直接读取已有资料。代码实施和独立代码 review 使用自己的 worktree；文档修改只需代码 worktree。需要执行项目代码时再安装环境。

原仓库是 `/mnt/public/xcj/Projects` 下的四个库，不在 `workspace` 下。需要完整环境时，从相应原仓库根目录调用：

```bash
bash .local/create_worktree.sh <base-commit> <new-branch-name> <workspace-root>
```

第三个参数为 `/mnt/public/xcj/Projects/workspace/<task-id>`，脚本创建其下的本库目录。多库任务分别调用各库入口，传入同一个 workspace 根目录。同一任务继续使用已有 workspace。

本地入口不进 Git，只填写本集群安装参数并调用本库受 Git 管理的创建脚本；后者负责 worktree、共享软链接和环境安装。只需源码时使用 `git worktree add`，无需安装环境。

创建后由 Manager 登记任务与 workspace。数据、checkpoint 和正式结果实体留在稳定源目录，worktree 按本库规则建立软链接。

## 结果简报与 review

执行 agent 在 `.worklogs/<task-id>/report.md` 写简短报告并提交，至少包含：

```text
完成情况，以及未完成事项或已知限制
workspace 绝对路径
每个 worktree 的代码库名称和完整 commit id
执行的验证及结果
正式成果位置
临时文件是否已处理，是否还有运行依赖
```

简报中的 commit 是该 worktree 的交付版本，不是后续 cherry-pick 生成的合入 commit。实验配置、metadata 和结果仍保存在实验所属库，简报通过链接引用。

Manager 为 review agent 单独创建任务说明，引用被 review 的任务要求、结果简报、各库 commit，以及自己的独享 workspace。review agent 独立检查或复现，结束后也提交自己的结果简报。发现问题时，Manager 将修复要求补入实施任务说明后再通知作者。

## 状态与归档

任务状态用于区分工作中、待接收、已接收和已归档；它由负责人和 Manager 更新，不代表自动探测 agent 的实时运行状态。

归档前确认成果已接收、临时文件已由负责人处理、运行依赖已结束或交接。归档移除登记的 worktree、独立环境和空的 workspace 外层目录，保留任务说明、结果简报与提交引用。遇到未处理文件或未提交改动时停止，由负责人处理。

smoke、实验结果和其他临时文件的清理属于执行任务。管理工具不扫描或代删这些文件，也不沿软链接删除共享数据。

## 长任务

训练、评测或服务启动后登记主机、进程身份、结果目录和依赖的 worktree。交接时明确接手负责人；远端不可达视为状态未知，agent 停止不代表进程结束。

常规检查每两小时一次，完成、失败和实验规定的中间检查点按任务要求处理。监控不创建新的 workspace。

自动唤醒需要实际可用并经过验证的调度入口，本工具不负责定时启动 agent。

## 工作记录

后续所有任务说明与简报集中在本仓库 `.worklogs/`；各库已有历史工作日志保留原位。每项任务维护一份当前说明和一份简报，不重复复制大日志、代码或实验产物。

环境创建不额外记录安装参数或依赖清单。`.local/tasks/` 只保存工具需要的任务状态、负责人、目录、交付与运行依赖信息，不进入 Git。
