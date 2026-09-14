# put-back J/T train2 eval1：两批正式100独立证据核验

Review source delivery (source TASK-ID: e6908de7-4b02-465a-987b-a19eba7a315a):
{
  "task": "e6908de7-4b02-465a-987b-a19eba7a315a",
  "commits": {
    "RMBench": "3775d4a878adb0f840c1f8a9e12aa014fb185a53",
    "robot-bridge": "f9626636c4776d8eb15f9c556775cb2d12c000e5",
    "openpi": "a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4"
  }
}

Source task requirements:

# Memory v1 新 checkpoint 评测准备

## 当前执行：原协议 put-back J/T train1/2 补齐三组 eval，新增训练 0

Manager 已验收报告 `638fb6acc42f0079f74cf35bb60eda15c2325e90` 的 T train0 eval1/2：66/100、74/100，重算两批各10份artifact hash、连续seed/terminal/outcomes、记录进程退出及smoke链。T train0合计210/300（70%），J为213/300（71%）；当前44批/4400执行/20模型/12个完整3eval。离线HF比较修正仍FAIL，与Manager首query原复算一致，不解除HF暂停；C3 GPU0仍给source owner的有限诊断，C2 GPU6给P0。

继续复用已有模型补齐缺失评估：put-back J(full_t_plus_1)与T(full_t_plus_30)，各training seed1/2，补evaluation seed1/2，共最多8个新formal100，新增训练0。只使用已在C验收的现有20000 checkpoint和原协议，不混HF reset或诊断分支。先去重完整结果；既有eval0和任何已完整有效批次不重跑，历史partial不拼接。若发现待Manager验收的完整批次，先提交该证据而不重复启动。

优先使用刚释放的C1 GPU1/2及19410/19412、19420/19422；实测资源安全后，GPU1排J、GPU2排T，第一轮train1/eval1，随后train1/eval2，再train2/eval1、train2/eval2。每项自己的matching video/no-video smoke2通过后才从新leaf跑完整100，固定eval1为200000..200099、eval2为300000..300099。不按成功率筛选smoke或改变顺序。没有新的训练/转换/数据集传输；checkpoint缺失或来源不符则报告而不猜路径。

沿冻结runtime `c-eval-putback-baselines-yaml` 的RMBench f401f5279c95451eb424ac98b831bab5552b2120 / bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 / OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，保持H50/K30、原环境与RNG生命周期。首infer显式90秒、后续30秒，保留此前准入配置，不能漏回默认30秒。不改运行树代码、依赖或共享cache；必要的manifest/config准备在本机独立路径完成后同步冻结副本，核对实际命令、metadata/schema/train_seed/eval_seed及hash。

本节授权按上述固定队列连续收尾/接续，不要求Manager在每批已通过相同合同后再次放行。每条长进程登记MAM；停止后按完整100合同核验、final_review、archive、smoke清理receipt，基础设施失败保留首因且暂停该项，不循环重跑。每次处理完可执行事项后发布当前状态置顶的紧凑report并结束turn，由MAM唤醒；不要轮询GPU或其他owner。HF source诊断仍独立进行，本任务不重复其工作。

## 当前收尾与 HF 审计口径更正

MAM升级通知中两条原协议T formal已stopped：eval1 JOBda058195-ff39-49ed-8e83-be5e1a8aaa7e、eval2 JOB3191f8c6-4c53-48a3-9ab7-8b44216ab2c0。先按既有完整100/连续seed/terminal/video/source/hash/进程合同收尾、出final_review并archive及smoke清理receipt，不能因HF工程失败漏掉原队列；结果未验收前不增加当前42批。

Manager已独立读8leaf失败证据与hf_engineering.py：evidence_summary将matched_baseline_action_query.result.actions的50×14与action_plan.queued_actions的30×14直接放同结构；compare_matched_pair再按整个列表比较。这是确定的比较口径问题。T收尾后在自己的离线审计工具做窄修：以query_id/actions_from_query匹配真实accepted queued事件、按queued_rows取实际发送前缀，并按source_step/已执行完成边界比较；区分预测H与下发K，query count不要叫action row count。缺失关联明确失败，不靠固定截30掩盖取消/异常。保留原工具、失败record及review原hash，新增版本和重算receipt，不覆盖旧证据，不重跑GPU。

Manager同时直接重算首个30×14前缀，rearrange两个episode仍max_abs约0.003873，put-back两集约0.003493；所以口径修正不自动解除暂停，不能放宽容差或用小数值宣称无害。现有input不含图像/语言，OpenPI0ce的policy_rng也只有stream/call而非实际key；更正后结论不得称完整输入或实际随机状态相同。真实首因已交源owner task0acf作有界首query诊断，C3 GPU0暂交该owner，HF新matching/r_s30/formal仍暂停；你无需重复诊断或改公共源码。

完成T验收及离线重算后发布当前状态置顶的紧凑report并正常结束。MAM direct-v2按既定Manager转交，不重开兼容性研究。

## 环境已知误报的具体裁决（不影响既定HF工程执行）

Manager已亲自只读核对C共享部署及稳定installer，确认旧worktree_env_smoke.py以解析后路径含site-packages判来源，与C installer显式--link-mode symlink不兼容。P0 task环境中的nvidia_curobo0.7.8安装在本task venv，geom_cu词法路径在该venv/lib/python3.10/site-packages，真实实体在uv/archive-v0/UYbDTNQF-bGDe1JmV92NN。扩展13,367,808 bytes，SHA256 `874b95cb65d84eeb0a84562482de7551638f7c9974d3323b152142476f8abb01`，与installed RECORD的SHA256以及稳定wheel内同名成员逐字节内容一致。稳定wheel `/mnt/public/xcj/Projects/state-vla/.cache/curobo/wheel/nvidia_curobo-0.7.8-cp310-cp310-linux_x86_64.whl` SHA256 `780a878713cad48043b4537268c860e52393ddeb46709a6377409f9c65f4f988`。原smoke脚本SHA256 `589733e0d89f16880303a6bb02c4573348496e7f53805537def5e1cafaab9b21`。因此这一次路径字符串拒绝是环境检查误报，尚未执行的真实cuRobo CUDA distance仍必须完成，不能把来源核对当成CUDA运算通过。

若你的HF新runtime遇到相同旧路径断言，可使用同样的任务自有验证副本：仅以本runtime真实venv/distribution归属、RECORD与上述稳定wheel/扩展hash核验替换字符串判断，其他实际render/CUDA distance检查原样保留，保存原脚本与diff/hash/新receipt，不修改冻结源码、共享环境或绕过真正计算。先重新核对自己runtime确为相同wheel和扩展内容；不匹配则不得套用该结论。无需等待P0工程结束，也无需因此机械重跑已验收40-reset。此为预先解决具体安装检查不兼容，不要求无此故障时新增无关检查或改运行方案。C2GPU6仍给P0，HF沿C3GPU0和原已发布工程合同。

## 当前执行：高频源码已准入，启动 C3 有限 GPU 工程验证

Manager 已阅读独立 review `8345c8e2d0ac5698cd0b70a38d44ae8df02aea44`，直接核对实际 config→gate→每集收尾、runtime_errors→run失败链以及正式 f401 祖先，接受代码 PASS。此节解除下文旧“HF 不得部署/不准入GPU”的状态；正式36批仍待本轮工程证据核验。

批准部署精确三库：OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`，robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`，RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`（包含正式f401）。源树位于本机 workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939。C1按.local/wuwen-4090.md创建本TASK-ID新的独立部署三树，C3运行；不得checkout/reset当前两条T formal或其他活跃共享路径。复用稳定资产/模型和既有环境入口，保持renderer补丁与system ICD，不复制数据集或随意升级依赖。

优先使用已预留并通过稳定40-reset的 C3 GPU0，实际启动前查资源/端口。已有基线gate receipt SHA565a83ef9e20713a871be9f1c41f5da2b1a94c072420e07a23309b70bb3f273a仅证明稳定基础；新runtime须自身真实smoke。若renderer/ICD环境未变，无需仅因记录器改动机械重做40-reset；有实际环境差异则按既有有界gate确认。P0接口验收另在C2自有树执行，不混分支、不占其卡；原协议C1 GPU1/2 T jobs继续自然收尾。

立即把已核对36条准备矩阵（SHA20e414eb14c7f752b158949fda2c62b678e6c3eab2bd2a56452f315364700adb）和baseline inputs（SHA305250a177196a83bc27464b3c9eec1dc2d60a61d27bad4472a608c8aa4d5610）落实为实际config/manifest/命令，先核对作者as-built参数，不能只改版本字符串或沿旧bridge hash。配置生成在本机、自有位置完成，按原审计入口与源码身份形成可复核提交/工件，不改算法。训练新增0，模型只读既有train0 J/S、rearrange/put-back，H50/K30/r_s5，T不得进HF，random_light=false/crazy_random_light_rate=0。

本次授权有限工程阶段：沿准备清单的4个普通baseline/shadow和4个matched baseline/shadow工程run（各两episode，既有eval0 seeds100000/100001，video/no-video）验证额外观测、状态probe、动作/RNG和任务线索。保留已通过的旧/新默认CPU兼容性结论；真实GPU成对检查需实际action/key/command/progress/cue证据，不能只比成功率。普通baseline默认不产rolling日志，不为凑证据偷偷改其RPC/采样或引入logger；如必要字段现有通路确实不可观测，报告最小观测缺口，由Manager裁定，不用虚构等价。matched baseline无probe，shadow不改cache/动作；多个episode的RNG作用域分别按旧continuous与显式key0-reset验证。

完成成对检查后可在同一冻结runtime跑J hf_fixed、hf_event两任务各自eval0 matching smoke2，另保留合同所需r_s30退化短检查；不扩r_s1网格，不看分数调阈值。核对已完成row时序、event只取消未执行suffix、正常action流replan、probe独立key、真实JSONL完整、terminal与退出、video。报告实际probe/replan/已执行丢弃行、wall与sim时间、infer延迟和显存，不声称物理异步实时性。工程与formal matching目录分开，工程不能代替不同模式的matching smoke。

工程验证完成后发布紧凑report（当前状态置顶，历史保持原位）含精确三树/配置/manifest、实际资源、成对证据hash与比较结论、matching gates、吞吐及下一首批命令。Manager核对后启动既定36批：J matched6+fixed/event12，S matched6+fixed6，再J periodic6，每arm/每eval seed自己的matching smoke2→fresh100；当前不直接启动HF formal100。预计>30分钟的工程/传输进程同样登记MAM真实PID，结束收尾再归档；当前可执行工作结束就结束turn，由MAM通知，勿轮询。代码/接口实际错误保留首因与失败leaf后上报，不修改阈值、拼partial或自行修公共源码。

## Manager 当前收尾验收与下一批既有模型评测

Manager已独立验收put-back N/S train0缺失eval0：N17/100、S41/100，分别核对final-review及10个artifact hashes、100连续固定seed/terminal/outcome、进程退出、video flags和command/smoke链。原协议N完整17/27/22=66/300，S41/44/51=136/300；当前42批/4200次执行/20模型/11个完整三eval。两job与smoke清理接受，已进入论文latest evidence snapshot，当前编译PDF仍冻结40批。

接续此前已批准的既有T/U队列，下一步明确先补put-back T(endpoint) train0的eval1/2两批：先核对完整结果去重；确实缺失时，在原已验收RMBench f401f527/bridge f9626636/OpenPI a869498协议和现有T train0 checkpoint上，逐批matching video/no-video smoke2→fresh formal100，固定200000..200099及300000..300099。优先用刚释放且实测可用的C1 GPU1/2，自有ports/目录，按既有错峰启动纪律；登记真实jobs。不能复用新HF reset协议、不能为此新增训练或改代码、不能拼partial/覆盖有效结果。T接口或资产若与runtime不兼容，明确报告实际原因，不能私改。

保留已验收C3 GPU0供HF工程准入，不因HF仍在修复就停掉所有已就绪的原协议工作。HF最新候选还因真实recorder接口不匹配被挡在review，未准入任何HF GPU。T两批启动或确认已完成后发布实际结果/job并正常结束，无需活跃等待。

## 目标、范围与工作区

准备新memory_config checkpoint的RMBench评测，使首批20k结束后可立即按“对应smoke2→正式100”开跑。兼顾列清旧drawer两个模型的offline回归入口，当前只做CPU准备；GPU时段由Manager另行分配。不要修改模型、数据转换、controller、scheduler或MAM，不新建通用launcher/队列框架，不派agent。

通过mam workspace add复用各库一键入口，为本任务建立RMBench、robot-bridge、openpi三个独立worktree/环境。bases：RMBench f022badd11228e5763a301339a5d1fe5574962b4；bridge 8ea6078543a875b5ae223df16891cdc1fe975c66（Pascal作最后CPU增量复核，Manager随后告知）；openpi 929e398（主库当前开发分支，代码树等价42011a3）。先由git解析openpi完整SHA再调用MAM。读三库AGENTS、RMBench docs/guidelines下实验规范以及bridge docs/design/conventions.md。

只在本任务RMBench的experiments/memory_chunk_20260910内新增必要的新schema配置/命令/中文说明，保持原F0文件。其它两库用于固定版本依赖和验证。若发现通用入口缺陷，报告具体复现，Manager交相应owner修，不跨写集。

## 已有事实与要复用的接口

新wire已由真实CPU transforms→Context独立验证；full/serial实际50update、BF16完整参数保存和仅checkpoint恢复均通过。语义输入memory_input_ids(F,)；动作输出robot-only，memory_prediction_ids分别full(H,F)/serial(1,F)。新schema由checkpoint metadata决定，不从实验名称猜方法，不注入legacy_full_feedback_selector替代schema。

优先复用现有robot-bridge benchmark入口、RMBench recorder、命令模板与metadata继承，不复制整份runner。先查现有入口是否仅需配置；合理时新增一个简短入口即可。正式eval结果RMBench/eval_result/memory_chunk_20260910/<run>，说明同名experiments组；禁止新建robot-bridge/eval_result。转换→训练→eval的metadata/config/实际command及commit按现成机制完整继承，不复制代码，不新增runtime/provenance框架。

首批模型为rearrange full_t_plus_1/full_t_plus_30各seed0/1、serial_lag30 seed0、no_memory seed0；put_back full两种目标seed0随专用norm验收后启动。训练owner任务e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe的report有准确配置名、输出路径和模型进程；只读获取即可，不反复监控它们。最终checkpoint为config/exp_name/20000，所有新sim训练来自demo_clean_state；评测场景继续原demo_clean_eval。

每个正式run在一个GPU上串行100，sim与infer共卡。初始条件沿既有seed100000起和同任务共同列表；每配置/ checkpoint先一个含video和no-video各一集的smoke，核对产物后从干净commit正式开跑。默认H50/K30，新full按schema在实际完成后取row30/index29；serial query反馈、no-memory空字段。不中途按成绩改配置或弃掉结果。50条检查按既定10个百分点诊断约定。

## 当前CPU交付

1. 给出可复制的新full/serial/no-memory和put-back评测入口/配置，支持明确checkpoint路径、run名和单GPU，不手写模型内部默认参数。证明checkpoint metadata进入真实backend/scheduler配置，没有绕过schema与smoke检查。
2. 用现有50step产物做仅元数据/命令dry-run，不加载GPU模型、不启动仿真。两checkpoint位置：
   - /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/gpu_smoke_checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/full_tplus1_d10cc01/50
   - 同根下pi05_rmbench_rearrange_blocks_serial_lag30/serial_lag30_d10cc01/50
   保持其只读；Manager暂留至新评测入口的必要技术验证完成。20k正式run仍需各自匹配smoke。
3. 列清旧drawer full_state和serial_soft各5ep offline回归的命令、数据输入和结果位置。旧模型在RMBench/policy/pi05/checkpoints/pi05_x1pro_drawer_sorting_s2m_full_state与pi05_x1pro_drawer_sorting_s2m_serial_soft，先读取实际目录/metadata，勿猜step子目录。可用数据在/mnt/public/xcj/cache/huggingface/lerobot/drawer_sorting_x1pro_shared_memory_s2m_15hz_v2，119ep；原public3路径在本集群映射public。沿既有offline机制、S2M与多字段配置，不另写drawer专用算法。此项先准备，不占GPU。

需要保留的回归按真实边界选择；不要复制大量schema/factory或重跑全部已验收core/loss测试。代码变动目标为现有入口的少量配置和接线，若预估超过约150行可执行代码先说明原因，不能靠删必要留痕压行数。

## 09:34 Manager对入口范围的裁定

采用本实验组的窄audit/manifest适配器。现有BenchmarkRunner要求静态manifest及checkpoint逐文件evidence，而公共模块只有验证入口；本轮保留满足该既有接口的必要构造，不扩展bridge公共框架。删除重复的detach/队列日志/GPU检查/check-smoke逻辑和drawer shell wrapper，README直接列现有drawer_offline.py命令。资源分配由Manager负责，启动长进程仍登记MAM，正式smoke门复用runner。

同一入口明确支持technical-smoke，用现有50step产物验证新wire；其结果标记技术验证、限smoke两集且不能用于formal门禁。正常smoke和formal仍要求完成的20000 checkpoint，formal须匹配该20k本身的smoke。不能另造runner或放宽正式检查。约150可执行行是控制复杂度的目标，必要审计接线可以略超，但交付应解释保留职责和实际行数，不压缩排版凑数。

生成的manifest/evidence按现有metadata继承机制随run保存；说明临时生成物位置与清理方式，避免在eval_result下留下看似正式run的输入缓存目录。先完成CPU交付，GPU授权另给。

## 当前依赖版本与交付

09:59 openpi主开发分支已合入独立review通过的wash与metadata恢复修复，HEAD a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，代码树等价056bcc8。你的openpi尚无活跃GPU任务，请在原登记分支上快进到该HEAD，更新本入口runtime固定SHA；不新建worktree/环境。沿已有dry-run核对d10 full/serial metadata仍进入Context即可，CPU旧路径已有Banach57e9c032独立GO，不重做完整模型测试。bridge继续8ea6078、RMBench继续原base上写本任务增量。Maxwell/Locke冻结运行树保持各自版本。

10:23 Manager接受498cc4c所列公共接口缺口与必要适配范围，但正式审计输入也应使用本任务RMBench/.local/memory_schema_eval下的临时目录，不能写入<checkpoint>/eval_inputs。原因是评测需可读取不允许写入的checkpoint，同一模型也会被多个实验/工作区使用；评测配置归执行run，其已有config_source继承已验证可以保留输入快照。请统一技术/正式临时存放机制，继续通过既有recorder复制到run，保持checkpoint所有文件不变，说明run完成后清理路径；只做这一处小修和相应CPU验证，不扩大runner框架或新造持久缓存。若公共接口确有必须写checkpoint的约束，先给具体代码证据。正式结果仍只在RMBench/eval_result/<group>/<run>。

先提交CPU准备commit并发布简短report，注明task_revision、三库实际SHA/workspace、命令dry-run与metadata检查、GPU待办和预计耗时。Manager验收后分配GPU进行新schema必要smoke或正式模型评测；未分配前不占本机GPU0/1或远端八卡，它们已有任务。超过1小时的正式进程用mam job add登记。

任务自己的smoke和临时文件自行清理，正式产物留共享主repo。正式运行期间冻结所有被调用worktree；结束、处理job并完成交付后由Manager归档环境/分支。

## 12:11 Manager文档修正（本轮仍不占GPU）

CPU实现7378904及空白review95ece0eb已经验收，主库已合入。此次只修改 README_memory_schema.zh-CN.md：
- 新20k训练实际保存在 /mnt/public/xcj/Projects/openpi/checkpoints/<config>/<exp_name>/20000；README目前表格/示例的policy/pi05/checkpoints路径不成立。主RMBench此目录是真实独立目录，只供旧模型；不要通过搬checkpoint或补软链来让错命令成立，修正文档即可。按训练owner最新report列实际路径，full的seed已含0/1/2与put-back的0/1；旧drawer仍用原RMBench checkpoint路径。
- README是操作说明，不需复述CPU review人名/旧版本等待和“未获GPU授权”等瞬时对话。简要说明调用入口和checkpoint自身smoke→formal约束，再给可复制命令。
- 删除 CHECKPOINT=... 以及后续 $CHECKPOINT；具体路径直接写入参数。不用 $PWD 或拼接继承的PYTHONPATH占位来猜工作目录。确有必要的进程环境设置可用具体值放在对应命令前，不建立export变量准备区；技术/正式模板明确指定实际worktree解释器、checkpoint路径与GPU0。
- 保留只读checkpoint、技术50不能替代20k门禁、逐步metadata与清理规则，但避免重复同一说明。暂不改可执行代码、配置或公共框架。
只需核对文字命令与现有CLI/路径、diff-check，不重复CPU模型与GPU检查。提交文档小修并发布report。F0 row1预计约12:50释放GPU0，Manager另通知你开始真实技术smoke及drawer offline；本轮不先启动GPU程序。

12:38资源调整：用户追加BF16导出模型的真实100rollout验证（任务35c9e781-7d2e-49a1-bb4c-25d77b865b3a），本机GPU0在F0 row1完成后优先交给该验证。你的GPU技术smoke与drawer offline顺延到下一张释放的卡，预计F0 row50的GPU1；具体分配由Manager检查后发布。本任务CPU和文档交付均已验收并合入，现阶段继续保留三树，不启动GPU。后续实际命令按分配卡调整，README的GPU0是可复制示例，不代表已经占有该卡。


## MAM 查询更新（2026-09-10）

系统 MAM 已更新：`mam task list` 和 `mam job list` 为带表头的简表，无 --json；完整task信息使用 `mam task status <id>`，实时job结构化详情使用 `mam job status <job-id>`。`mam task show` 仍默认Markdown，保留 --json。`mam task status` 仅显示保存的 job 状态与 checked_at，不刷新进程。按既定频率监控时使用 `mam job list --task e6908de7-4b02-465a-987b-a19eba7a315a` 获取实时进程状态，再结合已有日志检查进度。训练/评测协议、GPU 分配与检查频率不变。

## 15:06 GPU1移交与执行

F0负责人15:01确认GPU1所有自有进程退出、端口19310/19312释放、job已归档。现在授权本任务使用本机GPU1，sim和policy共卡；GPU0仍属于BF16正式100，不占用。复用已验收三库worktree，不创建新环境、不切换正在调用的代码版本。按前述范围依次执行：d10 step50 full/serial各一个technical smoke（各含video/no-video两条），然后旧drawer full/serial各固定5ep offline。实际参数用GPU1和已确认空闲的独立端口，留痕记录真实命令。技术模型效果不作20k模型性能判断；不以技术smoke替代各正式20k匹配smoke。预计超过1小时的程序按MAM登记。发现具体接线bug先报告，禁止绕过schema/gate掩盖问题。结束核对产物与进程、释放GPU1供后续Q2 seed2训练，发布简报。


16:01接口迁移：不要再将job list输出按JSON解析；用task status里的jobs取ID，再逐个job status获取实时结构化结果。既定监控频率不变。新增mam wait jobs/list/stop可按需使用，自动CODEX_THREAD_ID；停止等待不影响实验。
## 16:05 已验收结果文档收尾

Manager接受8eab15f1技术链路与drawer10ep offline交付，GPU1已转交训练。现在在原RMBench worktree的README_memory_schema.zh-CN.md简短记录实际技术PASS的含义、drawer两模型各5ep结果表和真实目录drawer_s2m_v2_regression_5ep_gpu1_20260910，避免读者把旧示例路径当此次实际结果；不把offline MAE写成闭环成功率。保留20k后续命令和每checkpoint自身smoke要求。只改文档，diff-check，不重跑模型。

本任务两份technical_rearrange_*_gpu1_20260910原始smoke已完成技术验收且不能用于正式门禁，可清理；已发布report是技术结论留痕，不另打包全量smoke。正式drawer产物保留。清理自有pycache等临时缓存，不跨清理ad6的step50checkpoint（其owner统一处理）。提交文档并发布report后保留三树，供明日20k评测继续复用。


18:22 MAM精简status已安装：task status 的未归档job摘要位于 jobs.unarchived（无jobs时该键可省略），不是旧jobs数组；job status直接提供status/checked_at/error及unknown时last_known信息，不再嵌套probe或identity。实时进程身份仍由工具内部核对。按新JSON读取；保持既定每小时频率，不因接口变更额外复查训练。


## GPU 调度更新（最新用户指令，替代此前预留安排）

wuwen-1 的现有训练自然结束、完成 checkpoint 保存并释放资源后，整机8张GPU保持空闲，不再启动训练、smoke、offline test或正式评测，直到用户另行允许。明天2026-09-11中午12:00前为其他同学预留GPU的要求改由wuwen-1承担。本机GPU0–7均可按原授权继续训练和评测，启动前核对可用性。本机GPU2–7的原预留限制已取消。不要终止现有训练；若wuwen-1训练预计超出截止时间，及时报告Manager裁决。

## MAM 项目配置迁移完成（2026-09-11）
在/mnt/public/xcj/Projects及其子目录内直接使用mam；已取消--root参数，自动读取项目配置。MAM根目录不变，已发布任务/报告改到project/state-vla，main只用于工具开发。现有task/job/workspace不变；报告仍在原路径编辑，mam task publish正常发布。本轮main已重写历史；后续若开发MAM必须从新的main基线创建worktree，不从旧任务或项目分支合回main。训练与评测业务代码基线不受影响。

## 9月11日04:32 正式评测排期准备（暂不占GPU）
复用保留的三个worktree，读取两个训练owner最新报告，为14个仿真20k模型（12个Q2受控重复+rearrange serial/no-memory基线）列出对应checkpoint、单GPU smoke2/formal100 run名和先后顺序。优先rearrange/put-back per-frame与repeated-endpoint按训练seed成对进入队列，不按中途成绩筛选。每模型先自身smoke（同一run两条rollout，一条video一条无video），核对产物/现有门禁后才能正式100；每run在一张卡串行执行，第50次做正常诊断。产物统一RMBench/eval_result/memory_chunk_20260910/<run>及对应experiments记录。
同时核对wash full/serial新20k的固定5ep offline入口与数据，必须复用已验证的通用memory/S2M机制；读取wash owner已固定的5ep，不另选episode。只准备命令及必要配置，不因脚本名drawer而另写wash专用实现。若接口存在实际缺口，给代码证据和最小修复建议交Manager裁决。
当前本机8卡全在训练，wuwen-1结束后全部停用。现阶段只做CPU/元数据/命令准备，不加载GPU模型、不重新运行已验收的technical smoke或旧drawer回归。预计07:20以后本机4–7先释放供仿真；wash GPU2/3预计07:27后优先完成其checkpoint恢复及5ep offline，再转仿真，具体授权由Manager确认。报告清楚“已准备”和“已运行”的边界；可在现有实验说明补紧凑队列，不新增调度框架。完成准备后报告即可，等待Manager分配卡。

## 9月11日06:53 正式仿真执行安排
本机GPU4–7由训练owner e7e5ac54确认各自训练保存/进程退出并发布释放后，授权本任务依次接用已释放卡；启动前再核对显存，不能抢占尚未结束的卡。GPU0/1仍训练，GPU2/3留给wash offline，wuwen-1停用。本任务负责14个既定模型的各自smoke2与正式100，沿上面已验收入口及固定队列，不修改公共backend/controller/scheduler。先在GPU4/6可用后分别运行rearrange full t+1/t+30 seed0，GPU5/7释放后运行put-back两变体seed0；后续按既定seed配对队列填充。每卡一次一个run，每个run100条串行，sim与policy同卡。为每个并行run使用独立端口、输出路径和必要的进程cache。
必须先确认该20k保存和训练owner CPU门禁完成；实际GPU恢复由本模型匹配smoke覆盖，不另重复整套技术smoke。每个checkpoint的smoke是同一run的2条rollout（视频开/关各一次），核对结果文件、视频可读、metadata及进程退出，再从已提交干净版本进入正式100。若入口或算法有问题，报告首因及最小修复建议，不用变更参数绕过门禁。
正式运行预计超1小时均mam job add，任务内多个job分别登记。50条时对照真正可比的旧实验，偏差超过10个百分点开始诊断；新训练未有可比基准时明确说明，不能强行引用不同配置成功率。保留正常失败与全部100条结果，不能按中途表现重新抽样。完成后更新本组实验说明，按协议清理自己的smoke/临时产物，保留正式结果及smoke门禁必要摘要；进程退出核验并archive job。保持active turn，使用mam wait jobs --task等待并结合日志做50条中检。报告阶段结果，不把CPU准备或smoke替代正式实验。

## 07:52 资源与实验台账补充
wash训练owner已验收并释放GPU2/3、归档任务。正式wash offline只使用GPU2串行两模型，因此GPU3现授权本任务接用（先核对实际显存/端口），按既定队列启动rearrange t+1 seed1自身smoke→formal；与其配对t+30 seed1保留优先队列，下一张释放卡执行，不按成绩挑选。GPU0/1仍训练，本任务不使用GPU2。4–7原分配不变，wuwen-1停用。
用户今天暂停统一架构重构，所有实验继续冻结源码。后续文档结果应更新本组EXPERIMENT_LEDGER.zh-CN.md对应模型行：已合入RMBench主xcj-dev（bc43568及整合commit），包含研究动机/假设和固定模型路径。勿在正在被formal使用的源码树中merge/修改文档；先完成这轮运行，后续安全整合文档并更新结果/实际eval链接，保持快照时间准确。重点继续50条诊断与完整100结果，不把training loss或smoke当正式成绩。

## 集群C迁移排期与对照交接
用户要求C评估环境验收通过后，后续新eval优先放C；当前已启动本机run继续收尾，不中途移动。环境task5773b6ec负责人Banach正在三库环境/三机smoke/一个100对照验收，暂不扩MAM。请交一个已完整收尾、可直接复现的本机100基线，给成功数、真实失败类型是否影响可比、三库冻结commit、ckpt及数据/seed/命令和必要资源清单；Manager将裁定C正式对照。不要为迁移修改active worktree。C未准入前不自行在C启动正式run；准入后会为后续任务发布C根README与手工workspace/TASK-ID要求。
同时本轮已完成的100run及时更新稳定实验记录，按原协议记录50检查/最终成功率与模型seed，不仅留在MAM报告。给Manager当前已完成结果、还在运行/排队清单和异常裁定需求，避免准备迁移时漏掉结果收尾。

## 9月11日第二批训练并行与台账
Manager已安排7ae41311训练rearrange serial/no-memory各seed1/2（GPU2–5）；695bc51f准备put-back serial/no-memory seed0（GPU6/7，配置门禁后正式）。补齐既定B组，不依赖C或Q2结果；不要占本机GPU或wuwen-1。请复用/安全创建本task文档worktree更新EXPERIMENT_LEDGER，区分已派发/准备/实际训练中，只有读到job及updates才能写运行中，后续正式目录由owner提供后链接。加入各项目的（B组训练seed重复及put-back同骨干能力基线）、预期检验而非预设成功率、checkpoint/eval待办。引用两个新task报告核对，交文档commit由Manager集成；不改冻结eval代码树。4个旧abort继续保留证据，8未启动仍待C验收，2完整结果保留。

## Manager待办清理与恢复责任
恢复后续评测准备。C任务2a879870已三机smoke通过，renderer修复17b55bf/创建优化9c71a3e已独立review；正式100正在运行，首50为34/50对本机35/50，尚未完成5pp验收。先在现有任务整理剩余14模型清单、已完成/不完整/待跑状态和准确模型目录，确定迁移C的最小批次，不重复跑成功项。C最终验收之前不启动新GPU评估，准备完给Manager阶段report；不要为了active伪造job。原先get_obs修复已有378da0ac/ae463958后续报告，应先核对已修状态，不重开已解决问题。

## C准入期间接续实际模型准备
Manager接受14行队列状态(2完整保留、12待评)。现在提前传输12个待评模型到集群C，属于既定eval准备，不需等待最终100准入。先读C:/mnt/public/xcj/Projects/state-vla/README.md及2a879870已用checkpoint传输记录，沿既有稳定openpi/checkpoints布局，复用已有模型不重传，不覆盖活跃模型/环境。源只读20000 params/assets/metadata，使用本集群wuwen-nx-aic与C wuwen-4090-aic高速路径；最多两条并发，错开至少60s。先核实两侧磁盘/源目标对应，不复制训练数据或cache。真实rsync进程在本机登记mam job，完成后核对文件/metadata完整性和传输结果，失败不写ready。开始第一批后使用mam wait实际保持active（不能仅后台wait后final）；不逐分钟模型轮询。优先put_back_full_t_plus_30_s0与rearrange_full_t_plus_30_s0，后续按表序推进其余10个。此阶段不跑新GPU评估。你提交13192bb文档需先由Manager集成后再清理docs临时树；原三库树暂留供队列准备。

## 集群C最终准入，放行既定12项评估
Manager核对2a879870最终证据：C100/100固定seed、70成功，本机69，19checks通过，255文件回传hash一致。现放行已整理12待评项，不重复2完整项。按C README在C workspace/本TASK-ID建自有三库worktree/环境，运行版本沿已验收RMBench17b55bf、bridge8ea6078、openpia869498，固定GPU映射和ICD；如某variant缺能力/入口需要修复先交Manager，不随意换算法。每模型完成自身2rollout有/无video smoke+产物检查，再固定源码同GPU串行100。模型到达即启动，不必等12个全传完；首批优先已指定两s0，先一机一run(C1/2/3实际空卡任选)，首批健康后可每机最多两run但每GPU仅一run，端口/cache独立，先报告实际资源不抢他人。每run前50比较可比历史/查基础设施，完整结果独立exp-group/run记录，不拼旧partial。真实job登记、本机MAM运行，等待使用mam wait。后续回传到本机RMBench同exp-group，保留旧两完整baseline。不要依赖2a879870或5773远端临时worktree/venv，它们将收尾清理；需shared stable cache/assets/model可继续用。你13192bb文档已合本机f58ac38，文档树可自行清理。

## 后续评估与台账、首次infer超时裁定
继续负责现有已完成模型队列和新增完成训练的接入。用户明确：已跑完训练要安排eval，eval后整理实验台账。核对695bc51f与7ae41311的最新report，只有最终20k产物完整且训练成功退出后接入；未完成的不要当作可评。现有有效100结果不重复。

针对已报告两个smoke在首次infer 30秒超时：授权在自己独立bridge worktree调查并做最小基础设施修复。先用失败日志/单模型串行有界诊断验证是否JAX首次编译超过预算，不预设首因。若证实首次编译，可只为首次infer提供合理有界预算或明确warmup；后续infer预算保持，不能修改算法/seed/horizon/memory或把超时当成功。代码需CPU有意义验证并提交，先报告commit与证据供Manager独立review，准入后再同模型smoke2→正式100。不在失败原因未明时重复并发smoke。传输继续按既定两路上限与间隔。

实验台账统一RMBench/experiments/<exp-group>，结果RMBench/eval_result/<exp-group>/<run>。逐run记录研究问题、设计变量/控制变量、预期结论、train commit/config/schema/seed、训练及checkpoint路径、eval commit/config/路径、实际成功率和失败分类、与基线差异及限制。现在先建立完整待评清单与状态，正式结果到达后更新，不等全部完成才记账。前50与已有可比结果差超过10个百分点先排查；固定100同GPU串行，单个smoke含2rollout(1video/1无video)，产物检查通过才formal。实验代码与台账交付提交，清理短smoke等临时产物但保留必要故障证据。

不用无变化等待进度写report或commentary；mam wait挂起时不做几十秒一次轮询。完成实际可执行工作后再等待事件。

## Manager准入：f962663首次infer预算
独立review03d538a0通过。接受显式policy_first_infer_timeout=90.0，仅首个infer；其余30s不变。冻结bridge f9626636c4776d8eb15f9c556775cb2d12c000e5，RMBench17b55bf、OpenPIa869498及原模型/seed/H50/K30保持。先在本机独立代码树准备并提交运行清单/config的最小更新，再同步C的本任务部署树；后续代码修改均在本机完成。
立即恢复首2项各自新leaf matching smoke2，避免同时冷启动：先启动第一项，首infer完成后再启动第二项。每项完整video/no-video、metadata、exit、资源收尾门禁通过，即可直接同GPU正式100，无需再次等Manager批准。失败保留证据不得当成功，超过90s仍退出并报告，不自动无限放大预算。
首2项健康后接续12项队列，按现有授权最多2/host且1/GPU，实际资源冲突优先避让。正式50截面/100收尾与台账同步，raw结果回传本机RMBench的同组两层目录。不能把串行27.23s诊断写成严格证明并发编译是唯一根因。所有代码修改和测试保持本机，C只运行部署副本与GPU程序。
台账5640242已通过review，Manager合入RMBench主xcj-dev；后续增量基于最新台账更新。不要重复已完成2run。

## 台账一致性收尾要求
Manager发现当前EXPERIMENT_LEDGER的队列表仍把已完成首批4项写作formal运行中，只在末尾追加了结果。请直接更新每个run对应表行的当前状态、最终成绩、失败分类及稳定本机结果链接；相同run出现的主表/状态概述保持一致。历史失败作为证据保留，但不能让同一当前表同时呈现旧状态与新状态。不要把台账退化成按时间堆追加日志。原12项全部完成之前继续本任务，不因阶段报告结束turn；完成事件用mam wait实际await。

## 新完成B模型接入
7ae41311最新report已验收rearrange no_memory seed1/2两个20k，训练job已归档，checkpoint-only恢复通过。现在接入这两个模型传输与C eval，不等serial seed1/2结束。路径以该已发布report为准；复用已验证no-memory variant，新增明确seed/run路径，不改schema。继续同源demo_clean_state/bs32/20k/H50/K30和各自smoke2→100门禁。给这两个新增模型分别建立台账行和传输/评估状态，seed0/1/2最终按独立训练重复分析。原12项仍运行的4项不打断，空位后接续。之后695和7ae的新完成产物同理接入，不重复重训/评估已有结果。

## 用户更新：每个checkpoint三个eval seed，每seed100 rollout
本轮仿真checkpoint（既有Q2/B与后续验收完成的B/U）统一eval_seed=0/1/2，每seed独立run且单GPU串行100，总计每checkpoint300。training_seed与eval_seed分列，结果路径包含两者；已有有效eval_seed0完整100和正在运行seed0全部保留，不重跑或覆盖。初始14个checkpoint是42个eval run，再按完成训练逐项加入，不能只补高成绩模型。wash属于真机/offline，不套RMBench仿真100协议。

立即核对现有seed入口：eval_seed必须实际改变仿真初始条件列表，不能只改目录名或只改policy RNG。沿RMBench既有eval-seed映射生成3组互不重叠的100条件，eval_seed0继续原100000–100099；如果现有映射不支持，先提出明确可复现映射并本机最小实现/测试交Manager审阅。各比较模型使用同任务同eval_seed的完全相同列表，保留实际环境seed/接受规则；推理随机种子也需明确记录保持对应可比。不可暗中扫seed、拼接失败partial或把3个训练seed当3个eval seed。

资源授权更新：解除此前每host最多2run的限制，可使用C1/C2/C3所有实际空闲GPU，一卡一个run，不能抢其他人的卡。按当前空闲卡列明确host/GPU/port/run计划再启动，进程与缓存/端口按run隔离。同一checkpoint可跨卡并行3个eval seed，每个seed的100条不能拆分。冷启动分批错开，保留首次90秒上限，不把扩并发掩盖成改时序。别只使用C2/C3四个槽而让其他已验收可用卡空闲。

沿既有匹配smoke门禁，各run一个smoke含2rollout（1有video、1无），检查产物后才formal；相同checkpoint复用只读文件与已安装环境，无需重新传模型/装环境/重训。代码在本机独立树修改提交，新runtime版本用新部署worktree，不改活跃eval树。seed支持或调度新增代码须交独立review再大规模启动；既有seed0合法运行继续。

台账按checkpoint列eval0/1/2的成功数、每项路径及合计/300；未齐时明确部分完成，不把缺失填0。完整后报告3组结果及合计率，仍按训练seed分别报告，跨模型按相同eval条件配对比较。研究计划从1变3 eval seeds为用户此次扩大样本的决定，记录调整日期，不把看过seed0后的新增写成原先预注册。逐run50检查和100收尾/回传/归档保持。先交明确seed映射和并发开跑计划，再持续执行授权队列。

## Additional completed B checkpoints (2026-09-12 14:02 CST)
7ae41311 has now finished and validated serial-lag30 train seed1 and seed2 as well as no-memory seed1/2. Their report contains exact paths and CPU restore evidence. Include all four in the existing authorized C evaluation queue: each train checkpoint eval seeds0/1/2 x100, preserve previous valid eval0, no change to protocol. Do not wait for further handoff of these models. Continue local-only code fixes with independent review for any new eval seed implementation before scaling; return current seed mapping and concurrency proposal if not yet published.

## Manager approval after independent eval-seed review (2026-09-12 14:45 CST)
Review300c4873 PASS accepted: RMBench f5087496a0f7c892bd322708e4ac0bbdeb74e523, bridge f9626636c4776d8eb15f9c556775cb2d12c000e5, OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4. Actual runner CPU mock verifies profile fixed.seed, rejected-candidate semantics, per-model same task/eval seed lists, smoke manifest mismatch rejection, trainingseed mismatch check and 14-run port/cache isolation. Deploy this code into your new manual TASK-ID C runtime copies (do not mutate any active trees), then execute approved first-wave14 and remaining queued models as resources allow: perrun smoke2 -> formal100, 3evalseeds/checkpoint, cold-start stagger, real-freeGPU checks, register each long job. Do not wait for further Manager approval. Record actual accepted-seed lists and check comparability in ledger; missing evals not zero. Existing14 eval0 retained. MAM proactive wake rollout will be announced separately; until then retain current monitoring.
# Manager approval: smoke/formal cache template fix

Independent reviewa8946c75 PASS accepted. Exact RMBench commit is 9d8f47887a50ea691e5624de139f10bfcfb54412, not the incorrect full hash in your previous report. Reviewer reproduced old actual BenchmarkRunner gate failure and fresh-patched smoke2/formal100 success with fake services (CPU only); 9 runner tests pass. Correct your report's commit identity.

Deploy approved9d8f478 with unchanged bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 and OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 in a clean owned C runtime. Start a new matching smoke2_r2 -> 100ep_r2 pair first, preserve failed evidence and never reuse old literal-command smoke. Once gate succeeds continue all previously authorized first-wave14 and remaining B/Q2 queue, 3eval-seeds/checkpoint, real-freeGPU checks, one run/GPU, stagger first inference, register jobs, report/ledger actual status. No further Manager approval is required for each run. MAM upgrade is not installed yet; current monitoring remains until migration notification.
# Verify effective Warp cache path, without altering active evaluations

User challenged the assumption that Warp caches must be separated by GPU; Manager agrees GPU ordinal is not a cache validity key. Manager read installed RMBench Warp0.15.1 on both local and C c-eval. That version uses module-name/output-architecture paths and hash sidecars, and its own build/config/context does not read WARP_CACHE_PATH; official v0.15.1 limitations warn about shared caches across processes. Earlier audit and9d8f478 review established command-template isolation, not effective Warp cache selection. We must not claim runtime isolation merely from an env string.

Read current simulator startup logs for actual printed kernel_cache_dir, and inspect actual cuRobo/Warp/bootstrap code to see whether any layer applies WARP_CACHE_PATH explicitly. Record installed version, selected real path and relevant code evidence in your report; do not rebuild/upgrade Warp, clear caches, change running commands or stop healthy formal runs. If env is ignored, correct the earlier report/guide claim and propose smallest necessary next-run fix with tradeoff (shared cache reuse vs concurrent compile safety), rather than silently adding per-run caches. GPU-number partition is an old script convention, not intrinsically required. Keep current approved evaluation queue moving unless actual failure requires intervention. User guides must describe usage; technical audit details belong report/development evidence.

## Manager decision on verified Warp cache findings

Your 17:40 evidence is accepted: Warp0.15.1 ignores WARP_CACHE_PATH in this worker, and the prior run-isolation claim was too strong. No cache corruption has been established. Continue current healthy runs and the already-approved queue. For next runs keep the existing host-local cache and stagger first compilation/inference on each host; no new code patch or further review is required merely to continue this existing startup discipline. Do not add GPU-number or per-run cache directories now. Escalate only concrete compile failure or a need for truly concurrent cold starts.

Keep the technical correction in the task report. The usage guide only needs to explain selecting a run and its output/ports; remove both the old Warp-isolation claim and detailed WARP_CACHE_PATH limitations from that user-facing guide. Do not replace implementation claims with more implementation explanation there. Continue ledger updates in the safe documentation tree and supply a consolidated docs commit/branch for Manager integration, without merging into active runtime trees. Existing rollout protocol and resource authorization remain unchanged.


## MAM proactive wake is installed (2026-09-12 18:35 CST)

The installed version now passed all191 source tests, optional wait compatibility, API compatibility and the isolated six-turn actual delivery acceptance. The production per-project service is healthy and bound to the Manager. This section supersedes all earlier requirements to remain active solely for monitoring or to poll hourly.

Finish currently executable work and publish actual results/status, then end turn normally while registered long jobs continue. MAM wakes a dormant executor for any stopped unarchived job, even when other jobs are running. Handle results/cleanup/archive according to this task, and end again when no immediate work remains. A running-only task does not need a standing active turn. Do not stop experiments or archive running training/eval jobs merely to end your turn. Manager receives completed/no-job task follow-up after review routing.

Optional `mam wait`, `mam wait list`, and `mam wait stop` are retained for a concrete need to wait within a turn. Do not produce unchanged waiting updates or start a custom loop to keep the turn alive. Existing experiment protocol, rollout checks, artifact paths and resource authorizations are unchanged. If a queued next run can be started now, continue that work before ending; automatic wake does not replace executing the queue.

## Complete put-back B training handoff

Manager accepted all six put-back serial_lag30/no_memory train seeds0/1/2 from task695bc51f final report f317c3d64b535e13fe2b8489df6bdc01c448eac9; all six checkpoint-only real inference gates independently checked in stable OpenPI logs. Training results are accepted; final temporary-cache cleanup precedes task archival. Source commit a7f3e07346cee7260cdc3a618eedc38c0702da61 retained as codex/put-back-memory-baselines. Use that published final report for exact stable checkpoint paths, configs and artifacts, never its deleted training workspace. Add all six to C transfer/eval/ledger, preserving already-completed work; each checkpoint still eval seeds0/1/2 x100. No repeated training.

Manager is assigning a separate diagnosis of repeated C2/C3 episode22 worker EOF. Preserve their partial evidence as not reportable and do not restart those affected slots blindly. Healthy C1 runs and artifact transfer/ledger work continue. Coordinate evidence with the diagnosis task through reports; do not change active runtime code or assume Warp/renderer causality from stderr alone.

## EOF diagnosis adjudication and result-count correction

Manager accepted diagnosis923ea224: previously reviewed renderer-reuse fix17b55bf is absent from r2 RMBench9d8f478. That exact patch is now being restored and CPU-checked in the diagnosis owner's independent tree, followed by independent review; do not deploy before the new combined candidate is approved. No driver/Warp edits or blind partial retry. Healthy C1 work and checkpoint transfers continue.

Correct the six failed run summaries using raw seed_preflight evidence: episode22 has accepted=null and status=error, with22 completed terminal episodes plus one reset-error record; it is not23 accepted rollouts. Keep each partial not reportable and preserve raw evidence. Update derived failure summaries/ledger consistently without fabricating complete denominators. Old complete C1 results remain valid. Prepare future rerun names/queue using original seed sequences, but wait for explicit candidate approval before GPU gates on the affected hosts.

## Manager approval: deploy reviewed renderer restoration and resume gated evaluation

Review87308f53 PASS accepted. Approved RMBench candidate77477931bee18c2476bea36b400ab45dc67d9ebe (9d8f478 + exact old17b55bf patch as eba81b4 + CPU regression), preserved as codex/c-eval-renderer-r3. Bridge remains f9626636c4776d8eb15f9c556775cb2d12c000e5; OpenPI remains a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 for the existing compatible queue. Do not overwrite running r2 trees or silently omit this patch when creating a new deployment. Verify the effective deployed commit and renderer source before launching.

Deploy a new owned manual C workspace runtime tree for r3 using existing .local entries and shared read-only resources. On each affected host C2 and C3, once an actually free GPU exists, reuse the existing bounded40-reset worker harness on a fixed mapped device. Require40/40 accepted, exit0 and no renderer/native EOF/segfault/traceback marker. Record host/GPU, frozen commits, exact command and evidence. Do not install drivers/change Warp/cache policy or stop external work to obtain a GPU. If unavailable, clearly leave that host pending rather than claiming validated.

After that host's40-reset gate passes, its matching video/no-video smoke2 must pass before each fresh formal100 run, with original fixed checkpoint/config/seed sequence and a new r3 leaf. Host-local approval is independent: C2 can continue when its own gates pass without waiting for unavailable C3, and vice versa. C1 healthy r2 runs finish unchanged; subsequent r3 runs on C1 require matching smoke under the new frozen version. Preserve all valid completed r2 results; rerun only infrastructure-failed/incomplete or not-yet-evaluated items. Never concatenate old22terminal partial records or use smoke success rate as a selection gate.

This authorizes GPU lifecycle gates, matching smoke and continuation of the already-approved full evaluation queue after their stated checks, with no additional per-run Manager permission. Reuse historical harness/evidence from2a879870 and diagnosis923ea224; do not design another framework. If a new model requires source beyond the approved OpenPI snapshot, report the precise incompatibility instead of changing it silently. Long runs remain registered, completions verified and archived, result/seed coverage ledger updated. Finish currently executable work then end turn for proactive follow-up.

## Resolve missing lifecycle harness and finish usage-document handoff

Manager clarifies the earlier 'reuse harness, no new framework': it does not forbid a small necessary replacement when the archived temporary harness is gone. Check the existing Git/history/retained evidence once; if the script cannot be recovered, reconstruct the minimal40-reset check using existing worker/proxy entry points, fixed seed100000–100039 and fixed-device contract. Keep it a small versioned utility in your own local independent tree, not a separate framework; produce CPU checks and commit for a focused review before GPU use. Report exact invocation so it survives workspace archival. Lack of the old temporary file is not a reason to leave this implementation pending indefinitely. Current GPU occupancy still prevents actual C2/C3 gate execution, and must remain clearly pending.

User asks whether environment/docs are fully done. Current ledger changes exist only on your docs branch while stable RMBench remains295effb. Provide one clean, consolidated documentation branch/commit for safe integration, including current C-ready/eval state, corrected partial counts and usage-only guide. Keep operational instructions in the existing C root README and relevant repo usage docs; put audit internals in reports. Do not edit active runtime trees. Clearly distinguish deployed code, CPU PASS, pending GPU gate, and completed formal result. Coordinate ledger candidate with Manager; no repeated model tests for documentation.

## User correction: low-occupancy C1/C3 GPUs are available for evaluation

User explicitly confirms C1/C3 GPUs have low memory occupancy and util0 and authorizes using them for eval. This supersedes the earlier conservative assumption that any external process or nonzero memory means unavailable. Recheck nvidia-smi memory free/used, utilization and known jobs/ports; compare actual free memory with the measured simulator+policy peak and headroom from accepted runs. Cards with adequate free memory and idle compute are eligible even if another VM has a low-memory resident process or [Not Found] PID. Do not terminate another user's process or require zero allocation. No artificial per-host two-run cap; use eligible resources with the existing staggered cold-start discipline.

Prepare concrete host/GPU/run assignments now. Focused review18db597f of bf3474 gate is underway. CPU/source prep and resource assessment can proceed immediately; after Manager accepts gate review, execute C3 40-reset then per-run matching smoke/formal, and C1 new-r3 matching smoke/formal as already authorized. Maintain correct fixed versions, seed lists and no overwrite of healthy completed results. If a card is actually unsuitable, report measured free memory vs needed budget rather than just presence of a process. This applies to C1/C3 per user's current observation; assess C2 separately.

## Manager acceptance of bf3474 gate; execute authorized C1/C3 plan

Independent review18db597f code PASS accepted. Gate bf34743334efc98440fa9b05e3f2f05e8303846a is authorized for C r3 deployment and actual40-reset use. Bring the gate commit into the owned r3 runtime before any active run starts; confirm renderer patch remains and freeze atbf3474 (bridge/OpenPI unchanged). On eligible low-occupancy C3 card run40-reset, then matching smoke/formal under prior host-local approval. C1 matching smoke/formal may continue on eligible cards. Existing nonzero low-memory resident processes are not automatically blockers; use measured free-memory/headroom as latest user instructed. Long gates expected>30min are jobs under updated AGENTS.

The docs reviewer compared the declared r3 command against the old local295effb-based code rather than the explicitly named C r3 runtime. Manager verified bf3474 runner defines --training-seed/--eval-seed, uses train/eval audit suffix, and yaml fixes bridgef9626636. Those three claimed incompatibilities therefore do not block the GPU gate/queue. Reviewer is correcting the context before documentation integration. Do not rewrite functioning runtime selectors to match old stable source. Provide actual gate/run/job progress and keep ledger deployment SHA accurate afterbf3474. Follow original fullseed/no-partial protocol. No further per-run approval required after stated gates.


## New Manager adjudication: 2e9677c interpreter fix accepted (2026-09-13 CST)

Manager 01a09657-e0f3-7352-b726-aba5bbd5d498 accepts independent review e755c753-4acf-4958-85f4-7595fba739a0, published report revision 8bb81b0637a101f1ce883df9b5c72695afda792d. Exact approved RMBench range is bf34743334efc98440fa9b05e3f2f05e8303846a..2e9677ce8ec9f623395184f63f32ddafa66e5e44, not the auto-captured source-task main worktree 3775d4a. The candidate preserves the virtualenv Python symlink while retaining absolute paths and user expansion. Manager independently inspected the 2-file diff, frozen bridge f9626636 Popen path, and reproduced numpy import success via venv path versus ModuleNotFoundError via its resolved base interpreter. Review PASS is accepted for this startup fix only; C3 GPU lifecycle is still unverified.

Proceed with the existing authorized queue: deploy exact 2e9677c into a NEW owned C runtime/worktree for C3; preserve bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 and OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4. C1/C2/C3 share storage, so a different SSH host does not make the same path independent. Do not update/reset/checkout the shared c-eval-renderer-r3 tree currently used by C1 bf3474 formal runs. Reuse existing environment-entry scripts and read-only shared assets, and verify actual HEAD/clean state and renderer reuse patch in the new tree before launching.

On an eligible C3 card, run the fixed fresh 40-reset gate (100000..100039, mapped cuda:0, system ICD) with new receipt/log paths. Keep the failed bf3474 zero-reset receipt and stderr. Only after this host's 40/40, exit0 and zero infrastructure markers may its per-run matching video/no-video smoke2 lead to fresh formal100. Existing resource authorization, including low-resident-memory cards with enough measured headroom, remains effective. Keep model/train-seed/eval-seed/protocol fixed, freeze each new runtime, preserve valid results and never concatenate old partials. No further per-run Manager permission is needed when those gates pass. C1 existing work continues on its current frozen version.

Publish exact new runtime paths/commits, gate receipt and outcome, jobs and current queue/ledger state. Any new runtime code change outside this accepted candidate needs focused review before deployment; CPU PASS must never be reported as C3 40-reset PASS. Keep long jobs registered (>30 minutes) and finish actionable work before ending turn for MAM wakeup.


## 当前Manager执行者交接（2026-09-13）
Manager 01a09657-e0f3-7352-b726-aba5bbd5d498 将用 mam task rebind 将本任务交给当前对话新建的 terra/max 执行者。以 mam task status 的当前 agent 为执行权限依据；旧执行者若发现已换绑，停止执行本任务，不再写workspace/report或处理job。新执行者换绑前仅只读准备并结束turn，待Manager明确接续消息后开始工作。换绑后直接继承原TASK-ID、全部现有workspace/worktree/分支/已发布报告与运行job，不再次workspace add，不复制或重启/重复登记job。既有任务目标、数据与评估协议、冻结runtime、独立review门禁和资源授权均不变。完成可执行事项正常结束turn，由MAM唤醒；不得高频轮询。


## 用户预算重排：暂停新增开跑（2026-09-13）
用户否决普遍每配置3训练seed的旧预算，要求优先RMBench九任务覆盖，Manager正在重写论文主张/文献定位/最小实验清单。自此不再按旧队列启动新的训练、smoke、formal或追加eval seed；此节覆盖所有此前自动扩展授权。已经运行的job自然收尾，正常核验/记录/归档，保留checkpoint和完整结果；不杀训练、不丢弃不利结果、不重启失败项。已训练未评模型只整理可复用清单，等待新排期，不自行开跑。当前可执行收尾完成后正常结束turn，MAM自动唤醒。

## 用户批准九任务计划并恢复评测（2026-09-13 09:35 CST）
用户已批准/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN.zh-CN.md实施，覆盖优先，默认每个模型3个eval seed各100。此节替代此前全面冻结。Manager已发现Codex拒绝MAM直接turn/start唤醒multi-agent v2 subagent，现用原生collaboration手工触发收尾。先核验九条stopped formal的完整100、固定seeds、terminal/exit/基础设施错误，回传可复核结果并归档job，不拼接不重跑valid结果。随后授权在已验收C runtime和实际空闲GPU上，按固定顺序补已存在模型缺失eval：先seed0的N/S/J覆盖rearrange+put-back，再补已有T/U六seed各自缺失的批次并保留原seed0/1/2，不新训练；已存在J/N/S额外training seed的300补齐用于预算判断。U必须先收到训练owner的验收manifest。已通过的matching smoke能复用则复用，不为评測seed重复训练。用独立/冻结runtime，不改活跃shared tree；不占wuwen-1。完成本轮收尾先发布紧凑报告，再开展合理并发续跑；长进程全部登记MAM。
## Manager验收与U可评清单（2026-09-13 10:02 CST）
Manager已独立重算新增9批raw 100 terminal/连续固定seeds/成功数并核对final_review五份artifact hashes，接受9份完整正式结果及job归档。U6已完成最终20k验收，Manager已逐项核对checkpoint布局、训练finalize日志、12个CPU/GPU原始restore JSON的checkpoint/step/seed与完整shape/BF16/finite证据。接受稳定manifest `/mnt/public/xcj/Projects/openpi/checkpoints/memory20k_cbbba844_manifest.json`，sha256 `681cc5aad845bc6863bb5bc9af0b0d59a60a3fbebfef90b7c2af479554d56e5b`。该文件每条validation_artifacts与training_log均有稳定checkpoint父目录artifacts来源；使用冻结6266bd8模型及其initial schema。按前述N/S/J seed0优先、再T/U已有training seeds完整300顺序接续；不要以旧report“冻结新增”段覆盖本次已发布授权。迁移只复制缺失资产并登记预计>30min传输，C新runtime若需要U metadata能力应独立树，不能改活跃r3树。

## Manager准入：put-back N/S YAML（2026-09-13）
Manager已直接SSH读取f401f5279c95451eb424ac98b831bab5552b2120的完整17行diff。N空字段joint_dense、S phase/origin_mat serial_token且query_selected/query与已报checkpoint合同一致；改动限独立准备tree、不动在跑runtime。准入该候选继续每新路径必要GPU gate，gate通过按现有seed0三eval优先队列正式启动并登记，不再等第二次代码审批。保持bridge/openpi冻结、禁止覆盖结果；报告可追溯metadata与receipt。

## 当前用户新增授权：高频状态推理与事件replan评测（2026-09-13 晚）
用户已授权复用checkpoint、仅修改推理、在4090集群开展高频状态更新与偏差触发replan评测，不重训。源码工程task0acf5d43-91b6-4171-b727-e3fe0f7e7939由putback_trace_alignment负责，独立review由Manager安排。先继续立即处理当前两个stopped rearrange J eval1/2，完整核验并归档，4条仍运行的N/S自然收尾；不因新方案覆盖或丢掉旧结果。

同时准备新评测：只读核对C1/C2/C3当前GPU、已验收host gate、冻结runtime、现有rearrange/put-back J0/S0/T0 checkpoint可用性，资源状态用实际memory/利用率/自有job判断。为独立新runtime准备精确run配置/命令和manifest，schema/权重不变；不能在活跃r3目录checkout/cherry-pick。第一轮rearrange+put-back已有模型可以立即做开发评估，不等待cover/swap-T新模型；后两者作为后续跨任务验证保留，不算已完成泛化。

Manager随后发布精确arms/触发阈值/试验计数。代码未验收前可做CPU/dry-run/资源及checkpoint准备，不能将新模式当已上线。源实现+独立review通过、Manager准入后，每模式匹配必要smoke2（video/no-video），通过即可按冻结清单正式3 eval seed×100，无需逐批重复问许可。首先跑小规模预先固定seed的诊断/吞吐gate，不按成功率挑阈值；任何性能pilot单列且不拼正式结果。把推理probe数、action replan数、K分布、事件/偏差触发、实际执行/丢弃行、wall/sim时间、峰值显存及失败类别加入原始记录验收。任务继续承担所有长job登记、完成收尾与结果报告。

在新模式准入前不为此空置全部4090；原有已授权eval可接续，但至少明确下一张可用于新smoke的卡和预计释放时间，避免全部排满数日。预计>30分钟的传输/正式程序都登记MAM。本轮不创建新通用调度框架、不自行改算法合同。

## 新推理首轮评测清单（Manager冻结）
科学/实现合同以0acf5d43最新版为准。0新增训练；现有rearrange_blocks与put_back_block各train0 J/S，同H50，原始模型/数据/seed列表不变。第一层J HF-fixed(K30,probe5)与HF-event(Kmax30,probe5,phase window3同时间rows中>=2不一致，连续2次,minprefix10)两臂×2任务×3eval=12个新正式100集批次。原J baseline K30复用已验收结果；新runtime关闭/影子模式必须先验证等价，否则补新baseline且明确原因，不默默换比较来源。

第二层S HF-fixed K30/probe5×2任务×3eval=6新批；原S baseline复用完整300。第三层J HF-periodic K10/probe5×2任务×3eval=6新批，作为频繁replan对照，后于核心12批与S路径准入；它不声称与event平均调用数严格匹配。总24新批=2400正式执行，existing baseline去重，不增加training seed。T endpoint输出本轮不进入frame-deviation/HF，保留原协议评测。

新功能每种路径先匹配smoke2含video/no-video；另做J baseline/shadow的同checkpoint/seed/action RNG成对工程核验，确认额外观测不会改变任务cue、动作流、仿真随机性或终态；保存实际command序列/进度证据而非只比成功率。工程seed固定900000/900001，不进入正式seed100000/200000/300000各100清单。依据smoke仅判接口/基础设施/执行合同/吞吐，不根据分数调阈值或换任务。r_s1仅可做短吞吐probe，不自动扩展到正式全网格。

代码review及Manager准入后按第一层优先从可用卡并发开跑，每批真实job登记；为保证响应，不需要收齐全部24批才发布进展。完成100集按原terminal/seeds/exit/video/metadata/rawhash合同验收，负结果保留；出错只修基础设施并独立运行完整新批。扩展cover/swap等留在后续，不能把本轮2任务说成九任务验证。

## Manager接受smoke合同核实后的更正
保留既有正式门禁，撤销900000/900001要求，不为它新增engineering seed CLI。baseline/shadow成对工程smoke使用既有eval0的100000/100001，独立目录标明工程等价检查，不据分数改阈值；不作为不同HF模式的matching gate。每个新正式配置/每eval seed仍跑严格匹配的smoke2→formal100，source/manifest/hash规则不放宽。明确random_light=false与crazy_random_light_rate=0留痕；先核对原baseline实际设置，若改变了原环境条件则补同条件baseline，不沿用不匹配成绩。新增试验数24批不含短工程smoke和因必要环境对齐追加的baseline，后者需明确单列原因和数量。

## Manager 六批终验与缺失 eval0 的接续

Manager 已从 C 原始记录独立复核最新六批的 final-review/30 artifact hashes、600 连续固定 seed 与 terminal/outcome、scheduler/自有进程退出、video flags 和 command/smoke 链接，并核对 stable C3 40-reset receipt。论文 commit 913b086 的 evening snapshot 现为40批/4000集/20个已评测模型，其中9个完成三eval seed；不能沿用18模型或误算为11个完整300模型。实际视频解码/全日志扫描仍为 owner 的验收范围。

put-back N/S train0 在此快照只有 eval1/2，eval0 尚未计入。请立即核实是否已有完整、未汇报的合规 eval0（只认连续100，不拼 partial、不把工程smoke算入）；若没有，沿已准入的 f401f527 RMBench / f9626636 bridge / a869498f OpenPI 基线和实际既有 checkpoint，用可用GPU接续两条缺失的 eval0：各自 matching video/no-video smoke2 → fresh formal100，原固定100000..100099，独立run/ports，登记真实job。此为已授权三eval baseline 队列的补齐，无新增训练或新模式，不需等待 HF 源码 review。先核对既有 run leaf，避免重复评测已完整结果；若原失败叶存在，保留并使用新名字。

HF 源码仍未准入，不部署 HF。其余既有排期维持；只运行当前 frozen runtime 实际兼容且已授权的项目，不为占满GPU改变模型/协议。发布实际进度后正常结束，不轮询。

## Manager HF 正式对照补充：统一 episode RNG 协议

作者默认reset P1修复及独立review尚未完成，不准入新runtime。Manager已核实历史policy server跨100集持久运行并连续消费action RNG，而HF合同逐episode回到initial key0；因此不再直接复用历史J/S成绩作为HF对照。保留当前已运行P-N/P-S eval0自然收尾，它们属于原协议，不能更换代码或混合新协议。

新增显式matched baseline配置，由HF作者提供窄接线并独立review：同checkpoint/H50/K30、同每episode action key0 reset、同random_light=false/crazy_random_light_rate=0，baseline自身不执行中途probe或改变MemoryContext。matched shadow采用相同RNG协议、增加probe但不改cache/动作，只用于工程等价。普通默认baseline和普通shadow的历史行为也须验证保留；不要用两条新路径的互比代替默认兼容性。

正式排期改为：第一阶段J matched baseline两任务×3eval=6批，与J HF-fixed/event12批共同构成18批；第二阶段S matched baseline6批与S HF-fixed6批构成12批；第三阶段J HF-periodic6批。合计36新批/3600正式episode executions/0训练，优先J，工程smoke不计入正式数。每配置每eval seed仍matching smoke2→fresh formal100。所有臂policy初始key固定0且逐episode恢复，probe独立流；eval0/1/2仅对应环境100000/200000/300000列表，不是三次policy seed。旧baseline继续留在原九任务台账，不跨协议拼接，不用旧高分挑新baseline，不改冻结阈值。待精确code PASS与Manager准入后再开新GPU工作；现在可以更新准备清单和实际配置/manifest记录需求，无需轮询。

Source report:

## 当前状态：put-back J/T train1 与 train2/eval1 已完成；train2/eval2 formal100 运行中（2026-09-14 CST）

固定原协议运行树始终 clean：RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。所有批次保持 H50/K30、原始 RNG 生命周期、首次 infer 90 秒、后续 30 秒；新增训练、转换、传输、源码、依赖、checkpoint 与共享 cache 变更均为 0。

| arm / train / eval | formal100 | 结果 | final review SHA-256 / MAM |
| --- | --- | ---: | --- |
| J `full_t_plus_1` / train1 / eval1 `200000..200099` | `c_put_back_full_t_plus_1_trainseed1_evalseed1_100ep_r3` | **47/100** | `f02b472b80d9009bca1d26df66a77c343ea4e48d8c39a1b68c70e607f6d13cc3`; job `bf7a953a-e35a-4ca3-a8cc-ccd9cf4f3cd0` archived |
| T `full_t_plus_30` / train1 / eval1 `200000..200099` | `c_put_back_full_t_plus_30_trainseed1_evalseed1_100ep_r3` | **46/100** | `94f4e4297d3b63b69b09a4296a1ef0684b3bb138c57d9b250767e305e6ca752b`; job `d805fb5c-f1ff-41ae-8b6d-59a3aa481e07` archived |
| J `full_t_plus_1` / train1 / eval2 `300000..300099` | `c_put_back_full_t_plus_1_trainseed1_evalseed2_100ep_r3` | **58/100** | `be14b50e2d1b4834a37349921a7b83fe2eb3721f7262a5d0273cbbdcf2ccca78`; job `0f7daad0-ba87-41dc-8efd-57431d03a289` archived |
| T `full_t_plus_30` / train1 / eval2 `300000..300099` | `c_put_back_full_t_plus_30_trainseed1_evalseed2_100ep_r3` | **62/100** | `a5bbb1ae0c73326326ead750b46c63ddf805d8e5c8fdaffc9ff2c93ef45ffd75`; job `8883cf5e-9fd9-4255-b120-eac472a20c40` archived |
| J `full_t_plus_1` / train2 / eval1 `200000..200099` | `c_put_back_full_t_plus_1_trainseed2_evalseed1_100ep_r3` | **70/100** | `32864e05054f65de653565d19908271e30ef8880b0f1eacb220100c5b41444bd`; job `0ccf5f61-bd19-4df7-88dc-9ec2f49d79c4` archived |
| T `full_t_plus_30` / train2 / eval1 `200000..200099` | `c_put_back_full_t_plus_30_trainseed2_evalseed1_100ep_r3` | **68/100** | `eaac667a3ecd3236aca2c8cadf5eec3a1eee35edd9ab60b513a2669c75d1b94a`; job `1ae7a228-0a13-4074-88ba-8b12886e1676` archived |

train2/eval1 两叶均以 100 条连续 seed/preflight/terminal diagnostics、100 个 episode JSON、100 个 scheduler exit 0、102/102 自有进程退出、视频、端口与 outer PID 释放、来源/manifest 和 10 个核心 artifact hash 完成终验；infrastructure marker 为零。J 的 normal failures 是 `block_not_moved_to_center=1`、`button_not_pressed_after_center=20`、`button_press_insufficient=8`、`pressed_before_block_centered=1`；T 为 `button_not_pressed_after_center=17`、`button_press_insufficient=15`。matching smoke cleanup receipt SHA-256 分别为 `0f1fcc6c9a51e74ffb4ea0bfdfc261a8686312c1f843e590ac896147b065fde5`、`49f1395c498f8e234be895fa68373e667b39d5c75936580ed8aa68ace523e12e`；仅这两个 smoke leaf 已删除，formal leaf、reviews、receipts、logs 和 J 的历史 r2 partial 均保留。task-local train2/eval1 finalizer SHA-256 为 `a532cd5d6b76c637165b05c9d0a431f820ad11ea6f59d4f9aa763aae201aa423`。

train2/eval2 的宽去重扫描 106 个 config leaf，没有发现有效完整结果：`records/putback_JT_trainseed2_evalseed2_20260914.dedup.json` SHA-256 `803df59c14edf4d87621e85d5ed6aac3e989f6ebacc4d9b89f8ba29324b48453`。独立 audit/manifest 与 smoke/formal dry-run 已通过（preparation receipt SHA-256 `59641d2d2c4934a5f7b001d146b2633cd7abdced3ba021057e73e54741c2c957`）；smoke verifier SHA-256 `757c5b1f704b1a718cfe982b76ab8f97af7e6c0b900caab6035dcf9d1398c455`。

| arm | matching video/no-video smoke2 | running fresh formal100 | C1 resource / actual outer PID / MAM job |
| --- | --- | --- | --- |
| J `full_t_plus_1` | 2/2; `300000..300001`; review `7c34c4fbe5116dcdd469f54949ed8bf569d5e610b28955b147d5294bacf4c7cc` | `c_put_back_full_t_plus_1_trainseed2_evalseed2_100ep_r3`, fixed `300000..300099` | GPU1, `19410,19412`, PID `1588842`, job `bebb94c2-ed93-49ce-9415-39c4048d8f9e` |
| T `full_t_plus_30` | 2/2; `300000..300001`; review `dbf7c55242d0a4a1861ac30ab123205b3df2a7479cefe2d69ff97dc427083dc6` | `c_put_back_full_t_plus_30_trainseed2_evalseed2_100ep_r3`, fixed `300000..300099` | GPU2, `19420,19422`, PID `1588843`, job `2319f9fc-4809-4846-8421-a78614a461b6` |

两条 formal 已以实际 PID 登记为 running，尚无正式分数。预启动记录为 `records/putback_JT_trainseed2_evalseed2_formal_prelaunch_20260914T023300Z.log`（SHA-256 `d23a155d1d74c35bd550c945e67dab25d910b27db9d50f97e705428a11964bf0`）。本 turn 不主动轮询；MAM 停止事件到达后，将以实际 job ID 派生终验器，按 check-only → final review → 独立复核 → MAM archive → cleanup receipt → 精确 smoke 删除的顺序收尾。

---

## 当前状态：put-back J/T train1 · eval1 正式100已启动（2026-09-14 CST）

已按发布 revision `468bc0d32e4dd5056b06264915a685912992811e` 去重并启动首对缺失评测；新增训练、转换和数据传输均为 0。广泛扫描结果显示，J train1/eval1 仅有历史 `r2` partial（23 集、`failure_review.json`，没有 `final_review.json`），J/T 的 train1/2、eval1/2 不存在可复用的完整正式100，因此没有重跑任何有效结果。

运行树冻结且 clean：RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。两条命令均从同一 C1 runtime 运行，checkpoint metadata 已核对为 `demo_clean_state`、H50/K30、full `last_executed` feedback；首个 infer 保持 90 秒，后续 infer 保持 30 秒。

| arm | matching smoke2 | smoke 结果 | formal100 / 资源 | MAM job |
| --- | --- | ---: | --- | --- |
| J `full_t_plus_1`, train1/eval1 | `c_put_back_full_t_plus_1_trainseed1_evalseed1_smoke2_r3` | 2/2；`200000..200001`，video/no-video、terminal、process/port、source/hash 全部通过 | `c_put_back_full_t_plus_1_trainseed1_evalseed1_100ep_r3`；C1 GPU1，19410/19412，outer PID `723437` | `bf7a953a-e35a-4ca3-a8cc-ccd9cf4f3cd0` |
| T `full_t_plus_30`, train1/eval1 | `c_put_back_full_t_plus_30_trainseed1_evalseed1_smoke2_r3` | 1/2；`200000..200001`，video/no-video、terminal、process/port、source/hash 全部通过 | `c_put_back_full_t_plus_30_trainseed1_evalseed1_100ep_r3`；C1 GPU2，19420/19422，outer PID `723438` | `d805fb5c-f1ff-41ae-8b6d-59a3aa481e07` |

两条 formal 已由 MAM 以实际 C1 outer PID 登记为 running；启动后尚未完成 episode，未报告分数。任务私有 records 保存 prelaunch、audit、dry-run、outer PID/log 与两份 smoke review。formal 停止后将先执行完整100/连续 seeds/嵌套 terminal/video/process/source/hash 验收，写 `final_review.json`、归档 job、写 matching-smoke cleanup receipt，再删除且只删除对应 smoke；遇到基础设施首因则保留 leaf 并停止该项。其后按既定队列继续 train1/eval2，再 train2/eval1、train2/eval2。

---

## 当前状态：C3 高频工程验证被 matched action gate 阻断（2026-09-14 CST）

C3 GPU0 上的获批有限工程验证已完成 8 个两集 leaf，**没有启动 HF matching smoke、r_s30 控制或任何 HF formal100**。运行根为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库仍干净且精确固定为 RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`。冻结矩阵、baseline inputs 与 run matrix SHA 分别为 `20e414eb…700adb`、`305250a1…5610`、`f5e5dc56…8a69`；任务私有工具 SHA 为 `dcf93891de82adaf21e676c55ee30901309f9c9a6097841ff4be4c7ba7f29c87`。

四个普通 baseline/shadow 与四个 matched baseline/shadow 均使用环境 seed `100000,100001`，每个 leaf 都完整终态、launcher/scheduler exit 0、episode0 video/episode1 no-video、端口释放，并实际记录 `random_light=false`、`crazy_random_light_rate=0`。普通 baseline 按合同没有 rolling action/probe RNG 日志；该可观测缺口保留，未被当成动作等价证据。

| profile | 审计 review SHA-256 |
| --- | --- |
| ordinary rearrange baseline / shadow | `0b3b0ec3053d76db967377fc8fca41bcbb5bc5e51b9d3004b1e0d41aef98083f` / `e06818739af8a68864e7e0ed970eb3b6b151b0da3b8154b657742557edcaa1a4` |
| ordinary put-back baseline / shadow | `49395fed252948f7ebe09ee79cbfc9ea2ead835c8430a4f3c481e57deab826aa` / `4595c78ee8cdf26cc4445728e4c9d98b4115fe1c6dcdfd6fced2e79118687926` |
| matched rearrange baseline / shadow | `3dfaa6716e8e7b589be1f34506bdb1a31962afa1dac446723e2b9c26f816bf45` / `61bb190ee46934954cf8a7b10dcdea3df0d743f310bb1049e9e53f4fed48f256` |
| matched put-back baseline / shadow | `a33b40b14ece0525b673265b1c6fb2858986468f41c4bf27501b9029e4ffb162` / `f595423190643ceaeefef7a0e2efbcbf8e513ac0cc984efea9a0fc3b51e2b93d` |

两个 matched pair 审计均以 `matched baseline/shadow action evidence differs` 退出，因而不满足 shadow 不改变动作流的准入条件。四个 accepted episode 都有每集 action RNG reset；matched baseline probe 数为 0，shadow 有 54–67 个 probe。两任务、两集中第一个 action query 都在 `source_step=0`、相同记录的 action RNG `{stream: action, call: 1}` 和相同记录的语义 state/memory 输入下出现不同 action 数组；put-back 随后从 baseline 17 次 action query 与 shadow 11 次 action plan 进一步分叉。记录的语义输入有意不含 camera payload，因此现有证据不能把首个差异归因于未记录视觉观测差异或 policy/runtime 行为中的任一方；没有猜测首因、调阈值、重跑或修改源码。

完整失败记录在 `.local/highfreq_engineering/audits/failures/matched_action_equivalence_failure.json`，SHA-256 `c6519c947782001a07295daf7aeed4a6a1d2295669c17ececd8acb537e2c26f4`；其中有每集首分歧 action 摘要、pair audit log/review hash 和未启动清单。扫描 93 个 outer/process/result 文件未发现 traceback、EOF、renderer、CUDA 或 runtime-error marker。收尾时 C3 GPU0 为 1 MiB used / 24080 MiB free / 0% util，19400/19402 无监听；未触碰 C1 正式任务、源码树或 checkpoint。下一步需要由源码 owner/Manager 针对 matched action 等价与完整输入可观测性裁定或修复后，再建立新的独立 runtime/leaf；当前不能把任何 engineering leaf 视为 matching gate。

## 本轮收尾：原协议 T 终验与 HF 离线口径更正（2026-09-14 CST）

两条已停止的原协议 put-back T formal 已按完整 100 集合同验收并归档，运行树仍精确固定为 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，三树 clean。`episode_diagnostics.jsonl` 的真实终态字段为 `diagnostics.episode_status.terminal`，两叶均为 100/100；各自还核对了 100 条 accepted preflight、连续固定 seed、100 份可解析 episode JSON、100 条 video check、100 个 scheduler exit 0、102 start/102 exit 记录、全部自有子进程退出、端口与 outer PID 释放。每叶只出现一次已知非致命 SAPIEN Vulkan ICD warning，基础设施 marker 为零。

| formal | 结果与固定 seed | final review SHA-256 | smoke 清理 |
| --- | --- | --- | --- |
| `c_put_back_full_t_plus_30_trainseed0_evalseed1_100ep_r3` | **66/100**，`200000..200099`；`button_not_pressed_after_center=17`，`button_press_insufficient=17` | `8fa19754e9339331cb1fdac287b2c4795ca5d0fdbec3dcaa9633571682ab15ec` | receipt 已保存，51 文件 / 2,350,262 bytes 的 matching smoke 已删除 |
| `c_put_back_full_t_plus_30_trainseed0_evalseed2_100ep_r3` | **74/100**，`300000..300099`；`block_not_moved_to_center=1`，`button_not_pressed_after_center=16`，`button_press_insufficient=9` | `1d841274165849390a7c0e7cf08882a01532a89d893f3a8885217de555d65d78` | receipt 已保存，51 文件 / 2,226,369 bytes 的 matching smoke 已删除 |

前五个实际解码视频帧数分别为 eval1 `330/500/357/363/500`、eval2 `330/361/360/359/361`。最终 review、保留的 smoke review 和 cleanup receipt 位于对应 formal leaf；任务私有复核器为 `c-eval-putback-baselines-yaml/records/finalize_t_evals_20260914.py`（SHA-256 `c85e6eb4c8fda5f2af11550854e1427fbc8fca7b4ce99ecc6064cf5584b1b71a`）。MAM jobs `da058195-ff39-49ed-8e83-be5e1a8aaa7e` 与 `3191f8c6-4c53-48a3-9ab7-8b44216ab2c0` 已 archived。

HF 的原 pair failure 和原工具未被覆盖，SHA-256 仍为 `c6519c947782001a07295daf7aeed4a6a1d2295669c17ececd8acb537e2c26f4` 与 `dcf93891de82adaf21e676c55ee30901309f9c9a6097841ff4be4c7ba7f29c87`。新增纯离线工具 `.local/highfreq_engineering/hf_queued_event_audit_v2.py`（SHA-256 `1be44b9bd3cd02235833707e40022d0690361efae60b131dcbeb287daeb02151`）和派生 receipt `audits/recomputed/matched_action_equivalence_queued_event_v2.json`（SHA-256 `bc30cf2ee8bfe7130cc68c1f8eff2862928e5baee1564b6841ffb29d0187d1fb）。它以 `query_id/actions_from_query` 关联 baseline 的 `H=50` prediction 和真实 `queued_rows=K=30` 下发前缀，再用 shadow `action_plan` 的相同 query、`execute_response.queued`、`source_step` 及两侧已完成行边界重建实际对象；query event 数与 action row 数分开记录，缺失关联会显式失败，没有固定截 30。

四集的关联错误为 0；rearrange 有 28 个配对 query event，put-back 有 22 个，后者另有 12 个 baseline query 在 shadow 提前终态后未配对。**50/50 已配对的 K-row 队列和共同已执行前缀都不精确相等**：两个任务每集首个 `source_step=0` query 的最大绝对差仍为 rearrange `0.0038730204/0.0038729906`、put-back `0.0034926604/0.0034926604`；后续已分叉轨迹的最大差达到 `0.2075123787` 和 `1.3522526920`，不能据此归因于单一首因。记录仅有 RNG `stream/call`，没有实际 key；输入快照也没有完整视觉或 prompt payload。因此形状口径修正不构成 PASS：没有启动 GPU、服务、HF matching smoke、r_s30 或 formal100，阈值未变，仍等待源码 owner/Manager 的有界诊断与裁定。

---

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

### C3 smoke 验收与 formal 接续（2026-09-13 01:23 CST）

已验收并归档 stopped MAM smoke `d7437ff4-4dbc-48c6-8c44-6ebb77a494a7`。`
`c_rearrange_full_t_plus_30_trainseed0_evalseed1_smoke2_r3` 的
`diagnostics_summary.json` 为 `completed`、target 2、无 benchmark error；
`seed_preflight.jsonl` 记录 200000 与 200001 都 `accepted=true`，
`episode_diagnostics.jsonl` 中二者都是 terminal success、无 runtime error。episode0 视频为 393 帧且
`video_checks.jsonl` 为 ok；episode1 的 no-video 证据也为 ok。两个 scheduler child returncode 均为 0，
worker/outer/process logs 对 EOF、renderer/native、segfault、traceback 和 runtime-error marker 的扫描均为 0。
`checkpoint_metadata/lineage/config_source/` 已逐文件继承 input audit/manifest。该 smoke 的 2/2 成功仅为
基础设施门禁证据，不是正式分数或选择依据。

同一 clean 的 C3 runtime、checkpoint、train/eval seed 和端口已直接启动 fresh formal100：

```text
MAM job: 5be8d262-f6f6-45a4-ae0d-5b02e3dfc043
run: c_rearrange_full_t_plus_30_trainseed0_evalseed1_100ep_r3
host/GPU/ports: C3 GPU0 / 19400,19402
fixed environment seeds: 200000..200099
smoke reference: c_rearrange_full_t_plus_30_trainseed0_evalseed1_smoke2_r3
runtime: RMBench 2e9677ce8ec9f623395184f63f32ddafa66e5e44; bridge f9626636c4776d8eb15f9c556775cb2d12c000e5; OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4
```

启动时 formal leaf 不存在，三库 tracked 状态 clean；runner 已写入 command/config/lineage，服务正在启动，尚无正式 terminal 或结果。C2 GPU6 的独立 40-reset gate `546b6d60-f038-4924-b60d-ece5d9489309` 仍 running 且 receipt 尚未出现，未据此推断进度或 PASS。

### C2 40-reset PASS 与 r3 接续（2026-09-13 01:29 CST）

已核验并归档 stopped MAM gate `546b6d60-f038-4924-b60d-ece5d9489309`。C2 receipt
`.../c-eval-renderer-r3-2e9677c/records/renderer_reset_gate_c2_gpu6_r3_2e9677c.json` 为实际 GPU PASS：
`passed=true`、`completed_count=requested_count=40`，seed `100000..100039` 的每条均
`accepted=true`、`state=ready`、`terminal=false`，`error=null`；worker/outer logs 中 EOF、renderer/native、driver、segfault 与 traceback marker 均为 0。结束时 C2 GPU6/GPU7 各4 MiB used、24,207 MiB free、0% util，19460/19462/19470/19472 无监听。runtime 三库仍为 clean 的
RMBench `2e9677c`、bridge `f962663`、OpenPI `a869498`。

按 C2 的旧 `r2` incomplete 项和固定 eval-seed 队列，已在 C2 GPU7 接续
`rearrange_full_t_plus_30 / trainseed0 / evalseed2` 的 fresh matching smoke：

```text
run: c_rearrange_full_t_plus_30_trainseed0_evalseed2_smoke2_r3
checkpoint: .../pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0/20000
smoke seeds: 300000, 300001
ports: 19470,19472
MAM: 96f548b9-4fc1-44a2-9e18-533a2cb8e090
```

其 C2-local audit/manifest、metadata route 和 dry-run 均已通过，正式 leaf 不存在；启动后 robot 服务已监听，尚未形成 terminal rollout 或 smoke verdict。只在该 smoke 的 video/no-video、terminal、退出和零基础设施 marker 全部通过后才直接启动 matching fresh formal100。C3 GPU0 的同 checkpoint evalseed1 formal `5be8d262-f6f6-45a4-ae0d-5b02e3dfc043` 保持运行，未修改。

### C2 GPU7 smoke 验收与交接快照（2026-09-13）

已完成此次交接前唯一待收尾的 stopped smoke。MAM job
`96f548b9-4fc1-44a2-9e18-533a2cb8e090` 已归档；
`c_rearrange_full_t_plus_30_trainseed0_evalseed2_smoke2_r3` 的固定
seed `300000/300001` 都为 accepted terminal success，episode 0 的视频可读
（383 frames），episode 1 保留 no-video 证据，两个 scheduler 均 exit 0，且
EOF、renderer/native、traceback 和 runtime-error marker 均为 0。formal leaf 在
smoke 验收前不存在，端口和 GPU 已释放；该 smoke 因此只作为对应 formal 的基础设施门禁，
不计入正式结果。

同一 frozen C2 runtime 已按已通过的 smoke 接续 formal，MAM job
`d7f772a9-1b0e-4d80-9350-a7c794ac03f1`：C2 GPU7，
`c_rearrange_full_t_plus_30_trainseed0_evalseed2_100ep_r3`，fixed seeds
`300000..300099`，ports `19470/19472`，版本为 RMBench `2e9677c` /
bridge `f962663` / OpenPI `a869498`。本次发布时 MAM 实时状态为 `running`；
尚未重新读取 formal rollout 产物，故不声明 terminal 数或结果。

交接时共有九个未归档、MAM 状态为 `running` 的 formal：C1 GPU1–7 的七项
serial-lag30，以及 C3 GPU0 的 full-t+30 trainseed0/eval seed1
(`5be8d262-f6f6-45a4-ae0d-5b02e3dfc043`) 和上述 C2 GPU7 formal。未启动、停止、
修改或归档任何仍需后继 owner 核验的 job；新 owner 应从这些登记 job 和既有 raw
artifact 继续处理。

## 2026-09-13 用户预算重排：新增调度已冻结

已读取发布 task revision `09addf80035e128be29f29c6861a40f5669e8142` 的最后一节。它覆盖此前
三训练 seed / 三 eval seed 的自动扩展授权：不再启动任何新的训练、smoke、formal 或追加 eval seed；已训练但
未评的 checkpoint 只保留为可复用清单，等待新的论文最小实验排期。九条此前已登记的 formal 不停止、不重启，
只自然收尾、核验、记录和归档。

本轮收尾了两条已停止的 put-back full t+1 / trainseed0 r3 matching smoke，均只作为基础设施
证据，均不产生正式分数，且不会接续配对 formal：

- C2 GPU6 / eval1：MAM `db874c5e-13dc-48a0-b98d-c1ca3bc400bf` 已归档。run
  `c_put_back_full_t_plus_1_trainseed0_evalseed1_smoke2_r3` 为 `completed`，固定 seed
  `200000/200001` 均 accepted terminal，episode0 视频 363 帧可读、episode1 no-video，两个
  scheduler 均 exit 0；worker/outer/process logs 对 EOF、renderer/native、traceback 和
  runtime-error marker 均为零。
- C3 GPU1 / eval2：MAM `1151b5e9-2ac0-43f7-8d20-c72bc8320d4c` 已归档。run
  `c_put_back_full_t_plus_1_trainseed0_evalseed2_smoke2_r3` 为 `completed`，固定 seed
  `300000/300001` 均 accepted terminal，episode0 视频 332 帧可读、episode1 no-video，两个
  scheduler 均 exit 0；同一组基础设施 marker 为零。

两项结果位于
`/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/` 的对应 r3 leaf；
均冻结在 RMBench `2e9677ce8ec9f623395184f63f32ddafa66e5e44`、bridge
`f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。其现有 checkpoint、audit/manifest 继承副本、
video/no-video 和进程记录均保留，供新排期复用。

安全文档树
`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-c-eval-docs-consolidated`
已在 `task/e6908de7-c-eval-docs-consolidated` 提交 `a3566f7`（父 `f251d71`）。该提交同步当前
r3 队列、两条 smoke 的验收/暂停 formal 状态，并说明旧“无运行中 formal”行只是历史快照；`git diff --check`
通过，树已干净。该文档分支未合入或改写任何活跃 runtime。

## 2026-09-13：九条 stopped formal100 终验与归档

针对发布 task revision `ab324eea674a8d124c23e1d243b3385289c150d6`，已从每个 formal leaf 的
`diagnostics_summary.json`、`seed_preflight.jsonl`、`episode_diagnostics.jsonl`、
`processes.jsonl`、`video_checks.jsonl` 与 worker/process logs 逐项复核。九条均为完整可报告的
100-episode 结果：summary 为 `completed`、target 100、error null；100 个 accepted 且连续的
固定 seed、100 个 terminal diagnostics、100 个 scheduler exit 0、100 个 video check `ok=true`；
所有 owned child 已退出，未发现 EOF、ConnectionResetError、traceback、segfault 或 runtime error。
每个 leaf 新增 `final_review.json`，其中保存上述五份核心 artifact 的 SHA-256、matching-smoke
provenance、冻结 runtime 和正常任务失败计数。worker 中每份各有一条已知的 SAPIEN
`Failed to find Vulkan ICD file` warning；健康完成 run 中同样出现，故不作为基础设施失败。

| run | train / eval seed | score | MAM job |
| --- | --- | ---: | --- |
| `c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3` | 1 / 1 (`200000..200099`) | 38 / 100 | `d626a209-7b69-4042-9427-3c73be8efe0d` |
| `c_rearrange_serial_lag30_trainseed1_evalseed2_100ep_r3` | 1 / 2 (`300000..300099`) | 37 / 100 | `71767977-6cda-461f-9a7a-6e8537c53e4d` |
| `c_rearrange_serial_lag30_trainseed2_evalseed0_100ep_r3` | 2 / 0 (`100000..100099`) | 12 / 100 | `b0b0bad2-ed95-4966-bf61-621fb86e701c` |
| `c_rearrange_serial_lag30_trainseed2_evalseed1_100ep_r3` | 2 / 1 (`200000..200099`) | 14 / 100 | `146e19f0-ed6b-4f4a-8bef-356bca4f665d` |
| `c_rearrange_serial_lag30_trainseed2_evalseed2_100ep_r3` | 2 / 2 (`300000..300099`) | 15 / 100 | `b9624ab0-9fdd-469e-a5a2-a2d22868dc22` |
| `c_rearrange_serial_lag30_trainseed0_evalseed1_100ep_r3` | 0 / 1 (`200000..200099`) | 27 / 100 | `977e29ab-e527-4e65-bc84-9b5bb2c03f02` |
| `c_rearrange_serial_lag30_trainseed0_evalseed2_100ep_r3` | 0 / 2 (`300000..300099`) | 23 / 100 | `a1453162-c880-45d0-b639-e3edf0db3494` |
| `c_rearrange_full_t_plus_30_trainseed0_evalseed1_100ep_r3` | 0 / 1 (`200000..200099`) | 90 / 100 | `5be8d262-f6f6-45a4-ae0d-5b02e3dfc043` |
| `c_rearrange_full_t_plus_30_trainseed0_evalseed2_100ep_r3` | 0 / 2 (`300000..300099`) | 94 / 100 | `d7f772a9-1b0e-4d80-9350-a7c794ac03f1` |

证据根目录：
`/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/<run>/final_review.json`。
C1 的七条使用 clean、冻结的 RMBench `bf34743334efc98440fa9b05e3f2f05e8303846a`；C2/C3 的两条使用
RMBench `2e9677ce8ec9f623395184f63f32ddafa66e5e44`；全部 bridge 为
`f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI 为
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。九个 stopped MAM job 已分别以 score、seed 范围和
`final_review.json` 路径归档；本 task 当前没有未归档 job。

## 2026-09-13 10:35 CST：N/S/J seed0 覆盖推进与 put-back baseline YAML 候选

本次接续以已发布 task revision d2841deafcc1cca51dd30bac14a4ddaa7425946b 为准，未重训、未拼接 partial，也没有修改任何活跃 C runtime tree。

### 当前 GPU 状态

- C1 GPU1 的 rearrange no-memory / trainseed0 / evalseed1 已完成其自身 smoke2，两条固定 seed 200000/200001 都是 accepted terminal；episode0 视频可读（700 帧）、episode1 有 no-video ok=true，scheduler 两次 exit 0、policy/robot 均正常受控停止，且 worker/outer/process 日志没有 EOF、ConnectionReset、traceback、segfault、runtime-error 或 scheduler_exited_before_terminal。smoke 的 0/2 是正常任务失败，未被当作基础设施失败或成绩筛选。
- 该 matching gate 复核后，已在 C1 GPU1 从冻结 RMBench bf34743334efc98440fa9b05e3f2f05e8303846a / bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 / OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 启动 fresh formal100：c_rearrange_no_memory_trainseed0_evalseed1_100ep_r3，固定 seed 200000..200099，端口 19410/19412，MAM job fad91d99-98b0-4545-ad14-ff90abfc16f1。本次发布时进程仍运行，已有正常 terminal rollout；不报告中途分数。
- C1 GPU2 已在同一冻结 r3 tree 启动 no-memory / trainseed0 / evalseed2 的 matching smoke2：c_rearrange_no_memory_trainseed0_evalseed2_smoke2_r3，PID 3183493，固定 seed 300000/300001、端口 19420/19422。短 smoke 未登记 MAM；尚未给出 gate verdict 或启动对应 formal。
- 已运行的 put-back full t+1 seed0 formal 保持不变：C2 GPU6 eval1 的 cb9080c2-b615-40de-8a15-69a7eed3d3f9 和 C3 GPU1 eval2 的 873c5bb0-c8fc-462c-8f40-8bbbe21747b6 都仍为 running。本次读取时两者各有 20 条 terminal/视频记录，尚未做 completion 判定。

### put-back no-memory / serial_lag30 入口候选（待 focused review）

独立 C worktree：
/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-putback-baselines-yaml/。

RMBench candidate：
f401f5279c95451eb424ac98b831bab5552b2120，branch
task/e6908de7-putback-baselines-yaml-rmbench；bridge/OpenPI 分别冻结在
f9626636 / a869498f。改动仅为
experiments/memory_chunk_20260910/configs/memory_schema_eval.yaml 的 17 行：
- put_back_no_memory：实际 pi05_rmbench_put_back_block_no_memory / put_back_block_no_memory、joint_dense、空 fields；
- put_back_serial_lag30：实际 pi05_rmbench_put_back_block_serial_lag30 / put_back_block_serial_lag30、serial_token、phase, origin_mat、query_selected/query feedback。

在 C1 用独立只读 Python receipt 实读两份 checkpoint metadata，并经
load_train_config → _runtime_metadata → MemoryContext 确认上述 config ID、field list、H50/K30、data repo 和 serial 两字段的 feedback。两个 checkpoint 均为完成的 20000，有 _CHECKPOINT_METADATA。

两项均在 CUDA 空、JAX_PLATFORMS=cpu 条件下通过 --prepare-audit、smoke dry-run 和 formal dry-run；formal 命令含 matching smoke directory。checkpoint 的逐文件 path/size/mtime inventory 前后一致，git diff --check 通过，候选三树干净且没有生成 eval leaf。已立即提交 focused-review 请求；review 通过前不部署该树、不启动其 GPU smoke/formal，也不改动 c-eval-renderer-r3 或 c-eval-renderer-r3-2e9677c。


## 2026-09-13：四条 r3 formal100 终验、归档与 YAML 准入状态

依据当前发布 task revision `c81ef808b7324b373ad7402a3c4110ce1f5a716d`，本节仅收尾此前已自然停止的四条 formal；未重启、拼接或筛选任何 rollout。每条均从原始 `diagnostics_summary.json`、`seed_preflight.jsonl`、`episode_diagnostics.jsonl`、`processes.jsonl`、`video_checks.jsonl` 和 worker/outer 日志复核：summary 为 `completed`（target 100、error null），100 个 accepted 的连续固定 seed，100 个 terminal diagnostics，100 个 scheduler `episode_terminal` / exit 0，100 个 video check `ok=true`，前五个视频实际解码。robot/policy 均以 `runner_shutdown` 退出；EOF、ConnectionReset、traceback、segfault、runtime-error、worker-RPC 和 scheduler-before-terminal marker 均为零。

每个 matching smoke 也重新核验：两条连续 seed 都 accepted terminal，episode0 视频可读、episode1 明确 no-video，两个 scheduler exit 0，且日志零基础设施 marker。各 formal 的 `command.txt` 引用该 smoke，且保留 `checkpoint_metadata/lineage/config_source/input_audit.json` 与 `input_manifest.json`。每份 worker log 有一条已知、非致命的 SAPIEN `Failed to find Vulkan ICD file` warning；健康完成 run 同样出现，未将其视为基础设施失败。

| run | train / eval seed | fixed environment seeds | score | MAM job | final review SHA-256 |
| --- | --- | --- | ---: | --- | --- |
| `c_put_back_full_t_plus_1_trainseed0_evalseed1_100ep_r3` | 0 / 1 | `200000..200099` | 68 / 100 | `cb9080c2-b615-40de-8a15-69a7eed3d3f9` archived | `941ce208451ae2ce4679186f7ba0ff010fb6d867b7af4524f84349236df220b0` |
| `c_put_back_full_t_plus_1_trainseed0_evalseed2_100ep_r3` | 0 / 2 | `300000..300099` | 76 / 100 | `873c5bb0-c8fc-462c-8f40-8bbbe21747b6` archived | `a8578f54235112d82a4a9536cb60c202d3059031e75942683c27d57c2f1a5628` |
| `c_rearrange_no_memory_trainseed0_evalseed1_100ep_r3` | 0 / 1 | `200000..200099` | 27 / 100 | `fad91d99-98b0-4545-ad14-ff90abfc16f1` archived | `824290051d964392cc1b1a8631163c4019810f84a3b1eba03c1ede0330e964cf` |
| `c_rearrange_no_memory_trainseed0_evalseed2_100ep_r3` | 0 / 2 | `300000..300099` | 20 / 100 | `305e6344-cb44-4634-9c45-66de5afe3691` archived | `3d1c253163016edb9fe00cbc74e668d71b8c4611baf83fe834608197d458318d` |

结果根为 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/<run>/final_review.json`。put-back 两条使用冻结 RMBench `2e9677ce8ec9f623395184f63f32ddafa66e5e44`；rearrange no-memory 两条使用冻结 RMBench `bf34743334efc98440fa9b05e3f2f05e8303846a`；全部 bridge 为 `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI 为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。归档前端口 `19410/19412`、`19420/19422`、`19460/19462` 均未监听。

put-back no-memory/serial 的独立 YAML 候选 `f401f5279c95451eb424ac98b831bab5552b2120` 已获 Manager 准入：只补 `put_back_no_memory` 的空 fields/joint_dense 和 `put_back_serial_lag30` 的 phase/origin_mat serial-token `query_selected/query` 路由。它保留在独立 `c-eval-putback-baselines-yaml` tree，bridge/OpenPI 仍冻结为 `f962663`/`a869498`；后续每个 eval seed 仍须先执行自己的 prepare-audit 和 matching smoke，再启动 formal。

## 2026-09-13 16:36 CST：N/S/J seed0 实际 C1 队列

本节记录已实际启动的评测，不把 smoke 成绩当正式结果，也没有新增训练、重启或拼接既有 rollout。

| 项目 | eval seed | C1 GPU / ports | 当前阶段 | MAM job / PID | 固定环境 seed |
| --- | ---: | --- | --- | --- | --- |
| rearrange full t+1, train0（J） | 1 | GPU3 / 19430,19432 | formal100 running | `884096c3-f7ad-48f2-b1a7-843bc0c2cb66` | `200000..200099` |
| rearrange full t+1, train0（J） | 2 | GPU4 / 19440,19442 | formal100 running | `071c8a2e-c00f-46d7-b180-c31c8e91c718` | `300000..300099` |
| put-back no-memory, train0（P-N） | 1 | GPU1 / 19410,19412 | formal100 running | `30fda7f6-0d1b-440d-857b-85e203dc9963` | `200000..200099` |
| put-back no-memory, train0（P-N） | 2 | GPU2 / 19420,19422 | formal100 running | `479c266c-7530-404b-9071-2f68344e2190` | `300000..300099` |
| put-back serial-lag30, train0（P-S） | 1 | GPU5 / 19450,19452 | formal100 running | `81818520-2cfb-4f20-a98a-712c06db482a` | `200000..200099` |
| put-back serial-lag30, train0（P-S） | 2 | GPU6 / 19460,19462 | formal100 running | `cdd254f1-b01f-4cf8-9017-cd7259403ee2` | `300000..300099` |

J 的两条 matching smoke 都经 `/tmp/e6908_validate_smoke.py` 验证通过：两条 accepted terminal、episode0 视频可解码（371/376 frames）、episode1 no-video、scheduler exit 0，且无基础设施 marker。P-N 的两条 smoke 也均通过同一门禁；eval1 视频为 487 frames，eval2 视频为 326 frames。P-N eval2 的 smoke 有一条正常任务失败，仍保留原始证据并照固定队列接续，未按 smoke 成绩选择或重跑。

P-N/P-S 使用独立、已准入的 YAML runtime：RMBench `f401f5279c95451eb424ac98b831bab5552b2120`（包含 `2e9677c` 与已批准 renderer reuse 修复）、bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。其四份 prepare-audit receipt 均已完成且 checkpoint before/after inventories 一致；P-N 是空 fields/joint-dense，P-S 是 `phase, origin_mat` 的 serial-token query feedback。J 的 frozen runtime 为 RMBench `bf34743334efc98440fa9b05e3f2f05e8303846a`、同一 bridge/OpenPI。所有启动前都核对 formal leaf 不存在、端口空闲及三库 tracked 状态干净；C1 首次启动按约两分钟间隔错开。

P-S 的两个 smoke 也均通过完整门禁：eval1/2 的 episode0 视频分别为 359/325 frames，episode1 均保留 no-video 证据。当前本轮已新增并登记 6 条 formal100；没有未收尾的短 smoke。所有结果位于 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/` 的各 run leaf。

## 2026-09-13 19:23 CST：put-back N/S 终验归档与高频评测准备快照

本节只收尾已自然停止的 formal100，并记录高频方案的独立准备状态；没有重跑、拼接或按成绩筛选 episode，也没有修改任何活跃 runtime。

四条 put-back formal 均重新核对原始 `diagnostics_summary.json`、`episode_diagnostics.jsonl`、`seed_preflight.jsonl`、`processes.jsonl`、`video_checks.jsonl`、worker/scheduler 日志和配对 smoke2。每条 summary 均为 `completed`、target 100、error null；100 条固定且连续的 accepted seed、100 个 terminal diagnostics、100 个 scheduler `episode_terminal` / exit 0、100 个 video check `ok=true` 均成立，前五个视频实际可解码。所有自有 child 都有受控退出记录；EOF、ConnectionReset、traceback、segfault、RPC/runtime-error、driver/renderer marker 均为零。每条 formal 的 command manifest SHA 与自身 smoke2 一致，且保留 `checkpoint_metadata/lineage/config_source/input_audit.json` 和 `input_manifest.json`。每份 worker log 各有一条已知、非致命的 SAPIEN Vulkan ICD warning，未作为基础设施失败。

| run | 固定环境 seed | score | matching smoke2 | MAM job | final_review SHA-256 |
| --- | --- | ---: | --- | --- | --- |
| `c_put_back_no_memory_trainseed0_evalseed1_100ep_r3` | `200000..200099` | 27 / 100 | `c_put_back_no_memory_trainseed0_evalseed1_smoke2_r3` | `30fda7f6-0d1b-440d-857b-85e203dc9963` archived | `5026bad9709661858c940ae26e587af1adc99b3476a148cd7fe178574bfb2c8a` |
| `c_put_back_no_memory_trainseed0_evalseed2_100ep_r3` | `300000..300099` | 22 / 100 | `c_put_back_no_memory_trainseed0_evalseed2_smoke2_r3` | `479c266c-7530-404b-9071-2f68344e2190` archived | `78e87aedac0b6e68b57e45cb940385621f05b3fd6b249313730e82c59687109c` |
| `c_put_back_serial_lag30_trainseed0_evalseed1_100ep_r3` | `200000..200099` | 44 / 100 | `c_put_back_serial_lag30_trainseed0_evalseed1_smoke2_r3` | `81818520-2cfb-4f20-a98a-712c06db482a` archived | `96ca056e69a4fe591aedfdd9ecb9dbf109d449a31fb74d9fec1e1335e4537fbf` |
| `c_put_back_serial_lag30_trainseed0_evalseed2_100ep_r3` | `300000..300099` | 51 / 100 | `c_put_back_serial_lag30_trainseed0_evalseed2_smoke2_r3` | `cdd254f1-b01f-4cf8-9017-cd7259403ee2` archived | `15d0143d9cd67fb009a095887e7ac7feabbdd85988c0ac5c5004bb4429e8708f` |

上述四条的运行时为 clean、冻结的 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。结果根为 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/<run>/final_review.json`；四份 smoke、formal raw artifact 和 final review 均保留，MAM 仅停止跟踪已结束的 PID。

同轮已归档的 J 结果保持不变：`c_rearrange_full_t_plus_1_trainseed0_evalseed1_100ep_r3` 为 87 / 100（`a0276c6b0a19d439208895c941292328bba72698663711c2adc17cb264e3b378`，matching `...evalseed1_smoke2_r3`，job `884096c3-f7ad-48f2-b1a7-843bc0c2cb66`）；`...evalseed2_100ep_r3` 为 90 / 100（`66f6a7991daae578a773209024825fac034e83f43c42f57ea2fc65133e6c143a`，matching `...evalseed2_smoke2_r3`，job `071c8a2e-c00f-46d7-b180-c31c8e91c718`）。两条都是固定 100 条完整结果，原 archive 保持不变。

### 高频状态推理：独立 runtime 与冻结清单

新路径为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-highfreq-base`；三树均 clean，冻结在 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。它只读复用 checkpoint/assets，未改写活跃 r3 tree、checkpoint 或 `eval_result`。

私有准备产物位于该 runtime 的 `.local/highfreq_preparation/`：

| 文件 | SHA-256 |
| --- | --- |
| `checkpoint_inventory_and_frozen_matrix.json` | `1345324299f57a99296ad419afde20c723cd75854e2e92c3403ce7faea4f7113` |
| `baseline_manifest_inputs.json` | `138d49a3f2289300e71e5fd3d3f5cd6cae178ad1c8b2c759eb1b6a8cb4399610` |
| `frozen_run_matrix.md` | `5b5bc1369017893a41b3b7df83470276106d885e092e9d102f5ebc3663cc2204` |

清单冻结 24 个 future formal100：J HF-fixed 与 J HF-event 各两任务×三 eval（12），S HF-fixed 两任务×三 eval（6），J HF-periodic K10 两任务×三 eval（6）。每个 arm/eval 仍要求自身严格 matching smoke2；另有 eval0 的 `100000/100001` baseline/shadow 工程配对，单列为工程等价检查，不能充当任何 arm 的 formal gate。实读基线配置的 `random_light=false` 和 `crazy_random_light_rate=0` 已进入准备留痕。

C3 GPU0 的稳定基础 renderer 40-reset gate 仍在运行：MAM `9325bb73-243c-405f-b9af-bf719d7ade20`，PID `1270746`，receipt 目标为 `records/renderer_reset_gate_c3_gpu0_highfreq_base.json`。本次快照中进程仍存活、worker log 继续写入，但 receipt 尚未产生；因此没有将 CPU/import 或进行中的 GPU job 表述为 gate PASS。结束后才会审计 40/40、ready/nonterminal、exit 0、error null 和零基础设施 marker，并据此 archive 或记录失败。

高频源码 task `0acf5d43-91b6-4171-b727-e3fe0f7e7939` 当前公开 revision 为 `7009b32ca379c4d188e631775c638ebeafae2498`，状态仍为 working，报告仍是 draft。本任务尚未收到独立 review PASS 和 Manager 的部署准入；因此没有 cherry-pick/deploy 该实现，也没有启动任何高频 engineering smoke、matching smoke 或 formal。待源码、独立 review 与 Manager 准入三者齐备后，才会在上述独立 runtime 接入指定 commit，并按冻结矩阵执行所需 gate→matching smoke2→formal100。

### matching smoke 临时产物清理回执（2026-09-13 19:25 CST）

依 RMBench 实验规范，四个已验收且已归档 formal 的 task-owned matching smoke2 leaf 已清理；formal raw artifact、`final_review.json` 和 MAM archive 均未改变。每个 formal leaf 新增 `smoke_cleanup_receipt.json`，其中保留 smoke 的 completed/2 条 accepted terminal/video/no-video/scheduler exit 0 结论、formal 的 final-review SHA、formal command 所引用的 smoke 路径、六份核心 smoke artifact SHA 和删除前目录统计。正式 leaf 的 `command.txt` 仍保留历史 smoke 路径，回执明确该路径已按验收后的临时产物规则删除。

| formal run | 删除的 matching smoke leaf | 删除前文件 / bytes | cleanup receipt SHA-256 |
| --- | --- | ---: | --- |
| `c_put_back_no_memory_trainseed0_evalseed1_100ep_r3` | `c_put_back_no_memory_trainseed0_evalseed1_smoke2_r3` | 51 / 1,864,401 | `09def792d79f920b4461d5ec26cb325332150687d04e7b54674f747fe3a76015` |
| `c_put_back_no_memory_trainseed0_evalseed2_100ep_r3` | `c_put_back_no_memory_trainseed0_evalseed2_smoke2_r3` | 51 / 1,733,810 | `671cce3ec5e9e03c7fa1195b741732b16f20cdc36e9ffcfe539b52e834bd90df` |
| `c_put_back_serial_lag30_trainseed0_evalseed1_100ep_r3` | `c_put_back_serial_lag30_trainseed0_evalseed1_smoke2_r3` | 51 / 1,891,558 | `a54cfba3e7fe4c3956df84932d412ec0cec539ac3192dda2ce011838dbf1a46b` |
| `c_put_back_serial_lag30_trainseed0_evalseed2_100ep_r3` | `c_put_back_serial_lag30_trainseed0_evalseed2_smoke2_r3` | 51 / 1,854,277 | `f645bb09afcbe7816e9dcb91a37c511c12191e7a1998d864ecfdd23815153161` |

因此前节“smoke raw artifact 均保留”仅应理解为 formal 验收前的留存状态；最终清理状态以本节回执为准。

## 2026-09-13 19:41 CST：C3 highfreq-base 40-reset renderer gate PASS

已验收并归档 MAM job `9325bb73-243c-405f-b9af-bf719d7ade20`。这是 C3 GPU0 的**稳定基础 runtime renderer 生命周期门禁**，只运行 `put_back_block/demo_clean_eval` 的 reset，不启动 policy 或写入 `eval_result`；它不代表高频状态推理源码已部署、review 通过或准入。

receipt 为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-highfreq-base/records/renderer_reset_gate_c3_gpu0_highfreq_base.json`，SHA-256 `565a83ef9e20713a871be9f1c41f5da2b1a94c072420e07a23309b70bb3f273a`：`passed=true`、`completed_count=requested_count=40`、`error=null`，固定 seed `100000..100039` 和 episode id `0..39` 连续。每行均为 `accepted=true`、`state=ready`、`terminal=false`、`logical_step=0`、`failure_reason=null`。receipt 的 ConnectionResetError、EOFError、renderer/driver、segfault、core dump 和 traceback marker 都为零；独立扫描 worker/outer logs 的 RPC/runtime marker 亦为零。outer log 记录 `passed=true, completed_count=40`。

核验时 outer PID `1270746` 已停止，19400/19402 无监听，GPU0 为 1 MiB used / 24,080 MiB free / 0% utilization。冻结 runtime 三树保持 clean：RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。

审计回执为 `records/renderer_reset_gate_c3_gpu0_highfreq_base.review.json`，SHA-256 `c88645dd60cef7eec14537d297c963a3116fffa54a574554a1360c77a02b4159`；它保存 receipt/worker/outer SHA、逐项门禁结论及进程释放状态。高频源码 task `0acf5d43-91b6-4171-b727-e3fe0f7e7939` 仍未收到 code review PASS 和 Manager 部署准入，本 task 未接入或启动任何新的 highfreq smoke/formal。

## 2026-09-13 20:18 CST：put-back N/S 缺失 eval0 接续

按最新已发布要求，先只读检查共享结果根；P-N/P-S train0 仅有已验收的 eval1/2 formal leaf，eval0 没有 complete formal、smoke 或失败 leaf，因此新建独立 eval0 名称，未拼接或覆盖任何既有结果。冻结 runtime 为 C1 共享路径
`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-putback-baselines-yaml`，三树在启动时均 clean：RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。

两条 formal dry-run 均使用正确的 `openpi/.venv/bin/python` launcher，未加载 GPU 或启动服务。P-N 的 dry-run SHA-256 为 `62f912ca45b8661f5791ecc6e879c5d4f585a8b96bd0ba0daedc895684257d3c`，P-S 为 `7ddbaf67636ea50d80393c0365888ef5d3580d81ab8cb6e1787f1e8e1c6909ba`。它们分别确认 eval0 manifest/audit 为 `7c211eda03bf7743d63f9657a32c296fb24c93d5cbd683caff0aa7c05de7b02b` / `6b86e8906a180eb1d5ef89fb345543bf20d0ccd7ef77f744355b5cb54e82121f` 和 `e4cfa333b77db30f942e502bf176b1fddcb730095faf44e8624d2825a486f60b` / `8eb767a16f46078059af78080625a7896028b4baf819cab27b9999182c39b523`，checkpoint metadata hash 分别仍为 `fbf28132edc56ce1d187f2435aad956066007d51758ed50576912a461c4e60e1` / `be0b69aee7cadf39bb223f130836cf5f1552cbfd4609d18e75772a9b9b9ba296`。两条均固定 train0/eval0 和环境 seed `100000..100099`，P-N 用 C1 GPU1/19410/19412，P-S 用 GPU2/19420/19422。

P-N 的 matching smoke `c_put_back_no_memory_trainseed0_evalseed0_smoke2_r3` 已完成并通过独立审计：summary `completed`、error null、2 个 accepted preflight 和连续 `100000/100001`、2 个 terminal diagnostics、两条 scheduler `episode_terminal` / exit 0、episode0 视频解码 500 frames、episode1 明确 no-video，日志零 EOF/ConnectionReset/traceback/segfault/runtime/scheduler-before-terminal marker。其 smoke review 为 `records/c_put_back_no_memory_trainseed0_evalseed0_smoke2_r3.smoke_review.json`，SHA-256 `7b47b1980562e9224c4f0cc2cb16e9e3f6d3f18be45dc29f4275ded2477cd1f3`；正式 dry-run 与该 smoke 的 manifest、source、解析后的共享 smoke leaf、GPU 和 ports 一致。两条 smoke 的任务成功率不作为选择门槛。

P-N 正式 leaf `c_put_back_no_memory_trainseed0_evalseed0_100ep_r3` 已于 20:17 CST 在 C1 GPU1 实际启动，outer PID `137091`，日志为 runtime `records/c_put_back_no_memory_trainseed0_evalseed0_100ep_r3.outer_20260913.log`，MAM job `d40eb04a-0ad4-421b-a74a-7734d6f3c9db` 已登记为 running。P-S matching smoke `c_put_back_serial_lag30_trainseed0_evalseed0_smoke2_r3` 正在 C1 GPU2 运行，outer PID `129295`；它通过自身完整门禁前不会启动 formal。HF 源码仍未接入该 runtime 或用于任何评测。

P-S smoke 同样已完成独立验收：连续 `100000/100001` accepted/terminal、两条 scheduler `episode_terminal` / exit 0、episode0 视频解码 330 frames、episode1 no-video、零基础设施 marker，且 smoke/formal 的 manifest、source、GPU2/19420/19422 与解析后的共享 leaf 一致。其 review 为 `records/c_put_back_serial_lag30_trainseed0_evalseed0_smoke2_r3.smoke_review.json`，SHA-256 `a0d9948549c5ecd9d23a3b36a1e81e793146dce51aebf5f19487e24c0d6ecee1`。

P-S 正式 leaf `c_put_back_serial_lag30_trainseed0_evalseed0_100ep_r3` 已于 20:20 CST 在 C1 GPU2 实际启动，outer PID `139655`，日志为 runtime `records/c_put_back_serial_lag30_trainseed0_evalseed0_100ep_r3.outer_20260913.log`，MAM job `a2f4bc51-5791-4e7d-96df-f9f26f6a6313` 已登记为 running。此刻 P-N/P-S 两个 eval0 formal 都在运行；matching smoke 和 audit 输入暂保留，待各自 100 条完整终验、final review 和 MAM archive 后才按实验规范清理。

## 2026-09-13 22:24 CST：HF matched-baseline RNG 作用域 CPU 准备

按发布 revision `a3c123524199886457c8a9ea87aacda258b2ac30`，只更新 C1 私有 highfreq 准备清单，未接入作者当前候选、未创建高频 manifest/结果 leaf、未启动 GPU，也未修改阈值、任务、checkpoint、活跃 P-N/P-S runtime 或其 MAM job。

准备目录为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-highfreq-base/.local/highfreq_preparation/`。正式矩阵现有 36 条 formal100 / 3600 episode executions / 0 新训练：J matched baseline 6 + J HF-fixed/event 12 为第一层 18；S matched baseline 6 + S HF-fixed 6 为第二层 12；J HF-periodic K10 6 为第三层。12 条 matched baseline 均使用各自 J/S checkpoint、H50/K30、原 task/environment/MemoryContext 行为，无中途 probe、replan 或 cache replacement；它们仅显式采用新的 RNG 协议，不能与历史普通 baseline 成绩跨协议拼接。

所有 36 条 future formal profile 冻结为 `episode_reset_key0_independent_probe_v1`：action 初始为 `jax.random.key(0)` 且每个 accepted episode 边界恢复；probe 使用独立 `jax.random.fold_in(jax.random.key(0), 0x50524F42)` 流并逐 episode 恢复，绝不消费 action stream。matched baseline 保留独立 probe stream 身份但要求 `probe_count=0`。普通 baseline/shadow 保持 `legacy_run_continuous_action_v1`：一个 policy server 在 run 内跨 episode 连续消费 action RNG，普通 reset 仍为 no-op。工程清单现有四条普通 legacy baseline/shadow 与四条 J matched baseline/shadow 对；工程 run 永不充当 formal matching smoke。

未来实际 manifest 的语义绑定要求已写入：`profile_kind`、`rng_scope_id`、action/probe 初始 key 表达式和 episode 生命周期、probe consumption expectation、checkpoint/H50/K30/domain-randomization 合同；matching smoke/formal identity 还必须绑定这些字段、精确 source hash、manifest hash、checkpoint、环境 seed 组和 smoke identity。原 24 条 HF 的 fixed/event/periodic mode 合同逐项保持不变；event threshold、K 与 probe interval 未改。只有精确源码记录该显式接线、独立 code review PASS 和 Manager 部署准入后才能产生实际 manifest。

更新后的 artifact SHA-256：

| artifact | SHA-256 |
| --- | --- |
| `checkpoint_inventory_and_frozen_matrix.json` | `20e414eb14c7f752b158949fda2c62b678e6c3eab2bd2a56452f315364700adb` |
| `baseline_manifest_inputs.json` | `305250a177196a83bc27464b3c9eec1dc2d60a61d27bad4472a608c8aa4d5610` |
| `frozen_run_matrix.md` | `f5e5dc56d13acea26d339387b790bec167f486fa3931f7041822ed7120684a69` |
| update receipt | `3c0eaf7f5105c3bd6351b35ba5cd79e6beaf135e5a546a85769e96b83bf39f69` |
| independent CPU validation | `8afd7013ab166a0e011c2e195839e725a9e38aa0286d8cf52c720b4933012a1f` |

独立 JSON 校验复核 36 个唯一 smoke/formal 名、`100000/200000/300000` 三个完整固定环境 seed 组、所有 formal 的 reset RNG scope、12 条 matched baseline 无 probe/replan、原 24 条 mode 合同、工程 scope 4 legacy + 4 reset，以及没有 `c_hf_*` 结果 leaf。highfreq-base 的 RMBench、bridge、OpenPI tracked 状态仍 clean；HF 作者实现仍未取得 code PASS 或 Manager 部署准入。

## 2026-09-13：P-N eval0 formal100 终验完成，待归档

本节只处理 C1 GPU1 的 put-back no-memory / trainseed0 / evalseed0（P-N）；未修改、轮询或判定 P-S。MAM job `d40eb04a-0ad4-421b-a74a-7734d6f3c9db` 的 outer PID `137091` 已停止，终验前确认端口 `19410/19412` 无监听。

正式 run `c_put_back_no_memory_trainseed0_evalseed0_100ep_r3` 已由独立 Python 校验器从原始产物完整复核：100 个 accepted preflight 和连续固定环境 seed `100000..100099`、100 个 terminal diagnostics、100 个 episode JSON、100 个 scheduler `episode_terminal` / exit 0、102 个 start 与 102 个 matching exit 记录、100 个 `video_checks ok=true`。episode0–4 五个 MP4 均用 cv2 逐帧解码，各为 500 帧；104 个 formal log 全量扫描的 EOF、ConnectionResetError、traceback、segfault、driver、RPC/runtime 和 scheduler-before-terminal marker 均为零。worker 仅有一条已知、非致命的 SAPIEN `Failed to find Vulkan ICD file` warning。

结果为 **17 / 100（17.0%）**；83 条均保留为正常任务失败，未重跑、拼接或按分数筛选。formal 的 copied input audit / manifest SHA-256 分别为 `6b86e8906a180eb1d5ef89fb345543bf20d0ccd7ef77f744355b5cb54e82121f` / `7c211eda03bf7743d63f9657a32c296fb24c93d5cbd683caff0aa7c05de7b02b`，31 份继承 metadata 均逐项复算。运行时三树均 clean 并固定为 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。

matching smoke `c_put_back_no_memory_trainseed0_evalseed0_smoke2_r3` 也从 raw artifact 重验：`100000/100001` accepted terminal、两条 scheduler exit 0、episode0 解码 500 帧、episode1 no-video、日志零基础设施 marker；其既有 review SHA-256 为 `7b47b1980562e9224c4f0cc2cb16e9e3f6d3f18be45dc29f4275ded2477cd1f3`。formal command 保留该 smoke 引用，并保留 input audit/manifest 副本。

正式验收记录为 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_put_back_no_memory_trainseed0_evalseed0_100ep_r3/final_review.json`，SHA-256 `d1a50ca1c31b861520ba2e12908babcd2dd5370e05998aaa1dde514e5626ce47`；其中保存核心 raw artifact、配置、command、scheduler 和 lineage 的 SHA-256。下一步仅归档该已完成 MAM job，再将 matching smoke 以 cleanup receipt 留痕后删除；formal raw artifact 与 final review 保留。

### P-N archive 与 matching-smoke 清理已完成

MAM job `d40eb04a-0ad4-421b-a74a-7734d6f3c9db` 已于终验后归档，archive note 固定记录完整 `100000..100099`、17/100、final review SHA 和 PID/端口释放。正式 leaf 已保留 `smoke_cleanup_receipt.json`，SHA-256 为 `688aff3ad62f52427b9f058cb69937a79deb008ad654abbf75a862f6ec6f86fb`：删除前 matching smoke 为 51 个文件 / 1,844,435 bytes，receipt 保留 smoke review SHA、completed/2、accepted terminal、video/no-video、scheduler exit、核心 raw artifact SHA、formal command 引用及 formal final-review SHA。随后只删除 `c_put_back_no_memory_trainseed0_evalseed0_smoke2_r3`；P-N formal raw artifacts、lineage、副本和 `final_review.json` 均保留。本节没有对 P-S 做任何操作。

## 2026-09-13：P-S eval0 formal100 终验、归档与 smoke 清理

按 Manager 的接续要求，本节完成 C1 GPU2 put-back serial-lag30 / trainseed0 / evalseed0（P-S）的已停止 formal；没有重启、拼接 partial 或改动 frozen runtime。MAM job `a2f4bc51-5791-4e7d-96df-f9f26f6a6313` 已归档，outer PID `139655` 已释放，端口 `19420/19422` 无监听。

正式 run `c_put_back_serial_lag30_trainseed0_evalseed0_100ep_r3` 的独立 raw-artifact validator 已完整通过：100 个 accepted preflight 与连续固定 seed `100000..100099`、100 个 terminal diagnostics、100 个 episode JSON、100 个 scheduler `episode_terminal` / exit 0、102 个 start 与 102 个 matching exit 记录，以及 100 个 `video_checks ok=true`。episode0–4 用 cv2 逐帧解码，帧数依次为 320、500、358、359、500。104 份 formal log 全量扫描的 EOF、ConnectionResetError、traceback、segfault、driver、RPC/runtime 及 scheduler-before-terminal marker 均为零；仅有一条已知、非致命的 SAPIEN `Failed to find Vulkan ICD file` warning。

结果为 **41 / 100（41.0%）**；59 条正常任务失败完整保留，其中 `button_not_pressed_after_center=46`、`button_press_insufficient=13`，没有按分数筛选或重跑。运行时三树均 clean 并固定为 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。formal copied input manifest / audit SHA-256 分别为 `e4cfa333b77db30f942e502bf176b1fddcb730095faf44e8624d2825a486f60b` / `8eb767a16f46078059af78080625a7896028b4baf819cab27b9999182c39b523`，31 份继承 metadata 也均逐项重算。

matching smoke `c_put_back_serial_lag30_trainseed0_evalseed0_smoke2_r3` 同样从 raw artifact 重验：`100000/100001` accepted terminal、两条 scheduler exit 0、episode0 解码 330 帧、episode1 no-video、零基础设施 marker；其既有 smoke review SHA-256 为 `a0d9948549c5ecd9d23a3b36a1e81e793146dce51aebf5f19487e24c0d6ecee1`。formal command 保留 smoke 引用和 input audit/manifest 副本。

稳定正式路径为 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_put_back_serial_lag30_trainseed0_evalseed0_100ep_r3/`。其中 `final_review.json` SHA-256 为 `ba49592d1d914c2cf49e997b1b7f09f69f5e66157751316e5353d3d6b29e5a68`，保存所有核心 raw artifact、配置、command、scheduler 和 lineage 哈希。matching smoke 已依实验规范删除；formal leaf 的 `smoke_cleanup_receipt.json` SHA-256 为 `0547d40468bb1f0d200d81ea5c4af99b94c80091dee8ebf3d9e6f983d9ccc7c4`，保留删除前 51 个文件 / 1,849,489 bytes、smoke core hash、验收结论、formal command 引用和 final-review SHA。formal raw artifacts、lineage 和 final review 均保留。

## 2026-09-13 23:24 CST：put-back T train0 的 eval1/2 smoke 通过并启动 formal100

按发布 task revision `966b80919a2636022b8aa343a32aaa627939d1e0`，先只读去重旧 T eval1/2 的 r2 partial leaf（各仅 23 条 preflight/diagnostic/video、48 条 process、没有 `final_review.json`），未复用或拼接。随后在 C1 独立、冻结且 tracked-clean 的 runtime
`/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-putback-baselines-yaml` 完成各自 matching smoke2；RMBench 为 `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge 为 `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI 为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。checkpoint 固定为 `pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s0/20000`；未训练、未接入 HF、未改动 runtime、checkpoint 或协议。

| matching smoke | 固定环境 seed | manifest / audit SHA-256 | raw-artifact gate |
| --- | --- | --- | --- |
| `c_put_back_full_t_plus_30_trainseed0_evalseed1_smoke2_r3` | `200000`, `200001` | `00c2a8af8c8eb455be87104fa66789266c8fbea2f65a7fa2ca4922003130f0c2` / `daa7428d0f4a3962d4bc651fad99f032c1e6ae79baff527c66d46eeccd96d8eb` | `completed`, target 2, error null；两条 accepted terminal、两个 scheduler exit 0；episode0 MP4 经 cv2 解码 325 帧，episode1 no-video。`seed_preflight` / diagnostics / video / processes SHA 分别为 `5691669ae57d33eccd3721fb6ed855f26faef232972440dd9f550e1b2d8c5875` / `cd874c5de8e7d7e15997ac7992a40dce74be1014ccaced3b5d0efeee3175b901` / `bdc82271083a03d45860567258fbdbe9e41ec265151ea65801be79fb98f75a41` / `61a4b546f47a24618f651ce094348b67a1b36f59faf9f52cb81da055de234e57`。 |
| `c_put_back_full_t_plus_30_trainseed0_evalseed2_smoke2_r3` | `300000`, `300001` | `735f9d1ae5af382e481a7b7289e76a7ed4268d48b7fc1fc9d64e92ad983569ab` / `b69c305f210f7f91501b2b3476341fcefaabee886955a214879aebbb98b87d1e` | `completed`, target 2, error null；两条 accepted terminal、两个 scheduler exit 0；episode0 MP4 经 cv2 解码 328 帧，episode1 no-video。`seed_preflight` / diagnostics / video / processes SHA 分别为 `3a1b5e3bef956e7e01c792037da5d21f212dffc68aced516bdbee8f449c0b664` / `dd836075a08e91aeb3d5b9171888385afb8d9a0676e6cdb2d31fdb15b29f615c` / `f6d62bccf423028f9ae5de64d8ffa5e7bfd8a8ea03846e33fe4a21399af0353b` / `d92bad3702f9881a40cf63e444a9f656e51bf44d035ab96e88479e2d484fa314`。 |

两个 smoke 均逐树扫描 EOF、ConnectionReset、BrokenPipe、traceback、segfault、driver、RPC/runtime 与 scheduler-before-terminal marker，结果为零；worker 各有一条既有健康 run 同样存在的 SAPIEN `Failed to find Vulkan ICD file` warning，未视为基础设施失败。正式命令的 metadata 合同仍为 `put_back_block_full_t_plus_30`、joint-dense `phase, origin_mat`、H50/K30、`last_executed` feedback、`demo_clean_state` 来源、policy RNG key 0 和 `demo_clean_eval` 环境。

| formal run | C1 GPU / ports | 固定环境 seed | outer PID | MAM job | 启动后核验 |
| --- | --- | --- | ---: | --- | --- |
| `c_put_back_full_t_plus_30_trainseed0_evalseed1_100ep_r3` | GPU1 / 19410, 19412 | `200000..200099` | 428749 | `da058195-ff39-49ed-8e83-be5e1a8aaa7e` | job status `running`；两个服务已监听并已有正常 episode0 raw artifact。 |
| `c_put_back_full_t_plus_30_trainseed0_evalseed2_100ep_r3` | GPU2 / 19420, 19422 | `300000..300099` | 431409 | `3191f8c6-4c53-48a3-9ab7-8b44216ab2c0` | job status `running`；正式启动器、独立结果 leaf 与 matching smoke 引用均已建立。 |

两条 formal 均从不存在的新 r3 leaf 以 `--smoke-run` 启动，没有覆盖 partial 或有效结果；两条 MAM job 均记录真实 remote PID/boot identity。本轮至此不等待 formal 完成；后续由 MAM 唤醒后再按完整 100 条 raw-artifact 合同验收、归档，并在正式验收后清理 matching smoke。
# put-back J/T train2 eval1：两批正式100独立证据核验

使用 terra/max，范围仅已完成两叶的只读证据审查；科学裁决及论文由 Manager 完成。先读 MAM AGENTS/README/.local/README/.local/wuwen-4090.md，mam task show 本 TASK-ID，并读取源任务 e6908de7-4b02-465a-987b-a19eba7a315a 最新已发布 report d034be9b616949f9556fb9c7665fc157007d6bc5 的置顶部分。上次 review 77900702 已归档，不复查旧结果或 HF。

C1 正式根 /mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/：
- c_put_back_full_t_plus_1_trainseed2_evalseed1_100ep_r3，owner 声称70/100；final_review SHA256 32864e05054f65de653565d19908271e30ef8880b0f1eacb220100c5b41444bd；smoke cleanup SHA256 0f1fcc6c9a51e74ffb4ea0bfdfc261a8686312c1f843e590ac896147b065fde5；已归档 job 0ccf5f61-bd19-4df7-88dc-9ec2f49d79c4。
- c_put_back_full_t_plus_30_trainseed2_evalseed1_100ep_r3，owner 声称68/100；final_review SHA256 eaac667a3ecd3236aca2c8cadf5eec3a1eee35edd9ab60b513a2669c75d1b94a；smoke cleanup SHA256 49f1395c498f8e234be895fa68373e667b39d5c75936580ed8aa68ace523e12e；已归档 job 1ae7a228-0a13-4074-88ba-8b12886e1676。

独立重哈希 final review 及其核心原件引用，重算各100条连续 episode0..99、accepted preflight、seeds200000..200099 和 diagnostics.episode_status terminal，重算结果及失败类别，核验100个episode、视频策略与已有解码记录、scheduler/自有进程退出、基础设施日志、smoke保留链和实际job身份。明确未重复解码视频、未重哈希多GB模型及已经删除的smoke raw的范围限制。

实际冻结 runtime c-eval-putback-baselines-yaml：RMBench f401f5279c95451eb424ac98b831bab5552b2120 / bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 / OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。核对真实checkpoint train2/eval1、H50/K30、首infer90秒/后续30秒、历史continuous action RNG、metadata和实际command；区别于源任务登记的worktree HEAD。task-local终验器 SHA256 a532cd5d6b76c637165b05c9d0a431f820ad11ea6f59d4f9aa763aae201aa423。

不执行模型/仿真/训练、不拷大资产、不修改产物、冻结源码、论文或owner报告，不触碰正在运行的 train2/eval2 或 HF。无源码变更，无需无关worktree。可参考旧review流程但必须独立核验本次原件。将小型原始证据副本和重算receipt置于本task目录，保留可供Manager独立核算的两叶final_review、preflight、diagnostics及核心引用。交简短report、receipt路径/hash、是否有计入正式结果的阻断与实际范围限制；发布后正常结束turn。

## Manager 最终验收（2026-09-14）

接受独立report 1cbebfb6f7623e97be069ddf13dc1c37b5852446 和receipt 8f18a36aa368cd7f723d8eed62cc9c44fb14e229f7176bbfa2ed741125f0ba29。Manager另从本地原件和C1重哈希两份final review及20项核心引用，独立重算200条连续seed/preflight/terminal/outcomes/失败类别、video策略、自有进程退出、actual config与smoke命令链。J70/100、T68/100纳入原协议正式台账；视频重解码、大模型完整rehash及已删除smoke raw的限制保留。

验收收据 /root/Documents/task-state-vla-paper/docs/analysis/putback_jt_train2_eval1_acceptance_20260914.json SHA256 2e2e91920f15378d36c1b65747e11015a32e84307c3b7619d5971131ebe3308f；独立receipt已原字节保存同目录。新快照 accepted_results_20260914_jt_train2_eval1.json SHA256 1419d39159916795b0786d02a7044eb35df15cb24d5492c8c7258964c14c8f43：50批/5000执行/20模型/14完整3eval。论文资料提交32554ae，编译PDF仍冻结44批。train2/eval2归源owner继续；本review完成，可归档。
