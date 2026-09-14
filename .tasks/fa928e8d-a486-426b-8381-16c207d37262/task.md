# 补 battery S seed0
先读AGENTS.md、涉及库指南、源任务e3bc64f1-7f0d-46d2-9e54-831aa1727384最终报告。基于冻结J/S源34002dce65962734c59725a0f6d982ae2c438a2d独立worktree，核实battery serial config是否已有，缺失则以同源swap/cover S模式做最小接入。
科学合同由Manager固定：与已经验收的battery J共享原50条demo_clean_state、phase-only字段/编码/current_truth及availability_at_row，不新增试错集合字段；S serial_token lag30，seed0，bs32，20k，H50/K30，pi05_base独立初始化，BF16 model-only，恢复不依赖训练source。保留phase-only不表达完整试错历史的限制，不能据此改标签。
先CPU合同测试、短训练/保存/恢复smoke，发布具体commit与验证原件供Manager准入20k。若现有冻结config已支持也须报告实际一致性；不擅自启动正式20k。资源只用wuwen-1一张空闲卡，与两个数据负责人协调，HF_LEROBOT_HOME unset，共享cache软链，不传数据集。长进程MAM登记。不重复已验收模型，不扩seed，不改论文。交付可执行launcher、全部参数/来源及恢复证据，完成后等待Manager正式准入。

## Manager 2026-09-14：转B集群解除显存阻塞
本机短smoke OOM无checkpoint，保留该失败，不在同等显存卡盲目重试。Manager实查wuwen-11 GPU0/1/3/4/6各81149MiB free、0%利用率。优先GPU0，启动前再实查，不构成长期占卡。用户已授权使用wuwen-11/12训练。
立即核对B集群共享/mnt/public3的既有源码/环境、pi05_base和battery训练数据资产；先复用真实匹配资产，缺失才按.local/README优先wuwen-nx-aic与zx-data路由传输最小必需资产。路径映射可改，训练语义、字段、数值/来源不能变，不把本机/mnt/public误认共享。wuwen-12 host key verification failed，本任务先用已可访问wuwen-11，不修改SSH信任绕过。
授权完成B的隔离环境/数据部署，以及相同bs32/H50/K30的50step保存与checkpoint-only恢复smoke，预计超30分钟作业/传输登记MAM。源commit、数据/hash、cache路径、GPU硬件与CUDA差异留痕；B缓存按实际共享路径配置，不修改本机与wuwen-1缓存合同。不自动开始20k，三项验收后发布具体B launcher供Manager准入。若B资产缺失则执行必要传输/部署而非只报等待；报告传输规模与预计耗时。
