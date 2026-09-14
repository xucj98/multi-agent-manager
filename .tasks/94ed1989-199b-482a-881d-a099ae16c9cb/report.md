# 六个 N/J 正式 20k checkpoint 的独立只读审查

结论为 `pass_with_scope_limits`：六个 seed-0、20,000-step、model-only BF16 checkpoint 的已存训练、保存、CPU 全参数恢复和 GPU checkpoint-only 恢复证据相互一致。就本审查覆盖的训练完成、保存和恢复证据而言，没有发现移交后续 eval 的阻断；这不构成正式评测成绩或成功率结论。

两个被复核的最终 receipt 保持原始哈希：N `b8240d5689c8f38f9e7d5ff5e198ccf9410b54749b41f734e4941fc78ea3b774`，J `01a4ad8016b888f5a322dee2225b41e4a7e0bb0afc5530ffd6c99c31646e8577`。独立审计 receipt 位于 `evidence/formal20k_nj/receipt.json`，SHA-256 为 `7609c6bb853c0ea42124da2c4b00d39bbbae2e4b3c57e718c287eec7048ddeab`；其重新哈希了这两份 receipt、它们引用的 N/J 训练和 CPU/GPU 恢复日志、checkpoint copied metadata/norm/binding manifest，以及六份 archived MAM job snapshot。

| 任务 | arm / schema / fields | 20k checkpoint（相对各 arm 根） | 最终 loss / grad / param | GPU checkpoint-only 输出 |
| --- | --- | --- | --- | --- |
| swap_blocks | N / `swap_blocks_no_memory` / `[]` | `pi05_rmbench_swap_blocks_no_memory/memory20k_5835fa0_nocmdbuf_swap_blocks_n_s0/20000` | 0.0017 / 0.0469 / 1805.2899 | actions `[50,14]` finite |
| battery_try | N / `battery_try_no_memory` / `[]` | `pi05_rmbench_battery_try_no_memory/memory20k_5835fa0_nocmdbuf_battery_try_n_s0/20000` | 0.0007 / 0.0233 / 1804.6187 | actions `[50,14]` finite |
| cover_blocks | N / `cover_blocks_no_memory` / `[]` | `pi05_rmbench_cover_blocks_no_memory/memory20k_5835fa0_nocmdbuf_cover_blocks_n_s0/20000` | 0.0012 / 0.0249 / 1805.1487 | actions `[50,14]` finite |
| swap_blocks | J / `swap_blocks_full_t_plus_1` / `phase, initial_empty_tray, first_origin_tray` | `pi05_rmbench_swap_blocks_full_t_plus_1/memory20k_34002dce_nocmdbuf_swap_blocks_j_s0/20000` | 0.0014 / 0.0497 / 1805.1434 | actions `[50,14]`, memory IDs `[50,3]` finite |
| battery_try | J / `battery_try_full_t_plus_1` / `phase` | `pi05_rmbench_battery_try_full_t_plus_1/memory20k_34002dce_nocmdbuf_battery_try_j_s0/20000` | 0.0008 / 0.0286 / 1804.6823 | actions `[50,14]`, memory IDs `[50,1]` finite |
| cover_blocks | J / `cover_blocks_full_t_plus_1` / `phase, red_pos, green_pos, blue_pos` | `pi05_rmbench_cover_blocks_full_t_plus_1/memory20k_34002dce_nocmdbuf_cover_blocks_j_s0/20000` | 0.0015 / 0.0470 / 1805.2087 | actions `[50,14]`, memory IDs `[50,4]` finite |

N 根为 `/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z`，冻结代码 commit 为 `5835fa04055d520e418cc1448c1bd58fa1e665cb`；J 根为 `/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z`，commit 为 `34002dce65962734c59725a0f6d982ae2c438a2d`。每个 checkpoint 顶层严格是 `_CHECKPOINT_METADATA`、`assets`、`metadata`、`params`，父目录仅有数字子项 `20000`，且没有 `train_state`。所有 train log 都重新解析到有限的 `Step 20000` 指标，并有 Orbax finalized、background save 无错误和 finalize-wait 完成标记，且没有既定 fatal marker。

六份已存 CPU 恢复 JSON 与最终 receipt 完全相同：每项均为 51 leaves、3,353,433,872 elements、6,706,867,744 bytes，shape 完整、全 BF16、全 finite。N/J GPU 恢复 JSON 也与 receipt 完全相同。checkpoint copied `train_config.yaml`、`datasets.json`、binding manifest 与 norm 被重新解析：每项为 batch 32、H50/K30、step/interval 20k、seed 0、BF16、model-only、对应 `*_demo_clean_state_shared_memory` repo 的 50 episodes；J field 是 `current_truth`、availability 是 `availability_at_row`、robot target 是 `action_at_row`。启动回执/launcher 记录实际 `XLA_FLAGS=--xla_gpu_enable_command_buffer=`、`HF_LEROBOT_HOME` unset 和 pi05_base 初始化；checkpoint `command.txt` 不含 XLA_FLAGS，符合其既有 allowlist，而非缺失证据。

六份 MAM archived snapshot 已单独保存：N swap `443b3b93-57ba-425e-bbce-f4903fea33c1`、battery `86f8ee1f-3d30-40f5-ba98-973b18232897`、cover `1495a251-7d9e-4f68-8afc-0a7cee6360f9`；J swap `4ea24e85-d5f4-40cc-8409-44beb7237e8f`、battery `a6eeac71-c0e2-4701-9530-521362c34083`、cover `191b644f-f116-4f0b-a096-1dab6da41ade`。本审查没有对 S 运行 job status、读取其日志/检查点或修改其进程；J 的共享早期 launch/receipt/snapshot 仅保存过滤后的 N/J 投影。

N validator 的动态 source-read guard 没有显式包含 `/Projects/openpi/data/memory_v1/`。冻结 N 源码的静态调用路径审查表明，checkpoint-only policy 使用 saved config、`params` 和 checkpoint `assets`，`create_data_config(training=False)` 不实例化 LeRobot dataset；N 保存的 schema 为 `memory: []`，而 `_load_sidecars` 位于未被该路径实例化的 `MemoryLeRobotDataset`。这消除了已记录 N restore 的实质性 sidecar-read 阻断，但 guard 本身较 J 窄仍是范围限制。静态说明在 `evidence/formal20k_nj/n_checkpoint_only_static_path.md`，SHA-256 为 `282489c63c8abec0f41c1694de1e57b5be77763ed2dc51162d939c5d51d7c2e9`。

可复算的小型证据位于 `evidence/formal20k_nj/`：210 个受控文件、5,725,267 bytes；collector manifest SHA-256 为 `83c742bbd71376696604b1028731835c6be01be5bffb3702a75dde532c8104c3`。它排除了 `params/**`、S、`__pycache__`、dataset/source sidecar/source norm、pi05_base 和 smoke checkpoint。没有重跑 CPU 全参数恢复、GPU restore、训练、仿真、模型加载或评测，也没有重哈希参数树。
