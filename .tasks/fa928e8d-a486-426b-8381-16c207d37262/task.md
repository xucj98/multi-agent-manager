# 补 battery S seed0
先读AGENTS.md、涉及库指南、源任务e3bc64f1-7f0d-46d2-9e54-831aa1727384最终报告。基于冻结J/S源34002dce65962734c59725a0f6d982ae2c438a2d独立worktree，核实battery serial config是否已有，缺失则以同源swap/cover S模式做最小接入。
科学合同由Manager固定：与已经验收的battery J共享原50条demo_clean_state、phase-only字段/编码/current_truth及availability_at_row，不新增试错集合字段；S serial_token lag30，seed0，bs32，20k，H50/K30，pi05_base独立初始化，BF16 model-only，恢复不依赖训练source。保留phase-only不表达完整试错历史的限制，不能据此改标签。
先CPU合同测试、短训练/保存/恢复smoke，发布具体commit与验证原件供Manager准入20k。若现有冻结config已支持也须报告实际一致性；不擅自启动正式20k。资源只用wuwen-1一张空闲卡，与两个数据负责人协调，HF_LEROBOT_HOME unset，共享cache软链，不传数据集。长进程MAM登记。不重复已验收模型，不扩seed，不改论文。交付可执行launcher、全部参数/来源及恢复证据，完成后等待Manager正式准入。
