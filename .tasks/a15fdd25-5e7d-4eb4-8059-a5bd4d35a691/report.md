task_revision: 188839a5902c749273bce2d5dab32d7cba50687b

完成与未完成：

已按Manager明确放行，在首次新smoke前完成--gpu/端口/cache小调整并冻结全部入口、四份配置和README；随后在GPU0运行row30的一次2-rollout smoke，真实加载旧full、一次video/一次no-video、逐query时序、继承metadata、source身份和进程收尾检查完成。现有--check-smoke/官方validator通过，结果1/2。等待Manager验收并发正式100通知；本轮未运行任何100，GPU1没有使用。

独立runtime review为dc14d105b1928c280270e0ec304d2b1d74bc9d7a，Manager已确认review相关代码与bc842036同源零差异。本任务不修改runtime、模型或新增队列系统。辅助RPC观测有覆盖/丢包限制，详见“terminal infer证据边界”；没有将其冒称为两条episode全程无损计数。

workspace与实际source commits：

- 原workspace保留：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691，继续使用其中三个独立worktree与环境。
- RMBench：f022badd11228e5763a301339a5d1fe5574962b4（实验：按 GPU 隔离 F0 端口与缓存），在425afaf完整正式入口上完成4文件小改；修改仅限experiments/memory_chunk_20260910/，首个smoke前已提交。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b，未合后续live进度或新memory wire。
- OpenPI：58d6f2155acc3af03017677bb3f536101e6699f4，使用本任务editable；bridge轻量openpi-client仍指向同任务OpenPI。
- 上述三库commit均由本次真实服务metadata确认。smoke完成后三个worktree保持干净，没有为结果更新源码/配置/README。

实际命令与资源：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --gpu 0 --mode smoke --detach
```

启动前GPU0为1 MiB/0%，无计算进程，19300/19302端口空闲。仿真/policy同用CUDA_VISIBLE_DEVICES=0，SAPIEN_RENDER_DEVICE=cuda:0，policy显存比例0.40。robot/policy端口为19300/19302，Warp缓存为.local/warp-cache/memory_chunk_20260910/f0/gpu0/{robot,policy}。

--gpu默认0、可选0/1；GPU1派生端口19310/19312和独立gpu1缓存。GPU1仍须训练owner的50step smoke结束且Manager释放通知后使用；届时可承接另一完整100ep，不拆分单个run。每个row使用其实际GPU/端口/配置对应的两条smoke，新增预检拒绝跨GPU凭据，原完整recorder/source检查保留。

结果与真实产物路径：

主目录：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_smoke_20260910/

- benchmark状态completed、error=null，两条accepted episode，无accepted runtime error。
- episode0：seed100000，Fail，button_press_insufficient，700 logical steps。
- episode1：seed100001，Success，406 logical steps。
- 成功1/2；这是smoke产物，不纳入正式主表，也不能推断F0成功率。
- 视频：主目录episode0.mp4，522786 bytes；runner视频检查通过，另用CPU实际解码700帧（320×240）。episode1视频明确关闭且没有episode1.mp4。
- 主目录留存config.yaml、command.txt、scheduler.yaml、checkpoint_metadata/的9个继承文件、episode0/1.json、episode_diagnostics.jsonl、diagnostics_summary.json、video_checks.jsonl与processes.jsonl。
- 额外只在结果目录写入smoke_verification.json、memory_traces_final.jsonl、video_metadata_verification.json，以及辅助RPC观测JSONL；源码没有变化，产物不依赖临时workspace留存。

metadata与固定协议：

真实policy_dir为 /mnt/public/xcj/Projects/RMBench/policy/pi05/checkpoints/pi05_full_key_state/shared_memory_full_key_state_seed0/30000。policy metadata与实际模型配置均为H50，scheduler K30/index29，全部旧memory字段共同选row30，没有memory_config注入。checkpoint参数真实恢复日志为6.03秒，沿用checkpoint自己的norm stats、原字段/归一化/编码/解码。

旧P1场景保持demo_clean_eval，seed0、起始候选100000、instruction generation100。旧metadata的数据来源为demo_clean_state / rearrange_blocks_demo_clean_state_shared_memory。新训练/转换checkpoint仍必须证明来自demo_clean_state，不能用缺metadata/详细子任务标注的demo_clean替代；该约束没有改变旧checkpoint的评测场景。

逐query时序检查：

已从scheduler真实stdout中按episode/query_id合并多次状态日志，38个query全部通过检查：accepted、planned_k=30、source/observed logical step连续、actual_k等于真实advance、统一index29/row30、字段before等于上次after，phase/empty_mat_side/button_press_status的selected raw到after符合旧one-hot argmax投影。

| episode | query数 | 实际总步数 | 最后actual_k | 最后selected row | terminal next_query |
| --- | ---: | ---: | ---: | --- | --- |
| 0 | 24 | 700 | 10 | index29 / row30，was_executed=false | false |
| 1 | 14 | 406 | 16 | index29 / row30，was_executed=false | false |

其余36个完整chunk的actual_k均为30，was_executed=true。terminal partial chunk仍固定选择模型row30，不偷换为last_executed；它是未执行的模型预测，未读取未来GT，且没有下一query消费。H50由模型metadata确认，trace的model_rows_available=30是此selector需要保留的预测行数，不表示模型H降为30。

terminal infer证据边界：

- 已验收bc842036的最小None hook：simulation在terminal完成反馈/trace后返回None，公共循环立即跳过infer/execute。此前本任务CPU定向集合53 passed，完整run_iteration回归确认terminal只保留reset、真实infer调用计数0，robot只get_obs。
- 本次真实episode0最终trace为06:35:08.109，scheduler于06:35:08.110停止；episode1对应06:36:33.311和06:36:33.312。两者最终均next_query=false，无后续query trace。
- 未改runtime，使用只读loopback观测记录本任务19302端口的命令类型。第二条观测到14次infer，与14个query一致；terminal时间以后观察到0次infer，随后连接关闭。证据为policy_rpc_commands.jsonl。
- 该辅助采集开始于episode0结束后，且raw socket报告2821个kernel drops；更早的完整帧采集policy_rpc_observation.jsonl也有gap。因此没有独立、全程无损的两条episode网络infer计数，不能仅凭抓包缺席断言绝无调用。零终止infer的结论依赖已审固定代码/CPU回归与本次真实terminal trace；RPC记录仅作补充。限制已原样写入smoke_verification.json，没有隐藏或重复跑smoke补成绩。

官方验证与source身份：

已实际执行并通过：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --gpu 0 --check-smoke
```

- config SHA-256：a3533390e920e58dadb0fa6bd5697280638fd76e661f7ca4d0a675f13f051a67。
- RMBench source_content_sha256：2708a5b2e349a8b4d4b1d0857f781fff236b0e392d9cb7294d2f1773c7bf2a29。
- bridge source_content_sha256：cc79d3bd6130ada19ab1631fced4b6e34c71d34ed587123250089d664251b1b8。
- smoke前输出、真实metadata保存值、smoke后现算值一致。完整GPU/scheduler配置、bridge source和两条产物预检通过；正式runner还会在实际metadata握手后保留完整assert_smoke_compatible。
- 本次小改的静态验证：GPU0/1×四行×smoke/formal共16组dry-run通过；同卡同row两种模式只差模式、结果leaf和自身smoke引用。默认GPU0、GPU2拒绝、跨GPU smoke拒绝通过；ruff、format、bash -n、git diff --check通过。GPU1只做dry-run，没有占卡。runtime未改，独立review不因本次启动参数变化重做。

进程、吞吐与后续：

smoke由start_new_session启动，host=is-dcfi2kjdq7g3k6aa-devmachine-0，runner PID1893450。开始06:29:59、完成06:36:33 +08:00，约394秒；含模型加载、冷缓存、视频与初始化，粗算18.3条/小时，不作为正式100的吞吐承诺。

两个scheduler PID1897431/1909195均episode_terminal退出、returncode0；policy1893531与robot1893530由runner_shutdown发送SIGTERM收尾，returncode=-15为预期。runner已退出，两个只读观测进程也已退出；19300/19302无监听，GPU0恢复1 MiB/0%。短smoke未登记MAM job，当前没有本任务新长进程。

下一步等待Manager验收本smoke并通知正式阶段。获准后使用已冻结入口：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --gpu 0 --mode formal --detach
```

正式启动后立即按输出host/PID登记mam job，先检查服务和首条episode，接近50条前监控进度；第50条由实验负责人手动对固定历史93/100基线检查偏差，同seed first50为辅助，超过10个百分点调查协议/基础设施并记录，保留全部不利episode，不宣称runner自动完成人工调查。100条后核对退出与产物、archive job。后续row及GPU1按既有scope和Manager资源放行继续，每行先同卡同配置smoke。workspace保留，当前100和GPU1均未启动。
