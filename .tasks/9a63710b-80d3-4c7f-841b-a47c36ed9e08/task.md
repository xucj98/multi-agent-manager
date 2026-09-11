# 集群C运行修复独立验收

审阅源任务2a879870-8dda-4613-a684-0ad48a5e86be的RMBench提交17b55bf(renderer复用)及9c71a3e(worktree创建优化)。MAM入口后创建自己的RMBench worktree，base9c71a3e，阅读库AGENTS。只审这两个增量及必要上下文，不重新安装三机环境。源码/证据从源report及同task目录renderer-source-audit.json、renderer-protocol-comparison.json、create-lazy-probe-20260912定位；远端C记录可只读SSH。

目的：旧strict评估第23次reset renderer崩溃，作者候选复用renderer；固定两seed相同动作/qpos/三相机已逐元素一致；40reset gate仍在进行。核查renderer生命周期、关闭/reset隔离、不同配置/设备是否错误复用、随机性/图像/动作/反馈协议是否改变。两seed诊断不是正式rollout，不要求重跑整套GPU测试；已有证据足够就判断准入，确实关键缺口才提出定向验证。不要改作者运行树或占GPU。

创建优化需核查消除重复递归遍历后软链接目标仍来自共享cache、失败不能假PASS、私有覆盖未被写回cache、计时与磁盘统计口径一致。对比作者前后实测，不要求一个绝对秒数。源码增量可做必要CPU小测试。重点给是否允许候选三机smoke及正式100的明确裁定，最多列真实阻断项及最小修复。不扩大policy/schema/环境框架。

报告填写本任务report.md并发布，记录workspace/审阅commit/验证/局限；清理自己的临时产物，保留worktree供Manager归档。不创建subagent。模型gpt5.6-terra max。
