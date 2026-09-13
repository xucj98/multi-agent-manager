# P0 选中 query 诊断记录接口：P1/P2 窄修复交付报告

## C2 最小 GPU 验收（J 首个真实 runner/diagnostic 失败后停止）

**状态：未准入。** renderer 生命周期 gate 与 Manager 授权的替代 worktree smoke 均已通过；随后唯一的 J `full_t_plus_1` 两 episode smoke 在首个选中 query 的 policy RPC 超时处失败。该失败没有产生任务要求的完整 J 记录，因此 S smoke 和任何 logging off/on 配对均未执行。

### 源与环境准入

- C2 固定映射为 `CUDA_VISIBLE_DEVICES=6`、`SAPIEN_RENDER_DEVICE=cuda:0`、`VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json`。GPU0 已有约 16.9 GiB 外部占用，未触碰 GPU0–5、C1 GPU1/2 或 C3 GPU0。
- 隔离部署位于 `/mnt/public/xcj/Projects/state-vla/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/c2-query-diagnostic`。运行时三树均干净并固定为 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、bridge `e147f600dc4329f330a6e2eb0335150b5b3093a3`、OpenPI `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`。
- C1 首次 RMBench installer 因系统缺少 `/usr/bin/time` 在启动前失败；同参数改用 shell `time` 后成功。原始与 retry 日志分别为 `records/install-RMBench.log`、`records/install-RMBench-retry1.log`，没有修改安装器、依赖或源码。
- 40-reset renderer gate 在 C2 GPU6 完整通过：`passed=true`、`completed_count=40`、seed `100000..100039` 均 accepted/ready、`error=null`，renderer/RPC marker 均为零。receipt `records/renderer_gate_gpu6.json` 的 SHA-256 为 `f67665446952f080f43e20a8219942d584fe448da55e49f0b66543c0f1d95451`；对应 MAM job `d1d00246-929f-420b-ae5c-d2d287a4b71d` 已归档。
- 原 `worktree_env_smoke.py` 先完成 SAPIEN render，随后把 task venv 内的 cuRobo 软链解析到共享 uv archive，因路径字符串不含 `site-packages` 在 `worktree_env_smoke.py:35` 报 provenance 断言。原日志 `records/c2-gpu6-worktree-env-smoke.log`（SHA-256 `cfe2d0e9f68d4407cc1026968509db89cc0403c8639eeea5c1ce2bc26f8702ba`）仍保留，不能被称为通过。
- Manager 对该确定的软链误报授权了冻结副本：只把路径字符串断言替换为词法 venv 路径、已安装 distribution/RECORD 和稳定 wheel 内容核验，保留实际 SAPIEN render、cuRobo CUDA distance、同步、finite 和距离阈值。替代 smoke receipt `records/c2-gpu6-worktree-env-smoke-validation-receipt-v2.json` 已 `passed=true`，SHA-256 `7496adfd40ed35ce1a5b32119b9b3fe3a86c1498e9fc7758962c6a8596c08b61`。这只证明该环境准入步骤通过，不证明模型或诊断验收。
- 随后使用的 task-owned 冻结 launcher、pair 脚本与 tools manifest SHA-256 分别为 `61e3e8ce80bbe0f17fd8d1b56472038189b5be3931bca16b476c2d70b0c1d732`、`cdf577911a203994be50fd423b522e95cd5604f43c94e15b0ea247c18f8bce42`、`36d913b151db2fc624783d856266ae06f6b6493d8b89ee00b14af084d5e5a442`。J 输入 manifest SHA-256 为 `7109aec53ea9f42bb64f4772b1bda3433dc04c889100c694385be5394bff9a41`；预生成但未运行的 S manifest 为 `2cf5b99fb952a2ed244e8f1de77b515b09a19fe70341f33d8ed4e0db2ff738a3`。

### J runner 失败证据

- `query_diagnostic_full_t_plus_1_smoke_20260914` 只接受了 episode 0 / env seed `100000`；episode 1 / `100001` 从未启动。选中 record 为 episode 0、query 1、sequence 1，固定 H50/K30、`max_records=2`、`max_array_bytes=67108864`。
- 该 scheduler 已连接 robot/policy，policy server 已加载 checkpoint 并监听端口。首个选中 query 等待 policy response 时，`WebSocketClient.call()` 在 30.0 秒后抛出 `TimeoutError: timed out in 30.0s`；scheduler 以 returncode 1 退出，runner 报 `EpisodeFailure: episode 0: scheduler_exited_before_terminal: scheduler exited with returncode 1`。scheduler stdout SHA-256 为 `ecb2dc2e568c88b36915af79a0af5fe4ca19bd26e542035ec6cb36f167175815`，policy stdout 为 `6cfd96082461fb5266e15d929ce0d76f6613d2e8c26866a137436864cb7e2ac5`，runner log 为 `4e23c03d75b58fcf9ad9ac335ec9d1e77ecfdb4b81c9828649fd9d00d556290d`。policy 日志在请求后记录了由 driver 执行 PTX 编译的提示，但该观察不足以归因超时根因。
- 结果 leaf 为 `/mnt/public/xcj/Projects/state-vla/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/c2-query-diagnostic/RMBench/eval_result/query_diagnostic_c2_20260914/query_diagnostic_full_t_plus_1_smoke_20260914`。`diagnostics_summary.json` 的 benchmark 为 `failed`，目标 2、实际 episode count 1、failure reason 为 `scheduler_exited_before_terminal`。
- 记录 JSON `records/diagnostics/full_t_plus_1/records/episode-000000-query-000001-seq-000001.json`（SHA-256 `7ccb86e357790d2ac8d48af35a0d092ebbc54802fdea994f910a3ab8419acaef`）明确为 `status=policy_response_missing`、`policy.status=not_received`，reason 是该 RPC timeout。相关 NPZ SHA-256 为 `74147ab0897a5f6f3177e534b6ba9f3c41ead69d6e52037fbe57e44c6e69e4e0`，只含 policy 前输入证据；没有 policy response、J 原始 memory 坐标、decoded IDs、动作 chunk/execute slice、action-dispatch 映射或可接受的生命周期完成证据。
- `validate_query_diagnostic` 对这份内部一致的**不完整**记录退出 0，并输出 `status=policy_response_missing`（validation log SHA-256 `71f20184e5c2da55169ac92e2f083e2570da5f6d813e156b1f944ce66cb37d94`）。这不满足 task 所要求的 `recorded` J evidence，不能被解释为诊断验收通过。

### 停止边界、清理与证据链

- J acceptance 未通过，故没有重启 J；没有运行 J 的 logging off/on pair；没有启动 S `serial_lag30` smoke 或其 pairing；没有增加 episode、GPU/内存预算，也没有修改已 review 源码、依赖、共享 cache、checkpoint 或 RPC timeout。J 未收到 policy response，pair 工具也不应在这种不完整输入上运行。
- 失败后 postflight（SHA-256 `fc2265553acc175007b888a9d887b5c51dcba15df1bcc343485bd3126c02c46f`）以及最终只读复核均显示：task-owned child 为空、端口 `19460/19462` 无监听、GPU6 为 4 MiB/0%，三树 clean。MAM job `9f76c2b1-f66f-4a63-a23c-a7e78b8fd88a` 已归档，注明 30 秒 policy RPC timeout 和清理状态。
- 新 failure receipt 为 `records/c2-query-diagnostic-full_t_plus_1-failure-receipt.json`，SHA-256 `681a5b4b5dc29069d69d1821190cb52e961be4f7009152b27b148533d8a67ad2`；它链接 runner、result leaf、process logs、record/NPZ、validation、pre/postflight 与 no-retry 边界。更新后的 run-evidence manifest 为 `records/c2-query-diagnostic-run-evidence.json`，SHA-256 `4c7991530ce13cf681151dbe93d556344d5dede4f0f098e1b0e42fd3ad5f8d84`；原 J 启动前版本保存在 `records/c2-query-diagnostic-run-evidence-before-j-smoke.json`，SHA-256 `f83efd753546825b3df2a09f006b0674cc1994ee6efeabe0908df5c9fe7ab23f`。

## 交付

- OpenPI worktree：`/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/openpi`
  - 冻结基线：`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`
  - 原接口提交：`cb861d3824a46d9c243be7ff69159bcec17a0ac7`
  - 本轮修复提交：`bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6` (`Preflight selected-query policy diagnostics`)
- robot-bridge worktree：`/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/robot-bridge`
  - 冻结基线：`f9626636c4776d8eb15f9c556775cb2d12c000e5`
  - 原接口提交：`a2c7f80b99556db2147c85ca9f625ffb840b276a`
  - P1/容量修复提交：`fa62a9febc8fab9098994d0cb8e1894a0590b7e8` (`Fix selected-query diagnostic lifecycle and bounds`)
  - Memory-v1 完整性修复：`b1695f7f04050836a764c1e85a6db163e3526ada` (`Validate Memory-v1 diagnostic evidence`)
  - 本次 live ingress 修复：`e147f600dc4329f330a6e2eb0335150b5b3093a3` (`Reject live diagnostic array descriptors`)

两个 worktree 均位于 `task/8968b7f5-74f7-44db-ad0b-058d3fd556ca`；OpenPI 停在 `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`，bridge 停在 `e147f600dc4329f330a6e2eb0335150b5b3093a3`，工作树干净。

## 修复内容

### execute 非 OK 后的生命周期

- Memory v1 record 只有在 trace 已 `accepted` 且已无下一次消费时才由 observation refresh 收口。controller 的 execute RPC 非 `ok` 后，`SchedulerBase.run_iteration()` 返回 retry 而不调用 `after_execute()`；该 record 会保持 active，`actual_k.value` 为 `null`，状态为 `not_yet_observed`。
- 新的 `_discard_unaccepted_diagnostic_candidate()` 在下一次 stale `build_act_request`、terminal observation 或 reset 时显式写入 discard 原因并收口，不改变 retry、动作构造或 execute 行为。
- legacy full-state candidate 在 policy response 到达时就关联 `diagnostic_record_id`，不再等待 `after_execute()`；因此 execute 拒绝后的 supersede、terminal 和 reset 都能更新同一 record。legacy/JT 未观测 actual K 仍写 `null`，不把旧 trace 初始化值 `0` 解释成执行零行。
- CPU 回归保留真实 `SchedulerBase.run_iteration()` 的 controller execute-non-ok 路径，覆盖 Memory v1 和 legacy full-state 的 retry、supersede、terminal 与 reset。

### 采集与存储容量

- scheduler 在复制 scheduler input 前按 shape/dtype/nbytes 预检；超限时只写入小型有限的 `not_recorded_array_limit` record，不请求 Policy sidecar，也不创建 NPZ。
- selection context 传递 `max_array_bytes` 和已保留的 scheduler 字节数。OpenPI 使用剩余预算，在每个诊断专用 host/device snapshot 前预检：三种 input view、显式 noise、raw actions、output-transform output、memory J/T/S evidence、RNG key、metadata 和 sampler kwargs。
- Policy 超限时保留正常 input/transform/sampling/RNG 路径，只返回小型 `not_recorded_array_limit` sidecar。serial path 在 diagnostic sampler 尚未选中前超限时走既有 sampler，保持 logging-off 的 action 与 RNG 语义。
- bridge 对 policy/scheduler/action-dispatch 全部计划保存的证据预检后才复制或 externalize；动作关联现在先传递同步引用给 recorder，避免在 cap 判定前额外复制 output action 或 execute request。
- 真实 `Policy.infer → OpenPI msgpack → bridge codec → recorder` seam 使用 `1024×1024` RGB 图像和剩余 1 byte Policy 预算。sidecar 在 input preflight 即受限，packed response 小于 16 KiB，recorder 写有限 cap record、无 NPZ；普通 actions、state 和最终 JAX RNG 与 logging-off 一致。

### P2 完整性与 checkpoint 身份边界

- `recorded` 现在要求 schema-v1 complete sidecar、选中 context（含容量 envelope）匹配、policy/sampler identity、metadata、三种 input view 和 batching、有效 JAX/PyTorch RNG evidence、noise evidence、memory representation、raw/transform 后 actions、有限 timing，以及 scheduler action mapping 和 execute request。
- recorder 对残缺 sidecar 写显式 `policy_sidecar_incomplete`；`validate_record()` 对手工改成 `recorded` 的残缺 JSON 也会拒绝。回归覆盖空 complete sidecar 和缺失 sampling-key data。
- 每条 scheduler policy identity 都标明 `policy_dir`、runtime provenance 和可能的 step 只是位置或运行引用。接口不提供逐 query 权重内容哈希；正式诊断结论仍需关联独立核验的 run-level checkpoint manifest。没有权重内容哈希的 manifest 不可称为强内容身份。
- 文档已更新 cap 范围、超限语义、同步 I/O 边界、完整性合同和 checkpoint 限制；synthetic dry-run fixture 已补足 P2 必需 evidence。

### 本次 Memory-v1 完整性窄修

- recorder 只有在 sidecar 的实际 representation 具备必需 evidence 时才写 `recorded`：serial 要求浮点 logits、选中 IDs、实际 condition IDs/来源及字段 domain 对应；joint dense 要求原始连续坐标、整数 decoded IDs、可读 labels、action-row 数和 raw-action slice 对应。joint 坐标明确保持为非 logits。
- 录入和 `validate_record()` 使用同一语义合同。离线校验会重新 materialize NPZ `array_ref`，再核对 IDs、labels、condition source 与 raw-action slice，手工把残缺文件改成 `recorded` 不能绕过。
- `metadata_incomplete`、`missing_key_state_output`、不支持 representation、Memory metadata 下的 `none`，以及 legacy sampler 未单独观测 selected IDs 都写成可见 `policy_sidecar_incomplete`；不保存伪造的完整 memory。incomplete 记录保留有界 memory 摘要和 legacy selected-ID 状态。
- scheduler 在保存 episode status、episode info、runtime provenance 或 scheduler input 前做数组预算预检；超限只留下小型 `not_recorded_array_limit` 记录，不提前深拷贝这些诊断来源。
- 新增 CPU 回归覆盖有效 serial/joint 样本、各类局部缺失/错误维度、descriptor-only 伪 evidence、NPZ ID/label 篡改、`none` 伪装、真实 legacy serial 生成器和预检无复制路径。dry-run fixture 也更新为完整 serial 合同。

### 本次 live `array_ref` ingress 窄修

- live Policy sidecar 进入 recorder 时，集中遍历 mapping/list 结构并拒绝任何预先 externalized 的 `{"array_ref": ...}`。它只读取结构，不复制数组、不会触碰 Policy/RNG 路径。
- 拒绝结果写成小型 `policy_sidecar_incomplete`，不会把不存在于本次 NPZ bundle 的 key 留在 policy record 中；scheduler/action-dispatch 自己的合法数组仍可保留。
- 离线 JSON/NPZ 的 `array_ref` 解析没有改变：只有 recorder 生成并绑定到该 `record_id` 的 descriptors 才在 `validate_record()` 中使用。文档已明确这个边界。
- 回归复现 raw model-action descriptor 与另一个必需 RNG key descriptor，并验证真实 CPU `Policy.infer → recorder → validate_record` 的 joint-dense 和 serial-token materialized sidecar 都仍为 `recorded`。

## CPU 验证

以下均为 CPU-only 验证命令；这些命令未启动 GPU rollout、训练、正式评测、部署、仿真控制或真机控制。C2 GPU smoke 的结果见报告开头。

```bash
# OpenPI worktree
JAX_PLATFORMS=cpu .venv/bin/python -m pytest \
  src/openpi/policies/policy_diagnostic_test.py -q
# 6 passed

.venv/bin/ruff check src/openpi/policies/policy.py \
  src/openpi/policies/policy_diagnostic_test.py
.venv/bin/ruff format --check src/openpi/policies/policy.py \
  src/openpi/policies/policy_diagnostic_test.py
.venv/bin/python -m py_compile src/openpi/policies/policy.py \
  src/openpi/policies/policy_diagnostic_test.py
# all passed
```

```bash
# Run from the OpenPI worktree with bridge source on PYTHONPATH
JAX_PLATFORMS=cpu \
PYTHONPATH=/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/robot-bridge \
.venv/bin/python -m pytest \
  /mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/robot-bridge/tests/scheduler/test_query_diagnostic.py \
  /mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/robot-bridge/tests/scheduler/test_openpi_simulation.py -q
# 61 passed

# robot-bridge worktree
.venv/bin/ruff check robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py \
  tests/scheduler/test_query_diagnostic.py scripts/query_diagnostic_dry_run.py
.venv/bin/ruff format --check robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py \
  tests/scheduler/test_query_diagnostic.py scripts/query_diagnostic_dry_run.py
.venv/bin/python -m py_compile robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py \
  tests/scheduler/test_query_diagnostic.py scripts/query_diagnostic_dry_run.py
# all passed
```

```bash
# CPU-only final check after the Memory-v1 and live-ingress fixes
OUT="$(mktemp -d /tmp/query-diagnostic.XXXXXX)"
.venv/bin/python scripts/query_diagnostic_dry_run.py --directory "$OUT"
.venv/bin/python scripts/validate_query_diagnostic.py "$OUT"/records/*.json
# status=recorded, array_count=17
```

dry-run 目录已删除。两个 worktree 的 `git diff --check` 也通过。

`tests/scheduler/test_openpi_memory_transform_contract.py` 仍有 4 个既有失败：
`openpi/transforms.py:246` 的 `ValueError: output array is read-only`。该失败已在 reviewer 的干净
`cb861d3` OpenPI source 上复现，早于本轮诊断修改；本轮未改动该 transform 路径。

## 存储、时间与未验证边界

默认关闭。开启时 `max_records` 默认 16、最大 64；`max_array_bytes` 每条默认 64 MiB、最大
512 MiB。上限只计算诊断专用快照的未压缩 array nbytes；重复证据按每次保存计数，有限 JSON
metadata、NPZ/msgpack 容器开销以及普通 policy RPC input transport 不计入该数字。超限记录明确
incomplete，不带 NPZ。

选中 JSON/NPZ 写入仍在 policy response 后、execute dispatch 前同步进行，可能增加该 query 的
本地 dispatch 延迟。JAX 设备异步和 controller 内部队列、TOPP、SDK、物理 tick、相机内部状态均未由
此 CPU 修复验证。C2 的 renderer gate 和 Manager 授权的替代 CUDA worktree smoke 已通过，但真实 J runner
在首个 policy RPC 的 30 秒 deadline 前未收到 response；因此没有完整 J evidence、S evidence 或同输入 RNG 配对，不能据此作模型、记录接口的 GPU 验收或机制结论。
