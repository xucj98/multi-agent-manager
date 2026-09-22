## 2026-09-22 当前清理交接要求（覆盖下文历史执行授权）

本轮只整理文件及交付状态，禁止启动训练、eval、数据生成、GPU smoke或继续旧实验计划。按当前 README 文件留存原则清理本 task 的附件：复用代码归业务库；确有必要的一次性分析附件留在本目录并提交；正式数据/checkpoint/原始评测结果留稳定产物目录不进 Git；临时脚本、调试输出、重复副本删除。保留 task.md/report.md 和既有已跟踪文件，不因为历史报告引用或旧保留要求而保留无价值副本。不清理其他 task，不迁移项目，不改 MAM 功能。

接手已有 workspace/worktree，不重复 workspace add。先核对必要代码/正式产物是否已交付到稳定位置。对 .tasks 未提交附件执行分类清理；workspace 中临时内容可以清理，正式产物不删。共享 MAM Git 操作须等待 Manager 单独授权；先报告需留附件清单及理由，Manager 批准后提交和发布简报。不自行 archive task；报告是否具备归档条件和具体阻塞。对原 stopped job 核对结果并建议收尾，不重启。交付简报应简洁记录清理数量、必要成果位置、未交付内容和阻塞，不另造审计文件体系。

---

## 2026-09-21 新Manager收尾裁决（当前有效）

状态：交付事实已核验；保留工作区待证据迁移与schema裁决。

observe N 20k与CPU恢复PASS已核验；swap-T N的数据/转换交付已完成，正式训练由2a792e9a接续。原7 jobs均归档。workspace/checkpoint-transfer-20260920保存observe/battery/press恢复证据，RMBench数据与代码仍用于后续S/J，不直接删除workspace。下一步是先迁移稳定证据并核对依赖，再完成任务归档。四任务S/J新执行合同待与用户讨论后另行发布。

本轮依据用户要求先交接并讨论计划，未启动新的训练/评测；不把无job自动解释为科学验收完成。

---

# 九任务优先补齐执行合同
Manager负责科学设计与最终裁决；本任务负责 observe_and_pickup、swap_T 的数据与工程实现。先读AGENTS.md、涉及仓库AGENTS.md，以及论文docs/EXPERIMENT_PLAN.zh-CN.md、ASSET_AUDIT.zh-CN.md（旧缺口必须实查）。创建独立worktree，禁止修改既有运行树。
立即检查现有可复用资产与生成入口；缺少demo_clean_state时执行必要代码适配、短smoke，然后生成每任务50条成功且完整的训练示范。固定确定性生成seed序列并保存所有尝试/失败/筛选记录；不得用正式eval种子100000..100099、200000..200099、300000..300099做训练数据。遵循benchmark原demo生成成功筛选规则，不改环境成功判据。原始轨迹须保存足够状态/事件/动作与来源，以便之后定义标签；生成时不要将未来/隐藏答案注入在线策略。
允许立即进行数据生成和N路径转换/配置实现，不必等schema全部完成。GPU使用wuwen-1的实际空闲卡；同组最初最多2卡，不抢占其他进程，和另一数据负责人协调卡号。每任务先2条生成smoke检验完整性再扩到50条，预计超过30分钟登记MAM job，失败保留证据；不要长轮询。共享cache规范 /root/.cache -> /mnt/public/xcj/cache，HF_LEROBOT_HOME unset，不复制数据集到wuwen-1。
observe需要保留遮挡前可辨认的参考身份，禁止把候选正确答案或场景对象索引作为在线输入；swap_T保留初始二维位姿/方向，不能为了复用类别接口而擅自量化成另一研究问题。
N使用14D机器人state+当前图像，无任务memory，pi05_base新初始化、seed0、bs32、20k、H50/K30；J固定joint逐行状态、上一chunk末执行行反馈。提交确切schema草案（字段、可获得时刻、目标时间、初值/unknown编码、连续归一化、source路径）由Manager裁决，先实现通用采集/N转换及必要接口，不能自行把草案当最终科学合同。S共用同任务字段，连续接口不支持须明确实现缺口，禁止偷换表示。
交付不是只读调研：发布可运行生成入口、实际smoke/生成进度、数据来源清单与下一步可执行命令；每个数据集就绪即发布，不等另一个任务。正式20k训练前提交数据完整性、来源/标签合同、CPU测试与短恢复候选供Manager验收，禁止未验收开正式训练。不要新增训练seed，不改论文主张，不接管HF工作。

## Manager接续：本机生成资源与资料路径
资料绝对路径是 /root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md 与 /root/Documents/task-state-vla-paper/docs/ASSET_AUDIT.zh-CN.md；已实际读取，不能因仅检索/mnt/public找不到而称资料不存在。请更正报告。
本机与wuwen-1共享同一/mnt/public，现明确授权在本机运行本任务数据生成。Manager本次实查本机GPU4有66290MiB free/0%、GPU5有54269MiB free/0%；这是可用余量而非独占承诺。A组优先GPU4/5，先与B组确认无冲突并重新实查，用原两集smoke测实际容量；不要求生成卡满足训练75GB门槛，不因wuwen-1满载停止本机生成。
在05e512f新代码上重新验证两任务各2条smoke；原provenance泄漏路径已改，旧smoke不能替代。通过后按既有合同立即启动各50条生成，长任务登记实际本机host/PID，不再等一次Manager确认。保留两种swap初始pose来源及全部可获得时刻，J/S schema未裁决不阻断原始采集或N转换。不启动20k训练；新的数据完整性/转换候选交付后由Manager裁决。

## 2026-09-15 立即执行：observe N优先B训练
Manager已核对candidate receipt及真实CPU batch，批准observe N smoke50 → checkpoint-only CPU recovery → fresh formal20k顺序自动执行；两项通过后不用再次等待Manager。允许设置本任务三个对应授权变量。科学合同固定ec86d857、seed0、bs32、H50/K30、pi05_base fresh、20k、BF16model-only。B优先GPU6，其次7/5/0–3；实查0–3各4413MiB且0%，有76741MiB free，不能因非零显存而拒用；不终止他人进程，预分配与真实峰值须容纳已有占用，GPU4禁止占用。

立即按B规范部署本任务独立openpi worktree及必要observe数据/sidecar/norm；B使用/mnt/public3/xcj/Projects/state-vla与/mnt/public3/xcj/cache，保持缓存软链、HF_LEROBOT_HOME unset。现有候选A绝对路径必须明确映射为B路径并核对hash，不能原样盲跑。无需等待B的RMBench/bridge通用安装，因为N训练只依赖已通过的openpi环境。跨集群必要数据传输按规范及MAM长job登记；此为B独立存储，区别于A/wuwen-1共享盘禁止重复拷贝。若传输暂阻，继续准备B，不让A可执行smoke停等；禁止A/B重复正式训练同一设定。

完成必要smoke/recovery后自动正式20k并立即登记真实PID，回报真实step、GPU、job和预计时间，不停在candidate/授权门禁报告。训练完成回传A核验恢复后删除B模型副本。swap_T数据采集与转换继续，N就绪按相同科学合同准备下一卡，schema工作不阻挡N。
