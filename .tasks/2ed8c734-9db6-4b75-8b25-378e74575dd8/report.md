task_revision: 338e74f6b679f7f8380d95bda5e2c20e309669b0

完成与未完成：已完成对 EXPERIMENT_PLAN、RELATED_WORK_POSITIONING 及必要的 MEMORY_CONFIG/MEMORY_DESIGN_FRAMEWORK 的空白只读审阅。未创建环境或 worktree，未修改论文、配置或代码，也未运行实验。

workspace、各库交付 commit：任务没有关联业务仓库或 worktree；无业务交付 commit。本报告是唯一修改并将由 MAM 发布。

验证结果与成果位置：只读核对计划中的变量定义、矩阵和计数。发现以下 3 项会影响开跑或结论的问题：

1. **P2 的公共 mask 和 loss 归约没有一条可唯一执行的规范。**
   - 位置：EXPERIMENT_PLAN_20260910.zh-CN.md:75、86；MEMORY_CONFIG.zh-CN.md:72、80。
   - 原因：计划要求 phase 仅在 `(t+j+1<=L) && (t+30<=L)` 时有效，且按固定 H 归约；配置约定则只定义各目标自身的 tail 有效位，并要求 masked memory loss 按有效项归约。当前配置没有表达跨目标的公共 mask。尾部样本的状态损失权重会因实现选择而不同，B 的 per-frame 基线也无法可靠地复用于 T。
   - 最小修改：在可执行配置中加入/固定该公共逐坐标 mask，并明确 state loss 的逐字段、逐样本和 batch 标量公式（包括零有效项）；B 和 T 都引用同一条规范并写入 checkpoint metadata。

2. **“12 次 offline”漏计已列为待完成的旧 drawer 回归。**
   - 位置：EXPERIMENT_PLAN_20260910.zh-CN.md:71、76、99。
   - 原因：R 的 12 次是 wash-cup/drawer × full/serial × 3 seed 的新 20k 模型；同时计划要求“旧两模型 5ep 回归”，且明确新 drawer 训练不能替代它们。若这些回归确实执行，offline run 至少为 14，而不是标题和总计中的 12。
   - 最小修改：明确旧两模型回归是预算外接口检查，或把 offline 上限和资源表改为至少 14；两种情况下都单列其非成功率性质。

3. **Q3 的启动条件与核心预算状态相互矛盾。**
   - 位置：EXPERIMENT_PLAN_20260910.zh-CN.md:19、70、73；MEMORY_DESIGN_FRAMEWORK.zh-CN.md:214。
   - 原因：正文称 Q3 是“有明确触发条件的后续比较”，但 C 已计入所有组开展时的核心 72 次训练/96 次仿真；唯一补充是“取决于 P1/P2 能否解释交互”，没有可记录的判定时点或标准。不同执行者可以合理地立即跑 C、等待，或跳过，导致两周范围和论文证据链不同。
   - 最小修改：将 C 明确为无条件核心组，或写下在何个已固定结果节点按什么预先记录的条件入队/不入队，并说明释放的预算是否保留。

已核对但无需修改：无 memory 能力基线与“保留辅助监督、训练和推理均固定 initial”的 U 对照已清楚区分；72 次训练和 96 次仿真的表内算术正确（含 F 的 36 次中复用 6 次）；旧 30k 结果被限制为参照，预设结论和因果措辞已有适当边界。
