# 工作区工具与四库入口独立验收

## 目标与负责人

负责人：Popper（gpt-5.6-terra max）。独立验证四库创建入口及任务管理工具是否满足当前任务说明。

## 输入与工作区

实施任务：`../workflow-env-entry-20260908/task.md`、`../workflow-tool-20260908/task.md`；相邻 `report.md` 为实施简报。收到交付后读取其中的仓库与完整 commit，用自己的 worktree 固定这些版本，不能复用作者环境。

独享 workspace：`/mnt/public/xcj/Projects/workspace/workflow-acceptance-20260908`。只建立需要的库。文档/代码只读审查不先安装环境。

## 验收范围

- 检查四库三参数 wrapper 与通用脚本：固定稳定 source、参数含空格、help/缺参、存在目标拒绝、去掉旧 README 依赖、openpi.local被忽略、各库软链接规则保留、GPU smoke 未被删除。
- 使用最终 robot-bridge `.local/create_worktree.sh`，在自己的 workspace 创建独立环境并完成 CPU 基础检查；本机与 wuwen-1 使用共享同一路径，可分别运行 CPU 检查。其它三库验证入口契约，不重复安装重型环境，不用 GPU。
- 工具验收以 workflow-tool 任务说明为准，重点检查真实 Git worktree归档、说明和简报关联、状态可查、重复登记保护、运行依赖、未提交代码、共享软链接目标保留。archive不能替agent清理smoke/temp。
- 按管理库 README 的命令完成一项小任务全流程，确认归档后说明和简报仍可读，workspace已移除。
- 发现有实际影响的问题立即写入自己的简报草稿并通知Manager，修改要求由Manager补入实施任务说明。

## 交付

本目录 `report.md` 写验收完成/未完成、review对应的每库完整commit、自己的workspace与worktree commit、运行过的检查和限制。你自行处理测试产生的临时文件，Manager 接收后归档移除workspace。

不修改实现代码，不迁移旧eval结果，不碰现用环境和活跃任务。不重复建立报告副本或多个验收workspace。
