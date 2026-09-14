task_revision: da337d9be843b7089fc8e7203814882502f81be1

# B/C 稳定入口与 OpenPI symlink smoke 部署就绪

## 已交付

B 的稳定根 `/mnt/public3/xcj/Projects/state-vla` 已补齐独立的 `RMBench` 和 `robot-bridge` 主仓库，分别固定为 `f401f5279c95451eb424ac98b831bab5552b2120`（`frozen-f401f527`）和 `f9626636c4776d8eb15f9c556775cb2d12c000e5`（`frozen-f9626636`）。两仓库的稳定 `.local/create_worktree.sh` 可用，tracked 源树 clean。

C 的 OpenPI 稳定仓库 `/mnt/public/xcj/Projects/state-vla/openpi` 现有两个受管环境 base：

| base | C 稳定 ref | 三参数入口的安装器 profile |
| --- | --- | --- |
| `34002dce65962734c59725a0f6d982ae2c438a2d` | `frozen-34002dce` | `legacy-patched`：继续应用原有 `openpi-uv-symlink.patch`。 |
| `c03898f5a76f4ac208f7d23ae14e2cc759be8853` | `frozen-c03898f` | `native-symlink`：确认原生 `--link-mode` 能力后不再应用外部补丁。 |

`c03898f` 是 `34002dce` 的直接子提交，包含显式 venv、词法 site-packages、补丁字节/私有 inode/链接逃逸检查和原生 `--link-mode hardlink|symlink`。通用说明在 `openpi/docs/worktree_env/README.zh-CN.md`；没有向集群入口增加优化模式或提交专属恢复命令。

C 的稳定 checkout HEAD 仍为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，没有 reset。入口改动仅在 `/mnt/public/xcj/Projects/state-vla/.local/create_worktree.sh`：

- 前副本与哈希：`adfc2ce56f81817e5c75e8c2a5c37c618424c500560c53f7eb26dbc9d4bb24a6`
- 后副本与哈希：`df626097cc5a103d73770af8373acd8100cd187754065bb320f03eb037d32472`
- 保留位置：`/mnt/public/xcj/Projects/state-vla/.local/backups/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/openpi-c03898f-entry/`
- 原 `openpi-uv-symlink.patch` 未改，SHA-256 为 `e82f41df208c7005afd767d96781a55182397ec3030b9c2c8abfd88d0dfb284a`。

入口对任何其他 OpenPI base 在创建目录前以状态 2 拒绝，并报告 `openpi base has no approved symlink installer profile`；不猜测能力、不全局移除旧补丁。旧 base 的补丁已在保留副本上成功应用并通过 `bash -n`，新 base 原生安装器也通过 `bash -n` 与 `--link-mode` 能力静态检查。

## C2 独立 worktree 验证

C1 的共享库 bundle 校验在 20 秒内以 124 超时；按任务要求改在 C2 执行准备和验证，不能把下列结果表述为 C1 通过。C2 主机为 `is-ddj72hiexddjfwo6-devmachine-0`；C1 随后已能快速解析新 ref 和入口哈希，说明共享稳定路径已就绪。

C2 用用户的三参数入口创建全新 worktree，未改活跃环境：

```text
bash /mnt/public/xcj/Projects/state-vla/openpi/.local/create_worktree.sh \
  c03898f5a76f4ac208f7d23ae14e2cc759be8853 \
  task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9-cpu-openpi-c03898f-c2 \
  /mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-openpi-c03898f-c2
```

安装在约 45 秒内完成：242 个包以 symlink 模式安装、`transformers patch: private files installed`、cache symlink probe、`pip check` 和 `openpi installer profile: native-symlink` 都成功。worktree HEAD 为 `c03898f5a76f4ac208f7d23ae14e2cc759be8853`，tracked status 为空。随后从该 worktree 根目录运行用户默认 CPU 命令：

```text
.venv/bin/python scripts/worktree_env_smoke.py
```

命令成功，输出的 Python、`openpi` 和 `openpi_client` 都在该 C2 worktree venv/源码路径，`numpy=1.26.4`。证据保留在：

- `/mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-openpi-c03898f-c2/create-worktree.log`
- `/mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-openpi-c03898f-c2/default-cpu-smoke.log`
- `/mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-openpi-c03898f-c2/verification-metadata.txt`

没有启动 GPU、修改模型/数据、重装他人环境或改动现有活跃 worktree。新建安装少于 30 分钟，无需登记 MAM job；本任务没有未归档 job。

## 供最终空白复验的入口

C1/C2 共享稳定库；下面是集群文档规定的 C1 三参数入口，实际 C1 复验应作为新的独立结果记录：

```text
ssh wuwen-4090-1 'bash /mnt/public/xcj/Projects/state-vla/openpi/.local/create_worktree.sh c03898f5a76f4ac208f7d23ae14e2cc759be8853 task/<TASK-ID> /mnt/public/xcj/Projects/state-vla/workspace/<TASK-ID>'
```

创建后仅运行新 worktree 中的普通 `.venv/bin/python scripts/worktree_env_smoke.py`。B 的两条既有三参数入口可由原空白使用者按此前报告复验。

此前三个预计较长的 CPU 安装/检查 job 均已核验并归档：`96d3f5cb-64ff-4a0d-8f9a-27f71eb413a7`、`1c84ec4b-be45-4f86-9328-a05cf39755b0`、`db8b6dd2-845a-45d2-8fbf-35658fa0346e`。
