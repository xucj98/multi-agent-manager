task_revision: 7e2af0d779690097a1607125c95fd37407274dc8

本阶段完成两个 live P1 的独立修复，已可交 Pascal 增量复核；未启动 GPU、真机、rollout 或长进程。

交付 workspace 与 commit：

- robot-bridge worktree：`/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/robot-bridge`
- live 修复：`ed2f2f34a1eea74e8449d39b889555fdfcc659fc`（`fix: synchronize live handoff progress`），直接父提交为 `c94f508907da6c9a6a786246a3f5968df28af46f`。
- openpi worktree 未改；本轮不重跑已通过的真实跨 transforms wire 验收。

实现：

- `ExecutionProgressTracker` 将成功 handoff 表达为已确认的轨迹前缀/位置。实时 tick 直接交接第三个目标时，前两个过期端点不会补发，但 controller progress 会完成位置 1..3，因此 `MemoryContext` 消费 model index 2，而不会将一次 SDK 调用误写成 row 0。
- X1 与 X1Pro 的同一次 `get_obs(wait_condition={"action_queue_remaining": 0})` 在排期队列清空后，还会等待该返回 observation time base 上的成功 transport/worker handoff。X1Pro 在等待中 drain 子进程事件。非零 `action_queue_remaining` 保持原有异步流水线时间队列语义。
- 文档明确 `completed` 是 handoff 确认的轨迹位置，不是 SDK 发送次数或硬件物理到位。没有新增 RPC、session 或控制循环；WS/UDP 和实时插值跳点保持原样。

验证（均为 CPU/fake SDK）：

- `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/robot/controllers`：90 passed, 1 skipped（16.08s）。覆盖真实 X1 loop、X1Pro worker、单行/末端、延迟 handoff 的单次同步 get_obs、正常 tick、跨端点跳 tick、partial prefix、cut/旧 epoch。
- `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/scheduler/test_memory_context.py tests/scheduler/test_memory_v1_schedulers.py tests/scheduler/test_openpi_takeover.py`：47 passed（16.78s）。新增 Context 断言：成功 handoff 到目标 3 得到 `actual_k=3` 并消费 model index 2。
- `ruff check robot_bridge/robot/controllers/execution_progress.py tests/robot/controllers/test_execution_progress.py tests/scheduler/test_memory_context.py` 与 `git diff --check` 均通过。

规模：7 个文件，374 additions / 55 deletions；生产实现与文档约 86 additions / 48 deletions，其余为必要的 loop/worker 和 Context 回归覆盖。

保留的独立后续项：`tests/scheduler/test_openpi_memory_transform_contract.py` 是此前已通过的跨 wire 草稿，仍未跟踪，未混入本 live commit。等待 Pascal 对 `ed2f2f3` 的增量复核；正式真机/rollout 验收仍需按任务流程另行执行。
