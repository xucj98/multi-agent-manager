# 版本说明

## 0.2.0（未发布）

- 安装与实例配置分开：`install.sh` 安装或更新系统程序，`mam service upgrade` 升级一个实例，`mam service start` 启动服务。
- 提供程序、daemon 和数据版本信息，按版本连续迁移，以及按版本创建 `mam-test` 和一键集成测试。
- 执行者用 `mam task start` 登记或接续任务，返工时进入 working；Manager 可通过 AGENT-PATH 定位任务，通过 `service rebind-manager` 接管实例。
- `task publish` 发布要求，`task report` 一起发布报告和附件；workspace 中的 `.task` 链接提供任务文件入口。
- 项目通过 `.local/hooks/` 配置 workspace 创建和归档前检查。归档清理 worktree、任务分支与 workspace；`--force` 显式使用 Git 强制清理。
- 新增 `mam message send`；默认在 Manager 空闲时投递，`--immediate` 可投递到当前 turn。`service set message-channel` 选择工具或用户消息渠道。
- 自动提醒根据任务、job 和关联 review 的当前状态合批投递，说明需要执行的动作。job 退出状态统一为 exited。
- 移除 `mam wait`，由 service 在需要处理后续工作时唤醒负责人。

从 0.1.0 升级的操作变化见 [0.2.0 适配说明](docs/upgrades/0.2.0.md)。

## 0.1.0

首个升级基线，提供 task、workspace、job 管理及自动唤醒服务。
