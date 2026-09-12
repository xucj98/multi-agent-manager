# 实施中的接口对齐

共享合同已落实到运行时 worktree；发现并已处理一个具体状态协议差异：

- 运行时 `service_status()` 的实际 JSON 使用 `status`（`healthy`、`pending`、`awaiting_manager`、`disabled`、`error`）、`running`、`healthy`、`manager`，以及 `pending: {count, events}`。
- 安装器初稿曾按未细化合同使用 `state` 和整数 `pending`，不能直接消费该返回值。现在将 `wake_compat.service_readiness()` 改为上述真实结构：`healthy`、健康的 `pending` 和 fresh-project `awaiting_manager` 都是已确认的 daemon 状态；`disabled`/`error` 仍非零失败。既有 bound task 且无 Manager 时，安装器保持明确的 `mam service start --manager AGENT-ID` 诊断。

其余边界保持不变：无 systemd；runtime 负责 `.local/service` 的 detached singleton；安装器在 pipx 更新和 control-socket smoke 通过后才对当前项目调用 `status/stop/start/status`，并清除 `CODEX_THREAD_ID`。我将继续用该实际协议完成测试和提交。

另一个实际对齐点：runtime 的 fresh `awaiting_manager` 路径刻意不连接 App Server；无 Manager、无 bound task 的首装不应因 control socket 尚不存在而失败。安装器将仅在已有/显式 Manager 或已有运行 service 的更新路径强制 `wake_compat` smoke（且在 stop 前完成）；纯 fresh idle 路径启动 daemon 后明确报告 compatibility 将在首次 Manager binding/reconnect 时验证，绝不声称已能投递任务。

## 提议的隔离验收（尚未执行）

自动 `wake_compat` 不创建/修改任何真实 thread：对每次临时随机、从未登记的 UUID 依次发出实际 runtime 所需的 `thread/read`、`thread/resume`、`thread/turns/list`、`turn/start` 参数；四项都必须返回 JSON-RPC “thread not found”类拒绝。这样验证方法名、参数形状、请求/响应通路和 `turn/start` 的前置拒绝，不启动模型请求，也不把成功握手误标为 eventstream/wakeup 已验证。若随机未知 thread 的 `turn/start` 意外成功，立即非零失败且不重试。

真实 E2E 需要 Manager 事先登记并协调：创建独立 MAM project/task 和已绑定的专用 agent，登记一个短命本地 job，启动该项目 scheduler，验证该既有 agent 收到含 JOB-ID/note 的简短 wake prompt；随后 archive job/task、stop 隔离 service 并保留验收记录。不会触碰生产 task、用户 thread 或训练任务。请 Manager 在准备好隔离 agent/project 后明确通知；在此之前只运行 fake-App-Server 单元/子进程测试，不执行真实 thread/turn。
