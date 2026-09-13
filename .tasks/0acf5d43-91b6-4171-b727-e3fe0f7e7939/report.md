# 交付报告

## 完成内容

- OpenPI 保留普通 `Policy.infer()` 的历史 response shape 与跨 episode 连续 action RNG：普通 `reset()` 恢复为 no-op，不再附加 `memory_raw_actions` 或 JAX `policy_rng`。新增明确 opt-in 的 `infer_audited()`，仅用于 rolling/matched action query；probe RNG 与计数在第一次 audited/probe 调用时才创建。
- 新增 `reset_episode_rng()`：显式协议将 action RNG 复位到 policy 初始 key，probe RNG 复位到 `fold_in(initial, 0x50524F42)`。它不改变普通 baseline 或普通 shadow 的历史 lifecycle。
- robot-bridge 增加 `infer_audited` 与 `reset_episode_rng` RPC、后端 capability 声明和 server 分发。普通 `OpenPiBackend.reset()` 保持 no-op；不支持 rolling-only RPC 的通用 backend 明确报错。
- `OpenPiSimulationScheduler` 新增默认关闭的 `reset_episode_rng: false` 配置。开启后：
  - `rolling_mode: baseline` 仍使用继承的 `SchedulerBase.run_iteration`、现有 `MemoryContext` 和 K30 执行，只将 policy request 显式切换为 `infer_audited` 并在 episode 边界发送 `reset_episode_rng`；
  - `rolling_mode: shadow` 保留 probe，但 probe 不更新 cache 或动作，且同样采用显式 episode RNG reset；
  - `hf_fixed`、`hf_event`、`hf_periodic` 始终采用显式 episode reset。status/trace 明确记录 action request 类型、RNG lifecycle 和 matched 标记。
- rolling/matched scheduler 现在写版本化、逐行 flush+fsync 的 JSONL episode evidence。文件由 benchmark result recorder 为每个显式协议 episode 分配，并在 episode result 中记录其路径。内容包括 episode/plan/query、无 RGB 的输入、canonical targets、raw/decoded forecast、action/probe RNG、queued actions 与完成/丢弃前缀、probe、boundary、trigger/clear、terminal 与异常。
- evidence 默认容量为 4096 个正常事件；超限时写 `truncated` 并在最终 `episode_finished` 标注 `evidence_complete: false`，不再只依赖内存 64 条 deque。普通 baseline 不请求路径、不建文件。
- schema、样例和可复制解析命令见：
  - `robot-bridge/docs/reference/rolling-evidence.md`
  - `robot-bridge/docs/reference/samples/rolling-evidence-v1.jsonl`

已有 rolling 功能保持：J 使用 canonical query+1+row forecast 对齐，event 使用固定 3 行、2/3、连续两次和最小前缀 10；trigger 只 clear 当前未执行后缀，再以 action RNG 正常重规划。S 使用 prefix-only state probe。高频模式继续要求已解析 `task_args`，并拒绝 `random_light != false` 或 `crazy_random_light_rate != 0`。

## 交付提交与工作区

- OpenPI
  - `4529a91 feat: add isolated memory state probes`
  - `0ce566b fix: preserve legacy policy RNG lifecycle`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi`
- robot-bridge
  - `53f853a feat: add rolling memory simulation modes`
  - `a0f1d50 fix: preserve matched RNG protocols and rolling evidence`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge`

## 验证

- robot-bridge full CPU suite：`PYTHONPATH=.../openpi/packages/openpi-client/src .venv/bin/python -m pytest -q` → `519 passed, 2 skipped`。
- rolling/runner/RPC targeted coverage：`63 passed`。覆盖 default baseline、matched baseline、default/matched shadow、HF reset/capability 拒绝、跨 episode matched action 流、trigger 旧计划 discard/新计划接续、terminal prefix、scheduler exception、capacity truncation、默认关闭无 evidence 文件，以及 benchmark 路径注入。
- OpenPI probe/RNG CPU tests：`JAX_PLATFORMS=cpu .venv/bin/python -m pytest src/openpi/policies/policy_probe_test.py src/openpi/models/pi0_probe_test.py -q` → `7 passed`。
- OpenPI Memory-v1 wire regression：`JAX_PLATFORMS=cpu .venv/bin/python -m pytest src/openpi/training/memory_data_test.py -k 'policy_full_memory_wire or policy_serial_memory_wire' -q` → `2 passed, 8 deselected`。
- 两仓相关文件均通过 Ruff、`git diff --check`；evidence sample 通过 JSON 解析。

## 未执行项

未训练、未修改 checkpoint、未运行 GPU smoke/formal 评测、未部署，也未启动需登记的长进程。正式评测仍须在独立 review 准入后由评测 owner 执行；历史 continuous-RNG baseline 不应与 explicit-reset HF 结果混作同一比较分母。
