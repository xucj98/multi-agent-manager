task_revision: 8f84e935ffe4bcd6e850306308f37a6da0edcffc

2026-09-10 12:17:27 +08:00 既定巡检：row1/GPU0为78/100，row50/GPU1为26/100，均正常继续。本轮未到新的50/100事件，没有重算成绩；Manager已接受row1中点调查，保持原配置。三树源码、配置和实验README继续冻结。

| run（H50/K30） | GPU | 当前状态/结果 | 正式runner PID；MAM job |
| --- | ---: | --- | --- |
| row30 | 0 | 92/100已验收；smoke清理、job归档完成 | 1933083（已退出）；a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 | 1 | 86/100已验收；smoke清理、job归档完成 | 2227400（已退出）；d358726f-3671-42d9-b3ac-801f15ddcdb7 |
| row1 | 0 | 78/100；已接受中点13/50及阈值调查；预计12:58完成100 | 2371167；2b4a98cd-a13e-4051-b466-dfc60c25bce4 |
| row50 | 1 | 26/100；首条检查已通过，尚未汇总成功率；预计12:57到50 | 2533991；b6ed2008-54fb-4056-86a9-6264abdec918 |

共同host：is-dcfi2kjdq7g3k6aa-devmachine-0。row1 robot/policy PID2371250/2371251，row50为2534074/2534075；runner均PPID=1、独立session。对应服务进程及监听端口正常（GPU0 19300/19302，GPU1 19310/19312），实际CUDA和缓存按卡隔离。自有进程树已保存，供完成时退出核验。

row1/row50已完成的78/26个scheduler全部退出0，均无runtime_error、候选拒绝、Traceback/ERROR/连接故障。快照时row1正在下一条query，row50处于两集间reset/preflight阶段。实际smoke与正式配置、recorder及metadata身份一致；未干预任何进程。

最近10个完整无视频周期（含reset/preflight）：row1平均114.398秒、31.47条/小时，100条预计12:57:50；row50平均100.655秒、35.77条/小时，50条预计12:57:29。两者估计窗口均12:50—13:10，替代上次粗估。

冻结workspace：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4。

本轮三树HEAD/clean核对通过，RMBench/bridge重新计算source hash与启动及smoke身份一致，完整值见JSON。旧评测仍固定demo_clean_eval；新训练/转换数据要求demo_clean_state，未合入主库新schema改动。

证据均在主RMBench真实目录；文件名相对于各行目录：

| run真实目录 | 必要证据 |
| --- | --- |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/ | final_review_0100.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/ | final_review_0100.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row1_100ep_seed0/ | progress_check_20260910_121727.json；midpoint_review_0050.json；threshold_investigation_0050.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row50_100ep_seed0/ | progress_check_20260910_121727.json；progress_check_0001.json；config.yaml中的smoke_verification引用 |

各run的config.yaml、command.txt、checkpoint_metadata/、processes.jsonl保留完整来源及启动命令。主历史基线仍为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/的93/100。详细中点调查、逐query与smoke结论引用现有JSON及已验收publication 697cb5257dbc0254d68fa22897c98afb1dca7c77，不重复展开。

下一事件检查12:55：row1接近100，完成后核对最终结果/失败/metadata/视频/trace，确认runner、服务、sim worker及自有后代全部退出，再清理被替代smoke、archive job。按Manager本轮指令，完成这些退出核验后GPU0交e690做新schema技术smoke及旧drawer offline；当前GPU0尚未释放，GPU1继续本任务row50。row50到50时做固定前50条人工比较及规定阈值调查。其余维持约小时和50/100事件检查，不频繁聚合成绩。

row30/row20 smoke已清理，仅保留正式门禁结论和原检查摘要；活跃row1/row50引用的smoke仍保留，后续完成时同样只留摘要、不整包归档。workspace保留。所有F0结束后才更新实验README并交付最终文档commit，补README_memory_schema.zh-CN.md导航链接，不复制正文。
