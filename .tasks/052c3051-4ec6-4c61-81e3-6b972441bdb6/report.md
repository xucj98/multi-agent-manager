# 独立终审：native-v2 fallback fixture（fda59da）

审查对象为 `fda59da93c2ba5bc74fd130b6c5ce0de33b3bad3`，相对前次终审的
`5b5ca3bb1524c53c8d39bbd2159c30b2bc40db9c`；源任务已发布 report revision 为
`ed4578374d7be9144dddab672c6f64eb02547bab`。审核 worktree 为
`/mnt/public/xcj/Projects/workspace/052c3051-4ec6-4c61-81e3-6b972441bdb6/multi-agent-manager`。

## 结论

**FAIL：不准入执行真实 fixture。**

先前对核心 runtime 提交 `46af8c2` 的条件性 PASS 保持不变。本次没有修改产品 runtime，且已正确修复上轮
Git 污染、部分 receipt 绑定、child archive attestation 及 stop 后等待的主要问题；但 runbook 当前无法运行任何
fixture service 命令，并且仍不能证明所声明的 post-restart cycle 数或精确 source commit。因此不能以它执行
真实 native-v2 fallback 验收。

## 阻塞问题

### P1：受控 CLI 的 `-m` 入口将 `cli` 加载两次，所有 service 命令失败

`docs/native-v2-fallback-acceptance.zh-CN.md:23,45` 把 `MAM` 定义为：

```bash
MAM=("$SOURCE_PYTHON" -I -m multi_agent_manager.cli)
```

同一错误还被写入 `scripts/native_v2_fallback_acceptance.py:239,690,1059` 的 receipt、fixture README 和帮助文案。
`python -m multi_agent_manager.cli` 将文件作为 `__main__` 执行；随后 `cli.service_module()` 导入
`multi_agent_manager.wake_runtime`，后者在 `wake_runtime.py:29` 导入包名下的
`multi_agent_manager.cli`。于是存在两组不同的 `ProjectConfig` 与 `Store` 类。

`cli.main()` 用 `__main__.ProjectConfig` 创建 `store.config`，但 `wake_runtime.stop_service()` 在
`wake_runtime.py:592` 用包名下的 `Store(config)` 重建 Store；后者的
`cli.py:167-170` `isinstance(config, ProjectConfig)` 检查拒绝该不同模块实例。`service_start`、
`service_stop` 和 `service_status` 都经由 `cli.py:1141-1158` 的相同路径，因此都受影响。

在自动删除的临时 sibling `state`/`project` 中，带 shadow `PYTHONPATH` 且不启动 scheduler 的复现为：

```bash
"$SOURCE_PYTHON" -I -m multi_agent_manager.cli service stop
# exit 2; stderr: {"error": "Store requires a project configuration"}
```

同一环境下 `task show` 正常，说明项目配置本身可读；但 runbook 必需的 `service start`、`service stop` 和
stop 后 `service status` 都不能执行，故无法到达 scheduler、restart 或 cleanup 步骤。未启动任何 service。

最小修复是始终将 CLI 作为包模块导入一次：

```bash
MAM=(
  "$SOURCE_PYTHON" -I -c
  'from multi_agent_manager.cli import main; raise SystemExit(main())'
)
```

并令 `_source_identity()` 记录完全相同的 `source_cli` argv，更新 fixture README/帮助和文档中的所有描述。
在相同临时项目和 shadow `PYTHONPATH` 下，上述 wrapper 的 `task show` 成功，`service stop` 返回
`{"status":"disabled","running":false}`，`task archive` 将仅该临时 task 标为 `archived`；未生成 daemon log，
确认没有启动 scheduler。

### P2：restart receipt 将 stop 前 cycle 计入“两个 post-restart cycle”

文档 `docs/native-v2-fallback-acceptance.zh-CN.md:141-154` 要求两个 **post-restart** cycle，并声称不会从
pre-stop cycle 推断。实际实现 `scripts/native_v2_fallback_acceptance.py:884-886` 仅要求：

```python
payload["service_cycles"] >= baseline["service_cycles"] + 2
```

`blocked.json` 在 stop 前生成；`wake_runtime.py:1598-1600` 的 `counters["cycles"]` 持久保存在 service state，
`start_service()` 不会重置它。因此可复现的计数为：blocked baseline 为 10，root 在 stop 前多等两个旧 daemon
cycle，重启后新 PID 只完成一个 cycle，当前值为 13；`13 >= 10 + 2` 通过，却只证明一个 post-restart cycle。

应在 `wait_fixture_service_stopped` 返回后、启动新 daemon 前记录一个新的停止 checkpoint（或相等的 frozen
counter），并要求 restarted receipt 相对该 checkpoint 增加至少 2，同时仍将 PID/source/escalation 身份绑定到
`blocked.json`。不要用更早的 blocked counter 证明 restart 后的 cycle 数。

### P2：source identity 接受 dirty source worktree，receipt 可错误标注为交付 commit

`_source_identity()` 在 `scripts/native_v2_fallback_acceptance.py:178-241` 核验 source HEAD 和三个 module path，
但从不要求 source worktree clean；`command_prepare()` 随后将该 HEAD 写为 `source_commit`。待测 Python 是
editable source worktree 的 Python，因此一个已修改但未提交的包文件会实际运行，同时 receipt 仍声称运行交付
commit。

我在自动删除的本地 source clone 中，保留 HEAD 为 `fda59da`、仅给已跟踪的
`multi_agent_manager/__init__.py` 加一处未提交修改，并建立仅指向该 clone 的临时 venv。`_source_identity()`
成功返回 `source_commit == fda59da`，且三个 module path 全在这个 dirty clone 中。这证明 HEAD/module-location
检查不足以支撑“待验收 source commit”的断言。

`prepare` 至少应以隔离 Git 环境拒绝非空的 `git status --porcelain`（或等价 HEAD tree 差异），把 clean result
写入 receipt；在首次 `service start` 前和最终停止后应再次核验同一 HEAD、clean 状态及 module paths，或将待测
source worktree 保持只读。这样才不会在 fixture 期间把未提交代码归因给 `fda59da`。

## 已确认的修复与验证

- `git diff --check 5b5ca3b..fda59da`、`git show --check fda59da`、
  `.venv/bin/python -B -m py_compile scripts/native_v2_fallback_acceptance.py` 通过；`plan` 与 `--help` 可运行。
- 在自动删除的临时目录中，直接导入 helper 并设置恶意 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、
  `GIT_CONFIG_GLOBAL`、`GIT_TEMPLATE_DIR`、`GIT_EXEC_PATH`、外部 hooks/template 后，新的
  `_fixture_git_env()` / `_run_fixture_git()` 没有改写外部 repo、config、index 或 HEAD，也没有运行外部 hook；
  fixture Git top-level 与 git-dir 正确。
- `-I` 下的 module-path 查询抵抗 shadow `PYTHONPATH`，并正确识别 source `fda59da`；receipt helper 会拒绝错误
  escalation error、错误 source signature 及错误 attempts。archive history/child archive 的新 signature 和
  attestation 绑定方向正确。
- 未运行 fixture script 的任何子命令，未创建真实 fixture task/job，未启动 scheduler、未连接 App Server、未发送
  follow-up，也未修改作者 worktree 或生产 MAM 状态。

修复 P1 与两项 P2 后，应先复审更新后的 docs/script 和这三个针对性负例；本次仅改验收工具和文档，无需因这些
修复重复核心 runtime 的 215 项回归，除非产品 runtime 随之改变。
