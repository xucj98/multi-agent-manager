task_revision: 5156d955bfdfcb17b9661f98f01f2a861aa9188a

完成：

- RMBench 的 rearrange_blocks / put_back_block sidecar、binding manifest 与首批 full、serial、no-memory YAML 已由独立 review 通过；sim 最终代码为 `63319ac984492cd8bfd8a71158200220a6e14e38`，Manager 已集成等价内容到独立开发分支。来源仅为恢复的 `demo_clean_state`，current truth 来自 current target 与 raw events，机器人 action 使用已预移位的 q(t+1) `action[:14]`、offset 0。
- wash-cup v3 正式转换已完成，使用冻结转换代码 `46e619e6db6bcd4f9d5d11d31b82e5f51e8522a0`，未使用 GPU、训练或真机。JSON source-frame 映射、follow state → 下一帧 master action、三相机视频及 phase 标注共用同一 selected source index。M+1 末帧修复已纳入正式数据。
- 补充了两份中文操作说明：`examples/x2robot/README.md` 和 `examples/rmbench/README.md`，说明真实路径、筛选、availability、S2M、M+1、绑定、YAML 和定向验证。
- 已清理被正式 v3 替代的 pre-46、follow→follow、v2 与 smoke 数据目录；原始 `/mnt/public/datasets/x1pro/wash-cup` 未改动。MAM 中保留简短处理记录。

workspace、交付：

- workspace：`/mnt/public/xcj/Projects/workspace/7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2/openpi`
- 转换冻结 commit：`46e619e6db6bcd4f9d5d11d31b82e5f51e8522a0`
- 最终 worktree HEAD：`377ddff2279180092ae72f42945af4f758ac20e5`（`docs: document memory v1 data adapters`）
- wash 正式输出：`/mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_172_15hz_s2m_master_v3_source_frame_aligned`
- wash 留痕：`.../meta/memory/command.txt`、`conversion.json`、`raw_episode_memory.json`、`source_metadata/`
- RMBench sidecar：`/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/{rearrange_blocks,put_back_block}_demo_clean_state_shared_memory/`

wash 正式命令和耗时：

```bash
PYTHONPATH=. .venv/bin/python examples/x2robot/convert_wash_cup_memory_to_lerobot.py \
  --memory-config examples/x2robot/memory_configs/wash_cup_phase_full_current_feedback.yaml \
  --dataset-root /mnt/public/datasets/x1pro/wash-cup \
  --output-base data/lerobot \
  --dataset-name wash_cup_x1pro_s2m_memory_v1 \
  --run-name all_172_15hz_s2m_master_v3_source_frame_aligned \
  --target-fps 15 --target-width 320 --target-height 240 \
  --video-codec h264 --num-workers 8
```

实际耗时 242.7 秒，正式目录约 2.3 GiB。长任务已用 MAM job `0ef32d88-c3fa-41df-b93c-d01379c20e70` 登记，并在成功读回和清理后归档。

读回验收：

- `meta/info.json`：172 episodes、143,698 query rows、516 video files、15 Hz；以本次实际落盘数为准，未为匹配旧统计删行。
- 13,944 个 M-row query 的 `phase` availability 为 false；这些行的 semantic/raw phase 都是 `unknown`，只屏蔽 memory loss，不删除机器人监督。M+1 尾行中另有 98 个 phase 不可用尾帧。
- 全部 172 个 sidecar 的 phase、availability、robot action、selected JSON index 都为 M+1；Parquet action 与 sidecar 前 M 行逐值相等，尾 action 重复最后一个 converted master action。所有 source index 满足 `selected[:-1] == observation`、`selected[1:] == action`。
- 逐集依据原始 annotation ranges 复算 current phase/availability 并与 sidecar 对齐；ep0 末 raw 2408 为 `label_5` / true，ep1 末 raw 2989 为 `unknown` / false。
- 读取 `command.txt` 确认实际 cwd、commit `46e619e...`、显式 source 和实际 full config；确认 `conversion.json` 的 master action/offset 0/M+1 布局和 172 份 source annotation metadata。
- 未重复 James 已通过的全视频时间轴审查；正式转换自身逐路校验 selected-frame 数，读回确认 516 个视频文件。
- `PYTHONPATH=. .venv/bin/pytest -q examples/x2robot/test_wash_cup_memory_adapter.py examples/x2robot/test_wash_cup_memory_config.py examples/rmbench/test_rmbench_memory_adapter.py`：24 passed。
- Ruff format/check（6 个适配器与测试 Python 文件）和 `git diff --check`：通过。

未完成：

- 数据层为 GO；模型训练、GPU 工作和训练 runtime 接入仍由相应 owner/Manager 单独裁定，本任务没有启动它们。
