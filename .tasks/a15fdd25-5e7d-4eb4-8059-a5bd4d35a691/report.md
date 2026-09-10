task_revision: 8f84e935ffe4bcd6e850306308f37a6da0edcffc

2026-09-10 11:28 +08:00 阶段简报：row20最终已获Manager验收并收尾；row50/GPU1匹配smoke通过后已启动正式100，登记及首条检查完成。row1/GPU0人工中点13/50，已按超过10pp要求调查，未发现协议/基础设施异常，原run继续。三树源码、配置及实验README保持冻结。

| run（H50/K30） | GPU | 当前状态/结果 | 正式runner PID；MAM job |
| --- | ---: | --- | --- |
| row30 | 0 | 已完成92/100并验收；smoke清理、job归档完成 | 1933083（已退出）；a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 | 1 | 11:09:21完成86/100并验收；smoke清理、job归档完成 | 2227400（已退出）；d358726f-3671-42d9-b3ac-801f15ddcdb7 |
| row1 | 0 | 11:24:29完成前50条，13/50（26%）；阈值调查已完成，继续100 | 2371167；2b4a98cd-a13e-4051-b466-dfc60c25bce4 |
| row50 | 1 | 11:19:16正式100启动，11:25首条正常任务终止及产物检查通过 | 2533991；b6ed2008-54fb-4056-86a9-6264abdec918 |

共同host：is-dcfi2kjdq7g3k6aa-devmachine-0。row1 robot/policy PID2371250/2371251；row50为2534074/2534075。正式runner均PPID=1、独立session；sim/policy实际同卡，GPU0端口19300/19302、GPU1为19310/19312，缓存按卡隔离。只使用本机GPU0/1，未改动现有调度。

row1固定前50条比主历史93/100低67pp，辅助同seed历史46/50；失败首因第二块未移到中间26、重复按压6、有效按压后扰动第一块3、未按1、按压不足1。37个失败均正常到700步限制，0runtime_error/候选拒绝，1080query与50个scheduler退出0核对通过。阈值调查核对历史协议、继承metadata、前5条视频，并确认与同卡row30除预定selector外启动及实际metadata一致。26条主要失败均有效按压一次、第一块仍在目标垫、第二次放置始终未完成；同seed视频取样与诊断一致。未发现运行错误；保留为该配置下的实验退化，不据此证明唯一因果，不改配置或删除失败。

row20最终86/100，比主历史低7pp；失败为重复按压11、按压不足3。100连续成对seed、1555query、前5视频、metadata/source和全部进程退出核验通过。详细时序及失败记录见最终JSON。

row50 smoke门禁全检查通过（0/2为正常任务失败，不计正式成绩）。正式真实模型/norm加载及完整smoke身份检查通过；首条700步后button_not_pressed，24query/700帧视频/退出0通过。index49/row50始终标明模型预测未执行关系，terminal后无下一query；证据边界沿用已验收bc842036，不冒充独立RPC抓包。

冻结workspace：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4。

本轮HEAD/clean与启动source hash核对通过，完整哈希见JSON。旧评测场景仍为demo_clean_eval；新训练/转换数据要求demo_clean_state。主库新schema合入不改变本运行树。

证据均位于主RMBench真实目录；文件名相对于各行目录：

| run真实目录 | 必要证据 |
| --- | --- |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/ | final_review_0100.json；smoke_gate_summary.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/ | final_review_0100.json；smoke_gate_summary.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row1_100ep_seed0/ | midpoint_review_0050.json；protocol_review_0050.json；threshold_investigation_0050.json；threshold_video_seed100001.jpg |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row50_100ep_seed0/ | startup_verification.json；progress_check_0001.json；config.yaml中的smoke_verification引用 |

各run的config.yaml、command.txt、checkpoint_metadata/、processes.jsonl保留完整来源与启动命令。主历史仍为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/的93/100。旧巡检与smoke细节引用JSON及历史publication 210f7374dc3951cbafbe38a211ff0b3a5414f654、32f98d85ef284180aced2dfb5c24b28b58ae781a。

清理：row30、row20原smoke目录已删除，row30旧压缩包也已删除；仅保留正式metadata门禁结论与原检查摘要。row20未创建压缩包。活跃row1/row50引用的smoke继续保留，完成后同样处理；workspace保留。

下一检查12:15，两路按稳定吞吐更新ETA，不重复聚合未到事件的成绩。row1最近10条完整无视频周期均值103.965秒、34.63条/小时，100条预计12:51，窗口12:40—13:05。row50以自身smoke无视频周期109.007秒和首条冷启动/video给出50条初估13:00、窗口12:45—13:15，12:15再修正。之后按约小时和50/100事件检查；完成100后核验、清理、archive job。

所有调用本树的正式进程结束后，再更新实验README并交付commit；最后补README_memory_schema.zh-CN.md导航链接，不复制正文，不在当前运行树合入新schema代码。
