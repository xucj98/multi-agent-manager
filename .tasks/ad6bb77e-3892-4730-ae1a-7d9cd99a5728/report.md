task_revision: 0d9ae60b182ae1b4ba66ecc78061d80f89b11755

完成与未完成：

- CPU 训练集成已固定：full joint-dense、serial token、F=0 no-memory、真实 M+1 sidecar loader、robot-only norm / identity memory、P2 逐坐标 FM loss、`memory_input_ids` / `memory_prediction_ids` policy wire，以及 BF16 model-only checkpoint metadata 都已接入。Banach final CPU firstfull GO 已关闭 R1/R2。
- GPU1 full t+1 实际 base smoke 已通过：50/50 optimizer updates，最终保存目录按完成 update count 为 `50`。完整参数树从磁盘恢复为 51 个 BF16 叶子、3,353,433,872 个元素、6,706,867,744 字节；assets、metadata、params 完整。checkpoint-only policy factory 对非 initial `memory_input_ids=[1,2,2]` 成功恢复，输出机器人 `actions (50,14)` 与 `memory_prediction_ids (50,3)`。
- GPU1 serial lag30 实际 base smoke 已通过：50/50 optimizer updates，独立 serial-token/key-state head 目录同样为完成计数 `50`。完整参数树为 56 个 BF16 叶子、3,353,474,844 个元素、6,706,949,688 字节。checkpoint-only policy factory 对同一非 initial 输入输出 `actions (50,14)`、`memory_prediction_ids (1,3)`，且 `key_state_prediction (3,)` 与 action-conditioned serial head 同次调用返回。
- 两个实际训练均读取 `rearrange_blocks_demo_clean_state_shared_memory`，没有使用或 fallback `demo_clean`。GPU1 全部 smoke 和恢复已结束，可释放；Locke 已按 full gate 自行获准启动冻结 worktree 的正式 20k，本任务不会启动正式训练。
- 后续实施：先从主库 `42011a3` 合入已验收 wash v3 数据增量，再做 put-back 独立 14 维 robot-only norm 的生成/真实 loader 验证、R3（aux `source=initial` 无 mask）与 R4（conditional decoder first-match）小增量，以及 wash full/serial 注册和真实 loader/config roundtrip。不会修改 Locke 的冻结运行树。

workspace、各库交付 commit：

- workspace: `/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi`
- openpi CPU integration: `ffa308d5485a2c8222d3e7735b08723c6e93a237`
- CLI repair: `5e3bfd6d46f13643c53271c1e3e1bc116dd4ff06`
- R1/R2 repair: `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50` (`fix: make memory checkpoint factories self-contained`)
- checkpoint dependency chain: `489359f -> 3d4fe31 -> cc706e37`; this task does not modify its owner files.

验证结果与成果位置：

- R1/R2 定向测试：`3 passed, 11 deselected`；Banach fresh-process 复现：`4 passed, 4 deselected`。R1/R2 改动的 `ruff check`、`ruff format --check`、`git diff --check` 全部通过。
- full 训练日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_logs/full_tplus1_d10cc01.log`；full BF16 restore：`.../full_tplus1_d10cc01_dtype_restore.log`；full checkpoint-only wire：`.../full_tplus1_d10cc01_restore_wire.log`。
- full checkpoint：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50`。
- serial 训练日志：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_logs/serial_lag30_d10cc01.log`；serial BF16 restore：`.../serial_lag30_d10cc01_dtype_restore.log`；serial checkpoint-only wire：`.../serial_lag30_d10cc01_restore_wire.log`。
- serial checkpoint：`/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/serial_lag30_d10cc01/50`。
