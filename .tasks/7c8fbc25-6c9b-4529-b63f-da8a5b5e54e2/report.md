task_revision: 4b18f95b18037ea45c01b6ec2597bd6bb6832660

阶段交付（RMBench sim 六项已准备；wash 正确重转换仍待继续）

workspace：`/mnt/public/xcj/Projects/workspace/7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2/openpi`

openpi 交付 commit：`69ca14825574981989340f8645ab3713208699fb` `feat: preserve RMBench sidecar metadata`

commit 链均由 `git rev-parse` 取得完整 SHA：

- `481527346573b73958dcd81591fc8473e20feaff` `feat: add RMBench memory bindings`
- `38bf82c1753e6e911e6215a6762cccc2a7bb15bd` `fix: store RMBench tails directly in sidecars`
- `2c91f9aff8275b42285c93da094302800ec65f4e` `feat: add rearrange serial and no-memory configs`
- `69ca14825574981989340f8645ab3713208699fb` `feat: preserve RMBench sidecar metadata`

上一份 report 误写的首个 SHA 已纠正为 `481527346573b73958dcd81591fc8473e20feaff`，不再使用手工补全值。

RMBench sidecar 已按当前实现重新生成到：

- `/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/rearrange_blocks_demo_clean_state_shared_memory/`
- `/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/put_back_block_demo_clean_state_shared_memory/`

两目录各有 `metadata/`：`command.txt` 是本次实际生成命令，`git_commit.txt` 为 `69ca14825574981989340f8645ab3713208699fb`，并复制实际 `binding_manifest.json`、同任务 YAML、converted `meta/`、以及 `demo_clean_state` 的 scene/language/seed/既有 metadata。它们只含 metadata/config；未复制代码、Parquet、视频或标签矩阵。checkpoint owner 可由 `sidecar_path` 的父目录读取该 metadata。

sidecar 没有 `tail_append`。每集 `series` 和 memory availability 均为 `M+1`；前 `M` 个 `robot_action_target` 逐值等于 converted `action[:, :14]`，第 `M` 行重复最后 converted action；图像、state 和 query 仍为 `M`。manifest 的 robot binding 是 `sidecar(series.robot_action_target, action_at_row, offset=0)`，不含切片，避免二次移位。

全量只读审计通过：rearrange 50 ep、20,103 query rows、20,153 sidecar rows；put-back 50 ep、17,588 query rows、17,638 sidecar rows。所有 100 集的 action 前/末行、每个 availability 的 `M+1` 长度和 converted mask 加 raw 末行均精确相等；复制到 `metadata/` 的全部 converted/source metadata 文件与上游逐字节相等。

新增两份英文 runnable YAML，复用 rearrange sidecar：

- `examples/rmbench/memory_configs/rearrange_blocks_serial_lag30.yaml`：三个字段 training input 为同一 named `previous=30` 的 `t-30`，负索引/缺 GT 自动 initial；infer cache；query target 为 current `t`；`current_condition` 为 reference/selected；三个字段在 `query_selected` 反馈 selected 值；H50/K30，无 P2 future validity。
- `examples/rmbench/memory_configs/rearrange_blocks_no_memory.yaml`：`memory: []`、空 input/target/updates，保留同一 `robot_action_target` 和 H50/K30。

API 语义 smoke：serial 的 query 30 读取 row 0、监督 row 30、action 从 row 30 offset 0；query 0 输入 initial。no-memory 返回空 memory input/target，并保持同一 robot targets。训练 owner 当前 reader 的 full binding 对 serial 正常构造通过。对 no-memory，若直接复用 full binding 会精确报错 `availability may only bind memory series: ['button_press_status', 'empty_mat_side', 'phase']`；同一 sidecar 改用只保留 `robot_action_target`、无 categorical availability 的 binding 则正常构造通过。训练配置需选择该 robot-only binding 或等价现有无记忆数据路径；本任务未改其 `src`。

验证：`ruff format --check examples/rmbench`、`ruff check examples/rmbench`、`pytest -q examples/rmbench/test_rmbench_memory_adapter.py`（9 passed）；CLI `--help`；两条实际生成命令；metadata byte audit；100 集 M+1 action/availability audit；训练 reader smoke。未使用 GPU、未启动训练。

未完成：wash-cup master v2 的视频与 pose/action source index 最大漂移 20 raw frame，仍禁止训练。后续需按 JSON timestamps 统一 state、next master action、annotation 和三相机视频的 source mapping，并在两集开头/中段/尾部逐帧验收后输出独立正确资产及同样的 metadata 链。
