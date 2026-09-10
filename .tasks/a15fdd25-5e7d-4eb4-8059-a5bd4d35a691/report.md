task_revision: 364aca46d7f387d9efdc658f8a7271bad45d563d

2026-09-10 13:01 +08:00 事件简报：row1已完成21/100，最终核验、smoke清理与job归档完成，GPU0退出检查通过，可交Carver任务35c9e781。row50/GPU1中点19/50，已完成超过10pp的调查，未发现协议或基础设施异常，原run继续完整100。三树源码、配置和实验README保持冻结。

| run（H50/K30） | GPU | 状态/结果 | 正式runner PID；MAM job |
| --- | ---: | --- | --- |
| row30 | 0 | 92/100已验收；清理/归档完成 | 1933083（已退出）；a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 | 1 | 86/100已验收；清理/归档完成 | 2227400（已退出）；d358726f-3671-42d9-b3ac-801f15ddcdb7 |
| row1 | 0 | 12:55:46完成21/100；最终核验、smoke清理、job归档完成 | 2371167（已退出）；2b4a98cd-a13e-4051-b466-dfc60c25bce4 |
| row50 | 1 | 12:59:36完成前50条，19/50（38%）；阈值调查完成，继续100 | 2533991；b6ed2008-54fb-4056-86a9-6264abdec918 |

row1最终比主历史93/100低72pp。失败首因第二块未移到中间50、重复按压16、有效按压后扰动第一块6、未按4、按压不足3；79个失败均正常到700步限制。100个连续成对seed、2209query、前5视频、metadata/source及全部进程退出核验通过，0候选拒绝/运行错误；保留已接受中点调查对应的配置退化，不改配置或删除失败。整体耗时11700.692秒，95个无视频完整周期平均107.982秒，详细时序见最终JSON。

GPU0释放检查于12:57:41通过：全部已知row1自有PID（含历史进程树后代）已退出，本任务worktree/GPU0进程扫描为空，GPU0无计算进程，19300/19302无监听，快照12MiB/0%。可交35c9e781-7d2e-49a1-bb4c-25d77b865b3a（Carver）做用户追加BF16转存100rollout；不再交e690，本任务不再使用GPU0。没有替Carver启动新任务。

row50固定前50条比主历史低55pp，辅助同seed历史46/50。失败首因未按按钮29、第二块未移到中间1、按压不足1。31个失败均正常到700步限制；1008query/50个scheduler退出0、前5视频与成对seed检查通过，0候选拒绝/运行错误。调查确认与同卡row20除预定selector外启动配置、robot/policy metadata及checkpoint身份一致；全部字段按index49/row50读取模型预测未执行行。29条未按按钮均press_count0，其中24条第二块终态已在中间，但无有效按压。未发现协议/基础设施异常，按该配置下的正常任务失败保留，不据此证明唯一因果。

唯一活跃正式run为row50，host is-dcfi2kjdq7g3k6aa-devmachine-0，robot/policy PID2534074/2534075；GPU1端口19310/19312和gpu1缓存保持原值。workspace保留：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4。

本轮HEAD/clean及正式/smoke身份检查通过，完整source hash见JSON。旧评测仍为demo_clean_eval；新训练/转换数据要求demo_clean_state，未合入主库新schema改动。

证据均位于主RMBench真实目录；文件名相对于各行目录：

| run真实目录 | 必要证据 |
| --- | --- |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/ | final_review_0100.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/ | final_review_0100.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row1_100ep_seed0/ | final_review_0100.json；gpu0_handoff_verification.json；smoke_gate_summary.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row50_100ep_seed0/ | midpoint_review_0050.json；protocol_review_0050.json；threshold_investigation_0050.json |

各run的config.yaml、command.txt、checkpoint_metadata/、processes.jsonl保留完整来源和可复制命令。主历史基线仍为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/的93/100。旧巡检与逐query细节引用现有JSON及历史publication，不重复展开。

row30/row20/row1被正式替代的smoke均已清理，仅保留正式metadata门禁与原检查摘要，无整包归档；活跃row50引用的smoke继续保留。下一巡检13:55；row50最近10个完整无视频周期平均102.653秒、35.07条/小时，预计14:25完成100，窗口14:15—14:40。完成后核验结果/失败/时序/metadata/视频/trace及退出，清理smoke、archive job，再更新实验README并交付最终文档commit。最终README补README_memory_schema.zh-CN.md导航链接，不复制正文；当前不改文档或源码。
