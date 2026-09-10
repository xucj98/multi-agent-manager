task_revision: c664d9b6fe34767c207c8fffaa81bb7a9f99e1b8

结论：GO。候选新 schema 评测入口满足本任务的 CPU 准备、checkpoint 只读、technical-50 / formal-20k 门禁和留痕要求；未发现可复现缺陷。

完成与未完成：

- 独立核对新增入口、YAML 和 README，并追到 OpenPI `load_train_config -> _runtime_metadata -> Policy.metadata`、bridge `OpenPiSimulationScheduler -> MemoryContext`。新 schema 会拒绝 legacy selector；实际 full metadata 在 H50/K30 时于 `chunk_completed/last_executed` 选择 model index 29（row 30），serial 在 `query_selected/query` 反馈。六个 variant 与 OpenPI config 的 repo、representation、字段和 feedback 一致；no-memory 无字段/feedback，put-back 为 phase/origin_mat。
- 对保留的真实 full、serial 50-step checkpoint 分别执行 CPU-only `--technical-smoke --prepare-audit` 和 `--dry-run`。两者均证明 `demo_clean_state`、32 维 padded action、H50/K30 和对应 schema；bridge audit verifier 复核 params/assets 与 metadata 文件集合。checkpoint 前后目录指纹一致，未出现 `eval_inputs` 或其他写入。
- 门禁错误输入已独立验证：普通 smoke/formal 拒绝 step-50，technical+formal 被 argparse 拒绝，serial checkpoint 不能伪装成 full，prepare-audit 不能同 dry-run 混用。代码及 recorder 进一步以 manifest hash、raw run/profile/policy metadata、video ON/OFF、子进程退出和同 GPU launch 身份把 formal 绑定到本身的 20k smoke；formal 固定 100 串行 rollout。
- 验证 generated `config_source` 会把 `input_audit.json` 和 `input_manifest.json` 继承至 `checkpoint_metadata/lineage/config_source/`；新 README 说明 local audit 的清理时机、结果目录和 GPU/MAM job 边界。`unittest discover -s tests -p test_eval_diagnostics.py -v`：3 passed。
- drawer 仅做只读核对：两个实际 checkpoint 都是 30000，训练 config 分别为 `pi05_x1pro_drawer_sorting_s2m_full_state` / `pi05_x1pro_drawer_sorting_s2m_serial_soft`；119-episode S2M 数据、`completed_layers`/`drawer_target` 双字段、原始五集 [1,22,23,24,26] 和 `eval_result/memory_chunk_20260910/drawer_s2m_v2_regression_5ep` 命令一致。未启动 drawer。
- 未运行模型、loss、数据转换、仿真、smoke 或 formal；未使用 GPU，也没有 MAM job。reviewer 生成的两个 `.local/memory_schema_eval` audit 输入和临时继承目录均已删除。

workspace、各库交付 commit：

- `/mnt/public/xcj/Projects/workspace/7af50239-0b3f-4343-a0d0-ca21ad7bcfa4/RMBench` — `737890494d38486c6335feed6fe55f550b271234`，干净。
- 同级 `robot-bridge` — `8ea6078543a875b5ae223df16891cdc1fe975c66`，干净。
- 同级 `openpi` — `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，干净。

验证结果与成果位置：

- CPU 命令均在上述 RMBench worktree 执行，环境强制 `JAX_PLATFORMS=cpu` 和空 `CUDA_VISIBLE_DEVICES`；仅生成过 worktree `.local/memory_schema_eval/inputs/` 下的临时审计文件，现已清理。
- 正式结果仍应由获授权的执行者写入 `RMBench/eval_result/memory_chunk_20260910/<run>`；每个 20k checkpoint 必须先生成自己的两集 smoke 并通过既有 runner 验证后，才可启动对应 100 rollout formal。
