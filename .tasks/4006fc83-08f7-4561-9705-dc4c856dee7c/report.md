# 高频状态 / replan：rolling evidence gate 修复增量复审

本报告替代未准入记录 `27b16d899cf0220986a7531ad04989b227270f61`，按已发布
review 要求 `841214e101f297b2b4d01ea5c12d3c3f4f251c68`，复审源交付报告
`2d3e0f7ba2fa61b9db83aa4550410e370af1a4b9`。审查只使用以下干净、精确
提交；未读取或采用作者工作区的后续未提交修改。

| 仓库 | 本轮基线 | 审查候选 | 状态 |
| --- | --- | --- | --- |
| OpenPI（本轮未改） | — | `0ce566bd34f99cb4775422f012ab67c16aa53885` | review worktree clean |
| robot-bridge | `552ea78f73e62fddc747d5d26e7e6c365fa00339` | `ffa122494c19e1c0154e877010f7b470967ccfc6` | review worktree clean |
| RMBench | `c99ec6a2c6df96ec8705b106b125935fce862052` | `6abebf08d084d0be43aa56ebe158dc8395fa58e4` | review worktree clean；候选保留正式 `f401f5279c95451eb424ac98b831bab5552b2120` 祖先 |

两个增量 diff 的 `git diff --check` 均通过。

## 结论：通过本项代码准入，可进入有限 GPU 工程 smoke

上一版的 P1（formal smoke 未验证 evidence）已修复。显式 rolling/matched 配置现在
从已解析的 scheduler YAML 决定 evidence 是否必需；matching smoke 和 formal episode
收尾都使用 RMBench 的同一检查。缺失、坏 JSONL、身份不符、无 `episode_finished`、
`truncated` 或 `evidence_complete: false` 均不能被记为完整 evidence，也不能通过
matching smoke。

早期 child 未创建文件的上一版 P2 也已按 Manager 裁决收束：episode 保存明确的
`missing`/`unavailable` 状态而非悬空普通路径，且原有 scheduler/runtime 失败原因和
消息保持第一原因。已创建的部分文件保留路径，并标为 `incomplete` 或 `invalid`。

因此，针对本轮 evidence gate 的代码已满足有限 GPU 工程 smoke 准入。此结论不表示
GPU smoke 或正式评测已经执行或成功；正式 100-episode 评测仍须先通过每个 arm/环境
seed 自身的 matching smoke，并由 Manager/评测 owner 按冻结合同启动。

## 共享检查链路

- bridge 只在解析后的 `openpi_simulation` 配置为非 `baseline` rolling，或
  `reset_episode_rng: true` 的 matched baseline 时设置 evidence required
  （`robot_bridge/benchmark/runner.py:102-110, 665-693`）。CLI 本身要求
  `--scheduler-config`，所以没有由手写 child command 绕开这项配置事实的正式入口。
  普通 baseline 保持 `required=false`。
- formal gate 将该已解析事实传给 `validate_smoke_run()`，而不是从 episode record
  是否恰好存在一个路径倒推（bridge `runner.py:354-378`）。随后
  `assert_smoke_compatible()` 比较保存的与当前的 `launch`/scheduler config，阻止把
  不同协议的 smoke 复用于 formal（`:795-825`）。
- RMBench 的 `check_rolling_evidence()` 逐行校验 schema v1 JSONL、header record、
  header `episode_id`/`seed`、无 `truncated`、最后的 `episode_finished` 与
  `evidence_complete is True`（`script/eval_diagnostics.py:675-759`）。
  `validate_smoke_run()` 对每个 matching-smoke episode 复用它并拒绝任一非
  `complete` 状态（`:762-831`）。
- bridge `_record()` 在每个显式协议 episode 收尾也调用同一 RMBench checker
  （`runner.py:404-472`）。完整 evidence 才写普通 `rolling_evidence_path`；缺失或
  unavailable 只写状态，部分/无效文件保留路径和状态。evidence 问题本身会使正常
  child 的 episode 成为失败；已有 child/runtime error 则不改写其 `reason`/`error`
  （`:441-457`）。RMBench `_DiagnosticTask` 优先使用 payload 的原始 reason
  （`script/eval_diagnostics.py:375-406`）。

这条路径保持上一轮已通过的真实 recorder path/reference、child header identity 与
单次 benchmark reset：审计 identity 仍独立于 `_reset_args`；默认 baseline 不请求
artifact，不新增 writer I/O。此前已审的 RNG、matched/HF、队列和算法合同不在本窄改中
发生变化。

## 实际边界验证

以真实 RMBench recorder 和 bridge child seam 复核了以下状态：

- 完整 child：每个文件的 header identity 与 accepted episode 相同，最终记录完整，
  episode 结果包含有效 path。
- writer 已打开后异常：部分 artifact 保留，并被记为不完整；run 作为基础设施失败。
- writer 创建前异常：没有普通 `rolling_evidence_path`，记录为 `missing`，原始
  `terminal_scheduler_error` 和 `scheduler exit=1` 保持在 runtime diagnostics。
- child 正常退出但只留下 header：formal episode 收尾用同一 checker 将其记为
  `rolling_evidence_incomplete`，并以 `accepted_infrastructure_failure` 拒绝。
- matching smoke：缺引用、缺文件、坏 JSONL、identity 不符、无终态、truncated 和
  `evidence_complete=false` 均被拒绝；普通 default smoke 无需 evidence。

另以实际 `RollingEvidenceWriter` 写出一份完整和一份容量截断 JSONL，再交给 RMBench
checker：完整文件得到 `complete`；截断文件得到
`incomplete (truncated)`。这确认 validator 与真实 writer schema 对齐，而非只接受手写
fixture。

## 独立 CPU 验证

未使用 GPU，未启动训练、真实 smoke/formal 评测、部署或需登记的长进程。

```text
robot-bridge
  PYTHONPATH=<OpenPI client> .venv/bin/pytest -q tests/benchmark/test_runner.py
  15 passed in 0.74s

  PYTHONPATH=<OpenPI client> .venv/bin/pytest -q tests/benchmark/test_stage3.py
  11 passed in 0.85s

RMBench
  .venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v
  5 passed in 9.70s

跨库实际 writer/checker CPU seam
  complete=complete; truncated=incomplete (reason=truncated)
```

RMBench 测试仍有既有 SAPIEN/Vulkan 与资源文件警告，但无测试失败。未机械重跑无关
全库；作者报告的 524 passed/2 skipped 不作为本独立结论。

## 限制与后续

本报告只解除本轮 recorder/evidence gate 的代码阻塞。尚未在 GPU 上验证真实 SAPIEN
服务、policy server 或实际 36 批评测协议，也不把 CPU seam 当作成功率结果。若后续变更
scheduler 配置解析、writer schema、result recorder 或 runner 收尾，应重新复核这条
共享 gate。
