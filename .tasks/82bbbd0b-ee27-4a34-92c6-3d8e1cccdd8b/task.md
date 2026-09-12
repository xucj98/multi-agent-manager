# C1 nvidia-smi/nvitop GPU进程不可见的只读诊断
# C1 GPU 进程不可见：只读诊断

## 目标
解释用户在 wuwen-4090-1 运行 nvidia-smi 看不到评估进程、nvitop 对显存占用 PID 显示 No Such Process / N/A 的原因。基于当前主机实测，区分同一容器内评估进程的 host/container PID 差异、其他隔离环境的占用，以及采样瞬态或工具行为。不得仅凭 /proc 不可见就认定是他人进程。

## 范围与约束
- 只读 SSH 诊断，遵循 README 与 .local/README；无需代码 worktree（不修改仓库）。证据写入本 TASK-ID workspace。
- 不停止/重启进程、服务、GPU，不修改 namespace、环境、软件包、评估 runtime，不新启评估，不读取敏感配置和 /proc/*/fd/0。
- 用户截图在 /root/.codex/attachments/f80e02cd-fae4-4581-92d1-0ad5eeb5fd64/codex-clipboard-2b8b0e2d-bb59-485c-8af5-2469d1633edf.png。
- 预期 C1 hostname is-ddfwxekq6usner7v-devmachine-0。当前原评估 owner TASK-ID e6908de7-4b02-465a-987b-a19eba7a315a。
- 约 00:50 CST 启动器 PID 2130358,2134661,2160494,2179059,2229745,2309480,2380811 对应 GPU1-7。以当前实测为准。
- 原 runtime /mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-renderer-r3。结果 /mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910。

## 验证与交付
1. 验证 SSH 身份、hostname、时间、PID namespace 与 /proc 挂载；读取自有评估启动器及 worker 的 /proc/PID/status NSpid 等必要字段。
2. 获取当前 NVML/nvidia-smi GPU 显存、compute/graphics PID；选择已知本任务 worker 对比，尽可能证明 host PID 与 namespace PID 对应，无法映射须明确边界。禁止推测性一一匹配。
3. 读取本地已安装 nvitop 相关源代码/版本（或官方源）解释 No Such Process 的生成条件，区分显示限制和作业退出。
4. 用真实评估进程树、少量已写 episode diagnostics 的时间/计数，确认评估是否仍在推进。避免输出巨大 JSON。
5. 提供用户可直接使用的简短只读命令查看自己评估进程和近期进展，报告区分已验证事实/推断/未确定项。
6. 写 report.md 并 mam task publish --file report；返回 CODEX_THREAD_ID 以便绑定。交付后结束 turn，由 MAM 唤醒 Manager。
