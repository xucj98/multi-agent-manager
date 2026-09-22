## 当前归档裁决（2026-09-22）

用户要求将全部旧任务收尾归档。允许清理临时 workspace、将唯一正式产物交付至稳定产物目录、在业务仓库为尚未合入的代码建立明确的持久 Git 引用，并核对收尾 stopped job。代码尚未合入 primary 本身不是阻塞：有持久引用并记录用途即可归档，不为归档强行合并搁置的 V 实现。禁止启动新训练、eval、GPU smoke。Manager 负责最后 archive；准备 agent 可按 Manager 派发跨任务整理，不改变原任务绑定或重复 workspace add。

---

## 2026-09-22 当前清理交接要求（覆盖下文历史执行授权）

本轮只整理文件及交付状态，禁止启动训练、eval、数据生成、GPU smoke或继续旧实验计划。按当前 README 文件留存原则清理本 task 的附件：复用代码归业务库；确有必要的一次性分析附件留在本目录并提交；正式数据/checkpoint/原始评测结果留稳定产物目录不进 Git；临时脚本、调试输出、重复副本删除。保留 task.md/report.md 和既有已跟踪文件，不因为历史报告引用或旧保留要求而保留无价值副本。不清理其他 task，不迁移项目，不改 MAM 功能。

接手已有 workspace/worktree，不重复 workspace add。先核对必要代码/正式产物是否已交付到稳定位置。对 .tasks 未提交附件执行分类清理；workspace 中临时内容可以清理，正式产物不删。共享 MAM Git 操作须等待 Manager 单独授权；先报告需留附件清单及理由，Manager 批准后提交和发布简报。不自行 archive task；报告是否具备归档条件和具体阻塞。对原 stopped job 核对结果并建议收尾，不重启。交付简报应简洁记录清理数量、必要成果位置、未交付内容和阻塞，不另造审计文件体系。

---

# 九任务优先补齐执行合同
Manager负责科学设计与最终裁决；本任务负责 press_button、blocks_ranking_try 的数据与工程实现。先读AGENTS.md、涉及仓库AGENTS.md，以及论文docs/EXPERIMENT_PLAN.zh-CN.md、ASSET_AUDIT.zh-CN.md（旧缺口必须实查）。创建独立worktree，禁止修改既有运行树。
立即检查现有可复用资产与生成入口；缺少demo_clean_state时执行必要代码适配、短smoke，然后生成每任务50条成功且完整的训练示范。固定确定性生成seed序列并保存所有尝试/失败/筛选记录；不得用正式eval种子100000..100099、200000..200099、300000..300099做训练数据。遵循benchmark原demo生成成功筛选规则，不改环境成功判据。原始轨迹须保存足够状态/事件/动作与来源，以便之后定义标签；生成时不要将未来/隐藏答案注入在线策略。
允许立即进行数据生成和N路径转换/配置实现，不必等schema全部完成。GPU使用wuwen-1的实际空闲卡；同组最初最多2卡，不抢占其他进程，和另一数据负责人协调卡号。每任务先2条生成smoke检验完整性再扩到50条，预计超过30分钟登记MAM job，失败保留证据；不要长轮询。共享cache规范 /root/.cache -> /mnt/public/xcj/cache，HF_LEROBOT_HOME unset，不复制数据集到wuwen-1。
press_button依据可见目标数字及实际按压事件累计计数，不以已发命令替代物理事件；ranking只保留过去尝试与可观察反馈，不能把隐藏正确排序输入策略。
N使用14D机器人state+当前图像，无任务memory，pi05_base新初始化、seed0、bs32、20k、H50/K30；J固定joint逐行状态、上一chunk末执行行反馈。提交确切schema草案（字段、可获得时刻、目标时间、初值/unknown编码、连续归一化、source路径）由Manager裁决，先实现通用采集/N转换及必要接口，不能自行把草案当最终科学合同。S共用同任务字段，连续接口不支持须明确实现缺口，禁止偷换表示。
交付不是只读调研：发布可运行生成入口、实际smoke/生成进度、数据来源清单与下一步可执行命令；每个数据集就绪即发布，不等另一个任务。正式20k训练前提交数据完整性、来源/标签合同、CPU测试与短恢复候选供Manager验收，禁止未验收开正式训练。不要新增训练seed，不改论文主张，不接管HF工作。

## 2026-09-20 Manager 追加：新任务 J/S schema 缺口审计

在 `blocks_ranking_try N` smoke/正式训练进入稳定状态后，追加一份只读 schema 缺口清单，覆盖 `observe_and_pickup`、`swap_T`、`blocks_ranking_try`、`press_button`：

- 列出 J/S 所需字段、字段的可获得时刻、监督目标时刻、初值/unknown 编码和连续归一化方式；
- 核对现有 raw state/event/provenance/trace 是否足以无歧义重建这些字段；
- 明确哪些字段已有证据、哪些字段缺失、哪些字段需要 Manager 决策；
- 只做审计和建议，不自行冻结科学合同，不启动 J/S 正式训练，不修改已有 N 数据或评测结果；
- 将结果写入 report 并发布，供 Manager 裁决后再安排实现。

## 2026-09-20 Manager 追加：并行启动 swap_T N

`swap_T N` 已有 50 集原始数据、N LeRobot 转换、manifest、norm、CPU batch 和端到端 state/action 校验；其 J/S schema 仍未冻结。为利用 wuwen-1 空闲 GPU，允许在 `blocks_ranking_try N` 的 gate 不被破坏、资源不冲突的前提下，并行启动 `swap_T N` 的正式训练：

- 仍使用既定 N 合同：pi05_base fresh、train seed0、batch32、20k steps、H50/K30、model-only BF16、无 task memory；不使用正式 eval seeds；
- 启动前再次核对 swap_T N manifest/norm/CPU batch 和数据路径，使用 wuwen-1 空闲卡并登记真实 PID/MAM job；
- 先短 smoke/recovery gate，再 formal20k；若 gate 或资源检查失败，保留证据并停止该 lane，不修改 J/S schema；
- 不影响或终止 blocks_ranking_try N，不抢占本机或 C1 正在运行的评测。

## 2026-09-20 Manager 冻结：四个新增任务的最小 J/S schema 与连夜启动目标

为满足九任务覆盖目标，Manager 冻结以下最小、可由现有 source/provenance 重建的字段；不得输入隐藏答案、目标排序或评测信息：

- `observe_and_pickup`：`target_identity`（遮挡前首帧可见的 object model/id，categorical，未知值为 `unknown`）和 `phase`（`visible_target`、`occluded`、`pickup`，依据 wall/动作边界；无法可靠标注的帧为 unknown）。identity 只在 episode 首次可见时获得，之后作为缓存；S 使用 query-30 的参考字段，J 预测 query+1..horizon 的字段；N 不变。
- `swap_T`：`red_initial_pose`、`blue_initial_pose`（episode 起始的环境坐标二维 xy+yaw，连续，xy 与 yaw 用固定 model normalization/xy_sincos；unknown 仅在起始观测不可用时使用）和 `phase`（`initial`、`first_placed`、`second_placed`、`completed`，依据已有动作/事件边界）。初始 pose 在 episode 首帧获得并缓存，不用未来目标 pose；S/J 分别按既有 serial lag30/full_t_plus_1 合同监督。
- `blocks_ranking_try`：`attempt_count`（0–5 的已完成尝试计数，integer categorical/normalized scalar）和 `last_feedback`（`unknown`、`failure`、`success`，仅来自已经发生的物理按压/环境 terminal feedback）；保留 visible order 仅作 provenance，不输入隐藏 target ranking。S/J 不使用未来 terminal feedback，目标按 query-30/query+1 截断。
- `press_button`：`phase`（`left_button_presses`、`middle_button_presses`、`confirm_button`、`completed`）、`left_press_count`、`middle_press_count`（0–9，按物理 joint threshold 事件累计）和 `confirm_pressed`（binary）；数字卡面值是初始可见事实，可作为 provenance/初始缓存，不把最终正确次数写入在线输入。S/J 按既有 lag30/full_t_plus_1 合同监督。

统一规则：训练字段来自同一帧或过去帧可获得的 source/provenance；未来字段只能作为 J target，不能作为输入；S train 用 reference、infer 用 selected；J train 输出逐行未来字段并按已执行行反馈；所有新增字段必须在 sidecar 中记录 source path、available_at、target_at、unknown mask、normalization 和 hash。若某个字段无法从现有 trace 无歧义恢复，立即报告并将该字段降为 unknown，不得猜测。

连夜目标（2026-09-20 04:30–10:30）：四个新增任务的 J 与 S 至少各启动一个经过 smoke/recovery gate 的正式 20k 训练；N 训练继续。每个长进程登记真实 PID/MAM job，使用 wuwen-1 空闲 GPU，不能影响已有 ranking N、swap_T N 或 C1 评测。若 8 条 lane 超过可用卡，先每任务启动 J 一条，再启动 S；不得因并发不足修改合同。

## 2026-09-20 Manager 追加：视觉歧义与按压边沿计数审计（J/S 启动前置）

在启动四个新增任务的 J/S 正式训练前，执行者必须先对 schema 做独立的可观测性审计，并把结果写入 report：

### press_button 的强制审计

不能只在按钮回弹高位时累计一次。环境在按钮 joint 低于阈值时记录按下边沿，并通过 reset/回弹高位解除 press flag；如果只采样高位计数，会把“已按下但尚未释放”“低位持续帧”“按压失败/未越过阈值”和“完整按压完成”混为一类，造成监督时刻错位，也可能因重复低位帧重复计数。

以边沿状态而非单一完成计数表达进度。优先核验如下候选编码的语义和逐帧可重建性：

- `00`：无已确认按下/释放的初始状态；
- `01`：按下边沿已发生、释放边沿尚未发生；
- `11`：第一次按压完成（按下+释放）；
- `12`：下一次按下边沿已发生、尚未释放；
- `22`：第二次按压完成。

实际编码须扩展到任务所需次数，并明确每一位分别代表哪一个按钮/哪一种边沿；不能只写一个整数。审计必须逐帧对照 `physical_press_events`、button joint qpos 阈值、reset 事件和 HDF5 observation 帧，验证同一按压不会因低位持续帧重复计数，也不会在 chunk 边界丢失按下或释放边沿。若某个边沿只能在事后 provenance 得到、在线时刻不可得，必须标为 source-only，不能作为在线输入。

### 四任务视觉歧义审计

对 `observe_and_pickup` 的 identity、`swap_T` 的初始 pose/yaw、`blocks_ranking_try` 的 visible order/attempt feedback、`press_button` 的数字卡片与按钮状态，逐字段记录：首次可见帧、遮挡/相似外观风险、是否能由当前 observation 区分、是否只能由 source provenance 区分、unknown mask 和训练目标时刻。禁止把隐藏目标排序、最终正确次数、未来 terminal feedback 或评测初始条件作为在线输入。

只有完成该审计并发布证据后，才可为对应任务启动 J/S 正式训练；审计不通过的任务可以继续 N，但必须暂停其 J/S lane 并报告具体歧义。
