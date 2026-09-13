# 交付报告

## 当前增量修复

已按 Manager 对复审 `27b16d899cf0220986a7531ad04989b227270f61` 的裁决，完成 rolling evidence 的 formal 准入链窄修；未改算法、默认 baseline、OpenPI、P0 logger、训练或运行中的 C 环境。

- RMBench 增加单一 `check_rolling_evidence()`：仅当 bridge 从已解析的显式 rolling/matched 配置传入 `rolling_evidence_required: true` 时，逐 episode 校验 artifact 文件、JSONL、schema v1、header `episode_id`/`seed`、最终 `episode_finished`、`evidence_complete: true` 以及无 `truncated`。
- `validate_smoke_run()` 复用该检查。缺引用、缺文件、坏 JSONL、身份错、无终态、`truncated` 或 `complete=false` 均拒绝 matching smoke；普通 baseline 不要求 evidence。
- bridge 将这一“是否需要”的配置事实传给 formal gate，并在每个显式协议 episode 收尾调用同一检查。正常 child 退出但 artifact 缺终态或不完整时，episode 记为 evidence/infrastructure failure，正式 run 不会把它当作正常完整结果或拼接 partial。
- 未创建文件时 episode record 不再留下普通 `rolling_evidence_path`；以 `rolling_evidence.state: missing` 或 `unavailable` 保存。已写部分文件保留其路径并标记 `incomplete`/`invalid`；已有 scheduler failure reason 与 error message 原样保留。
- 更新 [rolling evidence 文档](/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge/docs/reference/rolling-evidence.md)，说明 matching smoke/formal 的同一完整性合同。

上一轮已修复的真实 recorder path/reference、child header identity 和单次 benchmark reset 仍保留：`RMBenchResultRecorder` 按 episode 分配 `rolling_evidence/episodeN.jsonl`，显式 child 只接收审计 identity，不会据此发起第二次环境 reset。

## 验证

- RMBench recorder/validator CPU 回归：
  `.venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`
  → `5 passed`（既有 SAPIEN/Vulkan 资源警告，无测试失败）。
  - 使用实际 recorder 留存 normal、terminal、scheduler error 的 evidence 状态。
  - matching gate 接受完整 artifact，拒绝缺引用、缺文件、坏 JSONL、身份错、无终态、truncated 和 `evidence_complete=false`。
- bridge lifecycle CPU 回归：
  `PYTHONPATH=/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi/packages/openpi-client/src .venv/bin/pytest tests/benchmark/test_stage3.py tests/benchmark/test_runner.py -q`
  → `26 passed`。
  - 真实 RMBench recorder + child 覆盖 writer 前直接失败、writer 后异常、正常完整、default 无 evidence；保留每 smoke episode 一次 reset。
  - formal-mode CPU fixture 覆盖 child 正常退出但 evidence 无最终记录时，runner 以 `accepted_infrastructure_failure` 拒绝并把 episode 写为 Fail。
- bridge 全量 CPU 回归：同一 `PYTHONPATH` 下 `.venv/bin/pytest -q` → `524 passed, 2 skipped`。
- bridge 变更文件通过 Ruff、Python 编译与 `git diff --check`；RMBench 变更文件通过 Python 编译与 `git diff --check`。

## 精确提交与基线

- OpenPI（本轮未改）：`0ce566bd34f99cb4775422f012ab67c16aa53885`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi`
- robot-bridge：上一候选 `552ea78f73e62fddc747d5d26e7e6c365fa00339` 之上的当前候选
  `ffa122494c19e1c0154e877010f7b470967ccfc6` (`fix: enforce rolling evidence at benchmark close`)
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge`
- RMBench：正式 `f401f5279c95451eb424ac98b831bab5552b2120`，上一候选 `c99ec6a2c6df96ec8705b106b125935fce862052` 之上的当前候选
  `6abebf08d084d0be43aa56ebe158dc8395fa58e4`（`验证 rolling evidence 的 smoke 完整性`）
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/RMBench`
  - 已核对 `2e9677c..f401f52` 仅是 `memory_schema_eval.yaml` 的 17 行 N/S 配置新增，当前 candidate 保留完整 f401 祖先。

三个 worktree 均 clean；没有登记中的本任务 job。

## 首 query 有界诊断（C3 GPU0）

本轮仅诊断 `put_back_block`、train seed 0、环境 seed `100000` 的 matched baseline/shadow 首个真实 policy query；冻结运行树只读，未改生产源码、checkpoint、共享 cache、阈值或算法。冻结根为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 分别为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`；checkpoint 为 `pi05_rmbench_put_back_block_full_t_plus_1/.../20000`。

- 真实入口分别为 `matched_baseline._call_policy_infer` 和 `shadow._call_rolling_action_infer`。两者的 scheduler pre-RPC 完整输入树（3 张 RGB、state、memory IDs、prompt）相同，SHA-256 为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`；Policy transform 后树为 `df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`。
- 实际 action RNG 完全一致：split 前 `[0, 0]`，采样 key `[928981903, 3453687069]`，split 后 `[1797259609, 2579123966]`。隐式 diffusion noise、raw model H50、post-transform H50、实际 queued K30 的树哈希依次为 `127e5ee9a877…`、`035baf5219a…`、`baa84c42691…`、`cdcbecf0e633…`，baseline/shadow 均相等。
- 每侧一次真实 action query 加两次同输入/同 key replay，共消耗 `6 / 8` 个正常 action samples。以冻结 backend 的 wire cast `np.asarray(actions, dtype=np.float32)` 比较后，所有 H50 replay、跨入口 replay 和 H50 前 30 行对实际 K30 都为逐元素相等；两个队列均在逻辑步 0 立即清除 `30` 行，未执行轨迹动作。两个保留的失败目录均发生在 query 前，未计入样本。
- Policy transform 的原始 action 是 float64，而 frozen OpenPI backend 在线路上转为 float32；直接比较 pre-cast 值仅有该转换舍入（最大绝对差约 `5.93e-08`），不是推理差异。

结论：这一受控的新首 query 样本没有发现输入、transform、真实 PRNG key/noise、模型输出、队列或固定输入/key GPU replay 的分歧，因此不支持把历史不一致简单归因为 policy sampling 非确定性。它不撤销既有历史动作前 30×14 不一致审计（离线 queued-action 审计工具 SHA `1be44b9bd3cd02235833707e40022d0690361efae60b131dcbeb287daeb02151`，重算 SHA `bc30cf2ee8bfe7130cc68c1f8eff2862928e5baee1564b6841ffb29d0187d1fb`）：新捕获只说明该次重建的首 query 未复现差异。仍未确认的条件包括先前 run 的初始环境/完整输入状态或其他生命周期差异；现有证据不支持生产修复或解除正式评测暂停。

证据位于 C3 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic`：[`analysis.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.md) 与 [`analysis.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.json)，后者 SHA-256 为 `c14af95aac92df5cefbfd3958de0100f1efef780d28a7031e8f59435a4500db1`。诊断分析器 SHA-256 为 `71952d10f8050689fe57143448ad5162e12c0edc9a015d68a1006db9d9f02912`；调度 wrapper 记录了上述插入点，SHA-256 为 `318ac87ca3f7b963aff059a101f6c78cfa860735b28b04450b9beaf005050c4f`。

## 未执行项

此前的源码修复验证仍是 CPU-only；本轮例外是在 C3 GPU0 完成上述 6 次有界首 query 采样。未启动新的完整轨迹、matching smoke、formal 100、`r_s=30` 或 HF 效果试验，未训练、未改 checkpoint、未部署，也没有新增生产源码提交。剩余 2 个 action samples 保留，除非 Manager 提出新的有界假设，否则不再使用。
