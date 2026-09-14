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

第一次 C1 CPU job `65987649-f3f6-444b-bd91-080cdbcaaecb` 没有形成完整 receipt：它在写完
swap_blocks N / eval0 的 prepare、smoke dry-run、formal dry-run 后停止，
`c_protocol_preparation.partial_foreground_session_interrupted_20260914T120620Z/index.json` 只含第 0 条，
没有最终的 `status`/`total`。这三份 stdout JSON 均有效、stderr 均为空；没有下一条 invoke 的 stderr 或脚本级异常日志。
当时使用的是前台 SSH 输出流，进程停止边界与首次 `PASS` 输出完全相邻，因此按 launcher/session 中断保留为首因，
不把它误报为 schema 或 checkpoint 失败。

partial receipt 已保留，原输出目录重新留给同一、未修改的脚本。重启 job：

```text
MAM job: f3ad56f9-7766-46ee-8a98-110a3ba9d297
host/PID: wuwen-4090-1 / 1873761
script: .../transfer/prepare_c_nj_manifests.py
stdout/stderr: .../workspace/f3488141-90fd-4d2c-8998-934614d1b098/c_protocol_preparation.nohup.log
output: .../workspace/f3488141-90fd-4d2c-8998-934614d1b098/c_protocol_preparation/
```

该进程使用 `nohup`、stdin `/dev/null` 和 task-local log，且已由 init 收养；脚本内部仍固定
`JAX_PLATFORMS=cpu` 与空的 `CUDA_VISIBLE_DEVICES`。每次观测的 `nvidia-smi` 都没有显示新的 GPU compute process；
GPU0 的 16.9 GiB 进程是运行前已存在的他人进程。重启 job 只有在 `index.json` 达到
`status=passed,total=18` 后，才会验收 C checkpoint 路径、冻结 commits、matching smoke/formal 名称以及 GPU1/2 的交替建议，
并进入已批准的真实 smoke → formal 队列。

C OpenPI 的既有 `worktree_env_smoke.py` 在 symlink-mode 下因 `transformers_root.is_relative_to(.venv)` 路径断言失败；
只读核验显示 5 个 `transformers_replace` patch 文件内容匹配且 `nlink=1`，installer 的 `uv pip check` 通过。该路径断言不是
schema/manifest 阻断；真实 GPU smoke 必须按已发布准入通过自身门禁。

## 已批准的 GPU 队列（尚未启动）

已发布准入 revision `e325a9c9f863395844582d3ea7ccb77b64392a6e` 允许在 C receipt 完整通过后直接执行，
无需再次等待人工确认。每项必须保持 train seed 0、H50/K30、`demo_clean_eval`、首次 infer 90 秒、后续 30 秒，
并让每个 run 的单一 policy server 跨 episode 保持 continuous action RNG；真实 smoke 的基础设施或身份门禁失败会停止该 lane，
不能降低阈值、修改冻结协议或带入 HF per-episode reset。

C1 GPU1/2 每卡串行。按 swap → battery → cover 的 task N/J 配对轮转，先完成三个任务的 eval0 覆盖，再依次 eval1、eval2；
同一 task/eval 的 N/J 尽量固定在同一张卡。每个模型都执行自身 matching smoke2 后才启动其 formal100，formal 显式引用该 smoke，
每个长 formal 单独登记 MAM job，并保留全部失败、诊断、视频与退出证据。第一条候选 smoke 为
`c_wave1_swap_blocks_n_trainseed0_evalseed0_smoke2_r1`，matching formal 为
`c_wave1_swap_blocks_n_trainseed0_evalseed0_100ep_r1`。
