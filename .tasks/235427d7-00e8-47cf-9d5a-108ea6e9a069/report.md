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

## 保留的证据与明确阻塞

5773 任务仍为 `pending`，其已发布报告明确写明 RMBench 离线闭包/入口、CPU/GPU smoke 和 C 端正式 100 rollout 尚未完成。因此保留：

- `5773b6ec-rmbench-cp310-split-lock-v1/`、`5773b6ec-rmbench-sdist-cache-fix-v1/`、`rmbench-cache-plan/`、`rmbench-resolver-cache-fix-v1/` 和其余非重复 lockfile；它们仍是未完成 RMBench 离线 resolver/缓存闭包的本地复现材料。
- `assets.sha256`、`checkpoint-20000.sha256`，以及 OpenPI bundle、两份 patch、`transfer.8H0TPy/`；它们对应已报告的 C 端传输校验和仍待完成的环境重建/验收证据。
- 根目录异常文件 `=============================算力牛=============================`；这是唯一找到的本地 C `create_worktree` 入口副本，内容对应 5773 报告中已部署的稳定目标 `C:/mnt/public/xcj/Projects/state-vla/.local/create_worktree.sh`。5773 尚未完成，且本地没有可验证的同哈希稳定副本，故不删除。该任务完成时应由其 owner 核对该稳定目标后删除这个误名副本，或将必要副本明确归属到 5773 的受管交付位置。

未触及活跃任务报告、本任务 report、`.codex/hooks.json`、`.local/hook-probe`、用户提供的 `docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md`，或任何未列入本任务范围的未跟踪项。

## 验证

- 归档状态已确认：35c9 和 ad6 任务均 archived，相关 jobs/worktree 已移除或归档。
- 5773 当前没有未归档 MAM job，但任务及其 C 环境交付仍 pending；这正是保留上述闭包/传输证据的原因。
- 删除后已检查所有七个目标均不存在，保留项仍存在；主根状态只剩已明确保留的 5773 证据、活跃/排除项和本报告草稿。
