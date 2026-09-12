# 主动唤醒安装与兼容性验收：完成

交付代码位于 `task/e7183b34-6d86-4394-ada8-675f54b56c42`：

- Runtime 组合提交：`9b7c2b2`、`dec9a09`。
- 安装器/兼容性/liveprobe：`9d753d7`、`59729b1`、`f5d22d2`、`322e7af`。

`liveprobe` 现在在启动 fixture service 前，依次为 Manager、stopped-job executor、no-job executor、archived-job executor 创建并绑定正常 persisted thread，然后各完成一个短 baseline。新 thread 在首个 user turn 前会拒绝 `thread/resume`；因此代码在成功 `turn/start` 后立即订阅同一 thread，等待该 turn 的 `turn/completed`，再确认 `thread/read` 为 idle，最后才分页读取历史。这样不会在 active baseline 上轮询历史。

验收固定为六次模型调用：四个 baseline、一次批量 Manager task-ready 投递和一次 stopped-job executor 投递。若 idle 后 `thread/turns/list` 仍明确返回 `list_turns is not supported yet`，liveprobe 会在同一 thread 上调用 `thread/read(includeTurns=true)`，把两个结果写进 receipt 后非零退出，不会新增 baseline。安装器证据校验和安装文档已同步为六次调用；liveprobe 仅由安装器调用，`wake_compat.require_compatible()` 保持零模型轻量检查。

验证通过：

- `.venv/bin/python -B -m unittest discover -s tests -v`：108 passed。
- `bash -n scripts/install.sh`、`py_compile`、`git diff --check`：通过。
- 真实隔离验收：`wake_compat` 对随机未知 thread 的 `thread/read`、`thread/resume`、`thread/turns/list`、`turn/start` 均获明确拒绝，`model_requests=0`；随后 liveprobe 返回 `PASS`，`model turns: 6/6`。

真实 fixture receipt（全部为本任务创建的专用资源）：

| role | thread | baseline / delivery turn |
| --- | --- | --- |
| manager | `01a094d1-8ebd-7c91-b61a-891c3ca4cc3c` | baseline `01a094d1-8fdd-7d92-a911-2907c0040116`; Manager delivery `01a094d1-c767-7543-b425-27c7f1569411` |
| stopped-job executor | `01a094d1-8f08-7c40-98a5-c67c2c3c0e28` | baseline `01a094d1-9a72-7a43-8a99-6e524d7cb42d`; stopped-job delivery `01a094d2-3cd4-7280-b759-899064f422f1` |
| no-job executor | `01a094d1-8f51-7963-b233-cbfbe610293b` | baseline `01a094d1-a6e8-7c93-ab46-aa26d0a3eaf4` |
| archived-job executor | `01a094d1-8f94-7b71-8560-6b9a467d65ec` | baseline `01a094d1-b542-7291-8d38-8698cbb907ea` |

Fixture task IDs：job `49567f34-f948-491f-9c41-7e48e165fc6d`、idle `1e8f384e-c8a8-4421-9b94-39968c90e7dd`、archived `f0e7ed1d-83cc-4abb-b5de-785f9670e64e`。其 stopped job 为 `dafb30c1-6bbd-4ede-8560-78ece113fd44`，预先 archived job 为 `e76a294a-a864-4061-b921-1821ebeb76cb`。历史计数在 stopped job 前为 `{manager: 2, job_executor: 1, idle_executor: 1, archived_executor: 1}`，之后及两个 quiet window 均为 `{manager: 2, job_executor: 2, idle_executor: 1, archived_executor: 1}`。这确认了两条准确投递、idle/archived executor 未收到 scheduler turn，以及无重复 start。

清理完成：fixture service 已停止；两个 fixture job 和三个 fixture task 已归档；四个上表 persisted thread 均已 archive；marker-owned fixture 根已删除。未安装到全局、未启动/停止生产 service，未改动生产任务、用户 thread、远端任务或 GPU。

必要的历史清理收据：早期 ephemeral 尝试的已记录 baseline turn 为 `01a09498-344a-78c0-a6f6-718270589652`，唯一在原 stream 关闭后可确认的 thread ID 为 `01a09498-2cfc-7da1-a26a-a313733c2e23`；仅带 turn ID 的 interrupt 被 API 以缺少 `threadId` 拒绝，其他三个 ephemeral ID 未被旧实现保存，不能通过 API 安全重建，未对其猜测操作。随后两个失败的 persisted fixture 在 baseline 前/期间遇到 API 时序限制：已知 Manager turn `01a094c8-13ef-7921-a22f-26dabc2230a0` 被仅针对该已知 ID interrupt 后 archive；其余未 materialize thread，以及零模型 resume 失败 fixture 的四个 thread，archive 均明确返回 `no rollout found`。这些 API 无法确认的未 materialize IDs 没有被 unarchive、resume 或再次操作。最终通过 fixture 的全部资源已有明确 archive 回执。
