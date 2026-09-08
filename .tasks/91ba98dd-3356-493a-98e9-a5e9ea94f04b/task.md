# 进程与 App Server 只读查询模块

执行者：待绑定（gpt-5.6-terra max）。任务 UUID：91ba98dd-3356-493a-98e9-a5e9ea94f04b。workspace：/mnt/public/xcj/Projects/workspace/91ba98dd-3356-493a-98e9-a5e9ea94f04b，代码 worktree 为其下 agent-workflow；分支 task/91ba98dd-3356-493a-98e9-a5e9ea94f04b；目标 main。

## 范围

只编写 scripts/job_runtime.py 与 tests/test_job_runtime.py；不编辑核心 CLI、存储、公共 docs。标准库实现，无第三方包、守护进程、自动唤醒或状态 JSON 中转。目标模块约 180–280 行，必要测试约 100–180 行，规模偏离先告知 Manager。

## 对外契约

probe_process(host: str, pid: int, identity: dict | None = None) -> dict，返回 status=running/stopped/unknown, identity, checked_at, error。identity 含 host boot_id 和 /proc start_ticks，供主进程 PID 复用、重启判断；zombie 视 stopped。首次登记目标进程不存在应让核心明确拒绝；核对已登记身份不再存在则 stopped。无法访问/SSH失败为unknown，不冒充停止。SSH 调用仅使用固定程序和受控 PID 参数，host 不许作为shell/ssh选项注入；不能靠用户进程名查找。

probe_agents(agent_ids: list[str], socket_path: str | None = None) -> dict[str, dict]，返回每个 id 的 status=active/idle/notLoaded/systemError/unknown, checked_at, error。连接当前 App Server，经 initialize/initialized、thread/read(includeTurns=false) 查询，不 resume/start/interrupt 任何真实线程。复用一次连接批量查询；有超时且区分失败。

## 已核对环境

本机 codex app-server 0.153.4，Unix socket /root/.codex/app-server-control/app-server-control.sock。直接 AF_UNIX + WebSocket HTTP Upgrade 已实测：本线程 01a0802d-6af9-7a22-859a-ed7786527390 返回active、Lovelace 01a080d7-7a03-76e0-8731-794563d333d5 返回idle。codex app-server proxy 初次probe等initialize超时，避免依赖其未验证的管线；stdlib实现WebSocket最小子集或先查清proxy行为均可，不能另起server冒充当前状态。官方 https://learn.chatgpt.com/docs/app-server 。

## 验证

临时真实本地和 ssh wuwen-1 进程：running→退出→stopped、多个进程、PID身份不匹配、SSH不可达unknown、zombie；仅终止自己测试创建的进程。App Server 真正只读查询本线程和自己线程，并用socket fixture覆盖协议分帧/ping/错误/超时等必要路径。真实查询用现有server，不创建额外agent/工作区。测试后删除产物。

初始化阶段workspace由Manager先登记建立；工具可用后用其发布报告和归档。不新增外部业务库或GPU任务。

## 共同交付约定

按 main 上发布的本任务和 docs/task-management-design.zh-CN.md 实施。报告写回稳定管理库本任务目录 report.md，首行 task_revision: <所依据任务的完整 commit>，随后写完成/未完成、workspace、各库完整交付 commit、验证结论与成果位置。工具可用后通过 CLI 发布；代码只在自己的 worktree 提交。

先读管理库 AGENTS.md，跨库先读目标库 AGENTS.md 及对应规范。追加要求只以 Manager 发布后的任务文件为准。自身测试产生的文件及进程自行清理，保留待 Manager 归档的工作区。无需 GPU，不修改现用训练/评测环境和进程。没有常驻服务、自动唤醒、额外权限系统、环境 provenance 或旧 CLI 兼容层。
