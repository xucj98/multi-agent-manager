# 2026-09-22 清理交接（当前有效）

本轮仅清理文件并核对交付，未启动训练、eval、数据生成或 GPU smoke。`.tasks/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/` 无未跟踪附件，不需留存或提交新的一次性审计材料。

- 已删除 workspace 内 119,400 个可再生或重复文件（清理前 `du` 约 15.809 GiB）：`data_smoke/`、`data_smoke_postcommit/`、`checkpoint-transfer-20260920/`、两个 `.venv`、pytest/ruff 缓存及 15 个 `__pycache__` 目录。环境中存在跨 workspace hardlink，实际释放磁盘空间可能小于此逻辑占用。误识别的 6 个 tracked `.worklogs/` 文件已立即从 HEAD 恢复并保留。
- 稳定产物存在且未修改：50 集原始数据为 `RMBench/data/press_button/demo_clean_state` 和 `RMBench/data/blocks_ranking_try/demo_clean_state`；转换数据为 `/mnt/public/xcj/cache/huggingface/lerobot/{press_button_demo_clean_state_no_memory,blocks_ranking_try_demo_clean_state_no_memory,swap_T_demo_clean_state_shared_memory}`；20k checkpoint 为 `openpi/checkpoints/{press_button_n_formal_2bcf3a1_20260915,blocks_ranking_try_n_formal_2bcf3a1_20260920,swap_T_n_formal_retry1_ec86d857_20260920}`。三个 checkpoint 都有已提交的 `20000` 目录。
- 代码还未交付到业务主 checkout：RMBench `74db6317...` 和 OpenPI `2bcf3a155...` 仅由本 task 分支持有，均非当前 primary HEAD 的祖先。在 Manager 协调合入或保留可以承载代码的 ref 前，不能 archive 并删除任务分支。
- MAM stopped jobs `8a828bdf-4711-400e-89c3-1526b1694f22`（`blocks_ranking_try N`）与 `f39ba4a8-a6ca-4b6c-9cd2-b6a9f5330a57`（`swap_T N retry1`）均已 archive。对应 PID 的最后观测为不存在；定稳日志与上述稳定 `20000` checkpoint 的 `_CHECKPOINT_METADATA` 支持训练完成和 checkpoint finalize。两条 archive note 均明确记录已有 CPU restore PASS，本轮未重做 restore。
- workspace 现仅留 clean 的登记 RMBench/OpenPI worktree；剩余 ignored 项都是稳定产物软链接或 `.local` 入口，符合 MAM archive preflight。两个 job 阻塞已解除；在 Manager 协调代码合入或保留承载 `RMBench 74db6317...` 与 `OpenPI 2bcf3a155...` 的 ref 前，仍不得 archive task。

---

# N 训练状态与 J/S 可观测性审计

已按 task revision `4891522ffe0f1d87a39e84681bee32fe9347f760` 完成四任务 J/S 启动前审计。审计是只读的，未改 raw 数据、N rows 或评测产物。**四个 J/S lane 均为 BLOCKED，未启动任何 J/S smoke 或 formal。**

完整逐集证据：

`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/checkpoint-transfer-20260920/js_observability_audit_20260920.json`

该 JSON 覆盖 4×50 episodes 的 source path、首次可见帧、可见性/遮挡风险、online/source-only 判定、unknown mask、S/J target time、连续表示和逐事件 frame/boundary 检查。SHA-256 为 `3c3672a2f9601ca7ba1838d6f13bfa0e025ef843d445ea65ce27d7486de6df1c`；生成脚本为 `audit_js_observability.py`，SHA-256 为 `7b9a1b402b66e6a26ed07f3794f7672f4e0ffe298fc94b64ea02b67d2ff2c4f5`。

## 审计结论

| Task | 可见事实与时间 | 阻塞原因 | J/S |
| --- | --- | --- | --- |
| `observe_and_pickup` | reference 在 HDF5 RGB frame 0–43 可见，wall 在 frame 44 出现；50/50 trace 与 HDF5 一致 | exact `(modelname, model_id)` 只在 provenance；HDF5 无 instance ID/segmentation，23/50 含同 modelname distractor。遮挡后当前 observation 无法重新辨认 exact ID。 | BLOCKED |
| `swap_T` | 红/蓝 T 在 frame 0 可见，50/50 `state_trace` 行数与 HDF5 一致 | exact xy/yaw 与 phase boundary 只在 `validation_report/state_trace`；first visible actor origin 与 recorded initial pose 相差 1.9635–2.1847 cm，不能把 provenance pose 当作当前 observation。 | BLOCKED |
| `blocks_ranking_try` | RGB 初始三色块/按钮可见；186 physical press 和 186 feedback 事件均满足 `boundary = frame + 1` | HDF5 无 button qpos 和 terminal feedback；`last_feedback` source contract 明示 `manager_confirmation_required`。此外 raw `press_count_after` 最大 6，与冻结的 `attempt_count: 0–5` 不兼容。 | BLOCKED |
| `press_button` | 初始 RGB 可见数字卡和三按钮（episode 0 为 8、2）；441 physical low-qpos events 均与 HDF5 frame/boundary 对齐 | HDF5 无 environment button qpos，也无 reset/release event。release 只能由 expert source code 与 micro-stage end 推断，不能作为在线观察；13 个 press 和 8 个 inferred release 正好落在 K30 边界。 | BLOCKED |

所有字段均遵守：S 只可使用 `query-30` 时已可得的信息；J 的 `query+1..query+50` 仅为 target，episode tail mask，不能将未来 event/feedback 放入输入。

### press_button 边沿编码

要求的每个按钮采用 `(released_count, pressed_count)` 作为有序 pair：`00 → 01 → 11 → 12 → 22` 分别表示初始、第一次低位按下、第一次回弹完成、第二次低位按下、第二次回弹完成。明确记作 `L=(left_release_edges,left_press_edges)`、`M=(middle_release_edges,middle_press_edges)`、`C=(confirm_release_edges,confirm_press_edges)`：每个 pair 的第一位是已确认回弹/reset 边沿数，第二位是已确认 `qpos < -0.005` 按下边沿数。三个 pair 各自独立，count 范围 0–9，另有显式 unknown mask。

本 source 只保存低位 threshold event（`qpos < -0.005`）和 `press_count_after`，没有 `qpos > -0.001` reset 的逐帧 trace。left/middle 的 source-code reset 位于 press boundary 后 10 或 11 帧的 micro-stage end，confirm 没有后续 release trace。因此目前只能离线标出 press edge；`01→11` 等 release transition 必须是 unknown/source-only，不能将 `event_derived_final_state` 或最终正确次数作为在线输入。

## 需要 Manager 决策或补充的 source

1. 为 observe 提供并验证视觉 identity/matching 表示，或者保持 exact `target_identity` 为 unknown。
2. 为 swap_T 提供可验证的在线 pose extractor 和 phase event series，或者保持 xy/yaw/phase unknown。
3. 决定 blocks 的真实 physical press/terminal feedback 是否可作为在线 callback；将 attempt count 域修正为 raw 覆盖的 `0..6` 或重新定义该字段。
4. 在 press_button runtime 逐帧保存 button qpos、press threshold、reset/release event 和 HDF5 对齐行，然后重新生成 edge-state sidecar。

## N lanes

### blocks_ranking_try N

真实 formal 进程仍在 wuwen-1 GPU3：PID `2995216`，MAM job `8a828bdf-4711-400e-89c3-1526b1694f22`。它使用 seed 0、batch 32、H50/K30、model-only BF16、空 memory 和 `XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`；日志：

`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/checkpoint-transfer-20260920/blocks_formal.log`

本次核对时已稳定越过 step 5,100。此前转换、norm、CPU loader、50-step smoke retry 和 checkpoint-only CPU restore 均已通过。

已完成的 canonical demo producer job `0a3a2f9c-c590-4f17-9ff7-556b06baf1b0` 与 conversion/gate job `8c8cebda-18ba-4b0a-a4a9-033ef598a327` 已收尾归档；只有 formal N job 保持运行。

### swap_T N

重新核对的 N source 是历史目录名 `swap_T_demo_clean_state_shared_memory`，但 config `pi05_rmbench_swap_T_no_memory` 的 memory fields 为空，LeRobot rows 只有 RGB、14D robot state 和 action；它不是 J/S 数据。manifest SHA-256 为 `8afc1a90fb140cb159a58d6ea7d232dcae0c6a4b76acdc3470878024bbd79e25`，norm SHA-256 为 `9a249ce79bc5f3b744ff666578f79893ac1f8d6b680fa5f378d14b4d4e0c96be`。

本次补做的真实 CPU loader gate PASS：state `[32,32]`、action `[32,50,32]`、三路 image `[32,224,224,3]`、key-state fields absent、norm loaded。证据：

`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/checkpoint-transfer-20260920/swap_T_n_cpu_loader_gate_20260920.json`

首个 formal bootstrap（PID `3007464`、MAM job `c78ce336-db4f-49db-9b40-7d4f2c8f9377`）遗漏 `XLA_PYTHON_CLIENT_MEM_FRACTION`，在 step 1 前 OOM；日志与 failed root 保留，job 已归档。retry1 使用新的 root、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90` 和 command-buffer disable，已在 wuwen-1 GPU1 进入真实训练 step：PID `3008716`，MAM job `f39ba4a8-a6ca-4b6c-9cd2-b6a9f5330a57`。

retry1 checkpoint root：

`/mnt/public/xcj/Projects/openpi/checkpoints/swap_T_n_formal_retry1_ec86d857_20260920`

## Workspace

- RMBench worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/RMBench`，commit `74db6317bb4b690abc7b49258c5a2d402861f1f0`。
- blocks OpenPI worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/openpi`，commit `2bcf3a1551445d73777a959d5050872a4333f5af`。
- swap_T N uses the existing clean worktree `/mnt/public/xcj/Projects/workspace/f0011538-fbad-49f6-b117-4d628f2bf30c/openpi`，commit `ec86d857d075cd8e1dc7aba2445e557d76ab2069`。
