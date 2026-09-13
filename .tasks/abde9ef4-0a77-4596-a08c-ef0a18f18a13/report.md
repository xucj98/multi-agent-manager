# P0 S 接续工具独立准入核查

## 结论

**不通过；候选工具需修正后再准入。** 本次只做静态/小型 CPU 证据核查，未启动 GPU、模型、reset、replay 或改动作者工具。

已重算并匹配冻结身份：prepared receipt `ca94e5fd0b9f0ea5dcf507474c49d6c73462abe097b9d025a897aab18c2f9a96`、tool manifest `46cb62aad57e883d849b37d5871547656fb0469c6ec8b8e3d87df5a236e86443`、new pair `acabef4d10f45f4e5ade67b85d5d5b79d8a5c9a9550a85c25723354337336272`、pair diff `6bface9d305e426cb24983034baa5e62017b3dd38c5810cf66688dd54048f452`。

## 阻塞问题

1. **两种科学结论仍被根级 `passed` 和进程退出语义合并。** 新 pair 在 `tools/pair_query_diagnostic_logging_invariance_replay.py:334` 计算 `passed = invariance_passed and replay_passed`，随后在 338–339 将这个合取写为根 `status`/`passed`，并在 412–413 以它决定失败退出。`derive_pair_boundary_receipt.py:211–213` 也采用同一合取。于是已知的 J 情形（同进程 invariance 为真、saved replay 为假）仍成为单一根级 `failed` pair，而不是两个独立的结论；这违反“不得合并为一个 `passed` 结果”的明确合同。嵌套的两个布尔字段保留了原始信息，但不能修复根收据和流水线终态已经合并的语义。

2. **off/on 的 ordinary-output 比较会在第一个字段差异处短路，隐藏随后状态或缺失字段差异。** `_same_value` 在 79–99 对 mapping 返回第一个 mismatch；invariance 使用它作为一个根级 `_comparison`（308–310），没有像 saved-replay 那样使用逐字段 `_field_comparisons`（107–120、325–329）。最小 CPU 反例同时改变 `actions` 和 `state` 时，实际结果仅为 `ordinary_output.actions: array values differ`，而 `state` 的真实差异没有写入 invariance comparisons。该工具须严格、可见地报告 ordinary actions、state 和缺失字段，不能由首个 actions 差异遮蔽。

3. **工具 manifest 漏掉实际执行的 timeout 配置校验器。** `run_serial_lag30_continuation.sh:32` 调用冻结 launcher；该 launcher 的 77–80 行会执行 `validate_timeout90_config.py`，它是 90 秒首 RPC、30 秒后续 RPC、episodes/query、H50/K30 和 2-record/64-MiB 预算的实际保护。然而 `invariance_replay_s_tools_manifest.json:9–25` 只列出 launcher、completed validator、status writer 和未被该新 flow 调用的旧 pair，未列 `validate_timeout90_config.py`。本地重算该缺失脚本为 `2e84d49ae71d605f411b5b4ab0ec845d729ef857e024e35838abfc4fb8d35f09`。因此部署 verifier 即使通过也不能冻结一项实际执行且负责预算的依赖，不能作为 S 运行配置身份的完整证据。

## 已核实的非阻塞部分

- pair 只有两处 `backend.infer`（284、292），只创建一个 `OpenPiBackend`（278）；第二次调用恢复同一记录的 key，并只对 saved `actions` 使用 `np.asarray(..., dtype=np.float32)`（276）。
- 新的 S 入口固定为 preflight → `serial_lag30` smoke → recorded acceptance → 一个 pair（`run_serial_lag30_continuation.sh:30–37`），没有 J、renderer gate 或 formal 分支；原 launcher 固定 GPU6、19460/19462、90/30 秒以及既有隔离 leaf。
- preflight 会核对三库冻结/clean、保留 J 哈希、GPU6、端口、task-owned 进程和 S 新 leaf；失败会保留非覆盖 receipt。smoke launcher 的已有 runner 在 `finally` 中关闭 client 并终止其 own process groups，pair 本身不启动服务。

建议仅作最小任务私有修复：让两类结论和执行完成状态各自具名，off/on 也产出逐字段严格比较，并将 transitive `validate_timeout90_config.py` 纳入冻结 manifest/部署校验。之后再复核，不需要重跑 J 或 GPU。
