# P0 选中 query 诊断记录：b169 增量独立复审报告（仍有 P2）

## 审查对象与隔离

- OpenPI 保持 `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`，未修改。
- robot-bridge 仅从 `fa62a9febc8fab9098994d0cb8e1894a0590b7e8` 快进到冻结候选 `b1695f7f04050836a764c1e85a6db163e3526ada`。
- 原始冻结基线仍为 OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`、bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`。
- review worktree：`/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/openpi` 和 `/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge`；两棵树在复审结束时均干净。

已阅读本任务发布修订 `a77e8ca5d4303f58eda931849254f0bed64aba3a` 和源交付报告 `e5ec1cdd0017dd7a01ba3b29cc9d2035ec4e3bc0`。未修改作者源码，未运行 GPU、rollout、训练、正式评测或部署。

## 已独立确认的修复

1. **Memory-v1 evidence 合同。** 合法 serial 和 joint-dense sidecar 能写成 `recorded` 并通过离线校验；真实 CPU `Policy.infer` 路径配合完整 resolved Memory-v1 metadata 也分别成功写入并验证（joint 17 arrays，serial 20 arrays）。`metadata_incomplete` 和 `missing_key_state_output` 的真实 Policy sidecar 均改写为可见的 `policy_sidecar_incomplete`。`none` 在 metadata 声明 Memory-v1 时不能绕过合同；旧 serial sampler 的未单独观测 selected IDs 也保持 incomplete。

2. **materialized NPZ 语义复查。** 独立篡改后，serial 越界 selected ID、serial condition 与 selected ID 不一致、joint decoded ID/label 不一致，以及 joint raw coordinate 与 raw action 的声明 slice 不一致，都由 `validate_record()` 拒绝。Memory evidence 中结构错误的 `array_ref` 会在录入时得到明确 incomplete，而不会导致 recorder 抛异常或伪造 memory 完整性。

3. **preflight 顺序。** 分别把会拒绝复制的 1024×1024 ndarray 放入 `episode_info`、episode status、runtime provenance 与 selected scheduler input，并将 cap 设为 1 byte。四例都在任何诊断复制前写出小型 `not_recorded_array_limit` / `scheduler_input_preflight` 记录，未把 cap 作为 writer failure，且没有向普通 policy input 加入诊断 context。

4. **此前已通过的行为证据仍适用。** 默认关闭的输出、动作、state 和 RNG；serial cap 时保持普通三值 sampler；生命周期 retry/supersede/reset/terminal；以及 strict JSON/`-inf` NPZ 路径均沿用上轮独立结论。本轮 dry-run 重新写出并校验了 17-array 的 strict JSON/NPZ serial 记录。

## 新发现：P2，live `array_ref` 可伪造 `recorded`

`b169` 只要求 Memory-v1 特定字段在录入时已经 materialize；完整 sidecar 的其他必需 array evidence 仍可携带一个结构上正确、但没有任何 policy-side NPZ 可解析的 `array_ref`。

精确复现：以合法 serial sidecar 为起点，只将
`policy.outputs.model_actions_before_output_transform` 替换为：

```python
{
    "array_ref": {
        "key": "not-on-policy-wire",
        "dtype": "<f4",
        "shape": [2, 4],
        "nonfinite": False,
    }
}
```

在 `b169` 上，`record_policy_response()` 返回 `True`，JSON 被写为 `status="recorded"`；生成的 NPZ 不含 `not-on-policy-wire`。随后 `validate_record()` 才以 `references missing array 'not-on-policy-wire'` 拒绝该文件。该 raw model action chunk 是完成记录的必需证据。

根因是 `_Externalizer.convert()` 对 mapping 原样递归，无法为传入的 descriptor 创建数组（`robot_bridge/scheduler/query_diagnostic.py:263-285`）；`_complete_sidecar_error()` 对 raw 与 transformed action 允许 descriptor（同文件 `:904-924`）；而 `record_policy_response()` 随即写入 `recorded`（`:1210-1224`）。离线校验在 `:1024-1044` 才发现缺 key。该差异也适用于其他 live sidecar 的非-memory 必需数组，例如 RNG key、三种 input view、explicit noise 或 transformed actions。

这违反本轮要求的“录入侧与离线 validator 共享完整性合同”，并留下一个文件状态已经声称完整、但无法离线校验的记录。建议将 live Policy sidecar 的全部必需 array evidence 统一要求为 materialized host arrays（或在录入前以等价方式可靠 materialize/绑定），对任何 ingress `array_ref` 写明确 incomplete；修复后复测上述 raw-action 反例、Memory 字段反例、合法 real serial/joint 以及 preflight 路径。

## 独立验证

```bash
# OpenPI candidate
JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q \
  src/openpi/policies/policy_diagnostic_test.py
# 6 passed

# OpenPI environment + reviewed bridge candidate
JAX_PLATFORMS=cpu \
PYTHONPATH=/mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge \
.venv/bin/python -m pytest -q \
  /mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge/tests/scheduler/test_query_diagnostic.py \
  /mnt/public/xcj/Projects/workspace/afe0d0ee-2f2f-462a-8ace-cf6660d87e9d/robot-bridge/tests/scheduler/test_openpi_simulation.py
# 57 passed

# bridge serializer dry-run plus validator
.venv/bin/python scripts/query_diagnostic_dry_run.py --directory <temporary-directory>
.venv/bin/python scripts/validate_query_diagnostic.py <temporary-directory>/records/*.json
# status=recorded, array_count=17

.venv/bin/ruff check robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py tests/scheduler/test_query_diagnostic.py \
  scripts/query_diagnostic_dry_run.py
.venv/bin/ruff format --check robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py tests/scheduler/test_query_diagnostic.py \
  scripts/query_diagnostic_dry_run.py
# all passed
```

还独立执行了：真实 Policy serial/joint → recorder → validator；真实 `metadata_incomplete` / `missing_key_state_output` sidecar；四个 copy-forbidden scheduler source 的 cap 反例；以及上述 NPZ 语义篡改与 live raw-action descriptor 反例。前四类均按预期通过或拒绝，最后一例复现本报告 P2。

## 保留边界与结论

上轮对四个 read-only transform failures 的归类保持不变：同一测试 blob 在原始 `a869/f962`、原 logger `cb861/a2c7` 和旧候选均在 `src/openpi/transforms.py:246` 相同失败，早于整个 logger，不计为本候选回归。

4096×4 action-dispatch 容量观察仍未用合法 H50/K30/robot_dim=14 合同证实，未作为 blocker。

`b169` 已修复此前的 memory-completeness 与 scheduler-copy-preflight P2，但上述新的 evidence-ingress P2 仍会生成伪完整记录。因此当前候选**不具备进入最小受控 GPU smoke 的条件**；等待窄修和独立复核。GPU 验收从未执行，最终裁决仍由 Manager 作出。
