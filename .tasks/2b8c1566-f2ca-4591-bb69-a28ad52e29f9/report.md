task_revision: 761a5d251d16b630af630736294b2a51679c010b

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

## C1 空白复验状态

C1 `is-ddfwxekq6usner7v-devmachine-0` 已实际启动新的三参数复验，base、branch 和 workspace 分别为：

```text
c03898f5a76f4ac208f7d23ae14e2cc759be8853
task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9-blank-c1-c03898f
/mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/blank-c1-c03898f
```

该次尝试没有通过或失败的 smoke 结论：在 `2026-09-15T02:54:05+08:00`，其 `git worktree add` 子进程曾处于 `D / wait_on_page_bit_common`；随后保存的 `2026-09-15T02:55:02+08:00` 快照仍显示入口和受管安装器在等待，workspace 仅有初始 `openpi/.git`。因此未开始 uv sync，也没有运行 CPU smoke。按照任务要求，未重试、未中断其他 C1 安装；精确的进程、日志和目录快照在上述 backup 路径中。C1 不能据 C2 结果宣称通过。

这次启动原预计远低于 30 分钟，故未登记 MAM job；截至交付时本任务 `mam job list` 没有未归档 job。若共享盘恢复后仍需处理 C1，应先核对该次部分 worktree/branch 的最终状态，再决定清理或继续，避免重复创建。
