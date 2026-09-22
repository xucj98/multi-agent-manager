# 迁移验收临时 workspace add

在新项目根 `/mnt/public/xcj/Projects/state-vla` 验证 MAM 的实际 workspace
创建路径。仅创建并检查 RMBench、openpi、robot-bridge、opendm 与
multi-agent-manager 五个库的隔离 worktree 和环境；不启动训练、评测、服务或
GPU 工作。每个库使用其 current primary HEAD 作为 base。

验收后运行各库文档规定的 CPU-only smoke，检查 Git common dir、工作树路径、
环境可执行文件和软链接均只指向新 state-vla 项目。完成后发布报告并归档本
临时任务，移除全部测试 workspace 和 `task/<TASK-ID>` 分支。
