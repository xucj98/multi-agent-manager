# 独立终审：native-v2 fallback fixture

审查对象为 `5b5ca3bb1524c53c8d39bbd2159c30b2bc40db9c`，相对已审核心修复
`46af8c2afd3790a8e1d0538e4f624170753e67fc`；源任务本次已发布 report revision 为
`84411294455169c96f2cb63e0070316703e7f7d9`。审核 worktree 为
`/mnt/public/xcj/Projects/workspace/052c3051-4ec6-4c61-81e3-6b972441bdb6/multi-agent-manager`。

## 结论

**FAIL：不准入执行真实 fixture。**

先前对核心 runtime 提交 `46af8c2` 的条件性 PASS 仍有效：本次 README/设计文档已准确补足
`manager == executor` 只 blocked、不 self-escalate，以及 executor `active` 不代表 stopped job 已收尾的
P3 说明。本次新增的隔离验收脚本和 runbook 未达到其承诺的隔离与可复核程度，因此不能作为上线前真实
native-v2 fallback 证据执行。

## 阻塞问题

### P1：fixture Git 初始化继承调用方的 Git 上下文

`scripts/native_v2_fallback_acceptance.py:364-380` 的五个 `subprocess.run` 调用均没有 `env=`。因此
`git init`、`git -C state config`、`add` 和 `commit` 会继承调用方的 `GIT_DIR`、`GIT_WORK_TREE`、
`GIT_INDEX_FILE`、`GIT_CONFIG_*`、`GIT_TEMPLATE_DIR`、`GIT_EXEC_PATH` 等变量，也会继承全局/系统配置和
可能的 hook 路径。`-C state` 不能防止 `GIT_DIR` 重定向仓库：在两个新的临时仓库中设置
`GIT_DIR=<outside>/.git` 后，等价的 `git -C <fixture-state> config user.name ...` 实际修改了
`<outside>/.git/config`。

这直接违反 runbook 在 `docs/native-v2-fallback-acceptance.zh-CN.md:15-17` 所作的“只读写 fixture”保证，
并可让 `commit` 运行外部 hook 或改写生产 Git 的 config/index/提交。不能在此状态下运行 `prepare`。

修复应为每一个 Git 子进程构造专用环境：删除所有继承的 `GIT_*`，固定/禁用 global 与 system config，使用
fixture 自己的空 template 和 hooks 目录，并将该 `env` 传给每一次调用。初始化后还应以该净化环境确认
`git -C state rev-parse --show-toplevel` 和 git-dir 都属于 fixture state；任何失败只留下可安全诊断的
owned partial fixture，不能触及外部仓库。

### P2：restart checkpoint 既可能失败，也没有证明所声称的两个 cycle

runbook 在 `docs/native-v2-fallback-acceptance.zh-CN.md:97-99` 紧接着执行 `service stop` 和
`service start`。`wake_runtime.stop_service()` 先将 state 标为 disabled、发送 `SIGTERM` 后立即返回；若旧
PID 尚存活，`start_service()` 会拒绝并报 “the previous detached service is still stopping”。这是一条正常的
竞态，当前步骤不能可靠完成 required restart checkpoint。应在两条命令之间轮询**fixture** `service status`
直到 `running: false`，再启动。

即使成功重启，`scripts/native_v2_fallback_acceptance.py:485-486` 只要求
`service_cycles > baseline`，而文档声称至少两个 cycle。一次 post-restart cycle 就能通过。应要求明确的最小
增量（至少 `baseline + 2`，或加入 restart 前 checkpoint 以验证文档所说的两个 pre-stop cycle），同时保持并
复核 source/escalation signature、attempts 和 pending delivery。

### P2：source checkout 与 fallback payload 的证据链未闭合

- 文档在 `docs/native-v2-fallback-acceptance.zh-CN.md:26,50` 声称 source worktree 的 `.venv/bin/mam`
  会运行待验收 source；`prepare` 在脚本 `:339-343` 只检查 launcher 和 source 文件存在。该 console script
  没有隔离解释器，继承的 `PYTHONPATH` 可优先加载另一 checkout。独立临时 shadow package 复现了
  `PYTHONPATH=<shadow> "$SOURCE_ROOT/.venv/bin/mam" task list` 调用 shadow `cli`。后续 detached daemon 虽
  使用 `-I -S`，其 package path 却来自先前被加载的 `wake_runtime`，所以这会验到错误的代码。
  runbook 应使用 `"$SOURCE_ROOT/.venv/bin/python" -I -m multi_agent_manager.cli`（或等价受控 wrapper）
  调用全部 fixture CLI，并在 prepare receipt 中记录、核验 `multi_agent_manager.__file__`、
  `wake_runtime.__file__` 和待测 Git commit。
- `_running_fixture_context()` 在脚本 `:258-260` 校验 source 的 `last_error` 和 `source_event`，但没有要求
  Manager escalation 的 `error == EXACT_REJECTION`。`delivered` 的人类 attestation（`:503-505`）也只要求
  `[MAM Message]`、TASK-ID 和 JOB-ID。故“Manager 收到精确拒绝”可以在错误 payload 下通过。应同时校验
  escalation error、source-event linkage，并要求 attestation 包含精确错误。
- `assert-archived`（`:529-534`）只要求任何匹配的 history source/escalation 有非空 resolution。它没有将
  history signature 与 blocked/restarted/delivered receipt 绑定，也不重验 blocked 的 exact error、attempts、
  escalation source_event/error/accepted 状态。这允许无关的旧 history 充当 archive-stale 证据。应以 delivered
  receipt 为 baseline，要求两个 history entry 使用同一 signature，保留精确 blocked/escalation 字段，并记录
  预期的 stale resolution。当前 state 不能证明是哪位人执行了 `job archive`，所以“由 child archive”应保留
  人工 attestation，不能仅由非空 report 推断。

## 验证证据

- `git diff --check 46af8c2..5b5ca3b`、`git show --check 5b5ca3b` 通过；
  `.venv/bin/python -B -m py_compile scripts/native_v2_fallback_acceptance.py` 通过。
- 在一个自动删除的临时 sibling `state`/`project` 目录中，以作者 source worktree 的 venv 且清除
  `PYTHONPATH`/`PYTHONHOME` 运行：`task show` 正确从 `project/.mam/env.json` 解析并读取 published task；
  未启动 service 的 `service stop` 创建 `disabled` state；`task archive` 正确写 sibling state，并保留 archived
  job 的 `probe.status == "stopped"`。没有启动 scheduler、App Server、fixture 或生产 daemon。
- 以 source runtime 的纯内存 `_resolve_event` 验证 history 保留 source `signature`，并验证
  `_job_stopped()` 接受 `probe.status == "stopped"`。这些底层假设成立，问题是新增 verifier 没有将其与
  receipt 严格绑定。
- 临时 Git 重定向和 Python shadow 均在自动删除的目录内完成，未读取或写入生产 task/job/service state，未创建
  thread、未发送 follow-up、未调用 fixture script 的任何子命令。

本次新增内容未修改产品 runtime，故没有重复先前已独立完成的 215 项全量单测；在 P1/P2 修复并提交后，应先
复审脚本/文档，再决定是否准入真实 fixture。
