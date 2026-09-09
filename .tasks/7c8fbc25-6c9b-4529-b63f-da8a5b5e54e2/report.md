task_revision: 6c68fa0375b0a0abc8ff830b4fa86cfc09ac7693

阶段交付（sim binding 已独立提交，wash 后续修复）

workspace：`/mnt/public/xcj/Projects/workspace/7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2/openpi`

openpi sim 交付 commit：`4815273f3c15529401316138e9bc14a3bd36372f feat: add RMBench memory bindings`

- 新文件均在 `examples/rmbench/` 与 `examples/rmbench/memory_configs/`；没有改 `src/openpi` 或 `packages/openpi-client`，也没有重转图像/视频。
- 新增四份可运行 P2 YAML：rearrange/put-back 各 `full_t_plus_1`、`full_t_plus_30`。H50/K30，train 读 current reference、infer 读 cache、feedback 为 selected/last_executed/chunk_completed；两组只改变 phase target 时刻并共用 P2 `t+j+1` + `t+30` validity。robot target 为 converted `action[:14]`、`action_at_row`、`offset=0`。
- 全量只读审计通过：rearrange 50 ep/20,103 query rows，put-back 50 ep/17,588 query rows；每一行 active `observation.key_state_target_ids` 都与恢复的 `demo_clean_state` `scene_info.json`/`language_annotation.json` 重建的 current truth 一致。`observation.key_state_input_ids` 是 legacy t-20，未绑定。sidecar 保留 raw events 作为审计资料。
- `metadata/robot_edge_comparison.json` 的既有核验规则为 `converted_N=raw_N-1`，`state[:2]=raw[:2]`，`action[0]=raw[1]`，`action[-2:]=raw[-2:]`；两任务所有 50 集三个 max error 都是 0。因此 action 的 q(t+1) 绑定与 offset 0 已有源端数值证据。
- 已写共享 gitignored 训练资产（只含 JSON labels/availability/events/tail）：
  - `/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/rearrange_blocks_demo_clean_state_shared_memory/{episode_memory,binding_manifest}.json`
  - `/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/put_back_block_demo_clean_state_shared_memory/{episode_memory,binding_manifest}.json`
  每集均保留 M 个 converted query rows，外加 raw M 的 current-truth tail 和重复的 converted 最后 action；manifest 的 `sidecar_path` 是 training worktree 可解析的 `data/memory_v1/...` 相对路径。
- 训练 owner 可由 manifest 直接构造的 binding 为：state=`column(observation.state, observation_at_row, start=0, stop=14)`；三相机为 `observation.images.cam_high/cam_left_wrist/cam_right_wrist`；robot=`column(action, action_at_row, start=0, stop=14)`；memory fields=`sidecar(series.<field>, current_truth, labels)`；availability=`sidecar(availability.<field>, availability_at_row)`。

训练 prototype 的唯一剩余通用接口阻塞已用真实 episode smoke 复现：它目前将 column action 和 sidecar series 都构造成 M 行，因而 query `M-30` 的 P2 phase mask 前 30 行为 0；追加 sidecar `tail.series`/`tail.availability` 并重复 action tail 后应为 30。不能用 converted M-1 clamp 替代 raw M。请 training owner 在通用 binding 层将每集 tail append 为 M+1 logical `EpisodeMemoryData`（loader 仍只采样 M 个 converted query rows）；本 commit 的 manifest 已精确给出字段、source 和 path。

验证：`ruff format --check examples/rmbench`、`ruff check examples/rmbench`、`pytest -q examples/rmbench/test_rmbench_memory_adapter.py`（9 passed）；真实全量 100 ep audit；training owner worktree 对两份 manifest 的只读 build smoke 均复现上述 pre-tail mask 问题，确认 binding 字段本身可解析。

代码量：新增 1,179 行（adapter 688、tests 225、YAML 266），没有新增公共 framework。

wash 进度与后续：244 集中合格 172、剔除 72；无 phase GT 的 `availability=false` 共 13,404 行，必须逐字段 mask，不能当 initial/unknown 类监督。已确认 S2M 正确为 follow state -> next master action；当前 `all_172_15hz` 及 master v2 均不能作为训练资产。最新 review 发现 v2 video 与 pose/action source index 最大漂移 20 raw frame（例如 ep0 face q23 46 vs 43、q765 1515 vs 1527、q1205 2387 vs 2407），因此下一步是统一 video/state/action/annotation 的真实 source mapping 并先做两集多相机开头/中段/尾部逐帧验收。预计 30--45 分钟完成 mapping 审计与小修；若正确资产必须重输出，会单独报告时长和空间，不复用不同时间轴的视频。
