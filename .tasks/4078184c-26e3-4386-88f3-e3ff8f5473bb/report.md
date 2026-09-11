# 交付报告

- 完成：`mam job archive` 现在可归档 running、stopped 或 unknown/待核实的已登记 job，不触发进程探测或停止进程；保留原身份、最后观测、归档时间和原因。`mam task archive` 仅在所有 job 已归档后执行，不检查已归档 job 的实际存活。已归档 job 不再触发 `mam wait` 的待办或探测。
- 文档与帮助：同步 README、设计文档和 `task/job archive --help`，保留“归档 / archive”术语与现有命令。
- Workspace：`/mnt/public/xcj/Projects/workspace/4078184c-26e3-4386-88f3-e3ff8f5473bb/multi-agent-manager`
- 交付 commit：`330252072cb3c2a834a69a9d63cd1e34627668fa`（`fix: archive jobs without probing processes`）
- 验证：`.venv/bin/python -B -m unittest discover -s tests -v`，115 项通过；覆盖运行中的本地 sleep 归档后仍存活并清理、SSH 不可达/unknown 无需连接即可归档、未归档 job 阻止 task archive、全部归档后无需进程退出、wait 排除已归档 job。
- 限制：按任务要求，归档只结束 MAM 跟踪；仍在运行的外部进程需由其所有者或外部流程自行结束。
