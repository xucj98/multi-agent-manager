# 独立复审：统一 mam wait、安装器与 native 输入（仍有两个 P1）

审查 workspace：/mnt/public/xcj/Projects/workspace/8d648d66-b920-4a00-9472-cb7651412028/multi-agent-manager。

审查分支 HEAD 为 `1a9eeaa`，是对 `main@87f02d3` 的最终 merge（包含运行时 `758d523`、安装器 `b4382a2` 与生命周期补丁 `0dd2bcd`）。未修改实现代码，未重启生产 App Server 或改动 GPU/job。

## 阻断项

1. **[P1] native journal 在实际 invocation 边界仍有漏消息窗口。**
   - 位置：`multi_agent_manager/cli.py:920-928`，`multi_agent_manager/wait_runtime.py:292-319,321-328`。
   - 触发：CLI 先记录 `started_at`，但 `SessionMessages.from_environment()` 还会递归查找 journal、读取候选 header，最后才以 EOF 打开命中的文件。若 native `user.text` 在 `started_at` 之后、EOF 打开之前写入，它虽属于本次调用，仍被 EOF tail 永久跳过；event stream 也尚未订阅，不能补回。
   - 最终代码复现：在临时 current-session journal 中，让有效、当前 turn 的 `user.text` 在 `Path.glob()` 的候选查找期间写入；`from_environment(..., started_at=boundary)` 返回 watcher 后 `poll()` 为 `[]`。现有回归只覆盖 watcher 已经打开时的 compatibility 阶段。
   - 影响：刚开始 `mam wait` 时的 Manager 输入可能被遗漏，随后只能等其他状态变化或一小时超时。应让 identified journal 的可读取边界覆盖 discovery/open，或从 invocation timestamp 扫描该 journal，并增加上述 lookup-window 回归。

2. **[P1] 已确认 TERM 后的任一 relaunch 失败会让 App Server 保持停止。**
   - 位置：`scripts/install.sh:1057-1088`；相关承诺在 `docs/install.md:30-34`。
   - 触发：`send_term` 成功后，`wait_for_target_departure`、`launch_same_style` 或 `wait_for_replacement` 失败只释放 lock 并非零退出；没有 post-TERM recovery/trap。信号中断也落在这个区间。
   - 最终代码复现：用隔离的、满足 discovery 规则的 node wrapper/listener；listener 收到 TERM 后令已捕获的 `codex` wrapper 失去可执行权限。安装器只 TERM 该 listener，随后报 wrapper no longer runnable，返回 `1`；检查结果为 `post-term-socket-present=0`、`original-wrapper-running=0`。未接触生产进程。
   - 影响：已确认的安装操作能将可用 App Server 留在停止状态。至少应在 TERM 前预检完整 launch plan，并在 TERM 后失败/信号时做身份受限的恢复，或输出立即可执行、精确的人工恢复命令；不需要因脚本体积而重写其它启动流程。

## 最终增量与 native 证据

- `87f02d3` 的 `wait_runtime.py:738-745` 会忽略执行者连接中、尚未订阅的其他 bound agent 生命周期事件；它仍处理已订阅 caller 的事件和 current-turn `userMessage` item。新增回归先注入该无关事件再注入 caller native item，最终返回 `message`。未发现这个小补丁引入新的生命周期/queue blocker。
- 任务提供的协调真实 smoke 证据 `.local/native-wait-coordinated-900-1789145948-output.txt` 返回 `status=message`、`reason=message`、`message=received new message`，对应已就绪的 wait `67161` / job `fb8b8aa3-843b-422d-83f9-603950d0f79d`。这证明一条正常 `send_input` 在 ready 后成功唤醒；它不覆盖第 1 项 discovery 窗口，也不替代尚在整理的 latency/job-alive/cleanup 证据。
- journal watcher 对缺失 `CODEX_HOME`/`CODEX_SESSION_ID`、非唯一/错误 header、rotation、truncate 和不完整 native metadata 均显式报错；queue 的隔离 App Server 测试仍显示 `thread/queue/add` 只产生 queuedSubmission/queue change，不写当前 user-message row，`queue/start` 的后续 turn 也会被 current-turn 过滤。
- `wait_compat` 仍明确输出 native wake **not certified**，`docs/install.md:38` 同样没有过度声称。最终 live compatibility PASS 只验证 control socket、trace 和隔离 server 行为；一次耗时 1.416s，未创建真实模型 turn 或重启生产服务。

## 已接受项及文档复查

- exit-status propagation 已修复：trace 环境不匹配返回 1、不可读 PID 返回 2。
- trace watcher 在 compatibility 前建立，且每个新增行按 invocation timestamp 过滤；相应 setup/stale-row 回归均通过。
- installer happy path 能捕获并重放实际 node wrapper 的 argv、cwd、stdio 和环境，只替换两项 trace 设置；隔离同式重启测试通过。第 2 项仍使失败路径不可接受。
- README、AGENTS、wait design 与 install 文档对自动 scope、当前状态语义、queue、固定一小时、compatibility 非 native 认证的描述一致且足够简洁；修复第 2 项时应同步写明实际恢复行为。

## 验证

- `.venv/bin/python -B -m unittest discover -s tests -v`：**102 tests passed**，27.421s。
- `bash -n scripts/install.sh`、`git diff --check cc69d437..HEAD`：通过。
- 上述 native discovery-window 与 installer post-TERM 复现均在临时目录完成，过程/临时文件已清理。
- `.venv/bin/python -B -m multi_agent_manager.wait_compat`：通过；对生产 control socket 仅做 initialize/trace 读取，输出明确不认证 native wake。
