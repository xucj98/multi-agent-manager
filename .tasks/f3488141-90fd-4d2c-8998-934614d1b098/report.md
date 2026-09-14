# 六个首波 N/J 模型的 Cluster-C 评测执行（C1 runtime repair 运行中）

六个 20k checkpoint 已传输并验收，冻结 runtime 为 RMBench `ad7f9d6ba9acd16c31243ad4811e0dfa31cef514`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。C3 的 `c3-highfreq-engineering-20260914` 未被读取、修改或删除；没有启动训练、GPU smoke 或 formal。

本机 18 项 prepare、smoke dry-run 和 formal dry-run 已通过。它们固定 train seed 0、eval seed 0/1/2 对应 100000/200000/300000 起点、H50/K30、`demo_clean_eval`、首次 infer 90 秒与后续 30 秒。checkpoint schema 经 `load_train_config → _runtime_metadata → MemoryContext` 恢复，没有 GT memory 注入或按 task 名猜字段。六个 C checkpoint 的文件数和 `_CHECKPOINT_METADATA` SHA 已验收，未传数据集、pi05 base、训练缓存或 HF 资产。

## 首项已具备的执行门禁

`swap_blocks` N、eval0 的 prepare 和 smoke dry-run 已在 C1 成功完成。其候选为：

- smoke：`c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r1`
- formal：`c_wave1_swap_blocks_n_trainseed0_evalseed0_100ep_r1`
- checkpoint：`.../pi05_rmbench_swap_blocks_no_memory/memory20k_5835fa0_nocmdbuf_swap_blocks_n_s0/20000`
- audit：`RMBench/.local/memory_schema_eval/inputs/swap_no_memory--57835512d288ff62--train0--eval0/input_audit.json`

该 dry-run 的 metadata 已确认 `pi05_rmbench_swap_blocks_no_memory`、无 memory fields、`demo_clean_state` 来源、H50/K30、environment seed 起点 100000。输出位于 C1 task workspace 的 `c_protocol_preparation/00_swap_blocks_n_eval0_smoke_dryrun.stdout.json`。

## C1 共享 Python 缓存故障与修复

旧 CPU-only job `f3ad56f9-7766-46ee-8a98-110a3ba9d297` 已归档。它先完成上述首项 smoke dry-run，之后在 formal dry-run 的 Python 导入中反复进入 `wait_on_page_bit_common`；证据显示阻塞跨越 `wandb`、`pandas`、`multiprocess`、`fsspec`、`polars`、`aiohttp`，并最终定位到共享 Python 3.11 标准库 `bz2.pyc` 和 NumPy OpenBLAS 文件。它不是 checkpoint、schema 或 GPU 问题。

证据与局部精确副本位于：

```text
/mnt/public/xcj/Projects/state-vla/workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/c1_uv_cache_read_repair_20260915/
```

其中 W&B `0.19.11`（911 文件、68,306,476 bytes）、其运行时依赖闭包、NumPy（916 文件、64,653,996 bytes）和 Python 3.11 标准库（1,260 文件、30,731,458 bytes）均已从 C2 精确复制到 C1 本机根盘并完成源/目标清单哈希核验。局部 probe 因后续任意共享包仍可阻塞，证明单包补丁不足。

当前登记 job `cc6d002a-249b-4f7a-a9c4-d5fa06128ab1`（C1 PID `1889131`）以低 I/O 优先级从 C2 顺序物化三套冻结 venv 的完整 site-packages 及 CPython 3.10 标准库到 `/root/state-vla-local-overlay/f3488141-90fd-4d2c-8998-934614d1b098/`。它使用参数化、白名单 source streamer；每项先断言 C2 source path、落地后检查 runtime sentinel。首次 OpenPI 传输已确认进入正确的目标树（约 317 MB 时观测），没有修改共享 uv cache、venv、三库源码、checkpoint 或 C3 runtime。此前一次错误归档 C2 home 的 task-local 临时副本已立即清除，receipt 已保留；该 job 已归档且未影响 runtime。

完成后将以按解释器版本选择本机 stdlib、按 venv 选择本机 site-packages 的 task-local `sitecustomize` 启动 shim 验证 OpenPI、bridge 和 RMBench worker；不使用 `PYTHONHOME`，因此 venv `sys.prefix` 保持冻结 runtime。通过 CPU import 与真实 smoke 基础设施门禁后才启动 GPU。

## 已批准的真实 GPU 队列

首波 eval0 固定卡位：GPU1 swap N、GPU2 swap J、GPU3 battery N、GPU4 battery J、GPU5 cover N、GPU6 cover J；GPU7 备用，GPU0 禁用。每卡一 lane，先启动 GPU1 真实 smoke 验证本机覆盖层、端口和 policy load，再错峰启动其余五项。每项 smoke 通过后自动启动自身 matching formal100，formal 的真实 PID 立即登记 MAM；失败保留全部结果和诊断并停止该 lane。随后按同样映射执行 eval1、eval2。

## 2026-09-15 C1 GPU1: r1 failure preserved, local selector repair, r2 smoke started

`c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r1` created a result leaf but is **not** an accepted smoke: it completed zero rollouts after the RMBench worker `get_metadata` RPC timed out during robot startup. The leaf, process logs, `_result.txt`, diagnostics and SHA-256 receipt remain at the C1 result path; it is not reused by any later formal.

The repair stays outside all three repositories. The C2-validated local source/package/stdlib overlay now has task-local Python-home wrappers for Python 3.10 and 3.11. They select local stdlib before interpreter startup, prepend the task bootstrap for spawned workers, and retain the frozen venv `sys.prefix` and `sys.executable`. CPU probes passed for the real bridge→RMBench worker metadata handshake, OpenPI/bridge imports, NumPy/JAX/SAPIEN, source commits and the exact r2 dry-run. No source, dependency, checkpoint, HF/C3, GT-memory or reset behavior changed.

Fresh r2 commands were generated without changing r1:

- smoke: `c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r2`
- matching formal: `c_wave1_swap_blocks_n_trainseed0_evalseed0_100ep_r2`

Its GPU1 preflight passed (frozen commits, clean C2 worktrees, five transformer patches, checkpoint identity, GPU1 and ports 19410/19412). The real r2 smoke launched on C1 with outer PID `1900152`; its result leaf was created, robot service reached 19410, and the policy restored the 6.2 GiB checkpoint with about 10.1 GiB allocated on GPU1. At this report update it is still finishing policy startup before the 19412 listener and first rollout. Formal has not started and will use r2 only after two accepted rollout/identity checks; its real PID will be registered immediately.

Evidence is under C1:

```text
workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/c1_uv_cache_read_repair_20260915/full_overlay_validation_20260915/
```
