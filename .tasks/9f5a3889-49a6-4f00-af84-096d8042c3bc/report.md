task_revision: 9ffbc412d1ae9cfe3eb66ff397a3591f498ac4b6

完成与未完成：

- 已完成 robot-bridge 的 Memory v1 runtime 接入，统一 live、offline、RMBench simulation 和 takeover 的 semantic memory/context 生命周期。runtime 直接使用 `openpi_client.memory_config` 的 resolved config/model spec/encoder/decoder，不复制 parser 或 decoder。
- 已完成多字段 dense/token 输入、query/accepted/completed 反馈、实际执行行/partial/rejection/reset/takeover 丢弃、动态 control UI、逐 query diagnostics，以及 Memory v1 scheduler 参考文档。
- 已完成旧 full F0 的显式诊断入口。仅无 `memory_config` 的 legacy `full_state` 可配置 `params.legacy_full_feedback_selector`：`{kind: index, value: 0|19|29|49}` 分别选择 row1/20/30/50；K30 保持 `move_steps: 30`。`{kind: last_executed}` 是完整 K30 后 row30 基线。该路径复用旧字段布局、归一化和编码，trace 记录 selector、实际 K、选行、字段原始块/可安全识别值和下一 query；row50 标为未执行，不读取未来 GT。
- 已完成 F0 terminal 正式候选：`build_policy_obs()` 可返回 `None`，`SchedulerBase` 在 hook 后直接返回 `skip`，因而 RMBench terminal observation 仍处理 pending feedback/trace，却不调用真实 policy `infer` 或 robot `execute`。已删除先前临时 policy-client 代理和 simulation `run_iteration` 包装；Base 不读取仿真字段，现有 reset、WS/UDP 与控制顺序不变。
- 已完成 Pascal 报告的三个 live P1 最小修复：执行进度只由 x1 执行线程或 x1pro worker 成功 hand-off 消费；takeover/reset cut 清除所有未处理 proposal，只以实际发送动作作为后续 anchor；每个 `get_obs` 根据该次 observation 的时间基生成非破坏性 snapshot。CPU fake SDK/线程测试只证明 dispatch、队列和时间基语义，未证明真机 SDK ACK 或硬件动作。
- 新发布的跨库 `memory_input_ids` / `memory_prediction_ids` wire 契约尚未接入。后续增量只作用于有 `memory_config` 的新 schema；旧 F0 和 terminal 候选不改动。
- 未启动 GPU、真机、正式 RMBench eval 或正式 `eval_result` 写入。按要求，首批旧权重 F0 runtime eval 仍须独立 review 后完成 2 次 rollout smoke，再固定正式运行 commit。

workspace、各库交付 commit：

- robot-bridge worktree: `/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/robot-bridge`
  - `fd38513adb5ba171327358f70f55f88059de49d2 feat: unify Memory v1 scheduler feedback`
  - `92b365c21ea4f976fcfddd2dbd5b50bae2faf463 fix: skip terminal simulation policy infer`（初始 F0 定向测试）
  - `bc842036e3735390f35fe1138aa7b19f5ae2f95b fix: skip terminal simulation inference in base`（F0 正式候选；与前一 commit 连续应用）
  - `9d2784d143bcc4c4fdd59bc558f0e0a9303d42a5 fix: tie live progress to action handoff`（独立 live P1 修复，位于 F0 候选之后）
  - 13 files, 2252 insertions, 69 deletions；保留既有 `22a5c6c` metadata/progress 前置提交。
- openpi worktree: `/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/openpi`
  - `7061c94c52199e8efd45c0c417371347dfd7f8ea fix: preserve memory tail availability and bound feedback rows`
  - 任务树还含 `2ed2f26` lock、`5c65b04` 精简 API、`d7e57a2` availability；独立 venv editable 指向该任务树。

验证结果与成果位置：

- F0 正式候选（重排后 HEAD）：`.venv/bin/python -m pytest -q tests/scheduler/test_openpi_simulation.py tests/scheduler/test_lifecycle.py tests/scheduler/test_openpi_takeover.py`：46 passed，16.87s。terminal run_iteration 测试断言 normal reset 仍发生、真实 policy `infer=0`、robot `execute=0`，且 legacy F0 trace 保留 `actual_k=10`、`next_query=false`。
- live P1 定向交叉集：91 passed，14.98s；全 CPU 回归在 Base 简化前的等价 terminal 路径为 452 passed, 1 skipped，58.29s。最终候选的全回归将单独复跑并补充。
- Memory v1 定向 scheduler/context 集合：51 passed，17.63s。
- `git diff --check` 通过。Base/x1/x1pro 文件不在全仓 ruff 的既有 clean baseline 内，未将既有 lint debt 计为本次变更。
- 新增 MemoryContext 和新增测试通过 ruff；`git diff --check` 通过。仓库既有 scheduler 文件不在全仓 ruff 基线内，未将既有 lint debt 计为本次变更。
- 文档和旧 full selector 使用说明：`robot-bridge/docs/reference/memory-v1-scheduler.md`。
