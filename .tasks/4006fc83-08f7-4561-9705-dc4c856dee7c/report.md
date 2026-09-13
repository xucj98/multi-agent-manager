# 高频状态 / replan 增量冻结代码独立审查

本报告替代上一版冻结报告 `b55c30eceb74349f039d178f9b689cb7a45dbb59`，按审查要求
`9e6d34e80136422a0f9c79cd2df4af1f0e2a9e7a` 审查下列**干净、精确**候选；未读取或采用作者
工作区中的后续未提交修改。

| 仓库 | 本轮基线 | 审查候选 | 状态 |
| --- | --- | --- | --- |
| OpenPI | `4529a91c1f49a50c8710a7182e31ca5a32dfa05a` | `0ce566bd34f99cb4775422f012ab67c16aa53885` | review worktree clean |
| robot-bridge | `53f853aa71b80a7eadd9fb3092abe39c64df1149` | `a0f1d5035d77cea7cb300eb511ceb5cf3fd1a93d` | review worktree clean |
| RMBench（正式 recorder 接口，仅只读核对） | — | `eb0546a04c857f2ad325d0dc322211ff1f82c393` | 源树 clean；不是本轮作者交付 |

两个候选 diff 的 `git diff --check` 均通过。

## 结论：仍不准入 GPU smoke

此前的默认 action-RNG 回退 P1 已在这两个候选中修复：普通 baseline 恢复旧协议，显式
matched/HF 协议才重置 action/probe RNG，且普通 `infer` 不再携带 rolling sidecar。可是正式
benchmark 到 RMBench result recorder 的 evidence 接口仍不可用。这是 P1 准入阻塞：任何
rolling 或 matched 配置会在 scheduler 启动前失败，因而既不会产生可审计 JSONL，也不会留下
它的 episode 引用。

在 bridge/RMBench 用新的干净提交同时接通该接口，并以真实 recorder 完成跨进程 seam 验证前，
不得启动 GPU smoke、正式仿真评测、训练或部署。本报告不把局部 CPU 检查表述为评测完成。

## 本轮已通过的增量核对

### 默认 baseline 的 RNG、返回字段和开销恢复历史合同

- `Policy.reset()` 现在是 no-op；只有 `reset_episode_rng()` 恢复 action/probe stream
  （OpenPI `src/openpi/policies/policy.py:306-321`）。
- 普通 `Policy.infer()` 不复制 dense raw action，也不返回 `policy_rng`；显式
  `infer_audited()` 才请求这些 sidecar（`:83-170`）。
- `OpenPiSimulationScheduler` 对普通 baseline 继续走 inherited reset/infer；HF 始终调用
  显式 reset，matched baseline/shadow 仅在 `reset_episode_rng: true` 时采用同一每 episode
  reset 生命周期（bridge `robot_bridge/scheduler/openpi_simulation.py:480-529, 1527-1582`）。
  matched baseline 保持 `SchedulerBase` 的 K30/`MemoryContext` 路径且不 probe；matched
  shadow 的 probe 不更新 cache 或执行动作。

独立 CPU Policy 路径复现结果为：普通 response 字段仅有
`actions, memory_prediction, memory_prediction_ids, policy_timing, state`；普通 `reset()` 后
动作流继续（不重放首个采样）；`infer_audited()` 才有 `memory_raw_actions, policy_rng`；显式
`reset_episode_rng()` 会重放 audited 首个采样。审计 action RNG 标记为
`{"stream": "action", "call": 1}`。这验证的是旧默认协议与新增显式协议的分界，
不是只比较新版 baseline/shadow。

### rolling writer 的局部行为符合目标，但尚未进入正式结果目录

`RollingEvidenceWriter` 逐行 JSONL、每行 `flush` 和 `fsync`，保留 header、容量上限后的
`truncated`，以及始终写出的 `episode_finished`（bridge
`robot_bridge/scheduler/rolling_evidence.py:44-146`）。scheduler 已为 plan/probe/trigger/clear/
terminal/exception 接线，并在 `finally` 收尾（`openpi_simulation.py:531-614, 1926-1935`）。
这证明 writer 的局部设计，不证明 benchmark 产物存在；以下 P1 正是该差异。

此前确认的 J absolute target/row 对齐、固定原 forecast 比较、仅清未执行后缀、S prefix-only、
duplicate/stale/invalid/gap 在 probe 前短路、T/混合 target 拒绝，以及默认路径不增加 rolling
持久化开销，在本候选相关路径未见回归。候选没有提供实际评测的 matched YAML，因此本报告不声明
配置级多 episode 结果已验收。

## P1：正式 RMBench recorder 不支持或保存 rolling evidence

### 1. 真实路径申请在 scheduler 启动前直接失败

bridge 的 `BenchmarkRunner._accepted_episode()` 对显式 rolling/matched 配置先调用：

```python
self.result_recorder.path_for("rolling_evidence", episode_id=episode)
```

见 `robot_bridge/benchmark/runner.py:496-504`。这一步在其 `try` 块之前；真实
`RMBenchResultRecorder.path_for()` 只接受 `episode_video` 和 `process_log`
（RMBench `script/eval_diagnostics.py:532-540`）。

使用 RMBench 自己的 `.venv` 对该实际 class 做隔离 CPU 调用，得到：

```text
RuntimeError: unknown bridge lifecycle path: rolling_evidence
```

因此 reset 已接受的 episode 会在 scheduler 子进程启动之前向外抛出，不能由其后的
`_accepted_episode()` 异常记录路径补救。作者的 bridge unit test 使用允许任意 `kind` 的 fake
recorder（`tests/benchmark/test_runner.py:71-98`），没有覆盖正式 seam。

### 2. 即使补上 path，当前 episode 记录仍会丢失 artifact 引用

bridge `_record()` 已把 `rolling_evidence_path` 放入 episode payload
（`robot_bridge/benchmark/runner.py:400-422`）。但 RMBench 的
`RMBenchResultRecorder.event("episode", ...)` 只把 payload 转为 `_DiagnosticTask` 再调用
`EvalDiagnosticsRecorder.record_episode()`（`script/eval_diagnostics.py:366-397, 554-578`）；后者
最终 JSONL 只写 `episode_id, seed, result, diagnostics`（`:72-105`）。

独立 CPU 复现向 `_DiagnosticTask` 输入一个 `rolling_evidence_path`，写出的
`episode_diagnostics.jsonl` 中该字段为 `False`/不存在。即使 `path_for` 被扩展，正式 episode
record 仍不能定位证据文件。

### 3. evidence header 的 episode 身份未穿过 child CLI

runner 的 `_context()` 有 `episode_id` 和 `seed`（bridge `runner.py:383-398`），但生成的 scheduler
命令只传 `--episode-file` 和 `--rolling-evidence-file`（`:615-634`）。
`scripts/run_scheduler.py` 也只从这些参数写入 prompt/task_args 和
`rolling_evidence_path`（`:40-72`）。因此 `OpenPiSimulationScheduler.__init__()` 的 `seed`/
`episode_id` 仍为默认 `None`（`openpi_simulation.py:88-174`），而 writer header 正从
`_reset_args` 读取二者（`:548-568`）。

以 dummy scheduler 执行真实 `run_scheduler.py` entry 的 CPU seam，捕获到
`seed=None`、`episode_id=None`，同时 evidence path 正确传入。也就是说，即便前两项修复，当前
header 仍不能自行关联至正式 episode/seed。

## 需要随下一干净提交一起验收的最小接口修复

1. RMBench `RMBenchResultRecorder.path_for()` 必须为 `rolling_evidence` 返回结果目录下唯一的
   每 episode JSONL 路径；bridge 需保持该 path 只在显式 rolling/matched 协议申请。
2. RMBench 的 episode artifact/diagnostics 必须持久化该路径引用，包含 accepted rollout 的失败
   收尾情形，而不是只存在于 runner payload。
3. bridge runner/`run_scheduler.py` 必须把 benchmark 的 `episode_id`、`seed` 注入 scheduler，
   使 JSONL header 和 episode record 可双向关联。
4. 用**真实** RMBench recorder 做一个 CPU seam：benchmark 申请路径、启动 child、scheduler
   正常或异常退出、JSONL 可逐行解析、episode record 可定位该文件。该测试还应检查 raw/decoded/
   target/current-input/key/action/progress/trigger/clear/terminal/exception 的引用链，以及 4096 事件
   溢出时 `truncated` 加最终 `episode_finished(evidence_complete=false)` 都实际落盘。

在该 seam 通过后，才对新的精确 OpenPI、robot-bridge（以及如有的 RMBench）提交重新复审；不以
样例 JSON、writer unit test 或运行中 `get_status()` 代替它。

## 本轮验证

未使用 GPU、未启动训练、正式评测或部署。

```text
robot-bridge:
tests/scheduler/test_openpi_rolling.py
tests/benchmark/test_runner.py
tests/policy/test_openpi_metadata.py
tests/robot/test_server_dispatch.py
63 passed in 1.35s

OpenPI:
policy_probe_test.py + memory_data_test.py
-k 'probe or policy_full_memory_wire or policy_serial_memory_wire'
8 passed, 8 deselected in 11.46s
```

这些测试和上述三个窄 CPU seam 只覆盖候选的局部接口。P1 意味着正式 benchmark artifact 路径尚未
可用，故不构成 GPU smoke 准入。
