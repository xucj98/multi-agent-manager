# MAM job入口与操作文档调整统筹
# MAM job 入口与操作文档调整

Manager任务，workspace为Projects/workspace/4414f50e-b290-4bd1-9362-2c147774f542。用户要求将mam task job简化成mam job，README安装说明迁至docs/install.md，AGENTS明确预计运行超过一小时的程序（正式数据生成、训练、评估等）使用mam job add登记，通常的短smoke无需登记。--root仍用于覆盖管理资料根目录，默认本集群路径，日常无需指定。

Manager亲自修改AGENTS/README/install文档，保留现有未提交的mam task show补全；代码修改和独立review委派gpt-5.6-terra max。文档简洁、分工清楚，不修改历史设计文档与已发布任务。实施者只修改CLI及相应测试，不扩展进程机制，不保留旧命令别名。空白review使用独立workspace，验收代码和文档；通过后Manager安装main已提交版本，核验系统命令并归档本轮workspace。无需GPU、远端安装或实验操作。
