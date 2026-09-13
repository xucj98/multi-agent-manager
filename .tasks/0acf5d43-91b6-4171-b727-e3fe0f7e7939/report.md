# 交付报告

## 本次增量修复

已修复独立审查指出的真实 RMBench recorder 接口不兼容和 rolling evidence 身份遗漏。

- RMBench 的 `RMBenchResultRecorder.path_for()` 现在支持 `rolling_evidence`，按 episode 分配 `rolling_evidence/episodeN.jsonl`；`episode_diagnostics.jsonl` 的每条 episode 记录保留对应 `rolling_evidence_path`。
- bridge 生成 scheduler 子进程命令时，连同 evidence 文件传入已由 benchmark 接受的 `episode_id` 和 `seed`。
- `scripts/run_scheduler.py` 将两项身份写入专用 scheduler 参数，`OpenPiSimulationScheduler` 将它们写入 JSONL header。它们不会写进 `_reset_args`，所以不会触发第二次环境 reset、额外随机数消耗或覆盖实际 episode 身份。
- 显式 rolling 或 matched 协议缺少 evidence 文件或完整身份会明确失败；普通默认路径仍不请求或创建 evidence artifact。
- 更新 rolling evidence 参考文档，说明新 CLI 参数、episode result 引用和“一次 benchmark reset”合同。既有可解析样例仍在 `robot-bridge/docs/reference/samples/rolling-evidence-v1.jsonl`。

## 真实 recorder seam

- RMBench recorder 测试用真实 `RMBenchResultRecorder` 覆盖 normal、terminal 和 scheduler error episode；每条 `episode_diagnostics.jsonl` 记录均引用实际存在的 evidence 文件。
- bridge seam 测试复制相邻 RMBench worktree 的真实 recorder，在子 scheduler 正常退出和出错退出时运行它；验证 scheduler child 启动、evidence path 持久化、JSONL header 身份与 episode record 相同、两条 smoke episode 各只 reset 一次、error artifact 留存，且默认模式不产生 evidence 文件。
- 入口和 scheduler 测试验证生成命令携带两个身份 flags，CLI 只传审计身份而不传 reset 参数，且缺少身份被拒绝。

## 基线、提交与工作区

- OpenPI（本次没有改动）：`0ce566bd34f99cb4775422f012ab67c16aa53885`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi`
- robot-bridge：基线 `a0f1d5035d77cea7cb300eb511ceb5cf3fd1a93d`，本次候选提交
  `552ea78f73e62fddc747d5d26e7e6c365fa00339` (`fix: propagate rolling evidence episode identity`)
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge`
- RMBench：最终正式基线为
  `f401f5279c95451eb424ac98b831bab5552b2120`，本次候选提交
  `c99ec6a2c6df96ec8705b106b125935fce862052`（`修复评测 recorder 的 rolling evidence 引用`）
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/RMBench`
  - 已核对 `2e9677ce8ec9f623395184f63f32ddafa66e5e44..f401f5279c95451eb424ac98b831bab5552b2120`：只有 `experiments/memory_chunk_20260910/configs/memory_schema_eval.yaml` 的 17 行新增 N/S 配置，recorder 代码未变。最终 candidate 保留完整 f401 基线。

两个实际修改仓库均为 clean worktree；可交原 reviewer 对上述两个候选提交做增量复核。

## 验证

- bridge 全量 CPU 回归：
  `PYTHONPATH=/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi/packages/openpi-client/src .venv/bin/pytest -q`
  → `522 passed, 2 skipped`。
- RMBench recorder 回归：
  `.venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`
  → `4 passed`（仅有现有 SAPIEN/Open3D 资源警告）。
- bridge 变更文件通过 Ruff、Python 编译和 `git diff --check`；RMBench 变更文件通过 Python 编译和 `git diff --check`。

## 未执行项

未训练、未改 checkpoint、未部署、未启动正式评测或任何需登记的长进程；未使用 GPU。正式 GPU smoke/formal 评测仍须等待独立 review 准入，并由评测 owner 执行。
