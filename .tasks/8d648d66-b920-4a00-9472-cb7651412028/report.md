# 独立复审：统一 mam wait、安装器与 native 输入（未通过）

审查 workspace：/mnt/public/xcj/Projects/workspace/8d648d66-b920-4a00-9472-cb7651412028/multi-agent-manager。

审查分支 HEAD 为 63ca6bd，已合并 main@758d523（包括运行时 60cfd89、安装器 b4382a2 和 native 输入 8539bfe）。未修改实现代码，未重启生产 App Server。

## 阻断项

1. **[P1] native journal 在实际 invocation 边界仍有漏消息窗口。**
   - 位置：multi_agent_manager/cli.py:920-928，multi_agent_manager/wait_runtime.py:292-319、321-328。
   - 触发：CLI 先记录 started_at，但 SessionMessages.from_environment() 还要递归查找 journal、读取候选 header，最后才以 EOF 打开命中的文件。若 native user.text 在 started_at 之后、EOF 打开之前写入，它的时间戳虽属于本次调用，仍被 EOF tail 永久跳过；此时 event stream 尚未连接，也不能补回该事件。
   - 独立复现：在临时当前-session journal 中记录边界后追加一条当前 turn 的 user.text，再调用 from_environment(..., started_at=boundary)，poll() 返回 []。本机当前 journal 可被唯一定位，但这一查询不是原子操作；现有回归测试只覆盖 watcher 已打开后的 compatibility 阶段。
   - 影响：刚开始 mam wait 时的 native Manager 输入仍可能被遗漏，继而静默等待到其它状态变化或一小时超时。应把 journal 边界建立为可覆盖查找/打开阶段的稳定 offset，或从本次时间边界扫描当前 journal；补一条“写入发生在 from_environment 查找期间”的回归测试。不要只把 EOF tail 的建立时间当作调用边界。

2. **[P1] 已确认 TERM 后的任一 relaunch 失败会让 App Server 保持停止。**
   - 位置：scripts/install.sh:1057-1088，文档见 docs/install.md:30-34。
   - 触发：send_term 成功后，wait_for_target_departure、launch_same_style 或 wait_for_replacement 的失败分支只释放 lock 并以非零退出；脚本没有预检全部 launcher 条件，也没有 post-TERM trap/recovery。用户中断脚本也落在同一无恢复区间。
   - 独立复现：用隔离的、满足 discovery 规则的 node wrapper/listener，令 wrapper 在 listener 退出后变得不可执行。安装器确实只 TERM 该 listener，随后报告 launcher 不可运行并返回 1；socket 不存在、原 wrapper 已退出、没有 replacement。这没有接触生产进程。
   - 影响：一次已确认的安装操作可把可用 App Server 变为长期不可用，文档只说明会非零结束，未说明此后的恢复状态。应在 TERM 前预检捕获的 launch plan，并为 TERM 后失败/信号提供受身份约束的恢复或明确、可执行的人工恢复步骤；cleanup 只能针对本次安装器创建并记录身份的 wrapper。

## 已接受问题的复查

- **exit status propagation：已修复。** runtime_logging_ready() 保存 Python 的实际失败码，ensure_runtime_logging() 按 1（环境不匹配）和 2（不可读）分支处理。独立 source 检查在无 trace 环境时返回 1、无效 PID 返回 2；两条 installer 回归测试均通过。
- **compatibility 前 trace 边界：已修复。** trace watcher 在 compatibility probe 前打开并共享给 runtime；回归测试在 probe 内追加当前 turn span，随后被读取。
- **晚写陈旧 trace 行：已修复。** 每个增量行都按本次 started_at 过滤；针对初始 EOF tail 后追加旧 timestamp 的回归测试通过。本机真实 trace 使用微秒 timestamp，未发现秒级舍入问题。
- **.bashrc 环境传播／确定性同式重启：happy path 已得到实证。** 安装器捕获实际 node wrapper 的 argv、cwd、stdio 和环境，只替换两项 trace 变量；隔离重启测试验证重新建立同式 wrapper。本机生产 listener 通过严格 discovery，当前已具备 JSON trace 环境，因此没有重启它。第 2 项仍阻止把失败路径视为安全完成。

## Native 输入、queue 与兼容性证据

- 新 watcher 只保留 turn/message ID；它要求唯一、当前 session journal，缺少 CODEX_HOME／CODEX_SESSION_ID、header 不匹配、rotation、截断或无效 metadata 都会显式报错，不会退化为静默文件读取。
- item 事件同样限定为 caller、当前 active turn、userMessage、本次时间边界，并做 ID 去重；其他 agent、其他 turn 和陈旧 event 不唤醒。
- 以临时 CODEX_HOME 启动隔离 stdio App Server，调用 thread/queue/add（未调用 queue/start、未启动模型 turn）：结果仅有 queuedSubmission 与 thread/queue/changed，session journal 中没有 user-message row。当前 App Server schema 也表明 queue add 不返回 turn，queue start 才产生后续 turn；现有 current-turn 过滤会拒绝该后续 turn。因此没有发现 queue 会错误解除当前 wait。
- wait_compat 仍明确输出 native user-message/native-manager-send **not certified**，docs/install.md:38 也如实说明这一点。它的 PASS 只验证 control socket、trace 和隔离 server 行为，不能替代真实 native smoke；本次 review 不将 native wake 标为已验收。真实 smoke 由 owner 重跑中，未等待或轮询。

## 验证

- bash -n scripts/install.sh：通过。
- .venv/bin/python -B -m unittest discover -s tests -v：**101 tests passed**（27.5s）。
- .venv/bin/python -B -m multi_agent_manager.wait_compat：通过；对生产 control socket 仅做 initialize/trace 读取，输出明确不认证 native wake。
- 生成的本机 App Server protocol schema 与隔离 queue probe 均未创建真实模型 turn；生产 App Server、GPU 作业和用户 session 内容均未修改。
