task_revision: 4fefffca62dc87fcdfd77d9fc9ebabe2088c17a7

# B/C 稳定入口与 OpenPI 内容 profile 部署结果

## 已交付

B 稳定根 `/mnt/public3/xcj/Projects/state-vla` 已补齐独立的 `RMBench` 和 `robot-bridge` 主仓库，分别固定为 `f401f5279c95451eb424ac98b831bab5552b2120`（`frozen-f401f527`）和 `f9626636c4776d8eb15f9c556775cb2d12c000e5`（`frozen-f9626636`）。两仓库的稳定三参数入口可用，源树 tracked 状态保持 clean。

C 的 OpenPI 稳定仓库保留以下受管环境 base：

| base | C 稳定 ref | 安装器 profile |
| --- | --- | --- |
| `34002dce65962734c59725a0f6d982ae2c438a2d` | `frozen-34002dce` | `legacy-patched`，继续应用原有外部 symlink patch。 |
| `c03898f5a76f4ac208f7d23ae14e2cc759be8853` | `frozen-c03898f` | `native-symlink`，安装器原生支持 `--link-mode`，不重复打补丁。 |

C 稳定 checkout 仍为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，没有 reset；其安装器内容与 `34002dce` 相同，因此也会走 legacy profile。未改活跃 worktree、模型、数据或 GPU 进程。

## OpenPI 入口内容身份修复

共享入口 `/mnt/public/xcj/Projects/state-vla/.local/create_worktree.sh` 已由完整 commit 白名单改为：先将受管安装器提取到 `MANAGED_TMP`，在该文件上检查 `# worktree-local-entry: create_worktree.sh` 合同标记，再以完整 SHA-256 选择 profile。它不再使用 `git show | grep`，避免 `pipefail` 下 `grep -q` 提前退出造成的 SIGPIPE 误报。

| 安装器 SHA-256 | profile | 已验证 base |
| --- | --- | --- |
| `8a84fef951cd64b55f4311b3369a9db08128a9506a2632a79d87d2f9c2acbb95` | `legacy-patched` | `34002dce`、稳定 `a869498f` |
| `9c28f71bce800ad35a457dfbe35e0a58d15f91ff060a6b3efc982770a872e2f7` | `native-symlink` | `c03898f` |

未知的合同安装器仍明确拒绝，不会猜测能力或创建 workspace。`3435a2b60bfb34197adeb8fe54ad750aeb78a5ed` 的安装器 hash 为 `ef4c65af3e6f5227a120bfa58ecdf73b4f96a38d98c1bafa738f7242bcaa37ac`；入口返回状态 `2`，且目标 workspace 不存在。

入口前后副本、哈希和验证证据在：

`/mnt/public/xcj/Projects/state-vla/.local/backups/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/openpi-content-profile-entry/`

- 前哈希：`df626097cc5a103d73770af8373acd8100cd187754065bb320f03eb037d32472`
- 当前及后副本哈希：`d2f5e832c3f68ef068341df3a06683e823de5a5a1f845e6d23263242a0ac46cd`
- 静态验证：`static-validation.log`；其中包含三种 profile 映射、legacy patch 应用加 `bash -n`、未知 hash 拒绝和无 workspace 检查。
- C1 复验快照：`c1-blank-retest-blocked-snapshot.log`。

原外部 patch 未改，SHA-256 为 `e82f41df208c7005afd767d96781a55182397ec3030b9c2c8abfd88d0dfb284a`。稳定入口自身通过 `bash -n`。

## C2 已完成的独立验证

在 C2 `is-ddj72hiexddjfwo6-devmachine-0`，已用三参数入口从 `c03898f` 创建全新 worktree：

```text
bash /mnt/public/xcj/Projects/state-vla/openpi/.local/create_worktree.sh \
  c03898f5a76f4ac208f7d23ae14e2cc759be8853 \
  task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9-cpu-openpi-c03898f-c2 \
  /mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-openpi-c03898f-c2
```

安装完成后显示 native profile、242 个 symlink 安装包、私有 transformers patch、cache symlink probe 和 `pip check` 均成功。随后默认命令 `.venv/bin/python scripts/worktree_env_smoke.py` 成功；解释器、`openpi` 和 `openpi_client` 都来自该新 worktree。日志与 metadata 位于该 workspace 根的 `create-worktree.log`、`default-cpu-smoke.log` 和 `verification-metadata.txt`。这只是 C2 结果。

## C1 自测收尾（不作为空白验收）

本任务启动的 C1 `blank-c1-c03898f` 是修复者自测，不是原 `bed9952b-c1a2-40ec-9f6d-34feeba91aa5` 空白验收。它已从最初的共享盘 I/O 等待恢复，创建了 `c03898f` worktree 和 `.venv`，随后停在 `uv sync --frozen --active --link-mode symlink`。没有完成入口、`pip check` 或默认 CPU smoke，因此不提供 C1 通过或失败结论。

在 `2026-09-15T03:01:24+08:00`，本任务的 `uv sync` 与原验收者的 C1 安装同时使用 `/mnt/public/xcj/cache/uv`；原验收者当时已进入 `pip check`，而本任务仍在 sync 等待。为优先原验收者，只核对并向本任务的精确 `uv sync` PID `1895752` 发送 TERM。该子进程于 `2026-09-15T03:03:00+08:00` 退出；`2026-09-15T03:03:28+08:00` 复核本任务进程树已不存在。原验收者的入口、受管安装器和 `pip check` 进程未被信号操作。

保留部分 worktree、branch、`create-worktree.log` 与 `verification-metadata.txt`，没有删除或重试：

```text
/mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/blank-c1-c03898f
```

证据保存在 backup 路径的 `c1-blank-retest-cancellation-snapshot.log`、`c1-blank-retest-cancellation-result.log` 和 `c1-blank-retest-cancelled-create-worktree.log`。本任务没有仍在运行的 C1 进程，也没有未归档 MAM job；原验收者的进程归其任务处理。

## 最终空白验收与归档锚点

原空白使用者任务 `bed9952b-c1a2-40ec-9f6d-34feeba91aa5` 已归档，其最终已发布报告为 `499a7c59f9457f58b6d14baa1b728547cefc5878`。Manager 已接受六项文档驱动独立环境创建和 CPU 检查全部通过；其中 C1/OpenPI 使用 `c03898f5a76f4ac208f7d23ae14e2cc759be8853`，三参数入口和普通 `worktree_env_smoke.py` 均 exit 0，且 `PYTHONOPTIMIZE` 未设置。这是独立的 C1 空白验收，不以此前 C2 结果或本任务取消的 C1 自测替代。

`c03898f` 已保留为 C 稳定仓库 `/mnt/public/xcj/Projects/state-vla/openpi` 内的独立恢复 ref：

```text
refs/heads/frozen-c03898f -> c03898f5a76f4ac208f7d23ae14e2cc759be8853
object type: commit
parent: 34002dce65962734c59725a0f6d982ae2c438a2d
tree: f2316e769447f7bf3dab6fff5faa31878b813182
```

该 ref 独立于本任务所有 `task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9*` 分支；稳定 checkout 仍为 `a869498f…`。`show-ref`、`rev-parse`、`cat-file -t`、commit 元数据和受管安装器 hash 均已核对，记录在稳定证据中的 `c03898f-stable-ref-verification.txt`。归档不得删除或改名 `frozen-c03898f`，因此 archive 不会丢失唯一的交付 commit。

入口两轮前后文件、哈希、静态拒绝/兼容检查、C2 成功创建与 smoke、取消的修复者 C1 自测日志，以及原空白验收报告，已归集到：

```text
/mnt/public/xcj/Projects/state-vla/.local/backups/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/final-delivery-evidence/
```

目录包含 `SHA256SUMS`、`entry-history.txt`、`c03898f-stable-ref-verification.txt`、C2 成功日志、C1 取消日志、`blank-acceptance-report-499a7c59.md` 与 `cleanup-inventory.txt`。原始日志和 worktree 未移动。 已在 C1 对 `SHA256SUMS` 的 30 个条目执行 `sha256sum -c`，全部通过；记录为 `final-checksum-verification.log`。

## 清理边界

本任务没有再运行安装，也没有删除任何目录、模型、数据、cache、其他 workspace 或已用 runtime。C1/C2/C3 最后扫描没有本 TASK-ID 进程，`mam job list --task` 也没有未归档 job。

- **必须保留：** `frozen-c03898f`、稳定入口及完整 backup/evidence 目录；C2 成功 runtime `cpu-openpi-c03898f-c2` 及其 task branch 作为已用 runtime。
- **可在 Manager 明确授权后清理：** 已取消的修复者 C1 部分 worktree `blank-c1-c03898f` 和仅对应的 `task/...-blank-c1-c03898f` branch。应先用 Git 对精确 worktree 做移除并确认 `git worktree list`，随后才可删该精确 branch；不可使用递归删除，也不可碰 `frozen-c03898f`。
- **可在本任务归档后由 Manager 处理：** 本任务 A 侧 clean 的 `openpi` 和 `multi-agent-manager` worktree，以及 C 专属 bootstrap 副本。稳定 frozen ref 与证据已使这些不再是 `c03898f` 的唯一保存处。
- **暂不建议清理：** `bundle-staging/` 中 B 的恢复 bundle，需单独完成 B 的恢复 ref 审计后再决定。

完整路径、理由和推荐操作顺序见上述稳定证据目录的 `cleanup-inventory.txt`。

