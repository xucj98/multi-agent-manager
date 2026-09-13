# Codex 原生 multi-agent v2 子 agent：直达投递只读审计

## 结论

在本机的 Codex 0.154.0 中，未发现一个**由 MAM 外部直接调用**、同时能保留既有原生 v2 `ThreadSpawn` child 关系并触发其 turn 的公开入口。App Server 的普通直接输入和 queue 路径均被明确拒绝；`collaboration.followup_task` 是受协作 session/turn 与 `agent_control` 上下文约束的内部 Function 工具，不是 RPC/MCP 接口。因而对于从该上下文之外发起的 MAM 投递，没有已证实的零模型-turn 直达 API。

上游实现支持对既有非 root target 使用该工具，源码并不证明“只有直接 parent 能调用”。本集群已验证的可用转发路径是 root 在自己的 native `collaboration.followup_task` 上下文中执行；该已验证路径会经过 root 的模型工具调用，但不能据此概括所有可能的协作调用上下文。

本次只做了本机版本、生成协议和匹配源码的静态核查；没有向生产 child 投递消息、启动/steer/resume turn、修改 Codex 状态，或启动额外 server。

## 版本与可复核材料

- 本机 `codex --version`：`codex-cli 0.154.0`。运行中的 App Server 使用同一发行包中的 `codex` 可执行文件：`/usr/local/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`，SHA-256 为 `3188814c35471432d4123203e0eb38e5bddc60226e3d7ddf0e59e649ea140022`。
- 当前 Code Mode host 为同包的 `codex-code-mode-host`，SHA-256 为 `0c57be435e73b70d9106c850d751cd259a7f04da958a453d7ef59090d82b70f1`。现有 host 以 stdio pipe 启动，没有可外连的监听地址。
- 对照源码位于工作区 `/mnt/public/xcj/Projects/workspace/7c58c3ac-7425-420c-95b2-63296e0a84eb/upstream-codex-rust-v0.154.0`：tag `rust-v0.154.0`，commit `6b9826e3aa83b1a5947db50f4332cb9c65f1b340`。这是按发布版本匹配的源码审计，不把它表述为二进制可复现构建证明。
- 正常和 experimental App Server schema、TS 绑定保存在同一工作区的 `schema-normal/`、`schema-experimental/`、`ts-experimental/`。
- 报告引用的最小源码/协议副本已保存在与本报告同级的 `evidence/`；版本、来源和运行时二进制哈希见 `evidence/MANIFEST.md`，逐文件校验和见 `evidence/SHA256SUMS`。不保留完整 upstream checkout 或完整 schema 作为交付物。

## 候选入口

| 候选 | 外部可调用性及身份边界 | 对既有 v2 child 的结果 |
| --- | --- | --- |
| App Server `turn/start`、`turn/steer` | 是公开 RPC 的普通线程直接输入面；真实 fixture 已观察到 `turn/start` 返回拒绝。 | 不可作为直达入口。共享策略对 `multi_agent_version == V2` 且 session source 为 `SubAgent(ThreadSpawn)` 返回 `direct app-server input is not allowed for multi-agent v2 sub-agents`。 |
| `thread/resume` | 是公开线程加载/恢复 RPC，不是本轮已证实的直接输入调用。 | 本次证据不表明它单独受同一 gate 拒绝，也不表明它能触发既有 child turn；因此不能把它当成已验证的 delivery 入口。 |
| `thread/queue/add`、`thread/queue/start` | 是公开 experimental RPC。`add` 参数为 `threadId`、`clientUserMessageId`、`input`；`start` 参数为 `threadId`、可选 `queuedSubmissionId`。 | 不可用。`add`、`update` 和 `start` 都在入队/启动前调用同一个 direct-input gate。`list`/`delete` 不创建或启动投递，不能绕过此限制。 |
| `thread/inject_items` | 是公开 experimental RPC，但不是用户消息/启动 turn 的替代接口。 | 不可用。它先经同一 direct-input gate，随后只把已验证的 Responses `ResponseItem` 写入历史，并不启动 turn。 |
| 原生 `collaboration.followup_task` / `send_message` | **不是** App Server RPC、CLI 子命令或普通 MCP 工具；是 Codex core 的 `ToolExecutor<ToolInvocation>`，仅匹配模型 Function payload，并在调用者的协作 session/turn 和 `agent_control` 中解析目标。 | `followup_task` 以 `TriggerTurn` 经 in-process `agent_control` 送给既有非 root child；`send_message` 是 `QueueOnly`。MAM 没有公开外部调用合同。root 转发是已验证路径，但源码不支持“只有直接 parent/只有 root 才能调用”的断言。 |
| 原生 `wait_agent` / MAM 持续等待 | `wait_agent` 是等待 mailbox 活动的模型 Function 工具；MAM 的 `mam wait` 等待已登记事件。 | 它们不向 dormant child 写入新输入，也不启动 turn。若 child 已真实挂起在可持续的 wait 工具中，job 完成可作为该工具结果在同一 turn 中让它接续，原则上不需 root 再投递；本次没有验证 native v2 的工具持续性或断线恢复兼容性，因此这是未证实的事件等待候选，不是已排除路径。 |
| Code Mode host | 精确 gRPC 协议只含 `OpenSession`、`CloseSession`、工具回调、`Execute`、`Wait`、`Terminate` 等 JavaScript cell 生命周期接口。 | 没有 agent-control/send-input RPC。现有 host 是 stdio-only；另起 host 会得到不相关的 session，向现有 pipe 注入也不属于受支持接口。 |
| `codex queue` / 普通 thread | `codex queue` 的 TUI 实现明确向 App Server 发 `thread/queue/add`；普通 thread 的 UUID 不是 native child 的 agent-control 身份。 | CLI 没有额外权限，仍会命中 queue gate。创建/操作普通 thread 不能取得既有 v2 child 的内存 mailbox、canonical path 或 parent-child 关系。 |

## 核心证据

1. `evidence/source/codex-rs/app-server/src/request_processors/thread_input.rs:12-36` 定义共同策略：只有非 v2 或非 `SessionSource::SubAgent(SubAgentSource::ThreadSpawn { .. })` 的线程才可接受 direct input；否则返回上述固定错误。
2. `evidence/source/codex-rs/app-server/src/request_processors/thread_queue_processor.rs:72-89`、`:129-145`、`:181-198` 分别在 `add`、`update`、`start` 前调用 gate；`:280-296` 还区分已加载 v2 child 的固定错误和未加载 spawned child 的错误。这直接排除了“先 queue 后启动”的路径，无需向真实 child 发送测试消息。
3. `evidence/source/codex-rs/app-server/src/request_processors/turn_processor.rs:514-529`、`:1006-1019` 显示 `turn/start` 和 `turn/steer` 在处理输入前调用 gate；`:956-984` 表明 `thread/inject_items` 也先验 direct input，随后调用 `inject_response_items`，没有 turn-start 操作。这里没有把 `thread/resume` 归入此证据。
4. `evidence/protocol/ClientRequest.ts:163` 列出所有 client request（含 `thread/resume`、`turn/*`、`thread/queue/*`、`thread/inject_items`），其中没有 `followup_task`、`send_message`、`send_subagent_input` 或 agent-control method。
5. `evidence/source/codex-rs/core/src/tools/handlers/multi_agents_v2/followup_task.rs:37-55` 与 `evidence/source/codex-rs/core/src/tools/handlers/multi_agents_v2/send_message.rs:37-55` 都把模型 Function invocation 交给 `evidence/source/codex-rs/core/src/tools/handlers/multi_agents_v2/message_tool.rs:68-128`；后者在调用者的 session/turn 中解析 target、确保 agent 已知/已载入，再调用 `session.services.agent_control.send_inter_agent_communication(...)`。对 `TriggerTurn`，它只拒绝 root target（`:75-84`），故代码支持既有非 root target，而不证明仅限直接 parent。
6. `evidence/source/codex-rs/core/src/agent/agent_resolver.rs:8-30` 先把一个实际 UUID 解析为 thread id，否则才在发送者的 session/turn 上下文中通过 `agent_control.resolve_agent_reference(...)` 解析 canonical agent path。因此 canonical task name 不是可由 MAM 独立伪造的通用 RPC 身份。
7. `evidence/source/codex-rs/core/src/tools/handlers/multi_agents_v2/wait.rs:22-123` 将 `wait_agent` 定义为模型 Function 工具，并订阅 input-queue activity 后等待其 outcome。它本身不调用 inter-agent delivery；预先挂起后由活动/工具结果接续的 native v2 可用性仍需隔离 fixture 验证。
8. `evidence/source/codex-rs/code-mode-protocol/src/grpc/codex.code_mode.v1.proto:8-35` 没有 multi-agent 或 send-input service；`evidence/source/codex-rs/cli/src/queue_cmd.rs:29-62` 调用 `tui::run_session_queue_command`，后者在 `evidence/source/codex-rs/tui/src/session_queue_commands.rs:107-121` 发出 `ClientRequest::ThreadQueueAdd`。

## 对 MAM 的含义

当前实现中，把 `unsupported_multi_agent_v2_direct_input` 标为 blocked 并升级给不同的有效 Manager，是与本机运行时边界一致的做法。当前已验证的转发方式是 root 在 native `collaboration.followup_task` 工具上下文中协调；它不是 MAM 可直接复用的外部 API。另一个可设计、但尚未验证的方向是让 child 在真实可持续 wait 工具中预先等待 job 事件并在同一 turn 接续；在 native v2 上是否能跨所需时长和断线恢复，须用隔离 fixture 另行验证。后续版本若新增公开 agent-control RPC，也须在该版本的 schema、权限模型和隔离 fixture 上重新审计。

## 交付与验证

- 代码/配置改动：无；无需 commit。
- 调查工作区：`/mnt/public/xcj/Projects/workspace/7c58c3ac-7425-420c-95b2-63296e0a84eb`。
- 留存证据：`.tasks/7c58c3ac-7425-420c-95b2-63296e0a84eb/evidence/`（最小源码/协议副本及 `MANIFEST.md`、`SHA256SUMS`）。
- 验证：读取本机 CLI 版本和二进制哈希；检查 matching release tag/commit；检查生成 schema、Code Mode proto 及上述 request processor/tool handler 源码；对复制的证据文件生成 SHA-256 清单。按任务限制未做有副作用的 live RPC 验证。
