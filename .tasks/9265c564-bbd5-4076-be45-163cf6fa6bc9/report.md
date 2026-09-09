task_revision: 8da86ef2b2675840491c98fd5e7ae6a847237347

完成：已完成 Rearrange 的按钮字段、state token 与动作边界历史实现审计；未启动训练、评测或真机任务，原始 `eval_result`、checkpoint 与数据均保持只读。

workspace: `/mnt/public/xcj/Projects/workspace/9265c564-bbd5-4076-be45-163cf6fa6bc9/RMBench`

commits:
- RMBench: `9faa19d4fa03d66619cc09ce70b2803c35b499e1` (`docs: 整理 Rearrange 状态 token 历史审计`)

成果：
- `experiments/history_audit_20260909/rearrange_tokens.zh-CN.md`
- `experiments/history_audit_20260909/rearrange_token_designs.csv`
- `experiments/history_audit_20260909/rearrange_failure_evidence.csv`

关键发现：converter/训练的共享实现 `f40d3d02244fca2551e4c3fb97ea76647b3f3841` 和无按钮训练实现 `a3e91e87d1d96f159b7289cd87a0401372d616d0` 均为 clean。state 输入滞后固定 20 帧、H=50；Hard 是训练目标在 guard offset 后的 repeat-last holding，非 stop head、mask、可变长度或运行时重查询。serial 训练用 GT 当前 state token、推理用 masked argmax；部署在执行 K 个动作前缓存预测 state，故下一次查询时实际 memory 年龄为 K。按钮有无是 3-field 与 2-field 参数树的独立重训练，K=30 为 145/200 对 78/200，K=50 为 92/200 对 75/200，不能解释为同 checkpoint 输入开关。

证据边界/缺口：原始数据 metadata 记载 clean 的 `a4d318ca456d75de4e2c85d0ed80b4160e2e55a3`，但本地缺少该 Git object；这仅构成 source-data collection code 缺口，不影响已由其余 clean 历史 commit 和产物支持的实现事实。eval metadata 未记录 `git_status`，因此其 clean/dirty 状态为 unknown；未发现与本机制相关的 dirty metadata 或缺失 patch。诊断只定义了有效 press 与浅下压阈值，已按仍下降、抬升/回程失败、未按直接离开均未单列，计数按 unknown 报告。

验证：提交前 `git diff --cached --check` 通过；两份 CSV 的引用字段数检查通过；提交后 `git show --stat` 与 `git status --short` 核对通过，工作树干净。
