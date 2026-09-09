task_revision: 1ebde35fd5511b2c330ffa70de43993121b1a85d

完成与未完成：

已在任务登记的三个 worktree 中完成旧 shared-full checkpoint 的实际加载、2 accepted-rollout smoke、时序调查和正式入口准备。未启动任何 100-rollout 正式评测；正式运行仍等待 Manager 集成 review 与明确开跑通知。

本轮已落实 Manager 文档反馈：README 改为中文直接命令，脚本默认定位同一 workspace 的三库，无需先 export 根目录变量；第 50 条后的偏差检查明确由实验负责人执行；产物按共享主 RMBench 的真实保存路径报告。沿用 Manager 已验收的加载、视频和退出证据，本轮未重跑 GPU smoke，未启动 100，等待新 runtime 集成。

workspace、各库交付 commit：

- RMBench：`/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench`，交付 commit `d1a64cb2468d409411bbcfd3f23ae59d2ec8db6e`（`实验：中文说明评测流程并自动定位任务工作区`）。它在原入口 commit `83cbec9a2477858b727148016c3b4125f32296fa` 上仅修订 README 和脚本根目录默认值/启动 cwd；`config.yaml` 和三库模型、scheduler 核心未修改。
- robot-bridge：登记 worktree、无代码修改，base `b17f6c53ffbc1030972a9820cf592f28b937d501`。
- openpi：登记 worktree、无代码修改，base `71c80db723a242c61cfe429dd6794e9ece3cbcf1`。

直接命令（供后续获准复跑时使用，本轮未执行）：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
bash experiments/memory_chunk_20260910/commands/run_pi05_rearrange_full_smoke.sh
```

Smoke 结果与成果位置：

- 真实保存目录：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/pi05_rearrange_full_k30_oldfull_smoke_20260910/`。本轮用 `readlink -f` 确认 worktree 中的 `eval_result` 别名解析到该共享目录，产物不依赖临时 workspace 留存。
- 启动于 `2026-09-10T03:35:11+08:00`，结束于 `2026-09-10T03:41:57+08:00`，launcher exit code 为 0；两条 accepted rollout 的 seed 为 `100000`、`100001`。结果为 Fail（`button_press_insufficient`）和 Success，汇总为 1/2。该结果仅用于 smoke，不纳入正式成功率结论。
- 视频：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/pi05_rearrange_full_k30_oldfull_smoke_20260910/episode0.mp4`，700 帧、521128 bytes，既有 `video_checks.jsonl` 验证可读；episode 1 的视频明确关闭、无 `episode1.mp4`，视频关闭检查通过。两个 scheduler child 都以 return code 0 正常退出；robot/policy 均由 runner shutdown 收尾。
- 结果目录保留 `config.yaml`、`command.txt`、`checkpoint_metadata/`、两个 episode context、诊断、视频检查与 `processes.jsonl`。`validate_smoke_run` 已通过，config SHA-256 为 `2dbaa989b3703e3aeb0fd342528ddfa6e5b519e48783d8ce180296b734814a89`，bridge commit 为 `b17f6c53ffbc1030972a9820cf592f28b937d501`。
- 全程限定 GPU 0：`CUDA_VISIBLE_DEVICES=0`、`SAPIEN_RENDER_DEVICE=cuda:0`、policy `XLA_PYTHON_CLIENT_MEM_FRACTION=0.40`。结束后 GPU 0 为 1 MiB/0%，19300 与 19302 均未监听。

协议、数据来源与时序结论：

- 旧 P1 使用 checkpoint `policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000`，训练 metadata 明确为 `demo_clean_state` / `rearrange_blocks_demo_clean_state_shared_memory`，H=50。旧 P1 场景保持已核实的 `demo_clean_eval`，没有因新数据约束修改 task_config。
- 新 checkpoint 的训练/转换 provenance 必须证明来源为 `demo_clean_state`；`demo_clean` 因缺 metadata 与详细子任务标注不可作为替代来源。旧 checkpoint runtime 会提示缺少常规 `metadata/datasets.json`，但继承的 `rmbench_data_meta/source_data_config.yaml`、`key_state_config.yaml` 与 `train_config.yaml` 已保留上述来源证据。
- 当前 smoke 将 `scheduler.params.move_steps` 显式固定为 K=30。checkpoint 数据 metadata 的 saved `query_stride` 是 20，runtime 记录了 K30 对该 saved stride 的显式覆盖；这保持了已审计 P1 的 K30 评测入口。
- scheduler 先执行 `actions[:move_steps]`，等待 action queue 清空后的下一次观测，再以 `logical_step` 的实际 advance 取已执行前缀末行。若 30 个 action 都执行，K30 消费 row 30；若 episode 在 chunk 内终止，则消费实际 advance 对应的较早行。K20 可通过同一 `move_steps` 选择，但同时将执行长度和反馈行都改为 20。
- 没有独立的 “execute K30, feed row20” selector，也没有按 query 记录实际执行 K 和实际反馈行的 trace；现有产物只记录配置 K=30 与 episode logical step。因此不能把 K30/row20 称为时间对齐比较。需要 runtime owner `9f5a3889-49a6-4f00-af84-096d8042c3bc` 提供独立 selector 和逐 query trace；本任务未修改模型或 scheduler 核心。

验证与吞吐：

- 本轮仅做 `bash -n`、`git diff --check`、默认路径和共享产物路径检查。清空 `RMBENCH_ROOT/BRIDGE_ROOT/OPENPI_ROOT/RMBENCH_INPUT_ROOT` 后，从 `/tmp` 对实际脚本执行到首个 `mkdir` 前拦截退出；三库默认路径、各自 Python 和 RMBench 启动 cwd 均正确，未创建缓存、未启动 runner 或 GPU 进程。
- 入口通过 `bash -n`、实际 checkpoint restore、完整 smoke 与官方 `validate_smoke_run`。既有 bridge benchmark tests 为 32 passed，RMBench eval diagnostics tests 为 3 passed。
- checkpoint 参数恢复日志为 7.95 s。整个冷启动 smoke 为 406 s，即约 17.7 accepted episodes/hour 的粗略端到端值；两条的 episode 长度分别为 700 与 406 logical steps，且包含首次 XLA 编译，不能直接作为正式 100ep 的吞吐承诺。历史审计的 55.1 ep/hour 仍只是历史锚点。

正式运行状态：

补充 commit 已提交且 worktree 干净，旧 smoke 已由 Manager 验收、共享结果留存。等待 runtime owner 的 selector/trace 集成及 Manager review、明确通知后才能启动正式单 GPU 串行 100 rollout。第 50 条后的检查由实验负责人执行：相对固定基线偏差超过 10 个百分点时调查协议/基础设施，并在该 run 目录与任务报告记录结论；不宣称 runner 已自动实现该人工检查，保留不利 episode。短 smoke 未登记 MAM job；本轮无新运行进程或 job。
