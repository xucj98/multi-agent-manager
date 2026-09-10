task_revision: 51b7f02d2330dbfd132eaca201c6959348ce43ba

2026-09-10 11:11 +08:00 完成事件：row20最终86/100已完整核验、清理smoke并归档job；GPU1接续row50匹配smoke已启动（runner2522901），通过后直接正式100。row1/GPU0继续，50条前不汇总成功率。三树源码、配置和实验README保持冻结。

| run（均H50/K30） | GPU | 状态/结果 | 正式runner PID；MAM job |
| --- | ---: | --- | --- |
| row30 | 0 | 已完成92/100并验收，job已归档，smoke清理完成 | 1933083（已退出）；a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 | 1 | 11:09:21完成86/100，比主历史低7pp；核验/清理完成，job已归档 | 2227400（已退出）；d358726f-3671-42d9-b3ac-801f15ddcdb7 |
| row1 | 0 | 继续运行；最近10:42快照26/100，50条预计11:25，尚未汇总成功率 | 2371167；2b4a98cd-a13e-4051-b466-dfc60c25bce4 |
| row50 | 1 | 11:10:32匹配smoke2已启动，GPU1；检查通过直接100 | smoke2522901（短smoke无需job） |

共同host：is-dcfi2kjdq7g3k6aa-devmachine-0。row1正式runner2371167、robot/policy2371250/2371251仍运行；row20全部进程已退出。GPU1启动row50前为1MiB/0%、无计算进程，沿用19310/19312及gpu1缓存；GPU0继续row1。

row20最终86/100，失败首因重复按压11、按压不足3；连续成对100seed、0候选拒绝/运行错误，1555query、前5视频、metadata/source和全部子进程退出核验通过。耗时9933.112秒，整体36.24条/小时，95个无视频周期平均92.971秒。详细证据见最终JSON。row1下一50条事件原估11:25，尚未新增成绩统计。

冻结workspace：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4。

本轮三树HEAD/clean已查，RMBench/bridge重新计算source hash与smoke、正式metadata一致。旧评测固定demo_clean_eval；新训练/转换数据必须demo_clean_state。workspace保留。

证据均在主RMBench真实目录；表内文件名相对于各行目录：

| run真实目录 | 必要证据 |
| --- | --- |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/ | final_review_0100.json；smoke_gate_summary.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/ | final_review_0100.json；smoke_gate_summary.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row1_100ep_seed0/ | progress_check_20260910_104245.json；progress_check_0001.json；config.yaml中的smoke_verification引用 |

启动与来源见各run的config.yaml、command.txt、checkpoint_metadata/、processes.jsonl；逐query和smoke细节引用现有JSON。此前巡检publication为210f7374dc3951cbafbe38a211ff0b3a5414f654。主历史93/100仍为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/；同seed前50仅辅助。

清理：row30原smoke目录及row30_smoke_evidence.tar.gz已删除，正式metadata门禁结论和原检查摘要保留。row20 smoke也已按同一边界清理（32文件、672205字节，未创建压缩包）。row1活跃引用和正在运行的row50 smoke保留。

row50 smoke真实目录：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row50_smoke_20260910/；完整字段检查要求index49/row50，K<=30下was_executed=false，属于模型预测未执行行。

下一事件：row50 smoke两条video/no-video完成后全量核查，再正式100登记job并检查首条；row1约11:25做固定前50条人工中点。其余维持约小时和50/100事件巡检。全部调用本树的正式进程结束后再更新实验README并交付commit。
