# 第二批 B 能力基线：先启动已验收的四项重复

## 目标与授权
你负责本机下一批训练执行、监控及最终验收。先从已验收 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50` 用 mam workspace add 创建独立 OpenPI worktree并读取库 AGENTS。不修改训练实现。先启动下表四项，它们属于既定 B 组，不等待集群 C 或 Q2 eval。任务标题中的 put-back 项暂待专用配置验收，不阻塞四项。

| 本机 GPU | config | seed |
| --- | --- | --- |
| 2 | pi05_rmbench_rearrange_blocks_serial_lag30 | 1 |
| 3 | pi05_rmbench_rearrange_blocks_serial_lag30 | 2 |
| 4 | pi05_rmbench_rearrange_blocks_no_memory | 1 |
| 5 | pi05_rmbench_rearrange_blocks_no_memory | 2 |

14:22快照GPU2–7均空闲，GPU0/1已有其他占用且本容器看不到进程，不碰。启动时重新确认；wuwen-1禁止新作业。GPU6/7暂留另一个专用准备任务。

## 训练协议
与已完成 e7e5ac54 任务 rearrange serial/no-memory seed0完全相同，只变seed及唯一exp_name。单卡batch32、20,000 updates、同pi05_base、H50/K30、demo_clean_state已转换数据及专用机器人norm；BF16模型保存，仅保留20000及metadata/assets。读取源任务报告与共享checkpoint artifacts中的真实命令、配置、验收证据，不猜默认值。数据必须demo_clean_state，不能换demo_clean。现有实际50step、恢复与对应训练路径已验收，不重复GPU smoke；新独立环境做必要导入/配置/数据及输出不存在检查后立即启动。不要等全部四项准备好才启动先就绪项。

用python -u -B和可靠detach，独立exp_name包含本task短前缀、config和seed，禁止覆盖/混写；启动后立即mam job add登记真实host/PID，确认optimizer更新、有限loss、batch/步数并给Manager简报。保持运行树冻结。不改batch、模型、数据处理或loss。失败保留证据，重试需独立目录。

## 台账与收尾
先在report中写清每项为何训练：补齐B组同骨干serial和no-memory的三个训练seed，避免把seed0随机性当表示差异；对应full三seed已经完成。链接checkpoint路径，eval待C验收，不写预期成功率。按约小时监控，实际结束及时验收20000、完整参数/形状/BF16/有限值、模型单独恢复、metadata和退出/自有资源释放。必要结果同步给Manager纳入 RMBench/experiments/memory_chunk_20260910 台账。

长作业登记MAM，等待按用户约定使用工具；不建立通用调度系统、不创建subagent。执行者可阶段汇报，由Manager继续唤醒；进程不依赖tool会话。清理自身临时文件、归档停止job，保留共享正式checkpoint。发布report，worktree最终由Manager归档。

## Manager待办清理与恢复责任
恢复现有四路训练责任。先核对实际进度、PID和20k完成状态；完成的验收产物并归档job，仍运行的使用新版mam wait保持active等停止事件，取代小时模型轮询。更新现有报告/台账，使用原worktree不重建，不重复训练。

## 纠正本次等待交付
刚才你启动后台mam wait后发送final结束turn；这不等于保持active，Manager实际收到agent_completed。请恢复后接续已有等待工具session，或者只停止自己的旧wait再新开mam wait。必须通过等待工具调用保持本turn，直到job事件/用户消息返回，再处理结果；不能仅启动后台等待进程就结束turn。此次无需再读全日志/重复进度检查。

## 完成训练后的评估交接
用户要求完成训练及时安排eval并更新实验台账。请核对各run实际结束状态；完成后验证最终20k checkpoint完整/可恢复及metadata、归档已处理训练job，并在report给出明确可评模型清单（config/schema/seed/commit/绝对checkpoint路径、研究目的、预期结论）。通过任务报告交给e6908de7评估队列，勿自行重复启动eval。仍在训练的继续保留真实状态和完成事件监控。无需为没有变化的等待窗口改报告或发心跳；任务全部交付后结束turn，不为已完成事项持续wait。

## 临时释放执行者名额
当前Codex并发名额已满，Manager需要启动U组训练准备。你核对并交付本轮实际状态后停止自己的mam wait并结束turn；保持4个训练进程原样，不停止训练。Manager临时接手完成事件监控，训练完成时恢复你做产物验收及评估交接。本条替代此前必须持续active的要求，不新增任务状态，不重复无变化报告。
