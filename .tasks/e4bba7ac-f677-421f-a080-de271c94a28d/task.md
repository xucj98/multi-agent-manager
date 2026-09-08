# 管理工具实施统筹与文档

负责人：当前 Manager，线程 01a0802d-6af9-7a22-859a-ed7786527390。任务 UUID：e4bba7ac-f677-421f-a080-de271c94a28d。

用户已确认接口并授权实施。Manager 负责要求发布、分工、集成、各库 AGENTS.md 与管理库README/AGENTS、独立验收和 workspace 收尾；具体代码与代码 review 交给 gpt-5.6-terra max。用户对接口文档的最新编辑将job add及task archive的说明参数统一为 --note，按当前文件实施。

管理仓库发布分支 main，业务库保留已有开发分支。首次工具不可用，允许本轮一次性Git初始化/人工登记；后续 task/report 通过工具publish发布。保留此前未完成成果，不动正在跑的正式训练/评测。当前启动 core/runtime/env_review 三个实施或验收任务；工具就绪后再创建一个空白独立验收任务，基于发布要求和交付commit验证，验收通过再归档执行workspace。

完成标准：CLI及所依赖入口可实际创建/登记/查询/发布/归档；多个真实repo软链环境与本机/远端CPU基础检查；并发发布及删除边界测试；真实进程/App Server查询；空白agent按文档完成闭环；简报保存，工作区与自身临时产物清理。
