# 归并并清理三组正式评测结果（5+9+1 run）

目标：用户授权将 robot-bridge/eval_result 中完成的正式结果迁入 RMBench/eval_result，并删除前者。RMBench/eval_result 仅保留三组：重构前官方 m1mix 5 run、重构后统一 runtime 9 run、单任务训练 Mem-0 最终模型 1 run。按 <exp-group>/<run> 组织。

先读 RMBench 与 robot-bridge 的 AGENTS.md、RMBench/docs/guidelines/experiments.md 和 rmbench.md。根目录 /mnt/public/xcj/Projects；/root/Projects 是其别名。本机与 wuwen-1 共享该目录。无 GPU 操作，无需重新评测。实现/文档修改使用 mam workspace add 创建 RMBench worktree（base xcj-dev）；实际共享结果按本任务授权原地归并。

来源：
- RMBench/eval_result/mem0_official_m1mix_sdpa_reproduction 为5 run 组，预期 observe6、rearrange84、putback100、swapblocks80、swapT8，各100次。读取真实结果核验。
- RMBench/eval_result/unified_runtime_reproduction_20260908 已有部分结果，其余在 robot-bridge/eval_result 的 formal 目录；9 profile 为 pi05_rearrange_full/serial、dm05_swap_blocks_history/nohistory、mem0_put_back_block/observe_and_pickup/rearrange_blocks/swap_T/swap_blocks。pi05 serial 采用 f2，DM05 history 采用 exact-r5，putback 采用 template 最终运行，须以真实结果而非命名确认。
- RMBench/eval_result/mem0_swap_blocks_single_20260907 是到早期训练 worktree 的软链接，定位 step30000 最终100次；规范组名建议 mem0_swap_blocks_single_final_eval_20260908，与实验说明一致。
- 对应三个 RMBench/experiments 下 README 含来源及部分过时状态，需更新实际结果/新路径。重构结果无需重复加入主表。

执行与验收：
1. 优先用真实 episodes/summary/result 确认每个最终 run 完成100次、ID无重复，并报告15 run结果；若未完成不得伪称完成或删除唯一未完成结果，立即告知 manager。
2. 检查活动写入及目录/文件软链接、metadata/log依赖。移动前记录正式结果文件路径/大小/hash，用同文件系统 rename 或必要复制落地，保留视频、diagnostics、command.txt/config、checkpoint_metadata 全链路；历史原始 metadata 不改写。相同来源去重，不覆盖不同内容。保留结果不依赖待清理 worktree 或其他待删除 eval 目录；外部模型/数据指向交由清理 agent 处理，及时把依赖名单交 manager。
3. 三组必要正式文件确认安全后清理其他旧 eval/smoke/重复结果（用户已授权）；旧参考pi05/DM05结果如被保留组的 lineage 链接引用，先落地相应 metadata。不要删除链接目标处的模型/数据，不处理 workspace/worktree 本身。
4. 保留三个组各自所需的共享 provenance，可放组内明确非run的 metadata目录，不丢证据；最终恰好5+9+1个正式run。
5. 用小范围 manifest 对比证明完整性，检查保留结果中无新断链。更新三组实验README并提交交付commit，不切换共享checkout。提交的记录包含旧→新映射、最终成功率及metadata完整性；临时清单放任务workspace，结论进入report。
6. 不占GPU、不大规模扫描数据/模型、不过度反复验证。已定位旧监控由manager处理。对删除有疑点的独有成果先报出，不自行销毁。

交付：发布 report.md（task_revision、workspace/commit、三组绝对路径、15 run结果、文件完整性验证、删除项、遗留项）。清理自用临时文件，保留代码worktree等manager归档。业务主目录 robot-bridge 有用户未跟踪设计文档，勿触碰。

Manager 文档验收反馈（2026-09-09）：文件迁移已独立复核全部2209文件含71视频零hash差异，15run各100唯一ID，无需重复验证。README压缩后仍须保留关键比较与实验身份：统一runtime结果表增加历史baseline及百分点差（93/36/15/11/100/6/84/8/80对应现有9行），说明Pi serial的36%为同配置历史，主表30.5%属于[15,50]另一variant；DM05实际跨库目录写 ../opendm/user_checkpoints/...（不是不存在的OpenDM/）。自训README保留实际8×48/global384、base Qwen初始化及resume:null。官方README保留HF发布模型revision、发布卡五项参考值与来源链接、checkpoint及norm hash、observe使用3dbd7ae其余4827f83的commit区分；这些可用一张小表/几行表达，旧时序进度和待办可以删。完成后提交并重新发布report。
