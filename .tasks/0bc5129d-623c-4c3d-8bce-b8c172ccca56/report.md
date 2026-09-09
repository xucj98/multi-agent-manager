task_revision: 28c446150ca33eb7112ccd57ed438d9c0860da23

# 起始提交独立 runtime 审查（非最终验收）

审查范围仅为 `robot-bridge` 的 `bb908c66c17fd2f081c98265228376c3ff2fc3e6`
（controller execution progress）和
`22a5c6cc54f46daf0e025fa3f7fdbd1f07a2f6a8`（checkpoint
`memory_config` 透传）。scheduler / MemoryContext / UI 增量尚未收到，
因此以下不是完整验收结论。

审查 HEAD / 工作区：

- `22a5c6cc54f46daf0e025fa3f7fdbd1f07a2f6a8`
- `/mnt/public/xcj/Projects/workspace/0bc5129d-623c-4c3d-8bce-b8c172ccca56/robot-bridge`
- worktree 干净；未修改交付实现、未启动 GPU 或真机程序。

## 阻塞 scheduler 反馈接入的发现

1. **P1：`execution_progress.completed` 不是实际执行的行数。**
   `ExecutionProgressTracker.observe()` 只按排程 timestamp 是否小于
   observation timestamp 累加（`robot_bridge/robot/controllers/execution_progress.py:46-57`）。
   x1 / x1pro 在 `execute()` 入队时立即登记这些 timestamp，而不是在执行线程
   调用发送动作后登记（x1 `controller.py:414-431`，x1pro
   `controller.py:432-457`）。两条真实执行循环都只有同时存在 `before` 和
   `after` 锚点才调用发送动作（x1 `controller.py:237-257`；x1pro
   `exec_worker.py:133-145`）。

   CPU 最小复现用未初始化硬件的真实循环、替换发送函数为计数器：一个合法
   `(1, 14)` chunk 在 timestamp 后分别得到 x1 / x1pro
   `executor_calls=0`，但 tracker 都返回
   `{"completed": 1, "queued": 0}`。因此若 scheduler 用 completed delta
   消费 policy row，会在完全未发出该动作的情况下提交 phase / memory；末行、
   短 chunk 和部分执行尤其直接受影响。计数需要明确降级为“排程已越过观测时间基”的
   证据，或改为能和执行线程实际尝试发送相对应的证据；无论采用哪种，scheduler
   不能把当前字段当作实际已处理 policy row。

2. **P1：takeover 的 cut 仍可让旧 autonomous proposal 进入执行器，新增
   tracker 会把它记成完成。** `clear_actions()` 用 wall-clock `cut` 仅删除
   timestamp 大于 cut 的条目（tracker `drop_after()` 位于
   `execution_progress.py:59-67`，x1pro 的 worker marker 位于
   `exec_worker.py:117-126`）。执行器滞后时，已过排程时间但尚未被 worker
   处理的旧条目保留；下一个 post-cut 条目到来后，它们仍会作为插值的 `before`。
   
   CPU 复现按真实 x1pro worker FIFO 放入：已执行 anchor=0、旧条目=100、cut、
   新条目=3。首个 post-cut 调用的值为 `95.23934173583984`（8 次调用），表明
   旧 proposal 仍参与执行，而不是仅保留实际历史 anchor。独立 tracker 复现也显示，
   对 `cut - 1s` 的尚未执行条目，`drop_after(cut)` 返回 0，随后观测报告
   completed=1。根本 cut 行为早于本提交，但 `bb908c6` 使它成为反馈误消费和
   “接管/reset 不消费旧 proposal”要求的直接 blocker。后续 scheduler 不能以
   当前 completed delta 证明旧 chunk 已安全清除。

3. **P1：completed 未绑定到返回观察的时间基，跨请求会提前消费。** x1/x1pro
   都以本次 `get_obs` 所需 buffer 的最小 timestamp 调用全局、可变的 tracker
   （x1 `controller.py:324-368`；x1pro `controller.py:311-361`）。带图像与
   不带图像的请求时间基不同，控制 UI / 对齐 / 其它客户端的无图请求可先以较新的
   state timestamp 推进 tracker，之后 scheduler 的带图像观察仍拿到已推进的
   completed 值。最小输入 `enqueue([5]); observe(6); observe(4)` 的结果为
   `completed=1`、`completed=1`。后一次图像对齐观察实际仍早于 action timestamp，
   却被配上已消费的行。锁只保护数据结构，不能保护 observation-to-feedback
   关联；接入时需要把进度快照和生成它的同一观察时间基绑定，或禁止无关查询改变
   scheduler 的反馈证据。

## 已确认可用的起始部分

- `OpenPiBackend.get_metadata()` 对新 checkpoint 原样透传
  `memory_config`，旧 checkpoint 不新增该字段（
  `robot_bridge/policy/backends/openpi.py:402-415`）。相应单元测试确认
  identity 保持和 legacy omission；这条路径没有重解释旧 `memory` metadata，
  符合 legacy 可比性要求。
- Mock 的 completed 是同步执行的 policy rows；RMBench 的 completed 取
  `take_action_cnt`，每次 `_drain_to()` 正好调用一次 `take_action`，terminal
  时清空尾部。新增的 early-terminal 测试正确覆盖了 3 行队列只完成 2 行、
  `queued=0` 的情况。
- Offline controller 的 completed 是 `_current_frame`，即 policy-row target
  timeline，而非 render/substep；但它在 episode 切换时回到 0，并以
  `offline_dataset_status="ep_init"` 标识边界。后续 scheduler 必须先清 pending
  / baseline，再解释该计数，不能把它当跨 episode 单调计数；`dataset_done`
  返回也不含 execution_progress，不能伪造下一次 query。
- 真机 metadata 的 unit 标为 `control_commands`，不是 `policy_rows`，方向正确；
  scheduler 仍须显式保存 chunk 到 command/row 的映射，不能仅使用 raw counter。

## 验证

- `.venv/bin/python scripts/worktree_env_smoke.py`：通过。
- `tests/robot/controllers/test_execution_progress.py`
  `tests/robot/controllers/test_rmbench_simulation.py`
  `tests/robot/controllers/x1pro/test_buffers.py`
  `tests/policy/test_openpi_metadata.py`
  及相关 OpenPi / takeover / simulation scheduler CPU tests：
  `87 passed, 1 skipped, 1 deselected`（`CUDA_VISIBLE_DEVICES=''`）。
- 同一完整选择集未排除测试时为 `87 passed, 1 skipped, 1 failed`。失败的是
  `tests/scheduler/test_openpi_simulation.py::test_real_controller_images_through_scheduler_loop`：
  测试以 `object.__new__` 创建 scheduler 而未设置
  `_policy_reset_pending`，但 `SchedulerBase.run_iteration()` 已读取它。
  相关 base/test 行由早于审查范围的 `f01586b7` 引入，且 bb908c6 / 22a5c6c
  均未改动这些路径，故记录为既有、与本次两提交无关的测试装配失败。
- 未进行真机硬件、SDK 真实反馈或 GPU rollout 验证；CPU fake SDK 复现不能宣称
  真机通过。

## 未完成与后续

尚待 Manager 提供 scheduler / MemoryContext / UI 增量后，复核 row index、actual k、
query_selected/chunk_completed 时刻、legacy F0、reset/takeover 清 pending、UI 字段透传
和异常收尾。当前 metadata 透传未调用新 client API，因此尚未创建本 task 的 openpi
worktree；增量若实际依赖 `openpi_client.memory_config`，将按要求单独创建
`openpi@58d6f2155acc3af03017677bb3f536101e6699f4` worktree 后审查。
