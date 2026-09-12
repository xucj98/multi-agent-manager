# task rebind 独立 review：PASS

核验候选提交：`bc8726f3e2f13351c52650f03bc88bd76a68ed25`，相对任务指定 base `2cb730944dc7574feaff92253ef09644ae06c1da`。独立 review worktree 为 `/mnt/public/xcj/Projects/workspace/492c83a2-d96a-452a-84ba-c3365cf42cea/multi-agent-manager`，其 HEAD 为该候选提交。

## 结论

PASS。未发现阻断问题；建议可上线，最终裁决仍由 Manager 完成。

- `mam task rebind TASK-ID --agent AGENT-ID --note NOTE` 仅允许已记录 Manager 调用；拒绝归档/未绑定任务、Manager 作为替换目标、替换目标已绑定其他未归档任务，以及格式或状态无法核实的 executor。旧/新 executor 只有经只读 `thread/read` 确认为 `idle` 或 `notLoaded` 且没有活跃/不可核实的 optional wait 才会交接；同目标重试是无写入的 `unchanged`。
- 交接只改写任务的当前 `agent` 并附加 `{from_agent,to_agent,at,note,manager}` 审计。task/report publication、workspace、repos/worktree/branch、job ID/PID/identity/观测/历史与 review 引用保持原值；没有复制或重建 worktree、重启 job 或改写 Codex parent/UI 元数据。
- 锁序实现为 `service-start → service-cycle → bindings → task → sorted wait locks`。调度完整 cycle 被串行化，旧收件人的 pending、accepted、uncertain stopped-job 事件在下一 cycle 因 currentness 变化转入历史，原 stopped job 随后投递新 executor；Manager/review 路由按当前 task agent 重新计算。核对 bind、archive、wait 注册/取消及 `wait stop manager` 路径，未见反向嵌套锁依赖。
- README 保持为简短操作步骤；设计文档准确记录交接边界、锁序、幂等和审计，也已将长 job 阈值更新为 30 分钟。

## 验证

- `mam workspace add 492c83a2-d96a-452a-84ba-c3365cf42cea --repo multi-agent-manager --base bc8726f3e2f13351c52650f03bc88bd76a68ed25`：成功创建隔离 worktree。
- `.venv/bin/python -B -m unittest discover -s tests -v`：206 tests passed，80.674s。
- 定向交接验证（状态/元数据、optional wait、scheduler cycle、accepted/uncertain 旧待办失效、`wait stop manager` 并发）：7 tests passed。
- `.venv/bin/mam task rebind --help`：接口与必填参数正确；`git diff --check 2cb730944dc7574feaff92253ef09644ae06c1da bc8726f3e2f13351c52650f03bc88bd76a68ed25`：通过；review worktree clean。

本 review 未部署、未执行真实 task rebind，也未改动生产 service state、源任务绑定或 job。
