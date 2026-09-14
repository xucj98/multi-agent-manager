# 六个首波 N/J 模型的 Cluster-C 评测准备（进行中）

本轮未启动任何 GPU evaluator、smoke 或 formal，也没有训练或数据集传输。HF 仍依赖的
`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`
已只读确认存在，未改动。

## 已完成的本机协议准备

- 重新核对已接受清单
  `/root/Documents/task-state-vla-paper/docs/analysis/wave1_six_nj_training_acceptance_20260914.json`
  的 SHA-256：`f0a993bf14529be1f8064c1b95e827a716995b99dd7d0fb5f7f32af3245a9922`。
- RMBench task worktree 仅提交一个小配置变更：
  `ad7f9d6ba9acd16c31243ad4811e0dfa31cef514` (`Prepare N/J memory schema evaluation variants`)。
  它把 `memory_schema_eval.yaml` 的 `rmbench_base` 冻结为
  `f401f5279c95451eb424ac98b831bab5552b2120`，并加入 swap_blocks、battery_try、cover_blocks
  的 N(no-memory)/J(full t+1) 六个 metadata assertion variant。bridge/OpenPI 固定为
  `f9626636c4776d8eb15f9c556775cb2d12c000e5` 和
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；本地三库 clean。
- 18 个 `(模型, eval_seed)` 已逐项在 `JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES=''` 下完成
  `--prepare-audit`、smoke dry-run、formal dry-run。证据总表：
  `/mnt/public/xcj/Projects/workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/local_protocol_preparation/index.json`
  （18 entries，145 files，1,260,458 bytes）；`validation.json` 已验证：
  `demo_clean_eval`、100 episode、eval 0/1/2 的 100000/200000/300000 seed 起点、首次 infer 90 秒、
  formal 对 matching smoke 的引用。
- 每项都从 checkpoint metadata 经
  `load_train_config -> _runtime_metadata -> MemoryContext` 验证 train config、data repo、memory schema、
  fields/feedback、H50/K30、`demo_clean_state` 来源、`config/exp_name/20000` 与 training seed 0；没有向 eval
  输入 GT 或按 task 名猜字段。
- 接口无 schema 阻断：RMBench 的 `envs.<task_name>` dynamic loader 存在
  `swap_blocks`、`battery_try`、`cover_blocks`；BenchmarkRunner 在 100 集循环前只启动一次 policy server，
  每集只启动 scheduler，保持旧 protocol 的跨 episode action RNG 生命周期。每个 run 的 policy key 从 0 新建，
  而非 HF 的 per-episode reset。

## Cluster-C runtime 与资源

- C stable repositories 已含三项冻结 base object。为传递上述单提交配置，仅导入了 SHA-256
  `2dc3d25d499f907fae9d8940869ba323db8a04a9195c522b72de7744023201c6` 的 3.1 MiB git bundle，并建立 isolated ref
  `task/f3488141-90fd-4d2c-8998-934614d1b098-rmbench-protocol-config`；stable checkout 未切换。
- 已由 C1 installer 创建隔离 runtime：
  `/mnt/public/xcj/Projects/state-vla/workspace/f3488141-90fd-4d2c-8998-934614d1b098/wave1-nj-original-protocol`

  | repo | HEAD | status |
  | --- | --- | --- |
  | RMBench | `ad7f9d6ba9acd16c31243ad4811e0dfa31cef514` | clean |
  | robot-bridge | `f9626636c4776d8eb15f9c556775cb2d12c000e5` | clean |
  | OpenPI | `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` | clean |

- C1 的本轮只读 GPU 检查显示 GPU0 有 16.9 GiB 的既有他人进程；GPU1/2 空闲。因此 18 组清单交替建议
  C1 GPU1/GPU2，未抢占 C3 或启动 GPU。
- C runtime 的 RMBench import-only 及 bridge CPU smoke 均通过，未见新 GPU process。RMBench 的 Vulkan ICD warning
  与本机 CPU 检查一致。OpenPI 的现有 `worktree_env_smoke.py` 在 C installer 的 symlink-mode 下因
  `transformers_root.is_relative_to(.venv)` 路径假设失败；只读比较确认 5 个 `transformers_replace` 私有 patch
  文件均存在、内容匹配、link count 为 1，installer 的 `uv pip check` 已通过。这不是当前 schema/manifest 阻断，
  也未修改依赖或运行树；实际 GPU smoke 仍是后续运行时门禁。误触到要求 CUDA 的 RMBench environment script 后，
  已在 `CUDA_VISIBLE_DEVICES=''` 的导入阶段停止，未出现新 GPU process。

## checkpoint 传输

六个目标在开始前均不存在；来源可由 `wuwen-nx-aic` 读取，并可到达 `wuwen-4090-aic`。当前长 job：

```text
MAM job: f621fcb1-ffa2-4b80-ba70-28bed708d660
host/PID: wuwen-nx-aic / 30673
script: /mnt/public/xcj/Projects/workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/transfer_checkpoints_to_cluster_c.sh
```

它按树顺序使用 `rsync -a --partial --append-verify --bwlimit=10m`，随后执行
`rsync -aicn --delete --omit-dir-times`。每棵树先原子 claim 空目标，随后核验 `params/`、`assets/`、`metadata/`、
`_CHECKPOINT_METADATA`、文件数和 metadata SHA；已有不匹配目标会 fail，不覆盖。

截至本报告，已完成并 checksum dry-run 通过：swap J（55 files，
`de788ccfc1ee06b33b85da7d05de341b39d4b596c34d4ef958537031bc42ebfd`）、battery J（60 files，
`ef37c83666478420c978ce4d57f8b7faa0560a78b0ca8fc930b07bb7129d680a）、cover J（55 files，
`49a2f02f0e6700a754f29fa34dc2bac49e57056f81c07928eb6456a6ff52f2de`）。swap N 正在传输；battery N、cover N 待后续顺序传输。
传输 manifest、日志和 C 预检脚本均在本 task workspace 的 `transfer/`。

## transfer 完成后的确定步骤

1. 在 C1 运行已放置的
   `/mnt/public/xcj/Projects/state-vla/workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/prepare_c_nj_manifests.py`。
   它先重验所有 C checkpoint 的 count/metadata SHA，再生成 C 路径的 18 个 audit/manifest 与 CPU-only dry-run；不加载 GPU。
2. 再更新本报告为六树最终核验及 C manifest receipt，并 archive 已停止的 MAM transfer job。
3. Manager 冻结候选后，第一条可执行 GPU smoke（尚未执行）为：

```bash
cd /mnt/public/xcj/Projects/state-vla/workspace/f3488141-90fd-4d2c-8998-934614d1b098/wave1-nj-original-protocol/RMBench
CUDA_VISIBLE_DEVICES=1 SAPIEN_RENDER_DEVICE=cuda:0 \
  ../openpi/.venv/bin/python -B experiments/memory_chunk_20260910/commands/run_memory_schema_eval.py \
  --variant swap_no_memory \
  --checkpoint /mnt/public/xcj/Projects/state-vla/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z/pi05_rmbench_swap_blocks_no_memory/memory20k_5835fa0_nocmdbuf_swap_blocks_n_s0/20000 \
  --training-seed 0 --eval-seed 0 \
  --run-name c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r1 --gpu 1 --mode smoke
```

该命令须在步骤 1 成功并获得 Manager 的正式评测放行后才运行；matching formal 名称为
`c_wave1_swap_blocks_n_trainseed0_evalseed0_100ep_r1`。完整 18 条实际命令已在上述 `index.json` 中。
