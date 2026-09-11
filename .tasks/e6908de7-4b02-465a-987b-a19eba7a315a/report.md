# 09:51 第四项基础设施失败：GPU4 rearrange t+1 seed0停止于67条后

09:50:04，`rearrange_full_t_plus_1_s0_20k_100ep`完成67条正常episode（55 success/12正常失败）后，episode67/seed100067首次get_obs在logical_step0超时30秒，scheduler exit1。runner记录scheduler_exited_before_terminal（与先前三项外层失败标签不同，但scheduler栈仍为相同get_obs TimeoutError）。最终68条记录、benchmark failed，不能作为完整100结果；已完成的前50条诊断仍有效但仅作中检。

全部登记子进程退出，policy/robot正常shutdown -15，19440/19442无监听，GPU4=1MiB/81037MiB空闲/0%。failure_review.json、68条原始结果、trace、metadata、视频和smoke均保留，未重跑。公共证据为processes/069-scheduler.stdout.log；现已有4/6已启动formal因该起始RPC超时提前失败，剩余GPU5/7仍运行，GPU3/4/6保持空闲，不继续填充新任务。需公共owner处置及Manager裁定失败项重试规则，不能改timeout绕过门禁。三树源码继续冻结。

---

# 09:30 GPU5 put-back t+1 seed0前50条中检完成

`put_back_full_t_plus_1_s0_20k_100ep`前50条35 success/15正常失败（70%，仅中检，正式100继续）。失败原因button_not_pressed_after_center10、button_press_insufficient5。episode0–49与seed100000–100049严格顺序，无runtime_error，全部terminal、50个scheduler exit0。逐query最终trace记录684个实际执行query（635个K30、49个partial），1270个已记录字段更新均匹配last_executed行，无索引错配。正式目录`midpoint_review.json`保存检查摘要。

没有同新20k训练/config的旧基准，不用不同实验强行计算10个百分点偏差；保留全部正常失败，继续既定100不改参数。GPU4已过50中检，当前56条；GPU7 seed1当前23条，无runtime_error。GPU3/6继续空闲，三次公共RPC失败待处置；源码冻结、失败产物全部保留。

---

# 09:19 GPU4 rearrange t+1 seed0前50条中检完成

`rearrange_full_t_plus_1_s0_20k_100ep`前50条38 success/12正常任务失败（76%，仅中检，非正式100结果）。seed严格100000–100049，episode0–49顺序一致，无runtime_error，均terminal，50个scheduler exit0。正常失败为button_pressed_multiple_times4、block2_not_moved_to_middle4、button_press_insufficient2、button_not_pressed2；全部保留。

按每集query_id取最后trace检查：810个有实际执行的query，其中760个K30、50个partial；已有2280个字段反馈更新全部匹配last_executed索引，未见row/index错误。实际证据与检查摘要保存在正式目录`midpoint_review.json`。本新20k没有真正同训练/config的旧基准，不强行用F0做10个百分点对比；当前无须改协议/参数，按原固定100继续。

三个公共RPC失败仍待Manager裁定，GPU3/6暂留空；GPU4/5/7继续，三树冻结不merge台账。前述失败结果均保留，未补跑。下一关键检查为put-back t+1 seed0第50条及各run退出事件。

---

# 08:49 更正GPU3状态：与GPU6同时段出现第三次RPC失败

`rearrange_full_t_plus_1_s1_20k_100ep`于08:45:35失败，完成17条正常success后，episode17发生robot_status_transport_error 30秒超时，最终18条记录。与GPU6的08:45:37仅差两秒，发生在不同target变体，不能归因于t+30模型本身。此前08:45快照只读取episode_status.failure_reason，基础设施错误存储在其它诊断/runner字段，导致将18条记录误述为推进且无新增runtime错误；以本次summary及进程退出证据更正。后续监控同时核对benchmark状态/顶层runtime诊断，不只看episode_status。

全部登记子进程已退出，GPU3=1MiB/0%，19430/19432无监听。failure_review.json已保留，18条原记录与smoke不删除不重跑。GPU3和GPU6先留空，公共owner需结合同时段故障诊断；不改变现有源码/timeout。剩余GPU4 rearrange t+1 seed0、GPU5 put-back t+1 seed0、GPU7 rearrange t+30 seed1继续。三项失败均非完整100正式成绩。

---

# 08:47 第二次相同RPC失败：GPU6 rearrange t+30 seed0提前结束

08:45:37，`rearrange_full_t_plus_30_s0_20k_100ep`在完成32条正常episode（27 success、5正常失败）后，episode32/seed100032首个get_obs遇到30秒TimeoutError；runner同时报robot_status_transport_error，最终33条记录、benchmark failed。不是完整100，不能作为正式成功率。`processes/034-scheduler.stdout.log`、summary、33条原始记录和smoke均保留；`failure_review.json`已保存退出核对。scheduler exit1，policy/robot正常shutdown -15；全部登记子进程已退出，GPU6=1MiB/81037MiB空闲/0%，ss确认19460/19462无监听（初次bind受残留socket影响，未启动新任务）。

与08:23 GPU7 put-back故障同为episode首次get_obs、logical_step0、30秒外层超时；发生在不同任务/seed/卡，已不是单一seed证据。公共边界缺口及最小建议见下文，仍未证实底层慢首帧或卡死的根因，未改timeout/源码/参数。请Manager协调公共owner诊断并裁定失败模型重试规则。GPU6本轮先保持空闲，不继续投入第三项来掩盖重复公共故障；其余GPU3/4/5/7四项继续按原配置推进，GPU7 seed1已完成首条，第二条在08:45仍有query14/step402进展。失败两项均未补跑/覆盖。

---

# 08:37 GPU7 rearrange t+30 seed1 smoke PASS，formal100已启动

GPU7已按07:52下一空卡优先条款运行配对seed1。自身20k smoke2 CLI exit0，两集success（392/405步），video392帧完整可读、no-video通过既有validate_smoke_run；config_source内audit/manifest逐字节一致，所有登记子进程退出（scheduler0，服务正常shutdown -15）。config SHA256为89ede174d421fa17aec278dbb116c38c18641612ab5e842ed42c86c3019f0659。

08:36:37正式启动前复核GPU7=1MiB/81037MiB空闲/0%，19470/19472可绑定，原三树干净且SHA不变。run `rearrange_full_t_plus_30_s1_20k_100ep`，PID3521314，job48930d29-9e3c-430c-8f8a-e93671f08333；实际command保存在既有.local/memory_schema_eval/launches。对应smoke_verification.json随正式目录保留。

当前五个formal为GPU3/4/5/6/7，GPU0/1/2不使用，远端停用。此前put-back t+30 seed0基础设施失败仍完整保留待Manager裁定，未重跑。其他四项继续推进，尚未到50条中检。不修改正在使用的源码/文档，不合入台账，保持active turn。

---

# 08:26 GPU7 put-back t+30 seed0 formal提前失败，原产物保留

08:23:34 runner终止，外层命令报告benchmark退出2。`put_back_full_t_plus_30_s0_20k_100ep`完成16条正常episode（13 success/3正常失败），episode16/seed100016于logical_step0出现基础设施失败，summary共17条、status=failed；不是完整100结果，不能用13/17作为正式100成绩。全部17条、视频、metadata、trace及smoke原位保留，未补跑/覆盖/删除失败条。

首因证据：processes/018-scheduler.stdout.log显示08:23:04首次get_obs等待，最终transport TimeoutError 30.0s；runner同刻get_episode_status超时并报robot_status_transport_error。该episode没有Memory v1 query trace，最后状态ready/step0。未见此前模型推理错误；worker最后只见新实例导入信息，现有日志不足以判断是慢首帧还是底层挂起，不冒称根因已证实。

代码证据（固定bridge 8ea）：robot_bridge/benchmark/runner.py:418写死client timeout=30，430–434状态RPC失败即终止；scheduler/base.py:120–121使用WebSocketClient默认30秒（transport/websocket.py:113）；rmbench_simulation.py:129–131用同一锁串行worker RPC，而本次worker rpc_timeout=600。get_obs等待期间状态查询可等待同一锁，外层预算比内部短。

最小建议交Manager/公共owner：先针对该seed和首帧get_obs确认耗时/阻塞点，区分底层卡死与外层预算不匹配；若证实预算问题，在既有RPC调用边界显式协调有界timeout，不改memory/动作协议、不全局无界等待、不另造runner。本task未改超时或源码。失败项后续重试/补齐规则需Manager裁定，不能在同目录接续冒充原100。

收尾：进程事件全部有退出，失败scheduler exit1、policy/robot正常shutdown -15；08:25核对自有GPU7进程为空、19470/19472已释放、GPU7=1MiB/81037MiB空闲/0%。job1803ad5f-b94a-4b64-bdc1-2c7f8ed9339c已按失败归档。failure_review.json保留核对结果。其他四项formal继续，08:28落盘进度为rearrange t+1/t+30 seed0=23/24、put-back t+1 seed0=16、rearrange t+1 seed1=8，均无runtime_error。按07:52下一空卡优先授权，GPU7再次复核1MiB/0%和19470/19472空闲，已于08:27:26启动rearrange_full_t_plus_30_s1_20k_smoke2；保持原参数和独立smoke/formal，不重跑失败模型。当前GPU7为此新smoke，失败项仍保留待裁定。

以下为此前启动与smoke记录；GPU7 put-back的运行状态以上述失败收尾为准。

---

# 08:00 五项formal100运行，GPU3 seed1 smoke已通过

按06:53授权，在owner分别发布GPU4/6/7/5训练保存、CPU验收、进程退出和释放后逐卡接用；每次启动前显存均1MiB/0%，端口空闲，原三树干净。按最新07:52补充，GPU0/1不抢占，GPU2留wash，GPU3已获授权接用，wuwen-1停用。未修改源码/配置，未重跑技术50或旧drawer。

## 已完成：四个20k自身smoke

| variant（均训练seed0） | GPU | smoke结果 | 视频帧数 | 两条logical steps | config SHA256 |
| --- | ---: | --- | ---: | --- | --- |
| rearrange_full_t_plus_1 | 4 | 2/2，门禁PASS | 393 | 393/407 | 6f1d367559353dc42fa548f5ab9f700d216dfa08dd0f746dd98234f1d43a3afb |
| rearrange_full_t_plus_30 | 6 | 2/2，门禁PASS | 392 | 392/405 | 336b3e2454acdb33328d491a834c9ef81ed2f5d4514581d90f2e26ed94ba1bb5 |
| put_back_full_t_plus_1 | 5 | 1/2，门禁PASS | 333 | 333/500 | 7f9fa778a054e7138201069a4ebf7d6884d43e1e3fa6168e305e79751f0c5585 |
| put_back_full_t_plus_30 | 7 | 2/2，门禁PASS | 332 | 332/329 | c0b903e28db9d52717a6ca61c873c692156ae3ea711e4ee5881c3e0e9e83ae5b |

smoke run名均 `<variant>_s0_20k_smoke2`。四次CLI均exit0，既有validate_smoke_run验证当前manifest/source通过；每run两条accepted rollout无runtime_error，video/no-video各一集，视频逐帧读通。input_audit与input_manifest经config_source继承副本逐字节一致。每run两scheduler exit0，policy/robot正常runner_shutdown -15，所有start对应进程均已退出。

put-back t+1第二条为正常step_limit_reached（500步），不改参数或重抽样。这里的成功数仅为smoke结果，不替代正式100成绩。真实20000权重恢复与新wire由匹配smoke覆盖，不再另跑技术验证。

## 正在运行：五个formal100

| GPU | run | 实际启动CST | PID | MAM job |
| --- | --- | --- | ---: | --- |
| 3 | rearrange_full_t_plus_1_s1_20k_100ep | 2026-09-11T07:59:47.951854+08:00 | 3388704 | 7a618537-3350-45cc-bb45-d3d8fe62f722 |
| 4 | rearrange_full_t_plus_1_s0_20k_100ep | 2026-09-11T07:32:29.513716+08:00 | 3319712 | af7dd7c9-682c-4a78-9e6e-946cbf47672f |
| 6 | rearrange_full_t_plus_30_s0_20k_100ep | 2026-09-11T07:33:30.188818+08:00 | 3321184 | 1e72397f-0602-4018-bc7c-4e112ad7501a |
| 5 | put_back_full_t_plus_1_s0_20k_100ep | 2026-09-11T07:46:46.988207+08:00 | 3352946 | a58e56cc-2281-4d88-89af-53bdee13a768 |
| 7 | put_back_full_t_plus_30_s0_20k_100ep | 2026-09-11T07:43:56.270325+08:00 | 3344284 | 1803ad5f-b94a-4b64-bdc1-2c7f8ed9339c |

host均is-dcfi2kjdq7g3k6aa-devmachine-0。各run单GPU串行100，sim/policy同卡，分别引用自身smoke。robot/policy端口依次GPU4=19440/19442、GPU5=19450/19452、GPU6=19460/19462、GPU7=19470/19472；各卡独立Warp缓存。正式前重新核对空闲显存/端口与三树干净，可靠detach，立即登记各MAM job。

实际command/cwd/PID/启动时间保留于本worktree .local/memory_schema_eval/launches/<run>.json；临时启动日志同名.log。正式run沿既有recorder保存实际命令、配置、checkpoint/served metadata和source；smoke验证摘要保存为正式目录smoke_verification.json（新启动项在runner建目录后复制）。不在空run目录提前写入文件。

rearrange两项已完成正式首条并继续推进，put-back两项正在启动/首条阶段。尚未完成100，不宣称正式成绩。保持active turn，通过mam wait jobs --task等待并结合日志检查；第50条正常诊断，新20k尚无真正可比旧基准，不强行引用不同训练/模型/F0成功率。保留正常失败与全部100条，结束核对产物/退出、archive job，保留smoke门禁摘要后清理自有smoke和临时缓存。

## GPU3新增与剩余队列

已读07:52发布补充，GPU3启动前实测1MiB/81038MiB空闲/0%，19430/19432端口空闲、run名未占用、三树干净。rearrange_full_t_plus_1_s1_20k_smoke2于07:51:45启动，已完成2/2 success，logical steps392/406，视频392帧可读、no-video正确，既有门禁PASS，config_source逐字节一致；两scheduler exit0、policy/robot正常shutdown -15，全部自有子进程退出，CLI exit0。config SHA256 c37f27fd98cd41904d67c2907cc2b0cd850cf0a295d47ba4984aa4692a845e77。07:59:47已在GPU3启动对应formal100并登记job7a618537-3350-45cc-bb45-d3d8fe62f722（PID3388704）；正式前再次检查1MiB/0%和端口空闲。配对rearrange t+30 seed1保留下一空卡最高优先项，不按成绩筛选。

统一EXPERIMENT_LEDGER.zh-CN.md已获知合入主库；当前三树由正式run使用，不merge或改文档。安全结束运行后再整合台账、更新对应模型行和实际结果链接/快照时间。

## 剩余队列与位置

14项按README既定训练seed配对队列推进，不按中途表现筛选。目前12份已完成owner保存/CPU门禁交接及本入口audit/smoke dry/formal dry（各exit0）；只剩本机训练中的put-back seed2两项待交接。未开始的9个formal仍在队列，不因首批开跑宣称任务完成。

workspace: /mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a
- RMBench: 3e69b1e665a8eac0104d261b233f1b3339007e00
- robot-bridge: 8ea6078543a875b5ae223df16891cdc1fe975c66
- openpi: a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4

正式结果根: /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/。
CPU准备输出: 本RMBench/.local/memory_schema_eval/cpu_20k_20260911；临时audit/manifest在inputs/，checkpoint保持只读。三树继续冻结，后续全部运行结束再更新实验README，避免改变运行source身份。

旧drawer正式产物原样保留。wash公共接口缺口已交Manager协调，详见前轮report bf6d8e8f167bf5e1d705afcc3eb1f06b5f82c28b，本轮不跨写公共实现。
