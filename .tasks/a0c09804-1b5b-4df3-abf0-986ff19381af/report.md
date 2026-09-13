# 暂停中的集成与安装记录

生产更新按最新用户方向暂停，未完成生产 daemon 替换。

已完成的集成：

- 已验收 source `3f2738abcfc9cbe50b25222562fc58b2bac0a7ff` 以 compare-and-swap fast-forward 纳入 `main`。
- 已以 merge `c7533f97bd1c8594ecfaea8e73aa8c16917dbf04` 纳入 `project/state-vla`；随后并发发布使项目 HEAD 前进，但 source 仍为祖先。
- 安装 worktree 为 `workspace/a0c09804-1b5b-4df3-abf0-986ff19381af/multi-agent-manager`，精确 HEAD `3f2738abcfc9cbe50b25222562fc58b2bac0a7ff`。
- 原生 v2 fixture 汇总证据 `b49a5b40-1d18-40e6-bc28-c5c57dc011f3/native-v2-fallback-evidence.json` 已核验 SHA-256：`b87e37cbb0214f53f447f23d13c297863fdf14d753869756c895aead699858bf`，包含 14 项 receipts；未重跑该 fixture。

标准 installer 已实际执行到暂停边界：215 个 checkout unit tests 通过；pipx 已从本 task worktree 更新包；App Server trace compatibility 和无模型未知-ID API compatibility 均通过，且 App Server 没有重启。installer 随后启动了 isolated ordinary persistent-thread liveprobe。

收到暂停指令时，外层 installer 被安全暂停，允许其 fixture 子进程自行退出和清理；之后以 pending SIGTERM + SIGCONT 结束 outer installer，退出码为 `143`，其临时目录已清理。暂停发生在 fixture 子进程退出、外层 installer 验证 evidence 之前，因此不把六-turn liveprobe 写为安装 gate PASS。也没有运行 `start_project_service`。

生产 daemon 未被 stop/start：PID 仍为 `735869`，启动于 `2026-09-13 01:22:14`，Manager binding 仍为 `01a09657-e0f3-7352-b726-aba5bbd5d498`，service 保持健康。pipx 磁盘包的 `wake_runtime.py` 已与 source 一致（SHA-256 `c926e9d9d9d916ad80bbb37219be8e26f52f0700fe6a88171669390691f55de2`），但旧常驻 PID 未切换，不能称 fallback 已在生产 daemon 生效。

installer 已按标准行为更新受控 `/root/.bashrc` 的 MAM trace/PATH blocks，并保留 transcript 所列 backup；没有重启 App Server，也没有修改 Codex DB/features。用户已有的 primary dirt 与其他 task/report 草稿未 stash、reset 或覆盖。

证据位于 `.tasks/a0c09804-1b5b-4df3-abf0-986ff19381af/evidence/`：`pause-state.md`（SHA-256 `73ddb37fe962763924e8838b537b400a45a89c72d107967738e5b967d88e0dc4`）、完整 `install-transcript.log`、installer exit record 与前态/merge snapshots。

native-v2 direct `turn/start` 没有被恢复；现有 source 只对精确已知拒绝生成 Manager `manager_native_followup`，由 parent-native `collaboration.followup_task` 协调。后续等待 Manager 对直达方案的裁决。
