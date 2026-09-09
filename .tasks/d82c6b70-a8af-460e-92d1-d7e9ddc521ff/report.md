task_revision: f55914e7aebcd74a1cebbbffc879b11f2df2430e

审查对象：`openpi` 的 `f6327197459bf830c6b5d0b9ba5d643bc5e0cbd3` 加增量 `0f37cfc1ae42e4703b741f0f05fd1e3c58c87e89`；本任务独立 worktree 为 `/mnt/public/xcj/Projects/workspace/d82c6b70-a8af-460e-92d1-d7e9ddc521ff/openpi`，cherry-pick 后本地审查 HEAD 为 `8500eaadabc67263e1346000380aa323d6457349`。

验收结论：availability 增量的核心缺 GT 语义可用于首批全标注 sim P2；但通用 availability/反馈配置契约仍有两个 P2 问题，不能宣称完整训练、scheduler 或 checkpoint 路径已验收。无 P1 发现。

发现：

- P2 — 显式“全可用”会改变 `tail=clamp` 的已有字段标签语义。`packages/openpi-client/src/openpi_client/memory_config.py:458` 在 availability 映射存在时额外要求原始 target index 在 `[0, L)`，而取 target 值仍在 `:465` 用 `min(index, L - 1)` clamp。最小复现：`L=2`、`H=4`、phase target=`t+j+1`、`tail=clamp`、query=1；省略 availability 时 target mask 为 `[1,1,1,1]`、IDs 为最后帧 `[1,1,1,1]`，传入 `{"phase": [true, true]}` 后却变为全零 mask/ID。全 true 应与缺省“全部有 GT”一致，或需明确 availability 会改写 tail policy；否则带部分缺标注的 adapter 会无意改变尾部 full/aux 监督。首批带公共 `all_in_bounds` 的 sim P2 不受此例影响。
- P2 — feedback 的数值 row 未按 action horizon 做范围校验。`memory_config.py:735-743` 只要求 `index >= 0`；H=50/K=30 配置的 `row={kind:index,value:50}` 可成功 load 并原样进入 `MemoryModelSpec.feedback`，尽管合法 0-based dense 行只到 49。`last_executed` 的实际 k-1 语义及事件能力应由 scheduler 验证，但这种静态越界值应在 parser 拒绝，或提供明确、已测试的启动期校验；否则容易造成 row/off-by-one 反馈错误。

独立核验：

- 最终 HEAD 上定向 pytest：12 passed；Ruff check/format、`uv lock --check --offline`、`git diff --check` 均通过。未使用 GPU。
- 自建样本覆盖 availability 的 action_rows 与 serial query：缺 GT 输入为 initial，字段 target mask、dense 与权重为零，drawer/robot 仍受监督；有效 domain 值 `unknown` 仍被监督；缺 series、未知 availability key 和错误长度均拒绝。
- 自建 H50/K30 边界样本：query=19/L=50 有 30 个有效 phase 行，query=20 全无效；无效 dense/权重为零而机器人 clamp 仍为 1。共享 lag、initial 不能掩盖缺 reference/event、嵌套 YAML 重复键和未知字段也已独立验证。
- `loss.weight=0.25` 时 helper 的 memory coordinate weight 为 `1.0`，lambda 单独位于 `MemoryModelSpec.loss_weight`；这符合当前 helper 文档“downstream apply once”的分工，但本 commit 没有训练 consumer，不能据此声称最终逐坐标 `mask*lambda` 或真实 loss 已通过。类似地，未声明维度时 sample 宽度可为 6、model spec padded_dim 为 12，训练接入须成对 pad action 与 weight 后再验证。
- `to_dict()` JSON roundtrip 保持 resolved 配置、移除 source-only `record`；固定 commit 没有训练/运行时 checkpoint 接入，因此“只给 checkpoint 路径恢复”仍是后续任务的验证项。availability 仅检查目标自身的标注，不计算 P2 两候选时刻的 availability 交集；这与首批 P2 仅使用完整 sim 标签的范围一致。

已清理审查期间产生的临时脚本/缓存；未修改交付代码或共享环境。
