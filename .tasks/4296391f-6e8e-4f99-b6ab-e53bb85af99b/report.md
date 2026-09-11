# 08:36 live Memory v1 一致性、部署说明与现场只读复查交付

## 交付结论

已完成 CPU-only 的 live/offline Memory v1 一致性修补、现有 x1pro takeover 入口说明、
`dd0914b` RPC 修复独立准入和现场 policy-server 只读核查。没有实现阻塞；本地 live
代码仍须 Manager 独立验收后才可同步到现场，现场真机动作、内网连通和新 PM child 的部署
仍由现场负责人执行。

本 task workspace：

- robot-bridge：`/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/robot-bridge`，干净，HEAD `0a33dd19ab911ae3808c3ff141e3fd0603c22594`。
  - 功能提交 `a5caa5b57e96fd02de7d6df0cd2ffa5bf0030f5f`：native Memory v1 S2M live/takeover 支持与真实 metadata 回归。
  - 文档提交 `0a33dd19ab911ae3808c3ff141e3fd0603c22594`：wash-cup 现场 runbook。
  - 基线包含已准入的 launcher `124049fb78d29db1d77d13a9fd4a4b698fcfe6e9` 和 RPC 修复
    `dd0914b170fe5d227f24d36b07d90c0e422b7e58`；本 task 未改这两个 offline 写集。
- OpenPI：`/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/openpi`，干净，
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，未修改。

## live / offline 一致性最小修补

实证差异是同一真实 wash checkpoint 的 native `s2m` Memory v1 schema 声明 14 维
robot-only state，而原 `OpenPiScheduler` 强制 slave+master 28 维，导致 live/takeover
在启动前拒绝；`OpenPiOfflineScheduler` 已能接受。`a5caa5b` 只在
`robot_bridge/scheduler/openpi.py` 为 **非 projection、Memory v1、native s2m** 增加窄路径：

- 要求 `robot_dim == slave_state_dim == 14`、恰好一个 current-state sample、无 legacy
  `key_state`；其他 native s2m 和所有无 memory 的拒绝规则保持原样。
- 不请求 `master_state_ts`，传 14 维当前 slave state；动作从 `[0:14]` 取出，插值锚点也是
  当前 slave state。同步 K30 语义固定 queue latency 为 0，UI 延迟调节不改变它。
- `OpenPiTakeoverScheduler` 继承这一 scheduler 路径；其 UDP relay、模式状态机和端口逻辑
  没有修改。

新增的真实 full/serial 20k metadata projection fixture 与 CPU fake transport 回归使用非零
slave state，逐项比较 live、takeover、offline 的 policy state、K30 动作切片和
`memory_input_ids`。full 在未完成时不提前更新，完成后以 model index 29 / row 30 反馈；
serial 用当前 query 预测反馈。回归还覆盖 manual memory/reset、homing 和 takeover 丢弃
pending feedback，以及既有 UDP takeover 行为。

## 验证

全部为 CPU-only，`CUDA_VISIBLE_DEVICES=''`；未加载真实模型、占用 GPU、连接真机或发送动作。

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=<openpi-worktree>/packages/openpi-client/src \
  .venv/bin/python -m pytest -q \
  tests/scheduler/test_memory_v1_schedulers.py \
  tests/scheduler/test_openpi.py tests/scheduler/test_openpi_feedback.py \
  tests/scheduler/test_openpi_takeover.py tests/scheduler/test_openpi_memory_transform_contract.py
# 51 passed, 1 skipped

CUDA_VISIBLE_DEVICES='' PYTHONPATH=<openpi-worktree>/packages/openpi-client/src \
  .venv/bin/python -m pytest -q \
  tests/robot/controllers/test_memory_v1_offline.py \
  tests/robot/controllers/test_drawer_offline.py \
  tests/robot/controllers/test_x2robot_offline_phase.py
# 17 passed

CUDA_VISIBLE_DEVICES='' PYTHONPATH=<openpi-worktree>/packages/openpi-client/src \
  .venv/bin/python -m pytest -q \
  tests/launcher/test_offline_preflight.py tests/scheduler/test_memory_v1_schedulers.py
# 31 passed
```

`ruff check --select E,F,I robot_bridge/scheduler/openpi.py tests/scheduler/test_memory_v1_schedulers.py`
和 `git diff --check dd0914b..HEAD` 均通过。

RPC 增量的独立复核结论已在本报告下一节发布：独立 detached 树以实际
WebSocket/codec → policy server → RobotServer → `handle_execute` 路径跑 full/serial
各两集，`27 passed in 19.63s`；`dd0914b` 准入 GPU2 retry2，输出固定为
`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry2`。

## 现有入口与部署说明

新增 [wash-cup-memory.md](../../workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/robot-bridge/docs/tutorials/wash-cup-memory.md)，
并已在 `docs/README.md` 索引。说明复用 `scripts/launch/x1pro_takeover.sh` 与现场
`~/.robot_bridge_env.sh`，给出：

- full 优先、serial 随后的精确 remote checkpoint 路径；
- 由 Policy Manager 部署新 child、复制其 WebSocket URL 到 `RB_POLICY_URL`，不重启/停止
  已有 PM 实例，也不重复模型同步；
- 保留现场 `RB_POLICY_SSH` / `RB_ROBOT_SSH` / `RB_MASTER_SSH` / `RB_SCHEDULER_SSH`
  与 URL 配置，不硬编码内网地址；
- policy pane 必须显示既有 Manager 的 `[skip]` 保护，防止启动手工额外 policy server；
- Memory v1 phase UI、K30 `memory_diagnostics`、homing/reset、idle/teleop/autonomous
  takeover 和 full/serial 不同反馈语义的现场检查边界。

## 现场只读核查与最小部署方案

通过 `jx-4090-2-via-nx-aic` 完成授权范围内核查，未写远端、未传输模型、未碰 PM 状态。
当前远端普通 deployment checkout 均干净：

- `/home/xucuijie/Projects/robot-bridge`：`124049fb78d29db1d77d13a9fd4a4b698fcfe6e9`。
- `/home/xucuijie/Projects/openpi`：`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
- OpenPI venv：Python 3.11.15，`pip check` 通过；`openpi_client.memory_config` 和三个
  scheduler module 导入通过。PyYAML 6.0.2 已满足新源码唯一新增的 `PyYAML>=6.0` 依赖。

Policy Manager 的两个 wash 本地模型都为 `complete=true`、`syncing=false`、`instances=[]`；
同步 jobs 3/4 均为 `done`：

- `/home/xucuijie/Projects/openpi/checkpoints/wuwen-nx-aic/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000`
- `/home/xucuijie/Projects/openpi/checkpoints/wuwen-nx-aic/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000`

PM 当前已有 8949/GPU0 和 8950/GPU0 运行实例，未重启。它按整棵已同步的 bridge/OpenPI
checkout 与既有 `RB_PY` 启动 child，不能为单个 wash 模型选择独立源码或 venv；最小方案是
Manager 审核 `a5caa5b` 后再同步 bridge 源码，保留现有实例，随后用 PM 新建 wash child 于
空闲端口/经现场确认的 GPU，并把该 child 的 URL 作为 `RB_POLICY_URL`。不需要重复模型传输。

## 待现场/Manager 闭环

1. Manager 对 `a5caa5b` / `0a33dd1` 做独立 review，决定是否将该 bridge 版本同步到 policy
   server；当前远端仍刻意保持 `124049fb`。
2. 现场内网与负责人可用后，由其部署 full PM child、按 runbook 进行 UI/metadata/homing/受控
   动作检查，再在 full 通过后独立部署 serial。
3. GPU2 retry2 虽已获 `dd0914b` 准入，仍由 offline owner/Manager 按固定新输出路径执行并
   验收真实两模型 5ep 指标；该正式 GPU 结果和真机结果均不由本 CPU 复核代替。

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
