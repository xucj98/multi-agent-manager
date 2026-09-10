task_revision: e0c76a5922b212bee5e40651f8b65f6c44c336f9

完成与结论：**GO。056bcc887637cc6eda565a8ad7d45c88021d4bcd 关闭 1efc1294 报告的 d10 metadata 恢复 P1，新 wash full/serial roundtrip 保持通过。本轮无具体剩余阻塞。**

workspace、审查版本：

- 复用 /mnt/public/xcj/Projects/workspace/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/openpi 及原 .venv。
- 实际 review HEAD：8062669daa483d4287e07b36f968230c50afd772；git diff 056bcc8 HEAD 为空，worktree clean、git diff --check 通过。
- robot-bridge 保持 f84edbd6eea81104a00fd85409046eaaa8712e9b。CPU-only，未改实现/运行树、未派 agent、未创建环境；未重跑 loader、wire、模型数值或 GPU。
- 已通过 wash 范围引用 1efc1294ea137848cfa96cbb8a9bb0f246d495cf；历史 CPU/R3/R4 引用 6a328471cd1493e21c3bc617b0f697b445a17a96、53ca3e2eb1526a08309c0fbd1d9d1894f7b62bc8。八路固定 d10 的既有放行继续有效。

独立增量证据：

1. 两个原始真实 50-step checkpoint 分别从 /tmp 启动 fresh Python process，执行真实 load_train_config → create_data_config(training=False)，均通过。父进程仅导入标准库；子进程在 OpenPI import 前安装 audit，拒绝训练 dataset/sidecar/YAML/norm 读取，source_attempts=[]。runtime 重建为 full joint_dense / serial serial_token，robot14/padded32、inference norm=None，resolved schema 等于恢复配置。
2. 独立比较原 tagged YAML 与恢复后 to_yaml 的完整规范化节点树：只允许 DataConfig 中两个旧 null runtime 字段消失，所有其余字段值、类型标签、嵌套 mapping/sequence 均一致。原文件逐字节前后相等，未预处理或改写输入 checkpoint。源目录根为 /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints：

| 输入目录 | train_config.yaml 前后相同的 SHA256 |
| --- | --- |
| pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50 | 440cbdd256fd45ff20b996988997815c624f8586752a0b73f208ed52eeb7859a |
| pi05_rmbench_rearrange_blocks_serial_lag30/serial_lag30_d10cc01/50 | 517d634cd2b6bf6cc361ae55a56a32bffc753ab69d26761b22820b4413139558 |

3. 新 wash full/serial 分别执行真实 checkpoint_metadata.save（未 mock metadata collection），各仅一份 resolved memory_config、无 memory_adapter/model_spec，datasets metadata 保持 fps15。各自再另起受 audit 约束的新进程恢复，完整字段/标签比较及 runtime 重建均通过，未读训练源。
4. safe YAML 实际 load_train_config 入口另做独立检查：DataConfig 非 init 字段即便携带非 null 旧值也被忽略；batch_size/seed、嵌套配置保留；普通 policy_metadata 中同名 memory_adapter/model_spec、Unicode、嵌套列表/字典和 YAML alias 均保留。随后 inference runtime 重建通过，原 safe 文件字节未变。
5. 代码静态复核：tagged 路径按当前 dataclass 的 field.init 和对应节点 tag 过滤，safe 路径按 field.init 跳过，未增加版本或字段名分支；未发现本次交付范围内的残留兼容问题。

验证命令与输出：

公共环境为 CUDA_VISIBLE_DEVICES=''、JAX_PLATFORMS=cpu、PYTHONDONTWRITEBYTECODE=1、OPENPI_DATA_HOME=/mnt/public/cache/openpi、HF_HUB_OFFLINE=1、HF_LEROBOT_HOME=/mnt/public/xcj/Projects/openpi/data/lerobot。

```text
.venv/bin/python -B -u /tmp/review-9b73-056.py
fresh_real_entry_PASS x4 (d10 full/serial + new wash full/serial)
new_wash_save_PASS x2; source_attempts=[]; original_unchanged=true
056_INCREMENTAL_PASS; exit=0

.venv/bin/python -B - <<'PY'  # 独立 safe YAML 入口断言，检查项见第4项
...
PY
safe_real_entry_PASS; exit=0

.venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=/tmp/review-9b73-056-pytest src/openpi/training/config_test.py -k 'legacy_tagged_checkpoint_ignores_runtime_memory_fields or safe_checkpoint_ignores_non_init_runtime_data_fields'
2 passed, 7 deselected in 12.80s
```

已清理临时 review 脚本、日志、pytest basetemp 和生成的 metadata 副本；两 worktree 非共享、非tracked 源码 cache 扫描为空，未跟随共享软链接。原数据、资产、checkpoint、环境与分支保留，交 Manager 归档。
