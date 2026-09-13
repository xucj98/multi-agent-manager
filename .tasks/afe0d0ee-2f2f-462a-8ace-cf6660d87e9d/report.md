# P0 选中 query 诊断记录：live `array_ref` 窄修独立复审通过

## 审查对象与范围

- OpenPI 保持冻结提交 `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`，未改动。
- robot-bridge 审查树从 `b1695f7f04050836a764c1e85a6db163e3526ada` 快进到候选 `e147f600dc4329f330a6e2eb0335150b5b3093a3`；结束时两棵 review tree 均干净。
- 本次 diff 仅有 `docs/reference/query-diagnostic.md`、`robot_bridge/scheduler/query_diagnostic.py` 和 `tests/scheduler/test_query_diagnostic.py`（159 行）。没有新增 Policy、RNG、数组复制、GPU 或 scheduler dispatch 路径。
- 已读取当前任务修订 `f1d35929263b6219dbbcb121d41db68f9f36c4e4` 及源报告 `a217779ac9683cacd8c25d426597e9b78b32d9f0`。未修改作者树，未运行 GPU、rollout、训练、正式评测或部署。

## 复核结论

`_live_array_ref_error()` 会递归检查 live Policy sidecar，并在 recorder 取得/创建本条记录的 NPZ bundle 前拒绝任何精确的 `{"array_ref": ...}` descriptor。`record_policy_response()` 随即将其写为 `policy_sidecar_incomplete`，使用受限的 incomplete payload，因此不会产生 `status="recorded"` 却缺少 NPZ key 的文件。原 P2 的 serial raw model-action 反例和独立的 joint RNG-key 入口均走到这一集中分支。

该检查只位于 live ingress。recorder 写出后，`validate_record()` 仍照原有方式核验 JSON `array_ref` 与同 record 的 NPZ SHA-256、key、dtype、shape 和 nonfinite 标记，并在语义检查前物化数组。文档也明确了这两个阶段的边界。真实 Policy 产生的 serial/joint CPU sidecar 为 materialized arrays，能够继续录入并通过 validator；`-inf` serial logits 的离线 NPZ 路径也保持有效。

本次 scoped review 未发现新的 P1/P2。此前报告 `d1fffd76062e9b8b0ec36dd3b9506df9be18b892` 已确认的 Memory-v1 完整性、preflight、默认关闭/RNG、生命周期和旧 transform 基线归类结论保持不变。本次没有把人为 descriptor 反例泛化为真实 Policy producer 已会产生它的证据，也没有扩展到任意畸形输入空间。

## 独立验证

```bash
JAX_PLATFORMS=cpu \
PYTHONPATH=/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge \
.venv/bin/python -m pytest -q \
  /mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge/tests/scheduler/test_query_diagnostic.py \
  /mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge/tests/scheduler/test_openpi_simulation.py
# 61 passed in 7.24s

JAX_PLATFORMS=cpu \
PYTHONPATH=/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge \
.venv/bin/python -m pytest -q \
  /mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge/tests/scheduler/test_query_diagnostic.py \
  -k 'real_memory_v1_policy_sidecar_remains_recordable_at_live_ingress'
# 2 passed, 44 deselected in 5.29s

.venv/bin/ruff check robot_bridge/scheduler/query_diagnostic.py \
  tests/scheduler/test_query_diagnostic.py docs/reference/query-diagnostic.md
.venv/bin/ruff format --check robot_bridge/scheduler/query_diagnostic.py \
  tests/scheduler/test_query_diagnostic.py
git diff --check b1695f7f04050836a764c1e85a6db163e3526ada..e147f600dc4329f330a6e2eb0335150b5b3093a3
# all passed
```

另以临时目录独立构造并校验了三个最小路径：

1. 将完整 serial sidecar 的 `outputs.model_actions_before_output_transform` 替换为结构正确的 live `array_ref`，结果为 `policy_sidecar_incomplete`，recorded policy payload 不含该假 key，`validate_record()` 同样返回 incomplete。
2. 将完整 joint sidecar 的 `rng.sampling_key.key_data` 替换为同类 descriptor，结果相同。
3. 用 materialized serial sidecar 让 recorder 自己生成 JSON/NPZ descriptor，得到 `recorded` 且 `validate_record()` 成功。另运行 dry-run 和 validator，得到 `status=recorded`、`array_count=17`。

## 准入边界

代码**eligible for a minimal controlled GPU smoke**。这只表示本次 CPU 代码与离线证据合同的窄复审已通过；本轮没有执行 GPU 验收，是否启动该 smoke 仍由 Manager 按既定运行与证据合同决定。
