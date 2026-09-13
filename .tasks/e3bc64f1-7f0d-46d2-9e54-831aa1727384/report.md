# 第一波 N 训练与 J/S Memory-v1 接入进展

## N：已接受的 50-step gate

N 的冻结实现树保持不变：

- `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/openpi`：`867aa05e428d6ce259fba99f55def3b5b4fce951`，未修改。
- 实际训练使用独立 loader 执行树 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/loader/openpi`：clean `5835fa04055d520e418cc1448c1bd58fa1e665cb`。

Manager 已独立复核 loader projection 修复及真实 loader 证据，并接受三条 N 的 50-step gate。最终成功 smoke 结果根：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_smoke_5835fa0_nocmdbuf_20260913T0923Z`

| task | GPU | config | step-50 loss | checkpoint-only 恢复 |
| --- | ---: | --- | ---: | --- |
| swap_blocks N | 0 | `pi05_rmbench_swap_blocks_no_memory` | 0.0375 | CPU params + GPU policy 通过 |
| battery_try N | 2 | `pi05_rmbench_battery_try_no_memory` | 0.0431 | CPU params + GPU policy 通过 |
| cover_blocks N | 4 | `pi05_rmbench_cover_blocks_no_memory` | 0.0356 | CPU params + GPU policy 通过 |

三个 smoke 都使用真实数据、seed 0、batch 32、H50/K30、现有 robot-only norm、model-only BF16、default cache，且 `HF_LEROBOT_HOME` 未设置。每个 checkpoint 只有 `_CHECKPOINT_METADATA`、`assets`、`metadata`、`params`，没有 `train_state`。独立 CPU 恢复均验证 51 leaves、3,353,433,872 elements、6,706,867,744 bytes、完整 shape、BF16 和 finite；独立 GPU `create_trained_policy_from_checkpoint` 恢复均产生 finite `[50,14]` actions，且审计钩子拒绝读取训练 dataset/base checkpoint/source assets。

完整 receipt（含日志哈希、配置和 validation script 哈希）：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_smoke_5835fa0_nocmdbuf_20260913T0923Z/validation/wave1_n_smoke_receipt.json`

wuwen-1 的 NVIDIA driver 为 535.54.03（CUDA 12.2），jax/jaxlib 为 0.5.3。默认 CUDA command-buffer 路径在首次 smoke 的第一步报 CUDA <12.3 不支持，未产生 checkpoint；最终 smoke 和正式 run 均使用 `XLA_FLAGS=--xla_gpu_enable_command_buffer=`。该兼容项保存在各 run 的 `pids.tsv` 和 launcher script 中；现有 `checkpoint_metadata` 环境 allowlist 不保存 `XLA_FLAGS`，因此不把旧 `command.txt` 改写成包含它的记录。

## N：已启动的正式 20k

2026-09-13 17:38:55 CST 已在 wuwen-1 启动三条独立正式训练。它们从 `pi05_base` 初始化，**不**从 smoke checkpoint 续训；使用 clean `5835fa0`、seed 0、batch 32、H50/K30、`save_interval=20000`、model-only BF16、default cache、`HF_LEROBOT_HOME` unset 和上述 XLA 兼容项。

正式结果根：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z`

| task | GPU | PID | MAM job | exp name |
| --- | ---: | ---: | --- | --- |
| swap_blocks N | 0 | 2621614 | `443b3b93-57ba-425e-bbce-f4903fea33c1` | `memory20k_5835fa0_nocmdbuf_swap_blocks_n_s0` |
| battery_try N | 2 | 2621615 | `86f8ee1f-3d30-40f5-ba98-973b18232897` | `memory20k_5835fa0_nocmdbuf_battery_try_n_s0` |
| cover_blocks N | 4 | 2621616 | `1495a251-7d9e-4f68-8afc-0a7cee6360f9` | `memory20k_5835fa0_nocmdbuf_cover_blocks_n_s0` |

三个 job 已以真实远端 PID 登记为 running。下一项验收是 step 100 的有限 loss、实际 GPU 占用和日志 receipt；完成 20k 后再验收 params/metadata/shape/BF16/finite 和独立 checkpoint-only 恢复，并归档 job。尚未启动 J/S 正式训练。

## J/S：待独立 review 的 clean candidate

J/S 在独立开发树 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/js/openpi`，commit：

`afb7a4d0ac20f2cba3c6bb0d5a25c96f792479c3` (`feat(rmbench): add swap battery cover memory schemas`)

该候选添加 swap/battery/cover 的 full per-frame 与 serial lag-30 Memory-v1 YAML、current-truth adapter、config builders 及覆盖测试。语义固定为：swap 的四 phase 与 tray permutation 约束；battery 只使用 phase 并允许 optional `try_11`/`try_01`；cover 的 6 phase 和 red/green/blue 各 4 值，共 18D，保持 14+18=32。full 使用 future per-row phase、offset +1、row-30 tail mask、`fixed_horizon` 和 `last_executed` feedback；serial 使用 lag 30、query target 和 selected/query feedback。

验证：

```text
unset HF_LEROBOT_HOME
JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q \
  examples/rmbench/test_rmbench_memory_adapter.py \
  src/openpi/training/config_memory_test.py \
  src/openpi/training/config_test.py
# 54 passed in 68.61s
```

`ruff check`、`ruff format --check` 和 `git diff --check` 均通过。真实 50 集 source validation 在 candidate 上通过：swap 29,920、battery 32,626、cover 50,904 query rows；三者 state/robot target 均 finite，且 M+1 最后一行重复最后 action。证据目录：

`/mnt/public/xcj/Projects/openpi/assets/memory_v1/js_validation/afb7a4d0ac20f2cba3c6bb0d5a25c96f792479c3/`

该候选尚未生成 semantic sidecar，也未开 J/S 正式训练，等待独立 review。
