# 高频状态 / replan：真实 recorder 与 child 身份增量复审

本报告替代上一版冻结报告
`7d15393804ae60555385cb0b6b5c8ac86deabbab`，按已发布 review 要求
`9705c9fe2301694be733169a14501ca7498c0cf3`，增量复审源交付报告
`aac1cbd563f7a7aaf83fc0b161ee3dc4463f2959`。审查仅使用下列干净、
精确提交；未读取或采用作者工作区的后续未提交修改。

| 仓库 | 正式基线 | 审查候选 | 状态 |
| --- | --- | --- | --- |
| OpenPI（本轮未改） | — | `0ce566bd34f99cb4775422f012ab67c16aa53885` | review worktree clean |
| robot-bridge | `a0f1d5035d77cea7cb300eb511ceb5cf3fd1a93d` | `552ea78f73e62fddc747d5d26e7e6c365fa00339` | review worktree clean |
| RMBench | `f401f5279c95451eb424ac98b831bab5552b2120` | `c99ec6a2c6df96ec8705b106b125935fce862052` | review worktree clean；已确认候选包含 f401 |

两个增量 diff 的 `git diff --check` 均通过。OpenPI 保持上一轮已审候选，
本轮没有重跑无关全库测试。

## 结论：仍不准入有限 GPU 工程 smoke 或正式评测

上一版 P1 的真实 recorder 接口和 child 身份遗漏已经修复，且身份没有进入
环境 reset 参数，故不引入第二次环境 reset。不过，本候选仍有两个 P1：异常
child 可以留下指向不存在文件的 episode 引用；formal smoke gate 完全不验证
rolling evidence 的存在、身份或完整收尾。后者可让不完整 evidence 进入正式
统计的前置 smoke，因此不能准入。

## 已确认修复的路径

- RMBench `RMBenchResultRecorder.path_for("rolling_evidence")` 现在分配
  `rolling_evidence/episodeN.jsonl`，并通过 `record_episode()` 把
  `rolling_evidence_path` 保存在 `episode_diagnostics.jsonl`
  （`script/eval_diagnostics.py:72-108, 536-576`）。
- bridge 生成的 child 命令包含
  `--rolling-evidence-episode-id {episode_id}` 和
  `--rolling-evidence-seed {seed}`（`robot_bridge/benchmark/runner.py:615-643`）。
  `scripts/run_scheduler.py:78-93` 将它们传为专用审计身份；
  `OpenPiSimulationScheduler` 将身份与 `_reset_args` 分离，并用于 writer header
  （`robot_bridge/scheduler/openpi_simulation.py:167-204, 550-593`）。
- 正式 f401 scheduler 配置只包含 `move_steps: 30`、`debug_iterations: 0` 和
  `policy_first_infer_timeout: 90.0`，没有额外 reset 参数。结合上述接线，已核对
  benchmark 的已接受 reset 只发生一次，child 不会为获得审计身份而再次 reset。
- 默认 baseline 不申请 evidence 路径，正常路径不创建 `rolling_evidence` 目录或
  episode 引用。上一轮通过的默认 action-RNG 生命周期、matched/HF 显式 reset
  分界及 rolling 算法合同在本次窄改中未见回归。

`RollingEvidenceWriter` 自身对已打开的文件会写 header、逐事件 flush/fsync、
容量溢出 `truncated`，以及最终 `episode_finished` 和 `evidence_complete`
（`robot_bridge/scheduler/rolling_evidence.py:45-136`）。这只是 writer 局部行为；
以下两个 P1 说明它尚未成为可靠的正式结果准入链。

## P1-A：early child failure 会持久化悬空 evidence 引用

`BenchmarkRunner._accepted_episode()` 在启动 child 前预分配 evidence path
（`runner.py:496-504`），但无论 child 后续如何失败，两个异常分支都会无条件把
同一路径写进 episode payload（`:521-542`）。`_record()` 也没有检查文件是否存在
（`:400-422`）。真实 RMBench recorder 会忠实保存该字符串，因此失败结果会声称
拥有一个实际不存在的 artifact。

用当前 bridge runner、当前 RMBench recorder 和真实 `_accepted_episode()` 控制路径
做 CPU 复现：scheduler child 直接 `SystemExit(1)`，不创建 artifact。结果为：

```text
runner_exception=EpisodeFailure: episode 0: terminal_scheduler_error: scheduler exit=1
recorded_path_exists=False
failure_reason=terminal_scheduler_error
```

作者的真实-recorder seam 没有覆盖此边界：它的失败 child 在退出前手工写入一行
header（`tests/benchmark/test_runner.py:346-409`），所以断言的文件必然存在。

这不是只会由刻意构造的 child 触发。真实 `OpenPiSimulationScheduler` 直到
`init_state()` 的末尾才调用 `_ensure_rolling_evidence()`
（`openpi_simulation.py:236-313`）；父类在此之前已经建立 clients、读取 policy metadata
并进入 `init_state()`（`scheduler/base.py:131-147`）。metadata 缺失或不合法、初始化或
连接相关的早期异常都可能发生在 writer 打开前。当前外层 `try` 只包住其后的
`_reset_simulation_if_configured()`（`openpi_simulation.py:216-231`），不能覆盖这些路径。

失败 artifact 因此不能被离线审计，也不能让消费者区分“文件尚未创建”与“完整
证据可用”。这是本轮要求的异常 child artifact seam 的 P1。

## P1-B：formal smoke gate 不检查 evidence，能接受缺失或不完整证据

bridge 的 formal gate 直接委托 RMBench `validate_smoke_run()`
（`robot_bridge/benchmark/runner.py:354-374`）。该函数只检查标准 smoke 文件、两条
普通 episode 记录、视频/进程记录、summary 和 bridge hash
（`script/eval_diagnostics.py:647-706`）。它没有：

- 根据 rolling/matched 配置要求每个 accepted episode 都有 evidence 引用；
- 检查该文件存在于结果目录、逐行 JSONL 可解析，或 header 的 `episode_id`/`seed`
  与 episode record 一致；
- 要求末行是 `episode_finished`，或要求 `evidence_complete: true`；
- 因 `truncated` 或其它 incomplete evidence 拒绝 smoke。

两项独立 CPU 构造均被当前 validator 接受：第一项让两条 episode record 指向
不存在的 evidence 文件，得到 `validator_accepted=True`，而所有引用均不存在；第二项
让两个文件都有最终 `episode_finished`，但 `evidence_complete: false`，仍得到
`validator_accepted_incomplete_evidence=True`。后一种情况与 writer 的容量溢出语义
直接相符，因而违反“truncated/incomplete 不得作为完整证据进入正式统计”的冻结合同。

这与 P1-A 的失败结果问题不同：即使 smoke 的两个 episode 被记录为正常完成，当前
formal gate 仍会把缺失、损坏或明确不完整的 rolling evidence 当作有效 smoke 的一部分。

## 再次准入前的最小验收

1. 对所有显式 rolling 或 matched smoke episode，失败 child 在 writer 创建前不能留下
   可用性假象。实现可以产生有 header、异常和最终 incomplete 标记的可解析 artifact，
   或持久化明确的 `missing`/不可用状态；无论采用哪种表示，不能保存一个未验证的普通
   evidence 路径。
2. 扩展 `validate_smoke_run()`：对于要求 evidence 的协议，逐 episode 验证文件存在、
   JSONL 可解析、header 身份匹配 episode record、最后一行 `episode_finished`，且
   `evidence_complete` 为 `true`。缺失、truncated、无最终收尾或身份不一致必须拒绝；
   默认 baseline 继续不要求 evidence。
3. 用真实 RMBench recorder 和实际 scheduler child 覆盖：正常完整 artifact、writer 已打开
   后的异常、writer 创建前的初始化失败，以及默认关闭。formal gate 测试必须分别拒绝
   缺失引用、损坏 JSONL、身份不符、无最终记录和 `evidence_complete: false`。

完成上述窄修并提供新的干净精确提交后，再做增量复审；在此之前不得启动 GPU smoke、
正式仿真、训练或部署。

## 独立验证

未使用 GPU，未启动训练、正式评测、部署或需登记的长进程。

```text
robot-bridge focused CPU seam/tests
  7 passed in 0.46s
  覆盖真实 recorder 正常/已写 header 的异常、命令身份、CLI 转发、
  terminal、容量 truncation、default 无文件、缺身份拒绝。

RMBench recorder tests
  4 passed in 9.04s
```

RMBench 测试有既有 SAPIEN/Vulkan 和资源文件警告，没有测试失败。这些通过结果证实
已修复的接口接线和 writer 局部行为；它们不覆盖上述两个 P1，也不构成 GPU smoke 准入。
