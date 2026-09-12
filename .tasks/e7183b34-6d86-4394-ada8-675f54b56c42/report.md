# 实施中的接口对齐

共享合同已落实到运行时 worktree；发现并已处理一个具体状态协议差异：

- 运行时 `service_status()` 的实际 JSON 使用 `status`（`healthy`、`pending`、`awaiting_manager`、`disabled`、`error`）、`running`、`healthy`、`manager`，以及 `pending: {count, events}`。
- 安装器初稿曾按未细化合同使用 `state` 和整数 `pending`，不能直接消费该返回值。现在将 `wake_compat.service_readiness()` 改为上述真实结构：`healthy`、健康的 `pending` 和 fresh-project `awaiting_manager` 都是已确认的 daemon 状态；`disabled`/`error` 仍非零失败。既有 bound task 且无 Manager 时，安装器保持明确的 `mam service start --manager AGENT-ID` 诊断。

其余边界保持不变：无 systemd；runtime 负责 `.local/service` 的 detached singleton；安装器在 pipx 更新和 control-socket smoke 通过后才对当前项目调用 `status/stop/start/status`，并清除 `CODEX_THREAD_ID`。我将继续用该实际协议完成测试和提交。
