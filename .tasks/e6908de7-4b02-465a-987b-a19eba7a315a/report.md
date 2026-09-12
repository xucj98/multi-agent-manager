## C 迁移评测准备（2026-09-12 03:02 CST）

文档提交 `13192bb5ee4be7c18fe149996a17b18772826811`，在既有安全 docs tree
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`
的 `codex/e6908de7-b-training-docs` 分支，仅更新
`experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md`。它将过期的“14项均未运行”表替换为准确的 C 候选清单：2项完整100保留不重跑、4项历史不完整须从seed100000全新100、6项未GPU启动、2项能力基线待跑；最终准入后的最小批次为12项，14个20000 checkpoint链接均实读存在。

已读取 C 任务 `2a879870-8dda-4613-a684-0ad48a5e86be` 最新发布报告及两个实时 job status。三机 candidate smoke 已通过；put-back full t+1 seed0 的 C 严格100在本次核对仍为running，已记录前50为34/50、本机为35/50，尚未完成100或5pp最终验收。因此未启动任何新GPU评测、未登记本任务job，也没有对外部C job调用wait；本任务没有可等待的活跃job，按要求发布准备阶段报告。

已核对归档任务 `378da0ac` 与独立复查 `ae463958`：状态/diagnostic边界修复已归档，历史partial证据继续保留；没有重开RPC诊断、改变协议或把旧partial拼入新分母。迁移条目要求C owner使用独立结果leaf、每checkpoint自身video/no-video smoke2→formal100，不覆盖本机既有正式目录；C最终准入后再由Manager排期及指定运行树。

验证：`git diff --check`通过，C候选表恰14行、14个checkpoint路径存在；docs tree及原RMBench、robot-bridge、openpi冻结运行树均干净。未占GPU、未停止现场PM服务、未修改机器人或冻结eval树。待Manager集成文档commit，并等待C最终验收后恢复实际评测排期。

## put-back 状态增量（2026-09-11 16:40 CST）

文档commit `81f6aafa37e44e99bd0cb5de68066ccb508f8f86`，复用原docs树。按695bc51f最新发布report及Manager放行更新两行：no-memory GPU0正式step100，补真实输出/日志链接；serial自身gate通过、已放行，实际启动证据待owner，正式目录仍标计划。仅同步相邻快照及总数，保留四路repeat原快照。diff-check、实际链接检查通过，提交后干净；未占GPU、未改冻结eval树。

## 第二批 B 实际状态更新（2026-09-11）

文档交付 `25d57eb4aef881347ed881d0bb56408efce2be33`，复用原 `RMBench-ledger` / `codex/e6908de7-b-training-docs`，仅改实验台账。依据7ae41311已发布15:46:48小时巡检，四项repeat更新为训练中，记录有效进度、快照剩余ETA、共享输出目录及冻结训练SHA；依据695bc51f已发布15:47报告，no-memory记为CPU review/GPU50/恢复通过且已放行、等空卡未正式启动，serial记为配置review通过、待自身GPU门禁。两个put-back正式目录明确标计划，50step独立链接。

已删除过期“无published report”解释及重复MAM细节。diff-check和新增实际链接检查通过，docs tree提交后干净；未占GPU、未修改冻结eval三树或已有run，原2完整/4失败/8待启动边界保留。待Manager集成。

## 2026-09-11 第二批 B 文档交付

文档 commit：`f6dbff8a243d0ac67ff7c7a4cade99845f524272`，基于主 RMBench `d6a438857a04bb5778fa8d0d24344d4c6dbc81ed`，待 Manager 集成。
安全 docs tree：`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`，分支 `codex/e6908de7-b-training-docs`。仅修改 `experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`，没有重建环境。

14:29 CST 已核对 7ae41311 和 695bc51f 的最新发布 task、report 接口和 task status：两个 report 均未发布，只有草稿；无 job 摘要或已发布 updates。因此四项 rearrange serial/no-memory seed1/2 写“已派发、未确认启动”，两项 put-back seed0 写“配置准备、正式训练待门禁及 Manager 放行”。没有把 task working 当作训练中，没有读取草稿推断进度。

新增六行写明 B 组动机、预期检验、checkpoint/CPU交接及自身smoke2→formal100待办，并引用两个owner报告核对入口和发布task版本。未猜put-back注册名或真实产物目录，待owner发布后补链接。六项与首批14/14准备完成统计分开；原2完整结果、4失败证据、8未启动及公共RPC文档校正保留。

验证：diff-check通过；新增两处report路径存在（不视为已发布证据）；提交仅1个文档，docs tree干净。原三树均干净且冻结SHA仍为RMBench `3e69b1e665a8eac0104d261b233f1b3339007e00`、bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。未占GPU、未启动或重试模型；后续eval等待C准入和公共故障裁定。保留docs tree供集成，原运行三树继续保留。

## 14/14 CPU准备验收后的清理

Manager已验收14/14 CPU准备并将5dab24fd ff合入主RMBench。已核对主库包含该提交、文档树干净，删除额外RMBench-ledger worktree及codex/e6908de7-seed2-docs分支。原三库运行树和冻结SHA均保留、干净，四失败证据原位保留。

已核对自有schema Warp缓存目录不存在，实验入口目录无残留__pycache__。worktree的warp-cache入口实际指向共享主库，剩余F0/旧smoke缓存属于其它实验，未跨清理。保留C迁移所需14组CPU审计/dry-run及inputs材料，它们是可复核准备输入，不作为GPU运行结果或新持久缓存。此次未启动GPU，task无活跃job；后续仍等待C准入与公共RPC裁定，不重试失败项。上文新文档worktree/分支路径现仅作交付历史。

---

## 2026-09-11 最后两项seed2 CPU准备完成：14/14就绪

已读取稳定训练manifest `/mnt/public/xcj/Projects/openpi/checkpoints/memory20k_e7e5ac54_manifest.json`（14项），并核对最后put-back seed2两项closure-audit.json/closure-evidence.md与manifest哈希一致。owner已完成参数读回/BF16/finite/shape CPU门禁，本task未重复恢复完整模型。

原三库固定运行树复用，只使用现有run_memory_schema_eval.py，显式CUDA_VISIBLE_DEVICES为空、JAX_PLATFORMS=cpu、PYTHONDONTWRITEBYTECODE=1。两模型各执行prepare-audit、smoke dry-run、formal dry-run，共6步exit0；checkpoint metadata进入MemoryContext，字段phase/origin_mat、H50/K30、demo_clean_state来源及各自t+1/t+30 schema通过。checkpoint文件集合/大小/mtime前后未变。

| variant / train seed | 稳定checkpoint | 预定run（未GPU启动） |
| --- | --- | --- |
| put_back_full_t_plus_1 / 2 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s2/20000 | put_back_full_t_plus_1_s2_20k_smoke2 → put_back_full_t_plus_1_s2_20k_100ep |
| put_back_full_t_plus_30 / 2 | /mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s2/20000 | put_back_full_t_plus_30_s2_20k_smoke2 → put_back_full_t_plus_30_s2_20k_100ep |

日志在原RMBench `.local/memory_schema_eval/cpu_20k_20260911/put_back_full_t_plus_{1,30}_s2_20k_{audit,smoke_dry,formal_dry}.log`；汇总含实际命令/cwd对应位置与只读/隔离验证：同目录 `put_back_seed2_preparation.json`。两项临时audit/manifest仍位于既有inputs/<variant>--<checkpoint路径hash>，后续随config_source复制到正式run。未创建任何上述eval结果目录、未启动GPU/服务或MAM job；模板GPU5/7及端口仅用于dry-run，后续按C准入实际资源重新配置并完成自身smoke，不能作为GPU分配凭据。

稳定实验台账提交 **5dab24fdb1a1fcab742fc47dcb6a5fcd1a2339db**（base f2ec2cf，分支codex/e6908de7-seed2-docs）。仅文档临时worktree `/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`，未安装环境；只改EXPERIMENT_LEDGER.zh-CN.md的训练/CPU状态、最后两项20000链接与manifest证据，明确14项/12项Q2口径。diff-check、结果路径隔离和14组CPU日志检查通过，提交与原三库均干净；原运行SHA和四失败证据不变。该新文档提交尚待Manager合入，旧已合并临时分支的清理事实仍成立。

当前仍为2完整100、4基础设施失败、8项未GPU启动、0项运行；训练/CPU准备升级为14/14，不等同于GPU评测完成。继续等待C环境准入和Aquinas/task378da0ac公共RPC修复裁定，不自行重试失败或启动GPU。

---

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

8项尚未GPU启动：put-back seed1 t+1/t+30、rearrange seed2 t+1/t+30、put-back seed2 t+1/t+30、rearrange serial_lag30 seed0/no_memory seed0。14项均已完成20k保存/owner CPU交接及本入口CPU audit、smoke dry、formal dry；最后两项增量见本文最新CPU交付。

已读集群C迁移新条款：C未准入前不自行启动C正式run，已启动本机run均原位收尾；后续新eval在C准入与根README/workspace要求发布后优先排C。当前无可等待的活跃job；等待C准入及四失败的公共处置/重试裁定，未自行接续空卡新任务。任务整体14模型队列尚未完成，不标记全任务完成。

## C checkpoint 传输进度（2026-09-12 03:39 CST）

按最新条款仅传 12 个待评 `20000` checkpoint，不传训练数据、cache、环境或评测结果，未启动任何 GPU 评测。C 目标统一为 `/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/<config>/<exp>/20000`；每项先确认源端 `params/assets/metadata/_CHECKPOINT_METADATA` 和 C 端目标不存在，实际传输在 `wuwen-nx-aic → wuwen-4090-aic` 上以 `rsync -a --partial --append-verify --bwlimit=10m` 执行，完成后以 `rsync -aicn --delete --omit-dir-times` 复核。

已完成并归档 3 项，均在 C 端得到零差异校验、相同文件清单 hash 和 `_CHECKPOINT_METADATA` SHA-256：

- `put_back_full_t_plus_30 / s0`（job `07f340e8-19a8-4992-ae11-e91bb484c435`）；
- `rearrange_full_t_plus_30 / s0`（job `5de7d82e-cc15-4f11-a2e3-9b99a628c4c7`）；
- `rearrange_full_t_plus_1 / s0`（job `c72d46f9-9255-4044-b83d-b1df8fb31b0f`）。

传输日志及只用于本轮运行的窄 worker 位于 `/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c_checkpoint_transfer/`；待全部传输收尾、日志保留后清理 worker，不在 checkpoint 或冻结评测树写入任何文件。

当前两条真实 rsync 均已登记且未超过两路并发：`rearrange_full_t_plus_1 / s1`（job `ae1eecd7-380c-4b22-b70e-2fb0af53c1e8`）和 `put_back_full_t_plus_1 / s1`（job `0964e0d6-999c-4ca6-9cda-bf63792e9072`）。它们的启动相隔远超过 60 秒；我正使用 `mam wait` 接收停止事件，停止并不自动视为成功，仍须逐项 checksum/metadata 收尾和归档。C 的最终 GPU 准入尚未改变，本任务不会在 C 或本机启动新的 GPU eval。

## C 最终准入后的首批执行（2026-09-12 03:59 CST）

Manager 已验收 C 对照为 70/100，对本机完整基线 69/100 相差 1pp，放行本任务 12 项待评模型逐项 C smoke2→formal100；2 份既有完整本机结果仍不重跑。按 C 操作手册，我没有引用 `2a879870` 或 `5773b6ec` 的临时 worktree/venv，而是在 C1 创建本任务自己的共享三库 worktree：`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval/`。创建日志、失败 attempt 1（C1 缺少 `/usr/bin/time`，安装器尚未被调用）和 attempt 2 的完整 stdout/stderr、耗时、git status、非跟随软链统计均在其 `records/`；attempt 2 通过稳定 `.local/create_worktree.sh` 完成，SHA 为 RMBench `17b55bff1c79a0c5a836d1da089765934cb3a5b0`、bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`、openpi `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。

首批使用已先行抵达并已 checksum 验收的 s0：put-back full t+30 和 rearrange full t+30。两个 checkpoint 的 C worktree `prepare-audit` 都通过，metadata 经 `load_train_config → _runtime_metadata → MemoryContext` 进入实际 scheduler 配置，字段、H50/K30、`demo_clean_state` 和 `last_executed` feedback 均已留在 records。dry-run 生成的实际 smoke/formal 命令使用固定 `memory_chunk_20260910` experiment group（冻结入口 config 所定）和新的 C 专属 leaf，不会覆盖本机 baseline：

- C3 GPU0：`c_put_back_full_t_plus_30_s0_20k_smoke2_20260912` → `c_put_back_full_t_plus_30_s0_20k_100ep_seed0_20260912`；端口 19400/19402；
- C3 GPU1：`c_rearrange_full_t_plus_30_s0_20k_smoke2_20260912` → `c_rearrange_full_t_plus_30_s0_20k_100ep_seed0_20260912`；端口 19410/19412。

03:59 CST 的实际 C3 preflight 已保存：GPU0/1 都是 1 MiB/0%、无 compute app、上述四端口无监听，两个结果 leaf 均不存在；NVIDIA EGL ICD 固定为 `/usr/share/glvnd/egl_vendor.d/10_nvidia.json`（SHA-256 `9e6f14af…b2ddaf76`）。每项只在 matching video/no-video smoke2 成功、产物/退出/三库 clean 核对后登记并启动同 GPU formal100；第50条按可比历史和基础设施状态留快照。当前传输已完成 5/12、两条 s2 rsync 正在登记运行；C eval 放行不等于传输完成，模型到达后按队列接续。

## C 首批 smoke 基础设施超时（2026-09-12 04:13 CST）

首批两项已抵达的 s0 都完成本任务 C worktree 的 `prepare-audit` 与命令 dry-run，但真实 smoke2 均在 episode0 / seed100000 的第一次 policy `infer` 前后停止，未产生可用 smoke 门禁，**没有启动任何 formal100，也没有重试或改参数**：

- put-back full t+30 s0，C3 GPU0，job `e4b77207-6da7-4aa2-9cd0-6da61d273254`，leaf `c_put_back_full_t_plus_30_s0_20k_smoke2_20260912`；
- rearrange full t+30 s0，C3 GPU1，job `b7eedf3b-936c-483a-99e8-62c0fcf33487`，leaf `c_rearrange_full_t_plus_30_s0_20k_smoke2_20260912`。

两条证据相同：policy server 已从各自只读20k checkpoint恢复 params、norm stats和新schema metadata，scheduler 已连通 robot/policy；随后 `processes/002-scheduler.stdout.log` 在 `WebSocketClient.call()` 收到 `TimeoutError: timed out in 30.0s`，runner 将 policy/robot 以 `runner_shutdown` / `-15` 收尾。policy 日志没有自身 traceback，故目前只能确定“首次 infer 在30秒预算内未返回”，不能把冷启动编译、服务阻塞或模型行为中的任一项当作已证实首因；`_result.txt` 仅记录 `scheduler_exited_before_terminal`，不能算作0分结果。

公共边界证据在本任务冻结 bridge `8ea6078`：`robot_bridge/benchmark/runner.py:418` 以 `timeout=30.0` 构造 policy client，`robot_bridge/transport/websocket.py:149-167` 将其作为单次回包预算。请 Manager/公共 owner 裁定该既有 runner 是否需要一个有界、可审计的首次 infer 预热或 timeout 修复；本 task 不自行改 bridge、算法、checkpoint、seed 或绕过 matching-smoke gate。两个 failure leaf、worker/scheduler/policy日志、processes.jsonl 和 C3 资源快照均保留。04:13 CST 复核 C3 GPU0/1 各1 MiB/0%、无compute app、19400/19402/19410/19412无监听，三库 clean。

checkpoint 传输继续，不占 C GPU：现有8/12日志已有 `verified_at` 与零差异校验；刚收尾的 rearrange full t+30 s2（job `a6138b49-067b-488f-906a-4a46631bee61`）另行实读确认 `_CHECKPOINT_METADATA` SHA-256 两端均为 `5ca58395751d2ca07bdfd66f91dbbbb151fdc8a8393717bc2b520cac1693d73e`。put-back full t+1 s2（job `de532b30-cad1-4ff4-95d6-ef0f086d716f`）与 t+30 s2（job `c00832c4-5292-46b9-8de0-be4e501079c8`）是仅有两条活跃 rsync；完成后仍须逐项复核再归档。其余 C GPU eval 等该基础设施裁定，不因模型已到达而并发启动。

## 2026-09-12 C 首次 infer 诊断与最小修复（待独立 review）

保留的 C smoke leaf `c_put_back_full_t_plus_30_s0_20k_smoke2_20260912` 和
`c_rearrange_full_t_plus_30_s0_20k_smoke2_20260912` 都在 checkpoint/norm/schema metadata
恢复、robot/policy 连接成功后，于首个 scheduler `infer` 的既有 30 秒 WebSocket receive
预算退出；policy server 没有 traceback，未启动任何 formal100。真正的执行预算来自
`robot_bridge/scheduler/base.py` 的 policy client `call`，`runner.py:418` 只是 service/metadata
探测，不是这次失败的首因。

单一、有界、串行的 `JAX_LOG_COMPILES=1` 诊断使用同一 put-back checkpoint 和默认 30 秒预算，
从 `04:38:01` 到 `04:42:37` exit 0、2/2 成功；policy 首个 `jit(fun)` XLA compilation 记录为
`27.232250690s`。它与两份失败 leaf 的 30.0 秒 traceback 共同表明冷启动首次 infer 的编译窗口
已贴近预算，原来的并发冷启动会越界。完整证据在 C 自有 worktree
`c-eval/records/first_infer_diagnosis_20260912.md`，两份原始 failure leaf 保留且不计入成绩。

基于此证据，在 C 自有 bridge worktree 提交
`f9626636c4776d8eb15f9c556775cb2d12c000e5`（`Allow a bounded cold-start policy inference budget`）：
新增正且有限的 `policy_first_infer_timeout`，默认仍为既有 30 秒；只有显式配置时才把预算给一个
scheduler process 的首个 infer，之后调用保持 client 默认 30 秒。它只经
`OpenPiSimulationScheduler` 暴露，没有改算法、seed、horizon、checkpoint 或 memory schema。
CPU 验证在 C 闭包中通过：`tests/scheduler` + `tests/transport/test_websocket.py` 为
**101 passed, 1 skipped**。该 commit 现**待独立 review**；未更新 runtime pin 或 scheduler config，
review 前不重启这两项 smoke，也不启动其他 C smoke/formal。

12 个原始待评 20k checkpoint 的传输现已全部完成：每条
`c_checkpoint_transfer/*.log` 均有 `verified_at`，且使用 `rsync -aicn --delete --omit-dir-times`
零差异校验；worker 仍保留以供审计，日志不清理。新增训练仍不能接入：695bc51f 的 6 条 put-back
训练在其 `02:51` 已发布快照中均 running、无 `20000`；7ae41311 的 4 条 rearrange 训练在其
`04:29` 发布快照中均 running、无 `20000`。论文台账的 C 已评/12项待评/10项训练中清单正在安全
RMBench docs tree 更新；没有把训练中的路径写成 eval-ready。

## 2026-09-12 C 队列与论文台账提交

安全 docs worktree 从当前 RMBench `xcj-dev` `a7e94204715cccddf82674293b8b6fa0c51e9851`
建立分支 `task/e6908de7-c-eval-ledger-20260912`，提交
`564024207898fef1d5cabee48550a8aebf233529`，仅更新
`experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`。它登记了：

- 两份仅有的完整结果（put-back full t+1/s0 `69/100`，rearrange full t+30/s1 `92/100`）及其
  train/eval commit、failure 分类与不可比较边界；
- 12 个已传 C 的 `d10cc01` checkpoint 的精确相对路径、schema/seed、传输验收状态；两个已有
  C smoke leaf 明确为 `scheduler_first_infer_timeout` 基础设施失败、无成绩且无 formal；
- 695bc51f 的 6 条 put-back 与 7ae41311 的 4 条 rearrange B 组训练的 config/schema/seed、
  train commit 与预期输出路径，均标为训练中不可评，不预设结果或建立传输项；
- 固定 smoke2→formal100、100条分母、50条检查和等待独立 review 的边界。

文档 diff-check 通过；C 端实读 12/12 checkpoint 的 `_CHECKPOINT_METADATA`、`params`、`assets`、
`metadata` 均存在；本机实读新增 B 组预期的十个 `20000` 目录均不存在，与 owner 已发布快照一致。
未修改 C 冻结 eval tree、未启动 GPU、未停止服务或机器人。该 docs commit 待 Manager 集成；bridge
`f962663` 仍待独立 review，review 通过前队列保持停止而非重试。



## 2026-09-12 C 首次 infer 90 秒准入后的执行阶段

独立 review `03d538a0` 已准入 bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5` 的
`policy_first_infer_timeout=90.0`。本机运行配置提交
`3775d4a`（C 部署等价提交 `7933426`）：固定 bridge SHA，使用实验组内
`openpi_simulation_first_infer_90s.yaml`，并要求运行清单与 scheduler 的实际值一致。
它仅为每个 scheduler process 的首个 policy infer 给 90 秒有界预算，后续 RPC 保持 30 秒；模型、
schema、seed、H50/K30 和成功判定均未改动。

本机验证：`git diff --check`、入口 py_compile、两个 checkpoint CPU prepare-audit/dry-run 通过；
bridge scheduler/transport 测试为 **101 passed, 1 skipped**。C worktree 三库冻结为 RMBench
`79334268e28ccd91c59049224aad8d0d799d11a7`、bridge `f9626636`、OpenPI `a869498`；C3/C2 真实
scheduler 均记录了 `First policy inference uses 90.0s RPC budget.`。

四份新的 matching smoke2 均完成 2 条、video/no-video、metadata、scheduler/服务退出与 90 秒
scheduler 配置检查；旧 30 秒失败 leaf 保留不覆盖。

| C host/GPU | train checkpoint | smoke 结果 | 接续 formal100 MAM job |
| --- | --- | --- | --- |
| C3 GPU0 | put-back full t+30 / s0 | 2/2，0 runtime error | `a5f7560b-3667-4aeb-ba37-9491f104225f` |
| C3 GPU1 | rearrange full t+30 / s0 | 2/2，0 runtime error | `589ae4a2-749a-4542-9421-e137a6959812` |
| C2 GPU2 | put-back full t+1 / s1 | 1/2；另 1 条为正常 `button_not_pressed_after_center`，0 runtime error | `03bcccbb-89e4-4d4e-b69e-9aa0f6dee37a` |
| C2 GPU3 | put-back full t+30 / s1 | 0/2；均为正常 `button_not_pressed_after_center`，0 runtime error | `1ad3f257-3ebe-48a1-be64-5029672fcfb2` |

smoke gate 依既有 `assert_smoke_compatible`：要求两条 accepted rollout 无 runtime error、video ON/OFF
证据、所有子进程退出和 completed status，不按两条任务成功率筛选或改参数。四项 formal 都是固定
100 条 seed100000–100099、相同 checkpoint 自身 smoke 引用，尚无正式结果。C2/C3 各有两个 active
formal，达到每 host 最多两个 run 的授权上限；下一批待空位后按既定队列接续。50 条截面、完整收尾、
raw 回传和主 RMBench 台账增量将在结果到达时更新；当前不把 smoke 分数写为正式成绩。

## 2026-09-12 06:04 C formal 运行快照与台账增量

安全 docs tree 的增量提交为 `75a34d6376cc34e2309a81fa5e243e28c463d6ac`，仅更新
`EXPERIMENT_LEDGER.zh-CN.md`：将已过期的“待 review/未启动”改为 `f962663` 已准入、四个 matching
smoke 门和对应 raw leaf/MAM job，并保留两个原始 30 秒失败 leaf。没有写入正式分数或修改 C 的冻结
评测树；`git diff --check` 通过。

该快照中 C3 的 put-back t+30/s0 与 rearrange t+30/s0 分别完成 20/100、17/100；C2 的 put-back
t+1/s1 与 t+30/s1 分别完成 8/100、7/100。所有已完成 episode 均为正常 terminal 记录，未见
runtime error。已重新进入新版裸 `mam wait` 等待四个已登记 formal；既有 C3 50 条监控仍保留。到达
50 条或进程退出后才做下一次处理，不重复 smoke 或启动超过每 host 两项的并发。

## 2026-09-12 06:50 C3 两项 50 条检查

台账增量提交 `c37684b58348e56800ad8828cb92912db1dea274` 与
`2bcd01c8f70c3fee00d4ed2019f543168acb13a2`，仅记录 C3 的两个 midpoint，不改变 C eval 运行树。

- put-back full t+30/s0：episode 0–49 / seed 100000–100049，**38/50**、0 runtime error、全部 terminal；
  前五条视频存在，5–49 未产生额外视频。
- rearrange full t+30/s0：相同连续范围，**43/50**、0 runtime error、全部 terminal；视频策略同样正确。

两份 raw leaf 各自已有 runner 写入的 `midpoint_checks.jsonl`，都说明没有可作主要10pp判断的完整历史
baseline，`triggered=false`；不同 target 的受控比较不被当作基础设施健康基线。两项 formal 均继续运行，
这些数不作为正式成绩。C2 两项尚在 43/100、42/100，未到其 50 条检查点；四个 job 均保持运行，未接续
新模型。

## 2026-09-12 07:01 C2 两项 50 条检查

台账增量提交 `2eff5dc5a17b0c6f7db2a6d9e4e8f046cf3934cb`，在前两项 C3 midpoint 的基础上记录 C2：

- put-back full t+1/s1：episode 0–49 / seed 100000–100049，**25/50**；
- put-back full t+30/s1：相同连续范围，**32/50**。

两项均为 0 runtime error、全部 terminal、前五条视频存在且 episode 5–49 无额外视频。各自 runner
`midpoint_checks.jsonl` 都是无完整历史主比较、`triggered=false`；因此没有启动10pp基础设施诊断，也不把
这两项不同 target 的中期值当正式成绩。C2/C3 各继续两项 formal100，未有主机配额可接续下一模型。

## 2026-09-12 08:28 首批 C formal 收尾与 s2 接续

台账提交 `0c1ccf8b7a25b7de53159ffc4e275aaeea3c74dd`。首批完整结果已回传本机同组目录并树哈希复核：
put-back t+30/s0 **70/100**、rearrange t+30/s0 **90/100**、put-back t+1/s1 **47/100**、put-back
t+30/s1 **63/100**。四项均为100连续 seed、0 runtime error、全部 terminal；旧 job 已归档。

按既定 endpoint/seed 队列，C3 已运行 put-back s2 t+1/t+30（`d8f6e15c`、`f09cf37d`），C2 已运行
rearrange s2 t+1/t+30（`f677b217`、`81a085f9`）。每个新 checkpoint 均先完成 prepare-audit、错开冷启动的
video/no-video smoke2 和 90 秒首推理检查后才转 formal；没有依据首批成绩筛选后续模型。

## 2026-09-12 08:56 C 台账一致性修正

安全 docs worktree
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-ledger`
提交 `4ce7e47a9037c823b916c6959cac8d6f3448e236`，只更新
`experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md`。它将首批 C 四项已完成 formal 从队列表的
旧“运行中”直接改为最终状态：put-back t+30/s0 70/100、rearrange t+30/s0 90/100、put-back t+1/s1
47/100、put-back t+30/s1 63/100；每行包含正常任务失败分类、0 runtime error、100 条 terminal、已归档 MAM
job 和主 RMBench 稳定 `diagnostics_summary.json` 链接。

同步更新 Q2 主表、已完成正式结果概述和总览为 6 份完整100、4 份 seed2 formal 运行中、4 份 C checkpoint
待接续。历史 30 秒失败 leaf 仍作为证据保留，但不再与已完成 C 结果并列成当前失败。文本明确不同训练 seed/
checkpoint 的数值差异不是同 checkpoint 复现误差；仅同任务、同训练 seed 的完整配对才可用于后续 Q2 受控比较。

验证：`git diff --check` 通过；四条新增稳定结果链接均解析到
`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/` 下存在的原始结果文件。docs worktree
提交后干净；未修改 C 冻结 eval tree、checkpoint、GPU job 或机器人。四个 seed2 formal 保持原样，下一步直接
以 `mam wait` 等待其完成事件。

## 2026-09-12 10:23 put-back s2 收尾与 rearrange s0 接续

`mam wait` 收到 C3 GPU0 job `d8f6e15c-255a-4b86-9ab4-0c6bb87671f6` 停止事件。该 job 的
put-back full t+1 / train seed2 formal 已验收为 **67/100**：100 个 episode / 连续 seed
`100000–100099`、100 个 terminal、0 runtime error；33 条均为正常任务终态，分类为
`button_not_pressed_after_center` 17、`button_press_insufficient` 10、`block_not_moved_to_center` 2、
`pressed_before_block_centered` 2、`block_not_returned_to_origin_mat` 1、`block_held_above_origin_mat` 1。
前五条视频均以 ffprobe 可读，100 个 scheduler 均以 `episode_terminal:0` 退出，robot/policy 按
runner shutdown 回收；C3 GPU0 为1 MiB/0%、19400/19402无监听、三库干净。

raw leaf 已以 SSH tar 流回传到主 RMBench 同组目录；C 与本机的规范整树 SHA-256 都是
`c0c36a83a94324e610f79bc08370ba48513f2b915a712d22b1fa7fc853223794`。job 已按上述验收证据归档。
安全 docs tree 提交 `873cc721d35d3eb38470dd7117eb351b23176fda`：主表、C 队列和概述统一为
7份完整100、4份 formal 运行、3份待接续，并加入稳定结果链接与完整失败分类。

C3 GPU0 随即按同任务/训练 seed 配对接续 rearrange full t+1/s0：其 `prepare-audit` 确认
checkpoint metadata 经 `load_train_config → _runtime_metadata → MemoryContext`，matching smoke2 为
2/2（video/no-video、连续 seed、0 runtime error、90秒首推理、服务退出和资源释放均通过）。formal100
已登记为 MAM `37098e1a-aa94-4047-83d2-395c44edaa80`，固定 C RMBench `7933426`、bridge `f962663`、
OpenPI `a869498`；现与 C3 GPU1 put-back t+30/s2、C2 GPU2/3 rearrange t+1/t+30 s2 共四项运行。

## 2026-09-12 10:54 C 台账一致性、seed2收尾与 serial 接续

台账一致性已直接修正队列表和概述，未只追加时间日志：

- `4ce7e47` 将首批四项 C formal 的原“运行中”行改为最终 70/100、90/100、47/100、63/100，并保留各自稳定结果链接和历史基础设施 leaf；
- `8b4e2a2` 收尾 put-back t+30/s2 为 74/100；`137ce32` 收尾 rearrange full t+1/s2 为 **96/100**，使主表、已完成结果表、C checkpoint 清单和总览一致为九份完整100（本机两份、C七份）；
- `01dfe18` 只登记实际已启动的 rearrange serial-lag30/s0 formal。no-memory/s0 仍明确为已传输、待空位，不写成运行中。

rearrange full t+1/s2 的 C formal 已完成 100 个连续 seed `100000–100099`，全部 terminal、0 runtime error，结果为 **96/100**。四条正常任务失败分别为 `block1_disturbed_after_valid_press`、`block2_not_moved_to_middle`、`button_not_pressed`、`button_press_insufficient` 各1。前五视频 ffprobe 可读，scheduler 均以 `episode_terminal` / 0 退出，robot/policy 按 runner shutdown 退出；C2 GPU2 和 19420/19422 已释放，三库 clean。raw 已 SSH tar 回传到主 RMBench 同组目录，C/本机规范整树 hash 均为 `09da8bd3617c19cc6013ed0530c7be58e76653f64446aa78c786729769daa397`，稳定结果为 `c_rearrange_full_t_plus_1_s2_20k_100ep_seed0_first90_20260912/diagnostics_summary.json`。MAM `f677b217-4817-4ff2-bfd3-ecd2d64a0e12` 已归档。

释放的 C2 GPU2 已按既定队列接续 rearrange serial-lag30/s0。它的 prepare-audit/dry-run确认 checkpoint metadata 经 `load_train_config → _runtime_metadata → MemoryContext` 进入 serial `query_selected/query` 反馈；matching smoke2 固定 seed `100000,100001`，video/no-video 各一条、0 runtime error、服务/端口退出门通过。两条为正常 `button_not_pressed`，不以 smoke 成绩筛选。formal100 已于10:54 CST 在 C2 GPU2 启动，MAM job `162b998d-e6c2-4f8f-80ec-dc239f63f765`，冻结 RMBench `7933426`、bridge `f962663`、OpenPI `a869498`，固定 H50/K30、seed `100000–100099`、首个 infer 90秒且后续30秒。启动后 MAM 核对为 running，GPU2 已加载约10.6 GiB；其余 active formal 为 rearrange full t+1/s0、t+1/s1、t+30/s2。no-memory/s0 是下一空位队列。

验证：三个 docs commits 均仅改 `EXPERIMENT_LEDGER.zh-CN.md`，`git diff --check` 通过，所有已完成项的稳定结果链接已实读存在；C 运行三库、checkpoint 和其他 active job 均未修改。继续用新版裸 `mam wait` 等待真实 job 事件；不因阶段报告结束任务，也不重复 smoke 或已完成 formal。

## 2026-09-12 10:59 rearrange repeated seed2 收尾

`mam wait` 收到 C2 GPU3 MAM `81a085f9-1bf2-4a50-990f-b39870a6c9f2` 停止事件。rearrange full t+30 / train seed2 formal 已验收为 **93/100**：seed `100000–100099` 连续、100 个 terminal、0 runtime error；7条均为正常任务失败（`button_not_pressed` 4、`button_press_insufficient` 3）。前五视频 ffprobe 可读，100个 scheduler 均以 `episode_terminal` / 0 退出，robot/policy runner shutdown；GPU3 15 MiB/0%、19430/19432无监听，C三库干净。

raw leaf 已 SSH tar 回传主 RMBench 同组目录；C/本机规范整树 hash 均为 `b611a89f27050f05ed7c63dc65526cd7f95efb267845bb9958d88d9a766ff2da`，稳定结果为 `c_rearrange_full_t_plus_30_s2_20k_100ep_seed0_first90_20260912/diagnostics_summary.json`。job 已归档。相同任务、相同训练 seed 的完整 target 对照为 t+30 93/100 对 t+1 96/100，即 **-3pp**；二者仍是不同 checkpoint，不能写成同 checkpoint 复现误差。

安全 docs tree 提交 `abc59f0`，直接更新主 Q2 表、能力基线表、远端训练概述、已完成结果表、C checkpoint 清单和当前队列：10份完整100（本机2、C8），运行中仅 rearrange full t+1/s0、t+1/s1 和 serial-lag30/s0；no-memory/s0 已传输、将用释放的 C2 GPU3 接续。`git diff --check` 通过，新增稳定链接和本机回传树哈希均已实读核对。下一步只运行 no-memory/s0 自身 prepare-audit → matching smoke2；通过后才登记 formal100。

## 2026-09-12 11:10 no-memory 接续

C2 GPU3 的 rearrange no-memory/s0 已按释放槽位接续。prepare-audit确认 `fields=[]`、无 memory feedback，metadata 仍经 `load_train_config → _runtime_metadata → MemoryContext` 进入 scheduler；没有注入 legacy memory。matching smoke2 的 seed `100000,100001` 均 terminal、0 runtime error，episode0 视频 ffprobe 可读、episode1 按约定无视频，scheduler/robot/policy均正常退出。两条均为正常任务失败（`button_not_pressed`、`button_pressed_multiple_times`），不影响 smoke gate，也不作为性能筛选。

formal100 已于11:10 CST 在 C2 GPU3 启动并登记为 MAM `ff4d1718-ab99-45fd-a310-f843ce458c37`，冻结 RMBench `7933426`、bridge `f962663`、OpenPI `a869498`，H50/K30、seed `100000–100099`、首个 infer90秒/后续30秒不变。启动后 MAM 为 running，GPU3已加载约10.1 GiB。当前 C 12 项均处于“8项正式完成，rearrange full t+1/s0、t+1/s1、serial-lag30/s0、no-memory/s0 formal运行中”；没有未登记或待启动模型。

台账提交 `44aee09`，直接更新总览、能力基线表、C checkpoint 清单和队列历史；`git diff --check`通过，C三库、checkpoint和其它 active job未修改。继续使用裸 `mam wait` 等待真实完成事件；第50条仅按既有阈值检查，不以中途成绩改变参数、队列或分母。

## 2026-09-12 eval_seed 三组入口与 C 首波计划（待独立 review）

用户在已有 eval seed0 结果之后扩大样本：每个已验收 checkpoint 固定独立执行
`eval_seed=0/1/2`，每组各自 matching smoke2 → 单卡串行 formal100。已有完整或运行中的 eval0
leaf 不重跑、不覆盖；训练 seed 与环境条件组分列，不能把三个训练 seed 当作三个 eval seed。

本机独立实现树
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-eval-seed-runtime`
的提交为 `f5087496a0f7c892bd322708e4ac0bbdeb74e523`
（分支 `task/e6908de7-eval-seed-runtime`，父提交 `3775d4a`）。仅改
`run_memory_schema_eval.py` 和 `README_memory_schema.zh-CN.md`：普通20k入口强制显式
`--training-seed`、`--eval-seed`，从 checkpoint `exp_name` 的 `_sN` 核验训练 seed，派生 manifest
把 eval seed 写入既有 profile 的固定 `seed`，并把训练/评测 seed、环境候选起点、policy RNG key和
scope 写入 recorder 会保存的运行配置。普通 run 名也必须同时含 `trainseedN`、`evalseedN`；audit/manifest
按 train/eval/run 分开，命令模板中的 `WARP_CACHE_PATH` 也含该身份。没有新 runner、队列或调度框架。

真实 runner 的环境映射已经核对：`robot_bridge/benchmark/runner.py:489` 从
`100000 * (1 + int(settings["seed"]))` 开始，accepted rollout 后递增。因此三组为：

| eval seed | manifest/profile 固定 `seed` | 环境候选起点 | 候选命名空间 |
| ---: | ---: | ---: | --- |
| 0 | 0 | 100000 | `[100000, 200000)` |
| 1 | 1 | 200000 | `[200000, 300000)` |
| 2 | 2 | 300000 | `[300000, 400000)` |

同任务、同 eval seed 的模型会使用相同候选序列；preflight 拒绝仍由既有 runner 留在
`seed_preflight.jsonl`，不换到另一个 eval seed。每个 run 新起 policy server；冻结 OpenPI
`src/openpi/policies/policy.py:69` 的初始 JAX key 是0，作为固定 policy RNG 记录，并不替代环境 seed。
不同 eval seed 的 manifest hash 不同，既有 formal smoke-compatibility gate 因而不能交叉引用。

CPU 验证均不加载 GPU：对真实
`rearrange_no_memory` train seed1 20k checkpoint 分别执行 eval0/1/2 的 audit/manifest 和 dry-run，
实际读取到的 runner settings seed 为 `0/1/2`、起点为`100000/200000/300000`；`--training-seed 0`
配该 `_s1` checkpoint 被入口拒绝。`py_compile`、`git diff --check` 通过，bridge
`tests/benchmark/test_runner.py` 为 **9 passed**。任务自有 `.local/memory_schema_eval`、脚本 pycache
和 `/tmp/e6908_eval_seed_*` CPU 输入均已清理；checkpoint 未写入任何文件。

13:15 CST 的 C 只读资源快照如下。C2 GPU2/3 的既有 eval0 formal（MAM
`162b998d-e6c2-4f8f-80ec-dc239f63f765`、`ff4d1718-ab99-45fd-a310-f843ce458c37`）及其端口
19420/19422、19430/19432 保持原样。C1 GPU0及GPU3有其他占用，未纳入计划。其余下列14张卡
均为空闲，计划一张卡一个完整 smoke2→formal100，且每项独立端口/cache/run leaf；启动前仍须再核对。

| host | GPU | robot / policy port | 首波 checkpoint / eval seed | leaf 前缀（`_smoke2` → `_100ep`） |
| --- | ---: | --- | --- | --- |
| C1 `wuwen-4090-1` | 1 | 19410 / 19412 | rearrange no-memory train1 / eval0 | `c_rearrange_no_memory_trainseed1_evalseed0` |
| C1 `wuwen-4090-1` | 2 | 19420 / 19422 | rearrange no-memory train1 / eval1 | `c_rearrange_no_memory_trainseed1_evalseed1` |
| C1 `wuwen-4090-1` | 4 | 19440 / 19442 | rearrange no-memory train1 / eval2 | `c_rearrange_no_memory_trainseed1_evalseed2` |
| C1 `wuwen-4090-1` | 5 | 19450 / 19452 | rearrange no-memory train2 / eval0 | `c_rearrange_no_memory_trainseed2_evalseed0` |
| C1 `wuwen-4090-1` | 6 | 19460 / 19462 | rearrange no-memory train2 / eval1 | `c_rearrange_no_memory_trainseed2_evalseed1` |
| C1 `wuwen-4090-1` | 7 | 19470 / 19472 | rearrange no-memory train2 / eval2 | `c_rearrange_no_memory_trainseed2_evalseed2` |
| C2 `wuwen-4090-2` | 4 | 19440 / 19442 | rearrange full t+1 train0 / eval1 | `c_rearrange_full_t_plus_1_trainseed0_evalseed1` |
| C2 `wuwen-4090-2` | 5 | 19450 / 19452 | rearrange full t+1 train0 / eval2 | `c_rearrange_full_t_plus_1_trainseed0_evalseed2` |
| C2 `wuwen-4090-2` | 6 | 19460 / 19462 | rearrange full t+30 train0 / eval1 | `c_rearrange_full_t_plus_30_trainseed0_evalseed1` |
| C2 `wuwen-4090-2` | 7 | 19470 / 19472 | rearrange full t+30 train0 / eval2 | `c_rearrange_full_t_plus_30_trainseed0_evalseed2` |
| C3 `wuwen-4090-3` | 0 | 19400 / 19402 | put-back full t+1 train0 / eval1 | `c_put_back_full_t_plus_1_trainseed0_evalseed1` |
| C3 `wuwen-4090-3` | 1 | 19410 / 19412 | put-back full t+1 train0 / eval2 | `c_put_back_full_t_plus_1_trainseed0_evalseed2` |
| C3 `wuwen-4090-3` | 2 | 19420 / 19422 | put-back full t+30 train0 / eval1 | `c_put_back_full_t_plus_30_trainseed0_evalseed1` |
| C3 `wuwen-4090-3` | 3 | 19430 / 19432 | put-back full t+30 train0 / eval2 | `c_put_back_full_t_plus_30_trainseed0_evalseed2` |

前六行是新到达且已验收传输的 B no-memory train1/train2；它们没有有效的 eval0 formal，故各补全
0/1/2，不会覆盖任何旧 leaf。后八行只补已有 Q2 eval0 的 eval1/2。两份 B checkpoint 已实读 C
稳定路径的 `_CHECKPOINT_METADATA`、`params/assets/metadata`；其 metadata SHA-256 与本机源分别为
`eb437733…ba201`（train1）和`f379c34d…1111bd`（train2）。首波之后继续补其余 Q2 train1/train2和
serial/no-memory train0的 eval1/2；后续 B/U 训练只在其20k和CPU验收完成后加入。

冷启动仍不同时堆叠：review通过、C独立部署树完成后，先依次启动 C1/GPU1、C2/GPU4、C3/GPU0；每个
scheduler 的首个 infer 已返回或有明确失败证据后才继续对应主机下一槽。每项失败只保留 leaf 并先分类，
不把并发扩容当作重复未知原因 smoke。新 runtime 仍未部署到 C，C 的活跃 `c-eval` 三树没有修改，未启动
任何新 GPU 进程或 MAM job。

请 Manager 按最新要求安排独立 review，重点检查 profile `seed` 是否确实进入 runner、训练 seed约束、
manifest/smoke hash隔离及 run-cache 隔离；review通过前不会同步或启用 `f508749`。

## 2026-09-12 13:54 CST：eval_seed0 收尾、三组计划复核

三份已停止的 eval_seed0 formal 均已完成收尾，当前本 task 没有未归档 job：

- rearrange full t+1 / train seed0：**87/100**，正常失败为 `block2_not_moved_to_middle` 4、`button_not_pressed` 5、`button_pressed_multiple_times` 4；C/本机252文件树 hash 为 `3f6419baf179671a54a29ac192c9129ea2dd0665a5b8f698e5d22105cf457160`。
- rearrange full t+1 / train seed1：**99/100**，1条 `block1_disturbed_after_valid_press`；C/本机252文件树 hash 为 `a9dce212f4c189e40046a35e7d1afdad00e02ca99e48fab7b614b304ecdfb60e`。
- rearrange no-memory / train seed0：**23/100**，前50为14/50，正常失败为 `button_not_pressed` 43、`block1_disturbed_after_valid_press` 17、`button_pressed_multiple_times` 16、`button_press_insufficient` 1；C/本机252文件树 hash 为 `edba065cfa813797f243092ac16c238fb83e0d6944f3c627491f2e8c070aeec8`。

三项均为100个连续 accepted seed `100000–100099`、100个scheduler exit0、0 runtime error、100个视频检查通过；raw 保留在主 RMBench `eval_result/memory_chunk_20260910/`。至此12项 Q2 与两项能力基线的 eval_seed0 均已完整100（本机2项、C12项），不重跑或覆盖。

安全 docs worktree 提交 `295effbbab8347b1ba43dca051740cbfde82089a`（`task/e6908de7-serial-ledger-20260912`），只更新 `EXPERIMENT_LEDGER.zh-CN.md`：消除所有过期运行中状态、记录三项收尾与hash，并按checkpoint列eval0/1/2。未完成 eval seed明确为待review而非0分。

`f5087496a0f7c892bd322708e4ac0bbdeb74e523` 仍只在本机独立树
`RMBench-eval-seed-runtime`；普通20k运行强制训练seed和eval seed，runner实际使用 profile `fixed.seed`，所以 eval0/1/2 分别从 `100000`、`200000`、`300000` 起。训练seed由checkpoint `exp_name` 的 `_sN`核验；每个新run独立manifest、smoke hash和 `WARP_CACHE_PATH` 命令值。CPU复核为 `py_compile`、`git diff --check`及 bridge `tests/benchmark/test_runner.py` **9 passed**。C 的活跃 `c-eval` 三树没有改动。

13:54 CST 的只读资源快照与上表首波计划一致：C1 GPU1/2/4/5/6/7可用，C1 GPU0被占用、GPU3有外部1.2GiB使用而排除；C2 GPU2–7可用（首波使用4–7，2/3留给后续队列）；C3 GPU0–3可用。表列14组 robot/policy端口均无监听。独立review通过后，仍先错开 C1/GPU1、C2/GPU4、C3/GPU0 的冷启动；各自首个infer成功后才扩至同表其余卡，一卡完成自身smoke2再formal100。review通过前不部署、不启动GPU。

## 2026-09-12 14:16 CST：B serial 交接、传输与 cache 审计核对

`7ae41311` 已发布 rearrange serial-lag30 train seed1/2 的最终20k交接；两份均固定训练
commit `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，并完成 BF16/metadata、有限参数和 CPU checkpoint-only
Policy 恢复验收。源 checkpoint 均有 `params/assets/metadata/_CHECKPOINT_METADATA`：s1 为61个普通文件、4.9GiB、
metadata SHA-256 `813e498e0f4f6ffd44e708d84f4f592591a063f1fc29af235278fe78c8c34949`；s2 为63个普通文件、4.9GiB、
metadata SHA-256 `07de6b2dfac14c0a2742a759ee0005deec91380a76741668eb34aee62ee301ae`。

C 稳定目标在启动前均不存在，`/mnt/public` 有4.6TiB可用。复用本任务已有
`c_checkpoint_transfer/transfer_checkpoint.sh`，仅传checkpoint，执行 `rsync -a --partial --append-verify --bwlimit=10m`
及完成后的 `rsync -aicn --delete --omit-dir-times` 零差异校验。s1 于14:12:16 CST启动、MAM
`a5c39be1-dcfe-41f2-9041-879b2ff781a1`；s2 于14:13:57 CST启动、MAM
`a6561ab9-c3d3-4f42-b0bc-b0948ea9196c`，相隔101秒，均在 `wuwen-nx-aic` 运行。此时两项均为实际 running，尚未把部分目录当作C-ready；等待 checksum 和 metadata 收尾后才归档。未部署运行时，未启动GPU评测。

C资源审计确认旧命令按共享 `.local/warp-cache/.../schema/gpuN` 构造 `WARP_CACHE_PATH` 字符串；这只能说明命令路径会在跨 C 主机同号 GPU 碰撞，不能证明 Warp 实际缓存碰撞。
本机独立树 `f5087496a0f7c892bd322708e4ac0bbdeb74e523` 的入口改为
`.../schema/runs/<run_name>/{robot,policy}`；普通20k run强制带 `trainseedN` 和 `evalseedN`，当前队列表对每个
checkpoint/评测seed采用唯一结果leaf/run名。因此它只解决命令字符串的唯一性，不能说明 Warp 实际缓存已隔离；hostname没有单独进入路径，
不在本轮扩展实现。独立review `300c4873-f12a-4d15-9d79-2ccf9df5e749` 仍为 working，review准入前不将该代码同步C或扩容GPU队列。

安全文档树 `RMBench-serial-ledger` 提交 `efbabe4`：更新四份B checkpoint状态，并为serial s1/s2加入eval_seed0/1/2覆盖行；
`git diff --check`通过，文档树干净。

## 2026-09-12 14:23 CST：serial C 传输收尾

两条传输均已成功完成并归档，没有启动或修改任何 GPU 评测：

- serial-lag30 train seed1：`verified_at=2026-09-12T14:20:51+08:00`；脚本的 `rsync -aicn --delete --omit-dir-times` 为零差异，C 端 `_CHECKPOINT_METADATA` SHA-256 为 `813e498e0f4f6ffd44e708d84f4f592591a063f1fc29af235278fe78c8c34949`，普通文件61个、4.9GiB；MAM `a5c39be1-dcfe-41f2-9041-879b2ff781a1` 已归档。
- serial-lag30 train seed2：`verified_at=2026-09-12T14:22:29+08:00`；同一零差异校验通过，C 端 `_CHECKPOINT_METADATA` SHA-256 为 `07de6b2dfac14c0a2742a759ee0005deec91380a76741668eb34aee62ee301ae`，普通文件63个、4.9GiB；MAM `a6561ab9-c3d3-4f42-b0bc-b0948ea9196c` 已归档。

因此 rearrange B 的 no-memory/serial-lag30 各 train seed1/2 四份 checkpoint 均已在 C 稳定 OpenPI 根准备就绪；每份仍是
独立 eval_seed0/1/2 的三条 smoke2→formal100 队列，当前0条新评测已启动。安全文档树追加
`bcd5393`（父提交 `efbabe4`），将两份serial改为C-ready、覆盖表改为各0/3待 review；`git diff --check`与
工作树清洁核对通过。本 task 无未归档 job。

刚读取独立review `300c4873-f12a-4d15-9d79-2ccf9df5e749`：仍为 working，尚未发布准入结论。因此保持
`f508749` 只在本机独立树，C active eval tree和GPU队列均不扩容；C审计中所谓 Warp cache 的跨host结论当时仅是 run leaf/run-name 的命令路径唯一性，等待review裁定实际 runtime 选择。

## 2026-09-12 15:17 CST：C 首项 formal 门禁发现与最小修复（待独立 review）

已在新的 C 本任务 runtime 部署批准的 `f508749` / `f962663` / `a869498`，未触碰旧 `c-eval` 树。C1 GPU1 的
`c_rearrange_no_memory_trainseed1_evalseed0_smoke2` 自然完成：两个 accepted reset 是连续
`100000,100001`，video/no-video 证据齐全、`episode_diagnostics.jsonl` 为两条正常 terminal、0 runtime error，
robot/policy均由 runner 收尾；其任务表现为0/2仅是正常任务失败，未用作性能筛选。

同 checkpoint 的 formal100 随后登记为 MAM `7ef23083-70b6-4a6e-88e9-384ad857af4d`，但在第一个 reset 前自然退出，
已归档。失败 leaf 和 outer log 均保留在 C runtime 的
`RMBench/eval_result/memory_chunk_20260910/c_rearrange_no_memory_trainseed1_evalseed0_100ep/` 与
`records/c_rearrange_no_memory_trainseed1_evalseed0_100ep.outer.log`。明确首因不是模型、infer、renderer 或 GPU：
`BenchmarkRunner` 的 `assert_smoke_compatible` 拒绝了 literal launch 差异；原入口把
`WARP_CACHE_PATH=.../runs/<run_name>/{robot,policy}` 直接写入 command，故 smoke 与 formal 的不同 result run
名产生不同字符串。GPU1已恢复1 MiB/0%，端口19410/19412无监听；未启动 C2/C3 的后续 smoke。

本机独立 runtime tree 的最小修复为 RMBench `9d8f47887a50ea691e5624de139f10bfcfb54412`
（父 `f508749`）：只将该 cache 根改为公共 `BenchmarkRunner` 已有的`{result_run}` child-command 占位符。runner
在实际启动时才展开它，所以 smoke/formal 保存的 launch template 一致，同时每个具体 result run仍有独立
robot/policy `WARP_CACHE_PATH` 值；实际 Warp cache 选择需另行核验。不改 public runner、端口、模型、seed、manifest、scheduler或 checkpoint。

CPU 验证：直接构造同一 pair 的 smoke/formal `launch()`，确认二者 robot/policy command byte-identical且均含
`runs/{result_run}/`，而 `--result-run` 保持不同；`py_compile`、`git diff --check`通过；冻结 bridge 的
`tests/benchmark/test_runner.py` 为 **9 passed**。现有 bridge 测试也明确覆盖该既有占位符的严格 smoke/formal
兼容语义。

由于已完成 smoke 保存的是旧 literal command，不能拿它跨版本给新入口做 formal 门禁。独立 review通过后将创建新的
`..._smoke2_r2` → `..._100ep_r2` matching pair，保留已完成 smoke和失败 formal作为证据，不覆盖结果目录。当前本task无
active MAM job；C runtime仍停在已部署的 `f508749`，没有将未审 `9d8f478` 同步到C或扩展GPU队列。

## 2026-09-12 17:40 CST：Warp 实际 cache 路径核查与表述更正

本节更正此前把 `WARP_CACHE_PATH` 命令模板当作实际 Warp cache 隔离的表述。没有升级 Warp、清理 cache、修改任何活跃命令或停止健康评测。

C1 当前 r2 smoke 的 `processes.jsonl` 和当前 formal 的 `/proc/1037750/environ` 均证明 robot 子进程收到各自的 `WARP_CACHE_PATH=.../schema/runs/<result_run>/robot`；policy 子进程同理。两者 `HOME=/root`、`CUDA_VISIBLE_DEVICES=1`。但实际 simulator worker 使用的是 RMBench `.venv`（worker stderr 的 SAPIEN 路径），不是 OpenPI 或 bridge `.venv`；该解释器中的 Warp 为 **0.15.1**，模块位于 `/mnt/public/xcj/cache/uv/archive-v0/RAZBf65xLsHwUZrZGl_Ob/warp/__init__.py`。

启动日志没有可用的 `kernel_cache_dir` 输出：smoke 的 robot server log `robot-bridge/logs/robot_server/20260912-172129-1031015.log` 和 `processes/rmbench_sim_worker.stderr.log`，以及 formal 当前 `processes/`，均无 `kernel_cache_dir`、`Kernel cache:` 或 Warp greeting 行。因此日志不能证明环境变量被实际采用。

源码和同一 worker 解释器的只读 bootstrap 检查给出确定路径：在传入实际 smoke `WARP_CACHE_PATH` 时，`warp.config.kernel_cache_dir` 初始化前仍为 `None`；`warp/build.py:57–86` 只接受 `warp.config.kernel_cache_dir` 的显式 Python 赋值，`None` 时在第69行调用 `appdirs.user_cache_dir(appname="warp", appauthor="NVIDIA", version=warp.config.version)`。Warp `context.py:2881` 以该值调用 `init_kernel_cache`，故此 C1 进程的实际默认选择为 **`/root/.cache/warp/0.15.1`**；该目录已存在，而活跃 smoke 的传入 `.../runs/c_rearrange_no_memory_trainseed1_evalseed0_smoke2_r2/robot` 目录不存在。`context.py:2962–2963` 仅定义可打印 greeting，不改变选择。安装的 cuRobo 源码没有 `WARP_CACHE_PATH` 或 `kernel_cache_dir` 引用；本任务 robot bootstrap 也没有在 Warp 初始化前显式设置该 config。因此环境变量在 Warp 0.15.1 中被忽略，`runs/<result_run>` 只隔离命令、结果/audit 和 smoke/formal template，不隔离实际 kernel cache。

用户说明已在独立 docs worktree（不触碰 C r2 运行树）提交 `99b7d38`：`README_memory_schema.zh-CN.md` 改为 run 名隔离结果、审计输入和端口，并明确 `WARP_CACHE_PATH` 不能推断实际 Warp cache 按 run/GPU 隔离。该文档 commit 基于批准的 RMBench `9d8f47887a50ea691e5624de139f10bfcfb54412`，待集成；技术证据保留在本报告而非操作指南。

最小的**下一 run**方案是停止把 GPU 编号或 `WARP_CACHE_PATH` 当作 Warp cache 隔离机制。若保持 Warp 0.15.1 的默认 host-local `/root/.cache/warp/0.15.1`，应在同一 host 错开/串行首次 Warp 编译，以保留已编译 kernel 复用并避开该版本共享 cache 的并发写入风险。若调度必须允许同 host 并发冷启动，则只在实际 simulator worker 的 Warp/curobo bootstrap、且在 `warp.init()` 前，显式设定 `warp.config.kernel_cache_dir` 为 host+run 的可写目录；代价是失去跨 run reuse、增加首次编译。两者都需要独立 review 后才实施，本轮不静默添加 per-run cache。

健康队列继续：matching `c_rearrange_no_memory_trainseed1_evalseed0_smoke2_r2` 已完成两条 accepted rollout、video/no-video、0 runtime error和正常退出；其0/2任务表现不阻断门禁。formal `c_rearrange_no_memory_trainseed1_evalseed0_100ep_r2` 已在 C1 GPU1 启动，MAM job `c492ec19-772d-403b-a7d0-052c2b5c9c42` 为 running；checkpoint/metadata 已恢复，首个 infer 仍按既定90秒/后续30秒规则。首次 MAM 登记遇到一次 SSH 身份查询超时，未改变进程；重试后已成功登记。后续不因上述 cache 结论停止或改动该 run。

## 2026-09-12 17:55 CST：r2 队列实际接续

C1 GPU1 的 `c_rearrange_no_memory_trainseed1_evalseed0_100ep_r2` 已完成首个90秒预算内 infer 并连续完成前5个 accepted rollout，MAM `c492ec19-772d-403b-a7d0-052c2b5c9c42` 仍为 running。C3 GPU0 在确认 r2 三库 clean、GPU 1MiB、19400/19402 无监听及 formal leaf 不存在后，完成 `c_put_back_full_t_plus_1_trainseed0_evalseed1_smoke2_r2`：accepted seed `200000,200001`，episode0 video 361帧、episode1 no-video，0 runtime error，两个 scheduler `episode_terminal`/0，robot/policy由 runner 正常收尾。它的任务成功数不作为门禁条件。

因此 C3 同 checkpoint 的 `c_put_back_full_t_plus_1_trainseed0_evalseed1_100ep_r2` 已在同卡启动，MAM `6f11a3b5-9b18-460a-af9f-6afeb290ea25` 为 running。两项 formal 都保持批准的 r2 `9d8f478`、bridge `f962663`、OpenPI `a869498` 和90秒首次 infer/后续30秒规则；没有改动现有命令或 Warp cache。

安全 docs worktree 的台账提交 `82e51e7`（`task/e6908de7-r2-running-ledger`）将主状态、eval_seed 覆盖表的“待 review”更新为已准入的“待排队”，并准确标出上述 C1/C3 formal 运行中；没有把运行项写成分数或把缺失 eval 填0。`git diff --check`通过，两个 docs worktree均干净，C运行树未修改。



## 2026-09-12 19:20 CST：主动唤醒迁移后的 r2 队列接续与 C2 收尾

已读取18:35主动唤醒条款。本轮完成可执行接续、结果留痕和已停止 job 收尾后正常结束 turn；不为监控保留 active。C runtime 在启动前实读为干净的 RMBench `9d8f47887a50ea691e5624de139f10bfcfb54412`、bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，未修改活跃 runtime、机器人、Warp 或 checkpoint。

### 新通过的 smoke 与已登记 formal

以下 smoke 都核对了 completed/零 runtime error、两个 accepted environment seed、video/no-video、config_source lineage 和 scheduler exit；任务成功数不作为门禁。各 formal 均在通过 smoke 的同卡启动并已登记：

| host/GPU | checkpoint / eval seed | smoke accepted seed | formal MAM job |
| --- | --- | --- | --- |
| C1 GPU4 | rearrange no-memory / train1 / eval2 | `300000, 300001` | `7888aa9f-f4bb-4aca-847c-408edcebd7a5` |
| C3 GPU2 | put-back full t+30 / train0 / eval1 | `200000, 200001` | `3d9a4ea3-abf4-4b7e-bbfe-40a27785c3d0` |
| C1 GPU3 | rearrange no-memory / train2 / eval0 | `100000, 100001` | `ce4244c2-9207-4fc5-8271-9e9d99a5bda2` |
| C3 GPU3 | put-back full t+30 / train0 / eval2 | `300000, 300001` | `3c3b8746-aecc-493f-8c79-104534d1d6e7` |

既有 C1 GPU1/GPU2 的 no-memory train1 eval0/eval1，以及 C3 GPU1 的 put-back t+1 train0 eval2 仍保持原登记 running。因此当前共有7个已登记 formal；所有正式 leaf 保持100 rollout，不把 smoke 或 partial 写成分数。

C1 GPU5 的 rearrange no-memory train2/eval1 smoke、C3 GPU0 的 put-back t+1 train1/eval1 smoke 已启动且尚未完成；C1 GPU6/7 等待 GPU5 的首个 infer 后再按同主机错开冷启动。C3 无空卡。C2 不再接续，见下节。

### C2 两项 stopped job 收尾

C2 GPU6 (`1c64c244-3c1b-462b-baec-34f3a3ba7264`) 和 GPU7 (`c98c5377-3fc2-4c9f-b775-702feed541dd`) 的 rearrange full t+30/train0 eval1/eval2 都在 episode 22 的 accepted reset 遇到 `worker EOF` 后停止。两项均有23条 partial episode：前者20成功、后者21成功；无 `final_review`，不作为100条正式分数或自动重试。

各 leaf 已写入 `failure_review.json`，保留 diagnostics、episode JSON、process records、worker stderr 与 outer log；两个 MAM job 已按“不完整基础设施证据、不自动重试”归档。两条记录的 worker stderr 均含 renderer 初始化错误，但本轮只记录观察结果，不将其断言为根因或修改基础设施。C2 GPU6/7 在归档前端口空闲、显存约4–5 MiB；由于同型失败重复出现，本任务暂停在 C2 继续启动，等待具体诊断/裁定。

### 台账交付

安全 docs tree：`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-r2-running-ledger`，分支 `task/e6908de7-r2-running-ledger`。此前的 `71ee83b` 已将用户指南收敛为 run/输出/端口用法；本轮可集成增量为：

- `49daa98`：C2 EOF failure 分类与当时队列状态；
- `d1247e2`：两条新增 smoke 的实际启动；
- `d380508`：两条 smoke 转 formal 的 MAM ID 与覆盖表状态。

该树干净，`git diff --check`通过。台账主概述和覆盖表同步列出7个 formal、2个 smoke、C2两个不可计分 partial 和稳定结果链接；没有碰冻结 eval tree 或把缺失 eval 写为0。

下一次停止事件由 MAM 主动唤醒后，先完成对应 formal 的50/100收尾或短 smoke→formal 门禁，再接续当时实际空闲卡；不重复 C2 这两个未知 EOF leaf。


### 19:25 CST 增量：继续填充 C1/C3 空卡

上节19:20快照之后，两个短 smoke 已自然完成并通过同一门禁，直接转为新增正式100：

- C1 GPU5，rearrange no-memory / train2 / eval1，accepted `200000,200001`，MAM `2ec2a132-8913-495b-a4fc-774984ec8009`；
- C3 GPU0，put-back full t+1 / train1 / eval1，accepted `200000,200001`，MAM `e7bbf18a-b5e3-4c85-b893-cd04570680aa`。

二者均有 completed、0 runtime error、video/no-video、metadata lineage 和正常 child 收尾；任务成功数未用作门禁。C1 GPU6 已在其 audit/metadata（train2/eval2 → environment seeds `300000+`）和显存/端口复核后启动 matching smoke `c_rearrange_no_memory_trainseed2_evalseed2_smoke2_r2`；C1 GPU7 需等该 smoke 首个 infer 后才可按同主机错开规则继续。C3 四张卡均有 formal，C2 因已记录的重复 EOF 仍不接续。

因此截至该快照共有 **9 个已登记 formal**：C1 GPU1–5 的 no-memory train1 eval0/1/2 与 train2 eval0/1，C3 GPU0–3 的 put-back t+1/train1/eval1、t+1/train0/eval2、t+30/train0/eval1/2。C1 GPU6 仅为短 smoke，尚无 formal 分数或 MAM job。安全 docs tree 追加 `e6405ae`（父 `d380508`），并保持干净、`git diff --check` 通过；覆盖表已同步为9 formal/1 smoke。此更新取代上节的“7 formal、2 smoke”瞬时状态。

本轮不再主动等待或轮询。已登记的 formal 停止时由 MAM 主动唤醒；届时先收尾/归档，再按实际 GPU 与同主机冷启动门接续。

## 2026-09-12 19:45 CST：r2 stopped formal 收尾、C1 接续与重复 EOF 暂停

本轮按 18:35 主动唤醒规则处理两个已停止 formal，完成证据收尾后归档；未重跑任何不完整 leaf，也没有修改活跃 runtime、checkpoint、机器人或 Warp 配置。

### C3 不完整 formal

- C3 GPU1、put-back full t+1 / train0 / eval2（MAM `d0728059-eecf-444b-a4c0-0a3f9e5e9c43`）在 episode 22 的 accepted reset 遇到 `worker closed the RPC stream (EOFError)`。23 条 partial 有 17 成功，accepted 环境 seed 为 `300000–300022`，无 `final_review.json`。已写 [failure review](/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_put_back_full_t_plus_1_trainseed0_evalseed2_100ep_r2/failure_review.json)（SHA-256 `809fe642…90ef37f4`）并按“不计分、不可自动重试”归档。
- C3 GPU2、put-back full t+30 / train0 / eval1（MAM `3d9a4ea3-abf4-4b7e-bbfe-40a27785c3d0`）同样在 episode 22 accepted reset 发生 EOF。23 条 partial 有 16 成功，accepted 环境 seed 为 `200000–200022`，无 `final_review.json`。已写 [failure review](/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_put_back_full_t_plus_30_trainseed0_evalseed1_100ep_r2/failure_review.json)（SHA-256 `cec7cb89…b2a6038`）并归档。

两项的完整 `diagnostics_summary.json`、episode/proc records、worker stderr 和 outer log 都保留。GPU1 的 stderr 含 renderer 初始化错误，但当前只将其记为观察，不据此认定 EOF 根因。它们与此前 C2 GPU6/7 的两项 episode-22 EOF 构成四项跨卡/跨主机同型基础设施不完整结果；C3 GPU1/2 暂不再自动重试或接续，待具体诊断裁定。

### 健康 C1 接续

- C1 GPU6 的 rearrange no-memory / train2 / eval2 matching smoke 已完成：accepted `300000,300001`、一条 video 与一条 no-video、metadata/config_source lineage、两个 scheduler `episode_terminal`/0 和 runner child 收尾均已核对。其任务表现为 1/2，不作为门禁。匹配 formal100 已登记为 `378e4cd7-cfdb-4d8b-9e5f-6da6694a5641`，当前运行中。
- C1 GPU7 的 rearrange serial-lag30 / train1 / eval0 第一次短 smoke 在尚未生成该 checkpoint 输入 audit 时于 backend 前退出；旧 outer log 保留，没有模型或仿真产物。已用入口现有 `--prepare-audit` 写入 checkpoint metadata→scheduler 的审计/manifest，再以新 leaf `c_rearrange_serial_lag30_trainseed1_evalseed0_smoke2_r2_retry1` 启动。为使完成时自动唤醒并接 formal，这一短 smoke 额外登记为 MAM `23d046b3-c3b2-43bd-b59f-6965143accc7`，当前运行中。

本快照有 8 个已登记 formal 仍在运行（C1 GPU1–6 的 no-memory s1/s2 六项，以及 C3 GPU0/GPU3 两项 put-back），另有 C1 GPU7 的 matching smoke。C3 GPU1/2 空闲但按上段暂停；未停止任何健康进程。

安全文档树 `/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-r2-running-ledger` 的分支 `task/e6908de7-r2-running-ledger` 已提交：`60db08e`、`64a09a6`、`7b7670b`。它同步主概述、覆盖表、MAM ID、两条 failure review 和 audit-before-retry 事实；`git diff --check` 通过，工作树干净。短期本地 JSON 临时文件已清理。

当前可执行接续已完成；结束 turn 后由 MAM 对未归档的 formal/smoke 停止事件唤醒处理。

## 2026-09-12 19:50 CST：C1 serial-lag30 s1/eval0 smoke 门禁与 formal 接续

MAM `23d046b3-c3b2-43bd-b59f-6965143accc7` 的 retry smoke 已自然结束并通过门禁：

- `c_rearrange_serial_lag30_trainseed1_evalseed0_smoke2_r2_retry1` 的 benchmark 为 `completed`、2/2 accepted reset，环境 seed 为连续 `100000,100001`；episode0 有 700 帧可读 video，episode1 为 no-video。
- `processes.jsonl` 记录两个 scheduler `episode_terminal`/0，robot/policy 由 runner 正常收尾；`checkpoint_metadata/inheritance.json` 同时保留 `checkpoint_metadata` 和 `config_source`，后者指向已准备的 `Audit/rearrange_serial_lag30--a2793487ccf1bfd4--train1--eval0`。smoke 的 1/2 任务成功率不参与门禁判定。
- 原 audit 缺失的 smoke outer log 仍保留；retry 使用新的 smoke leaf，未覆盖任何失败证据。MAM smoke job 已按门禁通过归档。

已在同一 C1 GPU7、相同冻结 runtime 和端口映射启动 matching formal100：

- run：`c_rearrange_serial_lag30_trainseed1_evalseed0_100ep_r2`
- MAM：`504fc975-be9d-4307-9685-e0b967b23a76`，启动时已核验 running；当前仅处于服务启动阶段，未报告中间或正式成绩。

安全台账树追加 `6bc7637`（父 `7b7670b`），将 B 组主概述、checkpoint 行和 eval 覆盖表的 GPU7 项统一为 formal运行中，记录 matching smoke MAM 已归档。`git diff --check` 通过且树干净。

此刻共有9个已登记 formal running；C3 GPU1/2 仍按此前四项同型 accepted-reset EOF 结论暂停接续。当前没有未归档 stopped job，结束 turn 后由 MAM 对下一停止事件唤醒。

## 2026-09-12 20:00 CST：C3 GPU3 r2 formal 不完整收尾

MAM 主动唤醒后，C3 GPU3 的 `c_put_back_full_t_plus_30_trainseed0_evalseed2_100ep_r2`（MAM `3c3b8746-aecc-493f-8c79-104534d1d6e7`）已按停止结果收尾并归档。matching smoke `c_put_back_full_t_plus_30_trainseed0_evalseed2_smoke2_r2` 原已通过；formal 在 episode 22 / environment seed `300022` 的 accepted reset 遇到 `worker closed the RPC stream (EOFError)` 后停止。

该 leaf 只有连续 `300000–300022` 的23条 partial episode，其中16成功；没有 `final_review.json`，故正式成绩为 **not reportable**，不以16/23计分，也不自动重试。已写 [failure review](/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_put_back_full_t_plus_30_trainseed0_evalseed2_100ep_r2/failure_review.json)（SHA-256 `f08203eb…42d0e1e`），保留 `diagnostics_summary.json`、episode/proc records、worker stderr 和 outer log。worker stderr 的 Vulkan renderer 初始化错误仅作观察，不作为 EOF 根因结论。

这使 C2 GPU6/7 和 C3 GPU1/2/3 的 episode-22 accepted-reset worker EOF 共五项；C3 GPU1/2/3 不自动重试或接续，等待具体诊断裁定。当前余下8项 formal 仍运行：C1 GPU1–7 的 rearrange no-memory train1/train2 六项与 serial-lag30 train1/eval0，以及 C3 GPU0 的 put-back full t+1/train1/eval1。本轮未修改这些运行树、checkpoint、机器人或 Warp 配置。

安全文档树 `task/e6908de7-r2-running-ledger` 已提交 `77dbfcc3f37f90dadd42225ee7ce4fab056fd448`（`docs: record C3 GPU3 EOF partial`）：主概述、B 组状态、eval_seed 覆盖表和 C3 EOF 摘要已同步；`git diff --check` 通过且工作树干净。

## 2026-09-12 20:04 CST：C3 GPU0 r2 formal 不完整收尾与当前队列

在上一节19:56快照之后，C3 GPU0 的 `c_put_back_full_t_plus_1_trainseed1_evalseed1_100ep_r2`（MAM `e7bbf18a-b5e3-4c85-b893-cd04570680aa`）也在 episode 22 / environment seed `200022` 的 accepted reset 遇到 `worker closed the RPC stream (EOFError)` 并停止。matching smoke 已通过；formal 只有连续 `200000–200022` 的23条 episode、其中14成功，且没有 `final_review.json`，因此正式成绩为 **not reportable**，不将14/23计分，也不自动重试。

已写 [failure review](/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_put_back_full_t_plus_1_trainseed1_evalseed1_100ep_r2/failure_review.json)（SHA-256 `ec387ec9…394a36a`），保留 diagnostics、episode/proc records、worker stderr 与 outer log，并按“不完整基础设施证据、不自动重试”归档 MAM job。此后 C2 GPU6/7 和 C3 GPU0/1/2/3 共六项同型 episode-22 accepted-reset EOF；C3 所有 GPU 暂不接续或重试，待诊断裁定。stderr 中的 renderer 初始化信息仍只作观察，不作为根因结论。

实时 MAM job 表确认，当前仅 C1 GPU1–7 的七项 formal 运行：rearrange no-memory train1/train2 的六项及 serial-lag30 train1/eval0。它们未被停止或修改。

安全台账树 `task/e6908de7-r2-running-ledger` 已追加 `020d4ee89a41d4a0e15e2c40902cc01c612a06cf`（父 `77dbfcc3f37f90dadd42225ee7ce4fab056fd448`），同步主概述、C3 四个 failure review、eval_seed 覆盖表与当前七项 formal；`git diff --check` 通过且树干净。

## 2026-09-12 20:48 CST：C1 GPU1 no-memory seed1/eval0 完整收尾

MAM `c492ec19-772d-403b-a7d0-052c2b5c9c42`（C1 GPU1，`c_rearrange_no_memory_trainseed1_evalseed0_100ep_r2`）已自然完成并归档。固定环境 seed 为连续 `100000–100099`；100 条均 terminal，100 个 scheduler 均为 `episode_terminal` / exit 0，0 runtime error，所有自有子进程已退出。结果为 **24/100（24%）**，前50为12/50。不存在完整且同 checkpoint 的历史100条基线，故未强行做10pp比较。

正常失败为 `button_not_pressed` 42、`block1_disturbed_after_valid_press` 26、`button_press_insufficient` 6、`button_pressed_multiple_times` 2。正式产物在 `/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/c_rearrange_no_memory_trainseed1_evalseed0_100ep_r2/`；[final review](/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/c_rearrange_no_memory_trainseed1_evalseed0_100ep_r2/final_review.json) SHA-256 为 `350b677a2450e8bc6be03cbd7fa0cce0344db3e161a04df8a1efeb1eec4aa0d5`。formal 保留命令、metadata 与 audit/manifest 继承副本；matching smoke 已按协议清理，Warp shared cache 未清理。该24/100属于独立 train seed1 checkpoint，不能同 seed0 的23/100写成同 checkpoint 复现误差。

安全台账树 `/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-r2-running-ledger` 的 `task/e6908de7-r2-running-ledger` 已提交 `6c496ee`（`docs: record no-memory seed1 eval0 result`）。它同步主概述、B组实际状态、能力基线失败分类、覆盖表的 eval0 结果和稳定链接，并更正已部署 RMBench 完整 SHA 为 `9d8f47887a50ea691e5624de139f10bfcfb54412`；`git diff --check` 通过，树干净。冻结 C runtime 仍为 RMBench `9d8f47887a50ea691e5624de139f10bfcfb54412`、bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，未改动活跃树。

实时 MAM 表仍只有六项 C1 formal：GPU2 `5261ee5a`、GPU4 `7888aa9f`、GPU3 `ce4244c2`、GPU5 `2ec2a132`、GPU6 `378e4cd7`、GPU7 `504fc975`。没有新的 stopped job。下一项仍是已完成 audit/dry-run 的 serial-lag30 / train seed1 / eval seed1，但 C1 GPU1 有外部 VM 的 `[Not Found]` PID 占约3793 MiB，尽管19410/19412无监听，不能视为可用或抢占；C3 四卡也无空卡且 C3 GPU0–3 保持既有 EOF 暂停。故本轮未启动新 smoke/formal。自有 `/tmp` 收尾脚本已清理；不停止健康作业，后续由 MAM stopped 事件唤醒处理。

## 2026-09-12 21:01 CST：put-back B 六项交接、传输与三 eval-seed 队列

已按 `695bc51f` 最终报告 `f317c3d64b535e13fe2b8489df6bdc01c448eac9` 接入 put-back serial-lag30/no-memory 的 train seed0/1/2。六个 checkpoint 均来自固定训练 commit `a7f3e07346cee7260cdc3a618eedc38c0702da61`，各自完成20k、最终保存、checkpoint-only恢复和真实 policy 推理门禁，训练 job均归档；这只构成评测准入，不能替代每个 eval seed 的 matching smoke2→formal100。

六个源 `20000` 目录均预检为含 `_CHECKPOINT_METADATA`、`params`、`assets`、`metadata`，C稳定目标在启动前均不存在。优先配对的 serial-lag30/train0 和 no-memory/train0 已通过既有 `wuwen-nx-aic → wuwen-4090-aic` 路径启动，使用 `rsync -a --partial --append-verify --bwlimit=10m`：

- serial-lag30 s0：MAM `c7123658-ee6f-43fb-97d5-d6b8be0dee52`，20:55:11 CST；
- no-memory s0：MAM `350a4c91-88b3-4e66-8571-3bb30f7ab0c1`，20:56:45 CST。

两项启动间隔94秒，当前为实际运行的两路传输；完成后必须用既有 `rsync -aicn --delete --omit-dir-times` 零差异校验并核对目标 metadata hash，才归档并写 C-ready。serial/no-memory 的 seed1/2 共四项均为 READY 待传，未写成运行中，也没有启动GPU smoke/formal。

安全 docs tree `task/e6908de7-r2-running-ledger` 提交 `db4fd88661ca0bf804b33c9e9c4d96cbff32205e`（`docs: queue put-back B checkpoints for C eval`）：将第二批 B 从过时的6项训练快照更新为10项，列出六个精确 checkpoint、传输状态和每 checkpoint eval0/1/2 smoke2→formal100 队列；顶层概述和覆盖表均不把未传/未评项填0。`git diff --check`通过，docs tree干净；活跃 C runtime 未变。

C2/C3 的六项 episode-22 EOF partial继续保留为 not reportable、不自动重试，诊断已交 task `923ea224` / agent `01a09231`；本轮不从 renderer/Warp stderr推断根因或改活跃命令。实时MAM表中的健康 C1 六项 formal保持运行，未被传输或台账工作影响。后续 transfer/formal stopped 事件由 MAM 主动唤醒处理。

## 2026-09-12 21:41 CST：r3 renderer 部署、传输收尾与门禁缺口

已按最新授权建立独立 C runtime：
`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-renderer-r3`。三库实际 HEAD 为 RMBench
`77477931bee18c2476bea36b400ab45dc67d9ebe`、bridge
`f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；均用 C `.local/create_worktree.sh` 创建，三树 tracked clean。候选以仅含
`9d8f478..7747793` 的 bundle 经既有 `wuwen-nx-aic → wuwen-4090-aic` 路径导入，SHA-256
`f2f6e9e83ff2880a524e681054073c86ddb26781a6e9f6f6147acda68da91303`；导入后本地与 C 端临时 bundle 已清理，C stable object/ref 保留。

部署核对确认 `7747793` 父链为 `9d8f478 → eba81b4 → 7747793`；C runtime 的
`envs/_base_task.py` 含 `_PROCESS_RENDERER` guard，`9d8f478..eba81b4` 的 patch-id
`0c5fba6bd94eea3eb7f8ff82f72f6101f4de5eea` 与历史 `17b55bf` 相同。`git diff --check` 通过，候选
`RendererLifecycleSourceTest` 两项 CPU AST 测试通过。标准 `worktree_env_smoke.py` 强制 Torch CUDA 可用，故在
`CUDA_VISIBLE_DEVICES=''` 下按设计退出；没有将其算作 r3 失败，也没有在被占卡上重跑或创建 GPU 进程。

C2 与 C3 当前均无实际空卡，尚未启动 40-reset、smoke 或 r3 formal，r2 健康 C1 jobs/runtime 完全未改。历史 40-reset
receipt 保留的精确调用合同是固定物理卡映射到 `cuda:0`、系统 ICD、连续 seed `100000–100039`、无 policy/result leaf；但其
脚本 `/mnt/public/xcj/Projects/state-vla/workspace/2a879870-8dda-4613-a684-0ad48a5e86be/records/rmbench_renderer_reset_gate.py`
（历史 SHA-256 `c2ebcbc5c781297d63a9771fa60428e8a117ab92d7ce51114a111122a4753bd2`）随已归档 worktree 清理。C1/C2/C3 和当前 r3
源码均无该文件或公共替代入口。按本 task 明确的“复用既有 harness、不得另造框架”边界，未根据 receipt 重写平行 harness；恢复一个经批准的原 harness 前，C2/C3 host gate 保持 pending。

已收尾 stopped transfer `fe659917-4a05-4190-a9b1-a22824e09e43`：put-back serial-lag30/train seed1 的源/目标
`_CHECKPOINT_METADATA` SHA-256 均为 `3eb0cf905927657e99f019be888f0a0f196d26690f28378cce0272fe4cb5ecd5`、61 个普通文件，独立
`rsync -aicn --delete --omit-dir-times` 为零差异，MAM 已归档。安全台账树
`task/e6908de7-r2-running-ledger` 的可集成提交为
`81e815d98d6a198b3f99d1b11bb847f681b6c191`：主表将 put-back s0/s1 四项改为实际 C-ready，保留六项 r2 partial 的
not-reportable 原始证据，并标明各 host r3 gate 通过后以新 leaf 重跑。

## 2026-09-12 22:04 CST：r2 两项完整收尾、结果回传与 r3 门禁复核

C1 已停止的 r2 formal 已分别完成最终核验并归档：

- MAM 5261ee5a-09bb-4734-bead-b95370f4ad5b，rearrange no-memory / train seed1 / eval seed1：连续环境 seed 200000–200099 全部 accepted，100 条 terminal、100 个 scheduler exit 0、0 runtime error，结果 24/100，前50为11/50。
- MAM 7888aa9f-f4bb-4aca-847c-408edcebd7a5，rearrange no-memory / train seed1 / eval seed2：连续环境 seed 300000–300099 全部 accepted，100 条 terminal、100 个 scheduler exit 0、0 runtime error，结果 23/100，前50为12/50。

两项均验证五条正式视频可解码、video/no-video策略、checkpoint metadata/config_source audit、worker 无 EOF/renderer/native traceback 标记、robot/policy runner_shutdown 和端口退出；matching smoke 已按协议清理，shared Warp cache 未清理。最终文件为本机 RMBench 的 eval_result/memory_chunk_20260910/c_rearrange_no_memory_trainseed1_evalseed1_100ep_r2/final_review.json（SHA-256 4257a0023ce66b216a1ee255d33cd658dab585294c739463a84fbd248e33664a）和相邻 evalseed2 leaf 的 final_review.json（SHA-256 22812eca9ba46edb685dbfa25196c24747a7fe149fb14d68c33e15252fe22eff）。二者使用冻结 RMBench 9d8f47887a50ea691e5624de139f10bfcfb54412、bridge f9626636c4776d8eb15f9c556775cb2d12c000e5、OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。

结果按既有 wuwen-nx-aic → wuwen-4090-aic 路径回传；各 leaf 的 rsync -aicn --delete --omit-dir-times 均为零差异。本机文件 manifest SHA-256 分别为 41ece194efbd502e23ec795f91a8a0f5ff67de18cc787f09c58e774dbb78d3c1 与 bbb5598fc961b62762f154528a8e71ddb20f294f5bbf48bb69b23c692c4c4496。train seed1 的三个独立 eval seed 现为 24/24/23，合计71/300；不能与其他 train checkpoint 当作同 checkpoint 复现误差。

put-back serial-lag30/train seed2 的 MAM 8acbd36a-e597-4158-9349-fa52678b92ee，以及 put-back no-memory/train seed2 的 MAM 727cb400-e7b5-43db-9b56-eec75a9afc48，均已完成零差异验收并归档：前者 metadata SHA-256 为 b8798a992ff7017d8a7c87958cb85f12a9937185d2f7357613136c3194be5e47、62个普通文件；后者为 1ae4342011db2089fcc78e58e6c5eb68d0797340a3a6ce682b52592611174e65、59个普通文件。put-back 六个 checkpoint 现均 C-ready，尚未启动新的 GPU eval。

r3 的 C2/C3 独立 runtime 再次核对为 RMBench 77477931bee18c2476bea36b400ab45dc67d9ebe、bridge f9626636c4776d8eb15f9c556775cb2d12c000e5、OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。其 git 链为 9d8f478 → eba81b4 → 7747793；eba81b4 对 envs/_base_task.py 的唯一运行时改动是进程级 _PROCESS_RENDERER 单例，已在 C2/C3 源树逐行核对。C2 当前所有卡均有实际 compute-app 占用，不能接用。C3 当前可见零本机 compute-app 的候选卡，但历史 40-reset harness 本体仍缺失，故未占用或启动任何 gate；实际启动前仍须再核对分配与显存。

缺失证据已复核：历史稳定归档的 renderer/40-reset 仅保留 driver.log、exit、gate-receipt.json、launch.json、result.json 和 retired-candidate.patch；原脚本 rmbench_renderer_reset_gate.py 随 2a879870 worktree 清理，C1/C2/C3/state-vla 当前树及 MAM 历史记录中均无可执行副本或公共替代入口。按“复用既有 harness、不得另造框架”的发布边界，我没有根据 receipt 重写脚本。恢复经批准的原 harness 前，C2/C3 的40-reset、matching smoke 和 r3 formal 均保持 pending；健康 C1 r2 不改动。

六项旧 EOF leaf 的权威计数仍为 episode0–21 的22条 accepted terminal rollout，加 episode22 一条 accepted=null、status=error 的 reset-error record；不是23条 accepted。它们全部 not reportable，未拼接或重试。

安全台账树 /mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-r2-running-ledger 的分支 task/e6908de7-r2-running-ledger 已提交 1f91d189d755666e4fc668e65b7284b1e8dc09e3（docs: record no-memory seed1 eval coverage）。提交同步总览、两份最终结果链接和失败分类、覆盖表，以及 put-back s2 的 C-ready 状态；git diff --check 通过，树干净。活跃 r2 runtime 未修改。


## 2026-09-12 22:52 CST：r3 门禁替代、两项 formal 收尾与可集成文档

本节取代 22:04 节中“缺少 harness、待恢复”的**当前状态**；当时对历史脚本已丢失的记录保留为时间证据。新授权后再次检索 Git、保留归档、C1/C2/C3/runtime 与历史 receipt，仍未找到旧 `rmbench_renderer_reset_gate.py` 或公共等价入口，因此在独立 RMBench 树实现了最小、受版本管理的替代，尚未部署到 C。

### r3 lifecycle gate：已提交、CPU 通过、待 focused independent review

- 工作树/分支：`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-r3-lifecycle-gate` / `task/e6908de7-r3-lifecycle-gate`。
- 提交：`bf34743334efc98440fa9b05e3f2f05e8303846a`，基于已部署 r3 RMBench `77477931bee18c2476bea36b400ab45dc67d9ebe`；新增 `script/renderer_reset_gate.py` 与 `tests/test_renderer_reset_gate.py`。
- 工具仅通过既有 `RMBenchSimulationController` 启动/关闭既有 worker，固定 `put_back_block` / `demo_clean_eval`、seed `100000..100039`、物理 `--device` 到 worker `cuda:0`、系统 Vulkan ICD。它不启动 policy、不调用 recorder、不创建 `eval_result` leaf；receipt 与 worker log 均拒绝写进 `eval_result`。
- 真实 controller 静态契约已核对：构造函数启动 worker 并保存 metadata，`reset(**request)` 和 `shutdown()` 与工具调用一致。工具保留的职责是冻结 RMBench/bridge git state、确认 renderer 修复存在、40条连续 reset 及不跳 seed、worker marker 扫描、退出与原子 receipt；未复制 benchmark 的 process/metadata/smoke 管理。
- 规模：源码252物理行（223非空行），CPU mock测试140物理行（116非空行）。高于早期约150可执行行目标的部分是上述固定 receipt、前置条件和失败留痕；未压缩为难读代码，也没有形成通用 launcher/队列框架。
- CPU 验证均通过，且树干净：

  ```bash
  python3 tests/test_renderer_reset_gate.py
  python3 tests/test_renderer_lifecycle.py
  /root/.local/bin/python3.10 tests/test_renderer_reset_gate.py
  /root/.local/bin/python3.10 tests/test_renderer_lifecycle.py
  /root/.local/bin/python3.10 -m py_compile script/renderer_reset_gate.py
  /root/.local/bin/python3.10 script/renderer_reset_gate.py --help
  ```

  该提交现在只等待 focused independent review；review 通过后才可同步进 C r3 runtime。C2/C3 没有实际空卡，未启动40-reset、smoke或r3 formal。

### r2 两项完整 formal 收尾与回传

- C1 GPU6，`c_rearrange_no_memory_trainseed2_evalseed2_100ep_r2`（MAM `378e4cd7-cfdb-4d8b-9e5f-6da6694a5641`）完整完成：环境 seed `300000–300099`，**33/100**、前50 `13/50`、100 terminal、100 scheduler exit 0、worker基础设施标记全为0，前五视频可解码。最终 [review](/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/c_rearrange_no_memory_trainseed2_evalseed2_100ep_r2/final_review.json) SHA-256 `df019922757c7eca7f81c8db58b72c51c6995ae4e72ccaacc76505427bc7c613`；matching smoke 与该 run 临时 audit 已清理，MAM 已归档。
- C1 GPU7，`c_rearrange_serial_lag30_trainseed1_evalseed0_100ep_r2`（MAM `504fc975-be9d-4307-9685-e0b967b23a76`）完整完成：环境 seed `100000–100099`，**33/100**、前50 `16/50`、100 terminal、100 scheduler exit 0、worker基础设施标记全为0，前五视频可解码。最终 [review](/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/c_rearrange_serial_lag30_trainseed1_evalseed0_100ep_r2/final_review.json) SHA-256 `4b4d084928281ee24d91bd005812964557206c01ee5c3c3cd124a926dd744efe`；matching smoke/audit 已清理，MAM 已归档。
- 两个 formal leaf 均按既有 C → `wuwen-nx-aic` → 本机主 RMBench 路径回传；两段 `rsync -aicn --delete --omit-dir-times` 均零差异。no-memory/trainseed2 的三个独立 eval seed 现为 `37/49/33`，合计 `119/300`。它们是同一训练 checkpoint 的不同环境 eval seed；serial 33/100 来自另一训练 checkpoint，不混作同 checkpoint 复现误差。

### 文档与当前完成边界

安全文档树已提供可合入分支 `task/e6908de7-c-eval-docs-consolidated`，提交
`291d6d8017d11baf65aafca3805fe20a61619fa2`（父 `295effbbab8347b1ba43dca051740cbfde82089a`）：

- 台账主概述、B组训练表与三 eval-seed 覆盖表都从旧“formal运行中”改为稳定结果链接，保留六项 EOF 的“22 terminal accepted + episode22 reset-error”不计分证据。
- 使用说明改为 r3 runtime 的实际路径、端口/leaf 规则和40-reset命令；仅说明使用条件和输出，不描述 Warp 实现细节。
- `git diff --check`通过，分支/worktree干净；没有合入或修改活跃 runtime。

当前状态必须区分：r3 三库环境已经部署且 renderer 静态/CPU检查通过；最小 gate 工具的 CPU验证已完成但尚待独立review和同步；C2/C3 GPU gate 仍因无实际空卡 pending；r2 的上述两项和既有完整 leaf 是有效正式结果，但整套三-seed队列及 r3 正式评测尚未完成。六项 C2/C3 EOF partial 仍 not reportable，未重试。本 task 当前没有未归档 job。

## 2026-09-12 23:38 CST：C1 r3 已接续；C3 40-reset 的启动前解释器修复待聚焦复核

C1/C3 均按最新低占用卡标准复核。C1 GPU1–7 在启动前有约24,211 MiB free、0% util；实测单个
sim+policy 高峰约17.1 GiB used，故 GPU1/2/3 具备余量。没有终止外部进程或改动 r2 runtime、checkpoint、
机器人或 Warp 设置。C3 GPU0–3 各约24,080 MiB free、0% util；C3 r3 runtime 已实读为干净的
RMBench `bf34743334efc98440fa9b05e3f2f05e8303846a`、bridge
`f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，并确认
`envs/_base_task.py` 的 `_PROCESS_RENDERER` 复用补丁存在。

C1 的 `rearrange_serial_lag30 / trainseed1` 新 r3 matching smoke 均完成基础设施门禁：

| C1 card / eval seed | smoke evidence | formal100 MAM job |
| --- | --- | --- |
| GPU1 / eval1 | `c_rearrange_serial_lag30_trainseed1_evalseed1_smoke2_r3`：completed、2/2 accepted、episode0 video 700 frames 可读、episode1 no-video、两个 scheduler exit 0、零 worker infrastructure marker；任务正常失败 `button_not_pressed` 0/2 不阻断门禁 | `d626a209-7b69-4042-9427-3c73be8efe0d`，`c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3`，已登记 running |
| GPU2 / eval2 | `c_rearrange_serial_lag30_trainseed1_evalseed2_smoke2_r3`：同样 completed、2/2 accepted、video/no-video、两个 scheduler exit 0、零 infrastructure marker；0/2 正常 `button_not_pressed` | `71767977-6cda-461f-9a7a-6e8537c53e4d`，`c_rearrange_serial_lag30_trainseed1_evalseed2_100ep_r3`，已登记 running |

两项 formal 都引用各自同 checkpoint、同 train/eval seed 的 smoke，使用 bf3474/f962663/a869498、端口
19410/19412 与19420/19422；smoke MAM jobs 已验收归档。GPU1 已完成最初两个 terminal episode，GPU2仍在
错峰的服务冷启动阶段，尚无正式分数或50条诊断。

C3 首次 `renderer_reset_gate_c3_gpu0_r3_bf3474` 没有执行任何 reset：receipt
`completed_count=0`，在 `get_metadata` 前失败，worker stderr 的首因是
`ModuleNotFoundError: No module named 'numpy'`。根因是 gate 在
`script/renderer_reset_gate.py` 对 `RMBench/.venv/bin/python` 调用 `Path.resolve()`，解析虚拟环境
symlink 到共享 base interpreter，丢失虚拟环境 site-packages；这不是 renderer EOF/reset 失败，也不能作为
40-reset 结果。

最小修复已在独立且干净的 worktree
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-r3-lifecycle-gate`
提交为 **`2e9677ce8ec9f623395184f63f32ddafa66e5e44`**：仅以
`Path(os.path.abspath(...))` 保留虚拟环境解释器 symlink，并加一条 symlink 回归测试。验证均通过：

```text
python3 tests/test_renderer_reset_gate.py          3 passed
python3 tests/test_renderer_lifecycle.py           2 passed
/root/.local/bin/python3.10 tests/test_renderer_reset_gate.py    3 passed
/root/.local/bin/python3.10 tests/test_renderer_lifecycle.py     2 passed
/root/.local/bin/python3.10 -m py_compile script/renderer_reset_gate.py
git diff --check
```

这是 bf3474 已获通过后的新运行时发现，原独立 review 不覆盖它。按任务要求，**尚未将2e9677c同步到C3，未重跑 gate**；请安排该窄修复的独立复核。复核通过后，C3 GPU0 仍有约24 GiB free，可先运行新的固定40-reset，再按已有授权接续 matching smoke→fresh formal100。原失败 receipt、worker stderr 和 outer log 原位保留。

### 23:45 CST 队列/台账增量

安全 docs tree `task/e6908de7-c-eval-docs-consolidated` 已提交
`f251d71f9951802ac00ff16d5d0ec7e412d22fd3`（父 `291d6d8`）：主状态、r3 SHA、serial-lag30 s1
覆盖行均改为实际 C1 formal，s2/eval0 改为实际 smoke，并保留 C3 gate 的启动前失败/待复核边界；
不把运行或 smoke 写作成功率。C1 GPU4 又已在 GPU3 首次 rollout 后错峰启动
`c_rearrange_serial_lag30_trainseed2_evalseed1_smoke2_r3`，MAM
`ab03f43e-07f7-4ff7-a16c-03cef1dff15e`，端口19440/19442；GPU3 smoke MAM为
`1415096f-8cf5-4ece-a751-00a3fd3eea9e`。GPU5/6 的下一批已有CPU audit/dry-run，等前一同主机
smoke 的首次 infer/停止事件后继续，未并发抢启动。

## 2026-09-13 00:09 CST：新 Manager 交接与 C1 r3 接续

已确认新 Manager `01a09657-e0f3-7352-b726-aba5bbd5d498` 的交接；本 task 继续使用原 TASK-ID、既有运行树和 `mam task publish` 发布报告。只读确认文件为 workspace 根的 `manager-handoff-ack.md`，未重建任务、未重启任何已有评测。

C1 GPU5 的 `c_rearrange_serial_lag30_trainseed2_evalseed2_smoke2_r3` 已按既有 `validate_smoke_run` 实读验收：`diagnostics_summary.json` 为 `completed` / target 2，seed 300000、300001 均 accepted，episode0 video 和 episode1 no-video 的检查均为 ok，两个 scheduler child 都 exit 0，worker/outer logs 无 traceback、EOF、segfault 或 runtime-error marker。任务正常失败不作为 smoke gate 的选择条件。该 stopped smoke MAM job `b6ebe7cc-33f7-4194-b0ae-831a73918286` 已在核验后归档。

同一 checkpoint、同一 train/eval seed 的 fresh formal 已在 C1 GPU5 启动并登记为 MAM `b9624ab0-9fdd-469e-a5a2-a2d22868dc22`：

```text
c_rearrange_serial_lag30_trainseed2_evalseed2_100ep_r3
RMBench bf34743334efc98440fa9b05e3f2f05e8303846a
bridge f9626636c4776d8eb15f9c556775cb2d12c000e5
OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4
GPU5 / ports 19450,19452 / seed sequence 300000..300099
```

启动后 GPU5 使用约16.2 GiB，首个 reset accepted 且 worker 已进入实际 700-step rollout；尚未形成正式分数或50条快照。C1 GPU6 的 rearrange serial-lag30 trainseed0/evalseed1 只读 checkpoint 已完成 audit 与 smoke dry-run，随后启动 matching smoke2；GPU7 的同 checkpoint evalseed2 audit/dry-run 已就绪，按同机冷启动错开接续。

C3 GPU0–3 当前各约24,080 MiB free、0% util，bf3474/f962663/a869498 runtime clean 且 renderer process-reuse patch 存在。此前 C3 gate 的 `RMBench/.venv/bin/python` symlink 被 bf3474 的 `Path.resolve()` 跟随到 base interpreter，导致 `ModuleNotFoundError: numpy`，未完成任何 reset；原 receipt/log 保留。窄修复 `2e9677ce8ec9f623395184f63f32ddafa66e5e44` 由独立 review `e755c753-4acf-4958-85f4-7595fba739a0` 审阅中，尚未获当前 Manager 最终放行。因此不部署该提交、不重跑 C3 gate；这是当前唯一待 Manager 裁决的事项。

### C1 GPU6/GPU7 队列接续

GPU6 的 `c_rearrange_serial_lag30_trainseed0_evalseed1_smoke2_r3` 已登记 MAM `1d1b376f-5698-489d-a377-b80c3957a452`。它使用同一只读 trainseed0 20k checkpoint、eval seed `200000..`、端口19460/19462；首个 reset 已 accepted，GPU 使用约16.2 GiB，第一条 rollout 正在执行。

GPU7 的 `c_rearrange_serial_lag30_trainseed0_evalseed2_smoke2_r3` 已在 GPU6 首个 infer/reset 后错峰启动并登记 MAM `58def05d-7340-437f-8c3f-2d63312a0f7f`，使用 eval seed `300000..`、端口19470/19472。两项均只在自身 completed video/no-video smoke 验证后接续各自 fresh formal100；当前没有把 smoke 任务表现记为正式结果。


## C3 2e9677c 独立部署与当前队列（2026-09-13）

按已发布 task revision `6ae23ef9fb3e16fe81f95da1d36417b851b80532` 和新 Manager
`01a09657-e0f3-7352-b726-aba5bbd5d498` 的裁决，未更新 C1 正在运行的
`c-eval-renderer-r3`。已将精确 RMBench commit
`2e9677ce8ec9f623395184f63f32ddafa66e5e44` 作为 git bundle 导入 C 的稳定源库，
并用 C 的既有 `.local/create_worktree.sh` 在共享文件系统创建独立 runtime：

```text
/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-renderer-r3-2e9677c
```

其冻结且 clean 的三库 HEAD 是 RMBench `2e9677c`、bridge
`f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；三份创建日志在该 runtime 的
`records/{RMBench,robot-bridge,openpi}.create.log`。已核对 renderer reuse 源码和
`renderer_reset_gate.py` 的虚拟环境 symlink 保留路径，且 gate CLI 可由新 bridge
venv 导入。此为部署/CPU 验证，**不是** C3 gate 通过。

旧 bf3474 的零-reset 失败证据保持不变：
`c-eval-renderer-r3/records/renderer_reset_gate_c3_gpu0_r3_bf3474.json` 与同名
worker stderr；其中 `completed_count=0`、`ModuleNotFoundError: numpy`。

C3 GPU0 实测 24,080 MiB free、0% util 后，已用新路径启动固定
100000–100039 的 40-reset gate，映射 `CUDA_VISIBLE_DEVICES=0` /
`SAPIEN_RENDER_DEVICE=cuda:0` 和系统 ICD。MAM job
`10cfe400-13ee-483f-ba5f-00e6a094a1e3` 正在运行；新 receipt、worker stderr 和
outer log 均写入新 runtime 的 `records/renderer_reset_gate_c3_gpu0_r3_2e9677c.*`。
仅在该 receipt 40/40 accepted、exit 0 且无基础设施 marker 后，才会在这个 runtime
为受影响 C3 队列建立新的 matching video/no-video smoke2，再启动 fresh formal100。

健康 C1 队列没有中断：已停止的 C1 GPU6 serial-lag30 trainseed0/eval seed1 smoke
`1d1b376f-5698-489d-a377-b80c3957a452` 已核验 2/2 accepted、video/no-video、两个
scheduler exit 0 与无基础设施错误并归档。其对应 fresh formal100 已在 C1 GPU6
启动，MAM job `977e29ab-e527-4e65-bc84-9b5bb2c03f02`，使用现有冻结
bf3474/f962663/a869498 runtime、端口19460/19462；启动后已有连续 terminal rollout，
当前继续运行。C1 GPU7 matching smoke 和其余已登记 C1 formal 均保持原位。


### C1 GPU7 matching smoke 收尾与 formal 接续（2026-09-13）

已处理 stopped job `58def05d-7340-437f-8c3f-2d63312a0f7f`。对应
`c_rearrange_serial_lag30_trainseed0_evalseed2_smoke2_r3` 完整完成：固定
seed 300000/300001 均 accepted 且 terminal，episode0 的 700 帧视频可读、episode1
明确 no-video，两个 scheduler exit 0；无 traceback、EOF、segfault 或 runtime error。
GPU7 回到 1 MiB/0%，19470/19472 无监听，formal leaf 不存在。smoke 已按上述证据归档。

已在同一 clean C1 bf3474/f962663/a869498 runtime 的 GPU7 启动 matching fresh formal：
`c_rearrange_serial_lag30_trainseed0_evalseed2_100ep_r3`，checkpoint 为
`memory20k_e7e5ac54_rearrange_serial_lag30_s0/20000`，端口19470/19472。MAM job
`a1453162-c880-45d0-b639-e3edf0db3494` 已登记；它与既有 GPU6 eval-seed1 formal
`977e29ab-e527-4e65-bc84-9b5bb2c03f02` 保持独立运行。

C3 GPU0 的 `10cfe400-13ee-483f-ba5f-00e6a094a1e3` 仍在新 2e9677c runtime 中执行
40-reset gate，尚未写出 receipt；目前仅见 SAPIEN 的弃用警告，没有将运行中状态写成
C3 gate PASS。


## C1/C2/C3 当前评测快照与 C2 门禁启动（2026-09-13 00:53 CST）

按 Manager 最新资源核查，只复核并使用 C2 GPU6/7；没有触碰 C2 其它卡、没有修改 C1
`c-eval-renderer-r3`。下表的完成数只计
`episode_diagnostics.jsonl` 中 `diagnostics.episode_status.terminal=true` 的记录；
“最近终端记录”是该 JSONL 的最后一次写入时间（记录本身不含逐 episode 时间戳），不是 PID
存活判断。

| host / GPU | run | completed terminal / 100 | 最近终端记录（CST） |
| --- | --- | ---: | --- |
| C1 GPU1 | `c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3` | 52 | episode51 / seed200051, 00:52:47 |
| C1 GPU2 | `c_rearrange_serial_lag30_trainseed1_evalseed2_100ep_r3` | 49 | episode48 / seed300048, 00:53:11 |
| C1 GPU3 | `c_rearrange_serial_lag30_trainseed2_evalseed0_100ep_r3` | 39 | episode38 / seed100038, 00:52:03 |
| C1 GPU4 | `c_rearrange_serial_lag30_trainseed2_evalseed1_100ep_r3` | 36 | episode35 / seed200035, 00:53:16 |
| C1 GPU5 | `c_rearrange_serial_lag30_trainseed2_evalseed2_100ep_r3` | 28 | episode27 / seed300027, 00:52:37 |
| C1 GPU6 | `c_rearrange_serial_lag30_trainseed0_evalseed1_100ep_r3` | 19 | episode18 / seed200018, 00:52:16 |
| C1 GPU7 | `c_rearrange_serial_lag30_trainseed0_evalseed2_100ep_r3` | 11 | episode10 / seed300010, 00:53:06 |
| C2 GPU6 | `renderer_reset_gate_c2_gpu6_r3_2e9677c` | receipt pending | terminal reset count unavailable until receipt |
| C2 GPU7 | no run | — | reserved for post-gate matching smoke/formal |
| C3 GPU0 | `renderer_reset_gate_c3_gpu0_r3_2e9677c` | receipt pending | terminal reset count unavailable until receipt |

C1 GPU1 已到 50 条并由既有 recorder 写入
`.../c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3/midpoint_checks.jsonl`：
21/50 成功（42%），前50个 accepted seed 200000–200049 连续，视频检查 5 video/45 no-video
均 `ok=true`，无基础设施 marker。该项只有不完整历史基线，recorder 明确标为不可作主要比较，
因此没有捏造 10pp 结论；固定 seed/config/队列继续不变。

C2 GPU6/7 复测为各 4 MiB used、24,207 MiB free、0% util，C2 无本 task 进程；新 runtime
`c-eval-renderer-r3-2e9677c` 仍 clean 且冻结 RMBench `2e9677c`、bridge `f962663`、OpenPI
`a869498`。已在 C2 GPU6 启动并登记 MAM job
`546b6d60-f038-4924-b60d-ece5d9489309`，固定 device6→cuda:0、system ICD、seeds
100000–100039。receipt/worker/outer 证据路径为：

```text
.../c-eval-renderer-r3-2e9677c/records/renderer_reset_gate_c2_gpu6_r3_2e9677c.{json,worker.stderr.log,outer.log}
```

C3 GPU0 的同版本 host gate job `10cfe400-13ee-483f-ba5f-00e6a094a1e3` 仍在运行；其
receipt 路径为 `.../records/renderer_reset_gate_c3_gpu0_r3_2e9677c.json`。C2 与 C3 都尚未
生成 receipt，所以均是**未完成门禁**，不根据 warning/PID 推断 reset 进度或 PASS。任一
host receipt 仅在 40/40、exit0、零 marker 后，才在同一 frozen runtime 接对应未完成或
not-reportable r2 item 的 fresh matching smoke2→formal100；不重跑 C1 进行中的七项，也不
拼接旧 partial。

## 2026-09-13 01:17 CST：C3 2e9677c 门禁 PASS 与 fresh smoke 接续

已处理 stopped MAM job `10cfe400-13ee-483f-ba5f-00e6a094a1e3` 并归档。C3 GPU0 的新
`2e9677c` runtime 生命周期门禁为实际 GPU PASS，不是 CPU 结论：

- receipt：`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-renderer-r3-2e9677c/records/renderer_reset_gate_c3_gpu0_r3_2e9677c.json`；
- `passed=true`、`completed_count=requested_count=40`，固定 seed `100000..100039` 的每条 reset 都为 `accepted=true`、`state=ready`、`terminal=false`；`error=null`；
- worker 的 `ConnectionResetError`、`EOFError`、renderer/native/driver、segfault 与 traceback marker 均为 0；结束后 GPU0 为 1 MiB/0%，19400/19402 无监听；
- 独立 runtime 保持 clean：RMBench `2e9677ce8ec9f623395184f63f32ddafa66e5e44`、bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。C1 正在使用的 `c-eval-renderer-r3` 未修改。

门禁通过后，C3 GPU0 已接续一个历史 r2 incomplete/not-reportable 项的 fresh matching smoke：
`c_rearrange_full_t_plus_30_trainseed0_evalseed1_smoke2_r3`，checkpoint
`/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0/20000`，eval seed1 的 smoke seed 为 `200000,200001`，端口 19400/19402。其 audit 和 dry-run 已完成并保存于新 runtime 的
`records/c_rearrange_full_t_plus_30_trainseed0_evalseed1_smoke2_r3/{prepare-audit,dry-run}.log`，输入为
`RMBench/.local/memory_schema_eval/inputs/rearrange_full_t_plus_30--700143d20a84645f--train0--eval1/`。MAM job 为 `d7437ff4-4dbc-48c6-8c44-6ebb77a494a7`。当前 policy 已从该只读20k checkpoint恢复 metadata、params 和 norm stats，worker 已启动；尚无 terminal episode，因而尚无 smoke verdict 或 formal100。仅在完成两条 accepted video/no-video、scheduler/worker退出和零基础设施 marker 的核验后，才启动同名配对 fresh formal100。

01:17 CST 只读快照如下。C1 的数字严格计自各自 `episode_diagnostics.jsonl` 中 `diagnostics.episode_status.terminal=true`；“最近”是该记录文件的最后写入时间，非 PID 存活推断。

| host / GPU | run | terminal / target | 最近记录（CST） | 实际状态 |
| --- | --- | ---: | --- | --- |
| C1 GPU1 | `c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3` | 65 / 100 | 01:12:59 | formal running |
| C1 GPU2 | `c_rearrange_serial_lag30_trainseed1_evalseed2_100ep_r3` | 62 / 100 | 01:13:15 | formal running |
| C1 GPU3 | `c_rearrange_serial_lag30_trainseed2_evalseed0_100ep_r3` | 52 / 100 | 01:13:48 | formal running |
| C1 GPU4 | `c_rearrange_serial_lag30_trainseed2_evalseed1_100ep_r3` | 48 / 100 | 01:13:14 | formal running |
| C1 GPU5 | `c_rearrange_serial_lag30_trainseed2_evalseed2_100ep_r3` | 40 / 100 | 01:12:36 | formal running |
| C1 GPU6 | `c_rearrange_serial_lag30_trainseed0_evalseed1_100ep_r3` | 32 / 100 | 01:13:37 | formal running |
| C1 GPU7 | `c_rearrange_serial_lag30_trainseed0_evalseed2_100ep_r3` | 23 / 100 | 01:12:35 | formal running |
| C2 GPU6 | `renderer_reset_gate_c2_gpu6_r3_2e9677c` | receipt pending | — | MAM `546b6d60-f038-4924-b60d-ece5d9489309` running; JSON receipt still absent, so no reset-progress or PASS claim |
| C2 GPU7 | — | — | — | reserved for post-gate matching work |
| C3 GPU0 | `renderer_reset_gate_c3_gpu0_r3_2e9677c` | 40 / 40 accepted resets | receipt finished 01:02:21 | PASS; archived after verification |
| C3 GPU0 | `c_rearrange_full_t_plus_30_trainseed0_evalseed1_smoke2_r3` | 0 / 2 | — | fresh smoke running, no score/formal claim |

C2 receipt path remains
`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-renderer-r3-2e9677c/records/renderer_reset_gate_c2_gpu6_r3_2e9677c.json`。
