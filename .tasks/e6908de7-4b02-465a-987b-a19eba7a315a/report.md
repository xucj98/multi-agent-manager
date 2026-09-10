task_revision: 0d304cc88fcd38b3cdd443e44126ac7926954faa

完成本次小修：

- RMBench 最终 HEAD：737890494d38486c6335feed6fe55f550b271234（基于 CPU 准备提交 498cc4c49e8669dab822e55a2dd060a5e1c68d98）。
- technical、常规 smoke 和 formal 的 input_audit.json / input_manifest.json 统一生成在本任务 RMBench worktree 的 `.local/memory_schema_eval/inputs/<variant>--<resolved-checkpoint-path-hash>/`。checkpoint 不再写入 `eval_inputs` 或任何 sidecar；同一 checkpoint 可由多个实验组或 worktree 只读复用。
- 不新增公共 API 或 runner。BenchmarkRunner 既有 `--source-root` / `config_source` 已可读取该目录，RMBench recorder 既有 metadata inheritance 将两个输入文件复制到正式 run 的 `checkpoint_metadata/lineage/config_source/`。
- README 已说明：technical 结论记录后删除其 local 输入与技术结果；20k local 输入保留到匹配 formal 完成并确认继承副本后删除。它们不是持久缓存，也不在 eval_result 下创建输入目录。

CPU 验证（未加载模型、未启动仿真或 GPU）：

- 对保留 d10 full 50-step checkpoint 执行 `--technical-smoke --prepare-audit`：metadata 经 `_runtime_metadata -> MemoryContext`，得到 joint_dense、H50/K30、padded action 32、demo_clean_state 和 chunk_completed/last_executed；audit 落在新的 worktree-local 路径。
- Bridge `verify_audited_checkpoint` 验证 27 个 params/assets 文件、`verify_audited_metadata` 验证 29 个 metadata 文件均通过；checkpoint 下确认没有 `eval_inputs`。
- 使用既有 `inherit_metadata` 验证 `config_source` 复制 `input_audit.json` 与 `input_manifest.json` 到 `checkpoint_metadata/lineage/config_source/`。
- technical dry-run 和一个仅在 /tmp 构造、结束即删除的 canonical 20k checkpoint 的 formal dry-run，均传递 worktree-local `Audit` source root；未执行任何服务或 rollout。
- AST/YAML、`git diff --check` 通过。两类 local audit、/tmp canonical checkpoint、/tmp 输出和本任务 bytecode 均已清理。

固定工作区与依赖：

- RMBench：`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench`，`task/e6908de7-4b02-465a-987b-a19eba7a315a`，737890494d38486c6335feed6fe55f550b271234，干净。
- robot-bridge：同级 `robot-bridge`，8ea6078543a875b5ae223df16891cdc1fe975c66，干净。
- openpi：同级 `openpi`，a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，干净。

没有 MAM job 或 GPU 进程。GPU 授权后仍按既有规则：完成 20k checkpoint 先 prepare-audit、匹配两集 smoke，再用同 checkpoint 的 smoke 启动 formal；超过一小时的正式任务立即登记 MAM job。
