# 迁移独立验收简报

独立验收通过。新实例配置为
`PROJECT_ROOT=/mnt/public/xcj/Projects/state-vla`、
`MAM_ROOT=/mnt/public/xcj/Projects/state-vla/multi-agent-manager`、
`MAM_BRANCH=project/state-vla`。新 MAM 受跟踪非 `.tasks` 树与
`origin/main` 一致，`origin/main` 和既有 `project/state-vla` 历史均被保留；新
clone 无 Git object alternates。四个业务库的 local branches、local-only commits、
正式 data/checkpoints/eval 与 robot-bridge 既有未跟踪用户文档仍在新目录。

以新实例创建并发布的临时验收任务
`04ca83bb-fa82-477a-8369-8968508bb6c8` 实际执行了五库 `mam workspace add`，分别以
RMBench `aba4c6e9`、openpi `ef16a275`、robot-bridge `f45c6a47`、OpenDM
`9ab9d292`、MAM `55248562` 为 base。五个 worktree 均位于
`/mnt/public/xcj/Projects/state-vla/workspace/<task-id>/`，Git common dir 都指向
相应的新 primary checkout，分支、clean 状态和独立 `.venv` 均正确；受控共享链接未
指向旧顶层项目路径。

CPU-only 验证全部通过：RMBench simulator imports、openpi 和 robot-bridge 的
`scripts/worktree_env_smoke.py`、OpenDM editable import、MAM worktree 的
`.venv/bin/mam task list`。没有启动 train/eval、GPU 或新 service。新 service 前后均为
disabled，无 manager/job/runtime；旧 service 未改动且仍 healthy。

临时任务的已发布 report revision 为 `02b7310e673a0966c2e1f109934030f3e2b34689`。它已
归档，确认删除五个测试 worktree、五个 `task/04ca...` 分支及临时 workspace；未留下
测试附件或业务代码变更。归档首次被 smoke 生成的 `__pycache__` 保护阻断，已仅从该
专用测试 workspace 清理 bytecode/egg-info 后成功归档。未发现迁移或 MAM workspace
机制的阻塞项。
