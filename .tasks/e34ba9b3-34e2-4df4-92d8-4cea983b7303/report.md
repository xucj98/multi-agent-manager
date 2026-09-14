task_revision: 25c8959f56be40bada047087d4572bff069aba76

# V 工程、真实 CPU 准入与 P1 修复交付

完成既定 V 的真实五任务 CPU 输入准入、非空两步容量 profile 候选，以及 review `a98a1d8e-bf13-4316-9425-18389580fc6c` 指出的运行时 P1 修复。未启动 GPU、两步 smoke、20k 训练或闭环评测；没有登记长进程。

## 交付 commits

| 仓库 | worktree | 交付 commit |
| --- | --- | --- |
| OpenPI | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/openpi` | `66d9253cf1bdc4971e59cdae7827846eccdb4714` |
| RMBench | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/RMBench` | `f402babca5e7621be83f1725033e858aef69d091` |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/robot-bridge` | `20dae84e5fc2e48f93e72b5c1b8a0001071fec94` |

原 V 交付保持在 OpenPI `96e37e840f196d3b0945994d9a9bb5980d25ca58`、RMBench `a03fd1c3a40ac89542b7afe80d7188acd3dc2bd9`、robot-bridge `20dae84e5fc2e48f93e72b5c1b8a0001071fec94`；本轮只追加 OpenPI `dd6b4866eef80d76adbb5ed6eccc349ceca8c32f` / `66d9253cf1bdc4971e59cdae7827846eccdb4714` 和 RMBench `f402babca5e7621be83f1725033e858aef69d091`。三条 worktree 均为干净状态。

## Review P1 响应

- `VisualHistoryRuntime` 的 pending 现在绑定 episode generation 和 cache revision。reset 后的 late commit、或已被另一个提交取代的 pending 都会明确拒绝，不会把旧 episode 图像写入新 cache。
- V `Policy` 用 reentrant lock 覆盖 prepare、model sample、commit、reset 和 JAX RNG 更新；并发 infer/reset 不能反序完成或跨 episode 泄漏。
- reset 后首个 runtime 输入强制 `visual_history_frame_id.logical_step=0`，因此不能把晚到帧当 episode anchor。
- `VisualHistoryLeRobotDataset` 改为 16-frame LRU，并只解码最近四个 prior query、anchor 和 current；不会随整个 persistent worker 生命周期增长。
- V formal recipe 固定 `save_interval=20000`、`save_full_state=False`、`save_dtype="bfloat16"`。它保留 N/S/J 的 model-only 合同：完成 checkpoint 可按 metadata 做 policy restore，不支持 optimizer resume。两步 profile 强制 `save_interval=2`，其 CPU metadata restore gate 会核验该合同。

新增回归覆盖 reset→late commit、pending completion 反序、首帧非零 step 拒绝、policy infer/reset 串行化、LRU 上限，以及 formal/smoke checkpoint 参数。

## 五个真实 CPU 输入结果

证据文件为 RMBench `experiments/pi05_visual_history_v/cpu_preflight_20260914.json`。全部从 OpenPI `66d9253…` 以 `JAX_PLATFORMS=cpu` 执行：每行 50 episodes、三路 `[3,480,640]` RGB、raw state/action `[32]` 的前 14D robot prefix、K=30、实际 batch 32 和全部 18 图槽通过；模型侧 state/actions 分别为 `[32,32]` / `[32,50,32]`，norm 输入仍为 14D。

| task | query rows | N robot norm SHA-256 | batch 后 RSS MiB |
| --- | ---: | --- | ---: |
| `rearrange_blocks` | 700 | `5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b` | 1650.27 |
| `put_back_block` | 609 | `7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261` | 1726.64 |
| `swap_blocks` | 1,018 | `acb30919ff4be931da9c62173959971f9944bfc6d304ee80ab09448d79f6b336` | 1927.45 |
| `battery_try` | 1,111 | `5ebaa98a5bf1151f9480811173cf5cd4de0a5e53ca6e123dea75a997bbb0be89` | 1843.65 |
| `cover_blocks` | 1,718 | `ca4cf5ffdf648b61bcfa63e40532ab285b1368ceff728efa53fafa60bd27e551` | 2076.14 |

每个 worker 的 cache 都实际到达上限 16，decoded raw RGB arrays 为 `176,947,200` bytes；RSS 是 CPU loader 的观测值，不能代替 GPU 容量 profile。每行还核验 metadata、converter 和 N checkpoint 内 norm copy 的 SHA-256。

`observe_and_pickup`、`swap_T` 保持数据 owner `f0011538-fbad-49f6-b117-4d628f2bf30c` pending；`blocks_ranking_try`、`press_button` 保持 `2a792e9a-9fbe-4334-bf8e-b7e293bdd64a` pending。它们没有假 repo、假 norm 或 runnable job。

## 容量 profile 与 formal 候选

- `jobs_smoke_candidates.json` 现在只有一个 `rearrange_blocks` technical capacity profile，状态为 `pending_manager_authorization`。它固定 batch 32、H50/K30、三相机、source 分辨率、18 槽、真实 repo、matching N asset/hash、OpenPI `66d9253…`、robot-bridge `20dae84…` 和 RMBench 基线 `a03fd1c…`。
- 候选实际命令显式传入 `--visual-history-smoke --num-train-steps=2 --save-interval=2`；step-2 checkpoint 只能作为 `technical_smoke`，不可 formal/eval。receipt 固定写入候选 JSON 中的 `profile_receipt_path`，要求 peak GPU memory、init、两次 step、save、恢复后 18-slot inference mean/p95、source commits、norm hash、restore result 和 GPU identity。
- `jobs_formal_candidates.json` 仍为 `jobs: []`。模板固定 20k / batch 32 / seed 0 / `--save-interval=20000` / BF16 model-only，不会启动任何正式训练。
- 两个 manifest 的 pure validator dry-run 都返回 `gpu_started: false`；本轮没有执行候选命令。

## 验证

```text
PYTHONPATH=src JAX_PLATFORMS=cpu .venv/bin/pytest -q -m 'not manual' \
  src/openpi/training/visual_history_test.py src/openpi/training/config_test.py \
  src/openpi/training/checkpoint_metadata_test.py src/openpi/training/data_loader_test.py \
  src/openpi/policies/policy_test.py src/openpi/models/pi0_test.py
# 49 passed, 2 deselected

JAX_PLATFORMS=cpu PYTHONPATH=src .venv/bin/python scripts/visual_history_preflight.py \
  --output /tmp/v_preflight_all_runtime_fix.json
# 5 rows written; CPU only

python experiments/pi05_visual_history_v/validate_candidates.py \
  --manifest experiments/pi05_visual_history_v/jobs_smoke_candidates.json --dry-run
python experiments/pi05_visual_history_v/validate_candidates.py \
  --manifest experiments/pi05_visual_history_v/jobs_formal_candidates.json --dry-run
# both gpu_started: false
```

OpenPI changed-file Ruff、RMBench validator Ruff、JSON parsing、`py_compile` 和各 worktree `git diff --check` 均通过。候选 CLI 也以完整 nested repo/asset/smoke/save flags 做了 CPU-only config parse，未调用 `scripts/train.py`。

实际 step-2 checkpoint 尚不存在，因此候选中的 `--check-checkpoint` restore gate 尚未运行；CPU checkpoint metadata roundtrip 已覆盖该保存合同。GPU profile、formal training、policy runtime restore of a generated checkpoint 和评测都仍需 Manager 准入。修复 commit 已备好供 review `a98a1d8e-bf13-4316-9425-18389580fc6c` 复查，本执行者不等待 review 结果。
