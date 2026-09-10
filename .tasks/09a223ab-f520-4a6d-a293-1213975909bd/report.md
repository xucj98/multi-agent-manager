# 交付简报

## 完成项

- 删除 report 的任务要求版本首行、发布关联与校验，以及 `requirements_changed` 状态。
- `task show` 直接输出当前已发布文档，移除 `--revision` 查询参数；CLI help 同步更新。
- review 读取源任务当前已发布的要求和简报，只保存源任务与交付代码 commit。
- 状态展示忽略旧登记中的版本字段，仍显示已发布提交和各仓库交付 commit。
- 更新任务管理设计文档与覆盖测试。

## 交付

- workspace: `/mnt/public/xcj/Projects/workspace/09a223ab-f520-4a6d-a293-1213975909bd/multi-agent-manager`
- branch: `task/09a223ab-f520-4a6d-a293-1213975909bd`
- code commit: `93093842c8da33f8511eac932a113fc4f2a2a52e` (`Remove task revision binding`)
- modified: `multi_agent_manager/cli.py`, `tests/test_task.py`, `docs/task-management-design.zh-CN.md`

## 验证

- `.venv/bin/python -B -m unittest discover -s tests -v`：33 项通过。
- `git diff --check` 通过。
- 已检查 `task show`、`task publish`、`task create --review` 的 help；无任务版本查询参数或报告首行要求。

## 限制

未安装或合并；worktree 保留供验收。
