# 交付报告

## 原入口首 query 准备（仅 CPU，未执行）

已在任务私有目录准备保持原 `BenchmarkRunner` 启动、metadata、reset/preflight 和首 query 路线的有界诊断入口：[runner](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/original_entry_first_query_runner.py)（SHA-256 `376dd1fd087a5e79a9cbda4e83d1ff5b8534dc9c59429a60acbdf8ed2a0abf34`）仅替换其生成的 scheduler child；[scheduler](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/original_entry_first_query_scheduler.py)（`0561e295e644bee882c7abaee9d08e856b9e5ad00aeafbb4ed480ad7f3179ae2`）在首个同步 RPC 返回后才于 RAM 深拷贝完整 request/response，并在原 `run_iteration()`、`after_execute`、clear 和无 drain status 后写入收据。完整行为、边界和 8 MiB 单数组上限见[说明](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/original_entry_first_query.md)（`c11656f94b8d2ef043964465d8ecca9a0d83575fc7ff25bf1c5e3499f2d9d6db`）。

[CPU seam tests](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/test_original_entry_first_query.py)（`3f9653c70525febdf2b7167696539cc9e3c535f728974bef214dd48bdf756a5c`）当前复跑为 `11 passed`，并通过 Python 编译；覆盖一次 infer 上限、post-send ambiguity 不重试、预检拒绝不进入 seed `100001`、execute 后 clear/status 顺序和诊断 child 的 episode-0 failure leaf。默认 launcher 只打印计划，未执行 `--execute`，因此本次准备没有启动 GPU、正常 policy server、真实 reset、replay、warmup 或完整轨迹，也没有消耗剩余 action samples。

该捕获是 `WebSocketClient.call()` 返回后的对象观察，不能称作原始 wire bytes；真实 PRNG key 仍不可得。任何诊断 receipt 都是独立失败/有界收据，不能用作 matching smoke 或 formal 成功证据；当前正式评测仍暂停，生产源码树保持只读。

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

本轮仅诊断 `put_back_block`、train seed 0、环境 seed `100000` 的 matched baseline/shadow 首个真实 policy query；冻结运行树只读，未改生产源码、checkpoint、共享 cache、阈值或算法。冻结根为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 分别为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`；checkpoint 为 `pi05_rmbench_put_back_block_full_t_plus_1/.../20000`。实际导入的 `openpi/policies/policy.py`、OpenPi backend 和 simulation scheduler SHA-256 分别为 `1c4636db0e5fb97a8e5a4332de047d79d9ad5c63ea6880179d7606b41fa65563`、`a49f45fe5923723afc8982be2ff88d8b483c8bd6aba225838d4c92c7cad7ce5c`、`c6f9eeb9442153f5231b5a1be268ad1f1f04dfe83626caddf68b517839c0ca5b`。

- 真实入口分别为 `matched_baseline._call_policy_infer` 和 `shadow._call_rolling_action_infer`。两者的 scheduler pre-RPC 完整输入树（3 张 RGB、state、memory IDs、prompt）相同，SHA-256 为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`；Policy transform 后树为 `df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`。
- 实际 action RNG 完全一致：split 前 `[0, 0]`，采样 key `[928981903, 3453687069]`，split 后 `[1797259609, 2579123966]`。`implicit_noise_derived_from_sampling_key`、raw model H50、post-transform H50、实际 queued K30 的树哈希依次为 `127e5ee9a8777cfb6f05401c832f45f422efffe52a27bbf0b7b77396e9619c80`、`035baf5219a0e838d404ab4ca56a82063fc64cf7dfd79a508e5317e77268f90d`、`baa84c42691b0aa0e87d0fdb55f4a7c96897ac2a8e19dd45004bcd5e8fb9a096`、`cdcbecf0e6339267b95eccd58529ab6f076adf845d86410f7021661dd6a8e491`，baseline/shadow 均相等。前者是用捕获到的真实 sampling key 按冻结 `jax.random.normal` 表达式离线重建，不是 GPU sampler 内部 noise 的直接捕获。
- 每侧一次真实 action query 加两次同输入/同 key replay，共消耗 `6 / 8` 个正常 action samples。以冻结 backend 的 wire cast `np.asarray(actions, dtype=np.float32)` 比较后，所有 H50 replay、跨入口 replay 和 H50 前 30 行对实际 K30 都为逐元素相等；两个队列均在逻辑步 0 立即清除 `30` 行，未执行轨迹动作。两个保留的失败目录均发生在 query 前，未计入样本。
- Policy transform 的原始 action 是 float64，而 frozen OpenPI backend 在线路上转为 float32；直接比较 pre-cast 值仅有该转换舍入（最大绝对差约 `5.93e-08`），不是推理差异。

结论：这一受控的新首 query 样本没有发现输入、transform、捕获到的真实 PRNG key、离线重建 noise、模型输出、队列或固定输入/key GPU replay 的分歧，因此不支持把历史不一致简单归因为 policy sampling 非确定性。它不撤销既有历史动作前 30×14 不一致审计（离线 queued-action 审计工具 SHA `1be44b9bd3cd02235833707e40022d0690361efae60b131dcbeb287daeb02151`，重算 SHA `bc30cf2ee8bfe7130cc68c1f8eff2862928e5baee1564b6841ffb29d0187d1fb`）：新捕获只说明该次重建的首 query 未复现差异。诊断 wrapper 在 transform 周围做同步 host copy/`fsync`，并暂时 monkey-patch 全局 `jax.random.split`；它保持预期的随机调用语义，但改变了 timing/JIT 条件，所以新样本相等也不能排除未插桩运行时的 timing/numerical effect。仍未确认的条件包括先前 run 的初始环境/完整输入状态或其他生命周期差异；现有证据不支持生产修复或解除正式评测暂停。

证据位于 C3 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic`：[`analysis.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.md) 与 [`analysis.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.json)，后者 SHA-256 为 `c14af95aac92df5cefbfd3958de0100f1efef780d28a7031e8f59435a4500db1`。诊断分析器 SHA-256 为 `71952d10f8050689fe57143448ad5162e12c0edc9a015d68a1006db9d9f02912`；调度 wrapper 记录了上述插入点，SHA-256 为 `318ac87ca3f7b963aff059a101f6c78cfa860735b28b04450b9beaf005050c4f`。

## 离线历史首 query 对齐

未增加 GPU 采样、reset、replay、完整轨迹或生产源码改动。任务私有离线读取器 [`align_historical_first_query.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/align_historical_first_query.py) 以冻结 wire 合同 `np.asarray(actions, dtype=np.float32)`（`openpi.py:349-356`）读取旧 put-back matched artifacts 和新有界 capture；读取器 SHA-256 `94b3a1cbc209b0b1c58f670a74b0a61f4c2a9940a1f2a4fef7c88530dc7b5d58`。结果为 [`historical_alignment.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.json)（`4de3f6edc1af02fec61015439393f5d287da70bea0dd55732a0bf91c35ca2b1b`）和 [`historical_alignment.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.md)（`ffa48e8682d927b544b56664a117861afef1607dd9a0697e425b4394d5231bd6`）。

- 新 H50 的 wire SHA 为 `adf97a1dadeee7df55ab60d7bfe54f9d141cffd7b15c13dd114a222306a2d68a`，K30 为 `f0dcb3163e0723c363e9477faa873a499baba78e4bbba7a2ef7188724ac25fa4`。旧 baseline 的两集 H50 完全相同（SHA `4c69052f6e46e601de388993f3cb1ddc108617e8ded37230cdb758f21b854431`）；旧 shadow 只留第一 `action_plan.queued_actions` K30、两集也相同（SHA `0799a79aea6a7d860b7859f2a7ce988d1b3229f3b6ac2e6b0389cbbc4d405a40`），没有可回溯的 shadow H50 tail。
- 新 H50 对旧 baseline H50 有 `511/700` 个 float32 元素不同，max abs `0.0034926608204841614`、RMSE `0.0006454789071132261`，首差 `[0,0]` 为新 `-1.459865779906977e-05`、旧 `0.00032710886443965137`。新 K30 对旧 baseline H50 前缀为 `296/420`、max `0.0027747450512833893`、RMSE `0.0005912740981828194`；对旧 shadow K30 为 `301/420`、max `0.003492661053314805`、RMSE `0.000688904451176663`。历史 baseline 前缀对 shadow K30 仍为 `299/420` 个不同。新 K30 的 164 个元素同时不同于两边，其余类别也不组成任一旧数组，因此新 capture 精确等于旧 baseline 和旧 shadow 的结论均为 false。
- reset request 仅去掉 run-specific `video.output_path` 后完全相同（canonical SHA `789feb2835dae80d4415c21141594e8b913153374f2a8df9b0b714d160c1679d`）：`task_overrides={}`、`instruction_type=unseen`、`test_num=100`。instruction 精确相同（SHA `8537a6997ea8ad918e3237b6642490ded7c9204d9bd78075b1d6a88ec46f81bf`）；去掉 `eval_video_save_dir` 后 preflight task args 和相机配置也相同。旧/新保存的 `memory_input_ids=[0,0]`、state 均相同（int32/float32 raw SHA 分别为 `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc`、`aed9607efe0f26286bd388129c3f8720abc4de43b417ae34e0a12dfec2d25747`）。
- 这只证明配置与已留存字段相同：旧 rolling evidence 首 query 输入只有 state/memory，未保存 RGB、完整 prompt/token/transform tree、实际 PRNG key、sampler-internal noise；旧 shadow 也未保存 H50 tail。新 baseline/shadow 的 scheduler pre-RPC tree（含 3 张 RGB）和 post-transform tree 分别同为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`、`df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`，但这不能倒推旧全输入或旧真实随机状态相同。`episode_info.info.task_facts.final_block_pose` 也不能当作首 query 输入身份：`rmbench_sim_worker.py:135-149` 的 probe env 会 `play_once()`，`put_back_block.py:106-140` 随后记录该 pose，而 worker 在 `:155-179` 重建实际 episode env 后仍返回前者。
- 已确认入口差异：旧 `BenchmarkRunner.run` 在 metadata handshake 前连续启动 robot/policy（`runner.py:750-771`）；新 launcher 先启动并握手 robot，后启动 policy（`run_first_query_diagnostic.py:355-379`）。旧流程是正常 `run_policy_server.py`/`scripts/run_scheduler.py`，新流程是 task-private policy/scheduler wrapper，并新增 JAX/WARP/CUDA cache 路径（旧 receipt 未保存其值）。新 scheduler 仍加载相同 config、调用冻结 `apply_episode_prompt`，再 `_startup(); run_iteration()`；这与 `SchedulerBase.run()` 的名义首 action route（`base.py:614-648`）在构造后相同，但不能抹去 wrapper 或启动顺序差异。
- 建议但未执行的最后两样本方案：baseline、shadow 各一次，保留旧 `BenchmarkRunner` 的启动顺序与 reset flow；只在真实 execute request 之后的 scheduler 侧采集 post-wire K30，并在 logical step 0 clear queue。不得包装 `Policy.infer`、transform 或 `jax.random.split`。这样可区分差异是否由本次 diagnostic wrapper/startup path 引入；若未获授权额外观测，仍不能回建旧 RGB/实际 key。

## 原入口有界首 query 执行（C3 GPU0，2026-09-14）

Manager 授权的后续执行只使用了 matched baseline 的 **1** 次真实 action request；matched shadow 在来源校验阶段停止，使用 **0** 次。冻结运行树为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。结果 leaf 为 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910_hf_engineering/c_hf_j_matched_baseline_original_entry_first_query_env100000`；MAM job `ff3b2531-1b01-4685-b5d8-f23037d63253` 已归档。外层 exit `70` 是预期的诊断截停，保留了 episode-0 failure leaf，不能视为 benchmark 成功。

baseline 的实际 policy 身份不是仅由外层环境变量推断。结果 `config.yaml:750` 记录了 policy `get_metadata.policy_dir` 为 `/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000`；冻结 `BenchmarkRunner` 将 policy `get_metadata` RPC 返回值保存为 `run_context["policy_metadata"]`，拒绝与 manifest-resolved checkpoint 不同的 `policy_dir`，再写入 result config。该 config 的 `metadata_verification.actual_path`（行 442）和 `checkpoint_verification.actual_path`（行 535）分别解析到该目录的 metadata 与 checkpoint，校验 digest 分别为 `3b5d9b56a6d9abcaad95c6fc4824b2cd4e2b80bfc5d59ef7380f0d12f08622a4`、`d29535bfbe13776d3f006639b450cb85701647772414034fd01484838da940de`。policy stdout 还直接记录从该 checkpoint 加载 train metadata、恢复 `params`、并从 `assets/rmbench_put_back_block_robot` 加载 norm stats。

任务私有离线提取器 [`extract_baseline_identity.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/tools/extract_baseline_identity.py)（SHA-256 `f0640fadfd6be64fb6007ab4e7b490174c2172cc5862ea36cc9e1e04973593e1`）重读 runner、policy server、backend、recorder、launch、manifest、result config 和 policy log，输出 [`baseline_identity.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/analysis/baseline_identity.json)（`25f89ee7c4f8ba56e2976f8e4657b66af95df3c2a54e462800e065df916269e9`）。其 baseline 身份链检查全部为真。baseline 的 `MemoryCheckpoint` source-root 与旧 baseline command 一致，解析 `MemoryCheckpoint/20000/metadata` 存在；shadow 的 `--source-root MemoryCheckpoint=...` 少了 `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` 这一层，解析后的 checkpoint 和 metadata 都不存在。虽然 shadow launcher 的 `RB_OPENPI_POLICY_DIR` 值未被使用到，runner 在 metadata source 校验时即以 `InputNotReady: checkpoint_metadata` 停止：无 reset、policy startup、scheduler child、action RPC、result leaf 或 retry。

baseline scheduler receipt SHA-256 为 `f56e3438c911ce76232b9e69b0928b3860f2df8d5e03f607c3959b3ae8a4e252`，runner receipt 为 `d8988c7035fb3b554e1ed43d711eaf54a55835e37ac7ea4597d00ad9a1bdcfea`，验证摘要为 `b421a3b2f088043238fa6288e5bd968c9d023989206e77c797b0c837f86861ec`；shadow failure receipt 为 `64ee0c7c9f4e4d77a99e20af55ed830bc06b42455cbe820ca34e98ceb0a89d21`，其验证摘要为 `ee366342b9c58ebf36a2249f0e12404c021c321d2acc9ffcbc762fda5d9b8fbb`。baseline 完整保存 RGB/state/memory/prompt/request/response pickle，首个 `infer_audited` 与真实 execute 各一次；H50 为 float32 `50×14`、K30 为 float32 `30×14`，`queued=30`、`dropped=30`、`logical_step=0`。唯一 accepted reset 是 episode 0 / seed `100000` / `put_back_block`；无第二 inference、seed `100001`、replay、warmup 或 probe。事件顺序为 RPC 返回后的 RAM copy、原 `run_iteration`/`after_execute`、clear、无 drain status、持久化。

修正并重跑 [`analyze_original_entry_alignment.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/tools/analyze_original_entry_alignment.py)（`221f6e640dec1649f49f3153a799f72bb40aa63f2e57e02c613dc045a26540af`）后，provenance wording 与其实际 `source_root_matches_original=true` 一致。新 [`original_entry_alignment.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/analysis/original_entry_alignment.json)（`b96be2c03c9298785b767ad751037df9680a40178df920c9f6c8e6b816610530`）确认本次 H50 前 30 行与本次实际 K30 完全相等；与旧 baseline H50 有 `499/700` 个 float32 元素不同（max abs `0.004009723663330078`，RMSE `0.000707095339374057`），本次 K30 与旧 baseline H50 前缀有 `298/420` 个不同、与旧 shadow K30 有 `301/420` 个不同。它同时保留了旧 evidence 缺完整 RGB、完整 request、真实 PRNG key、wire bytes 和旧 shadow H50 的边界；因此不能从这一次有界、替换 scheduler child 且非终态的诊断得出历史差异的因果结论。

本节是有界诊断收据，从不构成 matching smoke 或 formal。shadow 不会自动重试；先前 6 个与本节 baseline 1 个正常 action samples 合计已使用 `7/8`，剩余 **1** 个未经 Manager 再授权不得使用。HF formal 继续冻结。

## 未执行项

此前的源码修复验证仍是 CPU-only；早先 C3 有界诊断已完成 6 次首 query 采样，本报告的“原入口有界首 query 执行”节另记录随后授权的 baseline 1 次真实 action request。未启动新的完整轨迹、matching smoke、formal 100、`r_s=30` 或 HF 效果试验，未训练、未改 checkpoint、未部署，也没有新增生产源码提交。累计已使用 `7/8` 个正常 action samples；剩余 1 个仅可在 Manager 对新的有界假设明确授权后使用。
