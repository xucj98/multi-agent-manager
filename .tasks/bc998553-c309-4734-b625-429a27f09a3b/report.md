# MAM proactive wakeup runtime implementation

完成。实施 worktree：`/mnt/public/xcj/Projects/workspace/bc998553-c309-4734-b625-429a27f09a3b/multi-agent-manager`，分支 `task/bc998553-c309-4734-b625-429a27f09a3b`，交付提交：`bf157209d6eb9ebdc0d07f5344ca175501941598`（`feat: add proactive wake service runtime`）。

## 实现内容

- 移除公开的 `mam wait`、wait 状态存储、`wait_runtime.py` 及其专用测试；新增 `mam service start [--manager AGENT-ID]`、`stop`、`status`。
- 新增项目隔离的 `wake_runtime`：在 `MAM_ROOT/.local/service/` 持久化 daemon 身份、Manager、待投递事项、投递回执、探测计划、诊断和计数；提供同步的 `start_service(config, manager=None)`、`stop_service(config)`、`service_status(config)`。
- daemon 使用独立 session，启动时核验自身 token/PID/身份后才报告 ready。首个 active 调度周期前状态为 `pending`；兼容性、旧 PID 身份或启动错误会持久化为可查询 `error`，无法核验已有 PID 时拒绝启动第二个 daemon。
- 首次无任务项目可处于 `awaiting_manager`；未绑定调用者在 `task create` / `task bind` 时从 `CODEX_THREAD_ID` 登记为 Manager。已绑定任务而没有可靠 Manager 时显式失败，不猜测线程。没有硬编码的旧 Manager ID。
- 调度按未归档任务独立处理：stopped job 优先投递给任务执行者，running-only job 只监控；空 job 的 idle 或 `notLoaded` 执行者形成 Manager 待办；review 会抑制源任务 idle 提醒但不会隐藏 stopped job。
- 监控阶段只做批量 `thread/read` 元数据查询；仅在实际待投递的目标上 resume。`notLoaded` 被视为已知可恢复线程，先 `thread/resume`，再 `thread/read` 复核为 idle；删除、缺失、capacity 和 paused/interrupted 均保留可见待办，不创建替代线程或盲目重启。
- `turn/start` 前持久化最新 turn 边界。RPC 应答丢失或 daemon 崩溃后先读取该收件人的最新 turn：边界未变才有退避重试，已变则标记 `ambiguous` 并停止自动重试，避免重复模型请求。
- 扩充 App Server 客户端的目标 `read`、`latest_turn`、`start_turn` 接口，不覆写 model、effort、cwd、sandbox 或 workspace。设计文档已同步服务模型与验收语义。

## 验证

- `.venv/bin/python -B -m unittest discover -s tests -v`：101 项通过。
- `git diff --check`：通过。
- CLI help 核对：顶层只显示 `task`、`job`、`service`、`workspace`，`service` 显示 start/stop/status。
- 新增 fake-App-Server 覆盖现有线程的 `turn/start`、`notLoaded -> resume -> read -> latest_turn`；调度测试覆盖 stopped/running 路由、busy 保留、review 抑制、未知探测、任务锁竞争、批量去重、restart/应答丢失歧义、paused/interrupted、并发启动、多项目、fresh bootstrap 与旧 PID 身份错误。
- 新增短暂真实 daemon smoke：无 Manager 的临时项目进入 `awaiting_manager`、确认 ready 后 `service stop` 正常退出；未连接 App Server，未创建 Codex 测试线程。

## 集成边界

本分支按约定动态导入 Manager 负责的 `multi_agent_manager.wake_compat.require_compatible()`；该共享 installer/compat 实现尚未并入本 worktree，因此没有进行生产安装、App Server 重启或真实训练任务投递。README、AGENTS、安装脚本和旧 `wait_compat` 均未修改。真实已登记 agent 的端到端唤醒和生产 rollout 仍由 Manager 在集成后执行。
