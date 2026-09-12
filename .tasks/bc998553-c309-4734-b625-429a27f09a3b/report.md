# MAM proactive wake runtime — review follow-up

实施 worktree：`/mnt/public/xcj/Projects/workspace/bc998553-c309-4734-b625-429a27f09a3b/multi-agent-manager`；分支：`task/bc998553-c309-4734-b625-429a27f09a3b`。

原始 runtime 提交为 `bf157209d6eb9ebdc0d07f5344ca175501941598`；本次供 Manager cherry-pick 的后续提交为 `45614a60f63517eff3075381c697d370f09bdccc`（`fix: reconcile proactive wake delivery states`）。

## 已修复的验收阻断项

- paused/interrupted 收件人会持久化阻断 turn 边界。后续仅在其元数据为 idle/notLoaded 时读取一次 `latest_turn`，不会为重查调用 `resume`；只有边界变化且最新 turn 为 completed 时才重新置为 pending。仍中断、边界未变或收件人 active 时不会启动 turn。
- `task_ready` 的 source executor 为 unknown/systemError 或发送前查询失败时，保留相同签名的 pending/accepted 事件，不生成新事件；归档、review 抑制、执行者重绑和 source active 仍会使旧事件失效。
- App Server 明确 JSON-RPC error 现在以兼容 `AppServerEventError` 的 `AppServerRpcError` 表示。`turn/start` 的明确拒绝记录为 retryable `rejected`，不会被后续无关 turn 误判为 `ambiguous`；仅无响应、传输失败和 daemon 在应答前退出进入 `uncertain` 边界对账。

设计文档已同步上述状态语义。

## 回归与验证

新增 fake App Server/调度回归覆盖：中断后 completed 恢复且 active→idle 才单次启动、重查不 resume；accepted/pending `task_ready` 经 unknown 读失败后仍不重复唤醒；归档、review 抑制和重绑失效；明确 RPC 拒绝的 retry；以及既有 response-loss→ambiguous 路径。

```text
.venv/bin/python -B -m unittest tests.test_wake_runtime tests.test_job_runtime -v
# 47 passed
.venv/bin/python -B -m unittest discover -s tests -v
# 109 passed
git diff --check
# passed
```

未修改 `scripts/install.sh`、`wait_compat.py`、installer 测试、README 或 AGENTS；未安装、部署、重启 App Server，且未创建真实 Codex 线程或 GPU 作业。
