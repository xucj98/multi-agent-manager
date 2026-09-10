# 目标
将 /mnt/public/xcj/table-1000 重新 clone 到 /mnt/public/xcj/Projects/table-1000/table-1000，迁移运行所需资产，为环境实施者提供准确清单。
# 范围与要求
先阅读 MAM AGENTS.md、README 核心原则/执行与交付、.local/README.md；检查源 repo 的 AGENTS.md、Git 状态、remote、分支、未提交工作和资产布局。通过真实 git clone 建立新 repo，保留可用 origin；不要修改、清理或覆盖源 repo。明确源未提交文件如何保留，不能静默丢失。资产复制到项目内稳定共享位置，由 worktree 软链接引用，避免重复复制；记录来源、大小、复制验证。不复制旧 venv 当作新环境。
本任务为首次仓库引入，允许先创建 canonical clone；需要修改 tracked 文件时仍建立独立 worktree。与环境实施 agent 协商共享资产位置、canonical branch/base；环境代码交由对方完成，不竞争修改。请尽快向 manager 报告 clone 可用路径/base 和资产概况。
# 交付验收
提供 clone remote/commit、源 dirty 状态处理、资产清单及完整性检查、后续风险；遵循 mam report 发布协议，保留验收材料。不得启动正式训练或数据生成。不要自行派发下级 agent。

# Review 裁决补充
迁移 review bd0a1f84-faa8-4823-8ccd-94c659e36a6a 通过；接受其 P3：旧 outputs/ 含不可再生的人类研究标注等历史产物，不能一概称可再生缓存。请将约13M outputs 完整备份到本任务 migration-backup 下独立 historical-outputs/（不加入共享资产、不建立默认 worktree 链接），保持源不变、目标仅当前用户可访问（目录0700/文件0600），若存在 SQLite 使用一致性备份方式或确认无人写入并做一致性验证。不要打印文件内容或 token。记录总体哈希/文件数、恢复方式，修正文档和报告分类并重新发布。

# 用户最新布局要求（覆盖之前路径约定）
主repo不应有业务软链接；PROJECT_ROOT只放 workspace/MAM/repos（保留MAM必要隐藏配置）。环境任务负责将共享资产实体移动到 canonical/.cache 及worktree软链更新；本迁移任务仅负责将备份（含正在补充的历史outputs）收拢 canonical/.local/migration-backup/TASK-ID，不要竞争移动资产。请与environment协调，修正 MANIFEST/report 所有最终路径和分类，验证迁移后完整性。不得保留PROJECT_ROOT/migration-backup业务目录。

# 用户明确授权：统一用户缓存目录
用户已明确同意将 ~/.cache 下现有内容移动到 /mnt/public/xcj/cache，校验后删除旧实体并建立 ~/.cache -> /mnt/public/xcj/cache。同时与 environment 协调，将 table1000 canonical/.local/uv-cache 中已下载的完整包仓库整合到 /mnt/public/xcj/cache/uv，避免两套。请你负责迁移、校验与替换路径，environment负责脚本/local配置。先与其确认停止uv写入窗口；注意MAM review或其他短任务可能用默认uv/pip cache，不覆盖或静默丢失目录冲突。采用分阶段复制/校验/最后切换，冲突内容要保全并报告，不使用危险盲目覆盖。~/.cache 有软链子项须保留语义，记录目录计数、大小、复制校验、最终readlink。保留 /mnt/public/xcj/cache/shared-python（这次创建）以及MAM独立worktree。全局uv目录现在是symlink环境的持久包仓库：不可cache clean/prune或手工删除包。不要展示cache中敏感内容。完成发布报告，写清此前备份依旧存在。
