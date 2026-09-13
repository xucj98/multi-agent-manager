# HF 首 query 两样本方案：独立工程核查

## 结论

方案在冻结 C3 runtime 上可行，但应把捕获点改为 **scheduler 的 policy transport client 返回后、把相同 result 交还原 scheduler 之前**。这里能保存完整实际 RPC request（含 `cmd`、3 张 RGB、state、`memory_input_ids`、prompt 与 call timeout）和 post-wire `actions` H50，不需要触碰 Policy、input/output transform、JAX 或模型采样。

这只能验证“沿旧 BenchmarkRunner 的启动/重置入口、去掉现有模型内部诊断后，首 query 是否再现差异”。无论结果相等还是不同，都不能单独把原因归到 wrapper、启动顺序、cache/JIT、历史图像或真实采样 key。

## 冻结来源与已核对事实

- 只读核对 C3 `wuwen-4090-3:/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`。三库 clean HEAD 为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。
- 本任务的只读 bridge worktree 是 `/mnt/public/xcj/Projects/workspace/655416db-f379-4793-878d-b2538ad26d81/robot-bridge`，同一 `ffa1224`，clean；没有源码改动或交付 commit。
- C3 的关键冻结文件 SHA-256：`transport/websocket.py` `f0a2bc7a…b52f`，`scheduler/base.py` `e9d7a93a…2d9`，`scheduler/openpi_simulation.py` `c6f9eeb9…0ca5b`，`rmbench_sim_worker.py` `9dd98c40…98e94`，`benchmark/runner.py` `cc04aca0…62aa`。

## 最小接入点与一次采样合同

1. 在 `OpenPiSimulationScheduler(...)` 构造完成后，以 task-private transparent proxy 替换其 `_policy_client`；只观察第一个 `cmd in {"infer_audited", "infer"}`。构造阶段已有 metadata RPC，matched 协议的 `reset_episode_rng` 也应原样透传、均不计 action sample。
2. proxy 先调用原 client；仅在它 **正常返回后**，立即递归深拷贝 request 的所有 ndarray leaf、完整 scalar/bytes leaf 与 RPC kwargs，再深拷贝 `result["actions"]` H50。随后把未经修改的 `result` 返回原 scheduler。所有捕获文件、hash、shape、dtype、timeout、command、action-call ordinal 写 task 私有 receipt；H50 保留 float32 wire 数组。
3. 不能只保存 `policy_obs`：baseline request 的 `cmd` 在 `SchedulerBase._call_policy_infer` 才加入（`robot_bridge/scheduler/base.py:478-490`），matched baseline 和 shadow 都实际发送 `infer_audited`（`openpi_simulation.py:1514-1527`, `1551-1576`, `1613-1667`）。完整 request proxy 才能记录真实 request surface。
4. 这在当前冻结实现中是安全的：`WebSocketClient.call()` 在返回前同步 `packb(request)`、send、recv、`unpackb`（`transport/websocket.py:149-170`）；codec 对 ndarray 仅读取 `tobytes()`（`transport/codec.py:49-79`），没有对 request 的回写或异步 callback。`build_policy_obs()` 构造 state、3 张 RGB、prompt，再由 `MemoryContext.add_inputs()` 写入复制后的 `memory_input_ids`（`openpi_simulation.py:1119-1186`; `memory_context.py:264-309`）。不过必须立刻深拷贝，不能保留原对象引用到 iteration 结束。
5. 先在 RAM 中完成深拷贝，再让原 scheduler 继续；磁盘 hash/NPZ/pickle/`fsync` 放到首轮 `run_iteration()` 返回、queue 已 clear 之后。这样仍有一次必要的 post-RPC copy 开销，但没有旧工具的 pre-RPC I/O；不得拿该样本解释 execute latency 或实时控制表现。
6. proxy 同时计数 action request。正常路径要求 `count == 1`；任何第二个 action request 在发送前 fail closed。若 action RPC 发生 transport/capture 错误，是否已在服务端采样不可判定，receipt 必须标为 sample-ambiguous，不能自动 retry 或消耗第三个样本。

post-wire H50 的位置明确：policy server 对 `infer_audited` 返回 backend result（`policy/server.py:94-96`），OpenPI backend 已将 `actions` cast 为 float32（`policy/backends/openpi.py:358-370`），client proxy 接到的是 `unpackb` 后的 wire response。随后 `build_act_request()` 才复制前 K30 行给 robot（`openpi_simulation.py:1986-2039`），因此 H50 与实际 K30 可以分别留存，不再混淆口径。

## 原入口、execute 与 step 0 clear

- 保留旧 `BenchmarkRunner` 的 robot/policy 连续启动后 metadata handshake（`benchmark/runner.py:750-771`）、episode reset 与 `episode_context`（`595-646`）；继续让原 `apply_episode_prompt()` 从该已接受 reset 取 instruction 和 resolved `task_args`，不发第二个 reset（`scripts/run_scheduler.py:20-37`; `openpi_simulation.py:186-205`）。原 matched baseline/shadow YAML 都是 `move_steps=30`、`reset_episode_rng=true`；分别为 `rolling_mode=baseline` / `shadow`。
- task-private scheduler harness 只复用原 config/`apply_episode_prompt`/frozen scheduler，并执行一次 `_startup(); run_iteration()`。这保留首个正常 obs → reset_episode_rng → action RPC → execute 的原方法；它不能声称是完全无 wrapper 的 scheduler loop。当前 `run()` 的首轮也是 `_startup()` 后进入该 iteration（`base.py:577-648`）。
- **必须等整个 `run_iteration()` 返回后**才通过 robot client 发 `clear_actions`，而不是在 execute RPC wrapper 内 clear：baseline 的 `after_execute()` 还在 execute response 后运行（`base.py:550-564`），shadow 也要在 `_rolling_start_plan()` 完成 plan bookkeeping 后返回（`openpi_simulation.py:1660-1755`）。robot proxy 可在 execute 返回后复制实际 K30，但不清队。
- C3 simulation 的 `execute(..., blocking=False)` 只向 queue 追加 action，不调用 `_drain_to()`（`rmbench_sim_worker.py:181-195`）；`clear_actions()` 只清 queue（236-239）。所以不再调用 `get_obs` 的前提下，要求 clear response `dropped == 30`，再以 `get_episode_status`（无 drain，224-230）核验 `logical_step == 0`、queue 已空。这是 step 0 clear 的足够条件。

## 防止第二 episode、重试和额外 action query

- `BenchmarkRunner` smoke 固定 target 为 2（`runner.py:380-385`）。首轮 clear 后诊断 scheduler 应写完独立 receipt，再以明确的 diagnostic nonzero exit 结束。runner 会把 scheduler-before-terminal 记为失败（`501-540`），`_record()` 留下 episode 0 failure，`runtime_errors` 使 loop 在 episode 0 后退出，不会 reset/启动 episode 1（`433-472`, `546-650`）。结果 leaf 必须保留为 failed，绝不作为 smoke 或 formal 输入。
- 另有一个必须显式处理的分支：若 seed `100000` preflight 被拒，runner 默认 `seed += 1; continue`（`621-624`）。两样本合同应要求唯一 reset 为 `episode_id=0, seed=100000, accepted=true`；否则在启动 scheduler 前停止并保存 failed receipt，禁止悄悄进入 `100001`。
- rolling JSONL 的 `evidence_complete=true` 不代表正常 episode：writer 会对任意 outcome 写这个字段（`scheduler/rolling_evidence.py:117-136`），validator 不检查 outcome（RMBench `script/eval_diagnostics.py:741-759`）。receipt 必须明确 `bounded_first_query`，而 benchmark leaf 的失败状态才是准入边界；正式 smoke validator 还要求两条正常 accepted rollout 且 status=completed（`762-825`）。

## 当前诊断工具不能复用的部分

现有 `diagnostic_first_query_scheduler.py` 在 RPC **之前**保存输入并 monkey-patch scheduler methods（`132-173`）；`diagnostic_policy_server.py` 又 patch `Policy.infer`、input/output transforms、`jax.random.split` 与 episode RNG（`102-308`）。它不满足本次“post-RPC、无模型/JAX内部插桩”的合同。`run_first_query_diagnostic.py` 还先启动并握手 robot、后启动 policy（`355-379`），并新增 JAX/WARP/CUDA cache 路径（`257-270`），而旧 BenchmarkRunner 是两服务先启动、再 handshake。新两样本应使用正常 `scripts/run_policy_server.py` 和旧 BenchmarkRunner 外层，不使用这些工具或 replay。

## 可支持和不可支持的结论

- 若新两臂完整 request 相同而 H50/K30 仍不同：可证明该冻结入口下、无模型内部插桩时仍能复现首 query 差异；不能从两样本区分 scheduler harness、启动/缓存/JIT/timing 或未保存历史条件。
- 若完整 request 不同：可定位本次两臂的 policy 输入在 RPC 前已不同；不能倒推旧 artifact 的缺失 RGB/prompt/token/transform tree。
- 若完整 request 和 H50/K30 都相同：仅说明这两个受控样本未复现，不能证明历史失败由 wrapper 造成、也不能撤销旧前 30×14 差异。
- 本次不观测真实 PRNG key，不把 stream/call 计数称为 key；历史缺少完整 RGB、完整语言/transform 输入、实际 key 和 shadow H50 tail 的不可观测缺口仍在。

## 验证与范围

完成只读静态核查：C3 三库 HEAD/clean 状态、frozen transport/RPC/scheduler/controller/runner 源行、现有 task-private tool source 与旧 command receipt。未运行 GPU、模型、reset、轨迹、replay 或训练；未改 C3 runtime、作者树、共享 cache 或生产源码。没有长进程或 MAM job。
