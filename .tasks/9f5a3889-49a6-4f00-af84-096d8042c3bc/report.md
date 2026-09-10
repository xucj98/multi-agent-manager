task_revision: bfab30b8285b76c20bd6f4ceed8bd73bf957b684

本阶段完成 Pascal `ff00b8f` 指出的 X1 非零 wait 回归修复，并保留此前跨库回归整理。未启动 GPU、真机、rollout 或长进程；任务保持等待 Pascal 增量复核。

交付 workspace 与 commit：

- robot-bridge：`/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/robot-bridge`
  - `8ea6078543a875b5ae223df16891cdc1fe975c66`（`fix: keep x1 pipeline waits asynchronous`）
  - 前序 live 修复：`ed2f2f34a1eea74e8449d39b889555fdfcc659fc`
  - 前序独立跨库回归：`29a5638f4a6bdfef2f107d331c2afde9daa03697`
- openpi：`/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/openpi`
  - `86d1adff94d5135988edd8dcca915606c1172872`（已审训练交付依赖链；无本轮训练实现改动）。

实现：X1 `_wait` 恢复非零 `action_queue_remaining` 的原有 `TimestampedBuffer.count_after(base)` 异步判断，不获取 `_action_execution_lock`。阈值为零时才在该锁内同时检查排期剩余与成功 handoff，故同步 drain 仍不会把过期时间戳当作完成证据。没有改写调度循环、发送顺序、X1Pro 路径或新增 RPC。

新增真实 X1 exec-loop/Event 回归：SDK 发送持执行锁时，`action_queue_remaining=1` 的 get_obs 在 release 前返回 `completed=0, queued=1`；现有零剩余用例仍要求 release 后才返回 `1, 0`。

验证（CPU/fake SDK）：

- `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/robot/controllers/test_execution_progress.py`：20 passed（1.99s）。
- `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/scheduler/test_memory_context.py tests/scheduler/test_memory_v1_schedulers.py tests/scheduler/test_openpi_takeover.py`：47 passed（16.17s）。
- 新增测试文件 ruff 与提交 diff check：通过。X1 文件的 33 条 ruff 历史告警在父版本和当前版本数量相同，未扩展或整理无关代码。

此前跨库回归：454 行草稿已压缩为 259 行，直接使用正式 full/serial/no-memory 配置、实际 tokenizer、input/output transforms 与 MemoryContext；本任务 OpenPI CPU 环境为 4 passed，bridge 常规环境预期 1 skipped。

剩余：Pascal 对 `8ea6078` 的增量 review；正式硬件/rollout 验收依既有流程执行，CPU 结果不代表硬件完成。
