# policy 主机代码同步与现场前置状态

## 已完成：policy 主机精确同步

独立 review 已 PASS 后，已通过 `jx-4090-2-via-nx-aic` 将 policy 主机
`/home/xucuijie/Projects/robot-bridge` 从干净的
`124049fb78d29db1d77d13a9fd4a4b698fcfe6e9` 精确更新为
`041405f0b35b2a173ac3461d297a43141d028026`。远端原本没有该对象；仅传输了
`124049f..041405f` 的 git bundle（17,703 bytes，SHA-256
`af943b080293f772c3c535ded811411755e2e94f7d9e726aee1334c144fc324c`），在远端
校验后 fetch 到临时 ref，再 `git reset --hard` 到该 commit。同步前 `git status` 和
`git clean -nd` 都为空，因此没有删除任何 untracked 文件；bundle 已在两端清理。

同步后核对：

- bridge HEAD 为 `041405f0b35b2a173ac3461d297a43141d028026`，工作树干净，
  `git diff --check 124049f..HEAD` 通过。
- OpenPI 未写入，仍为干净的
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
- 以现有 OpenPI venv 在 `CUDA_VISIBLE_DEVICES=''` 下导入
  `robot_bridge.scheduler.openpi`、`robot_bridge.scheduler.openpi_takeover` 和
  `openpi_client.memory_config` 成功；三个模块分别来自更新后的 bridge 和固定 OpenPI
  checkout。没有加载模型或占用 GPU。
- 没有 stop/restart Policy Manager 或任何 child。同步前后 manager PID `3646`、
  pourtea child PID `1249503`（:8949）和 `2140250`（:8950）一致；现有实例继续 running。
  三个进程的 `/proc/<pid>/cwd` 都仍为该 bridge checkout；本次 diff 不涉及
  policy-manager/runner，现有进程无需 source reload，而后续新建的 wash child 会从当前
  `041405f` checkout 启动。

## 刷新后的 PM/GPU 状态与 full 优先请求

只读 `status` 结果：PM 基准端口为 `8949`，现有 pourtea 占用 :8949/GPU0/7.0G 和
:8950/GPU0/7.2G；两个 wash 20k 模型均为 `complete=true`、`syncing=false`、
`instances=[]`。GPU0 仅余 315 MiB，GPU1 余 24,067 MiB；PM 给出的
`suggested_gpu` 是 `"1"`，`suggested_port` 是 `8951`。因此 full 的候选请求（**供
Manager 决定并发出，本次未调用 deploy**）为：

```json
{
  "cmd": "deploy",
  "backend": "openpi",
  "host": "wuwen-nx-aic",
  "path": "pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000",
  "port": 8951,
  "gpu": "1",
  "memory_gb": 7.2,
  "policy_config": null
}
```

`memory_gb: 7.2` 只是复用当前 Pi05 child 的已用显存预算（对应约 0.3001 fraction），
不是本次启动动作或 wash 模型实测结论；Manager 可在部署对话框中改为其确认的值。PM
启动命令仍是既有的
`/home/xucuijie/Projects/openpi/.venv/bin/python scripts/run_policy_manager.py --config configs/policy_manager.yaml`，
child 使用 `scripts/run_policy_server.py --config configs/policy_backends/openpi.yaml`；本次代码差异
不涉及 policy-manager/runner，因此不需要为这次 source sync 重启 PM。

## 尚未就绪：scheduler/master 与现场 launcher

本次只更新了 policy 主机，**不能称为真机全链路就绪**。`run_scheduler.sh` 会经
`RB_SCHEDULER_SSH` 在 master 机器人上执行
`cd ${RB_REPO:-$HOME/Projects/robot-bridge} ... scripts/run_scheduler.py`；因此实际
scheduler/master `jx-x1pro-m-060` 的该 bridge checkout 必须也精确为 `041405f`，并在
CPU-only 导入通过后才可启动 scheduler。执行
`x1pro_takeover.sh --skip-policy` 的现场 WSL/launcher checkout 同样必须为 `041405f`，
否则没有该选项或不会带入修复后的 URL 行为。

本 task 没有连接、修改或启动 master/scheduler，也没有发真机动作。现场负责人完成这两处
同 commit 同步、PM full child 显示 running 并把其 URL 写入既有
`~/.robot_bridge_env.sh` 后，才可依 runbook 做 full 的 UI/homing/受控动作检查；serial
须在 full 验收后另建 child。

# `--skip-policy` 启动修复：独立 review PASS

## 提交与准入范围

robot-bridge 新提交：`041405f0b35b2a173ac3461d297a43141d028026`
(`fix(launch): skip policy manager deployment`)，基于此前已审阅的
`0a33dd19ab911ae3808c3ff141e3fd0603c22594`。本 task worktree 为
`/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/robot-bridge`，
提交后已清理本 task 的 pytest/ruff/Python 缓存，工作树干净。

该提交只改三处：`scripts/launch/x1pro_takeover.sh`、wash runbook 和一个 CPU fake
tmux/ssh 测试。它增加显式 `--skip-policy`：

- 仅在该选项下要求非空的 `ws://` / `wss://` `RB_POLICY_URL`，不要求
  `RB_OPENPI_POLICY_DIR` 或 `RB_POLICY_SSH`；`--help` 正常退出，未知参数退出 2。
- policy pane 只打印外部 Policy Manager child 已就绪的说明；不发送
  `run_policy_server.sh`，因此不执行其端口探测、启动或重启逻辑。
- scheduler pane 把所选 URL 以 `printf %q` 的内联环境赋值传给
  `run_scheduler.sh`，避免已有 tmux server 的持久旧环境覆盖新 child URL。
- 不带选项的手工 policy 路径仍会发送原有 `run_policy_server.sh`，并仍要求
  `RB_POLICY_SSH`。

runbook 现在要求先在 PM 确认 wash child 为“运行中”，复制其 URL 后执行
`bash scripts/launch/x1pro_takeover.sh --skip-policy`；明确该路径不会触碰 policy
进程，且 URL 无效或 child 未就绪时应先修正 PM 状态。

## CPU 验证与独立 review

全程 CPU-only，未连接现场、未发真机动作、未更新远端 checkout，也没有停止或重启任何
Policy Manager 实例。复跑命令：

```bash
CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q \
  tests/launcher/test_x1pro_takeover_launch.py \
  tests/launcher/test_tmux_run.py \
  tests/scripts/test_run_scheduler.py
# 19 passed in 0.98s

.venv/bin/ruff check tests/launcher/test_x1pro_takeover_launch.py
bash -n scripts/launch/x1pro_takeover.sh
git diff --check
```

新测试用 fake tmux pane 显式注入旧 `ws://…:8949`，而调用端选中
`ws://…:8953`；断言 scheduler 的 SSH 命令只收到 `:8953`、skip 路径恰好三次 SSH
且没有 policy command，默认路径仍四次 SSH 并启动手工 policy。也覆盖缺失/非法 URL、
help 和未知参数。

reviewer `3b678966-7bf3-48f2-b462-920f9cc6a33f` 已对 skip/default 两条 shell 路径、
tmux URL 转发和 runbook 入口给出 PASS；因此已按后续授权完成上文所述 policy 主机同步。
该 PASS 不替代 scheduler/master 和现场 launcher 的同 commit 同步。

# 08:36 live Memory v1 一致性、部署说明与现场只读复查交付

## 交付结论

已完成 CPU-only 的 live/offline Memory v1 一致性修补、现有 x1pro takeover 入口说明、
`dd0914b` RPC 修复独立准入和现场 policy-server 只读核查。没有实现阻塞；本地 live
代码仍须 Manager 独立验收后才可同步到现场，现场真机动作、内网连通和新 PM child 的部署
仍由现场负责人执行。

本 task workspace：

- robot-bridge：`/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/robot-bridge`，干净，当前 HEAD `041405f0b35b2a173ac3461d297a43141d028026`（本节原交付基线为 `0a33dd19ab911ae3808c3ff141e3fd0603c22594`）。
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

交付后已清理两个本 task worktree 中的 `__pycache__`、`.pytest_cache`、`.ruff_cache`，
保留 `.venv` 和共享 ignored 数据/模型；已用 `git worktree remove` 删除独立 RPC detached
审查树 `/tmp/mam-4296391f-rpc-dd0914b`。两个交付树均干净，`mam job list --task` 无本任务 job。

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

## 现场只读核查与最小部署方案（同步前记录）

通过 `jx-4090-2-via-nx-aic` 完成授权范围内核查，未写远端、未传输模型、未碰 PM 状态。
当时远端普通 deployment checkout 均干净：

- `/home/xucuijie/Projects/robot-bridge`：`124049fb78d29db1d77d13a9fd4a4b698fcfe6e9`。
- `/home/xucuijie/Projects/openpi`：`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
- OpenPI venv：Python 3.11.15，`pip check` 通过；`openpi_client.memory_config` 和三个
  scheduler module 导入通过。PyYAML 6.0.2 已满足新源码唯一新增的 `PyYAML>=6.0` 依赖。

Policy Manager 的两个 wash 本地模型都为 `complete=true`、`syncing=false`、`instances=[]`；
同步 jobs 3/4 均为 `done`：

- `/home/xucuijie/Projects/openpi/checkpoints/wuwen-nx-aic/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000`
- `/home/xucuijie/Projects/openpi/checkpoints/wuwen-nx-aic/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000`

PM 当前已有 8949/GPU0 和 8950/GPU0 运行实例，未重启。它按整棵已同步的 bridge/OpenPI
checkout 与既有 `RB_PY` 启动 child，不能为单个 wash 模型选择独立源码或 venv；后续已按
独立 review PASS 将 bridge 同步到 `041405f`，保留现有实例。现在仍须由 Manager 在空闲端口/
确认的 GPU 新建 wash child，并把该 child 的 URL 作为 `RB_POLICY_URL`；不需要重复模型传输。

## 待现场/Manager 闭环

1. 独立 review 已 PASS，policy 主机 bridge 已同步到 `041405f`，OpenPI 保持 `a869`；现有 PM
   实例未重启。master/scheduler 和现场 launcher 的同 commit 同步仍是全链路前置条件。
2. 现场内网与负责人可用后，由 Manager 部署 full PM child、按 runbook 进行 UI/metadata/homing/
   受控动作检查，再在 full 通过后独立部署 serial。
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
