# 独立验收：统一 `mam wait` 与安装器（未通过）

审查 workspace：`/mnt/public/xcj/Projects/workspace/8d648d66-b920-4a00-9472-cb7651412028/multi-agent-manager`。

审查分支 HEAD 为 `686be5d`，其中合并了当前实现 `main` 的 `1800659`（运行时 `cc69d43`、兼容性/安装器 `e20da6d` + `e23d693` 和后续测试/pipe 修复）。未修改实现代码。

## 阻断项

1. **[P0] 安装器把不满足 trace 环境误判为成功。**
   - 位置：`scripts/install.sh:305-334`，以及调用处 `471-478`。
   - 触发：`runtime_logging_ready` 内嵌 Python 以 1（环境缺失）或 2（`/proc/PID/environ` 不可读）退出时，`if ...; then ...; fi` 后的 `$?` 是整个 `if` 的 0，不是 Python 的退出码。因此函数返回 0。调用方的 `if ! runtime_logging_ready ...; then status=$?` 也会丢失实际状态。
   - 独立复现：source 脚本后调用 `runtime_logging_ready 1` 和不存在的 PID `999999`，两次都返回 0，`RUNTIME_ENV_ERROR` 分别说明缺少环境和 PID 不可读。
   - 影响：新安装中 listener 缺少 JSON trace 时，脚本错误打印“already has JSON trace logging”、跳过带 `yes` 的重启流程，最后才在兼容性检查失败；不可读环境本应保证“不停止进程”，修复函数后仍会被调用处的 `!` 误分类。应在条件语句内保存命令状态，并在调用方使用非取反的 `if/else` 保存失败码。为两种状态各加 installer 测试。

2. **[P0] 兼容性检查窗口会丢掉当前 wait 的用户或 Manager 输入。**
   - 位置：`multi_agent_manager/cli.py:882-884`、`multi_agent_manager/wait_runtime.py:117-144`、`612-628`。
   - 触发：`wait_unified()` 先执行每次都运行的 `wait_compatibility()`；随后 `TraceMessages` 才以 EOF 作为起点打开 trace。此窗口内到达的同一当前 turn 的 `turn/steer` 或 native `turn/start` 已在日志中，初次 tail 会永久忽略，而 App Server 生命周期订阅不订阅这两种请求。
   - 独立复现：向临时 JSON trace 预写带当前 `turn.id` 的有效 `turn/steer` span 后构造 `TraceMessages`，`poll()` 返回 `[]`。本机一次真实 compatibility check 耗时约 1.4 秒，因此窗口不是理论上的瞬间。
   - 影响：调用已经开始的 `mam wait` 可错过用户 steer 或 Manager 输入，继续等待，违反“消息解除对应当前等待／不能一小时静默”的目标。应在兼容性检查前记录本次调用的 trace 文件 offset/时间边界，检查完成后只扫描该边界之后、精确匹配当前 turn 的 span；该边界只在内存中使用，不需要 cursor、ack 或历史重放。补一个输入恰好发生在 compatibility gate 内的回归测试。

3. **[P1] 已确认 listener 的 TERM 不能证明新 `.bashrc` 环境会生效，安装文档的自动重启承诺缺少可行路径。**
   - 位置：`scripts/install.sh:377-404`，`docs/install.md` 的“重启后”段落。
   - 证据：本机实际树为 `node /usr/local/bin/codex … app-server`（PID 4126604）→ native listener（PID 4126625）。npm wrapper 的 `/usr/local/lib/node_modules/@openai/codex/bin/codex.js:231-244` 只把已有 `process.env` 复制给子进程，`274-295` 表明子进程退出时 wrapper 自身退出，不会重新读取 `.bashrc` 或自行 respawn。
   - 影响：在原 listener 缺少 trace 环境的真实新装场景，写入 `.bashrc` 后只 TERM 子进程并不能使旧父进程获得新 export；外层 App 是否以读取 `.bashrc` 的方式重启也未验证。修复第 1 项后，脚本很可能在 20 秒内以“replacement listener appeared without…”失败，而文档目前表述为可完成的自动流程。需要先验证外层 App 的环境传播和 replacement 路径；若无法做到，安装器和文档应明确以不杀进程的非零结果收尾，而不是承诺自动生效。

4. **[P2] 初始 trace 连接没有对晚写的陈旧行做时间过滤。**
   - 位置：`multi_agent_manager/wait_runtime.py:124-144`、`212-234`。
   - 触发：初次打开使用 EOF，但 `_require_new_timestamp` 为 false；如果旧 wait 的同一 active turn span 因缓冲/延迟在新 wait 打开后才追加，代码接受它。
   - 独立复现：先构造 `TraceMessages`，再追加时间戳早一分钟、同一 turn 的 `turn/steer` 行，`poll()` 返回该信号。
   - 影响：旧 wait 的消息可解除同一 turn 后续 wait，违背 stale-wait 隔离。第 2 项引入本次调用边界时应同时在初始增量行上过滤早于边界的时间戳，并保留现有 request/turn 去重。

## 已验证的证据

- `.venv/bin/python -B -m unittest discover -s tests -v`：84 tests passed（26.8s），包括角色/责任矩阵、review delegation、状态即时返回、必需输出字段、取消、超时、断线和 trace rotation。
- `bash -n scripts/install.sh` 与 `python -m multi_agent_manager.cli wait --help` 均成功。
- 对当前真实 control socket 运行 `python -m multi_agent_manager.wait_compat` 成功；它验证 live control socket、JSON trace、隔离 server 的一般事件及 `turn.id` 映射，未启动真实模型 turn。
- 以本审查任务绑定的 `CODEX_THREAD_ID` 执行真实 `mam wait` 空集路径，返回 `{"status":"empty","reason":"empty","message":"no active subagents or unarchived jobs",...}`，未创建等待登记。

真实用户消息和 native Manager `send_input` 的端到端 smoke 仍由 Manager/运行时 owner 进行；上述 compatibility PASS 和单元测试不构成该路径的验收证据。因此当前不建议最终接受。
