# 独立验收：live S2M 小修通过，现场部署入口阻塞

## 准入意见

- **`a5caa5b` live S2M 代码：CPU 准入 PASS。** 14 维 native S2M、K30、full/serial
  的反馈时机，以及 live / takeover / offline 一致性都有实证。
- **`0a33dd1` 部署说明与其现有启动命令：现场准入 BLOCK。** 在修正 policy-pane 的
  跳过条件并补回归前，不应按 `wash-cup-memory.md` 同步或执行现场启动；它可能另起一个
  手工 policy server 并占用 GPU，违背文档承诺的 Policy Manager 共存行为。

## 关键阻塞（最小修复方向）

`docs/tutorials/wash-cup-memory.md:41-58` 要求从 Policy Manager 卡片复制一个新的
`RB_POLICY_URL`，并断言 policy pane 会输出 `[skip]`。但
`scripts/launch/x1pro_takeover.sh:58` 始终启动该 pane，而
`scripts/remote_server/run_policy_server.sh:30-35` 在 **远端** 只探测
`${RB_POLICY_PORT:-8000}`；命令既不读取也不转发本次选择的 `RB_POLICY_URL` 端口。

这不是同一个对象。Policy Manager 的实例端口由 `RB_POLICY_PORT` 基准向上动态分配
（`docs/design/policy-manager.md:250-260`）；源任务已发布报告记录的在运行实例也位于
8949/8950。若选中的 wash child 是另一空闲端口而基准端口未监听，policy pane 不会
skip，会按旧 `RB_OPENPI_POLICY_DIR` / `RB_POLICY_GPU` 启动手工 server。反之，基准端口
上碰巧有其他 manager child 时又会 skip，无法证明它对应本次 `RB_POLICY_URL`。

建议只做窄修补：让 x1pro takeover 的 policy pane 明确按本次 scheduler 所用的 policy
URL/端口识别已由 Manager 托管的实例（或在该入口显式不启动 policy pane），并为“目标
实例端口与基准端口不同”的 skip 和“无托管实例时仍能手工启动”各加一条无 SSH/GPU 的
shell 回归；随后把 runbook 的命令与实际行为对齐。无需改 scheduler、controller 或
MemoryContext。

## 功能复核证据

- 两个真实 20k checkpoint 的 `metadata/train_config.yaml` 经 OpenPI
  `checkpoint_metadata.load_train_config`、`_runtime_metadata` 和 bridge
  `OpenPiBackend.get_metadata()` 重建出的 scheduler metadata，与新增 full/serial fixture
  逐字段相等：均为 native `s2m`、14D、15 Hz、H50、K30；full 是
  `chunk_completed`，serial 是 `query_selected`。
- `robot_bridge/scheduler/openpi.py:291-296, 376-387` 将新路径限制在
  non-projection Memory v1 native S2M，且要求 `robot_dim == slave_state_dim == 14` 和单个
  当前观测。`openpi.py:821-853, 943, 1032-1041` 不请求 master、输入 14D state、从
  `[0:14]` 取动作并以当前 slave 作为插值锚点；其余 SM2SM/projection 分支保持原条件。
- 新增真实 metadata scheduler 回归通过实际 `OpenPiScheduler`、
  `OpenPiTakeoverScheduler`、`OpenPiOfflineScheduler` 的 build/execute lifecycle，而非仅
  `MemoryContext`：三者输入、K30 动作和反馈一致。full 在 robot 接受后仍保持旧值，
  `completed=30` 后反馈 model index 29 / row 30；serial 在当前 query selected 后反馈。
  手工 memory、homing 和 takeover 都会丢弃 full 的 pending completion，既有 UDP takeover
  组也通过。

## CPU 验证

所有命令使用 `CUDA_VISIBLE_DEVICES=''`（metadata 重建另设 `JAX_PLATFORMS=cpu`），未加载
权重、未占 GPU、未连接现场或发送机器人动作。

```text
robot-bridge/openpi worktree_env_smoke.py                         PASS
pytest memory/live/takeover/transform groups                      51 passed, 1 skipped
pytest offline controller + launcher preflight                    35 passed
真实 full/serial metadata -> backend metadata -> fixture 比较      PASS
ruff --select E,F,I（变更 scheduler/test）及 git diff --check     PASS
bash -n x1pro_takeover/run_policy_server/run_scheduler             PASS
```

最后一项只验证 shell 语法；部署 blocker 来自对实际启动路径和 Policy Manager 端口语义的
静态交叉审阅，未连接任何现场 SSH 目标或进行现场试运行。

## 工作区与收尾

- robot-bridge：`/mnt/public/xcj/Projects/workspace/3b678966-7bf3-48f2-b462-920f9cc6a33f/robot-bridge`，
  `task/3b678966-7bf3-48f2-b462-920f9cc6a33f`，干净，HEAD
  `0a33dd19ab911ae3808c3ff141e3fd0603c22594`（审阅功能提交
  `a5caa5b57e96fd02de7d6df0cd2ffa5bf0030f5f`）。
- openpi：`/mnt/public/xcj/Projects/workspace/3b678966-7bf3-48f2-b462-920f9cc6a33f/openpi`，
  `task/3b678966-7bf3-48f2-b462-920f9cc6a33f`，干净，HEAD
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
- 已清理本次 `/tmp/mam-3b678966-*` pytest / ruff 缓存；无登记 job。
