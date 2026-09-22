## 2026-09-22 当前清理交接要求（覆盖下文历史执行授权）

本轮只整理文件及交付状态，禁止启动训练、eval、数据生成、GPU smoke或继续旧实验计划。按当前 README 文件留存原则清理本 task 的附件：复用代码归业务库；确有必要的一次性分析附件留在本目录并提交；正式数据/checkpoint/原始评测结果留稳定产物目录不进 Git；临时脚本、调试输出、重复副本删除。保留 task.md/report.md 和既有已跟踪文件，不因为历史报告引用或旧保留要求而保留无价值副本。不清理其他 task，不迁移项目，不改 MAM 功能。

接手已有 workspace/worktree，不重复 workspace add。先核对必要代码/正式产物是否已交付到稳定位置。对 .tasks 未提交附件执行分类清理；workspace 中临时内容可以清理，正式产物不删。共享 MAM Git 操作须等待 Manager 单独授权；先报告需留附件清单及理由，Manager 批准后提交和发布简报。不自行 archive task；报告是否具备归档条件和具体阻塞。对原 stopped job 核对结果并建议收尾，不重启。交付简报应简洁记录清理数量、必要成果位置、未交付内容和阻塞，不另造审计文件体系。

---

# 六个首波N/J模型的集群C评测准备

terra/max；Manager负责设计与裁决，沿九任务覆盖优先。读MAM AGENTS/README/.local与集群C评测手册、涉及库AGENTS。旧e690任务已归档，本机worktrees已删除，但远端e690运行树/资产和全部正式结果保留，不能删除或更改HF正在使用的c3-highfreq-engineering-20260914。新任务建立自己的workspace/worktrees。

已接受六模型名单与完整来源见 /root/Documents/task-state-vla-paper/docs/analysis/wave1_six_nj_training_acceptance_20260914.json（SHA f0a993bf14529be1f8064c1b95e827a716995b99dd7d0fb5f7f32af3245a9922），训练owner task e3bc64f1-7f0d-46d2-9e54-831aa1727384 report7819a470。仅swap_blocks/battery_try/cover_blocks各N/J train0/20k，复用模型，无新训练。S待另外验收，不等S才准备这些六项。

目标：落实每模型eval0/1/2各100的18批原协议准备，H50/K30、旧continuous action RNG、demo_clean_eval、各列表100000..100099/200000..200099/300000..300099。原52批结果与HF实验分开。先做完以下实际工作，不只写计划：
1. 只读核对C现有checkpoint/资产清单，完整有效结果去重。缺失的六模型只传checkpoint及必要小型元数据，按.local规定经wuwen-nx-aic与wuwen-4090-aic优先路径，核对目标不存在/已有内容hash，不覆盖；无需传数据集、pi05_base、源码训练缓存。传输预计>30min登记MAM长job，断点续传核对源目标，不拷到HF runtime。checkpoint目录保持只读。
2. 核对三个新任务schema与现有Memory-v1 eval入口真实支持：N无memory；J swap phase/initial_empty_tray/first_origin_tray，battery phase，cover phase/red_pos/green_pos/blue_pos。必须使用保存的metadata/norm恢复，不在eval输入GT、改变标签或凭task名猜字段。冻结训练代码N5835fa04055d520e418cc1448c1bd58fa1e665cb、J34002dce65962734c59725a0f6d982ae2c438a2d；可读现有已接受原协议RMBench f401f5279c95451eb424ac98b831bab5552b2120 / bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 / OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4接口。先确认能否直接兼容新checkpoint；必要小型config/manifest在独立树准备，公共代码缺口给出证据/最小修复建议交Manager，不私自混合HF reset或修改活跃运行树。
3. 给出冻结候选runtime三库完整commit、18条实际config/manifest/命令dry-run、各自matching smoke2与fresh formal100名字/配置、资源建议。优先后续用已释放C1GPU1/2，先实测资源但本次CPU/传输准备不加载GPU，不抢C3高频卡。保留首infer90/后续30秒与既有renderer入口、视频/证据合同。新环境用现成C1 installer和共享cache，不升级依赖或自建部署框架。

交付清楚哪些checkpoint已传且验证、哪些仍传输job、接口是否有实际阻断、下一批可执行smoke命令和预计时长。Manager复核候选并冻结后接正式评测；此次不启动GPU smoke/formal，不因准备的18批叫作已运行。当前可执行工作处理完发布紧凑report并结束turn，用MAM唤醒，不轮询。

## 2026-09-14 Manager 准入：由准备推进18批正式评测
本节替代之前CPU-only限制。Manager已检查RMBench ad7f9d6 配置diff（仅六variant与原协议base）、本机18项validation及已发布传输/接口报告。冻结候选 RMBench ad7f9d6ba9acd16c31243ad4811e0dfa31cef514、bridge f9626636c4776d8eb15f9c556775cb2d12c000e5、OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。
C manifest job完成且18项CPU checks通过、六checkpoint校验通过后，允许按已生成确切manifest执行每模型eval0/1/2 matching smoke2 → formal100，共18批。不必再等一次人工确认，但任何门禁失败必须停止该lane并报告，不降阈值不改算法。开始前核实源码clean、真实加载路径与五个transformers patch内容正确；symlink路径断言的已知工具限制据实保留，真实smoke必须通过。
保持train0、H50/K30、首infer90秒后续30秒、每run单一policy server跨episode连续action RNG，不能带入HF per-episode reset。smoke的成功率不作放行阈值，正常任务失败可接受，基础设施/身份错误不可。每一完整formal必须引用自己的matching smoke，保留全部失败，禁止拼接partial。
C1 GPU1/2每卡串行一条lane，启动时实查空闲及端口；同一task/eval的N/J尽量同卡，按swap→battery→cover逐任务N/J配对轮转，先eval0覆盖三任务，再eval1/2，不因分数改变次序。C3 HF不抢占。长进程登记MAM，完成批次及时发布证据并按原门禁推进队列，Manager另行验收结果；无新训练。

## 2026-09-15 C1立即调度修正
Manager实查C1 GPU1–7均空闲；GPU0已有16.9GiB占用不使用。六N/J已完成训练及传输验收，CPU准备1873761运行4小时仍无index，不应形成全队列屏障。现将“18项全通过才开跑”改为“每个checkpoint/eval项身份、路径、冻结协议和matching smoke候选核验通过，即可该项GPU smoke；通过后自动formal100”，其他项尚未完成不阻挡。保留全部科学合同与失败门禁，不重复已验证checksum或恢复，不降低任何身份/协议检查。

授权C1 GPU1–6并行各一lane，GPU7备用；任务/模型固定卡以免冲突，先三任务N/J eval0六项，再各自eval1/2。检查现有CPU准备阻塞的子进程和日志，允许修复本任务launcher/逐项receipt，必要时结束并替换本任务卡住的CPU准备进程（先保存证据），不得影响他人进程。每项formal登记真实PID及job，完成收尾。首次infer90s/后续30s、H50/K30、seed0、原协议连续action RNG、固定评测seed不变。

六N/J共18正式批优先启动；随后安排已验收swap/cover S的6批接入（独立候选和metadata核验通过后同规则放行）。先报告真实smoke启动，再报告formal启动，不只报告静态候选。
