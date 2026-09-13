# 交付报告

## 完成内容

- OpenPI 增加了不消费动作 RNG 的 serial prefix 状态 probe，以及使用独立 probe RNG 的 joint-dense forecast probe；普通动作推理保留原有动作 RNG 流，并在 episode reset 时恢复两个流。
- robot-bridge 增加 probe 服务端分发和 OpenPI 后端能力声明；scheduler 仅对经过 canonical Memory-v1 target contract 校验的 J/S checkpoint 开启 rolling。
- 仿真 scheduler 支持默认关闭的 `shadow`、`hf_fixed`、`hf_event`、`hf_periodic` 模式。J 按 query+1+row 对齐 forecast；event 模式使用固定 3 行窗口、2/3 阈值、连续 2 次和最小前缀 10，并仅清除当前计划未执行后缀后以动作 RNG 重新规划。S 使用 prefix-only state probe。
- rolling trace 有界保存 64 个计划，记录输入状态/Memory IDs、原始与解码 forecast、target 时刻、偏差、实际/丢弃行数、RNG 与时间；不保留相机帧。
- 高频模式要求已解析的 task_args，并拒绝 `random_light != false` 或 `crazy_random_light_rate != 0`；benchmark `--episode-file` 将该只读快照传入 scheduler。
- 补齐离线 episode boundary 处理，确保 `ep_init` 重置 rolling 状态和 policy RNG，`dataset_done` 不创建新计划。

## 交付提交与工作区

- OpenPI: `4529a91 feat: add isolated memory state probes`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi`
- robot-bridge: `53f853a feat: add rolling memory simulation modes`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge`

## 验证

- robot-bridge: `PYTHONPATH=.../openpi/packages/openpi-client/src .venv/bin/python -m pytest -q` → `502 passed, 2 skipped`。
- OpenPI: `JAX_PLATFORMS=cpu .venv/bin/python -m pytest src/openpi/policies/policy_probe_test.py src/openpi/models/pi0_probe_test.py -q` → `6 passed`。
- OpenPI Memory-v1 wire 回归：`JAX_PLATFORMS=cpu .venv/bin/python -m pytest src/openpi/training/memory_data_test.py -k 'policy_full_memory_wire or policy_serial_memory_wire' -q` → `2 passed, 8 deselected`。
- 两仓修改文件均通过 Ruff 和 `git diff --check`。

## 未执行项

未训练、未修改 checkpoint、未运行正式评测、未部署，也未启动需登记的长进程。正式 smoke/formal 评测保留给独立 owner；请 Manager 发起独立 review 4006。
