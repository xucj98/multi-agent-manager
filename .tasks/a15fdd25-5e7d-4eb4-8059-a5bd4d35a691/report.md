task_revision: 03e23da22e39a090cb44d1f5956492560d6231a6

完成与剩余：

Manager已验收row30/GPU0 smoke，并一并授权F0四个run预算及同GPU后续各row的“匹配smoke→正式100”。已立即按冻结入口启动row30/GPU0正式100，登记真实host/PID的MAM job；真实服务metadata握手、原完整smoke兼容门禁与首条episode检查均完成。正式进程继续运行，尚未达到50条或100条，不归档活跃job。

本轮恢复检查时间为2026-09-10 08:00:14 +08:00：已完成41/100，正处于episode40结束到episode41启动的间隔，41个已完成scheduler均returncode0。不到50条，本轮只检查完成计数、耗时、进程和基础设施异常，不汇总成功率。runner/robot/policy正常存活，没有accepted runtime_error、Traceback、超时或连接故障；日志关键词只匹配启动时Orbax的一条INFO说明，之后未报加载异常。进程未干预，源码/文档未修改。GPU1仍由训练full/serial smoke及保存恢复准备占用，未释放、未使用；后续GPU0各row匹配smoke验收后可直接正式100，无需再次等待用户许可。

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

本轮进度/吞吐记录：上述目录progress_check_20260910_080014.json。前次progress_check_20260910_072909.json与首条检查progress_check_0001.json继续保留。config.yaml、command.txt、checkpoint_metadata/、processes.jsonl、episode_diagnostics.jsonl、video_checks.jsonl和各进程日志均已产生。eval_result是共享主RMBench真实位置，不依赖临时worktree保存。

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

下一检查为50条事件，预计2026-09-10 08:13 +08:00；届时一次性汇总固定前50条，核查主基线偏差和失败首因。不到50不重复汇总成绩，后续按约小时巡检与50/完成事件安排。GPU0本次快照为33433 MiB/0%，处于episode切换间隔，瞬时利用率不作吞吐结论。三库HEAD仍为上述冻结版本且均干净。本轮未检查训练进度或GPU1。

中点主基线已定位并确认原始_result.txt为93/100：/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/。历史config记录相同checkpoint、demo_clean_eval、K30、eval seed0和前5条video；历史前50条seed为100000—100049。完整历史93/100是主比较，同seed前50仅作辅助，不以另一份bridge 92/100替代。

达到50条时由实验负责人对历史93/100主基线检查绝对偏差是否超过10个百分点，同seed前50只作辅助；调查协议/基础设施和失败原因，区分反馈行实验效应与运行错误，不为接近93而改配置或丢弃不利episode。人工检查结论写run目录和本report。

row30完成100后记录结果、失败分布、时序和完整source/命令，确认进程收尾再archive本job。GPU1释放前按GPU0依次处理row20/1/50，各自匹配两条smoke确认后直接正式100，不再次请求已授权scope的许可。源码与实验文档保持冻结，workspace不删除。
