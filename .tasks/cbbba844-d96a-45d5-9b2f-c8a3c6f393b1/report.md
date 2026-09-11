# U 组 initial 输入对照：阶段快照

- 已在新任务独立 worktree 建立 OpenPI（base `a869498`）、robot-bridge（base `d49f616`）和 RMBench（base `a7e9420`）；未使用旧 2a/C 工作区，也未启动 C eval 或任何正式训练。
- 已补两份 full-initial memory config、OpenPI 两个训练 config 注册、RMBench 两个 eval variant，以及 OpenPI/bridge 的定向不变量测试。设计保持 full `t+j+1` 的 target、mask、14D robot target、joint-dense action loss、feedback update/reset、H=50/K=30、norm 与 `demo_clean_state` 数据不变；训练和推理 memory input 都固定为 schema 的 `initial`。
- CPU 定向验证已通过：
  - `PYTHONPATH=. CUDA_VISIBLE_DEVICES='' .venv/bin/pytest -q examples/rmbench/test_rmbench_memory_adapter.py`：12 passed（1.37s）。
  - `PYTHONPATH=. CUDA_VISIBLE_DEVICES='' .venv/bin/pytest -q tests/scheduler/test_memory_context.py`：15 passed（1.46s）。
- 当前资源只读快照：本机 GPU1/7 空闲，`wuwen-1` GPU4–7 空闲；未抢占其他已有训练。下一步是实际 dataset batch、model/loss 与 checkpoint metadata 的 CPU 验收，然后在本机 GPU1 顺序执行两条 50-step BF16 保存/恢复 smoke。完成干净提交后提交 Manager 独立 review；review PASS 前不启动六条 20k。
