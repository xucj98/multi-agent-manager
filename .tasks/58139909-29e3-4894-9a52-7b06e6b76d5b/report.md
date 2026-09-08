task_revision: bbe93515e22083e624a1d7ab28a04c129a7e9b0b

审阅结论：通过；未发现需要修改的代码或最终文档问题。

固定依据：
- 代码 commit：fa79410c72469974f6462f12adf2467eb9b5b744
- 最终 AGENTS/README commit：d8a251d592512e76028f4d3fe6b1b435b916a04e
- 安装与设计说明 commit：043861a3f810b719f6b7001bbd5a9d22bb2bebc6
- workspace：/mnt/public/xcj/Projects/workspace/58139909-29e3-4894-9a52-7b06e6b76d5b/multi-agent-manager

已有代码验证（本轮不重复）：
- 固定 diff 将 `job`、`workspace` 提升为顶层命令组，保留原参数、状态语义、`task status/archive` 内部处理和顶层 `--root` 位置；未引入依赖。
- 私有新 `mam` 已从 `/tmp` 验证三组帮助、默认根、`--root` 分流和已登记 worktree 的复用；旧 `mam task job`、`mam task workspace` 均以退出码 2 拒绝。
- `.venv/bin/python -B -m unittest discover -s tests -v` 已通过 22 项。本轮按更新要求未重跑。

最终文档增量审阅：
- AGENTS 的五个相对链接均指向 README 现有章节，README 的安装链接和保留的安装、设计说明文件均存在；设计说明中的 App Server 外部链接可访问。
- 从 prompt 仅取得 task ID 时，AGENTS 将执行者导向“执行与交付”；README 明确先以 `mam task status <uuid>` 获取登记的 workspace 与各库 worktree 路径，再以 `mam task show <uuid>` 获取已发布要求和版本。设计说明分别确认 `status` 返回 workspace、`show` 返回已发布内容，职责无歧义。
- 最终文档一致使用 `mam task`、`mam workspace`、`mam job`，未保留旧嵌套入口；统一从 MAM 仓库启动 agent、Manager 自己无需 task、任务正文不重复自身 UUID/workspace、超过一小时登记 job 的规则均完整且无重复冲突。
- 已确认最终发布任务正文不包含本任务自身 UUID 或 workspace 路径。

清理：review worktree 无未提交改动，未残留私有 editable `mam --help` 产生的 `multi_agent_manager/__pycache__`；保留 `.venv` 和 worktree 待 Manager 归档。

具体问题：无。
未完成项：无。
