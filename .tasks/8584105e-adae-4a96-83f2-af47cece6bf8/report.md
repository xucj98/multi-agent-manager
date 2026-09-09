task_revision: b4bace43f3874b2e54f39383933d043b85887bae

完成与未完成：完成一轮限定范围的只读定位及追加的 phase 选择核对；未实施、未建 worktree/环境、未跑训练/eval，未读取 GPU 或 checkpoint 资产；按 Manager 确认，不调查主 openpi 的环境。

工作区、各库交付 commit：MAM workspace `/mnt/public/xcj/Projects/workspace/8584105e-adae-4a96-83f2-af47cece6bf8`，按要求只读且无 worktree/交付 commit。openpi `codex/unified-sim-real-runtime` @ `71c80db723a242c61cfe429dd6794e9ece3cbcf1`（干净）；robot-bridge 同分支 @ `b17f6c53ffbc1030972a9820cf592f28b937d501`（已有未跟踪 `docs/design/low-dimensional-memory-design-space.zh-CN.md`，未触碰）；RMBench `xcj-dev` @ `e31d14fe0818235d471b371924ea30c273e75c7a`（干净）。

关键事实：

| 职责 | 已有入口/可复用机制 | 最小接入点 |
| --- | --- | --- |
| openpi 样本、模型、checkpoint | `training/config.py` 的 `LeRobotX2RobotMemoryDataConfig` 和 ALOHA key-state 配置；`policies/arx_policy.py::ArxSm2smInputs` 已生成 `memory_action_valid`/`action_loss_mask` 及 token sidecar；`models/pi0.py::sample_actions_with_key_state` 支持 serial；`training/checkpoint_metadata.py` 保存/恢复 train config 与 datasets 元数据。 | 将已解析的 memory 字段映射到现有 dense 或 token transform/model config，并把解析后的配置随 checkpoint metadata 保存。 |
| robot-bridge 推理、反馈、离线 | `policy/backends/openpi.py::OpenPiBackend` 从 checkpoint metadata 恢复 openpi 并暴露 metadata；`scheduler/base.py::run_iteration` 保留 `get_obs(wait_condition) → infer → execute`；`OpenPiScheduler.after_execute` 只在 execute 成功后提交反馈；offline/simulation scheduler 已有 memory 输入和评测 payload。 | 由 backend 输出 checkpoint 中的协议；在各 scheduler 的现有 `build_policy_obs`/反馈暂存点接一个字段级解析器，保留 wait-condition、takeover、reset 和成功 execute 边界。 |
| RMBench 转换、结果 | 现有 shared/state-token YAML 在 `converter_configs/`；实际 drawer/通用 key-state 转换仍在 `policy/pi05/examples/...convert_*_to_lerobot.py`；`script/eval_diagnostics.py::RMBenchResultRecorder` 已保存 config、command、diagnostics、metadata 继承与 `_result.txt`。 | 适配器先产出约定的 `series/constants/events/tail`，再复用既有 `actions`、mask 和 token 字段；将 resolved config/record 写入现有 recorder context，不另建结果格式。 |

full/serial 查证：独立 openpi 源码已有四个 RMBench 模板（含 `pi05_full_key_state`、rearrange serial、drawer full/serial），serial 模型返回 `key_state_prediction` 供 scheduler 递推；openpi 源码没有对 `RMBench/policy/pi05` 的直接引用。可是现有 checkpoint 资产、历史实验说明和实际 RMBench converter 仍位于 `RMBench/policy/pi05`；该副本与独立 openpi 的相关文件 SHA256 不同。因此独立源码具备对应模型/服务实现，历史数据转换与资产链尚未脱离 legacy tree。未验证实际资产是否均可只凭 standalone openpi 恢复，因任务禁止读取资产或运行。

phase 选择补充（代码事实）：独立 `openpi/src/openpi/models/pi0.py::_select_key_state` 在 `key_state_allowed_transitions` 缺失时，直接把 `schema[0]`/`previous_ids[:, 0]` 当 phase，只允许该字段保持或到 `min(previous+1, last)`；这等价于对第 0 字段硬编码 `ordered_step(max_advance=1)`，没有读取字段名。其余字段默认按 unknown→任意、非零后锁存，且 `(3,3,3)` 的第 2 字段还有 rearrange button 特例。`pi05_rearrange_state_token_boundary_ablation` 未提供 transition 表，因而会走该默认分支；drawer serial 模板显式提供逐字段表，才绕开默认。legacy `RMBench/policy/pi05` 的对应函数与注释也保留同一默认行为。`OpenPiBackend` 只转发 `key_state_prediction`，scheduler 将它提交为下一次输入；live dense phase 也是直接写入模型 action 值，未见额外单调筛选。故 wash-cup 若把可任意排列的 1..5 放在 token 第 0 字段且不提供显式表，会被现有默认选择错误限制。所查 tracked 运行代码中未找到 wash-cup 的独立模型/转换配置，不能据此确认其实际会传入何种表。

建议的传递路径：RMBench 数据适配器解析并语义校验一份配置 → openpi transform/model 与 checkpoint metadata → OpenPiBackend metadata → scheduler 的输入和 execute 后反馈 → RMBench recorder 的 config/lineage。不要新增 session 或通用插件总线。

阻止开工的事实（最多三项）：

1. 三库均未引用 `memory.schema.yaml`、`rearrange_full.yaml` 或 `MEMORY_CONFIG.zh-CN.md`；规格本身也明确模型、转换和 scheduler 尚未接入，需先确定 parser/semantic-validator 的唯一实现与 checkpoint 表示。
2. token 默认选择已把第 0 字段硬编码为单调 phase，并将 `(3,3,3)` 的第 2 字段硬编码为 rearrange button；只有显式 `key_state_allowed_transitions` 才会改为逐字段表。可变顺序的 wash-cup 1..5 不能依赖该默认分支。
3. 现有端到端契约仍有特殊分叉：live `OpenPiScheduler` 按单个 `field` 初始化且取 query `actions[0]`/单组 token，offline/simulation 有部分多字段或执行进度逻辑；同时生成标签、tail 与 mask 的可执行转换入口仍在 legacy `RMBench/policy/pi05`。开工前需确定 resolved protocol 怎样进入转换器并一致传到三种 scheduler。

验证结果与成果位置：仅静态读取上述入口、配置与 tests；无 smoke，未做环境调查。成果即本报告；未生成临时文件。
