task_revision: 4e4abfab12e3b19311dd5f1d5b4c61247ead2133

最终合入结论：可合入本轮轻量 openpi-client 契约实现。上轮报告 c00935a745544af6a343d96bfc4634b50b0cf744 的两项 P2 发现均已独立复核关闭；本次增量未发现新的可操作问题，无剩余合入阻塞。完成指定 diff 审查、定向复核和报告；真实训练 loss、scheduler 与 checkpoint 恢复不在本次验收范围。

审查对象：基线 `f6327197459bf830c6b5d0b9ba5d643bc5e0cbd3`、availability 增量 `0f37cfc1ae42e4703b741f0f05fd1e3c58c87e89`、最终修复 `58d6f2155acc3af03017677bb3f536101e6699f4`。复用本任务 workspace `/mnt/public/xcj/Projects/workspace/d82c6b70-a8af-460e-92d1-d7e9ddc521ff` 及其中 `openpi` worktree，cherry-pick 最终修复后的审查 HEAD 为 `66f8879059db8963c6998212b566642c78fe1af0`。helper 与测试文件均与作者最终 commit 内容一致；没有 reviewer 自行修订代码。

两项发现的关闭证据（路径相对上述 openpi worktree，行号按最终 HEAD）：

- 原 P2 availability/clamp：`packages/openpi-client/src/openpi_client/memory_config.py:458` 先按原始时刻算 validity，再于 :459–467 clamp 并以同一源帧读取 availability 和类别。独立样本使用 3 维机器人、两个 memory 字段，受检 stage 放第二位且 reference key 使用 stage_labels；N=2、H=4、query=1、target offset=1。省略 availability 与显式全 true 的全部 sample 字段逐项相同，action_rows 与 serial query 都成立。末帧 GT=false 且标签为非法占位字符串时，输入回退 initial、对应 target mask/ID 为零，dense 模式对应向量和坐标权重全零；机器人 clamp、另一 memory 字段及 padding 权重不变。缺 reference key 仍报错。
- 原 P2 feedback index 上界：`memory_config.py:541` 将 H 传给内部 parser，:737–741 在 load 时要求 `0 <= index < H`。独立 H50/K30 样本接受 0/29/30/49，拒绝 -1/50/51；因此上界是预测 horizon，不会错误缩到执行 K。合法 index 经 compile 和 JSON roundtrip 保持原值，first/last_executed 声明保留。

本轮独立验证（内存脚本执行，未导入作者测试 fixture）：

- 同一套 7 组检查分别运行在旧 HEAD `8500eaadabc67263e1346000380aa323d6457349` 的模块快照和最终 HEAD：旧版 4/7 通过，失败项为 clamp_dense、clamp_query、feedback_H50_K30_bounds；最终 7/7 通过。额外四组是末帧缺 GT 的 dense/query、P2 两组公共 mask、valid_mean 坐标权重。
- P2 两组分别 target=`t+j+1` 与重复 `t+30`。N=50（0-based 末帧 L=49）、H50/K30，query=0/19/20/49 的 phase 有效行数为 49/30/0/0。分别对省略与全 true availability 比较全部 sample 字段；两组 target mask、机器人目标和坐标权重一致，非零类别时刻也单独核对。公共 mask 仍按原始候选时刻判断，clamp 不会重新启用越界 phase 监督。
- valid_mean 定向样本 N=4、H=4、query=0，末帧缺 GT：字段 mask=`[1,1,0,0]`，每个类别坐标权重=`[2,2,0,0]`，等于 mask×H/count；机器人和另一字段保持 1。非默认 lambda=0.25 仍由 spec 单独提供，helper 不重复乘 lambda。
- 公开构造器及 load/make_training_sample/compile_model_spec/validate_model_dimensions/to_dict 签名与修复前一致。完整 diff 仅改 helper 与其定向测试（core +9/-5、tests +68/-4）；负 target index 已由原有 parser 拒绝，新增 clamp 路径无负索引读取。未改 dependencies、uv.lock、训练或 scheduler 代码。
- 最终 HEAD 执行 `.venv/bin/python -B -m pytest -q -p no:cacheprovider packages/openpi-client/src/openpi_client/memory_config_test.py`：18 passed；该结果由本 reviewer 实际运行。Ruff check/format（--no-cache）与 `git diff --check HEAD^ HEAD` 通过。无关测试及 lock 检查未重复；上轮已验证 lock 同步且本增量未改依赖。

验收范围保留：训练接入须将 helper 权重与 lambda 在逐坐标 loss 上合成一次，并成对 pad action/weight；scheduler 仍须以真实执行进度实现 last_executed=k-1、区分 accepted/completed；checkpoint 自包含恢复由对应任务验收。availability 检查实际目标源帧，不计算 P2 两候选时刻标注可用性的交集；首批 P2 全标注 sim 的范围不变。以上是既有跨任务契约，不是本轮剩余代码发现。

清理：独立脚本经 stdin 执行，旧模块快照只存在内存；使用 -B、关闭 pytest/Ruff cache，确认 worktree 干净且没有新增临时样本、脚本或缓存。CPU 验证禁用 GPU 可见性，独立脚本确认未导入 JAX/torch；未重建环境、未派 agent。worktree 保留待 Manager 归档。
