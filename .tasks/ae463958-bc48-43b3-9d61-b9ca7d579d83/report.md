# RMBench 慢 `get_obs` 状态查询与时序诊断独立 review：阻塞

## 准入结论

不批准候选 `robot-bridge de0e9dac89601b792e0eb56e56d88175cbe643e7` 和
`RMBench ed1e00b403c4f49cf2ad4f4fa7afd35609c55d6a` 按当前状态合入为可用于
formal 的运行时修复。它们可以把“长 worker RPC 堵住额外状态探测”从
`robot_status_transport_error` 中分离出来，并为单集诊断留下有效证据；但仍有两个
代码/产物边界阻塞，且四个 formal 首次 `get_obs` 的原始根因仍未知。

即使下列阻塞修正，四个 formal 也**不准入**：需要 Manager 另行裁定干净、固定版本的
复跑范围。旧 partial 16/17/32/67 不能拼成新分母或成功率。

## 阻塞项

1. cached status 的 `terminal` 仍被 runner 当作实时 terminal 使用。

   `robot_bridge/robot/controllers/rmbench_simulation.py:325-345` 在另一个 RPC（包括
   `reset`）持锁时，返回最后一次完整的 `episode_status` 和
   `episode_status_source="cached"`。文档在
   `docs/reference/robot-server-api.md:143-147` 及
   `docs/tutorials/rmbench-benchmark-runner.zh-CN.md:33-37` 明确说它不能代替 terminal
   判定；但 `robot_bridge/benchmark/runner.py:461-480` 完全不检查 source，直接在
   `latest["terminal"]` 为真时等待/结束 scheduler。

   这里必须与已确认事故严格区分：正常 `BenchmarkRunner` 在 `_loop()` 中同步等到
   `reset` RPC 返回，才启动 scheduler 并进入 `_wait()`，所以“旧 terminal + 下一集慢 reset”
   不是正常 runner 的已证实触发链，也不是四个历史首次 `get_obs` 超时的首因。它是通用
   多连接 API 的可达边界：外部并发 reset/status 调用仍可得到旧 terminal，而 runner 未执行
   source 检查。现有真实 localhost 用例只覆盖慢 `get_obs` 的 cached `ready`，没有覆盖这个
   API 语义。解除条件是让 runner 只接受 worker-source 的 terminal（或传递并检查等价的
   authoritative 标记），并新增 CPU 双 WebSocket 回归用例；该用例只证明防护，不得反推历史
   故障根因。

2. diagnostic leaf 仍生成常规 `_result.txt` 的成功率，不能由目录隔离单独保证不混入
   formal 结果。

   launcher 确实写入 `benchmark.mode: diagnostic`、`target_episodes: 1` 和
   `evaluation_kind: first_observation_timeline_diagnostic`；`validate_smoke_run` 也会拒绝
   非 smoke。可是 `script/eval_diagnostics.py:608-630` 对所有 mode 都写
   `Success Rate: <rate>`。实际 GPU3 leaf 的 `_result.txt` 已是 `Success Rate: 1.0`；而
   `experiments/history_audit_20260909/README.md:18-19` 将含普通 `_result.txt` 的 leaf 作为
   规范结果证据。没有 mode-aware 的 reader/汇总保护时，未来只扫 `_result.txt` 的台账会把此
   单集成功误报成评测结果。

   解除条件是在 recorder/结果读取器实现可执行的 non-formal 排除（例如 diagnostic 不写
   常规 `_result.txt`，或所有汇总严格拒绝 `benchmark.mode != formal`），并添加从 diagnostic
   输出到正式汇总的回归测试。README 文案和 run-name 前缀不足以构成准入保护。

## 已核实的行为与仍需补的覆盖

- 状态缓存的主要目标成立：持锁的慢 `get_obs` 不再让第二个 WebSocket status RPC 排队；
  `worker_state=lost` 由 runner 映射为 `robot_worker_lost`。默认 status probe 的 worker
  RPC 被限制为 5 秒，controller timeline 为 `deque(maxlen=64)`，`worker_trace_path` 默认
  关闭；动作、成功判定、scheduler 30 秒 `get_obs` 预算、真机 wait 和 UDP 均未改动。
- shutdown 路径使用独立进程组、SIGTERM/SIGKILL 和有界 `wait`；慢 worker RPC 的真实
  localhost 用例确认 server shutdown 后 worker 被 reap。该用例没有覆盖 worker 自己再派生
  子进程的情形，但当前 group-kill 设计和常规子进程回收逻辑合理。
- 5 秒健康探测仍缺关键反例测试。`_poll_episode_status()` 在空闲路径调用
  `_request(..., timeout=min(..., 5))`，而 `_request()` 超时会停止 worker。现有测试覆盖
  “长 `get_obs` 时不探测”和“已死亡 worker”，没有覆盖“仍有效但
  `get_episode_status` 超过 5 秒”。先用 CPU fake worker 固化期望策略；若这类延迟可合法
  存在，不能把它直接判 lost/杀掉。
- worker JSONL 只在 opt-in 时启用；proxy timeline 保持 `deque(maxlen=64)`。本次窄修复
  不扩 trace 机制或上限：单集 75 秒 launcher 与默认关闭已足够约束其范围，trace 写入异常
  仍不得改变 rollout。
- `.local` 在 worktree 中是到共享主 checkout 的软链接。runner 对 manifest 调用了
  `resolve()`，实际输出的 `input_manifest.source_commit` 为 `f2ec2cf`，而诊断脚本/recorder
  的 commit 是 `ed1e00b`。这不否定本次命令实际固定了 bridge `de0e9da` 和 recorder，
  但 RMBench 总体版本留痕有歧义；窄修复应将启动 worktree 的精确 RMBench HEAD 单列写入
  config，而不只要求 `6139577` 的干净后继，并由定向复查核对它与实际启动 worktree 一致。

## GPU3 单次产物核验

只读核对了
`RMBench/eval_result/memory_chunk_20260910/first_obs_timeline_rearrange_tplus1_s1_ep17_gpu3/`。
它与 launcher 的 `episode_id=17 / seed=100017`、GPU3、75 秒 episode cap、1500 秒外层 cap
对应，且 `config.yaml` 标记 diagnostic。worker JSONL 显示：reset receipt 到 response 约
73.392 秒；首次 `get_obs` receipt→enter 0.087 ms、enter→render-enter 0.029 ms、
render→return 6165.423 ms、receipt→response 6167.997 ms。该次 scheduler 正常退出，未触发
30 秒预算。

这只说明该次原 seed context 没有复现：worker 已收到请求、进入渲染并在约 6.17 秒返回。它
没有解释历史四次的间歇性 30 秒超时，不能归因于 memory、模型、seed、渲染或 GPU，也不能放行
formal 重跑。

## CPU 验证

- `env CUDA_VISIBLE_DEVICES= JAX_PLATFORMS=cpu .venv/bin/python -m pytest tests/robot/controllers/test_rmbench_simulation.py tests/benchmark/test_runner.py tests/benchmark/test_stage3.py tests/robot/test_server_dispatch.py tests/transport/test_websocket.py -q`（robot-bridge）：`39 passed, 1 skipped`。
- `env CUDA_VISIBLE_DEVICES= JAX_PLATFORMS=cpu .venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`（RMBench）：`3 passed`。
- RMBench diagnostic launcher `py_compile`、两库候选 diff 的 whitespace 检查通过。

作者将按最新任务只处理 cached-terminal 防护、diagnostic 产物排除、5 秒边界 CPU 用例和
RMBench 实际 HEAD 留痕；待其提交后再做定向 CPU 复查，不新增 GPU 要求。

未启动 GPU、仿真评测、真机、SSH 或远端命令；也未改动代码。

## Workspace 与版本

| 仓库 | 独立 worktree | 审阅 commit |
| --- | --- | --- |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/ae463958-bc48-43b3-9d61-b9ca7d579d83/robot-bridge` | `de0e9dac89601b792e0eb56e56d88175cbe643e7` |
| RMBench | `/mnt/public/xcj/Projects/workspace/ae463958-bc48-43b3-9d61-b9ca7d579d83/RMBench` | `ed1e00b403c4f49cf2ad4f4fa7afd35609c55d6a` |

本任务为只读 review，无交付代码 commit；测试缓存已清理，两个 worktree 均保留且干净，供 Manager
验收/归档。
