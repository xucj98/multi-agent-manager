# Manager 验收：当前 v2 直达投递接口核查

接受修订报告 df302c45a0cf63bd2ef7dce4a34c534f59a5046f。Manager 已独立阅读匹配 rust-v0.154.0 的 thread_input、queue add/start、turn inject_items、followup_task/message_tool、agent_resolver、wait handler 和 Code Mode proto，并复核官方文档。

当前结论限定为本机版本和已暴露接口：没有找到 MAM 可外部调用、保留既有 native v2 child、并在其结束 turn 后直接触发它的新公开入口。既有真实 fixture 已证明直接 turn/start 被拒绝以及 root 原生 followup 接续可行；本调查没有重跑 fixture。

初版报告有三处过强表述，已要求作者更正并复核：thread/resume 的加载语义不等于直接输入；followup 的非 root 目标不等于仅直接 parent 可调用；预先挂起在真实 wait 工具中属于同 turn 接续候选，不能因没有新 turn 语义就排除。

官方 Responses Multi-agent 文档明确将六个 collaboration 动作描述为 hosted actions，应用端不应执行 multi_agent_call 或提交其输出；其工具返回流也不能据此解释为外部 followup 调用 API。该官方宿主语义与本机进程内工具审计分别构成证据，不假定二者完全是同一个实现。

- https://developers.openai.com/api/docs/guides/responses-multi-agent
- https://learn.chatgpt.com/docs/app-server
- https://learn.chatgpt.com/docs/codex-sdk

普通持久 thread 的 direct turn/start 已有既往真实验收，是可用于另一种执行者组织的路线；将现有任务 rebind 给该类线程可以保留 MAM workspace/job，但不能承诺保留原生 sidebar child 关系。没有进行此迁移。

native v2 的 mam wait 预挂起、长时间工具结果接续与断线恢复尚未专项验证。它不是已结束 child 的直接唤醒 API，不能作为已修复宣告，也不能声称已消除轮询账单。

生产安装任务 a0c09804 继续保持已记录的暂停状态；没有执行新的安装或 daemon/App Server 切换。本次仅验收调查并保留最小证据。后续原生外部控制入口如需改造，应作为明确的 Codex 接口扩展独立设计，而非伪造工具调用或改写 parent 元数据。
