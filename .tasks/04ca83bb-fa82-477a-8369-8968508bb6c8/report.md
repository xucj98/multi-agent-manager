# 迁移 workspace add 验收

新实例配置为 `PROJECT_ROOT=/mnt/public/xcj/Projects/state-vla`、
`MAM_ROOT=/mnt/public/xcj/Projects/state-vla/multi-agent-manager`、
`MAM_BRANCH=project/state-vla`。创建本临时任务时显式移除了
`CODEX_THREAD_ID`，新 service 在前后均为 disabled、无 manager、job 或 runtime。

实际以各 primary HEAD 创建了五个 `task/04ca83bb-fa82-477a-8369-8968508bb6c8`
worktree：RMBench `aba4c6e9`、openpi `ef16a275`、robot-bridge `f45c6a47`、
opendm `9ab9d292`、multi-agent-manager `55248562`。路径均在
`state-vla/workspace/04ca83bb-fa82-477a-8369-8968508bb6c8/`；每个 Git common dir
均指向新 primary checkout，worktree clean，独立 `.venv` 存在。受控共享链接均
指向新 `state-vla` 路径，未检出旧顶层项目路径引用。

CPU-only smoke 全部通过：RMBench simulator imports、openpi
`scripts/worktree_env_smoke.py`、robot-bridge `scripts/worktree_env_smoke.py`、
OpenDM editable import，以及 MAM worktree 的 `.venv/bin/mam task list`。未启动
train/eval、GPU 或 service。

新 MAM 的受跟踪非 `.tasks` 树与 `origin/main` 相同；`origin/main` 与原
`project/state-vla` 历史均为 HEAD ancestor，且新 clone 无 object alternates。四个
业务库的本地分支和 local-only commits 仍存在，robot-bridge 原有未跟踪用户文档也仍在。

结论：迁移入口及五库真实 `mam workspace add` 通过。本任务归档后将清理全部测试
worktree、独立环境与 task branches；未发现需要业务代码修复的阻塞项。
