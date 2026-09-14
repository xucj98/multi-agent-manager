# 补 battery S seed0
先读AGENTS.md、涉及库指南、源任务e3bc64f1-7f0d-46d2-9e54-831aa1727384最终报告。基于冻结J/S源34002dce65962734c59725a0f6d982ae2c438a2d独立worktree，核实battery serial config是否已有，缺失则以同源swap/cover S模式做最小接入。
科学合同由Manager固定：与已经验收的battery J共享原50条demo_clean_state、phase-only字段/编码/current_truth及availability_at_row，不新增试错集合字段；S serial_token lag30，seed0，bs32，20k，H50/K30，pi05_base独立初始化，BF16 model-only，恢复不依赖训练source。保留phase-only不表达完整试错历史的限制，不能据此改标签。
先CPU合同测试、短训练/保存/恢复smoke，发布具体commit与验证原件供Manager准入20k。若现有冻结config已支持也须报告实际一致性；不擅自启动正式20k。资源只用wuwen-1一张空闲卡，与两个数据负责人协调，HF_LEROBOT_HOME unset，共享cache软链，不传数据集。长进程MAM登记。不重复已验收模型，不扩seed，不改论文。交付可执行launcher、全部参数/来源及恢复证据，完成后等待Manager正式准入。

## Manager 2026-09-14：转B集群解除显存阻塞
本机短smoke OOM无checkpoint，保留该失败，不在同等显存卡盲目重试。Manager实查wuwen-11 GPU0/1/3/4/6各81149MiB free、0%利用率。优先GPU0，启动前再实查，不构成长期占卡。用户已授权使用wuwen-11/12训练。
立即核对B集群共享/mnt/public3的既有源码/环境、pi05_base和battery训练数据资产；先复用真实匹配资产，缺失才按.local/README优先wuwen-nx-aic与zx-data路由传输最小必需资产。路径映射可改，训练语义、字段、数值/来源不能变，不把本机/mnt/public误认共享。wuwen-12 host key verification failed，本任务先用已可访问wuwen-11，不修改SSH信任绕过。
授权完成B的隔离环境/数据部署，以及相同bs32/H50/K30的50step保存与checkpoint-only恢复smoke，预计超30分钟作业/传输登记MAM。源commit、数据/hash、cache路径、GPU硬件与CUDA差异留痕；B缓存按实际共享路径配置，不修改本机与wuwen-1缓存合同。不自动开始20k，三项验收后发布具体B launcher供Manager准入。若B资产缺失则执行必要传输/部署而非只报等待；报告传输规模与预计耗时。

## 用户目录要求落实：替代此前未固定B落盘位置的部署说明
先读MAM `.local/README.md`、`.local/wuwen-4090.md`、`.local/wuwen-11.md`。稳定B_ROOT=/mnt/public3/xcj/Projects/state-vla；三库稳定入口在B_ROOT下；本任务RUN_ROOT=$B_ROOT/workspace/fa928e8d-a486-426b-8381-16c207d37262/battery-s，部署材料在同TASK目录deployment/，共享cache=/mnt/public3/xcj/cache。worktree由稳定入口installer创建，不直接使用旧顶层仓库作为新runtime、不手工另起散乱venv。已有旧资产核验后复用，不迁移/覆盖未知或活跃目录。
已报旧stage /mnt/public3/xcj/workspace/fa928e8d-a486-426b-8381-16c207d37262/deployment 尚无GPU/venv。授权先核实无进程引用，将该任务部署材料完整迁入新TASK/deployment（目标存在则先核对，禁止覆盖差异），核对hash并保存旧→新映射。AIC /tmp/battery_s_b_transfer_fa928e8d-a486-426b-8381-16c207d37262 同样迁入本机共享PROJECT_ROOT/workspace/TASK-ID下transfer staging，修改控制包所有路径，保留旧失败记录。旧stage只删除已核对迁移的本任务文件/空目录。
不得移动活跃run或全局旧仓库；无需等我重复确认目录迁移。先落实目录、稳定installer路径与环境smoke，再恢复已授权传输/短训练；发布实际路径、映射/hash和入口证据。正式20k准入不变。

## Manager正式20k准入（B v7）
已阅读cc5c33d报告、完整gate receipt及实际launcher，独立核对gate SHA fbf924dd27fe893417aefd0372fd5ec7d2123646c5e4151eed3cf52435e4fc66、9项核心证据本地/远端hash一致，B runtime HEAD34002dce且clean。短50step保存、CPU全参和GPU policy恢复证据满足本次沿冻结源码的训练准入；未由Manager重复数值恢复。
现授权在wuwen-11实查空闲GPU0上从pi05_base独立开始一条battery S seed0/bs32/H50K30/lag30/20k save20k/BF16 model-only正式训练。使用v7 launch_battery_s_b_formal20k_candidate.sh（SHA a985e81820280bd8b3e434aef64ab0cf6be9747d02433beb5dc72a5868c93607），允许设置MAM_FORMAL_20K_APPROVED为本TASK-ID；不得从smoke续训。启动前校验HEAD/hash、数据资产、GPU约75GB以上空闲与无干扰、正式根不存在。GPU0不可用可选同机满足条件空闲卡并记录。
用nohup/setsid等脱离SSH会话的持久入口启动，不让20k随连接结束；立即登记真实训练PID的MAM job，记录父子PID及启动收据。确认真正进入训练/有限step后发布，不长轮询。完成后验收20k保存与CPU/GPU checkpoint-only恢复，再归档job。
B统一Projects/state-vla目录及共享cache约定不变，HF_LEROBOT_HOME unset。只新增这一条模型；不扩seed、数据或schema。此前失败原件与迁移映射保留。

## 用户新增收尾要求：B checkpoint回传后删除远端副本
训练继续，不改运行中路径。完成后严格阅读本机 /mnt/public/xcj/Projects/multi-agent-manager/.local/wuwen-11.md 的“训练完成、回传与删除远端 checkpoint”。本任务新生成的formal及保留smoke模型须经zx-data→wuwen-nx-aic回传本集群 /mnt/public/xcj/Projects/openpi/checkpoints/ 同group结构，逐文件SHA-256/大小校验、A侧checkpoint-only恢复通过且无活跃依赖后，直接删除B相应已核验模型副本；保留日志/来源/失败/迁移及删除收据，不删除共享pi05_base、cache、数据或他人模型。长传输登记MAM；在报告中区分训练完成、回传验收、B副本删除三个状态。此清理用户已授权，无需再次请示；传输或本地恢复未通过禁止删除。
