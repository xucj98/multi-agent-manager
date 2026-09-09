task_revision: adb1826c8c585b62138e002404680a9eb33a6692

# 阶段报告：wash 数据审查已完成，等待 sim binding/YAML 增量

完成与当前结论：

- 审查工作树：`/mnt/public/xcj/Projects/workspace/3e78bfec-0cb7-41f4-ab7c-e002adf50c88/openpi`，固定审查提交 `1528b7b08eb119ede615c0520d6da3e8db6804a4`；未修改交付代码、未使用 GPU、未重转数据。
- S2M 代码修复 `63f35c8` 静态语义正确：state 为当前对齐帧的 follow 左/右 position、rotation、gripper 共 14 维；action 为下一对齐帧的同布局 master 14 维。与 RMBench `3f7086271dbe49100323496218caf0ed69b761b3` 的 drawer converter 一致。修复后的 `all_172_15hz_s2m_master_v2` metadata 指向该 commit，训练绑定声明 `robot_action_target` / offset 0。
- 在修复产物 episode 0 和 3 的 Parquet 与 raw JSON 间逐行复算，state→follow 和 action→下一对齐 master 的最大绝对误差都是 0；同一 raw frame 的 follow/master 明显不同（episode 0 frame 0 的最大差为 `0.6868467`）。
- raw wash-cup 扫描独立复现：244 集中 172 合格、72 剔除；非互斥原因是缺标注 16、label6 28、label 1..5 非各一个有效区间 56。次序是 `1>2>3>4>5` 120 集、`2>1>3>4>5` 52 集。抽样确认 alternate episode 的半开区间 `[150,255)` 在 150 包含、255 不包含；含 label6、缺标注和半截区间均被过滤。
- 修复产物 172 集共 142,609 行，13,404 行 phase availability=false；`raw_series=unknown`、semantic `unknown` 与 availability=false 的不变量无例外。真实 episode 在 q=22 的 t+1 目标缺 GT 时，shared API 将 phase dense target 与 phase weight 置 0，同时保留 14 维机器人 target/weight。定向测试 `examples/x2robot/test_wash_cup_memory_adapter.py`、`examples/x2robot/test_wash_cup_memory_config.py` 和 `packages/openpi-client/src/openpi_client/memory_config_test.py` 共 29 项通过。

阻塞发现（新的，需修复后再将 wash v2 用于训练）：

- `all_172_15hz_s2m_master_v2` 的视频与 sidecar/Parquet pose 没有同源帧绑定。converter 用 JSON `timestamp` 的近邻索引填 pose/action，却用 MP4 的 30 Hz PTS 转为 15 Hz 视频并复用旧视频。两条时钟不一致。
- 复现样本为 v2 episode 0 face：q=23 sidecar state index 46、视频实际匹配 raw frame 43（MAE 4.082 对 0.801）；q=765 是 1515 对 1527（9.461 对 0.766）；q=1205 是 2387 对 2407（3.024 对 0.676）。同一 episode 的 left wrist，以及 alternate-order episode 3 face 也出现同方向不一致。q=1205 已相差 20 raw frame，约 0.67 秒；action 也随 sidecar 使用错误的下一 source index。必须让视频采样和 state/action 共用可审计的 source-frame mapping，或按 JSON 时间重新生成视频，再重建 v2 的 Parquet/sidecar/metadata；不能只改训练 offset。

sim 基础资产已独立核验：

- `rearrange_blocks_demo_clean_state_shared_memory`（50 集/20,103 帧）和 `put_back_block_demo_clean_state_shared_memory`（50 集/17,588 帧）的 metadata 都指向 `demo_clean_state`。`scene_info.json`、`language_annotation.json` 和 `metadata/robot_edge_samples.json`/`robot_edge_comparison.json` 均在 RMBench 主库的对应源目录。
- 100 集都满足 `converted_N=raw_N-1`；edge metadata 的 raw q+1 首行与尾部值同 converted action 的最大绝对误差为 0。因此已转换 robot action 必须作为 `robot_action_target` 以 offset 0 使用。
- sim `key_state_target_ids` 与 scene/language 的当前事实、阶段边界逐项复算一致；`key_state_input_ids` 在前 20 帧为 initial，之后严格为 `target_ids[q-20]`。它不能被当成 current truth。rearrange 的 button `segment_4` 是零基第五段，episode 0 confirmed 边界为 210。

未完成与后续：

- 当前公开审查基线未包含承诺中的 sim binding 和正式基线 YAML 修正；现有 wash YAML 仍是已知的 initial 输入/空 feedback 版本，不能以能 parse 作为通过。收到明确增量 commit 后，将按实验计划复核 full/serial 时序、P2 公共 mask、feedback、series/constants/events 和 initial 获取 mask。
- 未执行训练、全量离线、GPU 或数据转换；不将上述独立数据核验表述为 train/offline 闭环通过。

复现要点：使用本 worktree 的 `.venv/bin/python` 读取 raw JSON、v2 Parquet/sidecar 和 sim edge metadata；视频问题可用 OpenCV 在上述 q 逐帧读取 raw/converted MP4 后比较缩放灰度帧。所有检查均为只读 CPU 操作。
