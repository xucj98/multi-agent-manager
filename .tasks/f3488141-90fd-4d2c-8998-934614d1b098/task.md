# 六个首波N/J模型的集群C评测准备

terra/max；Manager负责设计与裁决，沿九任务覆盖优先。读MAM AGENTS/README/.local与集群C评测手册、涉及库AGENTS。旧e690任务已归档，本机worktrees已删除，但远端e690运行树/资产和全部正式结果保留，不能删除或更改HF正在使用的c3-highfreq-engineering-20260914。新任务建立自己的workspace/worktrees。

已接受六模型名单与完整来源见 /root/Documents/task-state-vla-paper/docs/analysis/wave1_six_nj_training_acceptance_20260914.json（SHA f0a993bf14529be1f8064c1b95e827a716995b99dd7d0fb5f7f32af3245a9922），训练owner task e3bc64f1-7f0d-46d2-9e54-831aa1727384 report7819a470。仅swap_blocks/battery_try/cover_blocks各N/J train0/20k，复用模型，无新训练。S待另外验收，不等S才准备这些六项。

目标：落实每模型eval0/1/2各100的18批原协议准备，H50/K30、旧continuous action RNG、demo_clean_eval、各列表100000..100099/200000..200099/300000..300099。原52批结果与HF实验分开。先做完以下实际工作，不只写计划：
1. 只读核对C现有checkpoint/资产清单，完整有效结果去重。缺失的六模型只传checkpoint及必要小型元数据，按.local规定经wuwen-nx-aic与wuwen-4090-aic优先路径，核对目标不存在/已有内容hash，不覆盖；无需传数据集、pi05_base、源码训练缓存。传输预计>30min登记MAM长job，断点续传核对源目标，不拷到HF runtime。checkpoint目录保持只读。
2. 核对三个新任务schema与现有Memory-v1 eval入口真实支持：N无memory；J swap phase/initial_empty_tray/first_origin_tray，battery phase，cover phase/red_pos/green_pos/blue_pos。必须使用保存的metadata/norm恢复，不在eval输入GT、改变标签或凭task名猜字段。冻结训练代码N5835fa04055d520e418cc1448c1bd58fa1e665cb、J34002dce65962734c59725a0f6d982ae2c438a2d；可读现有已接受原协议RMBench f401f5279c95451eb424ac98b831bab5552b2120 / bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 / OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4接口。先确认能否直接兼容新checkpoint；必要小型config/manifest在独立树准备，公共代码缺口给出证据/最小修复建议交Manager，不私自混合HF reset或修改活跃运行树。
3. 给出冻结候选runtime三库完整commit、18条实际config/manifest/命令dry-run、各自matching smoke2与fresh formal100名字/配置、资源建议。优先后续用已释放C1GPU1/2，先实测资源但本次CPU/传输准备不加载GPU，不抢C3高频卡。保留首infer90/后续30秒与既有renderer入口、视频/证据合同。新环境用现成C1 installer和共享cache，不升级依赖或自建部署框架。

交付清楚哪些checkpoint已传且验证、哪些仍传输job、接口是否有实际阻断、下一批可执行smoke命令和预计时长。Manager复核候选并冻结后接正式评测；此次不启动GPU smoke/formal，不因准备的18批叫作已运行。当前可执行工作处理完发布紧凑report并结束turn，用MAM唤醒，不轮询。
