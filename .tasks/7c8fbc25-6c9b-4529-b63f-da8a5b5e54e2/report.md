task_revision: 482b78a2c7d024a06010c96426a77f51bde17605

阶段回报（2026-09-10，sim binding 优先）

- wash-cup 已扫 244 集：合格 172，排除 72；原因非互斥为缺 annotation 16、含 label6 28、labels 1--5 不是各一个有效区间 56。合格顺序为 `1>2>3>4>5` 120 集、`2>1>3>4>5` 52 集。
- `availability=false` 表示该对齐源帧不在原始 `subtasks` 任一半开区间中，即无 phase GT；它必须输入 initial、memory target mask/weight=0，不能静默作为 initial/unknown 类监督。172 个合格 episode 均有内部或尾部 gap，160 个还有前缀 gap；15 Hz 产物共 13,404 行 false。
- wash S2M 已确认原错误为将 `follow_*` 同时用作 state/action。正确语义为当前 `follow[14]` state 到下一对齐帧 `master[14]` action；同一 raw frame 的两个 14 维向量逐值不同。`all_172_15hz` 仍暂停作为训练资产，修复将输出独立目录。

rearrange/put-back 当前可核验事实：

- 已恢复的 converted 数据均由 `demo_clean_state` 产生：rearrange 50 ep/20,103 frame，put-back 50 ep/17,588 frame。小 metadata 与 edge report 已可读；asset 的 100 HDF5 核验给出 `raw_N=converted_N+1`，state 首两行、action 首行和末两行均 max error 0。
- `observation.key_state_target_ids[t]` 是 raw/current truth at `t`；`observation.key_state_input_ids[t]` 是 legacy `t-20`，绝不绑定为 current truth。rearrange target transition 例为 140/210/254，legacy input 为 20/160/230/274；put-back target 为 138/247，legacy input 为 158/267。
- converted `action[t,:14]` 已是 raw `q(t+1)`。binding 必须为 `action_at_row`、`offset: 0`，不能再次 offset 1；两套 P2 配置的机器人目标相同。

给 training owner 的精确 binding：

```text
state = column(observation.state, semantics=observation_at_row, start=0, stop=14)
images = {cam_high: observation.images.cam_high,
          cam_left_wrist: observation.images.cam_left_wrist,
          cam_right_wrist: observation.images.cam_right_wrist}
robot_action_target = column(action, semantics=action_at_row, start=0, stop=14)
field = sidecar(series.<field>, semantics=current_truth, encoding=labels)
availability[field] = sidecar(availability.<field>, semantics=availability_at_row)
```

当前 prototype 的具体 blocker（不可静默降级）：每个 converted episode 有 M 个 loader row/action、但 P2 query `M-1` 的 `phase(t+1)` 需要已恢复 raw 第 M 个 label；robot tail 应重复 converted 最后一个 action。`MemoryDataAdapter.build_episode` 目前要求 action 和所有 series 等长，且 `MemoryBindings.validate` 禁止 robot target source=sidecar；`tail` 仅读为 scalar，当前 API 不用它扩展 series。因此侧车 M+1 truth 无法与 action column M 同时绑定。

建议 training owner 在通用 binding 层实现一次性 tail append：读 M 个 column/sidecar 值后，按 `tail.<series>` 追加恢复 raw final label、availability true，按 `tail.robot_action_target` 追加 action[-1]；loader 仍只对 M 个 converted row 取 query。这样 P2 末 query 使用真实 `t+1` label，且 robot 维度保持 action offset 0。不要以 M-1 clamp 标签替代原始尾帧。

本任务正在生成两个任务的 M+1 sidecar、binding manifest 和全量 100 episode audit；未开始 GPU 训练。
