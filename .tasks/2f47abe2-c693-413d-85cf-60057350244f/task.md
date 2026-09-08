# 四库本地环境入口独立验收

执行者：Popper（gpt-5.6-terra max，agent 01a080dd-7fe2-7f30-805d-8657360a087a）。任务 UUID：2f47abe2-c693-413d-85cf-60057350244f。workspace：/mnt/public/xcj/Projects/workspace/2f47abe2-c693-413d-85cf-60057350244f。每库分支 task/2f47abe2-c693-413d-85cf-60057350244f，目标为各库当前开发分支（RMBench/opendm xcj-dev，openpi/robot-bridge codex/unified-sim-real-runtime）。

## 输入与任务

独立审阅已完成的环境入口成果；读取 .worklogs/workflow-env-entry-20260908/task.md 和 report.md 作为历史事实，最新用户统一管理要求以新接口文档为准。四库作者在 workspace/workflow-env-entry-20260908，下列提交已完成但尚未集成：
- RMBench 993e2291f3c707c43d69d1f200a23a825f71bfed、75486ee277b991a83c3e43f13e68bbf453f6d1d5。
- opendm e536bc40598968d29283720cbc9f53d2e025fb01、9f46ce78f972e53980a2eeb6efee9e0aaa58a812。
- openpi 1fb2d4220a10a0c361decb9bc2783ce975fc1f0e、5a572764b88e0d22b750eb9cdf34ca80a2eb2925、831afd54a4b10aa911068898617de8fa380ae09e。
- robot-bridge e76bd57ffa6b781b16e2b50c376a23d9bdfc7d8f、9c5056f1d6dfd155a111db6c28ea5cff469348df。

先完成只读审阅并报告实际缺陷；等待Manager集成后的固定base再运行创建。自己的所有worktree只在本UUID workspace，不复用作者环境。已有本地三参wrapper在四源repo .local/create_worktree.sh。

验收：本地入口/受管脚本引用稳定源实体、各库共享软链（RMBench整体data/assets、eval_result、pi05/Mem-0模型和数据；其他库按各自规范）、保留GPU smoke入口但本次不用GPU、openpi .local忽略。完整创建后在本机和ssh wuwen-1执行相同共享解释器CPU基础import；优先robot-bridge，并为随后CLI多库创建选择第二个轻量库。必要重型库安装须先告知Manager，避免耗时和磁盘无意义重复。

当前仅审阅/验收，不修改实现；发现缺陷写report草稿告知Manager。后续需要修复由作者处理。不要移动或删除运行中eval_result。不得把仅help/缺参失败当作环境创建成功。

## 共同交付约定

按 main 上发布的本任务和 docs/task-management-design.zh-CN.md 实施。报告写回稳定管理库本任务目录 report.md，首行 task_revision: <所依据任务的完整 commit>，随后写完成/未完成、workspace、各库完整交付 commit、验证结论与成果位置。工具可用后通过 CLI 发布；代码只在自己的 worktree 提交。

先读管理库 AGENTS.md，跨库先读目标库 AGENTS.md 及对应规范。追加要求只以 Manager 发布后的任务文件为准。自身测试产生的文件及进程自行清理，保留待 Manager 归档的工作区。无需 GPU，不修改现用训练/评测环境和进程。没有常驻服务、自动唤醒、额外权限系统、环境 provenance 或旧 CLI 兼容层。
