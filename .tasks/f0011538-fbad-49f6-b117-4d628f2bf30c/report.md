# observe_and_pickup / swap_T 进度交付（采集待 GPU）

## 已提交的工程交付

- RMBench worktree：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench`
  - commit `03ba4e2a8a0aee7b0b59ea0b701d85c1c9304873`
  - 两任务的 source-only 逐帧 trace、独立 `collection_provenance/episode<N>.json`、确定性 seed/attempt 记录、2 集 smoke/50 集正式入口、完整性验证器和 schema 草案。
  - provenance 在 replay 结束且环境关闭前冻结；不再写入 `play_once()` 的 `info`，避免进入 RPC/在线 policy 路径。
- openpi worktree：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/openpi`
  - commit `6c0501725dc4d244d813db18edaaba9fe69fafeb`
  - 14-D robot-only LeRobot converter、N sidecar、两个 no-memory YAML 与 pi0.5 H50/K30、bs32、20k、seed0 配置。
  - N 只写当前 RGB、`q(t)` 和 `q(t+1)`；trace/provenance 被复制至 `meta/rmbench/`，不成为训练列。

## 已验证

- RMBench：`compileall`、`validate_demo_clean_state.py --help`、`git diff --check` 通过。
- openpi：converter 与 robot-only adapter 子集 `13 passed, 32 deselected`；`ruff check` 通过；两个 N config 已在 CPU materialize，确认 H50、bs32、20k、robot-only sidecar。
- 修改 provenance 存储位置前的 2 集 smoke 曾通过：observe 2/2，swap_T 2/2；新 commit 将 provenance 从 info 路径移出，因此必须在本提交上重新跑两任务的 2 集 gate，之后才能启动正式 50 集。

## 来源与合同

- 实查未发现两任务可复用的成品 `demo_clean_state` source；正式数据将使用非 eval 的自然数尝试 seed（0 起），并保存 planning/replay 成功、失败和筛选记录。正式 eval seed 范围 `100000..100099`、`200000..200099`、`300000..300099` 已显式排除。
- `observe_and_pickup` 保存 reference `(modelname, model_id)`、全部 candidate pair、初始 pose 和真实 occlusion-wall frame；这些都只在 source provenance。
- `swap_T` 保存 actor-origin 初始 pose、逐帧当前 pose、Sapien `wxyz` quaternion 和 `[x,y,yaw]`。首帧落稳 pose 与 actor-origin 在旧 smoke 中相差约 red 1.96 cm、blue 2.18 cm；Manager 需冻结 canonical initial source。
- `MEMORY_SCHEMA_DRAFT.zh-CN.md` 只是一份待裁决草案。J/S 未实现；现有 serial runtime 不能承载连续 swap pose，不能量化为 categorical 代替该问题。

## 当前阻塞与下一条命令

截至 2026-09-14 19:44 CST，`wuwen-1` 的 GPU0--7 均约 74 GB/80 GB 已用且 100% 利用率。任务要求使用该机实际空闲卡，因此未抢占，也未启动新的 smoke、正式 50 集或 20k 训练。

有空闲卡后，在 RMBench worktree 执行并先验证：

```bash
.venv/bin/python experiments/wave1_missing_tasks_a/collect_demo_clean_state.py observe_and_pickup --smoke --gpu <gpu>
.venv/bin/python experiments/wave1_missing_tasks_a/validate_demo_clean_state.py observe_and_pickup --source-root data/observe_and_pickup/demo_clean_state_smoke --expected-episodes 2 --write-report
.venv/bin/python experiments/wave1_missing_tasks_a/collect_demo_clean_state.py swap_T --smoke --gpu <gpu>
.venv/bin/python experiments/wave1_missing_tasks_a/validate_demo_clean_state.py swap_T --source-root data/swap_T/demo_clean_state_smoke --expected-episodes 2 --write-report
```

smoke 通过后，用 `setsid` 分别启动两个 `--full` collector，立即以真实 PID 执行 `mam job add f0011538-fbad-49f6-b117-4d628f2bf30c ...`。正式 source 完整性、转换、N sidecar 与 norm stats 经 Manager 验收前，不启动训练。
