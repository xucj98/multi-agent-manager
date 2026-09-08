# 本集群协作入口与任务文档

负责人：Manager。用户指定此项由 Manager 亲自实施。

目标：维护 agent-workflow/AGENTS.md、README.md 和四库 AGENTS.md，说明本机与 wuwen-1 共享文件系统，按任务阅读各库规范，统一工作记录，落实任务说明、结果简报、独立 review 与归档职责。

四库文档 workspace：`/mnt/public/xcj/Projects/workspace/workflow-manager-docs-20260908`。管理仓库为新建原仓库，其文档直接在本仓库维护。只改文档，不安装环境或修改模型与运行代码。

当前追加要求：所有 agent 先读任务说明；变更要求先写任务文件；简报包含完成情况、workspace、worktree commit 与验证结果；review 有独立说明与简报；smoke/temp由执行者处理，归档仅移除workspace并保留资料。

验证：链接存在、文本简洁清楚、路径与编号无歧义。由首次接触项目的空白 agent 审阅，Manager 亲自修正后复核。四库改动合入各自当前开发分支，临时worktree在最终验收后归档。
