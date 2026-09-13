# 只读核查Codex原生v2直达投递：本机协议、工具宿主与可用接口

用户希望 MAM 在不经 root 模型 turn 的情况下直接续派原生 v2 child，或复用 collaboration.followup_task。你以 gpt-5.6-terra/max 负责本机具体版本技术事实调查；Manager独立调查官方资料并裁决方案。先读AGENTS/README/.local，本任务只读，不开发新产品代码，自己的调查文件放本workspace并最终publish report。

已知本机 codex-cli 0.154.0，App Server 对真实原生 child 的 turn/start 明确返回 direct app-server input is not allowed for multi-agent v2 sub-agents；root原生collaboration.followup_task可以成功。MAM 3f2738a补的是转交root，不是直接投递，真实fixture已完整验证。之前生成的app-server实验schema未看到公开subagent send-input RPC，但需要进一步核实工具宿主/Code Mode/进程版本，不能把schema缺项直接说成所有方法不存在。不要复做同一拒绝模型测试、不要新建线程。

查本机可用的 Codex binary/npm package、实际 app-server executable/argv 与版本、生成协议schema、可读源码/静态实现线索，寻找 collaboration.followup_task / send_subagent_input / native multi-agent v2 的真实路由：是否是外部可调用公开 RPC、进程内工具、Code Mode host 转发、云端 Responses multi-agent orchestration。区分当前工具说明的 canonical agent name 与 UUID。记录文件/版本/hash/具体字段，避免仅凭字符串推测确认可用。

可以在临时owned目录调用 --help/生成schema、只读control socket查询；不得对生产child发送测试输入、turn/start/steer/resume副作用、启动另一个server接管同一thread、改CODEX DB/parent/source/feature、调试注入/伪造caller或进程内部权限。不要输出凭据、authorization headers、完整环境或日志中的prompts。仅从允许的env项读socket/endpoint/launch信息，其他敏感项不展示。若找到有文档/实现依据的候选真实接口，给Manager精确调用合同和最小隔离验证方案，root再安排实际消息测试。

工具是本轮模型专有capability不必然是MCP公共函数；Cloud Agents sessions/subagents API不能仅因同名就用于本地Codex thread。重点寻找不消耗Manager模型turn且保留既有native child与workspace的路径；CLI exec resume、非原生普通thread等仅做源码层可行性/代价说明，别实际接管已有agent。

你无需web调查，官方文档由Manager负责（若确需使用OpenAI Docs技能遵守官方来源范围）。交付简明事实表：候选入口、是否实际暴露、身份条件、是否会调用parent模型、能否保持Windows侧边child关系、证据与未知；没有证据的不可写“已支持”。调查完成正常结束，不轮询。最迟拿到schema/本机实现层核心事实即先消息给Manager，避免无限扫描二进制/日志。
