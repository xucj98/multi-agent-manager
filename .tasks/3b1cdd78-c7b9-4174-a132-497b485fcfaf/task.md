# 清理已结束任务的旧 worktree、workspace 与 cuRobo 源码压缩包

用户授权清理 /mnt/public/xcj/Projects/workspace 下旧workspace、/root/Projects（实际同 /mnt/public/xcj/Projects）残留 worktree，以及 curobo-0.7.8.tar.gz。当前没有训练评测；manager复核进程。你的任务先审计，再在正式结果搬迁依赖解除后清理。另一执行者负责所有 eval_result 迁移与清理，你不得并发修改其文件。

范围：旧workspace为 bridge-mem0-remaining-execution-20260908、bridge-remaining-evals-20260908、bridge-runtime-integration-20260908、mem0-official-eval-turing-01a07a23、mem0-single-training-final-eval-prep-20260908、workspace-handoff-audit-20260908-0845；Projects一级旧树 RMBench-sync-upstream-mem0 与 mem0-swap-blocks-single-20260907。当前两个UUID任务workspace由manager验收后MAM归档，你不删除。保留 RMBench/openpi/opendm/robot-bridge/multi-agent-manager 主目录、主checkout未提交用户文件、模型和数据。

先读相关库AGENTS.md。讨论/调查及本任务文件清理不需新代码环境；确需改受版本管理代码才 mam workspace add。禁止新GPU作业。

审计并短报：
- git worktree list、各旧tree的tracked diff和untracked（区分真实修改/临时文件）、分支tip是否由主开发分支或其他持久引用保存。唯一有价值修改不得丢；报告后由manager裁决，必要时小范围保全patch/提交。不要为归档而合并不需要的代码，不切共享主checkout。
- 识别主repo软链接和editable/.venv引用是否指向旧树。尤其 RMBench assets/data/lerobot dataset、policy/Mem-0/checkpoints（自训模型）、其他训练/统计数据。必要真实模型/数据应在主repo持久路径落地并修正当前软链；同文件系统优先rename避免复制大模型。历史metadata里的命令文字不重写。
- curobo tar检查是否仅是可删除安装源包、现有cuRobo source/wheel/环境是否已独立可用，记录大小；不要删除uv缓存/共享wheel/cuRobo编译源或既有环境。
- 识别每个worktree的eval_result/logs仍被保留正式结果引用的路径，先交manager协调结果迁移，获manager依赖解除通知前不删除相应旧树。可以先删除明确无依赖的空目录/源码压缩包（确认后）。

实施：使用git worktree remove删除已审计且无依赖旧树并清理对应临时分支（仅明确这些tree创建的分支；保持xcj-dev/main及正在使用分支）。detach唯一commit若实验metadata引用且无持久引用，留最小git tag保全并记录，勿堆积worktree。避免follow symlink删除共享目标。仅移除具体已审计路径，勿扫除未知目录。不要扩大到/tmp或全系统垃圾清理。

交付：发布report.md，含task_revision、workspace、删除清单/空间（区分逻辑与物理/hardlink共享）、保留成果路径、未处理项及原因、最终worktree列表、链接/环境最小只读核验。自用临时文件清理。及时向manager报告阻碍，不长时间自行扩展调查。

Manager 现场裁决（2026-09-09）：bridge-runtime-integration-20260908/openpi 的7个modified及3个untracked源码/测试逐文件与主openpi一致；RMBench-mem0的4个modified源码与主RMBench一致；两个untracked bridge_worker.py/test_bridge_worker.py已经集成于主RMBench commit 7af489d，主版本仅增加gitlink provenance处理及对应测试。上述工作树改动已被主库成果覆盖，可随旧树删除，无需重新提交或复制源码。logs链接目标须按结果依赖检查。保持主库用户未提交文件不动。

Manager 对交接审计目录裁决：其中 dirty-worktree-patch-archives 的小型历史源码补丁、未跟踪源码副本及解释其base commit/archive ref的现有索引，压缩保留到 MAM gitignored 的 .local/archives/<本任务UUID>/legacy-source-patches.tar.gz；验证可读并保留hash、来源映射在report。其余过时清理日志/清单不继续保留。原 workspace-handoff-audit-20260908-0845 可删除，无需为了这几MB逐一做跨库历史源码考古，也不需把这些补丁重新合并进业务库。
