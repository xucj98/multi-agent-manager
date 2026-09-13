# 独立复审：native-v2 fallback fixture（3f2738a）

审查对象为 `3f2738abcfc9cbe50b25222562fc58b2bac0a7ff`，相对上轮终审提交
`fda59da93c2ba5bc74fd130b6c5ce0de33b3bad3`；源任务已发布 report revision 为
`7812f66701f28336811bb864fd0e232b53e9de3d`。审核 worktree 为
`/mnt/public/xcj/Projects/workspace/052c3051-4ec6-4c61-81e3-6b972441bdb6/multi-agent-manager`。

## 结论

**条件 PASS：本轮 docs/fixture-script 的三个阻塞项均已修复，可交由 root Manager 决定是否按 runbook 进行受控的真实 fixture。**

此前对核心 runtime `46af8c2` 的条件性 PASS 保持不变。本轮只修改
`scripts/native_v2_fallback_acceptance.py` 与
`docs/native-v2-fallback-acceptance.zh-CN.md`，没有修改 scheduler、Store、ProjectConfig、App Server 或生产状态。
这不是实际 native-v2 链路已完成的证明；真实 fixture 仍须由 root 在既定隔离边界内另行执行和验收。

## 三项复审结果

1. **受控 CLI：PASS。** `CONTROLLED_CLI` 固定为
   `from multi_agent_manager.cli import main; raise SystemExit(main())`，`source_cli` receipt、fixture README、
   parser help 与 runbook 的 `MAM` array 都一致使用
   `SOURCE_PYTHON -I -c CONTROLLED_CLI`，不再以 `-m` 将 `cli` 同时加载为 `__main__` 和包模块。

   在自动删除的 sibling `state`/`project` 中，以 source `3f2738a` 的 Python、shadow `PYTHONPATH` 和该精确
   argv 实际运行 `task show`、`service status`、`service stop`、`task archive`：均成功；两个 service 命令都
   返回 `status: disabled`、`running: false`，task 最终为 `archived`。没有调用 `service start`，也没有生成
   daemon log。此前 `Store requires a project configuration` 的 `-m service` 入口已被覆盖。

2. **restart stopped receipt：PASS。** `record-stopped` 要求 state 为 `enabled: false` / `mode: disabled`，
   传入的 `service status` 必须为同一 Manager 的 `status: disabled`、`running: false`，并要求其 counters 与
   fixture state 一致。它把旧 PID/identity、完整 blocked checkpoint 的 source/escalation payload 与冻结的
   stopped counter 写入 receipt。`assert --phase restarted` 同时核验 blocked 与 stopped receipt，以
   `stopped_cycles + 2` 为阈值，并要求新的 scheduler PID。

   纯内存 receipt 测试覆盖 `blocked=10`、stop 后 `stopped=12`：restart counter `13` 被该实际 `+2` predicate
   拒绝，`14` 才通过；伪造 stopped counter 与 `running: true` service-status 均被拒绝。由此不再将 stop 前
   cycle 当成 post-restart cycle。runbook 也先保存 `FIXTURE_STOP_STATUS`，在 `wait_fixture_service_stopped`
   返回后写 stopped receipt，才启动新 scheduler。

3. **source identity：PASS。** `_source_identity()` 现在用既有隔离 Git helper 要求
   `status --porcelain=v1 --untracked-files=all --ignore-submodules=none` 为空，并记录
   `source_clean: true`、空 `source_git_status` 与新的 controlled argv。`verify-source` 从 marker 重新解析
   source/Python，以完整 identity fields 精确比对 `prepare.json`；runbook 在首次 service start 前和最终 stop、
   `running: false` 后分别调用它。

   在自动删除的本地 clone 和专属临时 venv 中，clean source identity 成功；已跟踪 package 文件修改和未跟踪
   package 文件都被 `_source_identity()` 拒绝；清理后创建空提交导致 HEAD drift 时，
   `_assert_source_identity_matches_prepare()` 以 `source_commit` 漂移拒绝。上述查询均带 shadow `PYTHONPATH`，
   `-I` 下仍只解析临时 source package。

## 验证与边界

- `git diff --check fda59da..3f2738a`、`git show --check 3f2738a`、
  `.venv/bin/python -B -m py_compile scripts/native_v2_fallback_acceptance.py` 通过。
- 5 个 Bash fenced block 均通过 `bash -n`。
- 未运行任何 fixture script 操作子命令，未创建真实 fixture task/job，未启动 scheduler、未连接 App Server、
  未发送 follow-up、未安装或重启 production，也未修改作者 worktree。
- 本轮没有产品 runtime 变更；按窄复审要求未重复核心 215 项单测。若后续改动 runtime，应重新运行其完整回归。
