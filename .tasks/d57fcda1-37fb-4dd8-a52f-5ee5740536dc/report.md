task_revision: ac38727a995596ca1ab2e6c491a5f42c5a1ca128

完成与未完成：已完成只读审阅。已核对配置约定、JSON Schema、五个完整样例和链接的 shared 历史审计；未修改方案、代码、环境或快照。未完成项：无。

workspace、各库交付 commit：审阅快照为 `/mnt/public/xcj/Projects/workspace/d57fcda1-37fb-4dd8-a52f-5ee5740536dc/review`。本任务没有代码 worktree 或交付 commit。

SHA256SUMS：`review/SHA256SUMS` 的 10 个条目均以 `sha256sum -c` 验证通过。

审阅结论：无阻塞意见。五个现有实例在结构和已列出的关键跨字段语义上自洽，历史映射也与 `experiments/history_audit_20260909/shared_memory_timing.zh-CN.md` 相符：full 的 H=50、K=30 在第 29 个已执行行回灌 `g_hat(t+30)`；serial 在 query 时选择/缓存当前 token；random-lag 对同一训练样本共享 L。Swap T 的首帧 null、常量目标和首 chunk 第 29 行锁存也一致。

非阻塞意见（均不由当前五例触发）：

1. 输入读取没有定义 `series` 的上界越界。第 3 节只规定 `s<0` 使用 initial，而 `action.tail` 只规定目标；`Time.offset` 可为任意整数。复现：将 `rearrange_full.yaml` 的 `protocol.input.train.phase.time.offset` 改为 1，长度 T=10 的 episode 在 query t=9 得到 s=10，结构校验仍通过，但可合理地报错、丢样本、clamp 或套用 dataset tail。最小修复是在第 3/7 节指定 input-series 的 `s>=T` 一律报错，或新增显式 `input.tail` 并将其列入语义校验。

2. `action_rows` 上的 `conditional` decoder 未指定 `selected` 引用哪一行。第 5 节只规定 selected 必须是本 query 已解码字段；当被引用字段有 H 个 row 输出时没有 row 选择器。复现：在 `rearrange_full.yaml` 保持 `target.layout: action_rows`，把 `button_press_status` decoder 换为引用已在前面的 `selected.phase` 的 `conditional`；schema 通过，实施者可按同一 j 行、首行或整个向量理解。最小修复是规定 action_rows 按 row 独立、`selected.<field>` 取同一 j，且 `previous` 始终为 query 开始快照；或在有 row 选择器前禁止这种组合。

3. `scalar_id` 的类别数值映射未写死。第 4 节允许 categorical 的 `scalar_id`，第 5 节的 `nearest_category` 又按“类别 ID”反归一化，但 domain 仅提供有序字符串。复现：`values: [A, B, C]`、`encoding: scalar_id`、`decoder: nearest_category` 和未归一化输出 1，在 0-based 映射中选择 B，在 1-based 映射中选择 A；该变体结构校验通过。最小修复是明确 `values[i] -> ID i`（0-based）及其进入/退出 model_config 归一化的顺序，或为每个类别显式给 ID。

验证结果与成果位置：使用 `/mnt/public/xcj/Projects/RMBench/.venv/bin/python` 的 yaml/jsonschema 对五份样例做 Draft 7 校验，均通过；另按第 7 节对字段集合、lag、布局、表示、decoder、反馈和 K≤H 做只读语义扫查，均通过。时间展开复核：full 在 t=100 的 phase 为 101..150、side 为 100..149，K=30 反馈行 29 对应 phase(130)；fixed serial 为输入 80、target 100；random 例 L=37 时所有输入为 63、target 100；Swap T 在 t=0 为 null 输入、t=1 为 constant 输入、所有目标为 episode_start 的 0、K=30 的 last_executed 为 29。
