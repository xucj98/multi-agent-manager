task_revision: 51b7f02d2330dbfd132eaca201c6959348ce43ba

2026-09-10 10:42:45 +08:00 既定巡检：row20/GPU1为83/100，row1/GPU0为26/100，两路继续。未汇总row1成功率，未重算row20中点后的成绩。源码、配置和实验README保持冻结。

| run（均H50/K30） | GPU | 状态/结果 | 正式runner PID；MAM job |
| --- | ---: | --- | --- |
| row30 | 0 | 已完成92/100并验收，job已归档，smoke清理完成 | 1933083（已退出）；a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 | 1 | 83/100；已接受中点44/50，原run继续；预计11:07完成100 | 2227400；d358726f-3671-42d9-b3ac-801f15ddcdb7 |
| row1 | 0 | 26/100；首条检查已通过，尚未汇总成功率；预计11:25到50 | 2371167；2b4a98cd-a13e-4051-b466-dfc60c25bce4 |
| row50 | 1 | 未启动；row20收尾后自身smoke2→完整检查→正式100，已有授权 | — |

共同host：is-dcfi2kjdq7g3k6aa-devmachine-0。row20 robot/policy/sim worker PID为2227483/2227484/2227611，row1为2371250/2371251/2371378；两runner均PPID=1、独立session。实际服务进程存活，19300/19302与19310/19312分别由对应robot/policy监听，CUDA和缓存按GPU0/1隔离。本任务继续只用0/1。

row20与row1已完成的83/26个scheduler全部退出0；均无runtime_error、候选拒绝或日志Traceback/ERROR/连接故障。快照时row20正在第84条query，row1处于两集间reset/preflight阶段。完整正式/smoke配置、recorder及metadata身份仍相同。GPU0/1显存与进程快照见JSON，未干预进程。

最近10个完整无视频周期（含reset/preflight）：row20均值90.791秒、39.65条/小时，100条预计11:07:20，窗口11:00—11:15；row1均值107.997秒、33.33条/小时，50条预计11:25:18，窗口11:20—11:35。

冻结workspace：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4。

本轮三树HEAD/clean已查，RMBench/bridge重新计算source hash与smoke、正式metadata一致。旧评测固定demo_clean_eval；新训练/转换数据必须demo_clean_state。workspace保留。

证据均在主RMBench真实目录；表内文件名相对于各行目录：

| run真实目录 | 必要证据 |
| --- | --- |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/ | final_review_0100.json；smoke_gate_summary.json；smoke_cleanup_receipt.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/ | progress_check_20260910_104245.json；midpoint_review_0050.json；protocol_review_0050.json |
| /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row1_100ep_seed0/ | progress_check_20260910_104245.json；progress_check_0001.json；config.yaml中的smoke_verification引用 |

启动与来源见各run的config.yaml、command.txt、checkpoint_metadata/、processes.jsonl；逐query和smoke细节引用现有JSON。此前阶段publication为05e2a95b621ca6f04ba002cb06bab549041b8394。主历史93/100仍为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/；同seed前50仅辅助。

清理：row30原smoke目录及row30_smoke_evidence.tar.gz已删除，正式metadata门禁结论和原检查摘要保留。row1/row20活跃run引用的smoke继续保留；后续完成run按同一边界只留结论/摘要后清理，不整包归档。

下一事件：约11:07处理row20完成100，核对结果/失败分布/时序/视频/退出，清理并archive job后在GPU1接row50匹配smoke2→正式100并登记job、检查首条；约11:25做row1固定前50条人工中点。若提前出现完成或异常则按事件处理；其余维持约小时巡检，不频繁查询。全部调用本树的正式进程结束后再更新实验README并交付commit。
