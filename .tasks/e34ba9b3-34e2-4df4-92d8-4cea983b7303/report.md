task_revision: b361eb600b45611f223a8b99e91fbda661f69d26

# V 工程、CPU 准入与双卡容量 profile 交付

已完成既定 V 实现、五项真实 CPU 输入准入、P1 runtime 修复，以及 Manager 授权的 wuwen-11 GPU0/1 双卡 FSDP 两步容量 profile。双卡在首次 optimizer update 真实 OOM，未生成 step-2 checkpoint；因此 metadata gate、checkpoint-only policy restore、18-slot `[50,14]` 推理、推理显存和 CPU RSS 都没有运行。没有启动 20k formal、评测、额外 GPU profile，未使用 GPU4/GPU6，也没有扩大卡数或修改 batch、图像槽、相机或分辨率。

## 交付 commits

| 仓库 | worktree | 交付 commit |
| --- | --- | --- |
| OpenPI | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/openpi` | `66d9253cf1bdc4971e59cdae7827846eccdb4714` |
| RMBench | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/RMBench` | `4db38c1f936c3e1bed1c85114d8173b07a472243` |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/robot-bridge` | `20dae84e5fc2e48f93e72b5c1b8a0001071fec94` |

OpenPI 的 V 实现与 P1 修复保持在 `96e37e8…`、`dd6b486…`、`66d9253…`；RMBench 的 CPU 准入候选基线为 `f402bab…`，本轮增量 `4db38c1…` 只记录双卡结果、保留旧单卡证据并扩展纯 JSON validator。三条本地源码 worktree 均干净。

## V 工程与真实 CPU 输入

- `VisualHistoryRuntime` 的 pending 绑定 episode generation/cache revision；reset 后 late commit 与被更新 pending 都会拒绝。V policy 用 reentrant lock 串行化 prepare、sample、commit、reset 和 JAX RNG；episode 首次 infer 强制 `logical_step=0`。
- `VisualHistoryLeRobotDataset` 的 decoded-frame LRU 上限为 16；仅解码 anchor、current 和最近四个 prior query。V 在归一化前只选择 state/action 前 14 维，随后模型补至 32 维。
- `cpu_preflight_20260914.json` 覆盖 `rearrange_blocks`、`put_back_block`、`swap_blocks`、`battery_try`、`cover_blocks`：每项均为 50 episodes、三路 CHW `[3,480,640]`、batch 32、18 槽、H50/K30、matching N 14D norm。query rows 分别为 700、609、1,018、1,111、1,718；norm SHA-256 已在 manifest 及 preflight 中记录。
- `observe_and_pickup`、`swap_T`、`blocks_ranking_try`、`press_button` 保持对应 data owner pending，未填虚构 repo 或 norm。

## wuwen-11 双卡 FSDP 容量 profile

B 端隔离 worktree：`/mnt/public3/xcj/Projects/state-vla/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/openpi`，基于干净 OpenPI `66d9253…`；其受管环境 smoke 通过。启动前 GPU0/1 各有 76,741 MiB 空闲、0% 利用率且无可见 compute PID；GPU4/GPU6 未选用。

实际训练命令使用 `env -u HF_LEROBOT_HOME`、`CUDA_VISIBLE_DEVICES=0,1`、`PYTHONPATH=src`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.95` 和 `--fsdp-devices=2`。mesh 为 `(batch=1, fsdp=2)`，`PartitionSpec((batch, fsdp),)` 将 global batch 32 切为 GPU0 rows 0–15、GPU1 rows 16–31，即每卡 16；eligible 参数与 optimizer tensor 沿 FSDP axis 分片，未形成 data-parallel replica group。

冻结合同保持 Pi0.5、rearrange 的真实 50-demo repo、matching N norm `5d84df27…4478606b`、14D robot inputs、H50/K30、三相机、原始 `3×480×640`、18 slots、global batch 32、seed 0、BF16 model-only；仅增加资源配置 FSDP2 与技术计时所需 `--log-interval=1`。运行名和输出根为 `v_rearrange_blocks_capacity_profile_fsdp2_seed0_rerun1` / `pi05_visual_history_v_capacity_profile_fsdp2_rerun1`，不会覆盖旧 GPU6 单卡 OOM。

结果：模型初始化 240.99 s，profile wall 472.55 s；首次 optimizer update 前 OOM。GPU0 peak 74,747 MiB、minimum free 6,408 MiB、GPU1 peak 74,705 MiB、minimum free 6,450 MiB；两卡 max util 均为 100%。XLA 在 GPU0 与 GPU1 都报告请求 51,561,303,472 bytes（48.02 GiB）。没有完成 update、没有保存 checkpoint、没有 step-2 目录。故无有效 train-step/save 时长，也不能声称 restore、`actions.shape == (50,14)`、inference mean/p95、inference GPU memory 或 CPU RSS。

首个同名前缀启动器因 wuwen-11 缺少 `/usr/bin/time` 在 Python 启动前退出 127；其独立日志已保存，且不计为训练尝试。随后独立 `rerun1` 才是上述真实双卡 OOM。既有 GPU6 单卡收据 `a98_review_failure_20260915/profile_receipt.json` 原样保留，双卡收据不覆盖它。

## 证据、回传和清理

本地独立收据及原始日志位于：

```text
/mnt/public/xcj/Projects/openpi/checkpoints/
  pi05_visual_history_v_capacity_profile_fsdp2_rerun1/
    pi05_visual_history_aloha_v/
      v_rearrange_blocks_capacity_profile_fsdp2_seed0_rerun1/
        profile_receipt.json
        profile_metrics_summary.json
        remote_deployment/
        pre_python_launcher_failure/
```

`remote_deployment` 的 19 个文件已逐项 SHA-256 回传校验；receipt 本身的本地/远端 SHA-256 均为 `0cbfc0ed3af28ec2592bbe370921acee7585302c4a2cc5175af9a87a92de92e6`。没有生成模型或 checkpoint，因此本地 checkpoint-only restore 不适用；B 上仅删除空 checkpoint run 目录，保留轻量 failure evidence。未登记 MAM long job：实际 profile 7.9 分钟，低于 30 分钟阈值。

RMBench `README.md`、`jobs_smoke_candidates.json` 和 `validate_candidates.py` 记录 FSDP2 outcome、旧单卡 receipt 引用、formal 未授权状态和 validator 的 rejected-profile 分支。`jobs_formal_candidates.json` 仍为零个 formal jobs。

## 验证

```text
# B isolated environment
.venv/bin/python scripts/worktree_env_smoke.py
# passed: locked torch, private transformers patches, editable OpenPI

# B no-training mesh check
CUDA_VISIBLE_DEVICES=0,1 ... fsdp_devices=2
# device_count=2; mesh={batch:1, fsdp:2}; global32 -> 16/card; 18 keys; H50/K30

# RMBench result metadata
python experiments/pi05_visual_history_v/validate_candidates.py \
  --manifest experiments/pi05_visual_history_v/jobs_smoke_candidates.json --dry-run
python experiments/pi05_visual_history_v/validate_candidates.py \
  --manifest experiments/pi05_visual_history_v/jobs_formal_candidates.json --dry-run
# both gpu_started=false

# changed validator
openpi/.venv/bin/ruff check experiments/pi05_visual_history_v/validate_candidates.py
python -m py_compile experiments/pi05_visual_history_v/validate_candidates.py
git diff --check
# passed
```

双卡容量证据应交回原独立 review 增量验收；Manager 如需继续，只能在新授权下决定资源或冻结合同的后续处理。

## 2026-09-22 文件与交付状态

- `.tasks/e34ba9b3-34e2-4df4-92d8-4cea983b7303/` 仅有已跟踪的 `task.md` 和 `report.md`，没有未跟踪或 ignored 附件，无需迁移旧收据。
- 三个登记 commit 均存在于各 primary repository，但尚未进入 primary HEAD：OpenPI `66d9253cf1bdc4971e59cdae7827846eccdb4714`、RMBench `4db38c1f936c3e1bed1c85114d8173b07a472243`、robot-bridge `20dae84e5fc2e48f93e72b5c1b8a0001071fec94`；归档前需要 Manager 决定合入或保留相应 task/review 分支。
- V 当前搁置且没有未归档 job。归档前仍需 Manager 决定将搁置任务关闭、处置上述代码交付，并在授权时发布本段 report 草稿；本轮未更改 workspace、运行或审查。
