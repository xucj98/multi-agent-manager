# native multi-agent v2 wake rejection fix

代码交付为核心 runtime 修复
`46af8c2afd3790a8e1d0538e4f624170753e67fc`、此前 fixture 加固
`fda59da93c2ba5bc74fd130b6c5ce0de33b3bad3`，以及本次针对独立终审三项问题的
`3f2738abcfc9cbe50b25222562fc58b2bac0a7ff`。工作分支为
`task/b49a5b40-1d18-40e6-bc28-c5c57dc011f3`，worktree 为
`/mnt/public/xcj/Projects/workspace/b49a5b40-1d18-40e6-bc28-c5c57dc011f3/multi-agent-manager`。
真实验收应使用的新 source commit 是 `3f2738abcfc9cbe50b25222562fc58b2bac0a7ff`。

核心 runtime 的独立条件性 PASS 保持不变；本轮只修改
`scripts/native_v2_fallback_acceptance.py` 和
`docs/native-v2-fallback-acceptance.zh-CN.md`，没有修改 `Store`、`ProjectConfig`、产品导入结构、scheduler
或其他 runtime。

本轮修复内容：

- 所有 fixture MAM CLI 的精确 argv 统一为
  `[SOURCE_PYTHON, "-I", "-c", "from multi_agent_manager.cli import main; raise SystemExit(main())"]`。
  `prepare` receipt 的 `source_cli`、fixture README、parser help 和 runbook 使用同一入口，避免 `-m` 将
  `cli` 同时作为 `__main__` 与包模块加载。
- `_source_identity()` 通过既有隔离 Git helper 运行
  `status --porcelain=v1 --untracked-files=all --ignore-submodules=none`，拒绝任何 non-empty output，并在
  prepare receipt 写入 `source_clean: true` 和空 `source_git_status`。新增 `verify-source`，从 marker 取
  source/Python、复查完整 identity，并逐字段精确比对 `prepare.json`：HEAD、clean 状态、module paths、
  controlled CLI 和 Python 任何漂移均失败。runbook 在首次 fixture `service start` 前及最终 stop 且
  `running: false` 后调用它。
- 新增 `record-stopped`。它仅在 fixture state 为 `enabled: false` / `mode: disabled` 且传入的实际
  `service status` JSON 为 `running: false` 时写入 stopped receipt；receipt 将 blocked checkpoint 的
  TASK/JOB/Manager/child、source/escalation signatures、完整精确 payload/attempts、旧 daemon PID/identity
  与停止后的 service-status counter 和冻结 state counter 绑定。`assert --phase restarted` 必须同时读取
  blocked 与 stopped receipt，要求新 PID 不同，并以 `stopped_cycles + 2` 而非 blocked 时的旧计数
  验证 post-restart cycles。

有界验证均在自动删除的临时目录进行，未启动 scheduler、未连接 App Server、未创建真实 fixture task/job、
未安装或重启 production：

- `py_compile`、`plan`、所有新增子命令的 `--help`、`git diff --check` / `git show --check` 通过；runbook 的
  5 个 Bash code block 都通过 `bash -n`。
- 带 shadow `PYTHONPATH` 的隔离 project 实际使用新 `-I -c` wrapper 完成 `task show`、`service status`、
  `service stop` 和 `task archive`；全部成功且没有 daemon。这个检查覆盖 reviewer 复现的 `Store requires a
  project configuration` 入口问题。
- 通过真实脚本子命令和合成 fixture state 覆盖 restart 时序：blocked counter `10`、旧 daemon 停止后冻结
  `12`、新 daemon counter `13` 被拒绝，达到 `14` 才生成 restarted receipt。该 receipt 同时核验 blocked
  source/escalation 与旧 daemon identity。
- 独立临时 clone 和自己的 venv：clean source 的 `prepare` 与 `verify-source` 成功；已跟踪 package 文件 dirty
  时 `prepare` 拒绝；新建未跟踪但可导入的 package 文件时也拒绝；clean prepare 后创建空提交改变 HEAD 时
  `verify-source` 以 `source_commit` drift 拒绝。上述所有调用均在 shadow `PYTHONPATH` 下完成。

此前核心 runtime 的完整回归是独立验证的 `215` 项通过；本轮没有 runtime 变更，按任务约束未重复该套件。
未运行真实 native-v2 fixture、生产 task/job、scheduler、App Server、安装或 production restart。请独立 reviewer
只复审本次 diff 和上述三类针对性证据；真实 fixture 仍待 root Manager 在复审通过后安排。
