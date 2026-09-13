# 第一波 N / J / S 训练与 RMBench Memory-v1 交付进展

## 执行树与共同运行合同

- N 的已接受正式执行树保持为 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/loader/openpi`，clean `5835fa04055d520e418cc1448c1bd58fa1e665cb`；它没有被 J/S 修改。
- J/S 使用独立执行树 `/mnt/public/xcj/Projects/workspace/e3bc64f1-7f0d-46d2-9e54-831aa1727384/js/openpi`，clean `34002dce65962734c59725a0f6d982ae2c438a2d`。它相对已审核 J/S candidate `afb7a4d` 只合入已经验收的 episode-cache projection / nested binding loader 改动。
- 全部 run 使用默认 `/root/.cache -> /mnt/public/xcj/cache`，不设置 `HF_LEROBOT_HOME`，seed 0、batch 32、H50/K30、model-only BF16。wuwen-1 的 driver 为 535.54.03 / CUDA 12.2，jax/jaxlib 为 0.5.3；launcher、`pids.tsv` 和 receipt 显式保存 `XLA_FLAGS=--xla_gpu_enable_command_buffer=`。checkpoint `command.txt` 的既有 allowlist 不记录该变量，未改写 checkpoint metadata 来掩盖此限制。

## N：已接受的 gate 与运行中的正式 20k

N 的 smoke gate 根为：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_smoke_5835fa0_nocmdbuf_20260913T0923Z`

三条真实数据 smoke 都完成 step 50，保存 model-only checkpoint，并通过 CPU 全参数 BF16/shape/finite 与 checkpoint-only GPU policy `[50,14]` finite 恢复。详细 receipt：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_smoke_5835fa0_nocmdbuf_20260913T0923Z/validation/wave1_n_smoke_receipt.json`

N 的正式 root 为：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z`

| task | GPU | PID | MAM job |
| --- | ---: | ---: | --- |
| swap_blocks N | 0 | 2621614 | `443b3b93-57ba-425e-bbce-f4903fea33c1` |
| battery_try N | 2 | 2621615 | `86f8ee1f-3d30-40f5-ba98-973b18232897` |
| cover_blocks N | 4 | 2621616 | `1495a251-7d9e-4f68-8afc-0a7cee6360f9` |

它们从 `pi05_base` 独立初始化，未从 smoke 续训；N 的正式 step-100 receipt 已保存在该 root 的 `formal_step100_receipt.json`。

## J/S：semantic sidecar 与 loader gate

三份新 semantic sidecar 与 N 的 action-only sidecar 并列存放，未覆盖 `robot_only/`：

`/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/{swap_blocks,battery_try,cover_blocks}_demo_clean_state_shared_memory/episode_memory.json`

每份都逐集验证 50 episodes：Parquet `action[:14]` 的 q(t+1) 对齐、M+1 repeated tail、从 `demo_clean_state` source metadata 重算的 current truth、availability、events、field vocabulary、manifest 和 copied provenance 全部精确相等，且数值有限。

| task | query rows | semantic sidecar SHA-256 | manifest SHA-256 |
| --- | ---: | --- | --- |
| swap_blocks | 29,920 | `ba697b8c93dd3034d93ae2032efce22ea7b496023abb0a6d8dd2e5d8defef5c1` | `777e3cecb7299dd9ac0798e37427caeb489da4610d00b1d91409239cc3119bc0` |
| battery_try | 32,626 | `75bf188165027a06bf68e2924590f540252af78a0b099ace9cf40f4595de69cb` | `c8cd9c122734460b313e58748fd318f73be52945e2d296185b1c0c7b69138c4a` |
| cover_blocks | 50,904 | `573b0a5e02aec8f16cf5800348e883ab9951dc5d0f8febeabef931e5e47886ea` | `1b2a189e5c078fec45855ddf4e8be1b9fbe10acd920770ae40b0342cc65f7517` |

验证日志和生成前 robot-only 哈希位于：

`/mnt/public/xcj/Projects/openpi/assets/memory_v1/js_execution_34002dce_20260913T1005Z/semantic_generation/`

`/mnt/public/xcj/Projects/openpi/assets/memory_v1/js_execution_34002dce_20260913T1005Z/semantic_validation/`

定向 CPU suite 通过 68 项：`memory_data_test.py`、`test_rmbench_memory_adapter.py`、`config_memory_test.py`、`config_test.py`。五条 J/S config 的真实三相机、shuffle、`num_workers=2`、batch 32、三批 loader gate 也全部有限；full 动作/状态为 `[32,50,32]`，serial 的 token fields 分别为 swap `[32,3]`、cover `[32,4]`。日志：

`/mnt/public/xcj/Projects/openpi/assets/memory_v1/js_execution_34002dce_20260913T1005Z/loader_gate/`

## J/S：完成的 50-step smoke 与 checkpoint-only gate

五条真实数据 smoke root：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_smoke_34002dce_nocmdbuf_20260913T1015Z`

每条完成 50 次更新、保存且通过独立 checkpoint-only gate：

- CPU：完整参数 key/shape，BF16、finite；full 为 51 leaves，serial 为 56 leaves。
- GPU：有限机器人动作 `[50,14]`；full memory output 为 `[50,F]`，serial 为 `[1,F]`。
- checkpoint metadata、copy-in norm、schema、sidecar binding/provenance 均匹配；audit hook 拒绝 dataset、`pi05_base`、source sidecar/assets 与原 YAML 的读取。

具体 restore JSON 日志和 validator 位于 smoke root 的 `validation/`；`validate_js_checkpoint.py` 及其 SHA-256 也保存在该目录。

| GPU | config | smoke memory output |
| ---: | --- | --- |
| 1 | `pi05_rmbench_swap_blocks_full_t_plus_1` | `[50,3]` |
| 3 | `pi05_rmbench_battery_try_full_t_plus_1` | `[50,1]` |
| 5 | `pi05_rmbench_cover_blocks_full_t_plus_1` | `[50,4]` |
| 6 | `pi05_rmbench_swap_blocks_serial_lag30` | `[1,3]` |
| 7 | `pi05_rmbench_cover_blocks_serial_lag30` | `[1,4]` |

## J/S：已启动的正式 20k

所有 J/S 正式训练在完成各自 smoke + CPU/GPU restore gate 后，从 `pi05_base` 独立初始化，未从 smoke checkpoint 续训。正式 root：

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z`

`validation/formal_start_receipt.json` 记录每条 smoke gate、sidecar/manifest、robot-only 哈希、运行命令合同与 MAM job。五个正式 run 已实际出现在 wuwen-1 GPU pmon，MAM 亦以真实远端 PID 登记：

| task | GPU | PID | MAM job | config |
| --- | ---: | ---: | --- | --- |
| swap J | 1 | 2646142 | `4ea24e85-d5f4-40cc-8409-44beb7237e8f` | `pi05_rmbench_swap_blocks_full_t_plus_1` |
| battery J | 3 | 2646143 | `a6eeac71-c0e2-4701-9530-521362c34083` | `pi05_rmbench_battery_try_full_t_plus_1` |
| cover J | 5 | 2646144 | `191b644f-f116-4f0b-a096-1dab6da41ade` | `pi05_rmbench_cover_blocks_full_t_plus_1` |
| swap S | 6 | 2646145 | `cb3e5246-fa74-40df-8325-0431f9587f73` | `pi05_rmbench_swap_blocks_serial_lag30` |
| cover S | 7 | 2646146 | `081f64c5-ae21-4062-b7ea-1dd281ddaa1f` | `pi05_rmbench_cover_blocks_serial_lag30` |

下一项运行验收为每条 step-100 的有限 loss、GPU占用、日志和 receipt；20k 完成后再按 task 合同做最终参数/metadata/shape/BF16/finite 与 checkpoint-only 恢复，随后归档对应 MAM job。


## J/S：正式训练 step 100 回执

`/mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/formal_step100_receipt.json` 已在五条日志均出现 step 100 后生成，并由脚本再次核验五条远端 PID 存活、五组 `loss` / `grad_norm` / `param_norm` 均为有限数，同时保存 pmon、GPU 使用率和各训练日志的 SHA-256。当前 receipt SHA-256 为 `5d73850921cc3d5610ea035abd3a6a541ff0658e0d8a6708c3869f6eced7743a`。

| task | arm | GPU | PID | step 100 loss | grad norm | param norm |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| swap_blocks | J | 1 | 2646142 | 0.2167 | 1.1243 | 1802.3861 |
| battery_try | J | 3 | 2646143 | 0.0844 | 0.7095 | 1802.3865 |
| cover_blocks | J | 5 | 2646144 | 0.2557 | 1.3287 | 1802.3861 |
| swap_blocks | S | 6 | 2646145 | 0.6530 | 40.1187 | 1802.3918 |
| cover_blocks | S | 7 | 2646146 | 0.8665 | 39.2737 | 1802.3960 |

回执的 pmon 快照将 PID 2646142–2646146 分别映射到 GPU 1/3/5/6/7；随后 `ps` 再次确认五个训练进程均为 `Rl`。这些是仍在运行的 20k 正式训练，尚未归档；20k 结束后才执行最终 checkpoint 恢复验收和 job 收尾。
