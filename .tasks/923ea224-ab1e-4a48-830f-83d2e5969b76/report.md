# C2/C3 episode 22 simulator EOF：独立只读诊断

## 范围与冻结版本

本诊断未改代码、活跃评测、远端环境、缓存或结果；未启动 GPU、复现、安装、清理或终止进程。

- robot-bridge 独立 worktree：`/mnt/public/xcj/Projects/workspace/923ea224-ab1e-4a48-830f-83d2e5969b76/robot-bridge`，HEAD `f9626636c4776d8eb15f9c556775cb2d12c000e5`，干净。
- RMBench 独立 worktree：`/mnt/public/xcj/Projects/workspace/923ea224-ab1e-4a48-830f-83d2e5969b76/RMBench`，HEAD `9d8f47887a50ea691e5624de139f10bfcfb54412`，干净。
- 远端 r2 artifacts 固定的 OpenPI 为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
- CPU-only 检查：`CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/robot/controllers/test_rmbench_simulation.py tests/benchmark/test_runner.py`，**14 passed, 1 skipped**。这覆盖 worker/proxy 与 runner 的已有行为，不宣称能执行 native SAPIEN 根因复现。
- `git diff --check 9d8f478..17b55bf -- envs/_base_task.py` 通过；本任务没有提交。

## 结论

**确认的近因是同一 worker 进程内反复创建 SAPIEN renderer 的生命周期故障，不是 policy、scheduler、RPC timeout、seed 或 Warp cache 已被证明损坏。**  
冻结 RMBench 在每次 task `setup_demo()` 中新建 `sapien.SapienRenderer()`。C2/C3 的六个 worker 都在第 23 次 reset 尝试（episode id 22）首先记录 native `svulkan2 ... ErrorIncompatibleDriver`，随后 stdout framed RPC 在回复前关闭，bridge proxy 才观察到 EOF。C1 的同冻结配置完整 100 集运行没有该 native marker。

“accepted reset”须精确解释：原始 `seed_preflight.jsonl` 中 episode 22 的 `accepted` 是 **null**，`response.status=error`；它并非已成功接受的第 23 个 rollout。runner 以 proxy 保留的上一集 terminal `episode_status` 将其记为 `accepted_reset_error`。因此六份 failure review 所列“23 partial”是 22 个已完成 terminal 加 1 条 reset-error 记录，不能计入正式分母。

根因的上游 C++/SAPIEN/Vulkan-driver 内部机制仍未从 r2 日志中可证实；这里的“确认”指可操作的 renderer 生命周期近因及 EOF 传播链，而非宣称某个系统驱动整体失效。

## 六个失败的直接证据

所有 leaf 位于：

`/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/`

每个 leaf 均保留 `failure_review.json`、`seed_preflight.jsonl`、`processes.jsonl`、`processes/rmbench_sim_worker.stderr.log` 和同名 outer log：

`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-seeds-r2/records/<run>.outer.log`

| host/GPU | run | episode 22 seed | worker 首个 native 错误时间 |
| --- | --- | ---: | --- |
| C2/6 | `c_rearrange_full_t_plus_30_trainseed0_evalseed1_100ep_r2` | 200022 | 18:46:02.112 |
| C2/7 | `c_rearrange_full_t_plus_30_trainseed0_evalseed2_100ep_r2` | 300022 | 18:58:33.789 |
| C3/0 | `c_put_back_full_t_plus_1_trainseed1_evalseed1_100ep_r2` | 200022 | 19:53:56.460 |
| C3/1 | `c_put_back_full_t_plus_1_trainseed0_evalseed2_100ep_r2` | 300022 | 19:24:05.887 |
| C3/2 | `c_put_back_full_t_plus_30_trainseed0_evalseed1_100ep_r2` | 200022 | 19:34:04.430 |
| C3/3 | `c_put_back_full_t_plus_30_trainseed0_evalseed2_100ep_r2` | 300022 | 19:50:40.871 |

六个 worker stderr 都恰有一次以下紧邻 EOF 的 marker：

```text
[svulkan2] [error] Your GPU driver does not support Vulkan.
[svulkan2] [error] Failed to create renderer with error:
vk::createInstanceUnique: ErrorIncompatibleDriver
```

每份 `seed_preflight.jsonl` 的最后两条均是 episode 21 `accepted=true, status=ok`，随后 episode 22 `accepted=null, status=error`，错误为 `RMBench worker 'reset' failed: RPC failed (EOFError: worker closed the RPC stream during a frame)`。  
`processes.jsonl` 进一步排定因果顺序：scheduler ordinal 2–23（对应 episode 0–21）均以 `episode_terminal` / returncode 0 退出；episode 22 没有新 scheduler；之后 robot 和 policy 仅因 `runner_shutdown` 收到 -15。故 robot/policy 的 -15 是外层收尾，不是最早失败进程。

## 冻结代码中的传播链

1. `RMBench/envs/rearrange_blocks.py:6-7` 和 `envs/put_back_block.py:6-7` 的 `setup_demo()` 都调用 `Base_Task._init_task_env_()`。
2. `RMBench/envs/_base_task.py:281-288` 每次 `setup_scene()` 创建新 `sapien.Engine()` 和新 `sapien.SapienRenderer()`，再绑定 renderer。worker reset 在 `robot-bridge/robot_bridge/robot/controllers/rmbench_sim_worker.py:130-163` 关闭先前 env，并对 probe/actual setup 调用该路径。
3. native renderer 在 reset 22 关闭 worker stdout 前没有产生可封装的 Python exception frame。proxy 在 `rmbench_simulation.py:109-114` 读 framed response 时得到 EOF，停止其 child 并返回带缓存上一集 status 的 error。
4. `robot_bridge/benchmark/runner.py:495-520` 保存 raw preflight；非 `ok` response 携带的旧 status 非 `rejected` 时，它记录 `accepted_reset_error`。这解释了所有 run 名、模型、eval seed 都在相同 episode id 停止。

C1 的完整健康参照为：

`/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_rearrange_no_memory_trainseed1_evalseed0_100ep_r2/`

它以相同 r2 RMBench/bridge/OpenPI commits、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.4`、`SAPIEN_RENDER_DEVICE=cuda:0`（在各自 `CUDA_VISIBLE_DEVICES` 映射后）以及 startup/reset/episode timeout 660/660/3600 运行。其 100 个 scheduler 均为 `episode_terminal` / 0，worker stderr 的 `ErrorIncompatibleDriver` 计数为 0。C2/C3 同样使用每卡 `cuda:0` 映射、0.4 fraction 与相同 timeout，故现有 artifacts 不支持将本次归因于这些资源限制或 policy 推理。

## Warp 与 Vulkan 的边界

- `WARP_CACHE_PATH` 只在 robot/policy command 中出现。既有已确立事实是 worker 的 Warp 0.15.1 不会因该环境变量自动设置 `warp.config.kernel_cache_dir`；冻结 worker 也没有这项 Python 设置。没有 cache corruption 或 Warp traceback 证据，不能把它当作 EOF 根因。
- Vulkan 文本本身不足以做因果结论；本次将其作为近因，是因为它在六个 leaf 的第一个失败点出现、源代码将该点直接置于 reset 的 renderer 创建，并且无 policy/scheduler 失败先于它。
- 已发布的早期 C2 生命周期证据提供交叉验证：`.tasks/2a879870-8dda-4613-a684-0ad48a5e86be/report.md` 记录 system ICD 与每 5 次 `sapien.render.clear_cache()` 都仍在相同边界失败。它支持“不改 ICD/cache 作为最小修复”，但不把未记录的 driver 内部细节伪装为已知。

## 最小修复方案

建议仅修改 `RMBench/envs/_base_task.py`：将 `SapienRenderer` 变为**每个 Python worker 进程一个**的惰性模块级对象；每集仍新建 engine、scene、物理参数、相机、灯光和 task state。

```python
_PROCESS_RENDERER = None

# setup_scene()
global _PROCESS_RENDERER
if _PROCESS_RENDERER is None:
    _PROCESS_RENDERER = sapien.SapienRenderer()
self.renderer = _PROCESS_RENDERER
self.engine.set_renderer(self.renderer)
```

该精确最小 diff 已作为独立候选 `17b55bff1c79a0c5a836d1da089765934cb3a5b0` 存在；相对本任务冻结 RMBench `9d8f478`，`envs/_base_task.py` 仅为 8 行新增、1 行替换。它不改 worker/RPC、seed、expert preflight、policy、memory、action、observation、video、timeouts 或 Warp 设置。

约束：同一 worker 内 `SAPIEN_RENDER_DEVICE` 必须固定。当前单卡 run 将物理 GPU 映射为 `cuda:0`，符合该约束；若未来需要同一 worker 跨设备切换，应 fail-fast 或新建 worker，不能静默共用 renderer。

## 验证与后续门禁

本任务不执行以下 GPU 步骤。Manager 批准实现后应按顺序：

1. 在独立 candidate tree 进行 CPU unit/source review，确认 renderer 只创建一次而 engine/scene 仍每 reset 创建，并保留现有 worker/proxy/runner 测试。
2. 单卡固定设备做有界 40-reset lifecycle gate，跨过旧 episode 22；保存每次 accepted reset、worker stderr、child exit 和 GPU 回收，要求无 `ErrorIncompatibleDriver`、EOF、segfault 或 Python traceback。
3. 在各目标 host 重新做 matching video/no-video smoke2；通过后才用新的 result leaf 从原始固定 seed 序列开始 formal100。旧 22 terminal 和 error record 永不拼入新分母。

无需为区分当前两种主要原因再请求一次 GPU reproduction：已归档的 `2a879870` 证据显示该候选曾完成 C2 40/40 reset（无 renderer/EOF marker），随后 C1/C2/C3 smoke2 均通过；这是历史佐证，不替代当前冻结组合在部署时的门禁。

## 结果口径与限制

- 六个 C2/C3 partial 都没有 `final_review.json`，均为 **not reportable**，不自动重试、不计作 100-rollout 成绩。
- C1 已完成结果没有该失败标记，也没有证据需要追溯作废；本诊断不改变其成绩或活跃 C1 jobs。
- r2 artifacts 不记录 worker 的原始 native exit code，因为 proxy 在 EOF 后自行停止/reap child；因此无法仅据它们判定具体信号或修复 SAPIEN/driver 上游缺陷。
- 无代码提交、无 GPU 使用、无远端写入；保留两个独立 worktree 供审阅。

