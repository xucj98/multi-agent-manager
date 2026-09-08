# MAM迁移与文档精简统筹

Manager：01a0802d-6af9-7a22-859a-ed7786527390。任务UUID 6cef08d3-c6c2-432e-808b-7edd7c6cfb1b，workspace为Projects/workspace/同UUID。

用户已批准名称Multi-Agent Manager（MAM），将管理仓库从Projects/agent-workflow迁到Projects/multi-agent-manager，更新操作文档并通过pipx在本机安装mam。所有agent、管理命令和代码修改都在本机；wuwen-1仅通过SSH运行/查询GPU作业，不安装MAM。上一轮实施与验收subagent和workspace已全部收尾。

Manager亲自修订AGENTS和README；具体打包/CLI实现及独立review交给gpt-5.6-terra max。AGENTS只保留协作规则，README保留安装和最短操作流程，完整参数由CLI帮助提供。用户追加：docs中的设计文档保持原样，AGENTS不要求阅读它。业务库AGENTS已剔除集中管理规则，本轮无须重复修改。

实施任务5896e59c-e3e8-4043-b6b6-ba6e81f3a7db在自己的worktree准备支持新名称的Python包/命令与环境入口。Manager集成后，使用迁移前已发布CLI归档该实施worktree及分支；确认管理库无linked worktree再移动稳定目录。迁移不创建长期旧路径alias或兼容层；历史已归档任务中的旧路径按历史保存。通过pipx普通安装已提交代码，避免editable安装跟随共享checkout草稿变化。原有.tasks及.local/tasks保留。

完成标准：mam task list/status等现有接口可从任意目录运行；本机pipx安装入口位于/root/.local/bin；独立工作区创建和任务/报告发布、job查询、归档仍通过；空白执行者从最终简短文档完成实际闭环并审阅清晰/简洁/无冲突；实现测试通过；本轮临时产物和workspace及时归档。正式GPU实验及其结果不动。失败问题按任务要求迭代，追加要求先写任务并发布。
