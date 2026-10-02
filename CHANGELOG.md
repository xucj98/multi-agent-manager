# 版本说明

## 0.2.3

- 停用 MAM 工具消息渠道，全部通知使用用户消息，避免 HTTP 会话压缩后新增缺少 `call_id` 的工具结果；升级在备份后同步旧渠道设置。
- 任务交接统一由新执行者调用 `mam task start`；保留 `mam service rebind-manager`。

从上一版本升级的操作见 [0.2.3 适配说明](docs/upgrades/0.2.3.md)。

## 0.2.2

- 修复 Codex 收件人处于 `notLoaded` 状态时的自动唤醒预检，恢复提醒和消息投递。
- 修复普通终端通过显式 AGENT-PATH 查询任务时仍要求调用者身份的问题。
- 将 `mam task list` 简化为标题、任务状态、TASK-ID、执行者、agent 状态五列。
- 增加 0.2.1 到 0.2.2 的空操作数据迁移、测试 fixture 和真实旧版升级验收。

从上一版本升级的操作见 [0.2.2 适配说明](docs/upgrades/0.2.2.md)。

## 0.2.1

- 安装器通过 `mam-codex-check` 运行分层兼容性验收，保留版本、提交、阶段耗时、测试摘要和原始证据。
- 修复发布包下载、基础 Python 定位和旧版 worktree hook 的可靠性问题。
- 增加从 0.2.0 到 0.2.1 的空操作数据迁移和独立测试 fixture；完整旧版升级回归仍由发布集成入口执行。

## 0.2.0

- 安装与实例配置分开：`install.sh` 安装或更新系统程序，`mam service upgrade` 升级一个实例，`mam service start` 启动服务。
- 提供程序、daemon 和数据版本信息，按版本连续迁移，以及按版本创建 `mam-test` 和一键集成测试。
- 执行者用 `mam task start` 首次登记或接手任务；Manager 可通过 AGENT-PATH 定位任务，通过 `service rebind-manager` 接管实例。
- 任务按执行者活动和未归档 job 自动判断 working/pending；Manager 可用 `task block` 暂缓 pending 任务，恢复工作时自动转为 working。
- `task publish` 发布要求，`task report` 一起发布报告和附件；workspace 中的 `.task` 链接提供任务文件入口。
- 项目通过 `.local/hooks/` 配置 workspace 创建和归档前检查。归档清理 worktree、任务分支与 workspace；`--force` 显式使用 Git 强制清理。
- 新增 `mam message send`；默认在 Manager 空闲时投递，`--immediate` 可投递到当前 turn。`service set message-channel` 选择工具或用户消息渠道。
- 自动提醒在收件人空闲时按当前状态生成，每个任务最多提醒 3 次，状态变化后重新计数；消息头显示类型和来源。job 退出状态统一为 exited，通知由执行者查询和处理。
- 移除 `mam wait`，由 service 在需要处理后续工作时唤醒负责人。

从 0.1.0 升级的操作变化见 [0.2.0 适配说明](docs/upgrades/0.2.0.md)。

## 0.1.0

首个升级基线，提供 task、workspace、job 管理及自动唤醒服务。
