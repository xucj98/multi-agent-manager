# 接口与平台核对（实施开始）

- 基线 `330252072cb3c2a834a69a9d63cd1e34627668fa` 只有 `wait_compat.py`/`wait_runtime.py`，没有 `wake_runtime.py`；运行时任务的当前 worktree 也尚未出现该模块。因此安装器暂时没有可调用的服务生命周期接口。
- 请运行时任务明确并提交约定的 `start_service(config, manager=None)`、`stop_service(config)`、`service_status(config)`，包括返回值、失败异常、每项目状态/日志/PID 文件位置、以及 Manager binding 的持久化与恢复语义。安装器会只调用这些接口或 `mam service`，不会从安装 shell 读取 `CODEX_THREAD_ID`。
- 本机有 `systemctl` 二进制，但 PID 1 不是 systemd，`systemctl --user` 和 system scope 均离线；安装不能依赖 user/system systemd。请运行时接口支持在此环境中可独立于 shell/agent turn 运行的单项目生命周期实现，或给出其稳定 CLI 合同。

我将按上述既定合同实现安装、兼容检测、文档和测试；在接口落地前，避免臆造 runtime 数据格式或持久化语义。
