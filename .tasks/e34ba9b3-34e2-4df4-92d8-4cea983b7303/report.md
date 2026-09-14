# 视觉历史基线 V 工程交付

已完成 Pi0.5 视觉历史基线 V 的训练输入、推理缓存、bridge 运行时合同和 RMBench 候选入口。未改动九任务语义，也未启动 GPU、两步 technical smoke、20k 训练或闭环评测。

## 交付 commits

| 仓库 | worktree | commit |
| --- | --- | --- |
| OpenPI | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/openpi` | `96e37e840f196d3b0945994d9a9bb5980d25ca58` |
| RMBench | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/RMBench` | `a03fd1c3a40ac89542b7afe80d7188acd3dc2bd9` |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/e34ba9b3-34e2-4df4-92d8-4cea983b7303/robot-bridge` | `20dae84e5fc2e48f93e72b5c1b8a0001071fec94` |

三个 worktree 均已检查为干净状态。

## 实现内容

- OpenPI 新增固定 18 图像槽的 V 输入：episode 初始帧、最近 4 个已发生 query 和当前帧，按固定时间/相机顺序展平；按物理帧 identity 去重、禁止未来帧，短历史为零图加 false mask。
- 训练只选择 episode 内 K=30 的真实 query 行；推理端缓存仅在成功 infer 后提交，同一 frame retry 不重复进入历史，policy reset 清空 episode 缓存。
- V recipe 冻结 Pi0.5、内部 32D、机器人 state/action 14D、H=50、K=30、history=4、50 demonstrations、seed=0、batch=32、20k；唯一的两步 technical smoke 必须显式设置 `--visual-history-smoke --num-train-steps=2`。
- robot-bridge 转发 reset，验证 V metadata，使用 episode nonce + logical step 生成稳定 frame identity，强制 K30/H50/14D，绕开 legacy memory 路径，并拒绝 `run_kind=technical_smoke` 的 checkpoint。
- RMBench 候选入口位于 `experiments/pi05_visual_history_v/`，包括数据/源码/资源准入、显式 `--max-frames 10000` norm stats 命令、空 smoke/formal manifests、资源成本说明和九个未填写的 task rows。正式 policy server 必须导入上述已提交的 standalone OpenPI 源码，不能假设内嵌 `policy/pi05` 已同步。

## CPU 验证

- OpenPI：
  `PYTHONPATH=src JAX_PLATFORMS=cpu .venv/bin/pytest -q -m 'not manual' src/openpi/training/visual_history_test.py src/openpi/training/config_test.py src/openpi/training/checkpoint_metadata_test.py src/openpi/training/data_loader_test.py src/openpi/policies/policy_test.py src/openpi/models/pi0_test.py`
  — 43 passed，2 deselected。
- robot-bridge：
  `PYTHONPATH=. .venv/bin/pytest -q tests/policy/test_openpi_provenance.py tests/policy/test_openpi_metadata.py tests/scheduler/test_openpi_simulation.py`
  — 31 passed。
- RMBench：两个 JSON 通过 `python -m json.tool`；两个 manifest 的 queue runner `--dry-run` 都显示空 pending，未触发 GPU 探测或任务启动。
- 三仓库均通过 `git diff --check`。OpenPI 新增/修改的 V 文件通过 Ruff；`data_loader.py` 的全文件 Ruff 仍报告该文件基线已有的 49 个 W/Q 格式问题，新增路径的 F/E/I 检查通过，未为无关格式化扩展提交范围。

## 后续准入

尚缺每个任务的官方 task ID、50-demo 数据与三相机/14D 接口确认、同提交源码的 norm stats、保持 batch 32/原始分辨率/H50 的容量 profile，以及 Manager 的逐行资源和评测准入。满足后才可将一个已填充的 job 加入候选 manifest；两步 smoke 不能作为正式 checkpoint 或评测输入。
