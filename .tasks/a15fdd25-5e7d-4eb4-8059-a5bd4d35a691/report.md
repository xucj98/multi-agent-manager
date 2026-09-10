task_revision: eebd4b82e23caebe3886e3749f879f0e83348845

完成与剩余：

Manager已接受row30/GPU0的45/50人工中点，并于08:15释放GPU1。已完成row20/GPU1独立2rollout smoke的全部产物/source/视频/时序/退出检查，于2026-09-10 08:23:48 +08:00直接启动同卡正式100并登记MAM job；真实服务metadata握手及原完整smoke兼容性检查通过，首条episode检查已完成。两路正式进程继续运行，尚未完成各自100，不归档活跃job。未修改任何运行源码、配置或实验README。

冻结workspace与实际commit：

/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- OpenPI：58d6f2155acc3af03017677bb3f536101e6699f4。

三库在08:30检查仍为上述HEAD且git status干净。RMBench source_content_sha256为2708a5b2e349a8b4d4b1d0857f781fff236b0e392d9cb7294d2f1773c7bf2a29，bridge为cc79d3bd6130ada19ab1631fced4b6e34c71d34ed587123250089d664251b1b8；与row30/row20 smoke和实际正式metadata一致。运行期间只写ignored run分析产物与本MAM report，不合入后续live/new-wire，不重建或删除workspace。

当前进程与MAM job：

共同host：is-dcfi2kjdq7g3k6aa-devmachine-0。两路runner均PPID=1，各自独立session；每run完整100始终同一GPU串行，sim/policy共用该卡。

| run | GPU | 正式启动时间（+08:00） | runner PID | robot / policy PID | MAM job |
| --- | ---: | --- | ---: | --- | --- |
| row30 H50 K30 | 0 | 2026-09-10 06:52:04 | 1933083 | 1933452 / 1933453 | a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 H50 K30 | 1 | 2026-09-10 08:23:48 | 2227400 | 2227483 / 2227484 | d358726f-3671-42d9-b3ac-801f15ddcdb7 |

08:30核对两路runner/robot/policy均存活。GPU0端口19300/19302，GPU1端口19310/19312；Warp缓存为本worktree .local/warp-cache/memory_chunk_20260910/f0/gpu{0,1}/{robot,policy}。已读取GPU1实际进程environ确认CUDA_VISIBLE_DEVICES=1、SAPIEN_RENDER_DEVICE=cuda:0、policy显存比例0.40。GPU1 smoke和正式启动前均1 MiB/0%，没有旧计算进程；不使用其他GPU或远端。

真实产物目录：

- row30正式：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/
- row20正式：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/
- row20 smoke：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_smoke_20260910/
- row30已验收smoke：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_smoke_20260910/

所有目录均为共享主RMBench真实位置，worktree的eval_result软链接只提供访问入口。每run保留config.yaml、command.txt、checkpoint_metadata/、processes.jsonl、episode_diagnostics.jsonl、video_checks.jsonl及进程日志。两个正式run仍依赖各自smoke门禁，暂不清理这些证据。

row20/GPU1 smoke检查：

08:17启动，runner PID2214784、robot/policy PID2214865/2214866。08:22:55完成第二条，08:23完整检查通过，smoke及其所有子进程已退出。正式入口前再次执行原--check-smoke，未放宽任何recorder/config/source检查。

- accepted episode0/1，seed100000/100001；结果2/2，仅为smoke，不进入正式成绩。
- episode0为video：391 logical steps、14query，末chunk actual_k1，row20 was_executed=false；episode1无video：418步、14query，末chunk actual_k28，row20 was_executed=true。两集terminal next_query=false。
- 28个query按episode/query_id取最后状态，核对K30、index19/row20、三个字段raw argmax、one-hot、before/after连续性与step增量，全部通过。
- MP4逐帧解码391帧，240×320×3；episode1.mp4不存在，runner两条video检查均ok。
- 两个scheduler returncode0；robot/policy由runner_shutdown正常SIGTERM收尾（-15），无遗留进程或端口占用。
- 旧checkpoint/norm实际加载成功，H50、legacy字段、demo_clean_eval和instruction_generation_num100一致，未注入memory_config。
- smoke config SHA-256：4b6d66b2c6ad1cf160109578e0a7e0d54dc85af68839dc060105526d4f614714。

证据位于row20 smoke目录的smoke_verification.json、video_metadata_verification.json、memory_traces_final.jsonl；verify_smoke.py为只读日志的离线分析脚本，位于ignored run，未添加运行核心诊断。terminal真实infer边界依照固定bc842036、独立review dc14d105b1928c280270e0ec304d2b1d74bc9d7a及已验收smoke；本次完整trace检查没有冒充独立无损RPC抓包。

row20/GPU1正式首条：

已先核对固定commit信息、diff摘要和干净状态，使用以下直接命令：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 20 --gpu 1 --mode smoke --detach
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 20 --gpu 1 --check-smoke
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 20 --gpu 1 --mode formal --detach
mam job add a15fdd25-5e7d-4eb4-8059-a5bd4d35a691 --note 'F0 row20 H50 K30 正式100 GPU1；匹配2rollout smoke全检查通过，冻结f022bad/bc842036/58d6f21；与row30/GPU0并行' --host is-dcfi2kjdq7g3k6aa-devmachine-0 --pid 2227400
```

以上已执行，不应再次启动当前row20。formal启动前原smoke产物检查通过，真实robot/policy metadata握手后通过完整assert_smoke_compatible并进入首条。

episode0/seed100000于08:29:33.673终止：Fail、button_press_insufficient、700步step_limit_reached，无runtime_error；24query，最后actual_k10，index19/row20、was_executed=false、next_query=false，反馈连续性通过。scheduler PID2231566正常退出0，700帧视频逐帧可读。证据为row20正式目录progress_check_0001.json。

该正式首条与smoke首条结果不同，已保留原始事实；没有因此改配置、删episode或推断总体成绩。完整source/metadata一致，日志未见运行异常；旧Orbax INFO后已正常恢复模型，policy_hz默认20被checkpoint fps50覆盖符合旧协议。首次加载/video不代表稳定吞吐。

row30/GPU0保留的人工中点结论：

08:00:14完成41/100，最近10条完整周期平均84.590秒，约42.56条/小时；未在50前反复汇总成绩。第50条实际于08:12:39.242完成，与08:00估计08:12:40一致。Manager已接受中点报告e95ef21cc91ccb144b847c13725576c52bfe2d2e。

- 固定episode0—49、seed100000—100049，45/50（90%），比历史93/100低3个百分点，未触发超过10个百分点主阈值。同seed历史前50为46/50，仅作辅助。
- 失败首因为button_press_insufficient四条（seed100000/100029/100040/100047）、button_not_pressed一条（seed100005）；均700步step_limit_reached、press_count0，无runtime_error。
- 50个scheduler退出0；753query（703个完整K30、50个terminal partial）的index29/row30、字段反馈、step增量与终止trace问题列表为空。
- checkpoint和训练/转换metadata与历史一致，source冻结；相机快照D435/LargeView差异已由同一初始化覆盖逻辑解释，无证据表明实际协议更换。
- 证据为row30正式目录midpoint_review_0050.json、protocol_review_0050.json、progress_check_20260910_080014.json；其余早期检查文件保留。没有在本次GPU1开跑阶段重新统计row30成绩。

主历史基线仍为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/的93/100，不用另一份bridge92/100替代。

下一检查与剩余责任：

- 2026-09-10 09:10 +08:00计划巡检两路进度/吞吐/进程，GPU0原计划不变。row30上次中点外推100条中心09:24:32、窗口09:20—09:35，需届时按双卡并行后的实际吞吐修正。
- row20的50条初估窗口09:45—10:05（中心约09:50—10:00）。依据同GPU smoke无视频完整周期97.494秒、正式首条冷启动/video约5分46秒，后续4条video耗时尚未知；09:10用正式稳定周期修正。不到50不重复查成功率，到50固定前50条人工比较历史93/100及辅助同seed first50，记录首因和协议/基础设施边界。
- 后续只按约小时巡检及50/完成事件检查，不新建常驻队列。首条/短smoke事件等待均已退出。
- 各run完成100后核对结果、失败分布、时序及退出，先记录和处理临时产物，再archive对应job。两路活跃job当前不归档。
- 余下row1/50按GPU0/1空闲顺序执行，每row使用自身实际GPU/端口/配置匹配的2rollout smoke，完整检查通过后直接正式100；授权已发布，不再次请求许可。每run不拆卡，源码/配置/README持续冻结，workspace保留。

旧评测继续固定demo_clean_eval；新训练/转换数据必须有demo_clean_state来源证据，不能fallback到缺metadata/详细子任务标注的demo_clean。该新数据要求不改变本次旧checkpoint的评测场景。
