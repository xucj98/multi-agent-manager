# P0 选中 query 诊断记录接口：增量独立审查报告（等待窄修）

## 审查对象与隔离

- OpenPI 增量：`cb861d3824a46d9c243be7ff69159bcec17a0ac7..bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`
- robot-bridge 增量：`a2c7f80b99556db2147c85ca9f625ffb840b276a..fa62a9febc8fab9098994d0cb8e1894a0590b7e8`
- 原始冻结基线：OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`、bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`
- review worktree：`/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/openpi` 与 `/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge`

未修改作者源码；未运行 GPU、rollout、训练、正式评测或部署。临时基线 archive 已清理。

## 已独立核验

- Memory-v1 execute 非 `ok` 后，record 会跨 retry 保留，直至后续 supersede、terminal 或 reset 写出明确 discarded；unknown `actual_k.value` 保持 `null`。legacy full-state candidate 在 execute 前已带 record ID，失败路径不再 orphan。相关 query/simulation 窄测通过。
- 1024×1024 RGB、小数组预算的真实 Policy→codec→recorder seam 在 Policy 快照前得到 cap，产生小型 `not_recorded_array_limit` 记录，不传输完整图像 sidecar；Policy 侧 6 项诊断测试通过。
- 额外构造的 serial 小预算反例确认仍调用普通三值 sampler，未调用 details sampler；actions、condition IDs 与最终 JAX RNG 均和关闭记录相等。
- 默认关闭的最小 Policy 调用在原 logger `cb861` 与候选 `bc760` 得到相同输出键、state、actions 和最终 RNG 指纹。
- strict JSON/NPZ dry-run 成功写入并校验一条含 `-inf` serial logits 的记录（17 arrays）。候选的 JSON/NPZ link、hash、文件名、strict-finite 与初始发布保护也由 bridge 窄测覆盖。
- checkpoint 只提供位置/运行引用而非权重内容身份的边界已在 `docs/reference/query-diagnostic.md` 及 scheduler record 明确：正式诊断仍须关联独立核验、且含权重内容 hash 的 run-level manifest。

## 已接受但仍阻塞的 P2

1. **Memory 证据可被部分 sidecar 伪装为完整。**  
   `robot_bridge/scheduler/query_diagnostic.py:489-492` 的 `_complete_sidecar_error()` 仅要求 `memory.representation` 为非空字符串。将一个有效 serial sidecar 的 memory 替换为 `{"representation":"serial_token"}` 后，`record_policy_response()` 返回 true，JSON 写为 `status="recorded"`，`validate_record()` 仍通过（10 arrays）；缺少真实 `key_state_logits`、selected IDs 与 action-condition IDs。joint-dense 的 raw/decoded memory 证据同样未被该检查要求。Manager 已接受此 P2；下轮须按 representation 验证必需 evidence，并让录入侧与离线 validator 共享拒绝逻辑。

2. **scheduler context 在容量预检前复制。**  
   `robot_bridge/scheduler/openpi_simulation.py:883-890` 在 `begin_query()` 前对诊断专用的 `episode_info` 执行 `copy.deepcopy()`。以 1024×1024 RGB 的 ndarray 子类在 `__deepcopy__` 中报错、cap=1 触发时，recorder 状态为 `begin_query` write failure，且没有小型 cap record，证明复制发生在 preflight 之前。Manager 已接受此 P2；应把该 context 的容量估算移到复制前，并使超限明确可见且不影响正常调度。

这两项修复并经独立复核前，当前冻结候选**不可进入最小受控 GPU smoke**。

## 四项 read-only transform failure 的准确归类

对同一 `tests/scheduler/test_openpi_memory_transform_contract.py` 最小输入，分别强制加载：

- 原始 `a869/f962`
- 原 logger `cb861/a2c7`
- 当前 `bc760/fa62`

三组均为 4 个相同失败，均在 `src/openpi/transforms.py:246` 的 `AbsoluteActions` 原地写入只读 action 数组处报 `ValueError: output array is read-only`。bridge 测试文件在三个 commit 的 blob 相同；Policy 输出转换边界也未被本 logger 增量修改。因此这四例明确**早于整个 logger**，不是本轮修复引入，也不是 fixture 合同导致的误报。它们是独立既有问题，未计入本审查的 logger 阻塞项。

## 独立验证记录

```bash
# OpenPI candidate
JAX_PLATFORMS=cpu .venv/bin/pytest -q src/openpi/policies/policy_diagnostic_test.py
# 6 passed

# candidate OpenPI + bridge source
JAX_PLATFORMS=cpu PYTHONPATH=<review-bridge> .venv/bin/python -m pytest -q \
  <review-bridge>/tests/scheduler/test_query_diagnostic.py \
  <review-bridge>/tests/scheduler/test_openpi_simulation.py
# 35 passed

# strict JSON/NPZ standalone dry-run
.venv/bin/python scripts/query_diagnostic_dry_run.py --directory <temporary-directory>
.venv/bin/python scripts/validate_query_diagnostic.py <temporary-directory>/records/*.json
# recorded, 17 arrays
```

还以显式 `PYTHONPATH` 验证 archive 实际导入路径后，在 baseline、original logger 与 candidate 各执行 transform-contract 测试；三次均为上述同一 4 failed。该失败用于归类，不可表述为当前候选新增回归。

## 未裁决观察

4096 行、4 维 mock action 的 Policy→codec→recorder 反例显示：在 action-dispatch 证据加入总额后，record 可能在 bridge 端才成为 array-limit。该 mock 不符合本轮 RMBench 的 H50/K30/robot_dim=14 合同，且其 packed-byte 数含普通 RPC/容器开销；Manager 未将其裁决为本轮阻塞。下轮如需扩大容量审查，应先以合法合同构造相同问题。

## 下轮复审门槛

收到作者精确 clean commit 后，仅复核：

- representation-specific memory completeness，包括真实 `metadata_incomplete`、`missing_key_state_output`、旧 sampler selected-ID 缺失、伪造 `recorded` 与 offline validator；
- scheduler context 的 preflight-before-copy 反例、最小 cap record 和不影响动作/RNG；
- 受影响的 query/simulation、Policy seam 与 strict JSON/NPZ 窄测试。

当前结论：**不通过，等待两项 P2 窄修；不可进入 GPU smoke。**

