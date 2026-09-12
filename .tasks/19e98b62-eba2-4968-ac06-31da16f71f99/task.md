# Wash-cup R组独立训练seed重复

## 目的
执行论文既定R组：wash-cup full与serial分别补seed1/2，连同已有seed0形成三个独立训练重复，检验模型稳定性。只是既有已验收配置的seed重复，不改memory/schema/数据/训练实现，不以预期成绩选模型。
读/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md的R组，以及MAM已发布ad6bb77e-3892-4730-ae1a-7d9cd99a5728报告与稳定training_acceptance。已有seed0实际代码056bcc887637cc6eda565a8ad7d45c88021d4bcd，两配置pi05_x1pro_wash_cup_s2m_full_current_feedback和pi05_x1pro_wash_cup_s2m_serial_lag30。wash v3共172合格episode、S2M、phase当前子任务、15Hz、14DoF、H50/K30，全部沿用；不要误用RMBench的demo_clean_state数据要求。

## 执行与资源
独立OpenPI worktree固定056bcc887637cc6eda565a8ad7d45c88021d4bcd，读AGENTS，不改训练源码/环境合同。核对真实baseline metadata、resolved config和当前data/norm资源；除seed与独立输出/日志路径外必须等价。已有50step保存恢复验收可复用，无需为seed-only重复再跑smoke或CPU全套。若发现不等价或新代码缺口，报告再实施，不能偷偷改算法。
现在本机GPU4/5已由7ae no-memory训练释放且Manager确认空闲，分配full seed1→GPU4、serial seed1→GPU5；核对无外部占用后直接启动。seed2 full/serial排本机GPU2/3，必须等待7ae原serial训练自然结束并验收释放后再启动，不能停止/抢占它们。该接续交接由Manager通知，不做分钟轮询。
全部单卡bs32、20k，仅最终20000 BF16 model-only和必要资产metadata，不存optimizer。输出统一openpi/checkpoints/<config>/memory20k_19e98b62_wash_<full或serial>_s<seed>/20000，每次独立不覆盖已有结果。日志和运行身份留痕。先启动可用两条，不等后两张卡。

## 验收和台账
登记mam job，确认真实PID/设备/初始finite loss后报告。完成时核对最终metadata/全部参数shape BF16 finite、checkpoint-only恢复、退出和资源回收，归档job。用独立RMBench文档worktree新增本组说明或更新已有wash训练表：研究目的、预期结论、config/seed/commit、checkpoint链接、实际运行/完成状态；与e690的EXPERIMENT_LEDGER避免并发写冲突，优先新增README_wash_seed_repeats.zh-CN.md供Manager合并导航。
交付模型给Manager安排同一固定5episode offline回放；不得对wash运行RMBench仿真100，不操作真实机器人或内网Policy Manager，不自行部署。保持原训练数据筛选与offline可比协议。
训练运行时mam wait实际await完成事件，无变化不汇报/不写等待窗口报告。未结束的训练由本执行者负责，全部交付后结束turn，临时文件自行清理，保留worktree供Manager归档。
