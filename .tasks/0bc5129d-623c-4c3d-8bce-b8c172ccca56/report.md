task_revision: 5081029b1a90ea818ecd577f7d66944fc694f96b

# Runtime增量review：当前CPU范围GO，无剩余P1

**本轮变化：29a5638f的4项跨库回归通过；8ea6078修复X1非零wait，最后一项P1关闭。** 原两项live P1及prefix/cut/epoch结论沿用已接受的 `ff00b8f`；F0/sim、此前7项wire、latency、wheel结论沿用 `f51353f`、`05ba1a0`，本轮不重开。

独立工作区：`/mnt/public/xcj/Projects/workspace/0bc5129d-623c-4c3d-8bce-b8c172ccca56/`。
bridge实际HEAD：`3b079ec8cbdfce07d04011dbe46aa45aec2f029d`，含 `29a5638f4a6bdfef2f107d331c2afde9daa03697`、`8ea6078543a875b5ae223df16891cdc1fe975c66` 等价cherry-pick。后者来自作者正式报告 `be3a8da`。OpenPI保持 `f3f645938170cc6f84082d3b07bdc9820cb223c1`（ffa308d等价树）。

## 29a5638f：回归测试GO

只新增1个测试文件、259行，生产代码无变更。复用注册的full/serial/no-memory配置；单字段通过缩窄现有schema及bindings生成，未重建另一套schema。真实Paligemma tokenizer、机器人transforms、Normalize/Unnormalize、MemoryOutputs、Policy.infer及MemoryContext都执行；仅模型采样和module_jit替换为廉价CPU实现，未mock输入/输出接线。

- full单/多字段：仅cache变化就使真实tokenized_prompt改变；dense输出经过真实transform裁为14维actions，IDs仍进入Context，K30消费index29/row30。
- serial：真实输入transform把非初始IDs送到Observation；采样返回的IDs为0而logits argmax为1，Policy/Context保留返回IDs，未重新argmax。
- no-memory：真实链路允许省略两个memory字段，actions仍为14维。

**测试边界：** serial替换了整个sample_actions_with_key_state，因此证明的是采样返回IDs的透传，不额外证明Pi0内部确实用这些IDs条件化动作；该内部路径仍引用此前独立7项验收，不冒称这4项重新覆盖。按本轮“保留wire回归”的用途，结构与覆盖合理，无需为约200行目标继续压缩。

在bridge目录使用本任务OpenPI解释器：

```bash
CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 \
  ../openpi/.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/scheduler/test_openpi_memory_transform_contract.py
# 4 passed, 1 dependency deprecation warning in 10.08s；无skip
```

## 8ea6078：X1非零wait P1关闭

生产改动仅X1 _wait **+9/-7**：非零threshold走原count_after(base)路径；只有零threshold获取执行锁并同时核对排期与handoff。未改exec-loop、X1Pro、Context、发送顺序或RPC。测试 **+37/-2**，增加非零wait回归并复用既有辅助函数。

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/robot/controllers/test_execution_progress.py -k 'x1_zero_wait or x1_nonzero_wait'
# 2 passed, 18 deselected in 1.66s
```

另通过stdin执行独立CPU对照：真实X1 execute接收1行；真实loop持锁进入暂缓的_publish_action；以真实pose/JPEG buffers，同时发起零/非零wait的get_obs：

| 观察 | 实际结果 |
| --- | --- |
| threshold=1，SDK尚未release | 0.28ms返回completed=0、queued=1 |
| threshold=0，SDK尚未release | 持续等待 |
| handoff已完成，只更新pose、图像仍旧 | 零wait继续等待；旧图像查询仍为0/1 |
| 图像推进到handoff之后 | 原零wait返回1/0（总等待203.8ms）；实际只发送1次 |

这关闭 `ff00b8f` 的剩余P1，并保留同步观察约束。未重复已通过的prefix/cut/epoch或完整历史测试。

本轮无剩余CPU review blocker。证据为CPU/替代SDK发送函数；硬件连接及物理到位不在此次验收范围。真实GPU50按最新task由Manager验收，本review未执行GPU/rollout。双库干净、diff check通过；独立对照使用stdin，无临时脚本落盘，线程均join。保留worktree待Manager归档。
