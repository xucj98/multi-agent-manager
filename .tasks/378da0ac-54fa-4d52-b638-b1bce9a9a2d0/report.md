# formal 首次 `get_obs` 30 秒超时：定位与最小修复

## 结论

已证实的公共运行问题是**状态探测与长 `get_obs` 共用 RMBench controller 的串行 worker RPC 锁**：scheduler 的首次 `get_obs` 已在 controller 内等待时，benchmark runner 另一个 WebSocket 连接发出的 `get_episode_status` 会排在同一锁后面。两端 client 都是 30 秒预算，故三次失败被 runner 错标为 `robot_status_transport_error`，另一次先观察到 scheduler 的非零退出。这是故障分类/诊断路径的公共问题，**不是四项 scheduler 首次 `get_obs` 自身超时的已证实首因**。

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

## 阶段二：首帧时序取证与 GPU3 诊断方案

Manager 的阶段裁定成立：`ed2f470` 只解决 runner 状态探测被同一 worker RPC 锁阻塞而误报的问题，不能解释或消除 scheduler 自身首次 `get_obs` 的 30 秒超时。物理首帧为何未按时返回仍未证实；本阶段没有把它归因于 memory、模型、seed、渲染或 GPU 争用。

### 新提交与工作树

| 仓库 | 工作树 / commit | 内容 |
| --- | --- | --- |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/robot-bridge` / `de0e9dac89601b792e0eb56e56d88175cbe643e7` | 在 `ed2f470` 之上增加 opt-in worker/proxy 时序取证和单 episode diagnostic mode。 |
| RMBench | `/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/RMBench` / `ed1e00b403c4f49cf2ad4f4fa7afd35609c55d6a` | 新增独立 GPU3 诊断 launcher 与说明；未修改 `run_memory_schema_eval.py`、`memory_schema_eval.yaml` 或 C 严格对照版本。 |
| OpenPI | `/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/openpi` / `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` | 只创建固定版本 worktree，未改代码。 |

`de0e9da` 的 worker JSONL（仅在 `params.worker_trace_path` 配置时启用）使用同一 request id 记录 `get_obs_enter`、实际 `get_obs_render_enter`、render return/error 和协议响应。controller 同时在最终 episode diagnostics 中保留至多 64 条 `bridge_rpc_timeline` 事件：请求写入、lock 获取时间、非阻塞 cached status probe、worker RPC 返回/失败和已观测的 worker lost。runner 将最后一次 status diagnostics 保留到 scheduler exit、episode timeout 和 worker lost 的失败记录中。它没有修改 scheduler `get_obs` 的 30 秒预算、模型、动作、memory、seed 或成功判定。

CPU 覆盖包含真实 localhost WebSocket → Robot Server → controller → 子进程 worker 链：可控慢 render 时 status 返回 cached 且带 active `get_obs` lock 边界；worker trace 有进入/render/返回的有序事件；worker 被终止时 runner 记录 `robot_worker_lost` 和 timeline。另验证 diagnostic mode 仅运行指定 `episode_id=17`，由原评测 seed 序列得到 `seed=100017`，不使用 smoke 的两集语义。

### CPU 验证

- `robot-bridge/.venv/bin/python scripts/worktree_env_smoke.py`：通过。
- `robot-bridge/.venv/bin/python -m pytest tests/robot/controllers/test_rmbench_simulation.py tests/benchmark tests/robot/test_server_dispatch.py tests/transport/test_websocket.py -q`：`51 passed, 1 skipped`；skip 仍是既有独立 RMBench Python 3.10 环境条件测试。
- `robot-bridge/.venv/bin/python -m ruff check ...`：通过修改 bridge、worker、runner 和测试；`git diff --check` 通过。
- `RMBench/.venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`：3 项通过；fixture 输出既有 SAPIEN/资源告警，但无失败。
- `JAX_PLATFORMS=cpu ... run_first_obs_timeline_diagnostic.py --dry-run`：17.5 秒通过。它验证 s1 `20000` checkpoint schema、三树 pin、GPU3 端口、trace path、原失败 `episode_id=17 / seed=100017` 和生成的完整命令；未启动 robot/policy/scheduler、未加载模型权重或使用 GPU。

### GPU3 单次短诊断（准入前计划）

新入口是 [`run_first_obs_timeline_diagnostic.py`](/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/RMBench/experiments/memory_chunk_20260910/commands/run_first_obs_timeline_diagnostic.py)，完整说明与命令在 [`README_first_obs_timeline_diagnostic.md`](/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/RMBench/experiments/memory_chunk_20260910/README_first_obs_timeline_diagnostic.md)。它在启动前拒绝非 clean worktree，并硬校验：bridge `de0e9da`、OpenPI `a869498`、RMBench 是 `6139577` 的后继、GPU3、`rearrange_full_t_plus_1` s1 checkpoint 的 `20000`、`episode_id=17 / seed=100017`。结果唯一落在：

```text
eval_result/memory_chunk_20260910/first_obs_timeline_rearrange_tplus1_s1_ep17_gpu3/
```

准入后执行顺序为：先用入口 `--prepare-audit` 生成只读 checkpoint 审计与派生 manifest，再运行不带 `--dry-run` 的同一命令。launcher 内部执行经验证的 `timeout --foreground --signal=INT --kill-after=30s 1500s ...`，以 SIGINT 让 runner 的 `finally` 回收 robot/policy 子进程；1500 秒为 GPU 阶段总墙钟上限。service startup/reset 保留源 launcher 的 660 秒预算，单 episode runner 为 75 秒，scheduler 首次 `get_obs` 仍是 30 秒，worker 内部 RPC 仍为 600 秒，仅用于在 client 超时后保留取证和收尾，并未扩大 scheduler timeout。

若诊断再次超时，检查 scheduler traceback、`processes/rmbench_sim_worker.trace.jsonl` 与失败 episode 的 `bridge_rpc_timeline`：worker 已记 `get_obs_render_enter` 而无 return 说明卡在或晚于实际渲染调用；没有 worker receipt 则定位到 proxy/pipe 前；`worker_lost` 记录 returncode 与已知 active RPC。任何一次正常返回也只说明该次没有复现，不能放行四项 formal 重跑。四个 partial run 仍不能拼接，正式重跑仍需 Manager 后续决定。

### GPU3 单次短诊断实际结果（2026-09-11）

Manager 已发布 GPU3 准入后，按上文两条命令实际运行一次：先 `--prepare-audit`，再运行
`first_obs_timeline_rearrange_tplus1_s1_ep17_gpu3`。启动前 GPU3 为 1 MiB / 0%，19430/19432
无监听；三树均干净且分别固定为 bridge `de0e9da`、RMBench `ed1e00b`、OpenPI `a869498`。
没有修改 C 严格基线、旧 launcher 或 scheduler 的 30 秒预算。

诊断结果目录：

```text
/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/first_obs_timeline_rearrange_tplus1_s1_ep17_gpu3/
```

该次不是 formal 结果，也不构成 smoke 门禁。它完成一个指定 episode（scheduler exit 0 / `episode_terminal`）；
75 秒 episode cap 与 1500 秒外层 cap 都没有触发。`diagnostics_summary.json` 的 `status` 为
`completed`，仅表示该诊断 episode 正常结束，不能用于四项 partial run 的分母或正式成功率。

worker 单调时钟给出本次冷路径的可复核时序：

| 阶段 | 时长 / 边界 |
| --- | --- |
| reset worker receipt → response sent | 73,392.333 ms；在独立 660 秒 reset 预算内。 |
| 首次 `get_obs` worker receipt → `get_obs_enter` | 0.087 ms。 |
| `get_obs_enter` → `get_obs_render_enter` | 0.029 ms。 |
| `get_obs_render_enter` → render return | 6,165.423 ms。 |
| worker receipt → protocol response sent | 6,167.997 ms。 |

因此，这一轮**没有可归因的失败首因**：最早的慢阶段是 reset，但它发生在 scheduler 启动前且已成功；
原失败语义上的首次 `get_obs` 已到达 worker、立即进入渲染并在约 6.17 秒内返回，未触发 30 秒超时。
这排除了本轮中的 worker 入口排队或 render 卡死，却不能解释历史四次间歇性 30 秒超时，也不能支持
修改 timeout、归因于 memory/模型/seed，或放行 formal 重跑。

完整 episode 产生的 proxy 事件超过 64 条，所以最终 `bridge_rpc_timeline` 保留的是末尾窗口，未保留
初始 frame 的 controller lock-acquire 事件；worker JSONL 保留了该 frame 的 receipt/enter/render/return
证据。末尾窗口中，后续长 `get_obs` 期间的 status probe 均为 cached、`lock_wait_ms=0`，这验证
`ed2f470`/`de0e9da` 的状态诊断行为，但不构成首次 30 秒问题的根因修复。

收尾已核对：worker 写入 `worker_stopped`；scheduler 正常 exit 0，policy/robot 均由 runner
shutdown 以 `-15` 退出；GPU3 回到 1 MiB / 0%，19430/19432 无监听。保留上述 result、worker JSONL、
scheduler 日志、输入审计和 manifest；没有自动重跑，也没有新增实现。
## 阶段三：review 采纳的窄修复与定向复核请求（2026-09-11）

本阶段只落实 Manager 采纳的四项边界修复，没有启动 GPU、formal、smoke、真机或训练，也没有修改 C 严格对照、scheduler 的 30 秒 `get_obs` 预算、模型/memory/动作/成功判定或 trace 框架上限。

| 仓库 | worktree | 提交 | 内容 |
| --- | --- | --- | --- |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/robot-bridge` | `d49f6165cf5f1b5a7111c0826e52bde2d0b9e479` | cached terminal 权威性、5 秒 probe 边界测试、实际 RMBench execution-tree HEAD 留痕。 |
| RMBench | `/mnt/public/xcj/Projects/workspace/378da0ac-54fa-4d52-b638-b1bce9a9a2d0/RMBench` | `ad8b5c7cab1af696c303339d11cf0f82f8a066ac` | diagnostic 结果与常规成功率入口隔离。 |

### 已实现的边界

- runner 仍保存 cached status 及 diagnostics，但只有 `episode_status_source != "cached"` 的 terminal 才进入 scheduler 收尾；没有该字段的旧 controller 保持原行为。真实 localhost 双 WebSocket 测试先写入 terminal，再由另一连接持锁慢 reset，证实 runner 不会以 cached terminal 结束，而是在短测试 deadline 正确报 `episode_timeout`。
- 这不是四项 formal 的已证实首因：正常 `BenchmarkRunner._loop()` 同步等自己的 reset 返回后才启动 scheduler 和 `_wait()`，所以“旧 terminal + 下一次慢 reset”不在其正常单 runner 链中。它是多连接 controller API 的可达防御边界，不能反推为历史首次 `get_obs` timeout 的触发序列。
- 固定 5 秒空闲 `get_episode_status` probe 的既有策略已明确并补 CPU 用例：fake worker 在收到 status 请求后仍存活但延迟超过缩短后的 test bound，proxy 记录 `worker_rpc_failed/TimeoutError`、reap worker，并返回 `worker_state=lost`。这确认它按 worker 异常处理，不是 scheduler timeout 调整或新配置项。
- 后续 launcher 的 `usr_args._runtime.rmbench_execution_tree` 单列 `--source-root RMBench` 实际 root 与精确 HEAD；`input_manifest.source_commit` 保持为 manifest 父目录的独立身份。CPU 测试初始化不同 Git root 并验证两字段不会混淆。
- `RMBenchResultRecorder.finish()` 在 `mode=diagnostic` 只写 `diagnostic_result.txt`（status、target episodes、证据指针），不再写常规 `_result.txt` 或 `Success Rate`；smoke/formal 的原 `_result.txt` 格式保持。实际 recorder 产物测试同时覆盖 diagnostic 与 smoke。

### 已完成 GPU3 诊断 leaf 的透明后处理

已完成 leaf 在新代码之前运行，因此没有改写其 `config.yaml` 或宣称它原本带有新字段。为防止旧单集成功被常规入口索引，已删除：

```text
/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/first_obs_timeline_rearrange_tplus1_s1_ep17_gpu3/_result.txt
```

并新增同目录下不含成功率的 `diagnostic_result.txt` 与
`diagnostic_result_postprocess.json`。sidecar 记录被移除旧文件的 SHA-256、替换理由、后处理提交、以及未改动的 `config.yaml`、`command.txt`、`episode17.json`、`episode_diagnostics.jsonl`、`diagnostics_summary.json`、`processes.jsonl` 和 worker trace 哈希。

sidecar 同时明确这是事后核实，而非原 launcher 写入：实际 RMBench execution tree 为 `ed1e00b403c4f49cf2ad4f4fa7afd35609c55d6a`，bridge 为 `de0e9dac89601b792e0eb56e56d88175cbe643e7`，OpenPI 为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；原 `input_manifest.source_commit` 是共享 `.local` manifest 父目录的 `f2ec2cfe14d4a721a12d19ae9971af5c0e1777ff`。原始 episode、scheduler、worker trace、config 与 timing evidence 未改。

### CPU 验证

- `env CUDA_VISIBLE_DEVICES= JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 robot-bridge/.venv/bin/python -m pytest tests/robot/controllers/test_rmbench_simulation.py tests/benchmark tests/robot/test_server_dispatch.py tests/transport/test_websocket.py -q`：`54 passed, 1 skipped`。
- `PYTHONDONTWRITEBYTECODE=1 robot-bridge/.venv/bin/python -m ruff check robot_bridge/benchmark/runner.py robot_bridge/robot/controllers/rmbench_simulation.py tests/robot/controllers/test_rmbench_simulation.py tests/benchmark/test_runner.py`：通过。
- `env CUDA_VISIBLE_DEVICES= JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 RMBench/.venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`：`4 tests passed`；fixture import 输出既有 SAPIEN/Open3D/资源告警，无失败。
- 两个 worktree 均 clean，`git diff --check` 通过。

### 仍未证实与准入结论

四个 historical formal 的 scheduler 首次 `get_obs` 自身 30 秒超时的首因仍未知。上述 cached-status、cached-terminal 和 5 秒 probe 修复改善故障分类、API 终态语义与取证边界，但没有证明或消除 scheduler 首帧超时；GPU3 单次正常返回同样不能放行 formal。四个 partial leaf 继续只作原始证据，不能合并为任何新的成功率或分母。

请 `ae463958-bc48-43b3-9d61-b9ca7d579d83` 对 `d49f6165cf5f1b5a7111c0826e52bde2d0b9e479` 与 `ad8b5c7cab1af696c303339d11cf0f82f8a066ac` 定向复核：cached terminal 权威性、diagnostic result 隔离、5 秒 probe 的 worker 异常策略、实际 RMBench execution-tree provenance，以及上述“慢 reset”仅为防御边界而非四项 formal 首因的表述。
