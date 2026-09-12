# Wash-cup R 组 seed1/2：中断尝试已封存，正式 20k attempt3 已重启

截至本报告发布前，四条最终 20k 训练均以独立 session 的 attempt3 重新启动并由 MAM 实时刷新为
`running`。当前状态只说明已重新进入正式训练；没有把旧尝试的中间标量或当前启动状态当作最终模型结果。

## 当前正式运行

OpenPI worktree 仍是干净的 `056bcc887637cc6eda565a8ad7d45c88021d4bcd`，两个配置、wash v3
172 个 S2M episode、15 Hz、14DoF、H50/K30、专用 `x1pro_wash_cup_s2m_robot` norm（SHA256
`c2ab0a52acf8555be2942e4adca18f4c52020009b60f2b220fd336cff8fb8da8`）均未改变；未使用
RMBench `demo_clean_state`。与 seed0 的命令归一化比较仍只允许 GPU、`--seed`、独立
`--exp-name` 和日志路径差异，全部单卡 batch 32、20,000 updates、final-only BF16 model-only。

| 协议 / seed | GPU | PID / MAM job | 当前验证 | 最终目标 |
| --- | ---: | --- | --- | --- |
| full current-feedback / 1 | 4 | 593959 / `7518e4c3-ecc4-4f1a-bc39-cbb9e770b413` | running；独立 session、PPID 1；数据加载到 batch 32 | `checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_19e98b62_wash_full_s1/20000` |
| serial lag30 / 1 | 5 | 593965 / `1261e32e-293c-49b9-b4bc-cda02fe42413` | running；独立 session、PPID 1；数据加载到 batch 32 | `checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_19e98b62_wash_serial_s1/20000` |
| full current-feedback / 2 | 2 | 594097 / `b28ed7fa-6e7d-402c-80c5-a18c89caa939` | running；独立 session、PPID 1；数据加载到 batch 32 | `checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_19e98b62_wash_full_s2/20000` |
| serial lag30 / 2 | 3 | 594103 / `9a0d41f8-562d-4631-9d21-8271bda81876` | running；独立 session、PPID 1；数据加载到 batch 32 | `checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_19e98b62_wash_serial_s2/20000` |

启动前即时检查 GPU2–5 无 compute process；启动后实际 `nvidia-smi` 将四个新 PID 分别映射到
GPU4、5、2、3，各约 73.3 GiB。训练器已自行创建空的最终 run 根；每根已有
`launch_identity.json` 和指向规范 attempt3 日志的 `train.log` 硬链接。attempt3 的 Step100
有限指标尚未出现，因此本报告不宣称已通过新的初始 loss 门。

## 已停止尝试与留痕

attempt1 是真实训练：full seed1 最后 Step7500、serial seed1 Step7400、full/serial seed2 都为
Step5500，均没有 `20000`。四个 PID 在约 19:45 CST 的同一窗口消失；stdout/stderr 未留下
Python traceback、OOM 或 signal 记录，退出源只能标为未知。其 Step100 均 finite（full seed1
loss 0.0794、serial seed1 0.7461、full seed2 0.0785、serial seed2 0.6359），但不完整模型不交付
或评测。对应 MAM job 已以“interrupted before 20000”归档：
`068a3272-8345-4a2b-bd2e-ef0cb78856e0`、`7acf80e8-02ce-47ec-ac2a-86fb26347852`、
`b257c408-531b-4bd7-931a-3edec6f9903f`、`ecde2e78-a121-4ce8-98c8-554dd3ccfcaa`。

为保全首次中断痕迹而保留最终输出根的 attempt2 被训练器的 `FileExistsError` 在启动前拒绝；它未产生
训练 update、checkpoint 或 GPU compute，四个 MAM job 亦已带原因归档：
`68bf07ca-44c2-4c5b-b892-58c955548374`、`8235f836-e48e-4753-bb95-f7aedbe9cd57`、
`27ed3236-e056-47ac-a9fe-2dd7e0379200`、`465d8c0a-6adc-44c3-9eb0-390acbd4527b`。

两次失败尝试的日志、启动身份、末步数、状态 JSON 和 SHA-256 已移至不干扰最终输出根的
`/mnt/public/xcj/Projects/openpi/logs/attempt_history/19e98b62-eba2-4968-ac06-31da16f71f99/`，其中
`manifest.json` 逐条指向四个 run。attempt3 使用空目标根，因此没有改变训练器的目录契约。

## 文档与后续

独立 RMBench worktree 的
`experiments/memory_chunk_20260910/README_wash_seed_repeats.zh-CN.md` 已更新并提交至
`cdec70b16c27a8ac73cc80aa40b453f5016874b5`，记录固定研究目的、输入合同、尝试历史、当前
job/PID、checkpoint 路径与验收范围；没有并发修改 e690 的 `EXPERIMENT_LEDGER`。

MAM 主动唤醒继续监控四条 attempt3 job。本轮正常结束；任一 stopped job 会唤醒执行者，届时核对
Step100、唯一 `20000`、完整参数树 shape/BF16/finite、model-only、assets/metadata、checkpoint-only
恢复、退出和 GPU 回收后再归档，并将完成模型交给 Manager 安排固定 5-episode offline。本组不运行
RMBench 仿真 100、真实机器人或部署。

## 2026-09-13 01:33 CST：执行者交接后的实际运行核对

Manager 已将任务 rebind 给当前执行者；`mam task status` 显示 agent 为
`01a096ab-b7ba-7ce2-bd31-b38f1803b789`，既有 workspace、两个 worktree 和全部 12 条 job
记录未改变。没有新建 worktree、重启训练或重复登记 job。

即时实际核对确认四个 attempt3 PID 都存在、状态为 `R`、PPID 为 1，cwd 均为既有 OpenPI
worktree；`nvidia-smi` 将它们分别映射至约 73.3 GiB 的 GPU4/5/2/3。日志持续前进，且新的
Step100 均为 finite：

| 协议 / seed | PID / GPU | Step100 loss | 本次核对时最新完整指标 |
| --- | --- | ---: | --- |
| full / 1 | 593959 / 4 | 0.0794 | Step5400，loss 0.0128 |
| serial / 1 | 593965 / 5 | 0.7461 | Step5300，loss 0.0509 |
| full / 2 | 594097 / 2 | 0.0785 | Step5400，loss 0.0122 |
| serial / 2 | 594103 / 3 | 0.6359 | Step5400，loss 0.0573 |

四条 MAM job 仍为 running，因此没有可归档事项。本轮结束，后续由 MAM 在 stopped 事件时唤醒；
届时按既定最终 checkpoint、恢复和资源回收验收流程处理。
