# press_button / blocks_ranking_try 数据与 N 接入进度

## 已提交实现

- RMBench worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/RMBench`
  - `f4e84c0252dd777c9f066a401a0970ad4a274c76`：确定性 seed stream、保留 eval seed 拒绝、planning/replay append-only audit、成功 replay 校验、两任务来源记录和 S/J 来源合同草案。
  - `74db6317bb4b690abc7b49258c5a2d402861f1f0`：修正物理 event 到 HDF5 observation 行的对齐；保存边界保留以供复查。
- OpenPI worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/openpi`
  - `2bcf3a1551445d73777a959d5050872a4333f5af`：审计过的 N 转换器、`pi05_rmbench_no_memory` 配置、测试和 CPU norm-stat 入口。

来源合同草案位于：
`RMBench/docs/press_button_blocks_ranking_source_contract_draft.zh-CN.md`。

它将 `press_button` 的可见 card 数字与按 qpos 阈值确认的实际按压事件分开；ranking 仅允许可见 RGB/位置、过去尝试、物理按压和标为 `manager_confirmation_required` 的反馈。采样 permutation、正确排序和 block internal identity 不写入训练行或 provenance。

## press_button：50 条 canonical 原始数据、N 转换和 smoke 已验收

canonical source：

```text
RMBench/data/press_button/demo_clean_state/
```

正式生成 job `b45e86f0-7de1-4647-a5d0-71eeaa73bd7c` 已在通过验收后归档。验收结果写入：

```text
RMBench/data/press_button/demo_clean_state/metadata/acceptance_audit.json
```

证据：

- 恰有 50 条 selected planning trajectories 和 50 条成功 replay。
- training seeds 恰为 `410000..410049`，未使用任一保留 eval seed。
- 50 个 HDF5，合计 26,029 个 observation rows；每条均为 `[rows,14]` joint vector 和同步的 head/left/right RGB。
- 所有 physical press 都由 qpos threshold event 确认，event 的 `frame` 有效，`control_frame_boundary == frame + 1`。
- 可见 card digits、physical events、micro-stage 与离线最终状态均与来源合同一致，未使用隐藏任务数据。

完整转换已经完成。CPU 转换 job
`4f4aa392-7ceb-4d5f-9b72-db78c3160c85` 已归档（正常完成后的进程消失）：

```text
source: RMBench/data/press_button/demo_clean_state/
destination: /root/.cache/huggingface/lerobot/press_button_demo_clean_state_no_memory
log: RMBench/data/press_button/demo_clean_state/metadata/convert_no_memory.stdout.log
pid: RMBench/data/press_button/demo_clean_state/metadata/convert_no_memory.pid
```

该进程为 CPU-only，`HF_LEROBOT_HOME` 未设置、`CUDA_VISIBLE_DEVICES=`。转换器只写 current 14D state、`q(t+1)` 14D action、当前三路 RGB 与确定性 `seen` prompt；不写 memory 或 scene labels。

转换后的全量回读结果：50 episodes、50 Parquet、25,979 rows（26,029 个 source observation rows 减去每集最后一行 target 缺失）、50 个 source hashes/seeds；逐集核验 `observation.state == source q(t)[:14]`、`action == source q(t+1)[:14]`、三路 RGB 同步、14D state/action，manifest 为 `memory: absent` 且 `source_scene_labels_copied_to_rows: false`。job archive note 保留了同一核验结论。

CPU norm stats 已生成：

```text
/mnt/public/xcj/Projects/openpi/assets/pi05_rmbench_no_memory/press_button_demo_clean_state_no_memory/norm_stats.json
sha256=1690aec41ac1a07ff4ea6913463429c943cefb5df83ea23ce1c04e921128f9f0
```

真实 CPU JAX data-loader batch 也已通过，证据为
`RMBench/data/press_button/demo_clean_state/metadata/no_memory_cpu_loader_batch.json`：CPU backend、batch 32，state `[32,32]`（14D state 加 18D zero padding），action `[32,50,32]`，三路图像均 `[32,224,224,3]`，prompt `[32,200]`，值均 finite；`memory_config`、`memory_bindings` 和 key-state input/target 均 absent。该证据 sha256 为 `46e12b832787692709310e85d3517969626f1949c7c01994ee5b451826b9222c`。

按 Manager 验收前置要求，已在 GPU1 完成 N seed0 的 50-step 短 smoke（没有启动正式 20k）：

```text
root: /mnt/public/xcj/Projects/openpi/checkpoints/press_button_n_smoke_2bcf3a1_20260915
run:  pi05_rmbench_no_memory/smoke50_2bcf3a1_press_button_n_s0/50
receipt: /mnt/public/xcj/Projects/openpi/checkpoints/press_button_n_smoke_2bcf3a1_20260915/press_button_n_smoke50_receipt.json
```

50/50 optimizer steps 的 loss、grad norm 和参数 norm 均为 finite；首步 loss `0.2856`，末步 loss `0.0329`，末步 grad norm `0.2516`。checkpoint 已正常 finalize，包含 `params`、`assets`、`metadata` 且没有 `train_state`。CPU checkpoint-only restore 通过（51 leaves、3,353,433,872 elements、全 BF16、全 finite、shape 完整，且拒绝读取训练 source），日志及 receipt 均在上述 smoke root 中。

## blocks_ranking_try：formal 采集仍在运行

MAM job `0a3a2f9c-c590-4f17-9ff7-556b06baf1b0` 正在 GPU3 运行：

```text
RMBench/data/blocks_ranking_try/demo_clean_state/
seed stream: 420000 + attempt_index
max_attempts: 300
```

此前两条 smoke 已通过：seed `420000` 和 `420001` 均为成功 replay，HDF5 分别 555 / 2,431 rows；可见 provenance、物理 event 和 terminal feedback 均可审计，且 `hidden_permutation_or_target_ranking: not_recorded`。

最新状态（截至本报告更新）：formal audit 已完成 50 个 selected planning trajectory；已完成 32 个成功 replay，episode 32 的 replay 正在运行（job PID `1550791`，GPU3）。正式 50 个 replay 全部结束前，不宣称 ranking dataset 就绪；因此尚未进行 ranking 的转换、norm stats 或 data-loader 验证。结束后仍需对所有 50 条做同等级的 row/event/provenance/leakage audit，再独立转换为 N 数据并验证。

## 已完成验证

- RMBench：`PYTHONPATH=. .venv/bin/python -m py_compile script/collect_data.py envs/_base_task.py envs/press_button.py envs/blocks_ranking_try.py` 和 `git diff --check` 通过。
- event 对齐回归：control boundary `0, 1, 65, 629` 分别映射 HDF5 行 `0, 0, 64, 628`。
- OpenPI：

  ```bash
  PYTHONPATH=. .venv/bin/python -m pytest -q \
    src/openpi/training/config_test.py \
    examples/rmbench/test_convert_rmbench_no_memory_to_lerobot.py
  ```

  结果为 `12 passed`。
- post-commit press smoke 已回读为 2 episodes / 1,155 rows / 14D state-action / 三路 `(3,480,640)` RGB，manifest 为 `memory: absent` 和 `source_scene_labels_copied_to_rows: false`；其 CPU-only norm stats 已成功。

## 等待 Manager 的科学裁决与后续受控步骤

N 使用当前图像和 14D robot state、无任务 memory；配置固定 pi05 base 新初始化、seed 0、batch 32、20k steps、H50/K30 metadata。S/J 的来源合同目前仅为草案，不能视为最终科学合同。

press_button 的正式 N 训练命令已准备但未启动，需 Manager 验收本报告后执行：

```bash
CUDA_VISIBLE_DEVICES=1 JAX_PLATFORMS=cuda \
XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 \
OPENPI_DATA_HOME=/mnt/public/cache/openpi \
env -u HF_LEROBOT_HOME PYTHONPATH=. \
.venv/bin/python -u -B scripts/train.py pi05_rmbench_no_memory \
  --checkpoint-base-dir=/mnt/public/xcj/Projects/openpi/checkpoints/press_button_n_formal_2bcf3a1_20260915 \
  --exp-name=memory20k_2bcf3a1_press_button_n_s0 \
  --num-train-steps=20000 --save-interval=20000 --log-interval=100 \
  --seed=0 --batch-size=32 --no-wandb-enabled
```

在不启动训练的前提下，两个数据集各自完成时会依次提供：完整性审计、来源/标签合同、CPU norm stats、一次真实 CPU data/training-pipeline batch 和短 recovery/training candidate，供 Manager 验收后再决定是否准入训练。
