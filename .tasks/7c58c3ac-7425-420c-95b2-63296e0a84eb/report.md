# Codex 原生 multi-agent v2 子 agent：直达投递只读审计

## 结论

在本机的 Codex 0.154.0 中，未发现一个**由 MAM 外部直接调用**、同时能保留既有原生 v2 `ThreadSpawn` child 关系并触发其 turn 的公开入口。App Server 的普通直接输入和 queue 路径均被明确拒绝；`collaboration.followup_task` 虽能保留该关系并触发 child turn，但它是拥有该 child 的 Codex 会话在模型 turn 中执行的内部 Function 工具，不是 RPC/MCP 接口。因此它不能满足“不消耗 Manager 模型 turn”的条件。

本次只做了本机版本、生成协议和匹配源码的静态核查；没有向生产 child 投递消息、启动/steer/resume turn、修改 Codex 状态，或启动额外 server。

## 版本与可复核材料

- 本机 `codex --version`：`codex-cli 0.154.0`。运行中的 App Server 使用同一发行包中的 `codex` 可执行文件：`/usr/local/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`，SHA-256 为 `3188814c35471432d4123203e0eb38e5bddc60226e3d7ddf0e59e649ea140022`。
- 当前 Code Mode host 为同包的 `codex-code-mode-host`，SHA-256 为 `0c57be435e73b70d9106c850d751cd259a7f04da958a453d7ef59090d82b70f1`。现有 host 以 stdio pipe 启动，没有可外连的监听地址。
- 对照源码位于工作区 `/mnt/public/xcj/Projects/workspace/7c58c3ac-7425-420c-95b2-63296e0a84eb/upstream-codex-rust-v0.154.0`：tag `rust-v0.154.0`，commit `6b9826e3aa83b1a5947db50f4332cb9c65f1b340`。这是按发布版本匹配的源码审计，不把它表述为二进制可复现构建证明。
- 正常和 experimental App Server schema、TS 绑定保存在同一工作区的 `schema-normal/`、`schema-experimental/`、`ts-experimental/`。

## 候选入口

| 候选 | 外部可调用性及身份边界 | 对既有 v2 child 的结果 |
| --- | --- | --- |
| App Server `turn/start`、`turn/steer`、`thread/resume` | 是公开 RPC 的普通线程输入面；真实 fixture 已观察到 `turn/start` 返回拒绝。 | 不可作为直达入口。共享策略对 `multi_agent_version == V2` 且 session source 为 `SubAgent(ThreadSpawn)` 返回 `direct app-server input is not allowed for multi-agent v2 sub-agents`。 |
| `thread/queue/add`、`thread/queue/start` | 是公开 experimental RPC。`add` 参数为 `threadId`、`clientUserMessageId`、`input`；`start` 参数为 `threadId`、可选 `queuedSubmissionId`。 | 不可用。`add`、`update` 和 `start` 都在入队/启动前调用同一个 direct-input gate。`list`/`delete` 不创建或启动投递，不能绕过此限制。 |
| `thread/inject_items` | 是公开 experimental RPC，但不是用户消息/启动 turn 的替代接口。 | 不可用。它先经同一 direct-input gate，随后只把已验证的 Responses `ResponseItem` 写入历史，并不启动 turn。 |
| 原生 `collaboration.followup_task` / `send_message` | **不是** App Server RPC、CLI 子命令或普通 MCP 工具；是 Codex core 的 `ToolExecutor<ToolInvocation>`，仅匹配模型 Function payload。 | `followup_task` 以 `TriggerTurn` 送入既有 child 的 in-process `agent_control`，因而是能保留原生关系的路径；但必须由拥有该会话的模型发起工具调用，MAM 无外部调用合同，仍会消耗该 Manager 模型 turn。`send_message` 是 `QueueOnly`，也同样是内部工具。 |
| 原生 `wait_agent` / MAM 持续等待 | `wait_agent` 同样是模型 Function 工具；它等待 mailbox 更新、完成通知、steer 或超时，且不返回消息内容。MAM 的 `mam wait` 只等待 MAM 已登记事件。 | 都没有向 child 写入或启动 child turn 的语义，不能作为 delivery bridge。 |
| Code Mode host | 精确 gRPC 协议只含 `OpenSession`、`CloseSession`、工具回调、`Execute`、`Wait`、`Terminate` 等 JavaScript cell 生命周期接口。 | 没有 agent-control/send-input RPC。现有 host 是 stdio-only；另起 host 会得到不相关的 session，向现有 pipe 注入也不属于受支持接口。 |
| `codex queue` / 普通 thread | `codex queue` 的 TUI 实现明确向 App Server 发 `thread/queue/add`；普通 thread 的 UUID 不是 native child 的 agent-control 身份。 | CLI 没有额外权限，仍会命中 queue gate。创建/操作普通 thread 不能取得既有 v2 child 的内存 mailbox、canonical path 或 parent-child 关系。 |

## 核心证据

1. `codex-rs/app-server/src/request_processors/thread_input.rs:12-36` 定义共同策略：只有非 v2 或非 `SessionSource::SubAgent(SubAgentSource::ThreadSpawn { .. })` 的线程才可接受 direct input；否则返回上述固定错误。
2. `thread_queue_processor.rs:72-89`、`:129-145`、`:181-198` 分别在 `add`、`update`、`start` 前调用 gate；`:280-296` 还区分已加载 v2 child 的固定错误和未加载 spawned child 的错误。这直接排除了“先 queue 后启动”的路径，无需向真实 child 发送测试消息。
3. `turn_processor.rs:956-984` 表明 `thread/inject_items` 也先验 direct input，随后调用 `inject_response_items`，没有 turn-start 操作。
4. experimental 生成的 `ts-experimental/ClientRequest.ts:163` 列出所有 client request（含 `turn/*`、`thread/queue/*`、`thread/inject_items`），其中没有 `followup_task`、`send_message`、`send_subagent_input` 或 agent-control method。
5. `core/src/tools/handlers/multi_agents_v2/followup_task.rs:37-55` 与 `send_message.rs:37-55` 都把模型 Function invocation 交给 `message_tool`；`message_tool.rs:68-120` 解析目标、确保 child 已载入，再调用 `session.services.agent_control.send_inter_agent_communication(...)`。`followup_task` 使用 `TriggerTurn`，`send_message` 使用 `QueueOnly`。
6. `core/src/agent/agent_resolver.rs:8-30` 先把一个实际 UUID 解析为 thread id，否则才在发送者的 session/turn 上下文中通过 `agent_control.resolve_agent_reference(...)` 解析 canonical agent path。因此 canonical task name 不是可由 MAM 独立伪造的通用 RPC 身份。
7. `core/src/tools/handlers/multi_agents_v2/wait.rs` 和 `multi_agents_spec.rs:280-288` 将 `wait_agent` 定义为等待 mailbox 活动的 Function 工具，未调用 inter-agent delivery。它不能把待办送给 child。
8. `code-mode-protocol/src/grpc/codex.code_mode.v1.proto:8-35` 没有 multi-agent 或 send-input service；`cli/src/queue_cmd.rs:29-62` 调用 `tui::run_session_queue_command`，后者在 `tui/src/session_queue_commands.rs:107-121` 发出 `ClientRequest::ThreadQueueAdd`。

## 对 MAM 的含义

当前实现中，把 `unsupported_multi_agent_v2_direct_input` 标为 blocked 并升级给不同的有效 Manager，是与本机运行时边界一致的做法。若必须继续使用原生 child，唯一已证实的触发方式是让其 owning parent 在自己的 native `collaboration.followup_task` 工具上下文中执行；这不是 MAM 可直接复用的零模型-turn API。后续版本若新增公开 agent-control RPC，须在该版本的 schema、权限模型和隔离 fixture 上重新审计后才能改变结论。

## 交付与验证

- 代码/配置改动：无；无需 commit。
- 调查工作区：`/mnt/public/xcj/Projects/workspace/7c58c3ac-7425-420c-95b2-63296e0a84eb`。
- 验证：读取本机 CLI 版本和二进制哈希；检查 matching release tag/commit；检查生成 schema、Code Mode proto 及上述 request processor/tool handler 源码。按任务限制未做有副作用的 live RPC 验证。
