task_revision: 1e0ca4b161d99917d15f2fbd5f0b4c6f1ef5ba0c

本阶段完成跨库回归草稿收尾；未启动 GPU、真机、rollout 或长进程。此前 live P1 修复 `ed2f2f3` 保持不变，仍由 Pascal 增量复核。

交付 workspace 与 commit：

- robot-bridge：`/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/robot-bridge`
  - live：`ed2f2f34a1eea74e8449d39b889555fdfcc659fc`
  - 跨库回归：`29a5638f4a6bdfef2f107d331c2afde9daa03697`（`test: cover openpi memory transform contract`）
- openpi：`/mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/openpi`
  - `86d1adff94d5135988edd8dcca915606c1172872`：合入已审 `ffa308d` 父链中缺失的 RMBench 配置/sidecar 依赖；未自行修改训练实现。

回归从未跟踪的 454 行草稿压缩为 259 行独立测试，删除测试自建 schema、data factory 和 recording tokenizer。它直接加载已注册的 full、serial、no-memory RMBench 配置；单字段由正式 full schema 的字段筛选参数化，多字段使用原配置。真实 `PaligemmaTokenizer`、完整 input/output transform 顺序和 `MemoryContext` 都参与，只有模型采样替换为确定性 CPU 输出。

覆盖：非 initial cache 改变真实 Pi0.5 `tokenized_prompt`；full 32 维 raw action 裁为 14 维并保留 `memory_prediction_ids`，K30 消费 model index 29/row 30；serial 返回实际动作条件 ID（特意与 logits argmax 不同）；F=0 不发送/接收 memory wire 字段。

验证：

- `JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /mnt/public/xcj/Projects/workspace/9f5a3889-49a6-4f00-af84-096d8042c3bc/openpi/.venv/bin/python -m pytest -q -p no:cacheprovider tests/scheduler/test_openpi_memory_transform_contract.py`：4 passed（8.24s）。
- 同一 OpenPI 环境 `ruff check tests/scheduler/test_openpi_memory_transform_contract.py` 与 `git diff --check`：通过。
- bridge 自身 `.venv` 运行该模块：1 skipped（缺少训练依赖，预期行为）。

剩余：Pascal 对 live 提交和本独立回归提交的 review；正式真机/rollout 验收按既有流程另行执行，CPU 结果不代表硬件完成。
