# formal 首次 `get_obs` 30 秒超时：定位与最小修复

## 结论

已证实的公共运行故障是**状态探测与长 `get_obs` 共用 RMBench controller 的串行 worker RPC 锁**：scheduler 的首次 `get_obs` 已在 controller 内等待时，benchmark runner 另一个 WebSocket 连接发出的 `get_episode_status` 仍会排在同一锁后面。两端 client 都是 30 秒预算，故三次被 runner 错标为 `robot_status_transport_error`，另一次先观察到 scheduler 的非零退出。

四份源结果的 scheduler trace 都显示首个 `get_obs` 在 loop 启动后约 30 秒由 scheduler 自己抛出 `TimeoutError`；controller 内 worker RPC 在实际启动命令中设为 600 秒。首次 `get_obs` 为什么没有在 30 秒内返回（冷渲染、GPU/driver 争用、worker 卡死等）不能从现有产物区分：worker 在 runner 清理后才被中断，未留下响应完成时间或原始渲染异常。没有把该未证实部分归因给模型、memory、seed 或任务算法。

| formal run | 首次异常 | scheduler loop 开始 → 停止 | runner 最终原因 |
| --- | --- | --- | --- |
| `put_back_full_t_plus_30_s0_20k_100ep` | 16 / 100016 | 08:23:04.650 → 08:23:34.651 | `robot_status_transport_error` |
| `rearrange_full_t_plus_1_s1_20k_100ep` | 17 / 100017 | 08:45:05.263 → 08:45:35.264 | `robot_status_transport_error` |
| `rearrange_full_t_plus_30_s0_20k_100ep` | 32 / 100032 | 08:45:07.713 → 08:45:37.715 | `robot_status_transport_error` |
| `rearrange_full_t_plus_1_s0_20k_100ep` | 67 / 100067 | 09:49:34.382 → 09:50:04.384 | `scheduler_exited_before_terminal` |

直接证据在每个目录的 `processes/*-scheduler.stdout.log`：均为 `SchedulerBase.run_iteration → _robot_client.call(get_obs) → TimeoutError: timed out in 30.0s`；对应 `episode_diagnostics.jsonl` 的状态均是 reset 已成功后的 `ready / logical_step=0`。实际 robot 启动命令在 `processes.jsonl` 中显式给出 `params.rpc_timeout=600`。两个 rearrange worker stderr 中仅有清理后的 `BrokenPipeError`，没有先于清理的 Timeout、render 或崩溃记录。

源任务 `e6908de7-4b02-465a-987b-a19eba7a315a` 的最新 report 与上述产物已读。对比冻结运行 bridge `8ea6078` 与本任务基线 `f0f585a`，`benchmark/runner.py`、`rmbench_simulation.py` 和 `transport/websocket.py` 没有已有修复。

## 交付

工作树：
`/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/robot-bridge`

分支 / commit：
`task/378da0ac-54fa-4d52-b638-b1bce9a9a2d0` / `ed2f4709903050824ada97d775c4d10295969617` (`fix(rmbench): preserve status during slow observations`)

改动：

- RMBench controller 在 worker 正在处理 `get_obs`、`execute` 或 `reset` 时立即返回最后一次完整 `episode_status`，并标记 `worker_state=running`、`episode_status_source=cached`；不再把状态探测排到长 RPC 后。
- 空闲状态探测使用固定 5 秒有界 worker probe；worker 已失联则返回 `worker_state=lost`，而非伪装成运行中。
- BenchmarkRunner 将 `lost` 保留为 `robot_worker_lost`，连同最后可得的 status/diagnostics 回收 scheduler；controller shutdown 会中断并 reap 正在等待的 worker RPC。
- 新增 API/runner 文档，并新增真实 localhost WebSocket → Robot Server → controller → 子进程 worker CPU 测试，覆盖慢响应、worker 死亡与中断清理。

没有改变 memory、模型、动作、成功判定、seed、RMBench task 逻辑或 scheduler 的 `get_obs` 30 秒预算；也没有把不完整 run 计入成功率。5 秒只用于 lock 空闲时本应立即返回的状态健康探测，并不延长观测请求。

## CPU 验证

- `.venv/bin/python scripts/worktree_env_smoke.py`：通过。
- `.venv/bin/python -m pytest tests/robot/controllers/test_rmbench_simulation.py tests/benchmark tests/robot/test_server_dispatch.py tests/transport/test_websocket.py -q`：`49 passed, 1 skipped`；skip 是既有的独立 RMBench Python 3.10 环境条件测试。
- `ruff check` 通过修改的 controller/test；`runner.py` 的 import-order `I001` 在 `f0f585a` 基线已存在，忽略该条后 runner 检查通过。`git diff --check` 通过。

未启动 GPU、训练、真机或正式/烟雾评测。

## 版本影响、限制与重跑建议

| 版本 | 影响 |
| --- | --- |
| 冻结运行版 `8ea6078`（现有四份失败产物） | 长首次 `get_obs` 会同时堵住 runner 状态 RPC；失败可被标为 `robot_status_transport_error`，根因信息被覆盖。 |
| 候选修复版 `ed2f470`（基于 `f0f585a`） | 状态轮询保持可用，worker 丢失与运行中观测可区分，关闭有界；若 scheduler 本身的 30 秒 `get_obs` 仍超时，结果仍会失败，但会以 scheduler trace/exit 保留，不会被状态探测误判为成功或正常任务失败。 |

现有 `experiments/memory_chunk_20260910/commands/run_memory_schema_eval.py` 在第 212–213 行硬校验 bridge 为 `8ea6078`，不能直接用于 `ed2f470`。Manager 若要 GPU 进一步区分首帧慢渲染与 worker 卡死，应先建立带新 bridge pin 的独立、干净 launcher/manifest；不要修改活跃 8ea 运行树。建议只做一个 manager 指定空闲卡上的新 smoke（两集、独立 result run、保留 robot stderr 和 scheduler trace），并先为该 launcher 提供小于正式 3600 秒的明确诊断上限；当前冻结 launcher 的默认每集上限为 3600 秒，不适合作为未经批准的短复现命令。

若该 smoke 无 runtime error，再由 Manager 决定四项各自是否在新版本从 episode 0 以原 seed 区间重新跑完整 100；旧 16/17/32/67 条只作原始证据，不能拼接为新分母或正式成功率。代码内容已变，更不能复用旧 smoke gate。
