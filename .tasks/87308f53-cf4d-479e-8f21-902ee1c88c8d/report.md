# C r2 renderer 生命周期候选：独立审阅 PASS

审阅候选：

- RMBench `77477931bee18c2476bea36b400ab45dc67d9ebe`，父链为 `9d8f47887a50ea691e5624de139f10bfcfb54412` → `eba81b41b39652b940fdb6d93dc4451a91352960` → `7747793`。
- robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`。
- worktree：`/mnt/public/xcj/Projects/workspace/87308f53-cf4d-479e-8f21-902ee1c88c8d/{RMBench,robot-bridge}`。

结论：**PASS，无新 blocker。**

## 补丁身份与范围

`9d8f478..eba81b4` 的 `envs/_base_task.py` patch-id 与 `17b55bff1c79a0c5a836d1da089765934cb3a5b0` 相同，且抽取的两份 diff 字节一致。相对 r2 基线，候选仅有：

```text
8 insertions, 1 deletion: envs/_base_task.py
120 insertions: tests/test_renderer_lifecycle.py
```

运行时改动只把 `SapienRenderer()` 改为模块级 `_PROCESS_RENDERER` 的 `None` guard；action、RPC、seed、memory、video、timeout 和设备映射均不在 diff 中。

## 生命周期与当前组合

- `RMBenchSimWorker` 在单一 worker 主循环中串行处理 RPC；每次 reset 先关闭 active env，再对 probe/actual 路径调用 `setup_demo()`。`Base_Task._init_task_env_()` 每次均进入 `setup_scene()`，而该函数仍在每次调用创建 `sapien.Engine()`，并保留两条 fresh scene 创建路径。renderer 是唯一跨 reset 保留的对象。
- C r2 launcher 固定 `CUDA_VISIBLE_DEVICES=<assigned card>` 与 `SAPIEN_RENDER_DEVICE=cuda:0`；bridge `_start_worker()` 从父环境复制这些值，仅重写 Python/RMBench 路径。因此 singleton 的作用域是一个固定设备的 Python worker。
- 历史 gate 使用的 bridge `8ea6078` 是当前 `f9626636` 的祖先；对 `rmbench_sim_worker.py`、`rmbench_simulation.py` 和 `benchmark/runner.py` 的比较没有后续差异。当前组合不引入新的相关 worker 生命周期变化。

## CPU 验证

```bash
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests \
  .venv/bin/python -m unittest -v \
  test_eval_diagnostics.EvalDiagnosticsRecorderTest.test_records_jsonl_and_aggregates_generic_schema \
  test_renderer_lifecycle.RendererLifecycleSourceTest
```

结果：**3 passed, 0.014s**。`git diff --check 9d8f478..7747793` 也通过。

新增 AST test 能有效固定模块级 singleton、guard 中唯一 renderer 构造、fresh engine、两种 scene 路径及 renderer-to-engine 绑定，并且不导入 SAPIEN。它是 CPU 源码回归，**不是** native renderer、GPU、video 或 worker EOF 的运行时证明。

## 部署门禁审阅

计划正确且应保持冻结：在新 runtime tree 上先对受影响 C2/C3 固定设备运行 40 次连续 reset（跨过旧 episode 22），要求 40/40 accepted、exit 0 且无 native/EOF/traceback/segfault marker；随后每个目标 host 做匹配 video/no-video smoke2；全部通过后才从原始完整 seed list 在新 leaf 启动 formal100。历史 `17b55bf` 的 40-reset/三机 smoke 证据仅支持该方案，不替代本组合的重新门禁。

六份旧 partial 仍是 22 terminal episodes 加一条 `accepted=null` reset-error，不能记为 23 个 accepted 或拼入新 formal 分母。没有具体反证时，已完成的健康 C1 结果保持有效。

未运行 GPU、SAPIEN、部署、正式评测或全量 discover；未修改实现。两个 review worktree 干净，非 `.venv` Python 缓存和临时 diff 文件均已清理。
