# RMBench 慢 `get_obs` 状态查询与时序诊断独立复查：代码级准入，formal 继续阻塞

## 准入结论

本次定向复查认可以下两个**窄保护修复**可作为后续诊断运行和代码合入的依据，由 Manager 决定实际合入：

- `robot-bridge d49f6165cf5f1b5a7111c0826e52bde2d0b9e479`（基于原候选 `de0e9dac89601b792e0eb56e56d88175cbe643e7`）
- `RMBench ad8b5c7cab1af696c303339d11cf0f82f8a066ac`（基于原候选 `ed1e00b403c4f49cf2ad4f4fa7afd35609c55d6a`）

这不是四个历史 formal 首次 `get_obs` 30 秒超时的完整修复，也不批准 formal 重跑、旧 partial 拼接或把单次 GPU3 正常返回当作准入证据。四个事故的原始根因仍未知；正式运行范围和版本组合仍由 Manager 另行裁定。

## 已解除的代码/产物阻塞

1. cached terminal 不再结束 runner 的 scheduler。

   `robot_bridge/benchmark/runner.py:472-501` 会保存 cached 状态用于诊断，但仅在终态 status 不是
   `episode_status_source="cached"` 时等待或结束 scheduler。RMBench controller 在
   `robot_bridge/robot/controllers/rmbench_simulation.py:317-360,405-422` 明确返回 `worker` 或
   `cached`，所以该 controller 的 terminal 只能由 fresh worker status 触发；没有该字段的旧 controller
   保持既有兼容行为。

   `tests/robot/controllers/test_rmbench_simulation.py:426` 用两个真实 localhost WebSocket 客户端覆盖：
   一次已终态 reset 后，另一连接开始慢 reset，status 连接取得 cached 旧 terminal；runner 不会走
   `terminal_scheduler_timeout`，而是在既有 episode deadline 到达时记录 `episode_timeout`。

   这项用例的边界已写明：正常 `BenchmarkRunner._loop()` 同步等自己的 reset 返回后才启动 scheduler
   并进入 `_wait()`。因此“旧 terminal + 下一集慢 reset”是外部并发 API 的可达防护，不是正常 runner
   的已证实触发链，也不是历史四个首次 `get_obs` 超时的已确认首因。

2. idle status probe 的固定 5 秒策略有明确 CPU 回归。

   `_STATUS_POLL_TIMEOUT = 5.0` 位于
   `robot_bridge/robot/controllers/rmbench_simulation.py:20-25`；空闲 worker 的 status RPC 超过此健康边界
   会经既有 `_request` 失败路径被 reap，返回 `worker_state=lost`，不会扩张 scheduler 的 30 秒
   `get_obs` 预算。`tests/robot/controllers/test_rmbench_simulation.py:494` 用 CPU fake worker 的 0.2 秒
   status 延迟和临时 0.05 秒边界验证 timeout、`worker_rpc_failed` 证据与进程回收。该测试验证固定
   策略的边界分支，不把合法的慢 idle status 或历史首帧超时重新归因。

3. 实际 RMBench 执行树 HEAD 已与 manifest 来源分列。

   `robot_bridge/benchmark/runner.py:610-624` 将 source-root 的路径和 `git rev-parse HEAD` 写到
   `runtime.rmbench_execution_tree`，与 `input_manifest.source_commit` 保持独立。
   `tests/benchmark/test_runner.py:191` 断言两者不互相冒充。这消除了 `.local`/`resolve()` 可能让
   manifest 所在树身份替代实际 RMBench worktree HEAD 的留痕歧义。

4. 新 diagnostic leaf 不再生成常规成功率入口。

   `script/eval_diagnostics.py:608-647` 在 `mode=diagnostic` 时只写 `diagnostic_result.txt`，其中记录
   状态、目标集数与证据路径，不写 `_result.txt` 或 `Success Rate`；smoke/formal 的原 `_result.txt`
   格式保持不变。`tests/test_eval_diagnostics.py:69-119` 通过实际 recorder 产物同时断言 diagnostic
   不存在 `_result.txt` 且普通 smoke 仍含 `Success Rate`。这满足当前任务要求的 reader-facing
   排除，不引入全局汇总框架。

   已运行的 GPU3 诊断目录
   `RMBench/eval_result/memory_chunk_20260910/first_obs_timeline_rearrange_tplus1_s1_ep17_gpu3/`
   仍有旧代码生成的 `_result.txt`（`Success Rate: 1.0`）。它早于 `ad8b5c7`，不因新代码而被追溯改变；
   台账或 formal 汇总必须继续把该已知 leaf 视为 diagnostic，而不是正式结果。此项历史产物说明不构成
   额外 GPU 要求或对旧 episode/trace 的改写。

## 保留的 formal 阻塞

- 冻结 formal 运行中四次 scheduler 首次 `get_obs` 自身 30 秒超时的根因仍没有证据。此次改动只避免
  status RPC 被串行 worker lock 误读和改善取证/产物边界，未改变 scheduler 30 秒预算、模型、memory、
  动作、成功判定、seed、真机 wait 或 UDP。
- GPU3 的单次 `episode_id=17 / seed=100017` 诊断没有复现：reset receipt→response 约 73.392 秒，
  首次 `get_obs` receipt→response 约 6.168 秒。它表明该次请求到达 worker 并返回，不能解释四次
  间歇性 30 秒超时，更不能归因到 memory、模型、seed、渲染或 GPU。
- trace 仍是 opt-in，proxy timeline 上限仍为 64；本次没有扩展 trace 或其上限。即使窄修复合入，formal
  是否从 episode 0 以固定干净版本完整重跑，及如何隔离历史 partial，均由 Manager 决定。

## CPU 验证

在审阅者独立 worktree、CPU 环境执行：

- `env CUDA_VISIBLE_DEVICES= JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/robot/controllers/test_rmbench_simulation.py tests/benchmark tests/robot/test_server_dispatch.py tests/transport/test_websocket.py -q`（`d49f616`）：`54 passed, 1 skipped`。
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m ruff check robot_bridge/benchmark/runner.py robot_bridge/robot/controllers/rmbench_simulation.py tests/robot/controllers/test_rmbench_simulation.py tests/benchmark/test_runner.py`：通过。
- `env CUDA_VISIBLE_DEVICES= JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`（`ad8b5c7`）：`4 tests passed`。既有 SAPIEN/Open3D 导入告警未造成失败。
- 两个提交相对其原候选的 `git diff --check` 通过；作者 worktree 与审阅 worktree 均无代码改动或测试缓存残留。

未启动 GPU、仿真评测、真机、SSH 或远端命令，也未修改业务代码。

## Workspace 与版本

| 仓库 | 原候选 | 定向复查 commit | 审阅 worktree |
| --- | --- | --- | --- |
| robot-bridge | `de0e9dac89601b792e0eb56e56d88175cbe643e7` | `d49f6165cf5f1b5a7111c0826e52bde2d0b9e479` | `/mnt/public/xcj/Projects/workspace/ae463958-bc48-43b3-9d61-b9ca7d579d83/robot-bridge` |
| RMBench | `ed1e00b403c4f49cf2ad4f4fa7afd35609c55d6a` | `ad8b5c7cab1af696c303339d11cf0f82f8a066ac` | `/mnt/public/xcj/Projects/workspace/ae463958-bc48-43b3-9d61-b9ca7d579d83/RMBench` |

本任务为独立只读 review，无交付代码 commit；worktree 保留供 Manager 验收和归档。

发布时，两个审阅分支均已 fast-forward 到表中的定向复查 commit，使 MAM 的交付版本元数据与本报告一致。
