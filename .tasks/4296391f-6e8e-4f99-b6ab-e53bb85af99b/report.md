# 最新交付：bridge 本地 Memory v1 schema（待独立 review）

## 准入结论

bridge 候选提交为 `3906dd0032637410359be6dd5006b3f793f3191c`
(`fix(memory): ship bridge-local schema runtime`)，位于
`/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/robot-bridge`
的 `task/4296391f-6e8e-4f99-b6ab-e53bb85af99b` 分支。可交 reviewer
Bernoulli 独立复核；**尚未合入、push 或部署**。

OpenPI 保持干净且未修改：
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。bridge 的
`robot_bridge/memory_config.py` 与该 OpenPI 提交的
`packages/openpi-client/src/openpi_client/memory_config.py` 均为 SHA-256
`6287bddad81cd635556ef6b0b75b3abd64248289d74f101e1fa3a07db176aa80`，`cmp` 一致；
因此本次没有改动 parser、样本构造、编码、mask 或 feedback 算法。

## 变更范围

- bridge 新增本地纯模块 `robot_bridge.memory_config`；scheduler、policy metadata 注释和
  offline controller/测试改为直接导入它，不再导入 `openpi_client`。
- 删除仅为 scheduler 安装 `openpi-client` wheel 的脚本及隔离 wheel 测试。
- 新增本地 schema 行为回归，并以真实 wash full/serial 20k metadata 构建
  `MemoryContext`；文档收敛为 WSL checkout → 配置 `RB_*` → `push_code.sh auto` →
  `x1pro_takeover.sh` → `:8088`，不要求手工 wheel。

## CPU 证据

全部使用 `CUDA_VISIBLE_DEVICES=''`，未访问远端、未加载模型、未占 GPU、未发真机动作：

```bash
env -u PYTHONPATH PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES='' \
  .venv/bin/python -m pytest -q \
  tests/test_memory_config.py \
  tests/scheduler/test_memory_context.py \
  tests/scheduler/test_memory_v1_schedulers.py \
  tests/scheduler/test_openpi_takeover.py \
  tests/robot/controllers/test_memory_v1_offline.py \
  tests/launcher/test_offline_preflight.py \
  tests/launcher/test_x1pro_takeover_launch.py \
  tests/policy/test_openpi_metadata.py
# 109 passed in 24.53s
```

同一 bridge venv 中 `importlib.util.find_spec('openpi_client') is None`；在该条件下，真实
full（action_rows，H50/K30）与 serial（query，H50/K30）metadata 均成功创建
`MemoryContext`，写入初始 `memory_input_ids=[0]`，且未加载 JAX、Torch、OpenPI 或硬件 SDK。
`bash -n scripts/utils/push_code.sh scripts/launch/x1pro_takeover.sh` 与
`git diff --check` 通过。

本机完整 Ruff 会对逐字复制的上游模块和既有 offline 文件报告已有的宽规则风格项；为保持与
`a869` 的算法副本字节一致，本次没有为消除这些项改写源文件。这不是 CPU 行为准入阻塞，供
reviewer 按仓库基线确认。

## 后续

独立 review PASS 后再由 Manager 合入并发布同一 bridge commit，现场才可按已有
`push_code.sh auto`/TUI 流程同步。当前不得据此声称已部署或真机全链路就绪。

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

## 09:41 8951 EOF 来源定位与最小处置

### 已证实的来源与周期

本 task **没有**使用 `nc`、`telnet`、`curl` 或其他裸 TCP 探活，也没有保留任何
8951 的循环/后台探测。为 policy-only 验证而执行的访问均是在 policy 主机上由
`websockets.sync.client.connect(..., proxy=None)` 发起的有限次完整 WebSocket 请求：一次
metadata + 合成 infer + log 读取，一次 metadata/log 读取；二者均已退出。有效 infer 返回
`actions=(50,14)` `float32`、有限值，以及 `memory_prediction_ids=(50,1)` `int32`、范围
`[1,5]`。任务早期还有一次使用现有 `WebSocketClient` wrapper 的短暂 WebSocket smoke；它
未显式禁用 shell proxy，已停止，且不是裸 TCP 或持续进程。

用户报告的 `2026-09-11 01:33:19.121 UTC` 不是上述一次性验证：8951 的本地 child log 显示它
处于持续模式，01:32–01:34 期间约每 5.4 秒出现一对 EOF，两个 EOF 相隔约 1 秒。该序列在本任务
停止主动 8951 请求后仍在 01:39–01:41 持续出现。

在 policy 主机上以只读 `/proc/net/tcp` 每 50 ms 采样 48 秒（01:40:42–01:41:30 UTC）时，唯一
观测到的非监听 8951 对端为：

- `10.10.2.82 -> 10.10.4.22:8951`；01:40:44 见 `TIME_WAIT`（源端口 42514），01:40:53 见
  短暂 `CLOSE_WAIT`（48770），01:41:10 见 `ESTABLISHED`（34582；server PID 2264677）。
- 同一窗口 child log 继续报 `opening handshake failed` / `EOF before HTTP request line`，并从
  01:41:16 起记录多次实际推理的 `state` 形状 `(1,32)` 与 wash 模型 14 维归一化参数不匹配。

因此已确认观测到的持续连接源为 **10.10.2.82**，目标为 policy 主机 **10.10.4.22:8951**；它不是本 task
或 policy 主机本地 PM readiness probe。由于按授权没有探测该对端，不能从这台机器断言 10.10.2.82
是否为 master、WSL 或其他现场主机。policy 主机也无法从远端 TCP 连接反查该对端上的具体进程；本 task
没有连接、停止或修改该机器。尝试的 24 秒 `tcpdump` 因当前账户没有抓包权限而被内核拒绝
（`Operation not permitted`）；`/proc` 采样提供了上述源/目的与状态证据。

### 已排除的旧 PM health check

长期运行的 Policy Manager 为 PID 3646，8951 child 为 PID 2264677。实际 PM log 记录 child 于
01:25:30 UTC `Policy server ready on port 8951`，当前 PM status 仍为 `running`、`error=null`。
其运行代码的 `PolicyInstance._monitor` 只在 `state == "starting"` 时每 2 秒经
`127.0.0.1:8951` 发一次 `get_metadata` readiness probe；转为 `running` 后只轮询 child 是否退出，
不再连接 child。因此它不能产生 01:33 之后的持续 EOF。没有重启 PM、8951 或任何其他实例。

### 最小处置与现场影响

无需改动或重启 policy server。10.10.2.82 的负责人应先找到指向 `10.10.4.22:8951` 的旧客户端/
探活任务并停用或改正：健康检查必须完成真实 WebSocket 握手，推理客户端必须使用 wash native
s2m 的 14 维 state 与 Memory v1 输入，不能发送 32 维旧格式请求。该来源未清除前，不应把 8951
交给现场 scheduler，以免无效请求持续占用 child、淹没日志或与现场请求竞争。

8951 本身仍在 `0.0.0.0:8951` 监听，PM full child 的 PID/GPU/模型/metadata 与本报告先前部署记录
一致；本 task 的正确格式 policy-only smoke 已通过。待 10.10.2.82 的无效来源处理完，由现场同事按
既有 `RB_POLICY_URL=ws://10.10.4.22:8951` 和
`bash scripts/launch/x1pro_takeover.sh --skip-policy` 继续，不由本 task 探测或操作 master/WSL/机器人。

# 现场操作移交：远端操作已停止（最新用户指令）

> 本节覆盖此前“继续远端同步/重启”的执行计划。收到撤回后没有再发起任何远端
> 写入、重启或配置修改；两条 SSH 会话已退出。**远端状态最后只读观测截至
> 2026-09-11 10:05:35 CST**（该时刻为此观测记录的发布截止）；之后没有再次 SSH、
> 刷新服务状态或探测端口，因此下表不应被当作当前实时状态。

## 已实际完成的改动与最后状态

| 机器 | 已实际完成 | 最后确认的 commit / 服务状态 |
| --- | --- | --- |
| policy 主机 `10.10.4.22`（`jx-4090-2-via-nx-aic`） | bridge 已精确同步到 `041405f0b35b2a173ac3461d297a43141d028026`；OpenPI 保持 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；已部署的 wash full PM child 未被重启 | PM PID `3646`；wash full PID `2264677`，GPU 1、`:8951`；既有 child PID `1249503`（`:8949`）和 `2140250`（`:8950`）仍监听。MAM 长服务登记为 `9f91cf1c-8505-48e3-bd6e-cc7e8093a914`。 |
| 主臂 / scheduler `10.10.2.82` | **没有**同步代码、重启服务、修改 `~/.robot_bridge_env.sh` 或启动 scheduler；只读检查后已断开 SSH | repo `/home/xr/Projects/robot-bridge` 当时为干净的 `b2faa820e49138b839455ba7469245414914ce40`，且尚无 `041405f` git object。`rb-launcher.service` 为 active/running，PID `1995`，监听 `:8200`；未见 `rb_master`、`rb_robot`、`rb_scheduler` tmux session 或 `:8088/:9946/:9948` listener。硬件原生进程未碰：此前观测为 x2robot realtime PID `3452`、`robot_log` PID `3468`。 |
| 从臂 `10.10.2.96` | **没有**执行远端命令、代码同步、重启或配置修改；只成功完成 SSH 登录并立即退出 | hostname 为 `xr-msi-ex001-65`；repo、commit、服务 PID 与环境尚未读取，不能据此声称从臂已就绪。 |

没有在任何现场机器使用 `x1pro_takeover.sh --skip-policy`；没有因撤回而重启任何服务。

## launcher 与 policy 端口事实

实际 `.82` 入口是 systemd user unit `rb-launcher.service`：

```text
/home/xr/Projects/sdk_robot/.venv/bin/python scripts/run_launcher.py --config configs/launcher.yaml
```

它是 GUI launcher，管理 `rb_master`、`rb_robot`、`rb_scheduler` 三个 tmux 服务；**不**管理
policy pane，也不调用 `run_policy_server.sh`。`x1pro_takeover.sh` 是并列的 shell 入口，现场只应选择
其中一个，不能与 GUI launcher 同时使用。

最后只读得到的相关设置如下：

| 位置 | 值 | 实际用途 |
| --- | --- | --- |
| policy 主机 `~/.robot_bridge_env.sh` | `RB_POLICY_PORT=8949` | Policy Manager 的端口基准；legacy `run_policy_server.sh` 的本地端口占用预检读取它。 |
| `.82` `~/.robot_bridge_env.sh` | `RB_POLICY_URL=ws://10.10.4.22:8951` | wash full PM child 的 scheduler 目标。该文件没有 `RB_POLICY_PORT`。 |
| GUI launcher 传参 | `Settings.read(~/.robot_bridge_env.sh)` → `launch_env_from_settings()` → `RB_POLICY_URL` | launcher 的 `_base_env()` 会剥离启动器继承的 `RB_*`，只把设置文件读出的 URL 显式传给 `run_scheduler.sh`；后者以 `--policy-url "$RB_POLICY_URL"` 启动 scheduler。 |

因此 `8949` 与 `8951` 的数值**确实不同**，但在当前 GUI launcher 的实际执行路径中不存在
`RB_POLICY_PORT` → policy 启动 / 跳过这一环，也没有把 `8949` 传给 scheduler；scheduler 的已配置目标
是 `8951`。这不是 GUI 路径中的功能性端口不一致。若现场改选 shell 入口，才会触发 legacy
`run_policy_server.sh`：它仅预检 policy 主机的 `8949`，而 scheduler 仍使用 `8951`；现场应把这两项
分别视为“既有 PM 占用保护”和“wash full 实际目标”，不要把前者当作后者的健康判定。

## 留给现场同事的未完成步骤

1. 先选定一个入口：保持 GUI launcher，或在完全停止其同一套服务后改用
   `x1pro_takeover.sh`；不得并行使用两者。
2. 若选择 GUI launcher，先在 `.82` 与 `.96` 各自核对 repo、私有环境、现有控制进程和 git 状态；
   再按现场流程同步 bridge 至 `041405f0b35b2a173ac3461d297a43141d028026`，保留 ignored 的 SDK、venv、模型和私有环境。OpenPI 的固定目标为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
3. 每台机器用其既有 `RB_PY` 做 CPU-only import；确认 `.82` 的
   `RB_POLICY_URL` 仍为 wash full `ws://10.10.4.22:8951`。GUI 路径无需新增 `.82`
   `RB_POLICY_PORT`，也没有证据表明必须使用 `--skip-policy`。
4. 仅在现场明确决定更新 GUI 进程时，重启其既有 `rb-launcher.service`；该 unit 的注释说明
   restart 不会停止它已创建的 tmux 子服务。不要由此自动启动 scheduler、homing、execute、UDP action
   或 autonomous；先确认各服务 idle / takeover 状态。
5. 在 scheduler 真正启动后，以其日志和 metadata 核对 14D native S2M、15 Hz、H50、K30 与
   `ws://10.10.4.22:8951`；这一步和真实机械臂动作验收仍由现场人员完成。

policy 侧 full child 的 policy-only smoke、14D / 15 Hz / H50 / K30 metadata 已通过，但不能替代
`.82/.96` 同 commit、CPU import、scheduler 连通或真机安全验收。

## 当前现场手册（替换旧 runbook）

现场操作手册已在独立 bridge 交付树提交为
`cf7ffdb714232ad8555b85325e79b705eb18cbd6`
（`docs(wash): make GUI launcher the current field guide`）：

- [wash-cup-memory.md](../../workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b/robot-bridge/docs/tutorials/wash-cup-memory.md)
  现在只描述实际 `rb-launcher.service` GUI 流程、full `:8951`、GUI `:8200`、control UI `:8088`
  与 serial 的后续独立切换。
- 已删除旧 `a5caa5b` / `124049f` 版本叙述、“两个模型都未部署”、强制 `--skip-policy` 和
  shell/TUI 作为当前入口的描述。
- 文档明确 GUI launcher 与 `x1pro_takeover.sh` 是并列入口，不能同时使用；GUI 不调用
  `run_policy_server.sh`，并显式把环境文件中的 `RB_POLICY_URL` 传给 scheduler。

本次仅修改本地文档和 MAM report；远端停止指令后没有再执行 SSH 命令、代码同步、服务重启或配置写入。

## 当前现场手册改为 TUI（取代上一版 GUI 手册）

最新用户明确调试入口为 `scripts/launch/x1pro_takeover.sh`。因此当前有效文档提交为
`63bbd809b8261475f8ed2096f5dce7d1442bdf07`
（`docs(wash): provide TUI field update procedure`），取代此前仅描述 GUI 的 `cf7ffdb`。

手册现在给出可复制的现场步骤：

1. 保留 `rb-launcher.service` 常驻，但先通过 GUI 的正常“停止全部”或现场既有正常停止路径
   释放已知 `rb_master`、`rb_robot`、`rb_scheduler`，避免 TUI 重用旧代码的会话；不停止未知
   tmux、硬件 SDK 或 Policy Manager。
2. 主臂和从臂以现场变量指定路径与解释器，从已更新 policy 主机 Git 的 `HEAD` 先校验精确为
   `041405f` 再 fetch/reset；不假设 GitHub 有该 commit，也不执行 `git clean`。`.96` 的 repo/
   interpreter 仍明确留给现场填写。
3. 主臂 CPU-only 导入 scheduler、PyYAML 和 `openpi_client.memory_config`；仅在该轻量包缺失时，
   从 policy 主机的固定 OpenPI `a869` 构建审核 wheel，并以已有
   `scripts/deployment/install_openpi_client.sh --no-deps` 安装。PyYAML/NumPy 缺失是阻塞报告点，
   不从公共索引安装同名包，也不安装完整 OpenPI/模型。
4. TUI shell 校验既有 `RB_*` 拓扑后运行默认
   `bash scripts/launch/x1pro_takeover.sh`。原 policy pane 按 policy 主机的 `RB_POLICY_PORT`
   进行已有端口 skip；scheduler 独立采用 `RB_POLICY_URL`。`--skip-policy` 非必需且本流程不使用。

GUI 与 TUI 是并列启动入口：GUI daemon 可以共存，但同一时刻只有一个入口启动那组三项服务。
本次仅修改本地文档与报告；没有恢复或新增远端 SSH、代码同步、服务重启或配置写入。

## TUI 环境刷新增量

当前文档新增提交 `dfc9e1095badd7f37d9260d3275df3cca2700d90`：启动默认 TUI 前先检查并
`export` `RB_POLICY_SSH`、`RB_ROBOT_SSH`、`RB_MASTER_SSH`、`RB_SCHEDULER_SSH`、
`RB_POLICY_URL`、`RB_ROBOT_URL`、`RB_MASTER_URL`；已有 tmux server 时逐项执行
`tmux set-environment -g`，新 server 则继承 export 后的环境。这防止默认 TUI 路径在旧 tmux
全局环境中取到陈旧 URL/SSH target。

同时删除 `RB_PY="$RB_PY"` 的无意义自赋值，bridge 路径改用
`git -C "$BRIDGE_DIR" rev-parse --is-inside-work-tree`，支持 `.git` 为 worktree 文件。
仅文档变更，`git diff --check` 通过；未进行远端操作。

## 交接等待状态与本地清理

- 远端服务状态的最后只读观测截止已明确为 **2026-09-11 10:05:35 CST**；其后未做
  SSH、代码/配置写入、服务重启或端口探测。
- 2026-09-11 10:20:28 CST 本地 MAM 登记仍显示 full PM 长服务 job
  `9f91cf1c-8505-48e3-bd6e-cc7e8093a914` 为 `running`。这是登记状态，不构成新的远端
  健康检查；该 job 和本 task 均保留供现场交接，不 archive、不 stop。
- 已清理本 task 的 `/tmp/mam-4296391f-*` SSH 临时 known-host 文件。两个 task worktree
  除 `.venv` 外未发现可清理的 pytest/ruff/Python 测试缓存；`.venv`、模型和环境均保留。

# 依赖随 push_code auto 自动交付的最小方案（待 Manager 裁定）

## 推荐结论

采用随 robot-bridge 精确版本交付的、审核过的 openpi-client wheel artifact，并让
scripts/utils/push_code.sh auto 在正常 rsync 完成后，只对 RB_SCHEDULER_SSH 的既有
scheduler RB_PY 做幂等安装与 CPU import 检查。

artifact 从固定 OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 的
packages/openpi-client tree 243a6c6fd7fe840aea9a922f7309026d8aba9bb8 构建，连同
JSON manifest（OpenPI commit/tree、wheel SHA-256、memory_config.py SHA-256）提交到
bridge 的受控 artifact 目录。它是同一份 OpenPI schema 实现的不可变发布物，不在 bridge
复制或维护第二份 memory_config.py。

这满足现场固定链路：

    WSL bridge checkout → 配置 RB_* → push_code.sh auto
      (rsync bridge + scheduler 自动 ensure) → x1pro_takeover.sh → :8088

WSL 不需要相邻 OpenPI checkout，现场不需要手工构建、传输或执行 wheel 安装，也不从
公共索引按同名 openpi-client 解析。

## 为什么选此方案

- 当前 push_code.sh auto 只去重四个 RB_*_SSH 后 rsync bridge，明确排除 .venv；因此仅在
  pyproject.toml 声明依赖、或保留现有手工 install_openpi_client.sh，都不能进入日常交付链。
- MemoryContext 仅在 checkpoint 有 memory_config 时导入 openpi_client.memory_config。该模块
  直接只需要 NumPy/PyYAML，现有 scheduler runtime 应提供它们；不需要 OpenPI 训练树、JAX、Torch 或模型。
- 公共索引已有同名旧包，且当前 package version 都是 0.1.0，名称/版本不能证明 schema 来源。
  manifest 的 artifact 和模块内容 hash 才能拒绝错误同名包。
- 现有 scripts/deployment/install_openpi_client.sh 已有正确的 --no-deps、路径安装和
  MemoryContext smoke，可复用为 mismatch 时的实际 installer，而无需新建通用环境管理框架。
- 已有 scripts/tests/local/test_openpi_client_wheel.sh 可作为 artifact 发布门禁：它从审核
  OpenPI tree 构建 wheel，在干净 venv 实际创建 MemoryContext，并证明没有 OpenPI/JAX/Torch。

## 最小实现边界

1. 在受控发布机（不是现场）从 clean 的 OpenPI a869 package tree 生成 wheel 和 manifest；
   发布前运行既有 wheel 隔离测试。只有 packages/openpi-client tree 改变时才重新发布 artifact。
2. push_code.sh auto 保持现有 rsync host 集合和排除规则。scheduler host rsync 成功后，
   以远端 login shell 中的 RB_REPO/RB_PY 调用一个窄 ensure_openpi_client.sh：
   - 先检查 wheel manifest、RB_PY、pip、NumPy/PyYAML，以及已安装
     openpi_client.memory_config 的来源/内容 hash；
   - 已匹配则不运行 pip；
   - 缺失或错误同名包才从刚 rsync 的本地 artifact 用
     pip install --no-index --no-deps --upgrade --force-reinstall <wheel> 安装，
     再复用现有 MemoryContext smoke；
   - scheduler target 不可达、RB_PY/pip/基线 NumPy/PyYAML 缺失、或安装后仍不匹配时，
     push_code auto 非零退出，不进入 TUI。
3. policy、从臂、仅 master-server 的机器只得到原有 bridge rsync；不对它们 pip install，
   不触碰 PM、模型、GPU、服务或 robot SDK。若 master 与 scheduler 同机，仅执行一次。
4. 不在 pyproject.toml 裸写 openpi-client 名称依赖：这会重新引入公共同名包风险，
   且 rsync 后也不会自动执行 pip。artifact manifest/ensure hook 是本部署路径的明确、
   固定来源声明。

## 一次性前置与每次开发循环

一次性前置仅是发布审核 wheel+manifest，并确保 scheduler 的既有 SDK venv 有 pip、
NumPy、PyYAML；缺少这些时应修正其标准环境 provisioning，而不是让现场临时找 wheel。
当前本地 bridge .venv 本身没有 pip，不能据此推断现场 RB_PY 状态，需在实现的
fake/现场受控验收中确认。

日常循环不增加人工依赖步骤：WSL checkout 自带 artifact；push_code auto 在缺失/
hash 不符时自动补齐，第二次运行不重装；随后仍按现有 TUI 与 :8088 入口启动。

## 必要验收

- 只有 bridge checkout、没有相邻 OpenPI checkout 时，artifact install + scheduler
  MemoryContext CPU smoke 通过。
- scheduler RB_PY 缺 client、或装有同名旧包/相同 0.1.0 但 hash 不符时，自动替换；
  不访问 package index，也不出现 OpenPI/JAX/Torch。
- policy/robot/master-only targets 不执行 pip；scheduler 与 master 同机时仍只一次。
- 第二次 push_code auto 不执行 pip。
- 已有 tmux server 的全局旧 RB_* 不影响 ensure：远端 helper 以 fresh login shell 的
  机器私有环境解析 RB_REPO/RB_PY。已存在 rb_scheduler 服务则不得被 auto kill/restart，
  也不得声称已运行新代码；应以明确的 handoff/preflight 状态阻止把旧服务误当作更新完成。
  该服务交接边界与依赖安装分开实现。
