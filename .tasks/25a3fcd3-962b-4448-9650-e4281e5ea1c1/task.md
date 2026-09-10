# MAM 多项目配置与发布分支

在独立 MAM worktree 实施，base 801901f414fa1f9dcc5791dd179e0865a92593d6。先遵循AGENTS和README。

## 用户决策
mam 从当前目录逐级向上找最近 .mam/env.json。三个必填键 MAM_ROOT、PROJECT_ROOT（绝对路径）、MAM_BRANCH（有效本地分支名）。找不到报错；最近文件无效报错，不向上回退。取消硬编码root和环境默认回退；不另建项目注册系统。建议删除--root，以免与唯一配置来源冲突；测试改用临时项目env.json。help在无配置时可用。
MAM_ROOT隔离所有task/job/wait/锁/归档登记，PROJECT_ROOT/workspace管理任务工作区，业务仓库来源PROJECT_ROOT/REPO（保持现有布局），MAM_BRANCH是已发布task/report所在分支。所有写死main的发布/读要求/状态逻辑改用配置分支；发布要求MAM checkout在该分支，不自动切换。MAM_ROOT可以是普通checkout或linked worktree，不要primary()将linked根错误归并。保留现有并发发布、边界安全、进程身份保护。

## 交付与验证
修改代码、测试、设计文档和install文档相关内容；README/AGENTS由Manager修改，避免同时编辑。覆盖两独立项目隔离、子目录发现、最近优先、缺失/坏配置、路径别名、linked MAM根、非main发布且main不变、错误分支拒绝、已有记录/job不损坏；完整测试通过。用旧安装mam在共享根发布交付报告，Manager在验收后才迁移生产。不要更改现有生产分支、配置、运行中的训练和环境；不得自行安装合并。清理短测试产物，保留worktree。报告给出commit、修改文件、测试和Manager迁移注意事项。
