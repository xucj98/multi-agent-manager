task_revision: e842ba3262ad44843df572897a953a37571dd8c1

阶段回报（2026-09-10）

- wash-cup 扫描 244 集：合格 172，剔除 72。剔除原因非互斥：缺标注 16、含 label6 28、label1–5 不是各一个有效区间 56。合格次序为 `1>2>3>4>5` 120 集、`2>1>3>4>5` 52 集。
- `availability=false` 表示该对齐源帧不落在原始 `subtasks` 的任一半开区间，因此没有 phase GT；不能将 `unknown` 或 initial 静默作为该行监督。172 集均有内部及尾部空白，160 集另有前缀空白；15 Hz 产物有 13,404 行 `availability=false`。

S2M 阻塞已确认，`all_172_15hz` 暂停为训练资产：

- 根因在 `wash_cup_memory_adapter.load_s2m_trajectory`：它只解析 `follow_*`，再将同一数组复制给 `state` 和 `action`。此前 follower 逐值误差为零只能证明错误地复制成功，不能证明 S2M action 正确。
- 旧 drawer 的准确转换提交 `3f7086271dbe49100323496218caf0ed69b761b3` 先拼接 `follow[14] + master[14]`；state 取前 14 个 slave/follower 值，action 取后 14 个 master 值。其输出循环将 `action[frame_index + 1, :14]` 写为当前 LeRobot 行 action，故语义是 follow state 于当前对齐帧 → master action 于下一对齐帧。对应 S2M policy metadata 为 `slave_state_dim=14`、`master_action_dim=14`。
- 同一 drawer raw episode `drawer_sorting_lhy_0811@MASTER_SLAVE_MODE@2026_08_11_09_40_52` 的 frame 0（布局为左 pos/rot/gripper、右 pos/rot/gripper）给出直接反例：`follow=[-0.0022402577,-0.00025041853,-0.0029526813,0.072363025,0.093465416,-0.036769467,-0.010490417,-0.0010313406,0.0077726826,0.0092162838,0.0064907609,-0.040642711,0.031675495,-0.036049843]`；`master=[-0.0023880005,-0.00051593781,-0.001124382,0.086008182,0.082037862,-0.050148726,0,0.00010603666,0.0080337524,0.0057678223,0.0018346971,-0.054676536,0.040369338,0]`。两组均为 14 维但逐值不同。
- 修复正在本任务 worktree 实施：分离 follow state 和 master action 字段/验证，保留现有 `source_indices[:-1]` 到 `source_indices[1:]` 的下一对齐时间关系，更新 conversion metadata 为两套字段和明确 action 语义，并增加会拒绝 follower-as-action 的定向测试。修复后只写独立新输出目录；不重解码视频。

- API 增量 `0f37cfc1ae42e4703b741f0f05fd1e3c58c87e89` 已 cherry-pick 到本任务 worktree。转换已保存 `memory_phase_available` 和 raw sidecar availability；训练绑定将使用 `EpisodeMemoryData.availability={"phase": ...}`，让 API 对缺 GT 输入 initial、逐字段 target mask/weight 为零，同时保留 robot action 监督。
- sim 已恢复的 converted 数据仍确认来自 `demo_clean_state`：rearrange 50 集/20,103 帧，put-back 50 集/17,588 帧。asset owner 已恢复每任务的 `scene_info.json`、`language_annotation.json`、`metadata/robot_edge_samples.json` 和 `robot_edge_comparison.json`；源端 100 个 HDF5 的检查报告 `raw_N=converted_N+1`，state 首两行、action 首行及末两行的最大误差均为 0。现正只读核对 current target、lagged input、事件和 action `offset=0` 绑定；raw 尾部/事件不再是等待大文件的硬阻塞。
