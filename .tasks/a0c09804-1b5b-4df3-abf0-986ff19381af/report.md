# MAM native-v2 fallback：集成、标准安装与生产验收完成

用户选择将原生 v2 direct-input 拒绝降级交由 Manager 协调处理。本任务未恢复 direct `turn/start`，也没有设计或测试新的直达路径；已验收的 fallback 已安装到本项目生产 MAM daemon。

## 集成和安装源

- 已验收 source `3f2738abcfc9cbe50b25222562fc58b2bac0a7ff` 已先 fast-forward 到 `main`，再以 merge `c7533f97bd1c8594ecfaea8e73aa8c16917dbf04` 带入 `project/state-vla`。并发发布随后推进了项目 HEAD，但 source 仍为祖先。
- 本任务安装 worktree 为 `workspace/a0c09804-1b5b-4df3-abf0-986ff19381af/multi-agent-manager`，branch `task/a0c09804-1b5b-4df3-abf0-986ff19381af`，HEAD 保持精确 `3f2738a` 且 clean。
- 已核验先前完整 native-v2 fallback fixture，不重跑：`b49a5b40-1d18-40e6-bc28-c5c57dc011f3/native-v2-fallback-evidence.json`，SHA-256 `b87e37cbb0214f53f447f23d13c297863fdf14d753869756c895aead699858bf`，14 receipts。

## 本次标准 installer

从上述独立 worktree 非交互运行 `MAM_SERVICE_MANAGER=01a09657-e0f3-7352-b726-aba5bbd5d498 bash scripts/install.sh < /dev/null`，退出 `0`。

- checkout 单元测试：215 项通过（`82.068s`）。
- App Server trace compatibility：PASS；installer 确认已存在 listener 的 JSON trace 配置，无需重启 App Server。
- 无模型 unknown-ID App Server API compatibility：PASS。
- 隔离的普通 persistent-thread real-delivery gate：PASS，固定 6 个 `gpt-5.6-terra/max` 模型 turn；它验证四个 baseline、Manager 批量 delivery、stopped-job executor delivery、quiet window 和 fixture cleanup。它不创建或验证原生 multi-agent-v2 child，因而不代表 direct input 已恢复。
- 上次暂停的 installer 退出 `143` 和证据仍单独保留；本次没有重跑 native-v2 fixture。

标准 installer 把原始 `liveprobe-evidence.json` 放入其拥有的临时目录，并在退出时按其 cleanup trap 删除。为保持可核验性而不虚构已保留原始 JSON，新增 `resume-liveprobe-derived-receipt.json`：它绑定本次 transcript SHA、installer/liveprobe source SHA、`status=passed`、6 turn 和八项必要 check，以及成功返回必须完成 fixture cleanup 的代码路径。该文件明确标为 derived receipt。

## 生产 daemon 和安装包

- 原 singleton PID `735869`（启动 `2026-09-13 01:22:14`）在全部三个 installer 门禁通过后才由 installer 替换；新的 PID 为 `1074834`，`started_at`/`ready_at` 均为 `2026-09-13T12:09:04Z`。
- 新 daemon 以 pipx site-packages 的隔离 bootstrap 启动，命令使用 `/root/.local/share/pipx/venvs/multi-agent-manager/lib/python3.12/site-packages`，不引用本任务 worktree；`cwd` 是既有 `MAM_ROOT`。
- source 和 installed `wake_runtime.py` 均为常规非 symlink 文件，SHA-256 同为 `c926e9d9d9d916ad80bbb37219be8e26f52f0700fe6a88171669390691f55de2`。安装包因此不依赖本 task worktree 持续存在。
- 安装后 service 为 `running: true`、`healthy: true`、`status: healthy`，Manager binding 保留为 `01a09657-e0f3-7352-b726-aba5bbd5d498`，当时 `pending.count` 为 0。
- 未重启 App Server、未修改 Codex DB/features，未停止、改绑、归档任何训练或评测 job/task。安装前后核对显示训练任务 `e3bc64f1-7f0d-46d2-9e54-831aa1727384` 的 8 个未归档 job ID 完全相同；评测任务 `e6908de7-4b02-465a-987b-a19eba7a315a` 在两次快照中均无未归档 job。

新 daemon 加载的 source 对精确 native-v2 direct-input 拒绝会持久化 blocked source 并创建 `manager_native_followup`，供 parent Manager 使用 `collaboration.followup_task` 协调；本次未制造生产假 stopped job 观察该分支，且不宣称 direct child input 已恢复。

## Evidence

本次恢复安装的证据均在 `.tasks/a0c09804-1b5b-4df3-abf0-986ff19381af/evidence/`，与暂停期证据分开：

- `resume-install-transcript.log` — SHA-256 `ac8b86d21527b935f637d6e94dba53deaf56d2cb583541b615f4fd4bf17fb21a`
- `resume-install-exit.txt` — `installer_exit=0`
- `resume-liveprobe-derived-receipt.json` — SHA-256 `eb9734a2463f4defd8b8e6ac49d166ba9ba0a8dcd4f86a961e210e2f9bb96bbe`
- `resume-postinstall-runtime.json` — SHA-256 `33bc2880b82f698353dc9b32c178212d316330dd68a48267ce118ec9df1fec27`
- `resume-postinstall-package.txt` — SHA-256 `888b12f523a04ffa5da89ff2b50a74a72f9d3f4a5db39019ac1b9c18119e2687`
- `resume-production-topology-diff.json` — SHA-256 `e9a7ecbb8ccb7cac4f6a9699efa84e1c3afa2e36b77c57842708a53b3671dc4c`
- `resume-preinstall-snapshot.txt` — SHA-256 `67e380828bd7d1377723f1259fe52dcb8853a84be58af05d8f629170e7d15f0a`

生产切换和本任务交付均已完成，供 Manager 独立验收并按“降级处理完成”归档安装与 source 任务。
