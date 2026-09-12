# 独立复核：smoke/formal cache template 一致性

**结论：PASS，无阻断项。** 审阅 RMBench `9d8f47887a50ea691e5624de139f10bfcfb54412`（父 `f5087496a0f7c892bd322708e4ac0bbdeb74e523`）与冻结 robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`。独立 worktree 分别为 `/mnt/public/xcj/Projects/workspace/a8946c75-7694-4525-9238-975dfb3ee462/RMBench` 和 `.../robot-bridge`；未交付代码 commit，结束时均干净。

- 差异仅在 `run_memory_schema_eval.py` 将 cache 根从具体 `run_name` 改为既有 `{result_run}` child-command 占位符（4 行注释、1 行替换）。用同一输入调用修复前后 `launch()`：旧 smoke/formal 的 robot、policy命令不同；补丁后二者模板字节一致，且仅在子进程启动时展开。
- 私有有界 CPU fixture 使用真实 `BenchmarkRunner`、真实 RMBench recorder（仅把结果根重定向到 `/tmp`）和 fake services。旧 literal smoke 成功后，formal 先通过 smoke artifact 验证、再由 `assert_smoke_compatible` 以 `smoke launch differs from actual formal run` 在首次 reset 前拒绝，复现了 C 首因。补丁下重新生成 fresh smoke2 后，matching formal 完整通过 **100** 个 accepted rollout（seed `200000–200099`）；旧 smoke 未被复用。
- recorder 保存的 patched smoke/formal `launch`、profile、run 一致；结果 leaf 仍按各自 result run 分开。profile 固定 `seed=1`、`action_horizon=50` 和 `memory_config=review_memory_v1` 未变，formal 仍强制 100 episodes。
- 实际 `_Supervisor` 展开后，smoke/formal 的 robot/policy cache 分别落在 `runs/fresh-smoke/{robot,policy}` 和 `runs/fresh-formal/{robot,policy}`。以 C 首波 14 个唯一 r2 run name 展开，得到 28 个唯一实际 WARP cache 路径；因此共享路径上的跨 host 隔离继续依赖并满足全局唯一 run name，robot/policy 也保持分目录。

验证：CPU fixture 通过；`JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/benchmark/test_runner.py` 为 **9 passed**；`git diff --check f508749 9d8f478` 通过。未创建 OpenPI worktree，未使用 GPU、SSH、远端或生产结果目录，也未修改 C 部署。临时 fixture 已清理。
