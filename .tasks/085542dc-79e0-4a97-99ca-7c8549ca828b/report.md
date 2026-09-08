task_revision: 6ba1885432181ba73657ed18b1bee48d6a79ef9e
完成与未完成：已完成固定草案及第二轮的架构定向复核；full-state 时序训练取证按最新要求留给 Manager。未修改业务代码、未创建环境或 worktree。
workspace、各库交付 commit：无业务代码交付。取证基线为 robot-bridge `0095a3f`、OpenPI `71c80db`；RMBench 当前只读证据为 `e0bcc0c02d957d51bb1b073410447fc3213c7126`。
验证结果与成果位置：第一轮以 `git show 2196483` 读取草案；第二轮以 `git show dfc487d` 及其 diff 定点对照上述源码、配置和既有测试路径。full-state target 的时序训练证据由 Manager 核对，本审阅未重复调查。本任务规定不运行训练、GPU 或代码测试。本文件为成果。

# 审阅结论

整体职责划分可实施：语义 schema 放在 policy 一侧，原始标注映射留给 converter，表示编解码留给 OpenPI adapter，scheduler 保存上下文并通过已有控制面服务 UI。`get_obs(wait_condition)`、action chunk、UDP 遥操作、takeover、薄 server 和无 session 的约束都不需要改变。

实施前应先处理下面三个阻断项。其余两项是可删减的实现约束；不建议再增加插件、事件总线或跨 server 注册表。

## 阻断实现

### 1. §2/§4/§5：三份配置尚未形成不可变的单向依赖

当前 drawer 已出现同一事实的多处来源：RMBench `converter_configs/memory_schemas/drawer_sorting_x1pro.yaml` 同时有字段、初值、标注和 transition；`converter_configs/shared_memory/drawer_sorting_x1pro.yaml` 还有 dense dim、token stride、loss；OpenPI `src/openpi/training/config.py` 的 `_DRAWER_S2M_MEMORY_SCHEMA` 又有 labels、transition、dense encoding。robot-bridge `policy/backends/openpi.py` 的 `_merge_memory_fields()` 还按字段名把 dataset 与 train metadata 合并。

失败场景：converter 用旧 labels/顺序生成数据，之后 schema 或表示配置更新；训练和 bridge 仍能按名称拼接，却把旧 id 或 dense slice 当成新语义，错误不会在启动时暴露。

最小修正：明确且只允许如下方向，生成物不能反向成为配置来源。

```text
canonical schema YAML ─┬─> converter config ─> dataset schema snapshot + sha256
                       └─> representation config ─> adapter/layout
dataset snapshot + resolved representation ────────> checkpoint snapshots
checkpoint snapshots ──────────────────────────────> bridge metadata / UI / replay
```

schema 只保留字段语义、值域/单位/坐标约定和 initial；converter 保留原始路径、标注映射及数据选择；representation 保留 encoding、loss、normalization、layout 和反馈描述。训练必须校验 dataset schema 的规范化内容/hash 与 representation 引用一致，并把原字节复制进 checkpoint；snapshot 是产物，不是第四份可编辑配置。这样可删除 bridge 中“按名称合并两份 schema”的新路径，而非把它泛化。

### 2. §5：checkpoint “自包含”与现有加载机制不兼容

OpenPI `training/checkpoint_metadata.py` 虽保存 `train_config.yaml` 和 `datasets.json`，但 safe-YAML 恢复仍以 `_config.get_config(name)` 取得当前代码模板。robot-bridge `OpenPiBackend` 随后依赖该 config 创建 policy，并对旧 checkpoint 额外读取 `metadata/rmbench_data_meta/key_state_config.yaml`。因此仅把 schema、解析后的表示和 norm stats 写入 checkpoint，尚不能保证配置重命名、旧 RMBench snapshot 缺失时可以部署。

失败场景：历史 drawer checkpoint 的注册 config 被删除或 schema 从 RMBench 迁走；loader 在模型权重加载前就因找不到模板/旧 snapshot 失败，或重新拼出与训练时不同的 layout。

最小修正：新 checkpoint 增加一个固定的、直接供 inference 读取的 runtime metadata 文件，包含 schema 原文/hash、已解析的两种已知 representation 参数、adapter 名称、状态/动作维度和 checkpoint 内 norm asset 的定位。它不需要通用版本或插件体系；adapter 名只限本轮的 full-state 与 serial-soft。`OpenPiBackend` 调 OpenPI loader 直接读取该文件，不再在 bridge 合并 schema/layout。旧格式由 OpenPI 中一次性迁移器读取旧 train config 加已有 snapshot，写出同一新文件并保留来源；scheduler/controller 不根据目录名分支。

### 3. §9：新增字段的修改范围在旧路径迁完前被低估

“换 drawer 两字段只改 schema/映射”是迁移完成后的性质，当前并不成立。已知必须迁出的依赖包括：

- RMBench `policy/pi05/examples/x2robot/convert_drawer_sorting_to_lerobot.py` 固定 `MEMORY_FIELD_NAMES`、两个 index、`(3, 3)`、二维 token feature 和 implicit-zero one-hot，并把它们写入 `phase_layout.json`。
- OpenPI `training/config.py` 固定 `_DRAWER_S2M_MEMORY_SCHEMA`、`memory_dim`、`memory_field_dims`、`key_state_num_values`、initial ids 与 transition；`policies/arx_policy.py` 是可参数化的，但目前由这些常量驱动。
- robot-bridge `policy/backends/openpi.py` 解释 RMBench snapshot、dense layout；`scheduler/openpi.py` 仍取单个 `memory.field` 并做类别 UI 解码；`scheduler/openpi_offline.py` 和 `robot/controllers/x2robot_offline.py` 仍假定 drawer 的两个字段、6 维 dense 输出、整数 id 和原始 annotation。

失败场景：加入连续位置或第三个仿真字段后，converter 会写错 feature shape，offline controller 会拒绝字段名或把连续预测按 one-hot/整数评估。

最小修正：第一提交组先将上述 converter 的语义输出收敛成逐字段物理值和 validity，并迁入 OpenPI；旧 drawer reader 仅保留为 legacy 输入 adapter。第二组让 OpenPI adapter 独占 encoding、dense slicing、token id 和 decode，删除 bridge backend/scheduler 对 `dense_layout`、labels 的解释。第三组让 evaluator 读取转换数据的语义真值，按 schema 类型做分类准确率或连续物理单位误差。§9 应改为：新语义字段改 schema、converter mapping、representation/adapter/head 和相应 contract test；只改 encoding 时改 representation/adapter/head 与 checkpoint contract；generic scheduler/UI 不按字段名改。对应回归位置至少覆盖 OpenPI `config_test.py`、`arx_policy_test.py`，以及 bridge 的 `test_openpi_metadata.py`、`test_openpi_feedback.py`、`test_openpi.py`、`test_drawer_offline.py`。

## 可简化

### 4. §7/§8：删除 `MemoryContext` 的可插拔接口承诺，保留具体共享状态对象

草案称组件只有 `reset/prepare/stage/commit` 四个操作，但 §8 又要求 `set_memory`、`lock_memory`、状态展示和 schema 校验，公共责任没有落点。现有 `scheduler/openpi.py` 已把 reset、pending feedback、context epoch、手工覆盖和 control action 放在一个 scheduler；real/offline 两个 scheduler 各复制了一部分。

最小修正：保留一个仅供 OpenPI scheduler 家族复用的具体 `MemoryContext`，不要给它定义可替换/发现的接口。它持有原始 context、pending、semantic overrides/locks 和 epoch；scheduler 继续暴露已有 `set_memory`/`lock_memory`/status 控制动作并委托该对象。OpenPI adapter 固定提供“物理 observation + raw context + overrides → model input”和“model output → physical action + raw feedback + UI values”；只有 adapter 解释 layout，scheduler 只提交或丢弃 raw feedback。现有 `PolicyBackend.infer(dict)` 与 policy server 已能透传扩展字段，两个 server 均无需新插件点。

### 5. §3：保留 `memory-spec`，但将它缩为纯数据契约包

独立轻量包是值得的：converter、OpenPI adapter 和不加载 JAX 的 bridge/UI 都要用同一套 categorical/vector/unknown 校验；放进 RMBench 或 bridge 会倒置依赖，塞入已有 `openpi-client` 又会把 transport client 与任务语义混在一起。OpenPI `pyproject.toml` 的 workspace 已允许 `packages/*`，因此这是现有结构中的最小共享边界。

其范围应只含 YAML load、schema/value validation、规范化 dump/hash 和小型值类型；不含 encoding、transition 实验约束、converter、RPC 或 scheduler 行为。当前 OpenPI 与 bridge 均声明 Python 3.11，草案无消费者依据的“3.10+”可删除。canonical schema 文件放在 OpenPI `configs/memory/`；真机与仿真各自的原始提取只在 converter config 中引用它。这样 drawer 当前 schema 中的 annotation 映射迁到 converter，dense/token/loss 迁到 representation，schema 的真机/仿真共用位置保持唯一。

## 需要用户实验语义选择

用户最新澄清已固定 wash-cup episode 筛选：必须有子任务标注文件、没有 label 6，且标签 1–5 各恰好出现一次；步骤顺序不限，不再作为待确认项。full-state target 是 chunk-level 还是 frame-level 由 Manager 的实际训练监督取证确定；该结果会决定 §6 反馈表的 full-state 条目。连续字段的 `null` 继续表示未知，必须由 representation 显式编码，不能以物理零点替代。

## 压缩记录

- full-state 的连续反馈应原样保存在 context；类别 argmax 只能用于 legacy 分类 UI/评估显示。当前 bridge 的类别解码不能复用于连续字段的 commit 路径。
- `x2robot_offline` 目前会从原始 drawer annotation 计算真值；迁移后新任务优先读转换结果，保留它仅作 drawer 历史验收入口，符合 §8。
- takeover 的清队列与 context epoch 已有落点；本审阅不重述执行时序。只需使新的具体 context 对象沿用这些现有失效信号。

## 第二轮定向复核（robot-bridge `dfc487d`）

结论：schema、representation、checkpoint 与组件职责的修订通过，未发现新增架构阻断。实施前仍有两项任务要求的文档收口：§4 的 wash-cup 筛选文字须改为最新的固定规则；§6 的 full-state 反馈时序表须待 Manager 以实际训练监督核对 target 粒度后修订。`accepted-first` 不是默认正确算法。

- §2 将依赖固定为 schema → converter/representation → dataset snapshot → checkpoint，并以规范化内容/hash 拒绝按名称拼接；新增的 `memory_known` 是数据行的语义状态，不是第四份配置。schema 仍未吸收 annotation、encoding、loss 或 layout。
- §5 的 `metadata/inference_config.yaml` 由训练配置导出，直接提供模型/transform/layout 构造信息和 checkpoint 内资源引用；它不再以当前训练配置注册名或数据集路径还原。旧格式只在 OpenPI loader 迁移，符合 bridge 不猜目录的边界。
- §4 当前仍写有“无 label 6、存在标注”的候选计数以及据此固定五集的规则；这与最新任务覆盖要求不一致。实施前应替换为：存在子任务标注文件、无 label 6、标签 1–5 各恰好一次，顺序不限；候选数和五集 manifest 均由 Manager 的数据核对重新生成。此处是文档/数据选择收口，不要求另行建立训练时序取证。
- §6 明确区分表示事实（监督时点、history lag、cadence）和 scheduler run config 的取样/提交策略；`MemoryContext` 的 pending query、epoch、policy-index→执行位置映射仅是运行状态，不会写回 checkpoint。Manager 的训练证据确定 full-state 输出索引与 target 的关系后，才可在既有 scheduler YAML `params` 固化相应策略，并在启动时按 checkpoint cadence 校验；无需新增 server RPC 或通用框架。
- 该归属与现有实现相容：`scripts/run_scheduler.py` 已把 run config 传给各 scheduler，`policy/server.py` 的 `infer(dict)` 可透传扩展 memory 字段；`scheduler/openpi_simulation.py` 的 `logical_step` 路径和 `SchedulerBase.after_execute()` 分别证明 executed 与 accepted 两类机制可实现，但不构成选择 `accepted-first` 的训练正确性证据。连续 full-state 的 raw feedback 仍由 adapter/context 保存，类别投影只可用于分类显示或旧验收。
- §7 对具体共享 `MemoryContext` 补足状态读取和 set/lock，不再承诺可插拔接口；§8 将普通 replay 与 oracle 分开，避免 evaluator 真值进入普通模型输入。wash-cup 的筛选条件已按最新任务澄清固定。
