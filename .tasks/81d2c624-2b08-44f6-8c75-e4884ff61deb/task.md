# 首批训练资产：恢复pi05 base与仿真数据
# 目标

# 用户最新数据约束

用户明确指定仿真训练源只能用demo_clean_state；demo_clean缺metadata/详细子任务标注，不作为fallback。恢复数据必须含demo_clean_state的metadata和详细子任务划分。若恢复已转换LeRobot数据，必须可沿metadata确认来源为demo_clean_state且所需标签/事件保存完整；来源不明先不用于训练。请核对当前找到/正在传输的两任务数据，缺状态版就继续从zx-data/wuwen-11定位真实目录，不用clean版凑齐。

恢复首批pi05训练所需base初始化和rearrange/put_back数据，尽快解除开跑阻塞。用户已经授权schema施工和正式实验，可按需利用原wuwen-11资产；你负责定位/复制已有数据和权重，不写算法，不训练、不占GPU。

# 范围与步骤

先读MAM任务及RMBench/openpi AGENTS.md、RMBench实验规范。接续你已发布的 .tasks/320c8c68-c21c-4189-8f56-4d217ad071b4/report.md。此前已知路径缺失不等于所有资产不存在，先在本地已知cache、data、shared根做有界名称/metadata搜索（不要全盘rg所有文件）。可能已有pi05_base缓存或环境变量指定的LeRobot根。若本地找不到，通过 ssh wuwen-11 定向定位原镜像 /mnt/public3/xcj/Projects/RMBench、其记录的HF/Openpi caches（先从现有metadata确定）。源端只读，不改wuwen-11代码/环境/进程，不查GPU。

1. 优先Pi0.5官方base参数，不用finetuned shared或drawer模型冒充base。已有正确缓存直接复用；需恢复优先从旧集群复制，可从官方公开源下载作为fallback，记录来源。确认manifest/参数必要文件可读，是否加载验证另标；不盲目下载多份。
2. 获取rearrange、put_back单任务的原始或正确转换数据及其标注/metadata，优先原来50条expert数据与原始状态字段，不能将eval rollout当训练数据。若转换数据足以提供series/constants/events，先恢复可以启动的部分；数据不足明确缺失字段，不猜标签。将可用数据路径/feature schema/norm统计尽早通知Manager，数据适配agent任务7c8fbc25-6c9b-4529-b63f-da8a5b5e54e2由Manager同步。
3. 共享资产最终放主repo gitignored data/checkpoint或已有规范cache中（实际目标不指向你worktree）。先估算大小和磁盘可用，rsync可断点恢复，已存在非同源文件拒绝覆盖；源metadata随数据复制，不复制源代码。保存简短来源/命令/验证记录在任务report及现有数据metadata链，避免新增环境provenance系统。
4. 暂不恢复全部历史数据或所有checkpoint；drawer的5ep原始素材已可读，交给dataagent处理。重点base+两个仿真任务，不为搜索消耗几个小时。若wuwen-11连接失败给确切错误，继续本地/官方资产路径。

# 交付

只读/资产恢复无需建代码worktree；临时transfer文件置本workspace，正式数据放共享主目录。预计超过1小时传输用mam job登记host/PID及用途，并在完成/失败后记录收尾再archive job。给实际数据量、episode/frames、base来源、真实路径、完整性验证、尚未验证项。没有修改代码就记无commit。task_revision和report按MAM发布，清理自有临时文件后等Manager归档。不要自行派agent。

# 用户补充的传输拓扑（优先采用）

可以ssh wuwen-nx-aic，再从zx-data执行rsync拉取。wuwen-nx-aic与本机/wuwen-1共享同一个/mnt/public；zx-data与wuwen-11共享旧集群文件系统。该路径每条约10MB/s，最多两条并发，第二条必须至少在第一条启动60秒后再启动；同时启动会限为合计10MB/s。先核查已由你启动/运行的传输及目标，避免对同一文件并行写或重复复制。正式写入直接落共享目标，避免再经过本机中转。大传输登记真实执行host=wuwen-nx-aic及PID，可按base与数据拆两条并确保一分钟间隔。记录开始时间/实际吞吐，不调整他人的链路或进程。若已启动较慢的自有传输，先说明并安全停止自己那条再断点续传，不破坏已有目标。新发现有用路径尽早通知Manager。
