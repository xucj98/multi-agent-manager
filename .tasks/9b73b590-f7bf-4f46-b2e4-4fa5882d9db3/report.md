task_revision: 60d377c49dd6ba3bcf6a55ae2ebf417694164171

完成与结论：**wash full/serial 本轮 CPU 增量通过；7a62920 的 d10 checkpoint metadata 向后兼容未通过（P1，见下）。组合候选尚不能作为加载 d10 checkpoint 的新版交付。** 固定 d10 的八路正式运行保持已放行状态，无需重启、改写旧 metadata 或重跑 GPU50。

workspace、审查版本：

- 复用 /mnt/public/xcj/Projects/workspace/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/openpi 及原 .venv。
- 候选 062d12a5effbaf183718c9c208d880983693e64d + 7a629204b4ab6d3cd113443c538837f8fb5f08d4；实际 review HEAD 423fbe3f3d538e5bb7a3f2399bedf8fe635d663e，git diff 7a62920 HEAD 为空，git diff --check 通过。
- 仅 CPU，未修改实现、未派 agent、未新建环境。已登记 robot-bridge 保持 f84edbd6eea81104a00fd85409046eaaa8712e9b，仅静态读取 metadata 消费代码，未执行重复跨库/live 测试。
- 历史已通过项引用本任务 report 6a328471cd1493e21c3bc617b0f697b445a17a96、53ca3e2eb1526a08309c0fbd1d9d1894f7b62bc8；GPU50/put-back 沿用 Manager 验收。

**P1：init=False 使现有 d10 tagged YAML 无法恢复。**

位置：src/openpi/training/config.py:120–121；触发入口 src/openpi/training/checkpoint_metadata.py:102。现有 d10 YAML 的嵌套 DataConfig 含 memory_adapter: null、memory_model_spec: null；tyro from_yaml 仍将它们传入构造器。两个真实 50-step checkpoint 均在全新进程报同一错误，尚未进入权重加载或 inference factory：

```text
TypeError: DataConfig.__init__() got an unexpected keyword argument 'memory_adapter'
full child exit=1; serial child exit=1
```

只读复现输入根为 /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints，分别使用：

- pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50
- pi05_rmbench_rearrange_blocks_serial_lag30/serial_lag30_d10cc01/50

复现核心命令（checkpoint_dir 为上述任一完整路径）：

```bash
CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -B -c 'import sys; from openpi.training.checkpoint_metadata import load_train_config; load_train_config(sys.argv[1]).create_data_config(training=False)' "$checkpoint_dir"
```

独立复现还在 OpenPI import 前安装 source-read audit，并从 /tmp 启动子进程；没有借用父进程 schema cache。影响是新候选不能消费已验收/正在生成的 d10 格式；旧固定树与 checkpoint 权重不因此失效。修复应在新代码兼容旧 runtime null 字段，保留唯一 resolved schema；不修改已有 checkpoint。

wash 与新格式已通过的独立证据：

- 两个注册配置均走真实 create_data_loader，num_workers=0、shuffle=False、split=None，各取 batch32；143,698 rows / 172 episodes / fps15，state (32,32)、actions/weights (32,50,32)，三相机 (32,224,224,3)。使用已归档 CPU norm job396366a5 产出的 assets/memory_v1/x1pro_wash_cup_s2m_robot/norm_stats.json，只有 state/actions 且均14维。full 20维之后、serial 14维之后的 actions/weights padding 均为零。
- 抽查 ep0/4/171 的 q65：adapter actions 与真实 LeRobot/Parquet actions 全50行一致（atol=1e-6），state 原样取当前 follow14；action/state 最大差分别0.686465、0.127485、0.076816，未混成 follow target、SM2SM 或二次移位。真实 Arx 保持14维到 Normalize，独立 quantile 数值断言通过，再接 memory/tokenize/pad。face/left/right 到 base/left_wrist/right_wrist 的实际像素映射逐值一致。
- 对两配置执行未 stub 的 checkpoint_metadata.save/load，完整继承 info、conversion、source metadata。datasets.json 含 fps15、172ep、state/actions14、相机接口；upstream conversion 固定 offline IDs 为 processed IDs 的前5项，info train=0:172，follow→master、offset0 均保留。bridge backends/openpi.py:333、464–467 有从 checkpoint datasets 读取并发布 policy_hz 的现存路径，未发现此接口的 fps 缺口。
- 新 YAML 各只有一处 memory_config，不保存 memory_adapter/model_spec，memory_config_path=None；恢复 schema 相等，runtime adapter/spec 重建成功。另起全新进程、cwd=/tmp，在 import 前阻断原 dataset/sidecar/YAML/norm 的 open；两个 checkpoint-only factory 成功，source-read 尝试均为0。norm 从临时 checkpoint assets 读取。
- factory 的权重/模型 trunk 使用受控 CPU 替身，实际 Policy、Arx、Normalize、memory 和模型 transforms 均执行：非initial input [2] 进入 full one-hot/serial key_state IDs；full [2]→[4] 改变实际 tokens。输出 robot actions (50,14)，full memory IDs (50,1)、serial (1,1)，选中值3经机器人裁剪仍保留。此项仅验证新配置的 transform/wire 接线，不宣称重做真实模型数值或 GPU 验收。
- dataclasses.replace(installed_data_config) 确实清空两个 init=False runtime 字段；但当前训练 loader、norm、Policy 路径未发现 install 后 replace 调用，现存 replace 均在安装前。实际 TrainConfig replace 后 create_data_config 重建通过，当前调用路径不另列阻塞。

测试命令与输出（均在本 worktree，环境另设 PYTHONDONTWRITEBYTECODE=1、CUDA_VISIBLE_DEVICES=''、JAX_PLATFORMS=cpu、OPENPI_DATA_HOME=/mnt/public/cache/openpi、HF_HUB_OFFLINE=1、HF_LEROBOT_HOME=/mnt/public/xcj/Projects/openpi/data/lerobot）：

```text
.venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=/tmp/review-9b73-wash-author src/openpi/policies/arx_policy_test.py src/openpi/training/config_test.py -k 'wash_cup or defer_padding'
3 passed, 7 deselected

.venv/bin/python -B -u /tmp/review-9b73-wash.py
devices: TFRT_CPU_0
real_loader_PASS x2; real_metadata_PASS x2
fresh_factory_wire_PASS x2; blocked_source_attempts=[]
ALL_NEW_WASH_PROBES_PASS
exit=0
```

清理：临时独立脚本、pytest basetemp、生成的 metadata/norm 副本与临时日志已删除；两 worktree 非共享、非tracked 源码 cache 扫描为空，未跟随共享软链接。原正式数据、资产、checkpoint、环境和分支保留。剩余仅上述候选兼容性修复及其小增量复验。
