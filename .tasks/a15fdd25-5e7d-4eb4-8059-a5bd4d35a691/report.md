task_revision: 51b7f02d2330dbfd132eaca201c6959348ce43ba

2026-09-10 09:54 +08:00 阶段简报。row30最终已验收收尾；row1/GPU0通过匹配smoke后已正式启动并完成首条核查，row20/GPU1继续，随后GPU1接row50。运行源码、配置和实验README保持冻结。

| run（均H50/K30） | GPU | 当前状态/结果 | 正式runner PID；MAM job |
| --- | ---: | --- | --- |
| row30 | 0 | 09:29完成92/100；相对主历史93/100为-1个百分点，Manager已接受，job已归档 | 1933083（已退出）；a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 | 1 | 09:51:50完成前50条，人工中点44/50（88%），比主历史低5pp，未触发阈值；原run继续 | 2227400；d358726f-3671-42d9-b3ac-801f15ddcdb7 |
| row1 | 0 | 09:40:46正式启动；09:47首条核查通过，正常任务失败button_not_pressed，无runtime_error | 2371167；2b4a98cd-a13e-4051-b466-dfc60c25bce4 |
| row50 | 1 | 尚未启动；row20收尾后执行自身2rollout smoke→完整检查→正式100，已有授权 | — |

共同host：is-dcfi2kjdq7g3k6aa-devmachine-0。row20 robot/policy PID2227483/2227484，row1为2371250/2371251；两runner均PPID=1、独立session。端口GPU0为19300/19302，GPU1为19310/19312，实际sim/policy同卡、缓存按卡隔离。row1真实模型/norm加载和完整smoke/config/source身份核对通过；首条24query、700帧视频及scheduler退出0通过。smoke成绩不进入正式汇总。

冻结workspace：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4。

09:50三树HEAD/clean及两路正式/smoke metadata核对通过，source hash见各run JSON。旧评测固定demo_clean_eval；新训练/转换数据必须demo_clean_state。未修改进程或运行来源，workspace保留。

证据统一位于主RMBench真实目录，以下文件名均相对于各行目录；逐query、smoke与旧巡检细节不在本简报重复：

| run真实目录 | 必要证据 |
| --- | --- |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/ | final_review_0100.json；smoke_gate_summary.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/ | midpoint_review_0050.json；protocol_review_0050.json；progress_check_0001.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row1_100ep_seed0/ | progress_check_0001.json；config.yaml中的smoke_verification引用对应smoke的smoke_verification.json、video_metadata_verification.json |

每run的config.yaml、command.txt、checkpoint_metadata/及processes.jsonl保留启动与来源证据。主历史基线为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/的93/100；同seed前50仅辅助。旧详细report保留于publication 6c80a55924885491bb7a2a3db5116ec6544c4ee5。

清理：row30原smoke目录与row30_smoke_evidence.tar.gz均已删除，只保留正式metadata门禁结论和原检查摘要，receipt已注明。其job旧归档note描述的是压缩包删除前状态，当前以receipt为准。row1/row20活跃run引用的smoke保留；后续完成run同样只留结论/摘要后清理，不整包归档。

row20人工中点：固定episode0—49、seed100000—100049，44/50；辅助同seed历史46/50。失败首因重复按压5、按压不足1；764query/50个scheduler退出0，0候选拒绝、0runtime_error，协议与继承metadata核查通过。最近10条平均85.984秒、41.87条/小时，预计100条11:03（窗口10:55—11:15）。

下一事件：10:40巡检两路并用稳定吞吐修正ETA；row20约11:03完成后核查收尾并在GPU1接row50匹配smoke→100。row1约11:10—11:40到50，初估中心11:25。之后按约小时和50/100事件检查，100完成时核对结果/失败分布/时序/视频/退出并清理、archive job；全部调用本树的正式进程结束后再更新实验README和交付commit。
