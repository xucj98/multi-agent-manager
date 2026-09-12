# 最终集成复核：BLOCK

审阅候选：a05aff674d33c362c00fdc510d5a97c7b166fe4a（runtime 23f9024 / 9ee6300、installer 8ad4220 / fa530a0、Manager 文档）。

## 阻断问题：安装器会删除未标记的用户 shell 配置

scripts/install.sh 的 update_bashrc() 会对 MAM trace marker 外的每一行，按文本精确过滤：

    export RUST_LOG="off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info"
    export LOG_FORMAT=json

这不是只替换一个已知、带 MAM marker 的 installer-owned block。隔离复现使用临时 HOME 和未带任何 MAM marker 的 .bashrc：

    if [[ "$USER_TOOL_TRACE" == 1 ]]; then
    export RUST_LOG="off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info"
    export LOG_FORMAT=json
    fi

执行 source scripts/install.sh; update_bashrc 后，两个用户行被删除，条件块变为空块，设置被移动为全局 MAM block。命令返回 0 并创建 backup，因此 backup 不能补偿安装器没有保留无关配置这一事实。

这违反安装契约中“保留无关内容、只移除已知 installer-owned obsolete trace block”，且发生在 compatibility 验证或任何 restart 确认之前。应只替换精确、完整、带 marker 的已知 MAM block（如需支持无 marker 的历史格式，也必须能以完整且唯一的 installer-owned block 识别），并新增上述未标记用户条件配置的回归。

## 已完成的复核

- 完整 CPU suite：.venv/bin/python -B -m unittest discover -s tests -q，187 passed，73.988s。
- bash -n scripts/install.sh、Python 编译检查、git diff --check 通过。
- 已复核 wait record 的 per-agent 锁覆盖最终 wait 检查、attempt 持久化和 turn/start；现有 coexistence/race/no-duplicate 测试通过。
- 已复核 caller-runtime daemon bootstrap 以 -I -S 和解析后的调用方包目录隔离 MAM_ROOT / PYTHONPATH shadow；CPU source-isolation 回归包含在全量套件中。
- README、AGENTS、设计文档对“默认结束 turn，mam wait 可选”的表述一致。
- 未运行真实模型/liveprobe，未全局安装，未启动、停止或修改生产 App Server/service/GPU。

审阅 worktree 已删除非 .venv 的 __pycache__，无实现改动。因上述数据所有权问题，当前候选不应批准安装。
