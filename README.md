# Agent 工作区管理

本仓库管理多代码库协作中的任务归属、workspace 创建与回收。每个代码库维护自己的开发约定、环境安装及共享目录规则。

## 职责

| 位置 | 维护内容 |
| --- | --- |
| 本仓库 | 分工、任务登记、运行依赖、交付和回收 |
| 各库 `AGENTS.md` | 项目职责、必读规范和操作入口 |
| 各库受 Git 管理的 worktree 脚本 | 本库 worktree、共享软链接、独立环境及必要检查 |
| 各库 `.local/create_worktree.sh` | 当前集群的固定路径和安装参数，Git 忽略 |
| 各库实验目录 | 正式实验命令、配置、metadata、结果和结论 |

公共规则由 Manager 在任务分配中提供，进入目标库后读取该库入口。一个工作区可包含多个独立 Git 仓库，公共规则不会因为目录相邻而自动加载。

## 任务准备

讨论、只读调查和监控无需创建 worktree 或环境。代码实施和独立代码 review 使用各自的 workspace；文档修改只需代码 worktree。需要运行项目代码时再准备独立环境。

Manager 分配任务时明确：目标和交付物、负责人、仓库与修改范围、base commit 与目标分支、workspace、验证要求。实验任务另列实验组、run、结果归属、GPU 和监控责任。

可直接使用以下任务分配模板，填写与当前任务有关的项：

```text
目标与交付物：
负责人：
仓库、base commit、目标分支、允许修改的文件：
workspace：
必读规范：本库 AGENTS.md，以及本次涉及的开发/实验/环境规范
验证：
实验组、run、结果路径、GPU、监控与接手责任（实验任务填写）：
完成条件：成果被接收，临时产物与 workspace 已清理或明确交接
```

阅读规范不代替任务验收。Manager 把本次关键约束写进分工，review 检查其实际落实情况。

```text
Projects/
  agent-workflow/
  workspace/
    <task-role-id>/
      RMBench/
      openpi/
      opendm/
      robot-bridge/
```

只创建任务需要的库。原仓库是稳定入口；同一任务的修复和后续验证继续使用已有 workspace。review 固定待审 commit，使用 reviewer 自己的 workspace。

## 创建 worktree

各库从原仓库根目录调用本地入口，传入三个参数：

```bash
bash .local/create_worktree.sh <base-commit> <new-branch-name> <workspace-root>
```

最后一个参数是 agent workspace 根目录，脚本创建其下的本库目录。需要两个库时分别调用各库入口，传入同一 workspace 根目录。目标目录或分支已存在时停止，由负责人检查已有任务状态。

本地入口固定本集群 uv、cache、Python、wheel 与稳定共享源路径，调用受 Git 管理的本库脚本。它只校验并转发三个位置参数及固定安装参数，worktree 创建、共享软链接与安装逻辑仍在本库受 Git 管理的脚本中。本机和 wuwen-1 共享这份入口；其他集群维护自己的版本。安装后的基础检查由库脚本定义；GPU smoke 和正式实验由任务明确安排。

只需代码时可使用 `git worktree add` 创建并登记，不必安装环境。共享数据、checkpoint 和正式结果由各库脚本链接到稳定实体；`.venv` 与 editable 源码属于当前 worktree。

## 生命周期

任务经历工作中、待验收、已接收并清理三个阶段。负责人交付代码 commit、验证结论及正式成果位置，Manager 接收后执行回收。待验收目录只在有明确后续验收时保留。

运行中的训练或评测单独登记主机、进程身份、结果目录和所依赖的 worktree。agent 交接时转交监控责任；依赖它的 job 未结束时保留必要目录。远端不可达视为状态未知。

回收前确认有价值改动已提交并接收或明确保留、运行依赖已结束、临时文件已处理。使用 Git 移除 worktree，随后清除独立环境和 workspace 外层目录。共享软链接只删除链接本身，正式实体继续保留在稳定位置。工具只处理登记的路径；异常中断留下的未登记目录先核实归属。

## 实验与 smoke

实验执行前读取所属库实验规范。RMBench 新评测的物理产物统一写入 `RMBench/eval_result/<exp-group>/<run>`，对应说明进入 `RMBench/experiments/<exp-group>`；robot-bridge 通过仿真器接口记录结果。

当前 RMBench 正式评测前，完成一个包含两次 rollout 的 smoke：一次开启视频、一次关闭视频。检查视频、配置及 metadata 等产物后，保留简短验收结论和必要的复跑信息，清理临时视频、训练 checkpoint 和调试产物，再固定 commit 并启动正式 run。实验启动校验依赖保留的验收记录，而非已清理的 smoke 目录。

正式实验沿用各库的 `command.txt`、commit、config 和逐步继承 metadata 约定。环境创建仅提供操作便利，不新增调用参数、解释器或依赖版本台账。

## 长任务

常规状态检查每两小时一次，完成、失败及实验规定的中间检查点由任务负责人处理。监控读取已有进程和结果，不为每次检查创建 workspace。

自动定时唤醒需要经过验证的调度入口；仅在提示词中约定不能保证 agent 恢复执行。登记清楚下一次检查和接手负责人，使用实际可用的调度方式。首版 workspace 工具不代替训练调度器。

## 记录与完成

本管理仓库的 `.local/tasks/` 保存任务登记，不进入 Git。这与四个业务库仅保存本地创建入口的 `.local/` 分开；实验信息引用已有正式产物。跨库工作中值得保留的决定和问题结论写入 `.worklogs/`，按任务更新一份简短记录。

任务完成包括成果接收与临时工作区清理。普通 smoke、重复报告、失败已定位的临时重试产物和环境检查产物及时删除。需要继续保留的目录明确负责人、原因和结束条件。
