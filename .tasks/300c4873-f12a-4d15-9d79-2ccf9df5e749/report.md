# 独立 review：eval seed 0/1/2 与 C 并发隔离

**结论：PASS，无阻断项。** 审阅的是 RMBench `f5087496a0f7c892bd322708e4ac0bbdeb74e523`，并固定核对 robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。这是只读独立 review；RMBench worktree 为 `/mnt/public/xcj/Projects/workspace/300c4873-f12a-4d15-9d79-2ccf9df5e749/RMBench`，三树结束时均干净，无交付代码 commit。

- 入口将 eval seed 写入派生 manifest 的 `profile.fixed.seed`，真实 runner 因而使用 `100000 * (1 + seed)`。私有 CPU mock 以真实 `BenchmarkRunner` 跑通：eval 0/1/2 的 accepted seed 分别为 `[100000,100001]`、`[200000,200001]`、`[300000,300001]`。对两个同任务 checkpoint，eval1 首候选拒绝后都得到 `[200001,200002]`，保留既有 rejected-candidate 递增语义且不混入其他 eval 组。
- 三份派生 manifest 的 SHA-256 均不同；构造的 eval0 smoke 被 eval1 formal 的 manifest-hash 验证拒绝，随后 `assert_smoke_compatible` 也因 profile 不同拒绝。formal 仍由 runner 强制 100 accepted episodes；记录的 policy RNG key 0 不构成替代门禁。
- 真实 CPU dry-run 使用 no-memory train seed1 checkpoint 与 `--eval-seed 2`，读到 `training_seed=1`、`environment_seed_start=300000`、上界 `400000`，并生成 GPU7 的 19470/19472 端口和 `schema/runs/review_trainseed1_evalseed2/{robot,policy}` cache 路径。将该 checkpoint 传为 `--training-seed 0` 被正确拒绝（`_s1` 不匹配）。普通 20k run name 强制同时含 trainseed/evalseed。
- C 首波 14 项静态调用实际 `launch()`：C1 6、C2 4、C3 4 个端口对在各 host 内均无重复；14 个 run name 和 14 个 cache 根均唯一。每项 robot/policy 共用本项根下的不同子目录，因此跨 host 同号 GPU 不会复用 Warp cache。

验证：私有 `/tmp` mock integration（真实 runner、fake service/recorder）通过；`JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/benchmark/test_runner.py` 为 **9 passed**；`git diff --check f508749^ f508749` 通过。未使用 GPU、SSH 或远端/C 资源，未重跑既有 eval0，也未写入共享 `.local`。

保留的既有语义：runner 对连续 rejected candidate 没有按记录的 `environment_seed_group_end_exclusive` 硬停止；极端超过 100k 次拒绝才会跨数值区间。此次任务要求保留 rejected-seed 语义，100-episode 范围内无影响；若未来要求绝对数值边界，应单独在 runner 设计有界失败处理。
