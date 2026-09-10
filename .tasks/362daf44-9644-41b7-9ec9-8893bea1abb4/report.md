task_revision: 3d8c0c6e4bf4cecd74499c345958a0197d00fa57

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
