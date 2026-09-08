# 管理工具实施统筹与文档

负责人：当前 Manager，线程 01a0802d-6af9-7a22-859a-ed7786527390。任务 UUID：e4bba7ac-f677-421f-a080-de271c94a28d。

用户已确认接口并授权实施。Manager 负责要求发布、分工、集成、各库 AGENTS.md 与管理库README/AGENTS、独立验收和 workspace 收尾；具体代码与代码 review 交给 gpt-5.6-terra max。用户对接口文档的最新编辑将job add及task archive的说明参数统一为 --note，按当前文件实施。

管理仓库发布分支 main，业务库保留已有开发分支。首次工具不可用，允许本轮一次性Git初始化/人工登记；后续 task/report 通过工具publish发布。保留此前未完成成果，不动正在跑的正式训练/评测。当前启动 core/runtime/env_review 三个实施或验收任务；工具就绪后再创建一个空白独立验收任务，基于发布要求和交付commit验证，验收通过再归档执行workspace。

完成标准：CLI及所依赖入口可实际创建/登记/查询/发布/归档；多个真实repo软链环境与本机/远端CPU基础检查；并发发布及删除边界测试；真实进程/App Server查询；空白agent按文档完成闭环；简报保存，工作区与自身临时产物清理。

用户追加：AGENTS.md 和 README.md 由 Manager 亲自修订，待实现稳定后定稿；必须由空白 subagent 审阅清晰、简洁、无冲突。

独立审阅发现的文档收尾范围：RMBench docs/guidelines/rmbench.md 与 robot-bridge configs/benchmark/unified_sim/README.zh-CN.md、docs/design/unified-sim-real-runtime.md、docs/tutorials/drawer-offline.zh-CN.md、docs/tutorials/rmbench-benchmark-runner.zh-CN.md 仍引用已删除 .local/README.zh-CN.md，Manager 在最终文档修改时修正为现行入口。

用户最新文档分层要求：各业务库 AGENTS.md 不包含集中工作日志路径、.worklogs/.tasks管理路径或“跨库工作前读取目标库AGENTS”的公共流程。这些统一归 agent-workflow/AGENTS.md。各库只保留本库职责、必读文档及开发/实验约定；不得将旧.worklogs路径机械替换成.tasks后继续留在业务库。

用户追加清理：删除 agent-workflow/.worklogs 整个旧日志目录，包括未提交的旧报告；从现行文档移除保留旧日志的说明，新记录统一使用 .tasks。已提交记录可从Git历史读取，无需迁入新目录。

运行边界：所有agent、代码修改和管理CLI均在本机，只有训练、评估或其他GPU作业通过SSH在wuwen-1运行。管理工具从本机查询两端进程，无需在wuwen-1安装。用户正在讨论名称Multi-Agent Manager（MAM）与pipx安装；命名和安装尚未实施。
