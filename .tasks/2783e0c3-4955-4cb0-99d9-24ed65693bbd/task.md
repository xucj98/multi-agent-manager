# 目标
将 /mnt/public/xcj/table-1000 重新 clone 到 /mnt/public/xcj/Projects/table-1000/table-1000，迁移运行所需资产，为环境实施者提供准确清单。
# 范围与要求
先阅读 MAM AGENTS.md、README 核心原则/执行与交付、.local/README.md；检查源 repo 的 AGENTS.md、Git 状态、remote、分支、未提交工作和资产布局。通过真实 git clone 建立新 repo，保留可用 origin；不要修改、清理或覆盖源 repo。明确源未提交文件如何保留，不能静默丢失。资产复制到项目内稳定共享位置，由 worktree 软链接引用，避免重复复制；记录来源、大小、复制验证。不复制旧 venv 当作新环境。
本任务为首次仓库引入，允许先创建 canonical clone；需要修改 tracked 文件时仍建立独立 worktree。与环境实施 agent 协商共享资产位置、canonical branch/base；环境代码交由对方完成，不竞争修改。请尽快向 manager 报告 clone 可用路径/base 和资产概况。
# 交付验收
提供 clone remote/commit、源 dirty 状态处理、资产清单及完整性检查、后续风险；遵循 mam report 发布协议，保留验收材料。不得启动正式训练或数据生成。不要自行派发下级 agent。

# Review 裁决补充
迁移 review bd0a1f84-faa8-4823-8ccd-94c659e36a6a 通过；接受其 P3：旧 outputs/ 含不可再生的人类研究标注等历史产物，不能一概称可再生缓存。请将约13M outputs 完整备份到本任务 migration-backup 下独立 historical-outputs/（不加入共享资产、不建立默认 worktree 链接），保持源不变、目标仅当前用户可访问（目录0700/文件0600），若存在 SQLite 使用一致性备份方式或确认无人写入并做一致性验证。不要打印文件内容或 token。记录总体哈希/文件数、恢复方式，修正文档和报告分类并重新发布。
