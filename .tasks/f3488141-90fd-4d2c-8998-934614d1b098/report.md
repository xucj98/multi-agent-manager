# 2026-09-22 清理交接核对（manager 审计）

本次只核对本 task 的 `.tasks` 附件、现有简报和保存的 MAM task 记录；没有创建或修改 workspace、远端内容、实验或 job。该目录没有未跟踪附件，也没有待提交 diff；仅有已跟踪的 `task.md` 与本 `report.md`，两者均应保留。没有附件需要提交、迁移或删除。

task 当前仍为 `pending`。保存的 MAM 记录显示 `swap_blocks J` formal job `74f550ad-b8d7-4480-9cde-913cbe640ea5`（C1 GPU2，PID 2162806）和 `battery_try N` formal job `a98c0bc6-e386-4bb4-ad12-651e80407908`（C1 GPU3，PID 2189992）均为 `stopped`，最近检查时间分别为 2026-09-21T20:24:08Z 和 2026-09-21T20:24:09Z，且均未 archive。下方“运行中”文字是 2026-09-20 的历史状态，不作为当前运行结论；本轮未扩展到远端结果审计。

归档当前至少受这两条未归档 stopped job 阻塞，并须由后续负责人按正式结果的稳定留存位置与代码交付状态复核后收尾。未获 Manager 的共享 Git 授权，本次未 commit、publish 或 archive。

# 六个首波 N/J 模型的 Cluster-C 评测执行（C1 GPU1 r3 formal100 运行中）

六个 20k checkpoint 已传输并验收，冻结 runtime 为 RMBench `ad7f9d6ba9acd16c31243ad4811e0dfa31cef514`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。C3 的 `c3-highfreq-engineering-20260914` 未被读取、修改或删除；未启动训练。C1 GPU1 的 `swap_blocks` N/eval0 已完成 r3 smoke 并启动 matching formal100。

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

完整覆盖层物化 job `cc6d002a-249b-4f7a-a9c4-d5fa06128ab1`（C1 PID `1889131`）已完成并归档。它以低 I/O 优先级从 C2 顺序物化三套冻结 venv 的完整 site-packages 及 CPython 3.10 标准库到 `/root/state-vla-local-overlay/f3488141-90fd-4d2c-8998-934614d1b098/`；每项先断言 C2 source path、落地后检查 runtime sentinel。没有修改共享 uv cache、venv、三库源码、checkpoint 或 C3 runtime。此前一次错误归档 C2 home 的 task-local 临时副本已立即清除，receipt 已保留。

最终使用按解释器版本选择本机 stdlib、按 venv 选择本机 site-packages 的 task-local Python-home wrapper；wrapper 设置本机 `PYTHONHOME`、预置 bootstrap，且 CPU probe 已确认 venv `sys.prefix` 与 `sys.executable` 保持冻结 runtime。OpenPI、bridge、RMBench worker 和真实 bridge→RMBench metadata handshake 均已通过后才启动 GPU。

## 已批准的真实 GPU 队列

首波 eval0 固定卡位：GPU1 swap N、GPU2 swap J、GPU3 battery N、GPU4 battery J、GPU5 cover N、GPU6 cover J；GPU7 备用，GPU0 禁用。每卡一 lane，先启动 GPU1 真实 smoke 验证本机覆盖层、端口和 policy load，再错峰启动其余五项。每项 smoke 通过后自动启动自身 matching formal100，formal 的真实 PID 立即登记 MAM；失败保留全部结果和诊断并停止该 lane。随后按同样映射执行 eval1、eval2。

## 2026-09-15 C1 GPU1：r1/r2 失败保留，r3 smoke 已接受，formal100 运行中

`c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r1` 完成零条 rollout 后在 RMBench worker `get_metadata` RPC 超时，不是 accepted smoke。`c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r2` 通过服务、checkpoint 恢复和 metadata handshake，但在首个 reset 前因 task-local source runtime 缺少 `assets/embodiments/aloha-agilex/config.yml` 而失败，亦完成零条 rollout。两者的 result leaf、进程日志、`_result.txt`、diagnostic 和 SHA-256 receipt 均保留，不被 formal 或 r3 复用。

修复范围仅为任务本地覆盖层。C2 稳定 RMBench assets 以 `tar --dereference` 流式复制到 C1 唯一 staging 目录，逐文件 SHA-256 与 C2 manifest 精确匹配后原子改名为 `/root/state-vla-local-overlay/f3488141-90fd-4d2c-8998-934614d1b098/assets-overlay/RMBench-assets`，再由 `source-runtime/RMBench/assets` 链接到该目录。验证结果为 346 文件、1,352,865,357 bytes，manifest SHA-256 `96306eecd57db76b8ca4b1e3d17099790a03749b5702fe50f5c92581b0c34686`。没有修改任何 repository source、依赖、checkpoint、HF/C3、memory 或 reset 行为。

新 r3 launcher 由 r2 独立复制，保留 r1/r2 不变；其每次 preflight 均重新解析 assets 链接并重建逐文件 SHA-256 manifest，同时验证 checkpoint、冻结 commit、patch、GPU1 和端口 19410/19412。r3 smoke `c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r3` 已完成：seed `100000` 正常专家预检拒绝，随后 accepted seeds `100001`、`100002` 完成两条 rollout；首条为 Success，第二条为正常任务 Fail（step limit），无 runtime error。结果为 `completed`、2 episode、success rate 0.5；`episode0.mp4` 可读（588 frames），episode1 的关闭视频检查也通过。`smoke2_r3_acceptance.json` 保存了 matching formal 的完整门禁结论。

matching formal `c_wave1_swap_blocks_n_trainseed0_evalseed0_100ep_r3` 的独立 preflight 已通过，并于 C1 GPU1 启动，PID `1908255`。它已立即登记为 MAM long job `e2558306-1c2b-49b7-9efc-68ab68a13e55`，host `wuwen-4090-1`，当前运行中；formal 仅引用 r3 smoke，不会使用 r1/r2。完成后按 MAM 收尾、归档和发布结果。

证据位于 C1：

```text
workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/c1_uv_cache_read_repair_20260915/full_overlay_validation_20260915/
```

## 2026-09-20 live formal status

C1 eval0 formal100 两条 lane 仍在运行，第三批未启动：

| lane | GPU/ports | MAM job/PID | accepted/rejected preflights | 状态 |
| --- | --- | --- | ---: | --- |
| swap_blocks J, eval0 | GPU2 / 19420,19422 | `74f550ad-b8d7-4480-9cde-913cbe640ea5` / 2162806 | 71 / 68 | running; 71 diagnostics complete |
| battery_try N, eval0 | GPU3 / 19430,19432 | `a98c0bc6-e386-4bb4-ad12-651e80407908` / 2189992 | 46 / 85 | running; 46 preflights accepted, latest seed 100130 rejected |

两条 formal 都持续产生 episode 结果；scheduler 子进程正常 terminal、无 RPC/renderer/身份/路径错误。每个 run 继续保持自身 matching smoke、单 policy server 跨 episode continuous action RNG、H50/K30、首 infer 90 秒与后续 30 秒。必须达到 100 个 accepted episode 后，才验收完整 diagnostics/video/processes、归档对应 MAM jobs并发布完整结果；在此之前不启动第三批。

## 2026-09-22 最终归档

两个遗留 eval job 已归档。Manager 核对 C1 与本机稳定 `RMBench/eval_result/memory_chunk_20260910/` 的 diagnostics_summary：`c_wave1_swap_blocks_j_trainseed0_evalseed0_100ep_r1` 为 completed、90/100；`c_wave1_battery_try_n_trainseed0_evalseed0_100ep_r1` 为 completed、23/100，均无 benchmark error。这只是已存在单 seed 结果的收尾核对，不是新增完整三 seed eval 或重新科学验收。task 于 2026-09-22T08:45:21Z 归档，旧 workspace 已删除，稳定结果和代码引用保留。
