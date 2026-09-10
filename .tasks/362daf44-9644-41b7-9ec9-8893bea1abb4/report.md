task_revision: 826da63c2f4a7d404645e486795ff971fef12890

增量复验结论：GO。原报告两项阻塞已修复；以下为最终验收结果，后附旧报告仅保留历史。

workspace、最终 commit：
- 复用 `/mnt/public/xcj/Projects/workspace/362daf44-9644-41b7-9ec9-8893bea1abb4/multi-agent-manager`，从原提交快进到 `e6892fe7d9d29be71f03d69a5c32318706207090`，未修改源码或创建新环境。
- 固定源要求 `6da327722bf9e5834aebbd0475d554de6fdc3479`；源 report `7bd9b9f802369bd4f0f6cf96229e648802522787`。已阅读最新发布要求及增量 diff。

验证与结论：
- deadline：每个 target 前检查剩余预算，probe 使用 min(0.5, remaining)。临时 root 登记自己 wuwen-1 短进程的 8 个 remote job，真实 CLI `wait jobs --timeout 0.01` 耗时 0.080 秒，`--timeout 0.75` 耗时 0.820 秒，均返回 timeout，退出后无等待记录；约 0.07 秒 CLI/运行时开销符合最新非硬实时裁定。
- attention：真实本地 sleep 注册后停止，绑定不可用 agent；`job list --attention` 显示 `unknown/待核实`，普通 job list 仍显示 `stopped`。保留六列、完整 UUID，带换行描述清理为物理单行。
- 必要标准库回归 8/8 通过（3.419 秒）：全部 4 个 wait 测试、attention 新增测试、job 筛选/实时状态、job identity/attention/history、task 表头/status 测试。覆盖受控 0.01/0.75 秒预算、取消不杀 job、双等待隔离、empty/unknown/stale 等受影响路径。
- 增量 `git diff --check 1b8f4265 HEAD` 通过。生产代码仅增加预算判断及保留 needs_verification 来源的渲染；指定中文设计文档同步解释行为，无新增框架。
- 正常远端探测可用性及其他已通过验证沿用首轮证据；未重复全套无关测试。当前无阻塞问题，无本次必需未验项。此前 task renderer join/split 简化建议仍为非阻塞建议。
- 临时 root（包含测试 workspace）、本地进程均清理；自建 remote 短进程自然退出且 SSH 回收。使用 PYTHONDONTWRITEBYTECODE=1，保留干净 review worktree 待 Manager 归档。

以下为旧提交 1b8f4265 的历史 NO-GO 报告（依据任务 revision 3d8c0c6e4bf4cecd74499c345958a0197d00fa57），已由上方 GO 结论替代。

完成与未完成：
- 结论：NO-GO。固定交付的等待、列表、详情主体可运行，但以下两项已违反明确验收约定。
- 已验收：自动 `CODEX_THREAD_ID` 与本任务绑定 ID `01a08a39-d99b-79e2-bf72-28b1b1936d73` 一致；本地双等待者隔离，stop 仅 0.059 秒且未终止被监控进程；陈旧等待可重开；empty、timeout、已有 stopped、三类列表表头/物理单行、task list 移除 --json、job status 仅刷新目标均通过。
- 未完成：修复 deadline 与 --attention 待核实呈现，并补相应回归测试后再验收。

workspace、各库交付 commit：
- `/mnt/public/xcj/Projects/workspace/362daf44-9644-41b7-9ec9-8893bea1abb4/multi-agent-manager`
- `multi-agent-manager`：`1b8f4265dde093736dff2e0d77d185d9e640a6a8`（工作树干净）

验证结果与成果位置：
- `.venv/bin/python -B -m unittest discover -s tests -v`：30/30 通过；`git diff --check` 通过。
- 临时 root 的真实 CLI 验收使用自建短 sleep，结束时清理 root、workspace、waiter、进程和 review 产生的 pycache。
- `wuwen-1` 的自建非 GPU 短 sleep：0.5 秒探测 12/12 为 running，最长 0.314 秒、中位 0.279 秒；单 remote wait 最长 0.325 秒，stop 为 0.059 秒且 remote sleep 仍存活。两端 `CLK_TCK` 均为 100。

阻塞问题：
1. P1：`wait_jobs` 只在完整 target 扫描前后检查 deadline（`multi_agent_manager/cli.py:630-640`）。临时 root 向同一 `wuwen-1` 短 sleep 登记 8 个 remote job，执行 `mam wait jobs --timeout 0.01` 返回 timeout 却耗时 1.915 秒。每个 SSH 探测都固定允许 0.5 秒，目标多时超时会按整轮扫描放大，违背“timeout 后返回”。应在每个 target 前检查剩余时间，并把 probe timeout 限制为 `min(0.5, remaining)`。
2. P1：`job_list` 将“已 stopped、agent unknown”的记录放入 `needs_verification`（`cli.py:459-460`），但 `print_job_list` 经 `displayed_job_status` 仍输出 `stopped`（`cli.py:715-735`）。真实 CLI 中，未可用 agent 的 task list 显示 unknown，而 `job list --attention` 同一 job 显示 stopped。指定设计文档要求不确定项显示 `unknown/待核实`，当前文本丢失了待核实区别。renderer 应保留集合来源或显式标记该行。

建议：
- 修复后补“多 remote target 的短 timeout”和“agent unknown + stopped probe 的 attention 文本”两项真实/受控回归测试；无需为此引入 daemon 或连接池。当前 normal wuwen-1 的 0.5 秒可用性已实测通过。
- 生产代码净增约 336 行，略超任务提示；`print_task_list` 目前先 `join("\\t")` 再 `split("\\t")`（`cli.py:705-712`）可直接传元组，属于可删冗余，但不应以压缩行数替代上述行为修复。
