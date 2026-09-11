# 历史未跟踪遗留清理完成

已按发布范围在主根 `/mnt/public/xcj/Projects/multi-agent-manager` 做了逐项核验和限定清理；没有运行 `git clean`，没有修改任何源仓、其他 workspace、进程、GPU 或远端主机。

已注册并保留本任务 worktree：
`/mnt/public/xcj/Projects/workspace/235427d7-00e8-47cf-9d5a-108ea6e9a069/multi-agent-manager`，分支
`task/235427d7-00e8-47cf-9d5a-108ea6e9a069`，基线 `main` 的
`351c3a3e6dc807cae280a99d5f3c824f8d5750ff`。本任务没有代码或文档提案，worktree 保持 clean，无交付 commit。

## 已删除（删除前 `du -sk` 合计 92 KiB）

| 路径 | 删除依据 | 删除前占用 |
| --- | --- | ---: |
| `.tasks/35c9e781-7d2e-49a1-bb4c-25d77b865b3a/final_audit.py` | 任务已归档，三个 worktree/分支已移除；脚本硬编码已移除的 workspace，正式审计结果已在该任务稳定产物中。 | 8 KiB |
| `.tasks/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/{launch_wash20k.py,wash_checkpoint_gate.py}` | 任务已归档、worktree 已移除且 jobs 已归档；两脚本均硬编码已移除的 workspace，稳定 checkpoint/日志证据已由归档任务保留。 | 1 KiB + 8 KiB |
| `.tasks/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/asset-staging/` | 只有 5 个符号链接、没有普通文件；C 端最小资产已按保留 manifest 验证。以 `find -P -depth -delete` 删除，只解除链接，不跟随或删除任何链接目标。 | 8 KiB |
| `.tasks/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/manifest-staging/` | 两份 SHA256 manifest 与保留的 `assets.sha256`、`checkpoint-20000.sha256` 逐字节相同（哈希分别为 `22353e…`、`cb4032…`）；`transfer.json` 的计数和哈希已写入 5773 已发布报告。 | 58 KiB |
| `.tasks/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/rmbench-cp310-{cu121-locked-requirements,pypi-locked-requirements}.txt` | 内容哈希分别与保留的 `5773b6ec-rmbench-cp310-split-lock-v1/` 内规范副本一致：`5bcc1a…`、`4b2cacf…`；后者还保留安装顺序说明。 | 1 KiB + 8 KiB |

删除前以 `lsof` 检查五个普通文件、以 `lsof +D` 检查两个目录，均无打开文件描述符（退出码 1）。删除后逐一路径复核为不存在，`git status` 不再列出这些项。

## 后续：按 successor 当前状态整理 5773 证据

已读取 successor `2a879870-8dda-4613-a684-0ad48a5e86be` 的最新已发布报告（revision `e324362dd2349d6beba20fe7619834d0ef0f94c3`）。它确认 C 的稳定 `.local` 已保存精确离线锁和 patch、RMBench fresh 离线创建已成功；旧 owner 的 cache/资产/records 已在 C 端只读复用。当前 C 的 renderer 生命周期根因门禁与本机 MAM 根目录的旧传输文件无关，successor task/report 也没有引用下列 MAM 本地路径。

### 本轮删除（删除前目标合计 `du -sk` 为 15,925 KiB）

- 删除顶层 OpenPI bundle、两份 patch 和 `transfer.8H0TPy/`。bundle 所指 `a869498`、`958eeae`、`5f6ca06` 和 RMBench `6139577` 都仍由本机命名 refs 持有，其中 successor 分支直接持有相关 OpenPI/RMBench 提交。`openpi-uv-symlink-5f6ca06.patch` 与 `a869498..5f6ca06` 的完整 diff 同一 patch-id；installer-only patch 分别与该范围和 `a869498..958eeae` 的 installer diff 一致，且 transfer 中 `create_worktree_env.sh` 与 `958eeae` 的源码逐字节相同。
- 删除两个 cache-fix 目录中的 archive/sdist/simple/wheel payload，只保留 `apply-plan.json` 和 `manifest.sha256`。这些 payload 是完成 C cache 回填前的本机传输副本；successor 已实际用 C cache 和稳定离线锁完成 fresh 安装。
- 删除 `rmbench-cache-plan/{paths.txt,transfer.log,transfer-paths.txt}`，只保留 cache selection、wheel-link 映射和摘要。前者是 7.9 GiB 传输的原始路径/日志副本；后者保留可复核的闭包计数与链接选择。
- 删除根目录异常文件 `=============================算力牛=============================`。它没有重命名：与 `.tasks/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/remote-staging/.local/create_worktree.sh` 逐字节相同（SHA256 `544662…`），因此不是唯一脚本。保留副本位于已有任务 staging 路径；该 `.local` 路径受既有 ignore 规则保护，未作为 Manager commit 候选。

删除前对所有文件运行 `lsof`、对所有目录运行 `lsof +D`，均无打开文件描述符；目录删除均使用 `find -P -depth -delete`，未跟随符号链接。删除后每个目标均已复核不存在。

### 建议 Manager 提交的精简证据

以下路径都在既有 `.tasks/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/` 下、未 staged，总计约 300 KiB（含目录元数据），可直接作为一次小型历史证据提交：

```text
assets.sha256
checkpoint-20000.sha256
5773b6ec-rmbench-cp310-split-lock-v1/
rmbench-cp310-known-good-freeze.txt
rmbench-cp310-offline-locked-requirements.txt
5773b6ec-rmbench-sdist-cache-fix-v1/apply-plan.json
5773b6ec-rmbench-sdist-cache-fix-v1/manifest.sha256
rmbench-resolver-cache-fix-v1/apply-plan.json
rmbench-resolver-cache-fix-v1/manifest.sha256
rmbench-cache-plan/selection.json
rmbench-cache-plan/wheel-links.json
rmbench-cache-plan/summary.txt
```

关键完整哈希已重新记录：资产 manifest `22353e70420a0e474173413b3c18df6dc015506faf8352f31e06107f16bfcd4c`，checkpoint manifest `cb4032ce56b471eabb2f5138925af5cbce800cfbea8630aab85d44d9c665ab79`；split-lock 内保留两份 SHA256 校验和与安装顺序文件。5773 的已跟踪 `task.md`、`report.md` 不在上述新增候选中，旧报告仍描述其历史传输而不依赖已删除的本机副本。

未触及活跃任务报告、本任务 report、`.codex/hooks.json`、`.local/hook-probe`、用户提供的 `docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md`，或任何源仓、其他 workspace、GPU、远端主机和进程。`git diff --cached --name-only` 为空，本任务 worktree 仍 clean。
