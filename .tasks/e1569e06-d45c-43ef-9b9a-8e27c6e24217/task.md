# 独立审阅 MAM 删除 task revision

Review fixed source delivery (source TASK-ID: 09a223ab-f520-4a6d-a293-1213975909bd):
{
  "task": "09a223ab-f520-4a6d-a293-1213975909bd",
  "task_revision": "1ae6658e0fa675fd6f8221a8ed33d95a4700722e",
  "report_revision": "bf081c8318ae686c8679d2a928a74b90b7288bae",
  "commits": {
    "multi-agent-manager": "93093842c8da33f8511eac932a113fc4f2a2a52e"
  }
}

Source task requirements:

# 删除任务 revision 机制

## 目标与范围
以 multi-agent-manager main 的 c304888 为代码基线。按 MAM AGENTS.md/README 工作，在本任务独立 worktree 实施。用户最新 README/AGENTS 已审核提交，保持其措辞，除非发现实际矛盾需向 Manager 报告。

执行者始终依据最新发布的 task.md；Manager 修改发布后通知执行者。删除 task_revision 概念，不以另一名字重建版本绑定机制。移除 report 必填首行、发布时任务版本关联/校验、requirements_changed，以及 review 固定任务要求版本的关联。Review 应读取源任务最新发布要求和已发布成果，并保留具体交付代码 commit IDs。task show 默认直接显示已发布文档，不附加 task ID/workspace/版本头。删除专门的任务要求历史版本查询参数；普通 Git 发布历史和代码 commit 留痕继续保留。

同步审计实现、CLI help、测试和 docs/task-management-design.zh-CN.md 的相关表述。历史 .tasks 文档无需改写。现有本地登记中的旧字段可以忽略，不做迁移框架；现有 task、report、review 仍能查询，既有 jobs 不受影响。不修改其他运行中工作区、进程或环境，不顺带扩大 CLI 改造范围。

## 验收
运行仓库完整测试及 diff --check。补充有意义的覆盖：无 revision 首行可发布 report；修改并重新发布要求后正常交付；review 使用最新要求及交付代码 commits；旧登记可读取；show/help/status 不再要求或显示任务版本关联。确认报告与实际代码 HEAD 的交付校验仍合理。

## 交付
提交代码，在共享 MAM 根目录本任务 report.md 简述完成项、修改文件、workspace、commit、验证和限制。当前系统安装版仍要求旧首行；优先用修改后 CLI 正常发布本任务报告（MAM 根路径指向共享根），避免把已删除概念重新写入报告。不要自行安装或合并主分支。清理自己产生的短测试临时产物，保留 worktree 供独立 review。

Source report:

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

## 独立验收要求
先读取源任务最新发布要求及简报。用本任务独立worktree checkout交付93093842c8da33f8511eac932a113fc4f2a2a52e（mam workspace add），独立审计实现、测试、help和设计文档。重点检查删除完整性、旧登记可读、report无首行可发布、review最新要求与代码commit识别、show纯文档；不要把正常Git发布历史误判为task revision。运行完整测试和针对性CLI验证，不能只重复作者断言。阅读README/AGENTS确认简洁清晰且无行为冲突。不要修改主checkout或运行中环境，不安装、不合并。报告按严重程度列实际问题，或明确GO及证据；使用所审代码CLI发布无revision首行报告到共享MAM根。清理自己的测试临时产物，保留worktree供归档。
