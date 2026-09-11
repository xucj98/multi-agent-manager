# Manager长对话mam wait实机失败

MAM main c84dd3d，已实际pipx安装，109测试和live compatibility PASS，subagent真实message唤醒PASS。Manager在根目录运行mam wait，约数秒返回status/error reason/error message="App Server request thread/resume timed out" agent01a081fe-d6c2-74f2-a73d-68584e9d915b。这是很长的Manager对话，不能假设小agent测试代表它。

读MAM入口，以本task从main c84dd3d创建独立worktree。定位真实长thread订阅超时首因：是否返回历史过大/服务处理耗时/每消息读写期限/事件消费。可读现有.local/hook-probe及App Server本地源码/schema，需OpenAI技能按要求读。不得重启生产服务，不给Manager线程发消息，不创建真实模型turn，不泄露消息正文。只读订阅可能有resume副作用，禁止覆盖thread配置。优先现有public subscribe/省略历史能力或合理明确的订阅处理，而非盲目增加所有timeout/frame cap。确定最小改动与回归，保留无参wait/自动责任/1h/即时pending/消息精确匹配，不增加UI参数。

写scope MAM runtime/job_runtime及必要定向tests；文档非必要不改。做真实只读长thread订阅验证和自身可用wait检查，但不要冒充Manager身份登记wait。报告workspace/commit/根因/实测耗时与局限；发布report，清理短探针。实施gpt5.6-terra max，不创建subagent。后续Manager自行验收真实mam wait。
