# observe_and_pickup / swap_T 进度交付（正式采集中）

## 已提交的工程交付

- RMBench worktree：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/RMBench`
  - commit `05e512f529a4dea393d2f730b1f34ed6d5b5f212`
  - 两任务的 source-only 逐帧 trace、独立 `collection_provenance/episode<N>.json`、确定性 seed/attempt 记录、2 集 smoke/50 集正式入口、完整性验证器和 schema 草案。
  - provenance 在 replay 结束且环境关闭前冻结；不再写入 `play_once()` 的 `info`，避免进入 RPC/在线 policy 路径。断点恢复仅在 HDF5、trace 与 provenance 全部存在时跳过该集，半成品会保留并显式报错。
- openpi worktree：`/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/openpi`
  - commit `6c0501725dc4d244d813db18edaaba9fe69fafeb`
  - 14-D robot-only LeRobot converter、N sidecar、两个 no-memory YAML 与 pi0.5 H50/K30、bs32、20k、seed0 配置。
  - N 只写当前 RGB、`q(t)` 和 `q(t+1)`；trace/provenance 被复制至 `meta/rmbench/`，不成为训练列。

## 已验证

- RMBench：`compileall`、`git diff --check` 通过。
- openpi：converter 与 robot-only adapter 子集 `13 passed, 32 deselected`；`ruff check` 通过；两个 N config 已在 CPU materialize，确认 H50、bs32、20k、robot-only sidecar。
- 新 commit `05e512f` 的 2 集 gate 已完成并由 `validate_demo_clean_state.py` 通过：
  - `observe_and_pickup`：seed `0,1`，各 150 帧；真实 occlusion wall 均为 saved frame 44，前 44 帧 reference 可见，candidate identity/provenance 完整。
  - `swap_T`：seed `0,1`，344/348 帧；actor-origin 与首帧落稳位置差分别约 red `1.9636 cm`、blue `2.1846 cm`，两种来源均已保留。

## 来源与合同

- 已实际读取 `/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md` 与 `ASSET_AUDIT.zh-CN.md`。后者确认这两个任务均无 `demo_clean_state` source 或 converted cache；此前仅搜索 `/mnt/public/xcj` 而声称资料缺失是错误，现已更正。
- 正式数据使用非 eval 的自然数尝试 seed（0 起），保存 planning/replay 成功、失败和筛选记录。正式 eval seed 范围 `100000..100099`、`200000..200099`、`300000..300099` 已显式排除。
- `/root/.cache` 已确认链接至 `/mnt/public/xcj/cache`，当前 `HF_LEROBOT_HOME` 未设置。
- `observe_and_pickup` 保存 reference `(modelname, model_id)`、全部 candidate pair、初始 pose 和真实 occlusion-wall frame；这些只在 source provenance。
- `swap_T` 保存 actor-origin 初始 pose、逐帧当前 pose、Sapien `wxyz` quaternion 和 `[x,y,yaw]`。Manager 仍需在 actor-origin 与首帧落稳值之间冻结 J/S 的 canonical initial source。
- `MEMORY_SCHEMA_DRAFT.zh-CN.md` 是待裁决草案。J/S 未实现；现有 serial runtime 不能承载连续 swap pose，不能量化为 categorical 代替该问题。

## 正式采集进度

根据 Manager 明确授权，本机 GPU4/5 在启动前实查为 0% 利用率、分别约 66.3/54.3 GB 空余；B 组没有登记 GPU job 或 collector 进程。两条长任务已用 `setsid` 启动并立即登记：

| task | GPU | MAM job | PID | 启动状态 | 日志 |
|---|---:|---|---:|---|---|
| `observe_and_pickup` | 4 | `9964b617-dcdc-48eb-9cd7-38bf6f7fd5c9` | `1478749` | running；50 个 planning seed 均已成功，replay 中 | `logs/wave1_missing_tasks_a/observe_and_pickup_full_20260914T195822.stdout.log` |
| `swap_T` | 5 | `a7b7eb97-5c5b-4803-a448-024b92afbd43` | `1498697` | running | `logs/wave1_missing_tasks_a/swap_T_full_20260914T200406.stdout.log` |

50 集 source 完成后将先运行完整性验证，再处理为 HDF5/LeRobot、生成 N sidecar 和 `--max-frames 10000` norm stats。20k 训练尚未启动，仍待该数据交付和 Manager 准入。
