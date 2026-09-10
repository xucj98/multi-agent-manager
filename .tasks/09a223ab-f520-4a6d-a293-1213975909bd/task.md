# 删除任务 revision 机制

## 目标与范围
以 multi-agent-manager main 的 c304888 为代码基线。按 MAM AGENTS.md/README 工作，在本任务独立 worktree 实施。用户最新 README/AGENTS 已审核提交，保持其措辞，除非发现实际矛盾需向 Manager 报告。

执行者始终依据最新发布的 task.md；Manager 修改发布后通知执行者。删除 task_revision 概念，不以另一名字重建版本绑定机制。移除 report 必填首行、发布时任务版本关联/校验、requirements_changed，以及 review 固定任务要求版本的关联。Review 应读取源任务最新发布要求和已发布成果，并保留具体交付代码 commit IDs。task show 默认直接显示已发布文档，不附加 task ID/workspace/版本头。删除专门的任务要求历史版本查询参数；普通 Git 发布历史和代码 commit 留痕继续保留。

同步审计实现、CLI help、测试和 docs/task-management-design.zh-CN.md 的相关表述。历史 .tasks 文档无需改写。现有本地登记中的旧字段可以忽略，不做迁移框架；现有 task、report、review 仍能查询，既有 jobs 不受影响。不修改其他运行中工作区、进程或环境，不顺带扩大 CLI 改造范围。

## 验收
运行仓库完整测试及 diff --check。补充有意义的覆盖：无 revision 首行可发布 report；修改并重新发布要求后正常交付；review 使用最新要求及交付代码 commits；旧登记可读取；show/help/status 不再要求或显示任务版本关联。确认报告与实际代码 HEAD 的交付校验仍合理。

## 交付
提交代码，在共享 MAM 根目录本任务 report.md 简述完成项、修改文件、workspace、commit、验证和限制。当前系统安装版仍要求旧首行；优先用修改后 CLI 正常发布本任务报告（MAM 根路径指向共享根），避免把已删除概念重新写入报告。不要自行安装或合并主分支。清理自己产生的短测试临时产物，保留 worktree 供独立 review。
