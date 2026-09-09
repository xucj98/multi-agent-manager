task_revision: 8503ba7f08913e8bc8d0570ffe57217940a1878c

阶段交付：RMBench sim bindings、六份首批 YAML 与可审计 sidecar 已就绪；wash-cup 的正确重转换仍在修复 source-frame 对齐，v2 继续禁止训练。

workspace：`/mnt/public/xcj/Projects/workspace/7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2/openpi`

当前 openpi 交付 commit：`63319ac984492cd8bfd8a71158200220a6e14e38` `fix: narrow RMBench sidecar provenance`

RMBench commit 链均由 `git rev-parse` 取得完整 SHA：

- `481527346573b73958dcd81591fc8473e20feaff`：RMBench binding。
- `38bf82c1753e6e911e6215a6762cccc2a7bb15bd`：sidecar 直接保存 `M+1` 尾行。
- `2c91f9aff8275b42285c93da094302800ec65f4e`：rearrange serial/no-memory YAML。
- `69ca14825574981989340f8645ab3713208699fb`：初版 metadata 留痕。
- `63319ac984492cd8bfd8a71158200220a6e14e38`：收敛为单个 `command.txt`，删除候选训练 YAML 复制与独立 `git_commit.txt`。

实际重生成后的 sidecar 路径：

- `/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/rearrange_blocks_demo_clean_state_shared_memory/`
- `/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/put_back_block_demo_clean_state_shared_memory/`

每个 sidecar 父目录的 `metadata/command.txt` 以注释头记录本次实际 command、cwd 和 `63319ac984492cd8bfd8a71158200220a6e14e38`。`metadata/` 只保留实际 `binding_manifest.json`、converted `meta/` 与 `demo_clean_state` 的 scene/language/seed/既有 metadata；没有 `git_commit.txt` 或 `configs/`，也没有拷贝任何候选 memory YAML。binding manifest 只表达数据绑定，不再引用训练配置；训练最终选定 schema 由训练侧唯一 resolved `TrainConfig.memory_config` 保存。

sidecar 不含 `tail_append`。每集 series 和 memory availability 均为 `M+1`；前 `M` 个 `robot_action_target` 逐值等于 converted `action[:, :14]`，第 `M` 行重复末 action；图像、state 和 query 保持 `M`。robot binding 为 sidecar 的 `series.robot_action_target`、`action_at_row`；训练 API 对该语义强制 `robot_target.time.offset=0`，避免二次移位。

全量审计通过：rearrange 50 ep、20,103 converted rows；put-back 50 ep、17,588 converted rows。100 集均逐值验证 action 前/末行与每个 availability 的 `M+1` 长度。converted `meta/`、source `metadata/` 及 scene/language/seed 的复制均与上游逐字节相等。`ruff format --check`、`ruff check` 与 `pytest -q examples/rmbench/test_rmbench_memory_adapter.py` 通过（10 passed）。未使用 GPU，未启动训练或 MAM job。

首批 YAML 已在 `examples/rmbench/memory_configs/`：四份 rearrange/put-back P2 full、`rearrange_blocks_serial_lag30.yaml`（t-30 named previous input、current t query target、selected feedback）和 `rearrange_blocks_no_memory.yaml`（`memory: []`）。这些仓库内候选训练 YAML 不再进入 sidecar metadata。

wash 已确认筛选事实：244 集中 172 集合格、72 集剔除；剔除原因为缺标注 16、label6 28、labels 1..5 非各一个有效范围 56。合格顺序为 `1>2>3>4>5` 120 集、`2>1>3>4>5` 52 集；13,404 个 phase 行 `availability=false`，只能屏蔽该字段 loss，不能静默监督为 initial。S2M state 使用当前 `follow_*` 14 维，action 使用下一对齐帧 `master_*` 14 维。

阻塞与后续：旧 `all_172_15hz_s2m_master_v2` 的视频/pose/action source mapping 最多漂移 20 raw frame，禁止训练或复用视频。修复会先以 JSON timestamps 生成唯一 source-frame mapping，再令 state、next master action、annotation 与三相机 `select` 视频共享该 mapping；先在两集的开头/中段/尾部逐帧验证。预计 mapping 与两集三相机小样本验收约 1–1.5 小时；全量 172 集需先量测，若预计超过一小时将登记 MAM job 后运行。
