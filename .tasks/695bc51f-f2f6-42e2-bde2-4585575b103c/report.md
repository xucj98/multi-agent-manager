# put-back B组训练最终交付与可评清单

六项 serial_lag30/no_memory × seed0/1/2 均完成20,000 updates、最终保存、独立checkpoint-only恢复及真实policy推理，全部READY。训练进程均退出，六条训练job验收后归档；无queued/running训练，无新增实验。通过本报告交e6908de7-4b02-465a-987b-a19eba7a315a评估队列，由其按matching smoke2→固定100协议接续并更新RMBench实验台账，本任务不重复启动eval。

## 研究目的、设计和验收范围

与put-back已有full模型比较serial lag30与robot-only no-memory的同骨干任务能力。变量为memory表达/条件方式与独立训练seed；控制相同pi05_base、put-back demo_clean_state数据、专用robot norm、bs32、20k、H50/K30。预期检验memory方式是否改变正式成功率及失败分类，并报告三seed变异；不预设优胜模型或成功率，training loss及恢复PASS不替代eval结论。

- 冻结commit：`a7f3e07346cee7260cdc3a618eedc38c0702da61`，worktree `/mnt/public/xcj/Projects/workspace/695bc51f-f2f6-42e2-bde2-4585575b103c/openpi`，分支`task/695bc51f-f2f6-42e2-bde2-4585575b103c`，工作树干净并保留供Manager归档。
- 配置只增加put-back serial/no-memory注册与对应YAML/说明/测试，不改模型、loader、schema算法。独立review15254a5f PASS；CPU真实batch/14D/padding/字段验收和两条GPU50-step smoke均PASS。详细原证据见下方历史报告。
- 数据`put_back_block_demo_clean_state_shared_memory`；sidecar `data/memory_v1/rmbench/put_back_block_demo_clean_state_shared_memory/episode_memory.json`；norm `rmbench_put_back_block_robot`，14D state/action。源数据/norm绑定已随最终metadata/assets保存。
- serial schema v1：serial_token，phase(4类)/origin_mat(5类)，lag30输入与当前query监督，train reference/infer selected。no-memory schema v1：joint_dense robot-only，无memory字段。

## 完整可评清单

所有行均使用上述完整commit；checkpoint均为最终BF16 params/assets/metadata，不含train_state。

| config | schema | seed | 状态 | step20000 loss | 绝对checkpoint路径 |
|---|---|---|---|---|---|
| pi05_rmbench_put_back_block_serial_lag30 | v1 serial_token phase/origin_mat lag30 | 0 | READY | 0.0101 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0/20000 |
| pi05_rmbench_put_back_block_serial_lag30 | v1 serial_token phase/origin_mat lag30 | 1 | READY | 0.0111 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s1/20000 |
| pi05_rmbench_put_back_block_serial_lag30 | v1 serial_token phase/origin_mat lag30 | 2 | READY | 0.0096 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s2/20000 |
| pi05_rmbench_put_back_block_no_memory | v1 joint_dense robot-only | 0 | READY | 0.0004 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s0/20000 |
| pi05_rmbench_put_back_block_no_memory | v1 joint_dense robot-only | 1 | READY | 0.0005 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s1/20000 |
| pi05_rmbench_put_back_block_no_memory | v1 joint_dense robot-only | 2 | READY | 0.0004 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_no_memory/memory20k_695bc51f_put_back_no_memory_s2/20000 |

## 逐run证据与训练登记

每项都核对200个日志区间有限、最终Save Finalize完成；metadata内唯一resolved memory_config、batch32/seed/20k/BF16、数据绑定及专用norm通过。新解释器audit拒绝训练源读取；全参数逐shape匹配、BF16且有限。serial每项56叶/3,353,466,650元素，no-memory每项51叶/3,353,433,872元素。真实推理actions[50,14]有限；serial memory_prediction_ids[1,2]有效；no-memory无memory输出。各gate退出0。

- serial_lag30 seed0：本机 GPU6，PID 4009203，job `e087cfa2-04d2-460d-8b6e-974fdd7c7b1a`。训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s0.log`；恢复日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s0_checkpoint_gate.log`。
- serial_lag30 seed1：wuwen-1 GPU0，PID 1469044，job `68dde347-ad63-46e6-a35e-08c4ced8eeec`。训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s1.log`；恢复日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s1_checkpoint_gate.log`。
- serial_lag30 seed2：wuwen-1 GPU2，PID 1469115，job `88818158-8a76-4e96-a1a5-5641dd0b47cf`。训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s2.log`；恢复日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_serial_lag30_s2_checkpoint_gate.log`。
- no_memory seed0：本机 GPU0，PID 3996599，job `14bad7c3-59cb-45d5-8173-8eb92cb9b90a`。训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s0.log`；恢复日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s0_checkpoint_gate.log`。
- no_memory seed1：wuwen-1 GPU1，PID 1469111，job `e26bc150-d705-4f9c-9ae0-d8449e11cd0e`。训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s1.log`；恢复日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s1_checkpoint_gate.log`。
- no_memory seed2：wuwen-1 GPU3，PID 1469245，job `cadcb4ac-ceb3-4a8c-a773-2ee11516f789`。训练日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s2.log`；恢复日志 `/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_no_memory_s2_checkpoint_gate.log`。

最后一项no-memory seed2于2026-09-12 20:46:46完成最终保存，step20000 grad_norm=0.0235/loss=0.0004/param_norm=1804.3890；GPU3恢复退出后4MiB/0%。其余五项资源已在各自验收时确认释放；不代表这些卡当前未被其他任务接用。

正式命令在冻结worktree执行（每行GPU/seed/exp以上表为准）：

```bash
env CUDA_VISIBLE_DEVICES=<GPU> XLA_PYTHON_CLIENT_MEM_FRACTION=0.90 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot OPENPI_DATA_HOME=/mnt/public/cache/openpi .venv/bin/python -u -B scripts/train.py <CONFIG> --exp-name=memory20k_695bc51f_put_back_<MODEL>_s<SEED> --seed=<SEED> --no-wandb-enabled
```

各run使用nohup setsid及独立日志可靠detach，不覆盖目录；登记host/PID/启动身份。seed1/2仅改变seed及唯一exp，无重复seed-only smoke。

## 清理与留痕

两条smoke临时checkpoint均已删除；正式checkpoint、metadata/assets、训练及恢复日志保留。smoke日志已复制到各seed0的`/mnt/public/xcj/Projects/openpi/logs/memory20k_695bc51f_put_back_<MODEL>_s0_artifacts`。seed1/2无额外smoke产物。

serial首次smoke gate在参数恢复成功后因合成图片误用HWC[224,224,3]而在resize失败；retry1仅改为ALOHA约定CHW[3,224,224]后通过。原失败与retry1日志完整保留，不能将首次失败隐去。no-memory seed0最终gate摘要的input_memory_ids=[1,1]是沿用serial输出标签，实际obs已移除该字段；后续gate脚本标签已修正为null，无模型/训练变更。

完整过程历史：`/mnt/public/xcj/Projects/openpi/logs/put_back_695bc51f_final_artifacts/report_history_before_final.md`。最终恢复脚本：`/mnt/public/xcj/Projects/openpi/logs/put_back_695bc51f_final_artifacts/put_back_final_gate.py`。历史中的running/queued/等待要求仅为当时快照，以本报告六项READY为准。当前所有训练与交接工作完成，正式eval成绩由e690后续产出；不再维持等待。

## Final archive cleanup

已从本 task 的 OpenPI worktree 移出 `.pytest_cache`、`.ruff_cache` 与 9 个源码/client `__pycache__` 目录；源码范围内不再残留这些临时缓存，`git status --short` 为空。共享 `.venv`、链接、tracked files、最终checkpoint和稳定gate证据均未触碰。该共享挂载不支持系统回收站，缓存暂存于可恢复隔离目录 `/tmp/mam-695bc51f-cache-8UbpR7`，不在待归档 worktree 内。Manager 可重试归档。
