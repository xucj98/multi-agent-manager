task_revision: 03e23da22e39a090cb44d1f5956492560d6231a6

完成与剩余：

Manager已验收row30/GPU0 smoke，并一并授权F0四个run预算及同GPU后续各row的“匹配smoke→正式100”。已按冻结入口启动row30/GPU0正式100，登记真实host/PID的MAM job；真实服务metadata握手、原完整smoke兼容门禁、首条检查、08:00巡检和50条人工中点比较均完成。第50条于2026-09-10 08:12:39.242 +08:00终止，固定前50条为45/50（90%），相对历史93/100低3个百分点，未触发超过10个百分点的阈值。正式进程继续运行，未完成100条，不归档活跃job。

本轮08:00:14检查时已完成41/100，41个已完成scheduler均returncode0；当时只核对进度、吞吐和基础设施异常，未汇总成功率。随后准备基线和协议证据，使用短期文件事件等待第50条日志与scheduler退出落盘，于08:12:54完成固定前50条人工核查。该事件等待进程已自行退出，没有新增常驻监控或队列。runner/robot/policy于08:13仍正常存活，没有accepted runtime_error、Traceback、超时或连接故障；日志关键词只匹配启动时Orbax的一条INFO说明，之后未报加载异常。进程未干预，源码/文档未修改。GPU1仍由训练full/serial smoke及保存恢复准备占用，未释放、未使用；后续GPU0各row匹配smoke验收后可直接正式100，无需再次等待用户许可。

冻结workspace与实际代码：

继续使用 /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691 的三个独立worktree及环境，没有重建workspace。实际服务metadata确认：

- RMBench：f022badd11228e5763a301339a5d1fe5574962b4。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- OpenPI：58d6f2155acc3af03017677bb3f536101e6699f4。

启动前均干净，运行期间不改源码、配置或README，不合后续live/new-wire。中间记录只写ignored run目录和本MAM report。独立runtime review为dc14d105b1928c280270e0ec304d2b1d74bc9d7a；smoke验收依据为前版报告598cd4538b2b9ad293f4274bd01eb862029be53b及实际产物。

实际命令、进程与job：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --gpu 0 --mode formal --detach
```

- 正式启动时间：2026-09-10 06:52:04 +08:00。
- host：is-dcfi2kjdq7g3k6aa-devmachine-0。
- 真实runner PID：1933083，PPID=1，独立session，首条检查后仍在运行。
- MAM job：a19ad5c6-4449-41c3-a077-2d67e80c5286，已登记且状态running。
- robot/policy PID：1933452 / 1933453。首条scheduler PID1935794，已正常退出；后续episode由同一runner依次启动。
- 启动前GPU0为1 MiB/0%且无计算进程；sim/policy同用CUDA_VISIBLE_DEVICES=0，SAPIEN_RENDER_DEVICE=cuda:0，policy显存比例0.40。
- robot/policy端口19300/19302，Warp缓存固定在.local/warp-cache/memory_chunk_20260910/f0/gpu0/{robot,policy}，与本row已验收smoke一致。

已实际执行登记命令：

```bash
mam job add a15fdd25-5e7d-4eb4-8059-a5bd4d35a691 --note 'F0 row30 H50 K30 正式100 GPU0；冻结f022bad/bc842036/58d6f21，首条后报告预计50条检查时机' --host is-dcfi2kjdq7g3k6aa-devmachine-0 --pid 1933083
```

实际产物位置：

正式run：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/

本轮进度/吞吐记录：上述目录progress_check_20260910_080014.json。50条人工核查结果为midpoint_review_0050.json，协议比对证据为protocol_review_0050.json，一次性离线复算脚本为review_midpoint_0050.py（只读日志，位于ignored run内，不属于运行源码）。recorder的midpoint_checks.jsonl数值与人工复算一致；人工首因/协议/trace审查仍由本任务完成，不宣称runner自动执行人工检查。前次progress_check_20260910_072909.json与首条检查progress_check_0001.json继续保留。eval_result是共享主RMBench真实位置，不依赖临时worktree保存。

门禁引用的已验收smoke：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_smoke_20260910/。该smoke为1/2、video700帧/另一条无video，38个query检查通过；不以smoke成功率推断正式结果。唯一证据及活跃正式run的smoke依赖仍保留。

正式协议与source检查：

旧shared-full 30k checkpoint保持原字段、norm、模型、H50/K30，不注入memory_config。legacy_full_feedback_selector为index29，所有memory字段共同读取row30；旧场景demo_clean_eval，eval seed0、起始候选100000、instruction generation100，每run单GPU完整串行100条。正式继承已核实profile：前5条video，其余关闭。

新训练/转换数据来源要求仍是demo_clean_state，不能fallback到缺metadata/详细子任务标注的demo_clean；未因此修改旧评测场景。GPU1仅在训练50step smoke结束且Manager明确释放后，才可承接另一个完整run；每row必须使用自己实际GPU/端口/配置的两条smoke。

- 启动前--check-smoke产物/source预检通过，正式进程拿到真实robot/policy metadata后通过原完整assert_smoke_compatible并进入首条episode。
- smoke config SHA-256：a3533390e920e58dadb0fa6bd5697280638fd76e661f7ca4d0a675f13f051a67。
- RMBench source_content_sha256：2708a5b2e349a8b4d4b1d0857f781fff236b0e392d9cb7294d2f1773c7bf2a29。
- bridge source_content_sha256：cc79d3bd6130ada19ab1631fced4b6e34c71d34ed587123250089d664251b1b8。
- 首条完成后现算source与正式metadata保存值一致。没有放宽门禁或添加selector白名单。

首条检查结果：

- episode0 / seed100000，06:57:12终止，Fail：button_press_insufficient，700 logical steps；无accepted runtime_error。
- 24个query：前23个actual_k=30，最后actual_k=10；均index29/row30，terminal next_query=false。最后一行仍是未执行的模型预测，未偷换last_executed。
- episode0.mp4存在，runner视频检查ok、700帧。
- 首条scheduler returncode0，robot/policy与正式runner继续正常运行。
- 与验收smoke的首个seed表现一致，但不据此解释尚未完成的正式总体成功率。报告保留全部失败证据。

中点预计时机与后续责任：

08:00检查点已完成。本轮取最近10个无视频episode（episode_id 31—40）的完整完成周期，包含reset/preflight与实际执行：81.920/87.754/84.818/83.650/84.346/81.204/82.848/81.605/76.221/101.538秒，平均84.590秒、中位83.249秒，约42.56条/小时。最近完成时间07:59:58.316；按剩余9条外推，第50条中心估计08:12:40，窗口收敛为08:10—08:16 +08:00。与07:29估计基本一致，没有持续吞吐下降证据。

50条事件实际为08:12:39，与08:00估计一致。中点最近10个完整周期平均86.246秒，约41.74条/小时；按剩余50条估计100条完成中心为09:24:32，窗口09:20—09:35 +08:00。下一人工巡检计划为2026-09-10 09:10 +08:00，修正完成时机；随后在100条与退出事件收尾。只在约小时巡检和50/完成事件读取汇总，不频繁轮询。08:00的GPU0快照33433 MiB/0%位于episode切换间隔，瞬时利用率不作吞吐结论。三库HEAD在08:13仍为上述冻结版本且均干净。本轮未检查训练进度或GPU1。

中点主基线已定位并确认原始_result.txt为93/100：/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/。历史config记录相同checkpoint、demo_clean_eval、K30、eval seed0和前5条video；历史前50条seed为100000—100049。完整历史93/100是主比较，同seed前50仅作辅助，不以另一份bridge 92/100替代。

50条人工检查结论：

- 固定episode0—49、seed100000—100049，连续唯一且与历史前50条成对；50个accepted episode，无候选拒绝。45success、5failure；主比较90%对93%，差-3个百分点；辅助比较45/50对历史46/50，差-2个百分点。两项均不超过10个百分点，主阈值未触发。
- 失败首因为button_press_insufficient四条（seed100000/100029/100040/100047）、button_not_pressed一条（seed100005）。五条都以700步step_limit_reached正常结束，press_count=0、valid_press_reached_stage_1=false；属于记录到的任务按钮失败，无runtime_error或非零scheduler退出。不由这份中点结果单独归因于反馈行，也不为接近93而改协议或删除episode。
- 50个scheduler全部returncode0；按episode/query_id取最后状态共753个query。703个完整actual_k30，50个terminal partial，逐项核对K/step增量、index29/row30、三个字段raw argmax及before/after连续性、was_executed与terminal next_query=false，问题列表为空。trace不能冒充独立RPC抓包；真实terminal infer边界沿用已验收runtime review/smoke依据。
- checkpoint、任务场景、seed、K30、视频设置与历史配置一致；训练配置、key_state配置、source_data配置和转换命令与历史继承metadata逐字节一致。当前RMBench/bridge source hash与正式启动保存值一致，三库HEAD/clean符合冻结要求。
- 历史task_args的left_embodiment默认head camera记录为D435，而当前初始化后快照为LargeView；两版本envs/camera/camera.py内容完全相同，line55读取task camera类型、line186在创建相机前覆盖默认值，实际task camera均LargeView。当前task_args.eval_video_log=false反映第5条后的无视频模式，五条video协议未变；这些快照差异不构成协议漂移证据。

结论：保持原运行继续row30正式100；中点不触发阈值调查或干预。人工检查证据均已写主RMBench真实run路径和本report。

row30完成100后记录结果、失败分布、时序和完整source/命令，确认进程收尾再archive本job。GPU1释放前按GPU0依次处理row20/1/50，各自匹配两条smoke确认后直接正式100，不再次请求已授权scope的许可。源码与实验文档保持冻结，workspace不删除。
