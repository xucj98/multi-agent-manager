task_revision: 91530c64698867ed477219279221ce7ad964fe16

阶段回报（2026-09-10）

- wash-cup 扫描 244 集：合格 172，剔除 72。剔除原因非互斥：缺标注 16、含 label6 28、label1–5 不是各一个有效区间 56。合格次序为 `1>2>3>4>5` 120 集、`2>1>3>4>5` 52 集。
- `availability=false` 的含义是该对齐后的源帧不落在原始 `subtasks` 任一半开区间内，故该帧没有 GT；绝不能把 `unknown` 或 initial 当作该行 phase 监督。172 个合格 episode 全有内部及尾部空白，160 个另有前缀空白；原始 284,955 帧中 27,768 帧无标注、共 1,020 个 gap。15 Hz 转换输出有 13,404 行 availability=false，raw/semantic phase 均保持 `unknown`。
- 可用 wash 转换结果：`/mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_172_15hz`（172 集、142,609 parquet 行、516 视频、2.2 GiB）。逐值读回及固定 5 集 raw follower 对比已通过：state、下一对齐 action、timestamp 最大误差均为 0。
- sim 恢复目录 metadata 已确认源为 `demo_clean_state`：`rearrange_blocks_demo_clean_state_shared_memory`（50 集 / 20,103 帧）与 `put_back_block_demo_clean_state_shared_memory`（50 集 / 17,588 帧）。完整资产已由负责人于 19:57 UTC checksum dry-run 验证可用。
- sim 当前 memory 的实际绑定必须使用 `observation.key_state_target_ids[q]`：rearrange 为 phase / empty_mat_side / button_press_status，put-back 为 phase / origin_mat。`key_state_input_ids[q] = target_ids[q-20]`，首 20 帧为 config initial，不能当 current truth。精确转换 commit 复核显示 `action[q,:14] = observation.state[q+1,:14]`；直接绑定 action 时 offset=0，若以 observation state 建 `robot_observation_state` 则只取 q+1 一次，不能二次移位。
- 当前阻塞：两份原始 `data/{rearrange_blocks,put_back_block}/demo_clean_state` 仍不存在。因而可审计 converted 内部 q→q+1，却不能独立核对每集最终 action tail，或将 scene_info/language_annotation 的详细 raw 边界作为已恢复事实。需要恢复每集 HDF5、scene_info.json（rearrange：empty_mat_side、block1_place、press_return；put-back：origin_mat_name、center_pick/center_place/button_return）及 language_annotation.json（尤其 rearrange segment_4）。不会以 `demo_clean`、评测 rollout 或图像重建替代。

进行中：全量 converted sim 行级 current-target / lagged-input / q→q+1 审计；P2 两 full YAML 机器人目标完全一致的回归测试；随后更新本报告。
