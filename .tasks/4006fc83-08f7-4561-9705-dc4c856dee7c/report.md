# 高频状态 / replan 冻结代码独立审查

审查任务最新发布版本：`1e6d38efc7b1944201f5293aa467481b3cb326cb`（在
`71797867c4a2226ff06d7e7b35fcd13bfd051948` 的冻结审查要求上追加正式 RNG 对照裁决）。
本报告按源任务最新已发布准入要求 `93106894ecc53165ecb828ca247842fbb2a80489` 审查以下
冻结交付，不包含之后的任何作者修改：

- OpenPI：`4529a91c1f49a50c8710a7182e31ca5a32dfa05a`（基线
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`）
- robot-bridge：`53f853aa71b80a7eadd9fb3092abe39c64df1149`（基线
  `f9626636c4776d8eb15f9c556775cb2d12c000e5`）

两个独立 review worktree 均为上述精确 HEAD、无未提交修改；两个完整交付 diff 的
`git diff --check` 均通过。

## 结论：不准入 GPU smoke

冻结代码有两个 P1 准入阻塞项。它们修复并以新的精确提交重新审查前，不应启动 GPU
smoke、仿真正式评测、训练或部署；本报告也不把 CPU 检查表述为评测完成。

### P1：默认关闭路径改变跨 episode 动作 RNG、返回协议和开销

旧 OpenPI `Policy` 没有 `reset()` 覆写，旧 `OpenPiBackend.reset()` 是 no-op
（`robot_bridge/policy/backends/openpi.py:349-360`，旧 bridge）。冻结代码中：

- `Policy.reset()` 把 `_rng` 和 `_probe_rng` 恢复到初始 key
  （`openpi/src/openpi/policies/policy.py:278-294`）；
- OpenPI backend 转发该调用（`robot_bridge/policy/backends/openpi.py:388-394`），server
  分发 `reset`（`robot_bridge/policy/server.py:74-95`）；
- scheduler 在首次推理前及每个 offline `ep_init` 后发送该命令
  （`robot_bridge/scheduler/base.py:244-265, 519-533`）。

因此这不是仅在显式 high-frequency 模式下发生的变化。benchmark 每个 episode 启动新的
scheduler 子进程，但复用 policy 服务（`robot_bridge/benchmark/runner.py:475-480`），故默认
baseline 的下一 episode 会重新使用首次采样 key，而历史基线会继续其 action RNG 流。

Reviewer 在 CPU 上用当前真实 `Policy` 的 transform、`jax.random.split` 和 output 路径，配合
固定的 JAX joint model 做了 `infer; reset; infer` 与连续两次 `infer` 对照。前者的首个与
reset 后动作逐元素相同，reset 后动作与连续第二个动作不同；相应 action RNG key 分别为
`[1057776146, 3759860600]` 和 `[1224654690, 3373883985]`。这直接复现了默认路径的
随机流变化，而不是仅比较新版 baseline/shadow。

此外，`Policy.infer()` 对每个 JAX 请求无条件返回 `policy_rng`
（`openpi/src/openpi/policies/policy.py:154-158`），并对每个 joint-dense Memory-v1 请求复制并
返回 `memory_raw_actions`（`:130-153`）。这同样改变默认返回 payload 和增加未请求的复制开销。

按 Manager 最新正式对照裁决，普通 baseline/shadow 必须保持历史 no-op reset 与连续 action
RNG；只有显式 HF、matched baseline 和 matched shadow 使用每 episode 恢复 initial key0 的协议，
且 probe stream 独立。matched baseline 仍为原 K30/MemoryContext、无中途 probe；matched shadow
有 probe 但不更新 cache 或动作。冻结版本没有该按模式划分的接线，故不能证明这些对照的跨 episode
动作/key 等价。审计 sidecar 及其开销也必须仅在明确审计/高频请求时启用，普通 `infer` 的返回字段和
开销保持历史合同。

### P1：HF 审计证据没有随 benchmark episode 持久化

冻结合同要求有界地保留 raw/decoded forecast、RNG stream/call、cache consumption、触发/清队列
证据和绝对 target 对齐。实现确实在 scheduler 内生成这些内容，但只保存在
`_rolling_traces = deque(maxlen=64)` 中（
`robot_bridge/scheduler/openpi_simulation.py:242-252, 1096-1121, 1150-1237, 1280-1332`），
且唯一导出是 `get_status()` 的 control-API 快照（`:1553-1593`）。仓库中没有将该 rolling trace
写入 result recorder 或 episode artifact 的路径。

这无法满足 benchmark 的事后审计：runner 每个 episode 启动 scheduler 子进程
（`robot_bridge/benchmark/runner.py:475-480`），等待期间只查询 robot 的
`get_episode_status`，结束时只取 robot 的 `get_obs()` diagnostics
（`:425-468`），再由 `_record()` 写入 episode 结果（`:386-396`）。它不会查询 scheduler
`get_status()`。而 benchmark 启动的 `scripts/run_scheduler.py` 默认将 `control_port=0` 转为
`None`（`:48-64`），所以控制 API 本身也不可用；scheduler 退出后内存 deque 被销毁。

结果是 HF-J 的 raw/decoded forecast、实际 RNG 证据、target 对齐、trigger 和 clear 的证据不在
run 产物中，无法在之后审计或支撑实验结论。修复需要在每个 episode 退出前将有界 trace 持久化到
结果目录，并由 benchmark episode record 包含该工件或其完整引用；仅保留进程内 control 状态不够。

## 已核对且符合冻结合同的代码路径

除上述阻塞项外，冻结实现的以下关键合同路径与代码相符：

- J cache consumption 使用 `row = current - latest_source - 1`，并记录相同的绝对 target；
  `a+25` probe 的 row 4 可用于 `a+30` 边界（
  `robot_bridge/scheduler/openpi_simulation.py:1096-1121`）。
- event 比较固定原计划的 `reference_ids[d:d+3]` 和 fresh `ids[:3]`，记录同一绝对
  target；触发仅清未执行后缀，并以正常 `infer` 重规划，未使用 probe actions
  （`:1182-1237, 1336-1365`）。
- HF-J 不调用标准 `MemoryContext.accept()`，避免旧 pending chunk 在完成或 clear 后覆盖 rolling
  lifecycle（`:1312-1330`）；duplicate/stale/gap/invalid 观测在 probe 前打断 streak 并短路
  （`:1042-1094, 1405-1426`）。
- S 仅接受 `hf_fixed`，用 prefix-only state probe 更新 cache，并在 action boundary 只做一次
  full infer（`:394-412, 1123-1180, 1428-1444`）。T 或混合 target 在启动时拒绝。
- high-frequency 模式拒绝会因额外 `get_obs` 改变 RMBench RNG 的 random-light 配置
  （`:653-687`）。

这些通过项不抵消两个 P1，也不代表默认 baseline 等价已经成立。

## CPU 验证

在独立 worktree 完成，未使用 GPU：

```text
robot-bridge:
PYTHONPATH=<review-bridge>:<openpi-client> .venv/bin/python -m pytest -q \
  tests/scheduler/test_openpi_rolling.py tests/scheduler/test_memory_context.py \
  tests/policy/test_openpi_metadata.py tests/robot/test_server_dispatch.py \
  tests/benchmark/test_runner.py
60 passed in 1.78s

OpenPI:
JAX_PLATFORMS=cpu PYTHONPATH=<review-openpi-src>:<openpi-client> .venv/bin/python -m pytest -q \
  src/openpi/policies/policy_probe_test.py src/openpi/models/pi0_probe_test.py \
  src/openpi/training/memory_data_test.py \
  -k 'probe or policy_full_memory_wire or policy_serial_memory_wire'
8 passed, 8 deselected in 10.35s
```

上述测试覆盖 CPU wire、probe、rolling 和 runner 的局部合同；它们没有覆盖真实 GPU model rollout，且
当前 P1 结论已使该后续验证不准入。

后续作者修复必须提供新的干净 OpenPI 和 robot-bridge commit；需要对新精确版本重新进行默认关闭
跨 episode、审计工件持久化及相关 CPU/GPU 准入审查。
