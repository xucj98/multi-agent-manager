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
和 Warp cache 均按 train/eval/run 分开。没有新 runner、队列或调度框架。

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
`RMBench-eval-seed-runtime`；普通20k运行强制训练seed和eval seed，runner实际使用 profile `fixed.seed`，所以 eval0/1/2 分别从 `100000`、`200000`、`300000` 起。训练seed由checkpoint `exp_name` 的 `_sN`核验；每个新run独立manifest、smoke hash和Warp cache。CPU复核为 `py_compile`、`git diff --check`及 bridge `tests/benchmark/test_runner.py` **9 passed**。C 的活跃 `c-eval` 三树没有改动。

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

C资源审计确认旧命令按共享 `.local/warp-cache/.../schema/gpuN` 构造路径，跨C主机的同号GPU会碰撞。
本机独立树 `f5087496a0f7c892bd322708e4ac0bbdeb74e523` 的入口改为
`.../schema/runs/<run_name>/{robot,policy}`；普通20k run强制带 `trainseedN` 和 `evalseedN`，当前队列表对每个
checkpoint/评测seed采用唯一结果leaf/run名。因此它在该唯一性前提下覆盖了跨主机同号GPU的冲突；hostname没有单独进入路径，
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
`f508749` 只在本机独立树，C active eval tree和GPU队列均不扩容；C审计中 Warp cache 的跨host隔离结论仍仅依赖每个
run leaf/run-name全局唯一，等待review裁定。
