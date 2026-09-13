# 暂停状态证据

- 截止本文件写入，已验收 source `3f2738abcfc9cbe50b25222562fc58b2bac0a7ff` 已以 CAS fast-forward 更新 `main`；项目分支经 merge commit `c7533f97bd1c8594ecfaea8e73aa8c16917dbf04` 纳入 source。后续 Manager 发布使当前 project HEAD 前进，但 source 仍为祖先。
- 已核验原生 v2 fixture 汇总证据 `../b49a5b40-1d18-40e6-bc28-c5c57dc011f3/native-v2-fallback-evidence.json` 的 SHA-256 为 `b87e37cbb0214f53f447f23d13c297863fdf14d753869756c895aead699858bf`，其中列出 14 项 receipt。
- 安装 worktree 是 `workspace/a0c09804-1b5b-4df3-abf0-986ff19381af/multi-agent-manager`，HEAD 为 `3f2738abcfc9cbe50b25222562fc58b2bac0a7ff`，创建自 `main`。
- 标准非交互 installer 运行至暂停前：215 个 checkout unit tests 通过；pipx 完成从该 worktree 安装；App Server trace compatibility 与无模型未知-ID API compatibility 都打印 PASS；App Server 没有重启。它已经启动 isolated ordinary persistent-thread liveprobe。
- 收到用户“暂停生产更新”后，外层 installer 在 liveprobe 运行期间被 SIGSTOP；liveprobe 子进程自行退出、其专属 fixture service 退出，随后以 pending SIGTERM + SIGCONT 结束 outer installer。installer 以 `143` 退出并执行 `cleanup_install_tmp`；未执行 `start_project_service`。
- 因暂停发生在 liveprobe 子进程退出与外层 `validate_liveprobe_evidence` 之间，不能把 liveprobe 标为安装 gate PASS，也不能声称本次安装已完成。临时 evidence 随 installer cleanup 删除；保留的 transcript 只证明它被启动。
- production daemon 未被 installer stop/start：PID 始终是 `735869`，启动时间为 `2026-09-13 01:22:14`，Manager binding 为 `01a09657-e0f3-7352-b726-aba5bbd5d498`。pipx 盘上安装包已经更新，但常驻旧 PID 未被替换；不得把它当成 fallback 已生效。
- installer 按标准行为更新了受控 `/root/.bashrc` MAM trace/PATH blocks，并留下 transcript 指定的两个 backup。未重启 App Server，也未改 Codex DB/features。
- native-v2 exact direct-input rejection 仍只是 source 中识别的 capability boundary：当前 fallback 生成 Manager `manager_native_followup`，要求 parent-native `collaboration.followup_task`；它不恢复 native child direct `turn/start`。当前生产旧 daemon 仍可出现旧的 generic explicit-rejection 重试，未手动清理或改写该 state。
