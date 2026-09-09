task_revision: 8503ba7f08913e8bc8d0570ffe57217940a1878c

阶段交付：RMBench sim bindings、六份首批 YAML 与可审计 sidecar 已就绪，保持 GO；wash-cup 已修复 JSON source-frame 共源映射，正确 v3 全量转换即将执行。未用 GPU，未启动训练或 MAM job。

workspace：`/mnt/public/xcj/Projects/workspace/7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2/openpi`

当前 openpi 交付 commit：`a75d1737539d5497b2e8d3569756ef0dc67d5ed2`。其中 sim 的独立交付为 `481527346573b73958dcd81591fc8473e20feaff`（binding）、`38bf82c1753e6e911e6215a6762cccc2a7bb15bd`（M+1 sidecar）、`2c91f9aff8275b42285c93da094302800ec65f4e`（serial/no-memory YAML）和 `63319ac984492cd8bfd8a71158200220a6e14e38`（metadata 收敛）。wash 共源映射为 `773d177b93b6a6d8569a6761ae74118bef5d4adc`，闭环 full/serial YAML 为当前 HEAD 的 `a75d1737539d5497b2e8d3569756ef0dc67d5ed2`。

RMBench：rearrange 50 ep / 20,103 converted rows、put-back 50 ep / 17,588 converted rows均已逐值核对。sidecar 每集为 M+1：前 M 行 `robot_action_target` 等于 converted `action[:, :14]`，尾行重复末 action；availability 同为 M+1。binding 使用 sidecar `action_at_row` 和 offset 0，图像、state 与 query 保持 M。来源只用 `demo_clean_state`。sidecar 的 `metadata/command.txt` 记录真实 commit/cwd/命令；只保存实际 binding manifest 与上游 converted/source metadata，无 `git_commit.txt`、`configs/` 或候选训练 YAML。RMBench 定向测试与 Ruff 检查此前通过。

wash 筛选：244 集中 172 集合格、72 集剔除；非互斥原因是缺标注 16、label6 28、labels 1..5 非各恰好一个有效范围 56。合格 phase 次序为 `1>2>3>4>5` 120 集、`2>1>3>4>5` 52 集。旧 all_172/v2 MP4-PTS 时间轴有 142,609 query 行和 13,404 个 `availability=false`；该资产禁止训练。正确 v3 JSON-clock 映射有 143,698 query 行和 13,944 个 `availability=false`。这些行保留机器人监督，但 phase 仅作 initial 输入和字段级 loss mask，绝不作为 initial 类监督。

可独立复核的 v3 两集样本：`/mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_2_15hz_s2m_master_v3_source_frame_aligned_smoke`。每个 query 的当前 state 来自 `follow_*` 14 维，action 来自下一对齐帧的 `master_*` 14 维；phase annotation 与三路视频 ffmpeg select 使用同一 JSON timestamp source mapping。ep0 为 M=1216，观测 source `[0,1204,2406]`、action source `[2,1206,2408]`；ep1 为 M=1509，观测 `[0,1493,2987]`、action `[2,1495,2989]`。开头/中段/尾部三相机比对均通过，像素 MAE < 2.61。sample 的 `command.txt` 是当时实际命令，使用已废弃 full YAML，因此只作对齐 review，不能作训练资产。

正确 v3 全量转换将使用当前闭环 full 配置，仅用于公开 API 的数据契约校验；不会将 YAML 复制进转换 metadata，训练 schema 的权威位置仍为最终 resolved `TrainConfig.memory_config`。预计八路 CPU 转码与全量验收 30–45 分钟；若实测超过 1 小时，将登记 MAM job。正式 v3 成功后会清理技术 smoke 和旧错误 v2/旧 all_172 资产，并发布最终路径、命令和验证。
