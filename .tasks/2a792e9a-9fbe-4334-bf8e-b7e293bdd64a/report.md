# press_button / blocks_ranking_try 数据与 N 接入进度

## 已提交实现

- RMBench worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/RMBench`
  - `f4e84c0252dd777c9f066a401a0970ad4a274c76`：确定性 seed stream、保留 eval seed 拒绝、planning/replay append-only audit、成功 replay 校验、两任务来源记录和 S/J 来源合同草案。
  - `74db6317bb4b690abc7b49258c5a2d402861f1f0`：修正物理 event 到 HDF5 observation 行的对齐；保留保存边界以便复查。
- OpenPI worktree：`/mnt/public/xcj/Projects/workspace/2a792e9a-9fbe-4334-bf8e-b7e293bdd64a/openpi`
  - `2bcf3a1551445d73777a959d5050872a4333f5af`：审计过的 N 转换器、pi05 无 memory 模板、测试和 CPU norm-stat 命令。

RMBench 来源合同草案：
`RMBench/docs/press_button_blocks_ranking_source_contract_draft.zh-CN.md`。
它明确将 `press_button` 的可见数字与实际 qpos 阈值按压分开；ranking 只保留可见颜色/位置、过去尝试、物理按压和标记为 `manager_confirmation_required` 的环境反馈，不写 sampled permutation、block internal identity 或正确排序。

## 已验证

- RMBench：`PYTHONPATH=. .venv/bin/python -m py_compile script/collect_data.py envs/_base_task.py envs/press_button.py envs/blocks_ranking_try.py`、`git diff --check` 通过。
- Observation 行修复：边界 `0, 1, 65, 629` 映射到 HDF5 行 `0, 0, 64, 628`。
- OpenPI：

  ```bash
  PYTHONPATH=. .venv/bin/python -m pytest -q \
    src/openpi/training/config_test.py \
    examples/rmbench/test_convert_rmbench_no_memory_to_lerobot.py
  ```

  结果：`12 passed`。转换器只生成 current 14D state、`q(t+1)` 14D action、当前三路 RGB 和确定性 `seen` prompt；不写 memory 或 scene labels。
- 既有 press 两集 smoke 的转换与 CPU-only norm-stat 已成功，作为链路早期证据；该 smoke 的 event 坐标采用旧边界语义，不能作为本次最终来源对齐验收，已由 `74db631` 修复并在下列 fresh smoke 中复验。

## 正在运行的 fresh smoke

2026-09-14 19:59 CST 在 clean RMBench commit `74db631` 上启动，未登记 MAM job（短 smoke）：

```bash
CUDA_VISIBLE_DEVICES=2 SAPIEN_RENDER_DEVICE=cuda:0 PYTHONPATH=. .venv/bin/python \
  script/collect_data.py press_button demo_clean_state \
  --seed-start 410000 --seed-stride 1 --max-attempts 60 \
  --overrides episode_num=2 save_path=./data_smoke_postcommit

CUDA_VISIBLE_DEVICES=3 SAPIEN_RENDER_DEVICE=cuda:0 PYTHONPATH=. .venv/bin/python \
  script/collect_data.py blocks_ranking_try demo_clean_state \
  --seed-start 420000 --seed-stride 1 --max-attempts 60 \
  --overrides episode_num=2 save_path=./data_smoke_postcommit
```

产物与日志：

```text
RMBench/data_smoke_postcommit/press_button/demo_clean_state/
RMBench/data_smoke_postcommit/blocks_ranking_try/demo_clean_state/
RMBench/data_smoke_postcommit/_logs/
```

启动前 GPU2/3 均为 0% utilization、14.7/80 GiB used；运行期间两个任务分别使用 GPU2/3。当前处于采集执行，尚未宣称任何 50 条 canonical dataset 就绪。

## 后续受控步骤

fresh smoke 通过 audit、HDF5 行对齐、scene provenance 和 ranking 泄漏检查后，分别在 GPU2/3 从 clean commit 启动各 50 条生成，并以 `setsid` 保存 stdout/pid、用 `mam job add` 登记。每个 50 条完成即单独审计、转换为 LeRobot、以 CPU 计算 `--max-frames 10000` norm stats 并发布进度。不会启动 20k 训练；训练前仍须由 Manager 验收数据完整性、来源/标签合同、CPU 验证和短恢复候选。
