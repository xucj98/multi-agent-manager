task_revision: 98dd4d0ec1848b1fea3ca0f4b475e8851222959d

完成本轮独立 review 两项修复，待 Manager 安排原 reviewer 复核。openpi 交付 commit：`58d6f2155acc3af03017677bb3f536101e6699f4`（`fix: preserve memory tail availability and bound feedback rows`），直接父提交为 `0f37cfc1ae42e4703b741f0f05fd1e3c58c87e89`。worktree：`/mnt/public/xcj/Projects/workspace/f252006a-8676-4d10-b6a1-1a791d91c6a6/openpi`，保留且干净。

针对 d82 报告 `c00935a745544af6a343d96bfc4634b50b0cf744`：availability 按 tail=clamp 后实际读取的源帧检查，全 true 与省略 availability 的 target/mask/dense/weight 相同；末帧 availability=false 时，映射到末帧的 memory 目标仍为零 ID、零 dense 和零 loss，robot 与其他字段保留。公共 validity 继续按原始候选时刻判断，缺 series key 仍报错。反馈 row.kind=index 在 load 阶段检查 `0 <= value < action.horizon`，H50/index49 合法、index50 拒绝。公开 API 签名不变。

回归先在旧实现复现 4 个失败（dense/query 的 clamp，以及 H4/H50 的 index 上界），修复后全套定向测试 18 passed。覆盖全 true 等价、末帧 false、缺 key、P2 部分/全部无效的公共 mask、机器人及其他字段权重保留、反馈 0/H-1 合法与负数/H/H+1 拒绝。Ruff check、Ruff format check、git diff --check 均通过；未运行 GPU smoke 或正式训练。真实训练 loss、scheduler 和 checkpoint 接入由对应 owner 验证，本报告不代替端到端验收。

本轮仅改 client helper 与定向测试：core +9/-5 行，tests +68/-4 行；当前 core 990 行、tests 398 行。此前独立 lock 修复 `0dc120c`、精简 `f632719`、availability `0f37cfc` 均在提交链内，未再修改根 lock、src、scripts 或其他库。

论文 artifacts 已由 Manager 应用并校验；按最新授权清理本 workspace 的 `paper-artifacts/` 四个文件及目录，另清理自有临时 `/tmp/memory.schema.v1.yaml`。未改共享论文库。代码 worktree 保留待复核和归档。
