task_revision: efcb3e8ad17e596bafc8adddc7aca6eb8852c70a

阶段状态：sim 数据/binding/YAML 已由 James 独立验收并保持 GO；wash v3 视频、pose/action 共源映射和闭环配置已由 James 报告 7f4d74e 通过。现已补齐 wash M+1 低维末行，正式 172 集转换将以该提交重新生成。未使用 GPU、未启动模型训练或真机。

workspace：`/mnt/public/xcj/Projects/workspace/7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2/openpi`

当前 openpi commit：`46e619e6db6bcd4f9d5d11d31b82e5f51e8522a0`（`fix: retain wash-cup terminal memory row`）；前置 wash 提交为 `773d177b93b6a6d8569a6761ae74118bef5d4adc`（JSON source-frame 视频映射）、`a75d1737539d5497b2e8d3569756ef0dc67d5ed2`（闭环 full/serial YAML）、`94d9927f22f18d15e91fbe69b9bb7fa5ce494502`（显式 source 路径与项目根相对输出）。sim 最终增量为 `63319ac984492cd8bfd8a71158200220a6e14e38`，已集成到主开发分支 HEAD `216cf2e`，无需重复测试或重建环境。

wash M+1 小修：`EpisodeMemoryAnnotation` 现在对完整 selected JSON source mapping 生成 phase/raw phase/availability，保留 query/state/Parquet action 的 M 行；sidecar `series.robot_action_target` 前 M 行等于已有 converted master actions，尾行重复末 action，训练仍用 offset 0。time alignment 同时保存完整 selected M+1 source index/timestamp。

James 增量复核样本：
`/mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_2_15hz_s2m_master_v3_source_frame_aligned_smoke/meta/memory/raw_episode_memory.json`

样本实际读回：
- ep0：M=1216，sidecar=1217，末 raw 2408 为 `label_5` / available=true。
- ep1：M=1509，sidecar=1510，末 raw 2989 为 `unknown` / available=false。
- 两集均逐值验证 `robot_action_target[:M] == Parquet actions`，尾行重复最后一个 action；三路已验收视频未重编码。
- sample 的 `metadata/command.txt` 记录本次真实 metadata-only command、cwd 和 `46e619e6db6bcd4f9d5d11d31b82e5f51e8522a0`，无 `git_commit.txt`、`configs/` 或候选训练 YAML。

验证：`PYTHONPATH=. .venv/bin/pytest -q examples/x2robot/test_wash_cup_memory_adapter.py examples/x2robot/test_wash_cup_memory_config.py examples/rmbench/test_rmbench_memory_adapter.py` 为 24 passed；Ruff format/check 通过。新增定向边界覆盖 raw 2408 的 label5 闭区间内情况和 raw 2989 的区间外 unknown 情况。

正式转换：旧的早期 M+1 缺失 staging 输出会被清理，随后用当前 commit 在主 openpi data 共享路径重新生成 `all_172_15hz_s2m_master_v3_source_frame_aligned`。当前 v3 JSON mapping 的实际数据口径为 143,698 M query rows / 13,944 phase unavailable rows；不删机器人行，不为匹配旧 PTS 计数删行。完成后只读回数量、格式、metadata 和首尾低维值，不重复 James 已通过的视频时间轴审查。
