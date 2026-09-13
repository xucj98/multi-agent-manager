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

## 2026-09-13 16:40 CST：attempt3 三条完成验收与归档

本次以当前绑定执行者实际核对 PID、GPU、日志与 checkpoint，不依据旧 MAM 缓存判断。full seed1
（PID 593959/GPU4）、full seed2（594097/GPU2）及 serial seed2（594103/GPU3）都已自然退出并
释放各自 GPU；日志分别记录唯一 Step20000、Orbax finalization 和 `No errors found in background
save thread`。三条完成模型如下，均为原冻结 commit
`056bcc887637cc6eda565a8ad7d45c88021d4bcd`、bs32、20k、BF16 model-only：

| 协议 / seed | Step20000 loss | CPU 完整参数验收 | checkpoint-only GPU 恢复 | MAM job |
| --- | ---: | --- | --- | --- |
| full / 1 | 0.0050 | 51 leaves、3,353,433,872 elements；全 BF16、finite、shape 完整 | GPU4；actions `(50,14)`，memory IDs `(50,1)` | `7518e4c3-ecc4-4f1a-bc39-cbb9e770b413` 已归档 |
| full / 2 | 0.0048 | 51 leaves、3,353,433,872 elements；全 BF16、finite、shape 完整 | GPU2；actions `(50,14)`，memory IDs `(50,1)` | `b28ed7fa-6e7d-402c-80c5-a18c89caa939` 已归档 |
| serial / 2 | 0.0163 | 56 leaves、3,353,454,358 elements；全 BF16、finite、shape 完整 | GPU3；actions `(50,14)`，memory IDs `(1,1)` | `9a0d41f8-562d-4631-9d21-8271bda81876` 已归档 |

每条验证都要求 checkpoint 仅有数字目录 `20000`、`params/assets/metadata`、无 `train_state`；加载时
审计钩子拒绝原训练数据、base weights、外部 norm 和 memory YAML 读取。CPU 与 GPU 子命令均以
exit 0 完成；GPU 检查是 checkpoint 恢复与一次 finite infer，并非 offline rollout、RMBench 仿真或
部署。各 run 根的 `training_acceptance/` 目录保留 CPU/GPU 日志及
`formal_20000_acceptance.json`；`20000` 本身仍只含 `_CHECKPOINT_METADATA`、`params`、
`assets` 和 `metadata`。共享可复用验证脚本和被中断尝试的 SHA256 清单在
`/mnt/public/xcj/Projects/openpi/logs/attempt_history/19e98b62-eba2-4968-ac06-31da16f71f99/acceptance/`。
三个训练 PID 被回收前未能读取数值 exit code，因此只据成功保存日志陈述完成，不虚报 exit 0。

attempt1 的四条中断和 attempt2 的四条启动拒绝证据均未删除，仍位于同一 `attempt_history` 下的
各 run 目录；`interrupted_attempts.sha256` 记录其 JSON、启动身份与日志哈希。它们没有被当作
完成模型或纳入任何评测。

serial seed1（PID 593965，MAM `1261e32e-293c-49b9-b4bc-cda02fe42413`）在 16:40 CST 实际仍为
`R`/PPID 1、占用 GPU5；最后一次读取日志为 Step19800、loss 0.0073，最终目录尚未出现 `20000`。
它保持自然运行，未被终止、重启或重复登记。本任务的预算重排暂停规则仍生效：不会新开训练、smoke、
formal、offline 或额外 eval；该模型完成后才按同一验收与归档流程处理。

## 2026-09-13 17:02 CST：serial seed1 完成，四模型收尾

serial seed1 的 PID 593965 已自然消失，GPU5 在验收后为 1 MiB、0% 利用率。其 attempt3 日志记录
Step20000（loss 0.0093、grad_norm 0.1776、param_norm 1807.0801）和成功的 Orbax finalization；没有
将先前 Step19800 当作最终结果。唯一 checkpoint
`pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_19e98b62_wash_serial_s1/20000` 只含
`_CHECKPOINT_METADATA`、`params`、`assets`、`metadata`，无 `train_state`。

CPU 完整参数验收通过：56 leaves、3,353,454,358 elements，全部 BF16、finite 且与模型完整 shape
匹配。GPU5 checkpoint-only restore 也以 exit 0 通过，actions 为 `(50,14)`，memory IDs 为 `(1,1)`；
同样拒绝原训练数据、base weights、外部 norm 和 memory YAML 读取，未执行 offline rollout 或其他评测。
验收日志和 `formal_20000_acceptance.json` 位于该 run 根的 `training_acceptance/`，params disk bytes 为
5,257,150,891、metadata file count 为 185。原 PID 在检查前已回收，故不虚报数字训练 exit code，只依据
finalization 日志描述完成。

MAM job `1261e32e-293c-49b9-b4bc-cda02fe42413` 已归档；本任务现有 12 条 job 均已归档。最终 20k
模型为：full seed1 loss 0.0050、full seed2 loss 0.0048、serial seed1 loss 0.0093、serial seed2 loss
0.0163。RMBench 训练台账已更新为最终四模型清单并提交为 `c886ff2d58117b3f35de76fb7dbfcd8bfa07ee89`
（`docs: finalize wash seed repeat results`）；
它同时明确 checkpoint 可复用但当前预算重排暂停新增训练、smoke、formal、offline 和额外 eval。

attempt1 中断与 attempt2 启动拒绝的全部证据仍保留在
`/mnt/public/xcj/Projects/openpi/logs/attempt_history/19e98b62-eba2-4968-ac06-31da16f71f99/`，
其 SHA256 清单未变；这些失败/中断 run 没有被重训、丢弃或纳入任何结果。当前没有未归档 job 或可执行
实验事项，保留 worktree、checkpoint 和证据供 Manager 验收与后续排期。

## 2026-09-13：归档前稳定清单与材料保全完成

Manager 已独立接受四份 `formal_20000_acceptance.json`、每份五个 checkpoint metadata 哈希、验证脚本
及全部 CPU/GPU restore 日志。本轮未复制 checkpoint 参数或数据集，未启动训练、评测、offline、部署或
runtime；只建立了以下稳定小型索引和 Git 保全材料：

- [稳定四模型清单](/mnt/public/xcj/Projects/openpi/checkpoints/README_19e98b62_wash_seed_repeats.md)：四个 checkpoint、run 根的 `training_acceptance`、完整训练日志、历史 attempt1/2 与验证脚本的稳定引用。
- [归档 manifest](/mnt/public/xcj/Projects/openpi/checkpoints/archive_19e98b62_wash_seed_repeats/MANIFEST.md)：四组五个 checkpoint metadata、训练/验收日志与历史清单的 SHA256；还记录 cleanup 范围和 workspace 依赖审计。
- [归档 SHA256SUMS](/mnt/public/xcj/Projects/openpi/checkpoints/archive_19e98b62_wash_seed_repeats/SHA256SUMS)：`sha256sum -c` 全部通过；自身 SHA256 为 `9b1a17dca61201b6d923ad8a5dc6652a632b1c667f29ed7c9133bf8e8fb1b54a`。
- RMBench 最终说明的 byte-for-byte 副本、完整未合并文档分支 bundle（head `c886ff2d58117b3f35de76fb7dbfcd8bfa07ee89`）及 OpenPI 训练源完整 history bundle（head `056bcc887637cc6eda565a8ad7d45c88021d4bcd`）均在同一归档目录。两 bundle 通过 `git bundle verify`，并在 fresh bare repository 中实际 fetch、`git fsck --no-dangling` 和目标提交解析；RMBench 恢复的 README SHA256 与归档副本一致。

OpenPI 源提交也仍由 `codex/put-back-memory-baselines` 和 `codex/unified-sim-real-runtime` 本地分支可达，
但额外完整 bundle 消除了对其分支寿命的依赖。checkpoint/验收/日志均在共享稳定路径；历史
`cwd` 和 `metadata/command.txt` 中出现的 task workspace 仅是不可变训练 provenance，完成模型的
checkpoint-only restore 与归档材料不依赖该 workspace。

清理只删除了四份已被 manifest 记录 SHA256 的 task-created
`attempt3_running_20260912T1954CST/checkpoint_root_trace_receipt.json`；它们已由各 run 根的
`launch_identity.json`、完整 `train.log` 和 `training_acceptance` 覆盖。没有发现 task workspace 中
非 virtualenv 的 `__pycache__`、`.pytest_cache`、`.ruff_cache` 或 `.pyc`；virtualenv cache、历史日志、
启动身份、模型参数、数据和未知材料均保留。所有 12 条 MAM job 已归档，当前无可执行实验事项；等待
Manager 验收并 archive 本任务。
