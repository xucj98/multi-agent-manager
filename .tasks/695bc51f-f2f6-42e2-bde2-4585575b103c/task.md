# put-back B 基线配置及训练准备

目标：既定论文 B 组中 put-back 目前只有 full三seed，补 serial lag30 和 no-memory seed0，回答同骨干能力比较。两项不依赖Q2评估或C环境验收。你负责最小配置补齐、验证和后续获Manager放行后的训练；不改变模型/loader/schema算法。

先读MAM入口，用mam workspace add从OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 建本task独立worktree并读库AGENTS。现有rearrange serial/no-memory和put-back full均已有实际20k训练；按现有配置factory增加put-back serial_lag30/no_memory注册（若已有等价配置则复用，勿重复）。沿用已验收put-back demo_clean_state数据、sidecar及专用robot norm，不使用rearrange norm或demo_clean。

两条路径需实际loader核对batch/机器人14D、memory字段/serial token监督和条件/no-memory robot-only、目标与padding mask、norm及数据来源，确认相对rearrange既有基线只变任务数据/字段资产。CPU配置样本验收后提交小改交Manager，安排独立review。可用本机GPU6/7各做必要50step训练+BF16保存+checkpoint-only恢复（同类路径已有验收则聚焦本任务新配置，不重跑全套旧测试），记录有效updates/有限loss/恢复shape；不得动GPU0/1/2–5或wuwen-1。启动前查实际显存，碰到他人占用等待并汇报。

正式计划：GPU6 serial seed0，GPU7 no-memory seed0；单卡bs32、20k、H50/K30、相同pi05_base初始化、仅最终20000 BF16模型及metadata/assets。已有run禁止混写，失败retry新目录。正式开跑前提交配置commit和smoke证据给Manager，Manager快速验收后即放行，不等C。冻结源码，使用独立exp_name/可靠detach/python -u -B，登记mam job，确认初始updates/loss。评估另由C验收后安排。

report记录研究目的、实际命令/commit、数据/norm和结果路径、完成与缺口。正式训练如放行则按小时监控，完成后核实权重/metadata完整、退出资源释放并归档job。清理本任务smoke临时产物，保留正式checkpoint及待Manager归档worktree。不创建subagent，不改MAM，不修改他人运行树。

## Manager放行：put-back no-memory seed0
独立review15254a5f配置/真实CPU样本PASS，作者GPU7已完成50updates、有限loss、BF16完整保存与checkpoint-only恢复actions[50,14]。Manager已核对报告及实际保存日志，现正式放行GPU7 no-memory seed0的20k训练。沿a7f3e07冻结树、单卡bs32/20k/相同base及data/norm、最终BF16模型及metadata，独立exp_name不覆盖。立即重新确认GPU7空闲后启动、登记job并验证有效updates/有限loss，不等C或serial。先保留门禁简报到正式run artifacts再清理自身smoke临时checkpoint。serial配置review也PASS，但其GPU smoke尚未完成，仍等GPU6空闲，不碰其他占用。
