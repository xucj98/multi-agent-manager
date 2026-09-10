# Memory首批正式20k训练执行

## 目标、工作区与当前授权

你负责已授权的单GPU20k训练执行、监控、checkpoint验收和评测交接：远端八路继续，新增本机四路见下文。Manager统一判断代码/数据验收，其他owner继续实施；你不修改模型、loader、converter、schema或MAM实现，不重跑整个历史实验，不自行派agent。

### 10:39 本机新增四路授权

Manager于10:37读取本机GPU2–7均为1MiB占用、81038MiB空闲、利用率0；GPU2/3交wash，GPU0/1仍F0。你使用本机GPU4/5分别启动rearrange full_t_plus_1/full_t_plus_30的seed2，GPU6/7分别启动put_back full_t_plus_1/full_t_plus_30的seed1。这四项均在原Q2计划内，不新增实验预算。使用你已有d10冻结worktree/解释器，单卡batch32、20k、同pi05_base与已验收norm；仅seed/exp_name变化，不重新训练smoke或重建环境。

每路启动前复核本机实际显存及RAM，确认独立exp_name和输出不已存在，立即从本机python -u -B启动并登记真实本机host/PID。既有本机full/serial50step与同机环境已验收；这里只做启动所需检查，不重跑全部旧门禁。首次检查实际更新与已落盘有限loss，之后与八路远端一起约每小时检查；此轮新增工作不提前反复检查远端进度。所有运行树保持d10。若OOM按原异常协议报告，不隐式换batch。剩余put-back seed2配对等下一空闲时段另派，不自行超出这四项。

先按MAM AGENTS/README读取发布要求，用mam workspace add在本task创建openpi worktree，base=d10cc01d44c10e5ed0cd8c228d9409dd6cabac50；读取openpi AGENTS。独立环境由既有一键入口创建，复用共享assets/data/checkpoints软链接，不挂别人的PYTHONPATH。你本机管理、通过ssh wuwen-1执行训练；两端共享/mnt/public。所有正式进程使用你自己的固定worktree/解释器，运行期间不修改该树的源码或切换版本。

2026-09-10 08:05 Manager已验收full GPU50：实际50updates、51参数leaf全部BF16、3353433872元素、仅checkpoint恢复得到actions(50,14)与memory_prediction_ids(50,3)。结合CPU独立GO 6a32847，现放行wuwen-1 GPU0/1/3/6/7的五个rearrange full/no-memory正式20k，立即按下表启动并登记；保持d10源码冻结。GPU2等serial自身50step恢复通过；GPU4/5等put-back专用norm和实际归一化loader核验。不要等全部八项就绪才启动已通过的项，不向用户再次请求许可。

2026-09-10 08:15 serial GPU gate也已通过：50updates、56参数leaf全BF16、3353474844元素，checkpoint-only恢复actions(50,14)与memory_prediction_ids(1,3)。现追加放行GPU2的serial lag30 seed0正式20k，保持同一d10源码。full/serial验收由Manager读取真实日志/产物完成，不再等第三轮review。

2026-09-10 08:44 put-back数据门也已通过：专用norm由demo_clean_state生成，state/actions各统计14维且全部有限，SHA256为7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261；owner实际两种full loader均返回state(32,32)、actions/weights(32,50,32)，padding权重零。结合先前独立raw/adapter审查，Manager放行GPU4/5两项20k，使用同一d10冻结源码和已准备独立目录、python -u -B。先复核共享asset hash可见再启动即可，不重复规范/数据全量检查。R3/R4后续修正只涉及未使用的aux/conditional路径，勿更新正在运行的源码。

full证据在ad6任务workspace的gpu_smoke_logs/full_tplus1_d10cc01.log、full_tplus1_d10cc01_dtype_restore.log、full_tplus1_d10cc01_restore_wire.log；实际checkpoint为gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50。serial对应serial_lag30_d10cc01三个日志及同名config/run的50目录。它们用于本次验收，正式训练仍从同一pi05_base初始化。

## 第一批配置和资源

资源：wuwen-1 GPU0..7每卡一个训练；本机GPU4–7按10:39分配，GPU0/1用于F0、GPU2/3用于wash，不占用。启动前查实际显存，不能只靠看不到其他人的进程判断空闲；不终止别人的进程。每模型单卡batch32、20,000次optimizer update，H50/K30，save_full_state=False、save_dtype=bfloat16，最终只留20000一个checkpoint及assets/metadata。其余优化器参数沿既定config，不为命令长度手写全部默认参数。若OOM或训练不稳定，保留失败事实及时报告Manager，不能静默改变受控batch/模型/数据或混写重试目录。

| GPU | training config | seed |
| --- | --- | --- |
| 0 | pi05_rmbench_rearrange_blocks_full_t_plus_1 | 0 |
| 1 | pi05_rmbench_rearrange_blocks_full_t_plus_30 | 0 |
| 2 | pi05_rmbench_rearrange_blocks_serial_lag30 | 0 |
| 3 | pi05_rmbench_rearrange_blocks_no_memory | 0 |
| 4 | pi05_rmbench_put_back_block_full_t_plus_1 | 0 |
| 5 | pi05_rmbench_put_back_block_full_t_plus_30 | 0 |
| 6 | pi05_rmbench_rearrange_blocks_full_t_plus_1 | 1 |
| 7 | pi05_rmbench_rearrange_blocks_full_t_plus_30 | 1 |

GPU6/7使用研究计划已经批准的wash等待替补：Q2的配对seed1，属于原72次预算，不增加实验数。wash v3数据已通过最终独立review a2ee264，其训练注册配置和模型验收仍由实施owner完成；下一批空闲卡优先wash。当前继续准备既定八项。

不同config/seed每次使用独立、带明确实验组和seed的exp_name，已有输出拒绝混写；失败重试新目录。使用现有scripts/train.py，不开发通用队列/launcher系统。必要的实际启动命令和分配表写本task report即可，由MAM发布；长进程用可靠detach启动，不依赖短tool session存活。

## 数据、norm和已验收事实

新仿真数据只来自demo_clean_state，不fallback demo_clean。LeRobot根为/mnt/public/xcj/cache/huggingface/lerobot；两任务后缀_demo_clean_state_shared_memory。sidecar在主openpi/data/memory_v1/rmbench/<repo_id>/。数据/配置已独立验收：sim M个图像/query与M+1低维series；robot动作已对齐next frame，offset0，不自行二次移位。full P2共用mask/机器人目标/norm，仅phase目标t+j+1对重复t+30。serial固定lag30/current query/独立argmax，no-memory过滤为robot-only绑定。

base在/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base。新机器人norm只含state/actions各14维，memory one-hot identity，不参与stats。rearrange资产在openpi/assets/memory_v1/rmbench_rearrange_blocks_robot；put-back对应资产由实施ownerad6bb77e生成，实际就绪后才能用。不复制/重算每种目标时序的stats，也不能把rearrange统计用到put-back。

当前源版本d10包含CPU实现ffa308d、CLI模板修复5e3bfd6、自包含factory/YAML修复d10。Banach任务9b73b590做独立review；Bernoulli任务ad6bb77e在本机GPU1提供full/serial各50step模型证据。core/数据/actual tokenizer/P2 loss和梯度/serial条件/更新计数已经有通过证据，你不重复整个测试。runtime真实transforms→Context也已7项通过，live执行器修复不阻塞sim训练。

## 启动、留痕、监控和交接

开跑前交准备报告：独立解释器两端可运行、实际checkout SHA、八条命令、exp_name/输出路径、数据/norm就绪状态、可用GPU快照；相对路径按项目根，来源命令中实际环境设置如GPU/JAX/HF根要可还原。Manager放行后立即分阶段启动，每进程用mam job add登记wuwen-1真实PID/用途。

当前六路日志的progress已证实持续推进，但Step标量尚未写出，不能把无nan文本当作loss有限的证据。最可能是pbar.write走带缓冲stdout、progress走stderr；只读核对原因即可，不向活跃解释器注入代码或改源码，也不为刷新日志重启健康训练。后续尚未启动的GPU4/5使用python -u -B并据实记录命令，避免同类缓冲。现有六路在缓冲落盘后核对数值；报告保留当前可观察范围，沿既有约小时进度/异常监控。

每步沿现有机制保存真实command/cwd/git commit、resolved TrainConfig、上游数据/sidecar metadata/config；不复制代码或新增重复runtime/provenance。首次检查确认不是仅服务启动：实际optimizer更新前进、loss有限、batch32/单GPU与配置一致。根据稳定step耗时估计剩余时间，之后每小时检查一次，不频繁轮询；异常及时处理。agent可报告阶段结果，Manager在计划检查时机唤醒；进程必须保持可靠detach且MAM登记。

完成核对20,000更新、唯一20000 checkpoint、完整参数shape/BF16/无optimizer、assets与metadata、仅checkpoint路径可恢复。base约3.35B参数，裸BF16约6.71GB，不按旧12GB估算硬凑大小。随后向Manager/评测owner提供checkpoint和metadata；每个正式eval仍需自身2rollout video/no-video smoke后100，不在本任务未经安排启动eval。

记录实际结果、清理本任务临时smoke/无用文件后archive已停止job。正式checkpoint保留共享原repo路径；worktree等任务验收且无活跃job后由Manager归档。report包括task_revision、workspace/完整commit、完成/未完成、job及输出路径、下一检查时间。不要修改其他task的task.md/report.md。


## MAM 查询更新（2026-09-10）

系统 MAM 已更新：`mam task list` 和 `mam job list` 为带表头的简表，无 --json；完整task信息使用 `mam task status <id>`，实时job结构化详情使用 `mam job status <job-id>`。`mam task show` 仍默认Markdown，保留 --json。`mam task status` 仅显示保存的 job 状态与 checked_at，不刷新进程。按既定频率监控时使用 `mam job list --task e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe` 获取实时进程状态，再结合已有日志检查进度。训练/评测协议、GPU 分配与检查频率不变。

## 15:41 Q2 最后一对 seed2

e690负责人确认技术smoke与drawer10ep offline完成，GPU1显存1MiB/0%、相关端口与自有进程已退出。现在授权本机GPU1启动 pi05_rmbench_put_back_block_full_t_plus_1 seed2，沿已验收冻结d10cc01环境、同pi05_base/数据/norm、单卡bs32/实际20k更新、BF16仅最终20000模型及metadata，使用独立exp_name memory20k_e7e5ac54_put_back_full_t_plus_1_s2，禁止覆盖混写。使用python -u -B避免旧缓冲。先确认GPU实际可用，启动后MAM登记与首次真实update/loss检查，不重跑已验收50step。现有12路训练不变。

配对 full_t_plus_30 seed2 使用exp_name memory20k_e7e5ac54_put_back_full_t_plus_30_s2，等待GPU0的BF16正式100收尾后由Manager单独放行；本条尚不授权GPU0。此二者是既定Q2三seed实验清单的剩余两项，不额外扩展实验。


16:01接口迁移：不要再将job list输出按JSON解析；用task status里的jobs取ID，再逐个job status获取实时结构化结果。既定监控频率不变。新增mam wait jobs/list/stop可按需使用，自动CODEX_THREAD_ID；停止等待不影响实验。
## 16:11 GPU0 配对项放行

BF16负责人报告63f2857已确认100条完成、16:01:58自有GPU0进程退出/端口释放/无计算进程、job归档。现在授权本机GPU0启动先前明确的 pi05_rmbench_put_back_block_full_t_plus_30 seed2，exp_name memory20k_e7e5ac54_put_back_full_t_plus_30_s2。沿原冻结d10cc01、同数据/norm/base、单卡bs32/20k实际update、BF16仅最终checkpoint、python -u -B及metadata；不重跑50step、不覆盖。启动前核对实际显存，启动后登记job与首次更新/有限loss证据。现有13路不变，后续14路按小时合并监控。MAM结构化实时查询用job status，不解析job list表格。
