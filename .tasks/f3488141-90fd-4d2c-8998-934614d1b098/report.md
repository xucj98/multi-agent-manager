# 六个首波 N/J 模型的 Cluster-C 评测准备（C1 manifest job 运行中）

本轮没有启动任何 GPU evaluator、smoke 或 formal，也没有训练、数据集、pi05 base、cache 或 HF 资产传输。HF 仍依赖的
`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`
已保留且未改动。

## 冻结运行时与本机协议准备

- RMBench task worktree 只含一项小配置提交：`ad7f9d6ba9acd16c31243ad4811e0dfa31cef514`
  (`Prepare N/J memory schema evaluation variants`)；其 `rmbench_base` 固定为
  `f401f5279c95451eb424ac98b831bab5552b2120`，并增加 swap_blocks、battery_try、cover_blocks
  的 N/J metadata assertion variant。bridge/OpenPI 固定为
  `f9626636c4776d8eb15f9c556775cb2d12c000e5` 和
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，三库均 clean。
- C1 隔离 runtime 位于
  `/mnt/public/xcj/Projects/state-vla/workspace/f3488141-90fd-4d2c-8998-934614d1b098/wave1-nj-original-protocol`；
  RMBench/bridge/OpenPI HEAD 分别为 `ad7f9d6`、`f962663`、`a869498`。为导入 RMBench 小配置提交，只在
  stable repo 建立 isolated ref `task/f3488141-90fd-4d2c-8998-934614d1b098-rmbench-protocol-config`，未切换 stable checkout。
- 本机 18 个 `(checkpoint, eval0/1/2)` 已在 `JAX_PLATFORMS=cpu`、`CUDA_VISIBLE_DEVICES=''` 下完成
  `--prepare-audit`、smoke dry-run 与 formal dry-run。总表为
  `/mnt/public/xcj/Projects/workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/local_protocol_preparation/index.json`：
  `status=passed`、`total=18`。每项固定 training seed 0；环境 seed 起点为 100000/200000/300000，H50/K30、
  `demo_clean_eval`、首次 infer 90 秒、后续 30 秒和 matching smoke → formal 引用均已核验。
- checkpoint metadata 经 `load_train_config -> _runtime_metadata -> MemoryContext` 直接恢复 schema、fields、feedback
  与 `demo_clean_state` 来源；没有向 evaluator 注入 GT，也没有按 task 名猜字段。RMBench dynamic loader 已实际确认支持
  `swap_blocks`、`battery_try`、`cover_blocks`；BenchmarkRunner 每个 run 只启动一次 policy server，100 episode 中保持连续 action RNG。

## Cluster-C checkpoint 传输已完成并核验

传输 job `f621fcb1-ffa2-4b80-ba70-28bed708d660` 的原始日志位于
`/mnt/public/xcj/Projects/workspace/f3488141-90fd-4d2c-8998-934614d1b098/transfer/transfer.log`，脚本在
`2026-09-14T18:01:37+08:00` 完成。六个 C 目标都包含 `params/`、`assets/`、`metadata/`、`_CHECKPOINT_METADATA`，
文件数和 metadata SHA-256 与源一致，并各自通过 `rsync -aicn --delete --omit-dir-times`：

| checkpoint | files | metadata SHA-256 |
| --- | ---: | --- |
| swap J | 55 | `de788ccf…42ebfd` |
| battery J | 60 | `ef37c836…9d680a` |
| cover J | 55 | `49a2f02f…52f2de` |
| swap N | 56 | `d3bf7079…a2b1c9b` |
| battery N | 58 | `83f2b31c…5cbb7` |
| cover N | 59 | `d2f60c9f…a156426` |

没有覆盖既有目标，也没有传输数据集、pi05 base、训练缓存或 HF 资产。

## C1 manifest 生成状态

C1 正在运行同一套隔离 runtime 的 CPU-only 重验与 18 项 C 路径 manifest/dry-run：

```text
MAM job: 65987649-f3f6-444b-bd91-080cdbcaaecb
host/PID: wuwen-4090-1 / 1868128
script: .../transfer/prepare_c_nj_manifests.py
output:  .../workspace/f3488141-90fd-4d2c-8998-934614d1b098/c_protocol_preparation/
```

脚本内部固定 `JAX_PLATFORMS=cpu` 与空的 `CUDA_VISIBLE_DEVICES`。C1 首次导入现有 CUDA-build PyTorch 依赖时因共享缓存冷读而较慢；
每次观测的 `nvidia-smi` 都没有显示新的 GPU compute process；GPU0 的 16.9 GiB 进程是运行前已存在的他人进程。该 job 完成后将核对
`index.json` 的 `status=passed,total=18`、C checkpoint 路径、冻结 commits、matching smoke/formal 名称以及 GPU1/2 的交替建议，
再 archive 两个已停止 job。

C OpenPI 的既有 `worktree_env_smoke.py` 在 symlink-mode 下因 `transformers_root.is_relative_to(.venv)` 路径断言失败；
只读核验显示 5 个 `transformers_replace` patch 文件内容匹配且 `nlink=1`，installer 的 `uv pip check` 通过。该路径断言不是
schema/manifest 阻断；真实 GPU smoke 仍需 Manager 放行。

## 后续 GPU 门禁（尚未执行）

C1 GPU1/2 在本轮只读检查中为空闲，清单交替建议其执行。Manager 冻结候选并明确放行后，第一条 smoke 将使用
`c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r1`；对应 formal 为
`c_wave1_swap_blocks_n_trainseed0_evalseed0_100ep_r1`。完整 18 条 C 路径命令会在上述 C receipt 中保存，且不能在本 task 的
CPU/传输准备阶段启动。
