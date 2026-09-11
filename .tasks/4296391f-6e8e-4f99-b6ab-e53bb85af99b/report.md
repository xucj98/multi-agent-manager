# 08:25 RPC 修复独立复核：GPU2 offline retry2 准入

## 裁定

bridge 候选 `dd0914b170fe5d227f24d36b07d90c0e422b7e58` **准入 GPU2 retry2**。它是已验收 launcher
`124049fb78d29db1d77d13a9fd4a4b698fcfe6e9` 的直接后继，增量仅限 offline controller 的
`handle_execute` 类型保留和对应 RPC 集成测试；未改通用 base、server、scheduler、launcher
或 OpenPI。固定 OpenPI 仍为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。

此准入只恢复正式 GPU offline；不代表该 GPU 回放指标、真机动作或现场部署已验收。必须使用新的
输出目录：
`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry2`，
不得覆盖 retry1 或首次失败产物；继续保留 launcher 的 source/clean/provenance、metadata 和 K 门禁。

## 独立复核证据

在独立 detached 审查树 `/tmp/mam-4296391f-rpc-dd0914b`（HEAD 精确为候选 commit，工作树干净）复查：

- 候选相对 `124049fb` 仅修改 `robot_bridge/robot/controllers/x2robot_offline.py` 和
  `tests/robot/controllers/test_memory_v1_offline.py`，且祖先关系成立。Memory v1 的 IDs/rows/query 类型
  保留在 offline controller；`arms`/`phase` 仍按既有机器人 RPC 合同转为 `float32`；未配置 Memory v1
  时仍委托通用 handler。
- 新增集成测不是直接调用 `execute`：它经 localhost WebSocket msgpack codec、policy server、
  RobotServer 的 `handle_execute` 分发到 offline controller。full/serial 各两个连续 fake-policy episode，
  H4/K3 各执行 `3+3+2` 尾部；断言 RPC 后 prediction IDs 为 `int32`、model rows 为 `int64`、query
  为 Python `int`，而机器人 arms 为 `float32`。
- 同一链路验证非法浮点 IDs、rows、query 及零维浮点 query 都被拒绝且不排队；随后正常 episode 仍能
  完成。完整 episode 还核对实际执行行、canonical action GT、memory GT/mask/反馈、队列清空和下一集 reset。

CPU-only 复跑：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=/tmp/mam-4296391f-rpc-dd0914b:<openpi-worktree>/packages/openpi-client/src \
  <bridge-worktree>/.venv/bin/python -m pytest -q \
  tests/robot/controllers/test_memory_v1_offline.py \
  tests/robot/controllers/test_drawer_offline.py \
  tests/robot/controllers/test_x2robot_offline_phase.py \
  tests/scheduler/test_memory_v1_schedulers.py
```

结果：`27 passed in 19.63s`。此外，候选两文件 `ruff check --select E,F` 通过，
`git diff --check 124049fb..dd0914b` 通过，审查树无未提交改动。没有加载模型、占用 GPU、
连接内网或发送真机动作。

# 07:51 launcher 增量独立复核：GPU2 offline retry 准入

## 裁定

`124049fb78d29db1d77d13a9fd4a4b698fcfe6e9` 可用于恢复 wash 的 GPU2 offline retry。
此结论只覆盖 launcher 的 metadata / 执行 K 门禁；不代表 offline 指标、真实模型
回放或真机行为已经验收。

独立复核树：

- robot-bridge：`/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/robot-bridge`，已从指定基线 `fda269c1f333dabdb5628c083a4dba3db0938333` fast-forward 到候选 `124049fb78d29db1d77d13a9fd4a4b698fcfe6e9`；工作树在本节写入前干净。
- openpi：`/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/openpi`，固定 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，未改动。

## 真实输入复核

首次失败产物
`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep/wash_full/served_metadata.json`
的真实形状为：`policy_hz=15`、`action_horizon=50`、顶层 `query_stride` **缺失**、
`memory_config.protocol.execution.rows=30`、`completion=synchronous_rows`。因此不能把
采样 stride 的缺失解释为执行 K 的缺失。

候选补丁的门禁行为与字段含义一致：Memory v1 以 schema `execution.rows` 分别对
scheduler 与 manifest 的 K=30 交叉校验；顶层 `query_stride` 缺失/`None` 时不冒充 K，
若服务实际提供它仍按 manifest 的采样 stride 校验。旧 drawer 的两份真实 served metadata
仍为 `15 Hz / H30 / query_stride=15` 且无 memory schema，继续走原 sampling-stride 门禁。

## CPU-only 验证

在上述 bridge tree 运行：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=<openpi-worktree>/packages/openpi-client/src \
  .venv/bin/python -m pytest -q tests/launcher/test_offline_preflight.py
```

结果：`18 passed in 0.74s`。该组包括真实失败 metadata 投影、缺失/`None`/已提供但冲突的
sampling stride、schema/manifest/scheduler 三方 K 冲突、频率/H 冲突与 legacy drawer 回归。

另以真实失败 full `served_metadata.json` 和两个真实 drawer `served_metadata.json` 直接调用
候选 `_validate_served_metadata`：wash 缺顶层 stride 且 K30 通过；manifest、scheduler 或
schema 的 K 错配均拒绝；两个 drawer 原值通过，缺失或改成 30 的 stride 均拒绝。
`git diff --check fda269c..124049f` 与 `.venv/bin/ruff check --select E,F` 也通过。

## retry 条件

Manager 可在 GPU2 使用候选 commit，按既定新输出目录
`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry1`
恢复；不得覆盖原失败目录。正式运行仍须保留 served metadata、provenance、每模型实际
infer / 执行行和指标产物。未触发 GPU、内网、跳板或真机操作。

live S2M scheduler 路径与真机部署说明为独立后续项，未并入本准入结论。
