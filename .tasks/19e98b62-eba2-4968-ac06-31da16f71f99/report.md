# Wash-cup R 组 seed1/2：四条正式 20k 已启动

截至本次报告发布前，四条既定的 wash-cup 20k 重复均已真实启动，并由 MAM 实时刷新为
`running`。本报告只记录已发生事实；没有把启动阶段标量当作最终模型结论。

## 固定训练合同已核对

- OpenPI worktree：`/mnt/public/xcj/Projects/workspace/19e98b62-eba2-4968-ac06-31da16f71f99/openpi`，
  clean commit `056bcc887637cc6eda565a8ad7d45c88021d4bcd`；未改源码或环境合同。
- 复用已验收 seed0 的实际 metadata、resolved config、启动命令和 50-step 保存/恢复门；seed-only
  重复未重跑 smoke 或 CPU 全套。将 seed0 的 `metadata/command.txt` 与四个 `launch_identity.json`
  的命令归一化比较后，full 和 serial 各自的两条重复都完全匹配；允许的差异只有 GPU、`--seed`、
  `--exp-name` / 独立输出及日志标识。
- 两条配置均使用 wash v3 `all_172_15hz_s2m_master_v3_source_frame_aligned`：172 合格 S2M
  episode、15 Hz、14 维 state/action、H50/K30，专用
  `x1pro_wash_cup_s2m_robot` norm（SHA256
  `c2ab0a52acf8555be2942e4adca18f4c52020009b60f2b220fd336cff8fb8da8`）。未使用
  RMBench `demo_clean_state` 数据。
- 全部单卡、batch 32、20,000 updates、final-only BF16 model-only；目标输出目录此前均不存在。
  GPU2/3 在 Manager 的 14:02 CST release 授权后即时复核为空闲，才启动 seed2。

## 运行身份与初始有限指标

| 协议 / seed | GPU | PID / MAM job | 启动时间（UTC） | Step100（均 finite） | 最终目标 |
| --- | ---: | --- | --- | --- | --- |
| full current-feedback / 1 | 4 | 308592 / `068a3272-8345-4a2b-bd2e-ef0cb78856e0` | 03:58:27 | grad 0.5014，loss 0.0794，param 1802.3861 | `checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_19e98b62_wash_full_s1/20000` |
| serial lag30 / 1 | 5 | 308846 / `7acf80e8-02ce-47ec-ac2a-86fb26347852` | 03:58:52 | grad 55.5433，loss 0.7461，param 1802.3890 | `checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_19e98b62_wash_serial_s1/20000` |
| full current-feedback / 2 | 2 | 364395 / `b257c408-531b-4bd7-931a-3edec6f9903f` | 06:04:10 | grad 0.4952，loss 0.0785，param 1802.3861 | `checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_19e98b62_wash_full_s2/20000` |
| serial lag30 / 2 | 3 | 365424 / `ecde2e78-a121-4ce8-98c8-554dd3ccfcaa` | 06:04:36 | grad 40.9969，loss 0.6359，param 1802.3890 | `checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_19e98b62_wash_serial_s2/20000` |

每个 run 根已保存 `launch_identity.json`（完整命令、source commit、host、physical GPU、PID、MAM job、
norm SHA256 和 Step100 指标），并以 `train.log` 硬链接保留对应的规范日志
`openpi/logs/memory20k_19e98b62_wash_*_s*.log`。发布前日志尾部仍显示有限指标：full seed1 Step6500、
serial seed1 Step6300、full seed2 Step4400、serial seed2 Step4400；这些是运行中快照，不是最终结论。
最终 checkpoint 的 `metadata/command.txt`、resolved `train_config.yaml`、assets 和 data metadata 是正式训练留痕。

## 文档与后续

独立 RMBench worktree 的
`experiments/memory_chunk_20260910/README_wash_seed_repeats.zh-CN.md` 已新增并更新至
`8ff984bad94c7f0611d619ce66b487ac2e623d6d`，记录研究目的、非选择性重复原则、固定输入、四个
checkpoint 路径、启动状态、日志硬链接与验收范围；没有并发修改 e690 的 `EXPERIMENT_LEDGER`。

MAM 主动唤醒已启用。本轮正常结束；任一未归档 job stopped 时会唤醒执行者，届时逐条核对唯一
`20000`、完整参数树 shape/BF16/finite、model-only、assets/metadata、checkpoint-only 恢复、退出及
GPU 回收，归档 job，并将模型交给 Manager 安排固定 5-episode offline。不会自行运行 RMBench 100、
真实机器人或部署。
