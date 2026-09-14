# 视觉历史基线V工程实现
用户要求九任务N/V/S/J比较，Manager保留科学设计；你仅做既定V的工程实现与验证。先读AGENTS.md、涉及库指南和论文docs/EXPERIMENT_PLAN.zh-CN.md。独立worktree，不改运行中源码。
冻结输入合同：同pi0.5，无显式任务状态标签/监督；当前图像加episode初始观察锚点及最近4次已发生的查询观察，按物理帧身份去重，禁止未来图像。训练query间隔K30，与推理实际查询一致；短历史padding使用mask，不把重复padding当新帧。起始帧与最近查询重复时只保留一份，顺序/相机顺序固定。机器人state沿N的14D，H50/K30，seed0、bs32、20k、同50条示范。额外visual tokens/显存/耗时明确记录，不称外部方法复现。
立即检查既有视觉历史能力并实现通用训练transform/model输入与episode内推理缓存、reset/跨episode隔离，优先从已就绪数据任务做CPU验证；尚无数据的四任务接口应可复用。禁止为凑显存静默减bs、减相机或图像分辨率。若现有模型结构不能直接容纳历史token，提交具体最小变更及代价给Manager裁决，期间推进采样/缓存/测试独立工作。
交付真实代码、边界测试（初始/不足历史/去重/无未来/episode reset/训练推理一致）、可运行短smoke候选、资源预算；先CPU，不启动GPU/20k直到资源与候选准入。不调九任务语义、不负责主张或文献、不占用已有data GPU。每个实际阻断尽早报告。

## Manager接续：实际任务清单与CPU输入准入
工程交付已进入独立review a98a1d8e-bf13-4316-9425-18389580fc6c。保持交付commit供review，不改冻结历史宽度/bs/分辨率。现在并行补齐可就绪的五任务真实数据表，而不是空manifest：rearrange_blocks、put_back_block、swap_blocks、battery_try、cover_blocks，数据repo为各自demo_clean_state_shared_memory，现行50条来源/14D norm可参考论文 /root/Documents/task-state-vla-paper/docs/analysis/wave1_six_nj_training_acceptance_20260914.json 及源N元数据。九个官方task ID完整列在 /root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md，第2节，不应再报告ID缺失。其余四任务对应数据owner f0011538/2a792e9a 生成中，明确pending，不填假路径。
实查五任务episode数、三相机、14D、query采样与来源一致性，做真实CPU batch与非空配置dryrun；不要启动GPU/训练。V应共享对应N的机器人动作归一化：来源/动作列完全匹配时复用已验收norm并记录hash，不默认另采10000帧导致比较多一个变化。若现有V入口强制重算则指出并做必要最小修复，避免历史query子采样改变norm统计；不要重用不匹配的旧norm。
交付一个完整非空两步GPU容量profile候选：准确数据、源commit、实际命令、最大18图槽、bs32/H50、保存/恢复、峰值显存及每步计时字段。这是技术profile不计效果/正式训练，GPU资源及执行仍由Manager后续准入。不要等review结果才补数据清单与CPU候选。

## Manager对review a98a1d8e 的裁决
已直接检查VisualHistoryRuntime reset/prepare/commit，确认pending无episode generation且commit会写入reset后的缓存。接受其P1阻断：修复reset与在途infer、反序completion，覆盖RNG/state串行化及旧generation拒绝，增加真实边界回归；首infer必须保证初始step0或显式锚点，不得以晚到帧代替episode初始观察。五真实任务与N norm及非空profile按上节继续。
不接受把“model-only不能续训”自动当必须改full-state的缺陷：既有N/S/J均BF16 model-only，checkpoint-only policy恢复与训练optimizer续训是不同要求。继续匹配既有model-only合同，明确中断不可optimizer-resume；设置正式save_interval=20000并验证保存/CPU或GPU policy恢复候选，不自行增加full-state或改变实验。
修复后交付新commits及问题逐项响应供同reviewer复查。未完成不得GPU/正式训练/闭环准入。数据loader缓存需有界并测CPU RAM，不能随整个数据集无限增长。

## 2026-09-15 Manager：双卡容量方案准入
已核对a98复审及实际OOM receipt：原P1/五任务CPU/norm修复接受；单卡18槽bs32首update OOM为实测容量阻断，非已训练。当前授权作者实现并执行一个双卡技术profile，不授权正式20k。

优先wuwen-11 GPU0/1，先实查两卡空闲显存与利用率（此前各4.4GiB占用/0%，不能终止他人进程）；GPU4 battery与GPU6 observe预留禁止占用。利用现有训练device mesh/FSDP路径，固定GLOBAL batch32、seed0、18槽/三相机/原输入分辨率、H50/K30和base、norm、loss、optimizer。先确认batch在两卡的真实切分以及参数/optimizer分片语义，不将per-device batch32变global64。允许仅改资源配置/必要兼容限制并记录独立commit；不减少history/分辨率/相机/steps。禁止配置HF_LEROBOT_HOME，按B规范缓存软链，unset该变量；旧profile曾设置此变量须如实记录并在复测纠正，不改写失败记录。

只做两step profile→save2→checkpoint-only policy恢复，记录两卡峰值、真实step耗时、全18有效槽policy动作[50,14]和mean/p95、独立推理显存及CPU RSS。若推理单卡不适配4090须给实测资源需求，不能只证明训练成功。失败即保存明确证据，不自行扩大四卡/改科学合同。短profile通常无需长job，预计>30min按MAM登记。结果交原独立review增量验收后Manager决定正式队列；九任务N/S/J不等V。
