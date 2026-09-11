## 已验收后的临时文档树清理

Manager已验收两份正式100及台账f2ec2cf，并ff主RMBench。已核对主xcj-dev包含该提交、额外文档树干净，删除本task的RMBench-ledger临时worktree及codex/e6908de7-ledger分支。原RMBench/robot-bridge/openpi三个运行树及冻结SHA不变，四个失败run及各自smoke/诊断证据均保留。上文额外文档worktree路径仅作交付历史，不再存在。

C的69/100对照基线已获批准；RPC问题交Aquinas/task378da0ac。后续eval等待C准入与公共故障修复裁定，不自行重试四失败或接续GPU任务。

# 2026-09-11 11:38 本机正式评测阶段收尾

14项仿真队列当前：**2份完整100已验收、4份基础设施失败已归档、8项尚未启动、0项运行**。本task无活跃GPU进程；GPU3/4/5/6/7各自退出时已核对显存释放与端口无监听。没有重复启动已有run，也未改变失败项timeout/seed/参数。

## 已完成正式结果

| 模型 / train seed | 前50检查 | 正式100 | 失败边界 | 正式目录 |
| --- | --- | --- | --- | --- |
| put-back full t+1 / seed0 | 35/50，检查通过 | **69/100（69%）** | 31正常任务失败；0 runtime_error | put_back_full_t_plus_1_s0_20k_100ep |
| rearrange full t+30 / seed1 | 45/50，检查通过 | **92/100（92%）** | 8正常任务失败；0 runtime_error | rearrange_full_t_plus_30_s1_20k_100ep |

真实结果根：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/`。

两项均按episode0–99/seed100000–100099原顺序完整执行；各有100份episode JSON、100条视频检查，前5集视频完整解码、其余无视频。config_source里的audit/manifest逐字节继承一致，100个scheduler exit0，policy/robot正常shutdown -15，全部登记子进程退出。`midpoint_review.json`保存逐query最终trace/反馈行检查；`final_review.json`保存最终验收与清理事实；`launch.json`、`command.txt`、`config.yaml`和checkpoint_metadata保存实际命令与来源。无匹配旧20k训练/config基准，不强行与旧F0算10pp偏差；两份完成结果也不是同任务/seed配对，不能推导Q2目标差异。

put-back正常失败：button_not_pressed_after_center18、button_press_insufficient13；五视频帧数500/500/359/444/355。GPU5收尾1MiB/0%，19450/19452无监听，job a58e56cc-2281-4d88-89af-53bdee13a768已归档。
rearrange正常失败：button_not_pressed3、button_press_insufficient4、block2_not_moved_to_middle1；五视频392/406/411/402/385帧。GPU7收尾1MiB/0%，19470/19472无监听，job48930d29-9e3c-430c-8f8a-e93671f08333已归档。

已清理这两份完成run对应的自有smoke及GPU5/7 Warp缓存；正式目录保留smoke_verification摘要与全部正式结果。其它失败smoke/原始证据保留用于公共故障诊断。CPU准备输入/dry-run仍供剩余队列复用，未写checkpoint；不新增持久缓存/API。

## 稳定实验台账提交

仅文档分支 `codex/e6908de7-ledger`，从主库6139577建立未安装环境的临时worktree：
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`。

- `66f0a255a8c7878816ae1db1a42985f8990b3e04`：登记69/100完整基线、四失败边界、各模型真实状态及C对照入口。
- `f2ec2cfe14d4a721a12d19ae9971af5c0e1777ff`：补rearrange seed1正式92/100与全部运行收尾。

只改 `experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`。新增结果链接与CPU准备证据已核对，diff-check通过，文档树干净；可由Manager将以上两commit合入主库。没有将文档合入运行树改变source身份。原三个任务环境保留复用。

## 集群C对照基线交接

提名已收尾put-back full t+1训练seed0，**69/100**；31条均为正常任务失败，不因基础设施错误缺失episode。C准入的≤5pp对应64–74/100，须新环境自身smoke后完整100，不能复用已清理的本机smoke。

运行冻结SHA（不是上述文档提交）：
- RMBench `3e69b1e665a8eac0104d261b233f1b3339007e00`
- robot-bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`
- openpi `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`

Checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000`，完整params/assets/metadata只读使用。
训练原始数据：`/mnt/public/xcj/Projects/RMBench/data/put_back_block/demo_clean_state`；转换集：`/mnt/public/xcj/cache/huggingface/lerobot/put_back_block_demo_clean_state_shared_memory`。
实际评测为在线仿真put_back_block/demo_clean_eval，eval seed0、100000–100099，H50/K30、full last_executed、500步上限、instruction_generation_num100、前5集视频。

原命令/cwd在该正式run的launch.json，展开服务命令在command.txt。沿现有run_memory_schema_eval.py：variant put_back_full_t_plus_1，指定上述checkpoint、独立run名和分配GPU，prepare-audit→自身smoke2（video/no-video各1集）→引用自身smoke的formal100。
资源：单卡串行、sim/policy同卡；原A100、XLA_PYTHON_CLIENT_MEM_FRACTION=0.4；两独立端口、可写结果/临时Warp缓存、三库环境、RMBench共享assets及机器人/渲染资源、PaliGemma tokenizer缓存。4090显存配置需由其自身smoke确认，不能预设0.4足够。无需重训或复制全部训练原始数据用于在线rollout，但须保留checkpoint完整溯源及所需仿真资源。

## 四个基础设施失败与裁定需求

| run（均后缀_20k_100ep） | 正常完成条数 | 首次异常episode/seed | 结束CST | job（已归档） |
| --- | ---: | --- | --- | --- |
| put_back_full_t_plus_30_s0 | 16 | 16 / 100016 | 08:23:34 | 1803ad5f-b94a-4b64-bdc1-2c7f8ed9339c |
| rearrange_full_t_plus_1_s1 | 17 | 17 / 100017 | 08:45:35 | 7a618537-3350-45cc-bb45-d3d8fe62f722 |
| rearrange_full_t_plus_30_s0 | 32 | 32 / 100032 | 08:45:37 | 1e72397f-0602-4018-bc7c-4e112ad7501a |
| rearrange_full_t_plus_1_s0 | 67 | 67 / 100067 | 09:50:04 | af7dd7c9-682c-4a78-9e6e-946cbf47672f |

各run另含一条异常记录，不是完整100，未用不完整分母给正式分数。均在某集第一次get_obs、logical_step0遇到30秒transport超时；前三项runner报robot_status_transport_error，最后项报scheduler_exited_before_terminal，scheduler底层同为TimeoutError。原trace/metadata/视频/全部记录和smoke保留，各目录failure_review.json记录退出及GPU释放。GPU3与GPU6故障仅差2秒，跨模型/seed/卡，不能归因于某一target目标；慢首帧与底层卡死的根因尚未证实。

公共代码证据（bridge8ea）：benchmark/runner.py:418外层状态RPC timeout=30、430–434失败即终止；scheduler/base.py:120–121使用WebSocketClient默认30秒（transport/websocket.py:113）；robot/controllers/rmbench_simulation.py:129–131同一锁串行worker RPC，本次内部rpc_timeout=600。首次get_obs可使状态查询等待同一锁，存在内外有界预算不匹配的可能，但不是已证实根因。

最小建议：公共owner先确认首次get_obs慢/阻塞点，若证实预算问题，在既有RPC边界协调有界timeout；不改memory/动作协议、不全局无界等待、不另建runner。失败项如何重试/形成完整100由Manager裁定。本task没有修改公共源码或参数绕过门禁。此前一次进度快照只看episode_status漏报GPU3 runtime错误，已在efc7b696报告更正；后续始终同时读取runtime_error、summary与MAM退出状态。

## 后续队列与暂停边界

8项尚未GPU启动：put-back seed1 t+1/t+30、rearrange seed2 t+1/t+30、put-back seed2 t+1/t+30、rearrange serial_lag30 seed0/no_memory seed0。其中put-back seed2两项尚待最终20k/owner CPU交接；其它已完成CPU audit、smoke dry、formal dry。共12/14模型CPU已准备。

已读集群C迁移新条款：C未准入前不自行启动C正式run，已启动本机run均原位收尾；后续新eval在C准入与根README/workspace要求发布后优先排C。当前无可等待的活跃job；等待C准入及四失败的公共处置/重试裁定，未自行接续空卡新任务。任务整体14模型队列尚未完成，不标记全任务完成。
