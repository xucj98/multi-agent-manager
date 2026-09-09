task_revision: 6fcd3c5d8f5912e2d55626f67b2ae39f050d9ff3

完成与未完成：

- 已完成 robot-bridge 的 Memory v1 runtime 接入，统一 live、offline、RMBench simulation 和 takeover 的 semantic memory/context 生命周期。runtime 直接使用 `openpi_client.memory_config` 的 resolved config/model spec/encoder/decoder，不复制 parser 或 decoder。
- 已完成多字段 dense/token 输入、query/accepted/completed 反馈、实际执行行/partial/rejection/reset/takeover 丢弃、动态 control UI、逐 query diagnostics，以及 Memory v1 scheduler 参考文档。
- 已完成旧 full F0 的显式诊断入口。仅无 `memory_config` 的 legacy `full_state` 可配置 `params.legacy_full_feedback_selector`：`{kind: index, value: 0|19|29|49}` 分别选择 row1/20/30/50；K30 保持 `move_steps: 30`。`{kind: last_executed}` 是完整 K30 后 row30 基线。该路径复用旧字段布局、归一化和编码，trace 记录 selector、实际 K、选行、字段原始块/可安全识别值和下一 query；row50 标为未执行，不读取未来 GT。
- 已完成 F0 独立小修：RMBench terminal observation 仍处理 pending feedback/trace，但不会把不可消费的 terminal 输入送入真实 policy `infer`；局部代理保留 `SchedulerBase`、真机循环及原有 `build_act_request(...)->None` skip 语义。
- 正在完成 Pascal 报告的 live P1 最小修复，单独保留为未提交工作：执行进度只由实际 worker hand-off 完成、takeover cut 清除未执行旧 proposal、每次 observation 按自身时间基生成 snapshot。该部分不会进入本次 F0 commit。
- 未启动 GPU、真机、正式 RMBench eval 或正式 `eval_result` 写入。按要求，首批旧权重 F0 runtime eval 仍须独立 review 后完成 2 次 rollout smoke，再固定正式运行 commit。

workspace、各库交付 commit：

- robot-bridge worktree: `/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/robot-bridge`
  - `fd38513adb5ba171327358f70f55f88059de49d2 feat: unify Memory v1 scheduler feedback`
  - `92b365c fix: skip terminal simulation policy infer`（F0 可独立 review）
  - 13 files, 2252 insertions, 69 deletions；保留既有 `22a5c6c` metadata/progress 前置提交。
- openpi worktree: `/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/openpi`
  - `7061c94c52199e8efd45c0c417371347dfd7f8ea fix: preserve memory tail availability and bound feedback rows`
  - 任务树还含 `2ed2f26` lock、`5c65b04` 精简 API、`d7e57a2` availability；独立 venv editable 指向该任务树。

验证结果与成果位置：

- robot-bridge `.venv/bin/python -m pytest -q`：445 passed, 1 skipped，57.85s。
- Memory v1 定向 scheduler/context 集合：51 passed，17.63s。
- F0 terminal 修复：`.venv/bin/python -m pytest -q tests/scheduler/test_openpi_simulation.py`：15 passed，2.57s；新增 loop 测试断言真实 mock policy `infer` 调用数为 0，并保留 legacy F0 `actual_k=10`、`next_query=false` trace。
- F0 修改文件的 ruff 与 `git diff --check` 通过。
- 新增 MemoryContext 和新增测试通过 ruff；`git diff --check` 通过。仓库既有 scheduler 文件不在全仓 ruff 基线内，未将既有 lint debt 计为本次变更。
- 文档和旧 full selector 使用说明：`robot-bridge/docs/reference/memory-v1-scheduler.md`。
