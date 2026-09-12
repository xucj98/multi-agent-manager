# 审计清理 .local 和历史临时探针

## 授权与边界
用户明确授权：交接已完成，可删除交接文档；.local 中无保留价值文件可清理，并要求解释 hook-probe/ui-probe 用途。你负责具体审计和清理。先报 CODEX_THREAD_ID，再读 MAM AGENTS/README/.local/README 与本任务发布要求。通过 mam workspace add 2c4d4a5b-61a7-4f39-9b9b-c0dad5d5479a --repo multi-agent-manager --base main 建独立审计工作树；生产 .local 清理是本任务明确授权目标，不把独立树 .local 当目标。不要开发MAM代码；并行任务在做 rebind。

目标 /mnt/public/xcj/Projects/multi-agent-manager/.local。保留核心 README.md、create_worktree.sh、当前 tasks/service/waits 运行状态和锁。不得删除/移动活跃 task登记、job、workspace、服务队列/日志或唯一实验原始证据。不要改用户 dirty docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md。不要笼统 git add。只读检查可以使用现有代码/CLI和小段必要配置，避免全读凭证/环境或约2GB app-server.log。

## 先审计再清理
先给 Manager 简短清单：每类用途、是否仍被引用/进程持有、可删/需保留及依据、外部配置或系统入口遗留。你可以自行清理已核实的普通历史临时文件；对系统入口或未知唯一证据先报告具体核验结果给 Manager，由 Manager 裁决（不是向用户重复申请）。
- MANAGER_HANDOFF.md、MANAGER_CURRENT.md、handoff-snapshot-20260912 已是已完成交接材料，确认持续有用研究约束已存在发布 task/report/论文台账、当前Manager位于manager.json后删除。不要在 .local 再造一份冗长交接文档替代。
- native-wait*、安装/测试尝试日志、history-migration-20260911、archives 各自判断用途和是否唯一备份。不要按名称批量断言无价值；唯一旧源码patch或无法从git恢复的历史记录倾向保留并简述原因。可清理零字节stderr、已归档smoke临时记录等。
- hook-probe README 说明针对测试线程 01a090a5-928a-7022-a9d7-f4d768fbd896 观测 UserPromptSubmit/PreToolUse/PostToolUse/Stop/Interrupt，原项目 .codex/hooks.json可能仍引用。核验文件只包含此次探针后可按原README清理，仅删该探针配置，不删除用户其他hooks；核对相关watcher没有活跃依赖，不终止生产服务。
- ui-probe 是 Windows App proxy metadata 采集，当前 /usr/local/bin/codex 被临时 wrapper 替代，调用 .local/ui-probe/proxy_tap.py。原入口信息 original-codex-entry.json：symlink ../lib/node_modules/@openai/codex/bin/codex.js。先检查当前 wrapper内容/owner、原目标存在、npm是否升级、实际proxy进程及其记录写法，向Manager报告。恢复原symlink须原子且仅针对确认仍是本探针wrapper的入口；不可覆盖升级后的入口。不能 kill/restart 活跃 App Server 或 proxy，因为用户 Windows 对话在用。恢复入口并不终止已运行的采集代理；决定哪些文件可立即删/哪些需等待连接断开，不能使当前通讯中断。不得读取 /proc/PID/fd/0 抓包。

## 交付
用 report.md 保留一份紧凑清理账：实际删除/保留分类、数量/体积、外部配置/入口恢复结果、尚存依赖及精确路径、hook-probe/ui-probe 的通俗说明、验证service healthy和用户改动未变。必要原始临时凭证不写报告。清理结果经 Manager 验收，不自行归档 task/worktree。发布报告后结束turn，由MAM唤醒。
