# 接续集群 C 环境与真实评估验收

## 交接与当前优先级
原owner5773b6ec-6584-42db-9d0d-9ef5d40f7c31长时间无新进度回复，Manager已关闭该agent。你是唯一C环境写入/安装/eval负责人。先读原task已发布要求和report（mam task show，report可读本地文件），本task继承其中用户验收范围、严格对照版本/数据/运行协议与README交付。先立即给当前阻塞的精确命令/错误和最短解决路径，再继续。不要重做已传输cache/checkpoint/资产；不要花长时间重复写报告。

在本机通过MAM创建需改仓库的独立worktree，base用原owner提交（下列）并读库AGENTS；原owner本地worktree只读，避免覆盖其未提交工作。C:/mnt/public/xcj/Projects/state-vla/.local 和三库.local稳定入口由你接续维护；原owner远端workspace/5773...中的current环境/records允许复用排查，所有变更及接管路径登记到你的report，旧task保留原始登记。新的fresh测量/strict formal worktree在C workspace/本TASK-ID下手动创建并登记。不扩MAM，不在C运行agent。不得删除来源不明目录。

## 已完成与阻塞
SSH wuwen-4090-1/2/3可达，C共享/mnt/public（不同于本集群同名FS），只-1安装，-2/-3直接运行。必须uv symlink，cache=/mnt/public/xcj/cache/uv，共享Python=/mnt/public/xcj/cache/shared-python，其他cache在state-vla/.cache。现有包/资产已同步，bridge和OpenPI CPU smoke已PASS。原task records在C workspace/5773.../records。

bridge安装改动3ebf9d075e5e64a350ddb35cd8632e3abd04373c（含bdb4182）；OpenPI 5f6ca06436c7b33905b442c769c7800d3f4a17e2（含3435a2b/958eeae）；RMBench c59c6561de72092f95c14582ebaf8b1fe8728d00。三库link-mode及OpenPI文件级symlink私有transformers覆盖已独立review通过（76b4与c03e报告），默认本机hardlink不改。C wrapper在固定旧运行树外提取installer并patch；勿污染运行树。

14:58最后报告：RMBench 7.91GB精确cache已传完，265条uv内部链接已核对并调整，安装在torch/torchvision PyTorch index解析numpy/pillow处离线失败。原owner正尝试264项本机已验证依赖闭包隔离离线安装。16:00 Manager只读查看C无uv/rsync/eval进程，但你需核实当前状态，不能假设文件未变。先查已有闭包/日志/本地未提交改动，最小修复离线解析，不重传整个cache、不引入大型环境框架，必要新增小commit交Manager审阅。不要把导入成功当eval通过。

## 必须完成的验收
1. 三库各.local/create_worktree.sh BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT，从全新路径成功创建，测实际耗时和独占worktree/venv空间、共享cache增量；故障恢复过程单列，不充作一键结果，不du -L重复计cache。
2. 三台C机器各一个smoke含2rollout，一条video一条无video，真实sim+policy+renderer/cuRobo及完整产物。只用实际空闲GPU、不碰他人进程，不使用本机或wuwen-1GPU。
3. 单次完整100，单GPU串行，精确复现本机put_back_full_t_plus_1_s0_20k_100ep=69/100。通过阈值64–74/100；50条先核对趋势/异常，禁止挑重跑结果。固定RMBench3e69b1e665a8eac0104d261b233f1b3339007e00、bridge8ea6078543a875b5ae223df16891cdc1fe975c66、OpenPIa869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。完整命令/模型/data/seeds从原task及本机eval_result/memory_chunk_20260910/put_back_full_t_plus_1_s0_20k_100ep/launch.json和command.txt取，模型已传到C，不重新拷。H50/K30，ep0–99/seed100000–100099，只有前5集video。原bridge正规安装当时client依赖，最新bridge不需要client；不手挂PYTHONPATH旧包。
4. smoke/提交干净代码及产物检查后正式，超1h进程本机mam job add登记C真实host/PID。结果C RMBench/eval_result/<exp-group>/<run>，结束同布局回传本机并校验、RMBench/experiments/<exp-group>写完整比较记录。历史首get_obs30s故障根因未明，不擅自改timeout或混新RPC修复进严格旧代码；若复现及时保留证据报告。
5. 稳定state-vla/README.md给后续eval执行者读取：三机共享与安装/运行、手动workspace/TASK-ID+worktree三参数实际命令、GPU检查、smoke2→commit→100/50核对、结果回传/实验记录、任务结束清理自己的远端worktree/branch/临时smoke且不跟随共享软链。简洁操作手册，不扩MAM。

本task全部交付验收后才迁移后续eval。继承模型/数据/cache保持稳定，旧与新task远端临时目录清理清单交Manager一并裁定；不自行删旧owner本机worktree。报告精确completed/pending、commit、路径及测量结果，不声称根因已修复或C已准入，直到验收完成。

## 旧绝对路径shim稳定性裁定
已知C旧cuRobo YAML绝对路径需要兼容。当前retry1运行期间不要改动其路径。待该smoke完整退出后，将本task创建的C /mnt/public/xcj/Projects/RMBench兼容入口改为指向稳定state-vla/RMBench（或稳定同资产根），不能长期指向workspace/本task/formal运行树，避免归档断链及并行eval互相改全局路径。先核对两目标所需assets真实路径/内容一致，路径修正只影响外部资产定位，不修改严格运行源码；后续三机smoke/formal使用稳定映射。记录实际目标及清理归属，只改你本task创建的shim，不覆盖已有未知目录。旧失败leaf保留到根因与门禁摘要写入稳定记录后再按任务清理要求处理。

## C正式结果回传避免覆盖本机基线
当前C formal leaf与本机69/100 baseline的exp-group/run同名。运行期间不改输出路径、不移动目录。完整退出并验收后，将C本次正式结果整理为独立实验组cluster_c_eval_acceptance_20260911/put_back_full_t_plus_1_s0_20k_100ep，再同布局回传本机RMBench/eval_result；绝不能覆盖本机memory_chunk_20260910/put_back_full_t_plus_1_s0_20k_100ep基线。保留原始command/config内容（不伪称最初就在新目录启动），在验收实验说明写明C实际原路径→最终归档路径映射、原本机基线路径。复制前确认目的不存在，校验内容hash。C当前运行及固定协议不变，结果整理仅在所有进程退出后执行。

## README定向修订（Manager审阅18:12）
手册应面向后续eval执行者，不把本次严格旧版验收固定成所有后续实验协议。三库base commit/模型/seed/video数量由发布task给定；保留可替换三参数示例。明确agent/MAM命令在本集群本机执行，SSH到C1手工建workspace；C2/3只运行。旧版严格client安装/锁和本次具体commit、完整磁盘表/失败恢复放验收实验说明，不放通用入门主线；如果保留可复制的旧版示例，必须补齐实际client安装依赖步骤，否则读者按现有三条创建命令无法跑旧scheduler。默认新bridge不需要client，不能误导所有eval都装旧wheel。
50条中检按前50个已完成episode做截面，保存快照；进程持续运行时文件可能已有51条，不能要求实时文件恰有50行从而误报门禁。仍须检查固定协议种子序列和无基础设施异常；本次100固定seed不变。只修改稳定README/文档，活跃formal不改。手册约100行内即可，避免实现细节/本次历史过程挤占操作步骤。

## Vulkan候选环境修正的重跑边界
Manager已读取episode22 svulkan2/RPC EOF证据：旧C100仅22条正常终态，不计完整验收，保留失败leaf。允许当前系统ICD候选的40次reset验证；它只检验worker生命周期，不能替代policy+video/no-video的2rollout。候选环境通过后先在同一C2 GPU按新环境完整smoke2并保存实际VK_ICD_FILENAMES等参数，产物/退出门禁通过后才以新leaf重新完整100（固定原seed和模型/源码）。新leaf从100000起，不拼接前22条，不挑成绩。保持旧smoke/失败/新smoke各自记录清晰。若仍出现错误，报告具体首因和下一最小诊断，不自动循环重试100。代码不改；环境差异如实保留。

## 用户追问149秒创建耗时：补一轮分段测量
用户问的是RMBench单次149秒为何慢，非总排障4小时。原fresh日志中uv安装时间3.41+17.40+19.80+0.512+1.00约42.1秒，其中cuRobo1秒。Manager只读测当前已存在fresh venv的两次sorted(rglob)扫描分别4.996/4.802秒（70559entries，暖缓存复测，不能当原次计时）；仍不足以解释剩余耗时。
请在本task自己的可清理profile子目录，使用同一入口/同一base补一次CPU-only完整创建分段计时（例如外部timestamp shell trace，不改受管installer），覆盖wrapper预检、git worktree、venv、每次uv调用含进程前后墙钟、双软链校验和收尾；不要只加总uv自报Installed时长。记录是否暖cache及共享FS条件，不将本次测量冒充原149秒。无GPU、无包版本变化、无活跃formal树修改；profile树/branch与临时文件登记并完成后自行清理。优先保留正在运行的renderer gate及必要结果验收，再并行此CPU测量。给Manager实际占比和是否值得修复，不凭猜测改安装流程或扩MAM。

## Resume: Manager decision 2026-09-12
User asked current status; full acceptance remains incomplete. Resume this existing task/workspace. Prior pause awaiting renderer decision is lifted for diagnosis and minimal fix preparation. Keep failed22-rollout run intact, do not combine/skip seeds. Investigate repeated renderer creation lifecycle (releasing references/resources vs reusing renderer) using existing bounded harness, no repeat cache transfer or env rebuild. Environment-only restriction must not force endless ineffective ICD retries: if source fix necessary, prepare minimal patch on task-owned independent branch and establish that actions/observations/reset/seed protocol is unchanged; deliver patch and evidence for Manager independent review before formal eval. Do not change policy, memory timing or chunk protocol. Avoid silently restarting worker every episode merely to hide failure without review. Once reviewed, perform three-machine smoke as relevant then complete one100-rollout sequential singleGPU run and compare matched local69/100 within5 percentage points; run from new leaf with original fixed seed list. Initial response should identify next concrete diagnostic and prior evidence reused.
Also resolve creation-time overhead: measured duplicate recursive symlink checks100.8s/151.8s. Inspect what each check guarantees, remove duplicate full traversal or replace with bounded equivalent checks in environment entry, preserving symlink isolation and private overrides. Measure one fresh creation time and disk use after change, CPU only, clean its worktree/branch afterward. Report actual measurements; no invented speedup target, no broad redesign. Prioritize renderer blocker, do not leave silent waiting for Manager for already-authorized diagnostic. Stage completion reporting, no minute model polling.

## Manager acceptance and conditional formal authorization
Independent review9a63710b reportf1764ef found no code blocker; Manager accepts17b55bf renderer and9c71a3e creation optimization plus40/40 reset and fixed2seed image/action equivalence. Proceed now with C1/C2/C3 candidate video/no-video smoke, each worker fixed SAPIEN_RENDER_DEVICE=cuda:0 and own GPU assignment, clean committed candidate source (not dirty diagnostic overlay). Once all3 pass acceptance/video/no-video/artifacts/shutdown and clean tree checks, you are authorized to immediately start one new full100 sequential singleGPU run from original seed100000–100099/model/H/K/norm, no further permission pause. Register formal MAM job, verify actual episodes, stage report after start; at50 check anomaly and comparable local69/100; full100 acceptance requires difference<=5 percentage points. Infrastructure errors stop and report precise cause, no seed skipping or merging old22. Final result documentation and transfer follow prior task exp-group/run convention. Creation optimization may now be applied to stable C wrapper after preserving exact patch provenance and verifying default entry CPU syntax; no new rebuild loop. Clean own diagnostic temporary trees after evidence retained, preserve formal trees while jobs active.
