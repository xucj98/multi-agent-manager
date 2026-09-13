# 同实例probe验证：冻结工具与C3执行身份核对

Review source delivery (source TASK-ID: 0acf5d43-91b6-4171-b727-e3fe0f7e7939):
{
  "task": "0acf5d43-91b6-4171-b727-e3fe0f7e7939",
  "commits": {
    "openpi": "0ce566bd34f99cb4775422f012ab67c16aa53885",
    "robot-bridge": "ffa122494c19e1c0154e877010f7b470967ccfc6",
    "RMBench": "6abebf08d084d0be43aa56ebe158dc8395fa58e4"
  }
}

Source task requirements:

# 高频状态推理与偏差触发replan：复用checkpoint的推理实现

## Manager 工具验收：两处实测缺口，先窄修 CPU（尚未授权 GPU）

Manager 已亲自阅读 report c17983bba05513737c9188efc1dd185947e9e477、完整1000行helper、8个测试、说明和source audit，并核对工具 SHA fa9bf3292a09e39dd1d2421d4276c16b76034deeb22794ed61cd1681b95ae9e1、tests SHA f881cde072d2518413ee21ba1cb8ab0bd8bc816cfa865efc3e8cd29c1489f6aa。独立复跑现有8个CPU测试全部通过，但另外两个使用真实工具和既有FakeBackend的有界CPU反例发现以下必须修复项；不能凭原8项通过运行GPU。

1. **调用前发生实际key物化，与明确合同冲突。** default_key_snapshot 直接 np.array(jax.random.key_data(key))，_state 又在 run 开始、_reset 和 _invoke 的 policy_state_before 中同步调用。Manager 的计数seam观测到第一次 infer 前调用了10次key_snapshot，首次甚至在reset前。改为仅捕获真实不可变key对象引用和Python序号，在对应正常backend调用返回（包括异常返回）后才物化这些前后引用，不在首次infer/reset后至调用前读GPU数组。C0/C1完整结果比较后才进入P，P reset到首probe之前也不新增实际key物化；必要的前置reset一致性检查可用已冻结源码支持的对象引用关系和序号，实际key内容在对应调用后核验。不要为了修时序牺牲实际key/初始key一致性检查、停止边界或偷偷推迟到全部调用后才发现第一个probe修改action。保留来源固定输入deepcopy，无全局patch/split/wrapper。增加一次真实工具CPU时序测试，明确拒绝上述pre-call物化，覆盖保存的旧key引用没有被后续新key覆盖。
2. **收尾异常可把实际8次调用记成0并丢失产物。** Manager 注入key_snapshot在第三次action返回后失败，run 的finally再次读取key时抛出，execute的外层catch把它当precheck_or_backend_initialization_failure并生成新CallBudget；实测backend已调用3action+5probe，最终receipt却写0+0且无任何pickle。把checker及已用budget/calls/artifacts保留到外层，收尾、key物化、恢复或序列化失败均不得清零或误标尚未加载。保存已有完整输出；恢复用独立保护的finally保证仍尝试执行；保留首因与另外的收尾错误，不让后者覆盖前者。无需建新框架，只修现有控制流并增加覆盖实际反例的CPU测试。

另外更正 README/report 中“policy state 在收据后恢复”的表达：现代码在 run finally 内恢复，磁盘receipt由外层随后写；区分恢复前状态已经记录与磁盘写入时间，按修正后的真实顺序说明。

本轮只修改task-private helper/tests/说明与报告，不动冻结三库，不运行GPU/模型/reset环境，不新增采样预算。保持原设计3 action+5 probe上限、无warmup/retry及普通输出严格比较；不因失败放宽条件、不扩大为环境等价或效果实验。交修复diff、新hash、CPU结果和新plan（旧plan保留）后正常结束turn，Manager验收再发布有限执行授权。

## Manager新对照设计：同实例probe副作用检查（本次仅CPU准备）

Manager已独立验收最后pair报告f2d2d63fb941f0c1c9075aaa15050506f9ea0855的诊断事实：v2分析SHA be1382272b3cbae2454b17e3bcedaf2656c6693da88fffdfccbde3bf6473c5c7及45个不同绝对路径引用文件已重哈希。两侧actual request（包括cmd、三图像、state、memory、prompt）/call args/kwargs逐字段同dtype值相同；实际metadata/checkpoint校验和服务命令、当前记录环境一致。两臂各一次accepted reset episode0/env100000、infer/execute各一次、原iteration后clear30/logical_step0、exit70成立；自身H50→实际execute.actions.arms K30精确。跨臂H50有532/700不同（maxabs0.0036021433770656586，RMSE0.0006788336719106482）；K30有314/420不同（maxabs0.002218961715698242，RMSE0.0006341486370427415）。Manager额外检查memory_prediction_ids(50,2)及memory_prediction精确相等，memory_raw_actions(50,32)有1230个元素不同。实际PRNG key仍未观测，不作数值/编译/RNG根因推断。当前8/8诊断阶段完成，不把失败改为PASS，不增加正式计数。

Manager的判断：跨进程首query比较把重放可复现性与“执行probe是否改变后续action”混在一起；本次无任何probe便有差异，该比较不能单独裁定probe副作用。下一检查应显式有同实例自身重复对照。以下设计是未来有限检查的准备合同，不是自动解除8/8上限或GPU执行授权。

请完成上节只读source audit后，如未发现与合同矛盾的实际调用点，按此准备一个最小task-private检查脚本与CPU seam tests；若有矛盾，报告具体位置，不自行改实验或运行GPU：
- 只复用冻结HF三库和put-back J train0/20k，已有原入口baseline完整policy request。服务传输的cmd从payload按真实server相同规则剥离；不改普通输入数值/dtype/结构。只加载一次真实OpenPiBackend，调用真实backend.reset_episode_rng、infer_audited和probe_forecast，不替换Policy/model/transform/JAX随机函数。
- 顺序为C0：reset→一次infer_audited；C1：reset→一次infer_audited；只有C0/C1的完整ordinary action/state/raw输出（剔除timing）与最终action key严格相等才进行P：reset→同一个固定保存输入上5次真实probe_forecast→一次infer_audited。C1是同实例无probe的重复控制，P检验probe对正常action的副作用。五次固定输入probe只是隔离副作用，不是模拟五帧观测，不声称验证HF效果。
- 未来运行上限明确为3次ordinary action inference+5次joint forecast probe（共8次完整sampler计算），无额外warmup、重试、环境reset、仿真轨迹、episode或formal。本次仅CPU准备，尚未使用这些预算；旧8/8阶段不改记账。任一控制失败即停止后续并保留已用调用数/首因，不为了pass调整容差或增加重复。
- 用实际Policy不可变JAX key引用记录每次reset后、infer前后、probe前后的action/probe key与序号；真正数组内容转换在对应正常调用返回后或本次检查末尾进行，不在模型热路径新增全局wrapper/split/同步复制。所有probe前后action key和action序号必须不变；probe自身stream按实际前进。P的初始action key等于C0/C1，最终action key与C1相等；比较采样key如需从保存初始key离线重构，明确派生身份而非直接截获sampler内部noise。
- 普通outputs保存完整小型数组，状态和raw联合输出均检查，shape/dtype/值严格；保留每一项比较结果和实际key/调用数。旧跨进程saved output仅可额外对照且与本检查结论分开，不用它使本次同实例结论短路。推理输入不得被probe或比较工具改写；保存输入身份前后核对。
- CPU tests只覆盖控制不等时不执行probe、probe改变action key/序号或ordinary输出时拒绝、正常固定输入/key与合法probe序列通过、精确调用预算/无重试；用seam替代GPU但调用顺序和判定使用真工具。保留输入路径/hash、参数/三库身份、输出位置与最小diff，不建设新框架。默认脚本是plan/CPU，不得因工具完成自行加载模型执行。

Manager同时依据source audit裁定controller30-row与分次5-row推进等价的范围，另行安排所需验证。该同实例检查即使通过也只支持probe软件副作用边界；完整scheduler/环境及效果的准入仍单列，跨进程历史失败原件保留。交干净小型工具/测试与source audit后结束turn，由Manager验收再发未来有限GPU授权。当前任务三库源码/现有HF正式状态完全不变。


## 当前CPU接续：核对同一policy实例内的对照边界

已收到最后shadow报告f2d2d63fb941f0c1c9075aaa15050506f9ea0855；正常action预算8/8耗尽，当前仍不增加GPU/reset/replay/完整轨迹。Manager正在亲自核对两臂原始证据，并重新判断跨进程逐位相等能否承担“shadow无副作用”的准入作用，不把已发现差异自动归因于HF算法或浮点执行。

请原terra/max执行者只做一次有界、只读的源码核对，与Manager证据审阅并行：
1. 对冻结0ce566bd/ffa12249，逐项追踪两个scheduler首个infer_audited到真实backend/Policy的调用与episode reset。列出影响action推理的可变状态（实际action/probe PRNG、计数、缓存等），区分此次receipt实际观测的值和仅由源码可推断的生命周期；不要再把stream/call当实际key。
2. Manager正在考虑用“同一已加载policy实例、固定已保存的完整输入与起始action key，在真实shadow probe之前/之后比较action/state/最终key”隔离probe副作用。只核对这个对照在现有代码上是否可实施、需要复位哪些实际状态、真实probe是否改变action路径、最少需经过哪些生产调用点；给具体源码位置和任何会使对照误判的边界。当前不实现工具、不设计新大框架、不运行模型；完整实验合同与预算由Manager决定。
3. 同时只读核对原30-row drain与shadow分次5-row drain的controller路径是否逐行执行相同传入actions，是否每次drain会额外规划/平滑/改变物理推进；给具体路径，不凭query计数或相同K声称环境推进等价。

交紧凑source audit即可，保持源码/runtime与已保存证据不变。无需外部调查、再次review全库或复跑测试。科研结论与下一步准入由Manager独立裁决。


## Manager裁决：修正shadow来源路径，补做剩余一次首query

Manager已独立核对报告61bf6a18627ad3644febdfcadd0a0478a814ce9a、原入口两侧launcher、baseline实际result config和policy身份链，以及冻结BenchmarkRunner在_require_sources之后才创建recorder/启动服务的源代码。baseline实际MemoryCheckpoint source root正确，与旧baseline命令一致；其get_metadata.policy_dir与manifest解析checkpoint、metadata/params/norm-stats加载日志吻合。此前口头推测baseline也用了错误root不成立，以实际原件为准。shadow实际root是错误的.../pi05_rmbench_put_back_block_full_t_plus_1_s0，不能解析MemoryCheckpoint/20000/metadata；failure receipt64ee0c7c9f4e4d77a99e20af55ed830bc06b42455cbe820ca34e98ceb0a89d21记录InputNotReady、preflight event_count0、scheduler_exits空、run_dir=null，属于任务私有launcher路径错误，未消耗action sample。

Manager已重哈希baseline_identity25f89ee7c4f8ba56e2976f8e4657b66af95df3c2a54e462800e065df916269e9、alignment b96be2c03c9298785b767ad751037df9680a40178df920c9f6c8e6b816610530及其与两侧runner/scheduler receipts的38个不同绝对路径引用文件。亲自重读pickle：正常请求RGB/state/memory/prompt与先前插桩输入逐字段同dtype/值相等，当前多留cmd；H50 float32前30行精确等于实际execute.actions.arms；当前H50对旧baseline为499/700不同、maxabs0.004009723663330078、RMSE0.000707095339374057，K30对旧baseline/旧shadow为298/301元素不同。actual infer/execute各1、无第二infer、原iteration成功后clear，queued30/dropped30/logical_step0，退出70及失败leaf明确。接受baseline本次有界捕获，不等同matching smoke、旧数值复现或历史差异因果解释。

现明确授权原terra/max执行者在同TASK-ID上完成以下窄修并直接补做尚未消耗的最后1次shadow action sample，无需再次等待Manager许可：
1. 本机生成原shadow launcher的独立修正版，只将--source-root MemoryCheckpoint的值改为已验明的
/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0
并使用全新result/capture/plan/log文件名，保留旧baseline和shadow失败原件/脚本；不修改已review的runner/scheduler/capture_common或三库源码。保存最小diff及内容hash。
2. 执行前先保存plan，检查实际解析的MemoryCheckpoint/20000及metadata存在、与RB_OPENPI_POLICY_DIR指向相同checkpoint、沿现有manifest身份校验；这是文件/配置预检，不做预热或额外reset/采样。核实C3 GPU0/19400,19402空闲，三库仍0ce566bd/ffa12249/6abebf08 clean，三个工具hash、旧shadow manifest/config保持。不得新改renderer/JAX/cache/超时/阈值。
3. 只运行matched shadow，put_back_block J train0/20k、env100000、一次正常action request、H50/K30、8MiB snapshot、原流程iteration/after_execute后step0 clear及无drain status；完整保留request含cmd、H50、实际K30、metadata/reset/调用身份。预计>30min登记job并正常结束turn。无baseline重跑、第二query/episode、warmup/replay/probe或正式100。
4. 与已验收原入口baseline完整输入逐字段、H50/K30、policy命令与metadata/reset/环境对照，独立检验每臂H50前缀等于其实际K30；相同输入字段全部列出，真实PRNG key仍unavailable。比较旧两侧/先前插桩已有数组仅离线，不新增样本。报告置顶应为最新状态，勿继续把已执行步骤标题写成当前CPU未执行。

本次只修确定的前置路径错误以完成原已设计的配对；正常action总预算仍8（当前7）。任何失败或post-send ambiguity都停止并保留首因，不自动增加样本或调容差。无论两臂相等与否，都不凭一组首query自动解冻HF完整匹配或formal。完成资源收尾、归档job、发布紧凑report后结束turn。


## 当前执行授权：原入口两次首 query 验证

Manager 已验收准备 report32da353ec1da3b386cfd6fe8e1b1b67806fb4d60，亲自阅读两个工具及依赖，重算runner SHA376dd1fd087a5e79a9cbda4e83d1ff5b8534dc9c59429a60acbdf8ed2a0abf34、scheduler SHA0561e295e644bee882c7abaee9d08e856b9e5ad00aeafbb4ed480ad7f3179ae2、capture_common SHAf6e80912a2d40f9298bf0060e92c7e5126d5a476d94c6a3e6c33eeed2265cc2f；在真实冻结bridge依赖上独立复跑11个CPU seam tests全部通过。结合先前独立方案核查88976c0，现明确授权同一terra/max执行者运行，不再等待另一轮许可。

将上述精确工具的小型冻结副本部署到本TASK-ID C3证据目录，复用旧C3 HF工程runtime只读源。固定C3GPU0、put_back_block J train0/20000、env100000、matched baseline和matched shadow各一次正常action request，两臂顺序执行，最多使用剩余2/8样本，无warmup/replay/probe/第二episode。核对GPU及原独占端口空闲、三库精确HEAD/clean、实际checkpoint、工具hash；根据旧工程manifest/config/command构成原入口CLI，先保存其无--execute的plan并核对旧reset/语言/配置/环境可确认部分，再在同一参数上添加--execute。不能把本次未记录或旧不可观测条件声称已相同，不新增cache/JAX/renderer override，不重装/重传模型或复制整套runtime。

每臂独立全新result与diagnostic root，max array bytes保持8MiB/每snapshot。工具保持原完整iteration/after_execute后clear和status，完成step0、queued30/dropped30且只一次infer；exit70是明确的诊断截停，必须与完整收据及原failed benchmark leaf一起验，不能单凭exit70认成功。第一臂完整有界捕获成功才进入第二臂；失败或sample-ambiguous停止，禁止自动重试/补样本。完成后检查两臂完整request各字段、H50/K30，以及与旧两侧/之前插桩捕获的精确数组差异；K30对本次H50前30需独立比较（工具只检查shape/type）。留全量输入/调用参数/输出/身份、失败叶及哈希，不把诊断当smoke成功，不解冻HF formal、不调容差。

若预计>30min登记MAM实际长进程，正常结束turn由MAM唤醒；否则完成两样本、归档已有job、资源收尾并发布紧凑report。本次只准入该明确两样本，源算法/阈值/其他任务不变。

## Manager 已接受独立方案核查：补齐两个停止边界后交工具验收

独立工程核查 report 88976c0165e29956838f62d50df7e55f0ecce66e 已完成。Manager 亲自核对冻结 transport/codec、worker execute/clear、runner _wait/_loop 源码，接受其可行性和以下增量要求；这是设计准入，**尚不是未交付工具的 GPU 准入**。作者继续准备，不扩大工作范围。

- 同步 policy RPC 返回后立即在 RAM 深拷贝完整 actual request、call kwargs 与 post-wire H50，再把未修改的原 result 还给 scheduler。磁盘文件/hash/fsync 放到完整首轮 run_iteration 和 after_execute 完成、queue clear 后，不在模型前增加 I/O。不得后台持有原数组引用；metadata/reset RPC 原样透传，不算 action sample。
- 在发送前拒绝第二次 infer/infer_audited。首个 RPC 若发生 post-send transport/capture 异常，记 sample-ambiguous 并停止，不能自动 retry；每臂最多一次发送，剩余两样本不能因错误重置计数。
- **固定 env100000 的预检拒绝必须停止。** Runner 默认 accepted=false 会 seed+=1 并再次 reset；必须在任务私有外层保留首个原始 preflight 事件后，在其进入该分支前终止。仅允许 episode0/seed100000 的一次 reset；拒绝、身份错、缺 accepted、意外 terminal 或 reset传输异常都保留失败证据并停止，不以 seed100001替代。可在原 preflight 事件发出后的窄 hook 实现，勿重写整个 runner。
- 真实 execute 后须等原 run_iteration 完成再 clear，随后仅用无 drain 的 get_episode_status 验证 logical_step0；明确 queued30/dropped30/queue空。保留原 runner 的失败处理：诊断 child 明确截停，使其在 ep0记录 scheduler_exited_before_terminal/runtime error 后终止，不进入ep1。不要把 writer 的 evidence_complete=true 当正常episode；失败 leaf 加独立 bounded_first_query 收据，永不作为 matching smoke/formal入口。

CPU 准备检查补上 accepted=false 不二次reset、不发infer；post-send异常不重试；第二infer在发送前阻止。保持之前完整输入/请求返回值不变、原执行/after_execute/clear顺序检查。交工具实际路径、最小diff/hash、CPU结果后由Manager核查并通知运行。没有新增训练或正式评测授权，不更改之前的两样本结论范围。

## 当前接续：准备原入口两样本验证，先完成 CPU/源代码核对

Manager 已独立验收 report 240caf91cdab0aa8fc91b198424495bf00237969 的离线数值部分：重哈希其 34 个引用文件，逐项重读两集旧 baseline H50 / shadow K30 和新 NPZ，确认新 H50 vs 旧 baseline 为 511/700 不同，历史 K30 为 299/420 不同，报告数值准确。接受“新结果不等于任一旧侧”；**不接受仅凭下一组两样本便能区分 wrapper、启动顺序等具体原因的表述**。同时改变入口/缓存/插桩后一次复现或不复现只能给有边界的证据，不能独立作因果归因。

Manager 的下一步设计：保留旧 BenchmarkRunner 启动/metadata/reset/episode prompt/首 query 路线、正常 policy server、冻结源码和 checkpoint。put-back train0 / env100000，matched baseline、matched shadow 各一次 action infer，共用剩余 2/8 的预算。**本次通知只授权任务私有工具准备及 CPU 检查，GPU 待 Manager 审阅独立工程核查后明确通知。** 不等待 reviewer 才开始准备。

与此前建议的区别：必须保存本次实际 policy 请求的完整 RGB/state/memory/prompt/请求选项、post-wire H50 响应、真实 execute K30 和 reset/命令/环境身份。优先在 scheduler 的同步 policy RPC 返回后、将结果交回原逻辑之前才复制/写盘请求和响应；请求可沿原 call 参数取得，禁止新增 get_obs/reset/infer、模型/transform/JAX wrapper 或 pre-infer host copy/fsync。Manager 已读 WebSocketClient.call：packb→同步 send/recv→unpackb，本身不修改请求；仍请核对实际 scheduler 请求/返回值的后续复用。保留正常 execute 请求后，在下一次会推进队列的 get_obs 之前 step0 clear，记录 queued=30、dropped=30、完成步数0。实际请求仅引用到 RPC 返回后取值的局限如实说明，不伪称直接截取实际 wire bytes。

沿原 robot/policy 启动及握手、reset 请求；正常 policy server 不使用前次 diagnostic_policy_server.py，不改 Policy.infer/input transforms/random.split，不追加 replay/warmup。保留原环境可确认部分并完整记录当前 JAX/WARP/CUDA/XLA/缓存配置，不新建一套 runtime/模型/通用日志框架，不人为声称旧未记录环境已相同。本次可保留新的 scheduler 小型 wrapper及第一 query 后截停；若沿原 runner 必须通过明确的 diagnostic stop / 非零 child 退出避免第二集，保留原异常语义和 failure leaf，另写诊断完成收据，不能把截停伪装为 successful smoke。

CPU/源码检查应证明：一次 infer 上限且不重试，不开始第二 episode；返回后才捕获输入/响应；execute 后 clear 不推进动作；完整请求字段留存且不修改原值。预先列明最小 hook/命令差异、停止与失败资源释放路径、新产物路径和字节上限。比较本次两臂完整输入、H50/K30，以及旧两侧和前次新捕获；未观测到的真实 PRNG key仍写 unavailable，不能拿 stream/call 当 key。无论相等与否，均不凭两次首 query 自动解除全轨迹匹配/HF formal 暂停，也不调容差。

独立核查 TASK-ID 655416db-f379-4793-878d-b2538ad26d81 正与 Manager 并行核对上述接入点；你先准备小型工具并发布准备报告，保持原 source trees只读。无需改生产源码或重新 review 整个算法。

## 当前接续：旧工程与新首query捕获的离线差异定位

已收到报告18f786b49c3461fb2b2fc766b2afa8febe234e26：新捕获6次正常action sample没有复现历史差异。Manager正在独立核验wrapper与原始数组。请与Manager并行做下面的离线定位，不增加GPU采样、reset、完整轨迹或修改生产源码，剩余2次采样暂保留。

1. 把这次新捕获的首query完整H50/queuedK30，与旧matched baseline/shadow的put-back episode0及episode1真实对应动作逐项比较，给出新结果究竟等于旧哪一侧，或两边均不同。保留float32 wire合同，列真实差值，不把哈希不一致本身当输入已不同的证据。
2. 逐项对比旧hf_engineering.py执行入口与新run_first_query_diagnostic.py：实际robot/policy环境/命令、checkpoint/metadata、reset config overrides、instruction获取与设置、相机/图像预处理、scheduler初始化与reset顺序、第一次get_obs及动作key初始化路径。用源行号和旧command/config/preflight/episode artifact指出已确认差异，特别核对本次从profile组装的reset是否遗漏旧runner的task_overrides或语言指令。不要继续笼统列“可能环境/生命周期”。
3. 若旧轨迹没有保存的字段无法回溯，明确最小不可观测缺口；给出能只用剩余两次action samples区分具体假设的最小方案供Manager裁决，但本次先不执行。不要重复八leaf长轨迹、扩日志框架或调阈值。

交紧凑离线报告与派生artifact/hash。当前已确认旧前缀数值差异不是50/30形状误差；新的控制样本相等也不自动撤销旧失败或证明所有运行确定。停止点是具体差异/最小有界验证方案，完成后正常结束turn。

## 当前任务：HF GPU成对差异的首query窄诊断，正式评测继续暂停

C3工程report `1b0006941651c958d7ece0b217034c33634a2bd0` 已发布，8个2episode leaf正常退出，但matched两任务未通过动作等价。Manager已亲自核对原始failure文件SHA `c6519c947782001a07295daf7aeed4a6a1d2295669c17ececd8acb537e2c26f4`、精确source与比较脚本，作如下裁决：

- evaluator脚本将matched baseline的50×14完整预测和shadow的30×14实际queued_actions直接比较，是审计口径错误；已交eval owner修自己的离线比较。不能仅修shape便宣称PASS。
- Manager直接重算相同前30×14：rearrange episode0/1分别284/292个数值不同，max_abs 0.0038730204/0.0038729906，RMSE0.0007002742/0.0007253131；put-back两个episode各299个不同，max_abs0.0034926604，RMSE0.0006326193。因此同一执行前缀仍确有差异，不凭形状错误撤销工程暂停，也不擅自放宽容差。
- 第一动作发生于source_step0，早于任何中途probe，不能归因于之后probe消耗RNG。当前recorded input只有robot_state/memory_input_ids，没有图像或完整语言输入。Manager又直接核对OpenPI0ce: policy_rng只有stream/call，无实际PRNG key；“计数相同”不证明采样key相同。不得称完整输入/真实随机状态已相同。

请复用本task已有源码树，先只读查配置/命令/模型/权重身份、实际import来源、Policy初始化/reset及首query观测路径，排查是否为记录口径、不同初始visual/language/transform输入、实际key、固定输入下GPU采样差异；不预设原因、不改变算法/阈值/模型/动作执行频率。原准入commit仍OpenPI0ce566bd34f99cb4775422f012ab67c16aa53885/bridgeffa122494c19e1c0154e877010f7b470967ccfc6/RMBench6abebf08d084d0be43aa56ebe158dc8395fa58e4。

可直接使用已释放的C3 GPU0做有界诊断，但先核对资源与独占端口，复用eval owner精确冻结runtime作为只读源，任务自有工具/证据写到本TASK-ID，不能在eval owner运行树改源码或共享cache。优先put-back train0 / env100000的matched baseline和shadow，各只捕获首个真实policy query的完整输入及实际action PRNG split前/采样/split后key、输入transform前后image/state/memory/prompt/token的shape/dtype/hash（必要完整数组只保留这个query、有界），以及输出完整H50/实际K30。捕获wrapper只用于工程诊断并保存source/hash/插入点，不额外split RNG或调用模型，不把新instrumentation冒充原始证据。不要再跑完整16episode对照。

然后在同一实际完整输入与同初始key/同noise下，做最小GPU重复/两条入口交叉调用，区分输入不一致与推理不一致；总正常action采样最多8次，首轮不执行新长轨迹，不做正式100、r_s30或HF效果试验。实际PRNG可在task私有诊断wrapper观测；生产wire是否需补真实key由证据与Manager随后裁决，当前不无目的扩日志框架。若用P0工具只复用测试思路，不合入另一个未完成GPU验收分支。

交紧凑报告：已确认与未确认原因、首个真正差异位置、实际来源/full input/key/action证据及hash、最小必要修复方案；需改生产代码时先交具体原因，由Manager裁决后干净提交并另审。上游算法已通过CPU的部分不机械重做。预计>30min诊断登记MAM真实PID；完成或遇确定需裁决点正常结束，不轮询。root负责解释和裁决，仍terra/max执行。

## 当前修复：Manager 对复审 27b16d899 的裁决

Manager 已直接读取冻结 bridge552ea 的 _formal_gate/_accepted_episode/_record、writer，以及 RMBenchc99 的 validate_smoke_run，确认下列遗漏。上一轮真实 recorder 接线、child identity 和单次 reset 已通过，不重做算法/RNG改动。候选基线仍 OpenPI0ce566bd34f99cb4775422f012ab67c16aa53885（保持不变）、bridge552ea78f73e62fddc747d5d26e7e6c365fa00339、RMBenchc99ec6a2c6df96ec8705b106b125935fce862052（保留 f401 祖先）。复用已有独立树。

1. 接受 formal smoke gate 缺证据校验为 P1：既有 validator 根本未消费 rolling evidence，缺文件或 evidence_complete=false 仍能被当作 matching smoke。请在现有 recorder/validator 中加入可复用的窄验证，runner 根据实际显式 rolling/matched 协议传递“需要 evidence”，不能以 record 是否恰好带 path 决定是否需要，否则缺整个字段仍绕过。逐 episode 校验引用、实际文件/可解析 JSONL、支持的 schema、header episode_id/seed、最终 episode_finished/evidence_complete 严格 true；存在 truncated、缺终态、身份错或不可解析均拒绝。默认 baseline 仍不要求 evidence，既有标准 source/manifest/video/process门禁不弱化。
2. 初始化失败的悬空引用接受为 P2 可用性问题：已有 terminal_scheduler_error/runtime_error 会判 run 失败，故此项本身并不证明失败被计成成功，但文件状态仍不诚实。采用最小明确 unavailable/missing/incomplete 状态即可，不要求为未执行推理伪造事件/重开 writer。未创建文件不能写成普通可用引用；已写部分文件保留并明确 incomplete/原始错误，原 failure reason 和 traceback 留存。不要覆盖已存在 artifact。
3. 不仅 smoke，正式100各 episode 收尾也必须使用同一证据检查规则，成功退出但日志截断不能静默标为正常完整 run。证据异常按基础设施/证据失效保留失败 leaf，不当算法失败混入成功率，不拼 partial；无须另造验收框架或将全部科学时序解释塞进通用 validator。

必要 CPU 验证：真实 recorder + child 在 writer 前直接失败、writer 后异常、正常完整和默认关闭；matching gate 接受完整并拒绝缺引用/文件、坏 JSONL、身份错、无终态、truncated、complete=false；至少一例正常 child 退出但 evidence 不完整的正式收尾拒绝。保留既有默认行为与一次 reset 检查。先完成该冻结链的窄修并提交 clean 新版本、更新简短文档/report；不要继续任意 edge-case 硬化，不修改 P0 logger、训练、阈值或源码运行树。仍 CPU only、未准入 HF GPU；作者测试不能代替独立复审和 Manager 最终裁决。完成后 publish report 并结束。

## Manager 当前增量裁决：真实 RMBench recorder 接口不匹配

新OpenPI0ce566b/bridgea0f1d50进入独立review后发现P1。Manager直接核对runner._accepted_episode和既有RMBenchResultRecorder.path_for：前者请求rolling_evidence，而真实recorder只接受episode_video/process_log，未知kind抛RuntimeError；调用又在try外，故显式HF/matched运行会在scheduler启动前失败，不能按fake recorder测试PASS准入。

Reviewer还确认真实event('episode')未保留runner传入的rolling_evidence_path。请与真实已验收RMBench recorder对齐最小路径分配及episode结果引用，测试真实recorder和runner的seam，覆盖normal/terminal/error与引用实际存在。可优先使用既有支持接口；若必须改RMBench，批准在本任务独立worktree中从已验收正式f401f5279c95451eb424ac98b831bab5552b2120做窄artifact/path/reference接线及测试，先核实commit可用性，不改共享活跃C runtime，不新建通用框架。交付所有实际修改库的精确clean commits及样例，交原reviewer增量复核，GPU仍不准入。

新增同一链路的身份遗漏已由Manager源码核对并接受：a0f1d50 child CLI只传episode_file/evidence_file，未传episode_id/env seed，writer从_reset_args取得null。请从已接受的benchmark episode身份建立明确的记录上下文，JSONL header与episode record双向一致；不能通过给scheduler新增环境reset来取得身份，benchmark已reset一次，修复后不能二次reset、消耗额外场景随机数或覆盖实际身份。

Manager已查本机缺f401对象且你当前RMBench tree基于2e9677c；同时SSH核对C的2e9677c..f401仅memory_schema_eval.yaml新增17行N/S配置，真实recorder文件不变。为避免后续部署缺配置，最终交付仍须保留f401完整基线。可以从已授权C只读源 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval-highfreq-base/RMBench` 用SSH git fetch或小bundle引入f401到本机，然后在自己的worktree保存/接续补丁到该基线上；不丢弃自己未提交修改、不改远端runtime。MAM创建记录base仍2e不影响报告写明最终实际f401→候选diff与完整HEAD，不能把旧base元数据当最终验收版本。

论文作者与代码reviewer职责不变。其余增量审查继续，不因这项已确认阻塞等待整体report才开始修；原冻结算法、RNG与36批正式合同不变。

## 目标与职责
用户已明确授权：只改推理、复用现有checkpoint，实施高频状态更新和偏差触发提前replan，并在4090集群评测。不新增训练，不改模型参数/训练代码/标签，不改变已在跑任务。你以 gpt-5.6-terra/max 负责工程实现，Manager亲自决定科学设计和验收。先读AGENTS、mam task show及各库规范；独立worktree由mam workspace add创建。

基线 OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，robot-bridge f9626636c4776d8eb15f9c556775cb2d12c000e5。RMBench如需窄入口接线，选已验收2e9677ce8ec9f623395184f63f32ddafa66e5e44及C renderer运行合同，先解析该commit可用性；不要修改共享活跃runtime。与285d审计及8968记录接口owner交流事实，但不要等待其整个任务完成或扩大耦合，独立实现本任务所需最小记录。

## 先行可执行实现
1. 加默认关闭的推理模式：baseline、仅高频状态更新且固定K、相同更新加状态偏差触发replan。动作仍H50，正常最大执行K30；monitor间隔先5个已完成policy rows，可配1/30用于控制。保持默认关闭时行为/RNG/调用次数相同。显式参数开启、失败拒绝不支持合同。
2. S现有prefix阶段直接产生当前状态：抽取可复用状态专用调用，保留同权重/transform/decoder，跳过不必要action diffusion。与原完整推理状态结果在同输入下精确对齐，不创建新head。probe不推进动作RNG。旧S lag30只是本轮推理分布变化的记录项，不以此阻塞不重训实验。
3. J逐行输出是t+j+1未来状态，T是重复t+30；不能把J row0声称为当前t、不能将T row0当当前状态。先实现可返回metadata确认target offset的只读probe接口和forecast对齐辅助：原chunk起点t0，已完成d行，新J probe row0目标t0+d+1，对齐原J row d（不是d-1）。这一路是新旧预测一致性，不是已实现独立当前状态测量。正确的状态递推/消费规则由Manager稍后补充；不要擅自将未来值写为当前状态。先推进接口、执行前缀与进度/RNG测试。
4. scheduler独立保存原计划的动作/状态forecast、monitor状态、实际完成前缀。在已完成边界取得真实新观测，默认继续原动作后缀，禁止每次probe隐式替换动作。在明确trigger后才丢弃尚未执行后缀，重新从当前观测生成动作；必须复用现有安全执行/清队列/进度机制，不能清掉别的任务或已执行动作。仿真分段发送不得改变同一原chunk的逐行控制内容和TOPP语义；给真实源码证据与基线分段等价测试。若controller一次阻塞执行整个chunk，明确最小可用分段路径和暂停仿真计时局限，不声称异步实时。
5. monitor原始结果与沿schema规则选择后的值都留痕；字段类别不相减当距离，不将J raw坐标softmax伪装成校准置信度。threshold、debounce、min-prefix由Manager冻结。T/S无同时间逐行forecast时拒绝frame-deviation trigger，不能用终点/当前值硬造轨迹；可用单独命名的已识别状态变化trigger，待Manager明确后实现。

## 验证与交付
先用CPU/模拟controller验证：关闭等价；固定K开monitor但不更新时相同动作流和动作RNG；多次probe不覆盖执行队列；early trigger实际只执行前缀、取消后缀且新chunk正确接续；terminal/停止/不足K/重复或过期观测/执行失败和episode reset；index0/29/边界错位；不支持T和无状态checkpoint明确失败。状态路径对齐检查需真实model函数结构测试，必要小模型参数CPU，不只mockserializer。

记录每次动作/probe调用类型、实际row/target时刻、输入状态、raw/decoded输出、原forecast、偏差与trigger原因、K实际执行/丢弃、动作及状态RNG身份、观测与计算时长；输出有界，逐run配置/commit/checkpoint哈希留痕。短smoke模板与正式评测交给独立owner，在独立review通过前不自己部署C或跑正式。尽快先发关键接口可行性/准确偏移结论，继续代码实现；完成commit并发布report。任何>30分钟程序按MAM登记，不高频轮询。

## Manager冻结首轮算法合同（本节覆盖先前待定项）

**只改推理，新增训练数0。** 支持现有新20k Memory-v1 categorical J（各字段target query+1+row）与S（query+0）。T的phase为query+30，首轮只保留原baseline，不进入rolling或frame-deviation模式；不能按输出shape或名称猜支持性，要核实canonical target refs。unsupported混合target需在启动前解释错误。

**执行路径**：仿真优先一次提交原K actions到既有队列；get_obs使用remaining=K-d逐次_drain_to，只让真实完成d增长；保留原后缀，trigger明确clear剩余后再新推理。终止时不probe/不replan。server不解释task语义，scheduler决定更新和触发，controller保持现有逐row执行。新功能仅simulation，不把真机插值路径一并改造。逐episode独立重置monitor、计数、RNG、forecast。检查任务get_obs副作用/全局RNG，shadow对照不等价时先修必要读观测副作用或报告，不能算算法收益。

**J高频rolling**：动作边界a生成原计划A_a,Z_a；monitor forecast初始等于Z_a，source a。每次实际完成到u时，先从最近monitor forecast的row(u-source-1)读取target恰为u的各字段，按原schema编码/保留规则形成新query输入m_u；不消费未来行。r_s=5，probe在u=a+5,10,15,20,25（非terminal）读取新观测，用当前m_u及独立probe RNG完整joint采样，动作丢弃，新forecast保存source=u。在原K边界u=a+30不多做一个probe，按最近forecast对应target=u的row取m_u，进入正常动作infer。例probe@a+25的row4输入a+30。r_s=30退化为原K30反馈，r_s=1仅工程/吞吐可配置。新probe forecast联合生成但未采用的动作不等于实际已执行动作，记录其为“刷新预测与递推的部署变体”，不能宣称独立当前状态测量或预测被实际接触确认。

**J事件触发**：始终比较当前动作计划最初Z_a与新probe Z_u，不能偷偷把参照换成上一次probe。d=u-a；phase字段的old rows[d:d+3]与new rows[0:3]对应相同绝对target u+1..u+3。先对每行按实际categorical argmax/原decoder后的IDs作不等指示，D=3行平均；D>=2/3为本次偏差大。连续2个有效probe均偏差大，且d>=10且d<Kmax30才trigger；任何一致probe清连续计数，重复/过期观测不增加，无法对齐/越界/缺phase/非法ID不能触发并明确报错。unknown也是模型合法预测类别，首轮不通过忽略unknown压低误报。不使用phase编号差、不用未经校准softmax置信度、阈值不按新成功率调。
trigger时当前m_u已按上一forecast对齐到u，新probe仍只用于偏差；clear仅尚未执行的队列，记录丢弃数量；用同一最新观测和m_u经**正常action RNG**重规划，不能直接取probe生成的actions。新动作计划成为后续比较参照，计数清0，重新至少执行10行。非trigger继续原actions，新probe保存作rolling forecast。默认max K30保留，无“正常phase变化就必重规划”的隐式条件。

**S固定K高频**：动作边界调用原完整infer，它已经预测当前状态并条件化动作，存为monitor状态；执行中每5行只做prefix state probe，输入上一monitor状态并保存新selected，原动作queue不变。下一action边界仅做一次完整infer（不可probe后又在同帧递推一次），输入最近probe状态。S训练lag30→部署较短lag如实记为推理协议改变，不重训。chunk级current output也可后续用稳定phase-change触发，但首轮不实现/不把它叫forecast-deviation。

**首轮模式和工程门槛**：J baseline K30；J shadow(r_s5、不改cache/动作)作工程等价；J HF-fixed(r_s5,K30)；J HF-event(r_s5,Kmax30,window3,threshold2/3,consecutive2,minprefix10)；S baseline/HF-fixed。另支持J HF-periodic K10/r_s5作为后置频繁重规划控制，显式runtime max-K覆盖留痕，stored metadata不改。K10不是事件臂平均调用数的严格匹配对照，不做该声称。正式先rearrange/put-back train0同现有checkpoint；其他9task扩展待对应checkpoint和target合同验收。

每个probe有单独可重现RNG流，动作RNG只由动作infer消费。shadow多probe后同动作输入/RNG须输出一致；J采样导致的预测波动通过固定随机流/窗口/连续判据记录，不能由触发次数声称物理异常次数。需要测试固定观测/输入的重复probe波动，报告但不据此调整正式阈值。

## Manager接受独立合同审查后的补充
Reviewer4006确认时间公式正确，并指出必须验证的P1：标准MemoryContext pending chunk不能在a+30把旧Z_a row29覆盖rolling新值，early clear后也不能用下一chunk的completed把已取消的旧pending“补完成”。HF-J须隔离标准pending反馈或在同一明确生命周期内正确结清/废弃，原动作plan id/source/actual prefix及丢弃后缀显式关联。probe不是被执行chunk，不能伪造accept或完成证据；默认路径维持原Context行为。

任何invalid/stale/duplicate/gap观测都打断偏差连续计数；旧/重复u必须在probe前短路，不消耗probe RNG、不替换forecast。非terminal出现非预期进度跳跃、超过计划K或target越界，明确失败该诊断执行，不跨缺口累积“连续”。测试高@5/invalid@10/高@15不触发、clear后新plan进度不结清旧pending、完整K边界不回写旧forecast。

评测owner核实正式门禁固定eval_seed0/1/2→100000/200000/300000，且逐臂matching smoke source/manifest严格相等。撤销900000工程seed要求，不为此增加新CLI：baseline/shadow成对工程smoke沿既有eval0 seeds100000/100001，独立run目录/工程标签，不据分数调已冻结阈值；正式每配置/每eval seed仍自身matching smoke2→formal100。工程shadow不得冒充HF-fixed/event的matching smoke。派生新配置明确random_light=false、crazy_random_light_rate=0并留痕；若原baseline未满足，不能无声改变环境后沿用旧结果，需报告并统一新对照。

## Manager 初验 P1：默认关闭的跨 episode 动作 RNG 改变

4529a91/53f853a 已交付并进入独立 review4006。Manager 用真实旧/新 Policy 类（仅以固定 CPU 模型替代采样器、保留实际 transform/split/output 调用链）亲自复现：infer→reset→infer，首个动作一致，第二个动作不一致，新版重复了第一次动作。旧 action RNG 两次推理后的 key_data 为 [4165894930,804218099]，新版重置后为 [1797259609,2579123966]。同时直接核对旧 OpenPiBackend.reset 为 no-op，新版无条件调用 Policy.reset；真实 SchedulerBase 初始及 ep_init 都发送 reset，所以此差异会进入默认 baseline。

此问题接受为 P1，当前不准入 GPU。请窄修确保未显式启用高频协议的请求保持原 action RNG 生命周期、响应字段和诊断开销；当前 infer 对所有 J 无条件复制 memory_raw_actions、对所有 JAX 返回 policy_rng 也应移到明确开启的审计/高频请求路径。不能只以新baseline对新shadow便证明旧默认行为不变。

原冻结合同中的高频逐episode reset 应作为明确启用的高频实验协议，不能改写公共 baseline。请提供最小显式接线方案并与 reviewer 对齐：默认模式维持旧行为；高频的 action/probe episode reset 与留痕仅影响明确开启的请求/会话；shadow 对照必须与用于比较的baseline采用相同动作RNG生命周期。若高频协议与历史baseline在此不等价，应向Manager明确列出需要重评的matched baseline，不能静默复用旧成功率或据此调阈值。新训练仍为0；是否补matched baseline由Manager根据证据决定。

作者可先修此已确认问题并提交新的干净commit；reviewer继续冻结版本的其他检查，最终只对新精确commits给准入结论。保留infer→reset→infer默认关闭、显式开启、probe不影响action流和baseline/shadow跨episode比较的有意义回归。

## Manager 正式 RNG 对照裁决

Manager 已直接核对 BenchmarkRunner：policy server 在整个100集 run外创建，只有scheduler按episode重建；历史action key在同一run内连续消费。create_trained_policy未传rng，初始值为jax.random.key(0)。因此显式HF逐episode回到initial key与历史baseline确实不同，不只是无影响的reset接口变动。

保留HF逐episode reset合同，新增同协议matched baseline，不直接拿历史baseline作为HF效应的分母。请以最小显式配置把已有reset_episode_rng RPC接到baseline与shadow；普通baseline和普通shadow仍默认历史no-op，不能默默改变默认。无需新建第二套baseline执行算法，也不改变原MemoryContext/K30反馈或额外插入状态更新。显式matched baseline无中途probe；matched shadow有probe但不更新cache/动作，与matched baseline同一action key生命周期。必要审计字段仍显式开启，普通infer输出/开销保持原合同。

所有本轮HF、matched baseline、matched shadow：action初始key0，每episode恢复同一初始key；probe流fold_in(initial,0x50524F42)，每episode恢复且独立于action。这不是3个policy sampling seeds，eval seed0/1/2仍是三个环境列表。matched baseline/shadow在多episode中必须保持相同action采样key和实际执行动作；HF-event的额外正常infer允许改变该episode内后续action query消耗，不能宣称所有臂每物理时刻使用同一噪声。

额外matched baseline由Manager批准：J两任务×3eval=6批先与核心J12批一起开展；S两任务×3eval=6批随后与S HF-fixed6批开展。原24部署批次加12对照=36批/3600正式执行，新增训练仍0；工程smoke另记，阈值/任务/频率均不变。旧结果保持有效且留在九任务原协议证据中，不与新reset协议跨批拼成300。实际配置名、默认值、RNG身份及两种baseline用途写入作者交付说明，精确commit交独立review后才可GPU准入。

## Manager 接受 review P1-2：rolling 证据必须随 episode 留存

独立冻结报告b55c30e指出rolling trace只有scheduler的64条deque/get_status。Manager已亲自核对53f853a：_rolling_start_plan/_rolling_probe/_rolling_trigger_replan更新内存而不输出rolling日志；benchmark._wait等scheduler退出后仅读robot get_obs诊断，_record不收scheduler状态。因此成功率即使可保存，关键raw/decoded、RNG、consumption和trigger/clear证据会随进程丢失，接受为GPU准入P1。

请在本任务内窄修持久化，优先沿现有每episode scheduler日志或已登记result路径输出有版本的结构化记录，不创建通用记录框架、不等待独立P0 logger。记录须能离线关联episode/plan/query、输入/forecast target、原始和解码状态、实际采样key、执行动作及已完成/丢弃前缀、probe、边界与terminal/异常原因。可增量事件或阶段快照，避免每次全量复制历史；不传输额外RGB或巨量旁路数据。普通默认路径保持原开销。

不能只在get_status或正常退出时输出最后64条：700行/K10可能超过64个plan，且错误退出也要保留已完成证据。日志容量应明确、有界、超限标记incomplete，不得静默截断后通过正式验收。新增有意义验证：episode子进程退出后实际文件可解析、trigger旧计划丢弃和新计划接续完整、终态最后已执行前缀、异常/截断明确，默认关闭无新增输出。作者交付样例文件/解析命令/最小schema，由reviewer独立复核。若某个指标仍无可复核来源如实列出，不能只凭内存状态称已满足留痕。

Source report:

# 交付报告

## 最新修订（2026-09-14；同实例 probe 副作用检查仍仅 CPU 准备）

已修复 Manager 复核指出的两处 CPU 控制缺口；**没有**以 `--execute` 运行检查，没有构造真实 `OpenPiBackend`、加载 checkpoint/model/GPU、发送 sampler request、环境 reset、仿真轨迹或 formal。历史正常 action 诊断预算仍为 **8/8**，本节未改变其记账或结论。

- 工具现在在每个 action/probe 调用前只保存实际 JAX key 的不可变对象引用与 Python sequence；对应 backend 调用正常或异常返回后，先保存完整输出，再物化调用前/后的 key 数据。它不在 reset 与第一个 action/probe 之间读取 key 数组。P reset 到 probe 1 前只比较 key 对象身份和序号；probe 1 返回后立即物化并严格比较 P reset 与 C0/C1 的实际 action/probe/initial key 内容，任何失败均在下一个 probe/action 前停止。
- `run()` 的 protected finalization 会在内存中先捕获 `policy_state_before_restore`，然后独立尝试恢复 policy 状态；只有 `run()` 返回后，外层才序列化并写磁盘 receipt。因此 `policy_state_before_restore` 表示恢复前的内存状态，不能表述为“收据写入后恢复”。post-call key 物化、finalization、restore 和 artifact serialization 的次要错误分开记录，绝不覆盖已存在的首因、调用账本或已完成 artifact。
- `execute()` 保留已构造 checker 的 calls、budget、record 和 artifacts；即使末次 key 物化或清理失败，也不会回退成新的 `0 action + 0 probe` precheck receipt。artifact writer 会独立尝试每一个已完成 pickle，并把单个写入失败写入 `serialization_errors`；若此前没有首因，该序列化失败成为 receipt 的首因，已有首因绝不被替换。
- CPU seam tests 现为 `11 passed`：原有控制/预算/输入隔离/plan tests 之外，新增了拒绝 sampler 返回前任何 key 读取且验证旧 key 引用不会被后续 reassignment 覆盖的时序 seam；通过注入 checker factory 的 `execute()` 末次 key 物化失败 seam，验证最终 receipt 仍为 `3 action + 5 probe` 且 C0/C1/P/五个 probe outputs 保留；以及单个 pickle 失败后继续写其他 artifact 的 seam。Ruff 与 Python compile 通过。
- [检查说明](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/README.md)、[源码审计](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/source_audit.md)、[工具](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/tools/probe_side_effect_check.py) 和 [CPU tests](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/tools/test_probe_side_effect_check.py) 已同步到 C3 task-private 根 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check`。工具、tests、说明、审计 SHA-256 分别为 `6edd0ba2ce04c6ba70c9efa239cd5f603e9097ad7079f10dce013a660850491c`、`fb1d7a84cc9ae6b88a36fa9521bc676abad5c0d75d45c44dee314fda31db6e8b`、`7ae2d57856fb0db3302a530cde8cd9c3d8cd00a65fd4beb26c450b6b0c1933c8`、`b879680aedb7655e1299079f15d4e80173ecf8fcf7422de643e29f78d85c3abc`，本机与 C3 一致。旧 `plan_20260914_v2/plan.json` 和中间 `v3` 均保留；新 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/plan_20260914_v4/plan.json` 已在默认模式写入，SHA-256 `4408a8732f3fa259f5224de6dfe7c40add97e40e5a7fc511a076f8f4fb5a9916`。其 `mode=plan` 明确记录未构造 backend/model/GPU/server/environment reset 或 sampler，并确认冻结 OpenPI / bridge / RMBench 为 `0ce566bd` / `ffa12249` / `6abebf08` 且 clean。

源码审计结论仍是可实施性而非实验结果：`Policy.probe_forecast` 使用独立 `_probe_rng`，而 `infer_audited` 消耗 `_rng`；backend 对两者均是直接转发，显式 `reset_episode_rng` 初始化/复位 rolling state。现有 WebSocket RPC 不暴露或设置实际 key，因此单独 RPC 无法做该精确对照，必须使用本工具的同进程 backend helper。controller 方面只证实 worker deque 将同一输入 action rows 按顺序逐项传给 `env.take_action`；`get_obs` 仍会 render/camera，环境 `take_action` 有 TOPP/physics/可能 light RNG，故不声称 30-row 与分次 5-row drain 的完整环境推进等价。

本节交付后等待 Manager 验收和未来明确 GPU 授权；不能据 CPU seam pass、plan 或源码审计把 probe 副作用检查写成 PASS，更不能解冻 HF/matching/formal。

## 最新状态（2026-09-14；覆盖下方历史样本预算）

已完成 Manager 授权的 `put_back_block` / train seed 0 / env seed `100000` 修正来源路径 matched shadow：它只发出 **1** 次正常 action request，并以预期的诊断截停 `exit 70` 结束。收据确认唯一 accepted reset 为 episode 0 / seed `100000`，恰有一次 `infer_audited` 与一次 execute；原 iteration 后 clear，非 drain status 为 `queued=30`、`dropped=30`、`logical_step=0`。没有第二 query、episode、replay、warmup 或 probe。

旧 shadow 失败原件仍保持不变（`64ee0c7c9f4e4d77a99e20af55ed830bc06b42455cbe820ca34e98ceb0a89d21`）：它因 `MemoryCheckpoint` source root 缺少 `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` 层而在 service/reset/action 前停止，未消耗 sample。修正版只改用正确 source root、全新 result/capture 路径和 run 名；没有修改冻结工具或三库源码。

- 正常 action sample 总预算现为 **8/8**，剩余 **0**。不得 retry、重跑 baseline，或启动 matching/formal smoke、完整轨迹或 formal 评测；formal 仍冻结。
- 两臂完整实际 policy-request leaf fields 完全相同：`$.cmd`、`$.images.cam_high`、`$.images.cam_left_wrist`、`$.images.cam_right_wrist`、`$.memory_input_ids`、`$.prompt`、`$.state`。`policy_call_kwargs`、正常 policy/robot commands、runner environment、policy metadata、checkpoint verification 与 metadata verification 也相同。
- 每臂自身 H50 `float32[50,14]` 的前 30 行均精确等于实际 K30 `float32[30,14]`。跨臂仍有数值差异：H50 为 `532/700` 个元素不同，max abs `0.0036021433770656586`、RMSE `0.0006788336719106482`；K30 为 `314/420` 个元素不同，max abs `0.002218961715698242`、RMSE `0.0006341486370427415`；首差均在 `[0,1]`（baseline `0.0005527432076632977`，shadow `-0.001193587202578783`）。
- 版本化配对分析同时归一化共享 result root 与冻结运行树 result root。归一化后 preflight/episode context 仅余六个 `task_facts.final_block_pose` 标量差异；它们不在捕获到的实际 policy request 中。既有源码证据表明该 task-fact probe 不是有效的首 query 输入身份，因此这些值不能被当作实际输入不一致的证明。
- 没有可直接捕获的模型侧实际 PRNG key；响应中的 `policy_rng` 只是 stream/call 元数据，未据此推断 key。

本对照仅是有界诊断，不是 matching smoke 或 formal 证据；一组首 query 的相同或不同都不解冻正式评测，也不建立历史差异的因果解释。

证据根为 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914`。关键完整性哈希如下：

- 修正 launcher `launch_shadow_fixed_source_root.sh`：`171d33f1068074bbcb5551da27263adb1315ae223f51aed2765a9884cd6af6e6`；三处最小 diff：`plans/matched_shadow_fixed_source_root.launcher.diff`，`e4f8faeb5359162b8171217e952d308161c57cba251e9a8ce7926180957f5071`；repair record：`dd337fdab6022ec196c64ff6831f15ccf5b7b37ad07506e0dde16f81bcd0da31`。
- plan `67788b1eabfdd70af3464dc93443e8375c974eea3b1d62d8c6197f2436159666`；preflight tool `c8be70cb403df3951038c0c42861b9aaa58aba872d20ae1d465ceee7810fe412`，preflight result `4adefcb45e34d41f2ed49878978f5a743fe0fe0d82cf1a4f501ec1cde2be3d69`。
- 修正 shadow runner receipt `a31cb6e3810fdf39b8a85c047d4579d6ca66b036c9c237a949dee9a47586a6e5`；episode receipt `474ac041805e6c68a7405cf957320243535846eeeb1344ff32fa313be880b752`；v2 validation `a1625cd5048bbc9be1a2569a490ce116932258bc174ea93355c48af686c92ac6`。
- v2 analyzer `tools/analyze_fixed_shadow_pair_v2.py`：`fb62a01b35c460b18bd9357dae9a96ae55b53ce46b8b83ad2357ea75cdc52d4b`；analysis JSON `be1382272b3cbae2454b17e3bcedaf2656c6693da88fffdfccbde3bf6473c5c7`；Markdown `14d0e508b787019dcbcd4e05519ac223a6117b3fac1e1b7f9868ce666cdb5cfa`。用临时输出重跑后，三份 v2 输出逐字节 hash 均一致。


## 历史：原入口首 query 准备（当时仅 CPU，尚未执行）

已在任务私有目录准备保持原 `BenchmarkRunner` 启动、metadata、reset/preflight 和首 query 路线的有界诊断入口：[runner](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/original_entry_first_query_runner.py)（SHA-256 `376dd1fd087a5e79a9cbda4e83d1ff5b8534dc9c59429a60acbdf8ed2a0abf34`）仅替换其生成的 scheduler child；[scheduler](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/original_entry_first_query_scheduler.py)（`0561e295e644bee882c7abaee9d08e856b9e5ad00aeafbb4ed480ad7f3179ae2`）在首个同步 RPC 返回后才于 RAM 深拷贝完整 request/response，并在原 `run_iteration()`、`after_execute`、clear 和无 drain status 后写入收据。完整行为、边界和 8 MiB 单数组上限见[说明](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/original_entry_first_query.md)（`c11656f94b8d2ef043964465d8ecca9a0d83575fc7ff25bf1c5e3499f2d9d6db`）。

[CPU seam tests](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/test_original_entry_first_query.py)（`3f9653c70525febdf2b7167696539cc9e3c535f728974bef214dd48bdf756a5c`）当前复跑为 `11 passed`，并通过 Python 编译；覆盖一次 infer 上限、post-send ambiguity 不重试、预检拒绝不进入 seed `100001`、execute 后 clear/status 顺序和诊断 child 的 episode-0 failure leaf。默认 launcher 只打印计划，未执行 `--execute`，因此本次准备没有启动 GPU、正常 policy server、真实 reset、replay、warmup 或完整轨迹，也没有消耗剩余 action samples。

该捕获是 `WebSocketClient.call()` 返回后的对象观察，不能称作原始 wire bytes；真实 PRNG key 仍不可得。任何诊断 receipt 都是独立失败/有界收据，不能用作 matching smoke 或 formal 成功证据；当前正式评测仍暂停，生产源码树保持只读。

## 当前增量修复

已按 Manager 对复审 `27b16d899cf0220986a7531ad04989b227270f61` 的裁决，完成 rolling evidence 的 formal 准入链窄修；未改算法、默认 baseline、OpenPI、P0 logger、训练或运行中的 C 环境。

- RMBench 增加单一 `check_rolling_evidence()`：仅当 bridge 从已解析的显式 rolling/matched 配置传入 `rolling_evidence_required: true` 时，逐 episode 校验 artifact 文件、JSONL、schema v1、header `episode_id`/`seed`、最终 `episode_finished`、`evidence_complete: true` 以及无 `truncated`。
- `validate_smoke_run()` 复用该检查。缺引用、缺文件、坏 JSONL、身份错、无终态、`truncated` 或 `complete=false` 均拒绝 matching smoke；普通 baseline 不要求 evidence。
- bridge 将这一“是否需要”的配置事实传给 formal gate，并在每个显式协议 episode 收尾调用同一检查。正常 child 退出但 artifact 缺终态或不完整时，episode 记为 evidence/infrastructure failure，正式 run 不会把它当作正常完整结果或拼接 partial。
- 未创建文件时 episode record 不再留下普通 `rolling_evidence_path`；以 `rolling_evidence.state: missing` 或 `unavailable` 保存。已写部分文件保留其路径并标记 `incomplete`/`invalid`；已有 scheduler failure reason 与 error message 原样保留。
- 更新 [rolling evidence 文档](/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge/docs/reference/rolling-evidence.md)，说明 matching smoke/formal 的同一完整性合同。

上一轮已修复的真实 recorder path/reference、child header identity 和单次 benchmark reset 仍保留：`RMBenchResultRecorder` 按 episode 分配 `rolling_evidence/episodeN.jsonl`，显式 child 只接收审计 identity，不会据此发起第二次环境 reset。

## 验证

- RMBench recorder/validator CPU 回归：
  `.venv/bin/python -m unittest discover -s tests -p 'test_eval_diagnostics.py' -v`
  → `5 passed`（既有 SAPIEN/Vulkan 资源警告，无测试失败）。
  - 使用实际 recorder 留存 normal、terminal、scheduler error 的 evidence 状态。
  - matching gate 接受完整 artifact，拒绝缺引用、缺文件、坏 JSONL、身份错、无终态、truncated 和 `evidence_complete=false`。
- bridge lifecycle CPU 回归：
  `PYTHONPATH=/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi/packages/openpi-client/src .venv/bin/pytest tests/benchmark/test_stage3.py tests/benchmark/test_runner.py -q`
  → `26 passed`。
  - 真实 RMBench recorder + child 覆盖 writer 前直接失败、writer 后异常、正常完整、default 无 evidence；保留每 smoke episode 一次 reset。
  - formal-mode CPU fixture 覆盖 child 正常退出但 evidence 无最终记录时，runner 以 `accepted_infrastructure_failure` 拒绝并把 episode 写为 Fail。
- bridge 全量 CPU 回归：同一 `PYTHONPATH` 下 `.venv/bin/pytest -q` → `524 passed, 2 skipped`。
- bridge 变更文件通过 Ruff、Python 编译与 `git diff --check`；RMBench 变更文件通过 Python 编译与 `git diff --check`。

## 精确提交与基线

- OpenPI（本轮未改）：`0ce566bd34f99cb4775422f012ab67c16aa53885`
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/openpi`
- robot-bridge：上一候选 `552ea78f73e62fddc747d5d26e7e6c365fa00339` 之上的当前候选
  `ffa122494c19e1c0154e877010f7b470967ccfc6` (`fix: enforce rolling evidence at benchmark close`)
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/robot-bridge`
- RMBench：正式 `f401f5279c95451eb424ac98b831bab5552b2120`，上一候选 `c99ec6a2c6df96ec8705b106b125935fce862052` 之上的当前候选
  `6abebf08d084d0be43aa56ebe158dc8395fa58e4`（`验证 rolling evidence 的 smoke 完整性`）
  - `/mnt/public/xcj/Projects/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/RMBench`
  - 已核对 `2e9677c..f401f52` 仅是 `memory_schema_eval.yaml` 的 17 行 N/S 配置新增，当前 candidate 保留完整 f401 祖先。

三个 worktree 均 clean；没有登记中的本任务 job。

## 首 query 有界诊断（C3 GPU0）

本轮仅诊断 `put_back_block`、train seed 0、环境 seed `100000` 的 matched baseline/shadow 首个真实 policy query；冻结运行树只读，未改生产源码、checkpoint、共享 cache、阈值或算法。冻结根为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 分别为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`；checkpoint 为 `pi05_rmbench_put_back_block_full_t_plus_1/.../20000`。实际导入的 `openpi/policies/policy.py`、OpenPi backend 和 simulation scheduler SHA-256 分别为 `1c4636db0e5fb97a8e5a4332de047d79d9ad5c63ea6880179d7606b41fa65563`、`a49f45fe5923723afc8982be2ff88d8b483c8bd6aba225838d4c92c7cad7ce5c`、`c6f9eeb9442153f5231b5a1be268ad1f1f04dfe83626caddf68b517839c0ca5b`。

- 真实入口分别为 `matched_baseline._call_policy_infer` 和 `shadow._call_rolling_action_infer`。两者的 scheduler pre-RPC 完整输入树（3 张 RGB、state、memory IDs、prompt）相同，SHA-256 为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`；Policy transform 后树为 `df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`。
- 实际 action RNG 完全一致：split 前 `[0, 0]`，采样 key `[928981903, 3453687069]`，split 后 `[1797259609, 2579123966]`。`implicit_noise_derived_from_sampling_key`、raw model H50、post-transform H50、实际 queued K30 的树哈希依次为 `127e5ee9a8777cfb6f05401c832f45f422efffe52a27bbf0b7b77396e9619c80`、`035baf5219a0e838d404ab4ca56a82063fc64cf7dfd79a508e5317e77268f90d`、`baa84c42691b0aa0e87d0fdb55f4a7c96897ac2a8e19dd45004bcd5e8fb9a096`、`cdcbecf0e6339267b95eccd58529ab6f076adf845d86410f7021661dd6a8e491`，baseline/shadow 均相等。前者是用捕获到的真实 sampling key 按冻结 `jax.random.normal` 表达式离线重建，不是 GPU sampler 内部 noise 的直接捕获。
- 每侧一次真实 action query 加两次同输入/同 key replay，共消耗 `6 / 8` 个正常 action samples。以冻结 backend 的 wire cast `np.asarray(actions, dtype=np.float32)` 比较后，所有 H50 replay、跨入口 replay 和 H50 前 30 行对实际 K30 都为逐元素相等；两个队列均在逻辑步 0 立即清除 `30` 行，未执行轨迹动作。两个保留的失败目录均发生在 query 前，未计入样本。
- Policy transform 的原始 action 是 float64，而 frozen OpenPI backend 在线路上转为 float32；直接比较 pre-cast 值仅有该转换舍入（最大绝对差约 `5.93e-08`），不是推理差异。

结论：这一受控的新首 query 样本没有发现输入、transform、捕获到的真实 PRNG key、离线重建 noise、模型输出、队列或固定输入/key GPU replay 的分歧，因此不支持把历史不一致简单归因为 policy sampling 非确定性。它不撤销既有历史动作前 30×14 不一致审计（离线 queued-action 审计工具 SHA `1be44b9bd3cd02235833707e40022d0690361efae60b131dcbeb287daeb02151`，重算 SHA `bc30cf2ee8bfe7130cc68c1f8eff2862928e5baee1564b6841ffb29d0187d1fb`）：新捕获只说明该次重建的首 query 未复现差异。诊断 wrapper 在 transform 周围做同步 host copy/`fsync`，并暂时 monkey-patch 全局 `jax.random.split`；它保持预期的随机调用语义，但改变了 timing/JIT 条件，所以新样本相等也不能排除未插桩运行时的 timing/numerical effect。仍未确认的条件包括先前 run 的初始环境/完整输入状态或其他生命周期差异；现有证据不支持生产修复或解除正式评测暂停。

证据位于 C3 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic`：[`analysis.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.md) 与 [`analysis.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/analysis/analysis.json)，后者 SHA-256 为 `c14af95aac92df5cefbfd3958de0100f1efef780d28a7031e8f59435a4500db1`。诊断分析器 SHA-256 为 `71952d10f8050689fe57143448ad5162e12c0edc9a015d68a1006db9d9f02912`；调度 wrapper 记录了上述插入点，SHA-256 为 `318ac87ca3f7b963aff059a101f6c78cfa860735b28b04450b9beaf005050c4f`。

## 离线历史首 query 对齐

未增加 GPU 采样、reset、replay、完整轨迹或生产源码改动。任务私有离线读取器 [`align_historical_first_query.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/tools/align_historical_first_query.py) 以冻结 wire 合同 `np.asarray(actions, dtype=np.float32)`（`openpi.py:349-356`）读取旧 put-back matched artifacts 和新有界 capture；读取器 SHA-256 `94b3a1cbc209b0b1c58f670a74b0a61f4c2a9940a1f2a4fef7c88530dc7b5d58`。结果为 [`historical_alignment.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.json)（`4de3f6edc1af02fec61015439393f5d287da70bea0dd55732a0bf91c35ca2b1b`）和 [`historical_alignment.md`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/first_query_diagnostic/alignment/historical_alignment.md)（`ffa48e8682d927b544b56664a117861afef1607dd9a0697e425b4394d5231bd6`）。

- 新 H50 的 wire SHA 为 `adf97a1dadeee7df55ab60d7bfe54f9d141cffd7b15c13dd114a222306a2d68a`，K30 为 `f0dcb3163e0723c363e9477faa873a499baba78e4bbba7a2ef7188724ac25fa4`。旧 baseline 的两集 H50 完全相同（SHA `4c69052f6e46e601de388993f3cb1ddc108617e8ded37230cdb758f21b854431`）；旧 shadow 只留第一 `action_plan.queued_actions` K30、两集也相同（SHA `0799a79aea6a7d860b7859f2a7ce988d1b3229f3b6ac2e6b0389cbbc4d405a40`），没有可回溯的 shadow H50 tail。
- 新 H50 对旧 baseline H50 有 `511/700` 个 float32 元素不同，max abs `0.0034926608204841614`、RMSE `0.0006454789071132261`，首差 `[0,0]` 为新 `-1.459865779906977e-05`、旧 `0.00032710886443965137`。新 K30 对旧 baseline H50 前缀为 `296/420`、max `0.0027747450512833893`、RMSE `0.0005912740981828194`；对旧 shadow K30 为 `301/420`、max `0.003492661053314805`、RMSE `0.000688904451176663`。历史 baseline 前缀对 shadow K30 仍为 `299/420` 个不同。新 K30 的 164 个元素同时不同于两边，其余类别也不组成任一旧数组，因此新 capture 精确等于旧 baseline 和旧 shadow 的结论均为 false。
- reset request 仅去掉 run-specific `video.output_path` 后完全相同（canonical SHA `789feb2835dae80d4415c21141594e8b913153374f2a8df9b0b714d160c1679d`）：`task_overrides={}`、`instruction_type=unseen`、`test_num=100`。instruction 精确相同（SHA `8537a6997ea8ad918e3237b6642490ded7c9204d9bd78075b1d6a88ec46f81bf`）；去掉 `eval_video_save_dir` 后 preflight task args 和相机配置也相同。旧/新保存的 `memory_input_ids=[0,0]`、state 均相同（int32/float32 raw SHA 分别为 `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc`、`aed9607efe0f26286bd388129c3f8720abc4de43b417ae34e0a12dfec2d25747`）。
- 这只证明配置与已留存字段相同：旧 rolling evidence 首 query 输入只有 state/memory，未保存 RGB、完整 prompt/token/transform tree、实际 PRNG key、sampler-internal noise；旧 shadow 也未保存 H50 tail。新 baseline/shadow 的 scheduler pre-RPC tree（含 3 张 RGB）和 post-transform tree 分别同为 `4627c2bafafc3367081dd2b9e5536ad951b8c948a1cbbea7254565473bb6d288`、`df25383745457905f7a9ca23299cb00c3bf61ee922ca83e3b6c82abfde52baf0`，但这不能倒推旧全输入或旧真实随机状态相同。`episode_info.info.task_facts.final_block_pose` 也不能当作首 query 输入身份：`rmbench_sim_worker.py:135-149` 的 probe env 会 `play_once()`，`put_back_block.py:106-140` 随后记录该 pose，而 worker 在 `:155-179` 重建实际 episode env 后仍返回前者。
- 已确认入口差异：旧 `BenchmarkRunner.run` 在 metadata handshake 前连续启动 robot/policy（`runner.py:750-771`）；新 launcher 先启动并握手 robot，后启动 policy（`run_first_query_diagnostic.py:355-379`）。旧流程是正常 `run_policy_server.py`/`scripts/run_scheduler.py`，新流程是 task-private policy/scheduler wrapper，并新增 JAX/WARP/CUDA cache 路径（旧 receipt 未保存其值）。新 scheduler 仍加载相同 config、调用冻结 `apply_episode_prompt`，再 `_startup(); run_iteration()`；这与 `SchedulerBase.run()` 的名义首 action route（`base.py:614-648`）在构造后相同，但不能抹去 wrapper 或启动顺序差异。
- 建议但未执行的最后两样本方案：baseline、shadow 各一次，保留旧 `BenchmarkRunner` 的启动顺序与 reset flow；只在真实 execute request 之后的 scheduler 侧采集 post-wire K30，并在 logical step 0 clear queue。不得包装 `Policy.infer`、transform 或 `jax.random.split`。这样可区分差异是否由本次 diagnostic wrapper/startup path 引入；若未获授权额外观测，仍不能回建旧 RGB/实际 key。

## 原入口有界首 query 执行（C3 GPU0，2026-09-14）

Manager 授权的后续执行只使用了 matched baseline 的 **1** 次真实 action request；matched shadow 在来源校验阶段停止，使用 **0** 次。冻结运行树为 `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914`，三库 clean HEAD 为 OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。结果 leaf 为 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910_hf_engineering/c_hf_j_matched_baseline_original_entry_first_query_env100000`；MAM job `ff3b2531-1b01-4685-b5d8-f23037d63253` 已归档。外层 exit `70` 是预期的诊断截停，保留了 episode-0 failure leaf，不能视为 benchmark 成功。

baseline 的实际 policy 身份不是仅由外层环境变量推断。结果 `config.yaml:750` 记录了 policy `get_metadata.policy_dir` 为 `/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000`；冻结 `BenchmarkRunner` 将 policy `get_metadata` RPC 返回值保存为 `run_context["policy_metadata"]`，拒绝与 manifest-resolved checkpoint 不同的 `policy_dir`，再写入 result config。该 config 的 `metadata_verification.actual_path`（行 442）和 `checkpoint_verification.actual_path`（行 535）分别解析到该目录的 metadata 与 checkpoint，校验 digest 分别为 `3b5d9b56a6d9abcaad95c6fc4824b2cd4e2b80bfc5d59ef7380f0d12f08622a4`、`d29535bfbe13776d3f006639b450cb85701647772414034fd01484838da940de`。policy stdout 还直接记录从该 checkpoint 加载 train metadata、恢复 `params`、并从 `assets/rmbench_put_back_block_robot` 加载 norm stats。

任务私有离线提取器 [`extract_baseline_identity.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/tools/extract_baseline_identity.py)（SHA-256 `f0640fadfd6be64fb6007ab4e7b490174c2172cc5862ea36cc9e1e04973593e1`）重读 runner、policy server、backend、recorder、launch、manifest、result config 和 policy log，输出 [`baseline_identity.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/analysis/baseline_identity.json)（`25f89ee7c4f8ba56e2976f8e4657b66af95df3c2a54e462800e065df916269e9`）。其 baseline 身份链检查全部为真。baseline 的 `MemoryCheckpoint` source-root 与旧 baseline command 一致，解析 `MemoryCheckpoint/20000/metadata` 存在；shadow 的 `--source-root MemoryCheckpoint=...` 少了 `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` 这一层，解析后的 checkpoint 和 metadata 都不存在。虽然 shadow launcher 的 `RB_OPENPI_POLICY_DIR` 值未被使用到，runner 在 metadata source 校验时即以 `InputNotReady: checkpoint_metadata` 停止：无 reset、policy startup、scheduler child、action RPC、result leaf 或 retry。

baseline scheduler receipt SHA-256 为 `f56e3438c911ce76232b9e69b0928b3860f2df8d5e03f607c3959b3ae8a4e252`，runner receipt 为 `d8988c7035fb3b554e1ed43d711eaf54a55835e37ac7ea4597d00ad9a1bdcfea`，验证摘要为 `b421a3b2f088043238fa6288e5bd968c9d023989206e77c797b0c837f86861ec`；shadow failure receipt 为 `64ee0c7c9f4e4d77a99e20af55ed830bc06b42455cbe820ca34e98ceb0a89d21`，其验证摘要为 `ee366342b9c58ebf36a2249f0e12404c021c321d2acc9ffcbc762fda5d9b8fbb`。baseline 完整保存 RGB/state/memory/prompt/request/response pickle，首个 `infer_audited` 与真实 execute 各一次；H50 为 float32 `50×14`、K30 为 float32 `30×14`，`queued=30`、`dropped=30`、`logical_step=0`。唯一 accepted reset 是 episode 0 / seed `100000` / `put_back_block`；无第二 inference、seed `100001`、replay、warmup 或 probe。事件顺序为 RPC 返回后的 RAM copy、原 `run_iteration`/`after_execute`、clear、无 drain status、持久化。

修正并重跑 [`analyze_original_entry_alignment.py`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/tools/analyze_original_entry_alignment.py)（`221f6e640dec1649f49f3153a799f72bb40aa63f2e57e02c613dc045a26540af`）后，provenance wording 与其实际 `source_root_matches_original=true` 一致。新 [`original_entry_alignment.json`](/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/original_entry_first_query_20260914/analysis/original_entry_alignment.json)（`b96be2c03c9298785b767ad751037df9680a40178df920c9f6c8e6b816610530`）确认本次 H50 前 30 行与本次实际 K30 完全相等；与旧 baseline H50 有 `499/700` 个 float32 元素不同（max abs `0.004009723663330078`，RMSE `0.000707095339374057`），本次 K30 与旧 baseline H50 前缀有 `298/420` 个不同、与旧 shadow K30 有 `301/420` 个不同。它同时保留了旧 evidence 缺完整 RGB、完整 request、真实 PRNG key、wire bytes 和旧 shadow H50 的边界；因此不能从这一次有界、替换 scheduler child 且非终态的诊断得出历史差异的因果结论。

本节是有界诊断收据，从不构成 matching smoke 或 formal。shadow 不会自动重试；先前 6 个与本节 baseline 1 个正常 action samples 合计已使用 `7/8`，剩余 **1** 个未经 Manager 再授权不得使用。HF formal 继续冻结。

## 历史：修正 shadow 前的未执行项

此前的源码修复验证仍是 CPU-only；早先 C3 有界诊断已完成 6 次首 query 采样，本报告的“原入口有界首 query 执行”节另记录随后授权的 baseline 1 次真实 action request。未启动新的完整轨迹、matching smoke、formal 100、`r_s=30` 或 HF 效果试验，未训练、未改 checkpoint、未部署，也没有新增生产源码提交。累计已使用 `7/8` 个正常 action samples；剩余 1 个仅可在 Manager 对新的有界假设明确授权后使用。
# 同实例 probe 工具 C3 身份核对

terra/max 独立只读执行身份核验，与 Manager 亲自代码复审并行。先读 MAM AGENTS/README/.local/README/.local/wuwen-4090.md 和源task 0acf5d43-91b6-4171-b727-e3fe0f7e7939 最新report cc13734159384e2151b799e8c871a6b92a7ff9e9。不要重新review科学设计或全工具，勿改变代码/文档/计划，不加载backend/模型、调用JAX devices或运行GPU。

在 C3 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check`，只读重哈希工具6edd0ba2ce04c6ba70c9efa239cd5f603e9097ad7079f10dce013a660850491c、tests fb1d7a84cc9ae6b88a36fa9521bc676abad5c0d75d45c44dee314fda31db6e8b、README 7ae2d57856fb0db3302a530cde8cd9c3d8cd00a65fd4beb26c450b6b0c1933c8、audit b879680aedb7655e1299079f15d4e80173ecf8fcf7422de643e29f78d85c3abc，与本机逐一相等。plan_20260914_v4/plan.json预期SHA4408a8732f3fa259f5224de6dfe7c40add97e40e5a7fc511a076f8f4fb5a9916；读取其真实所有小型源文件/请求/YAML引用重哈希，勿读取/复制全部checkpoint参数。

核实其冻结runtime `/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914` 三库实际clean HEAD 0ce566bd34f99cb4775422f012ab67c16aa53885 / ffa122494c19e1c0154e877010f7b470967ccfc6 / 6abebf08d084d0be43aa56ebe158dc8395fa58e4。核对 README 实际执行模板 Python/PYTHONPATH 与 `.venv` editable安装定位：经 Python 标准库 importlib PathFinder（不执行包）或 .pth/metadata 文件检查确认将从上述树导入 openpi、robot_bridge，不只对磁盘另一个树做git验证。报告当前CUDA环境模板与实际baseline policy环境能确认的差异；无须复制所有环境值。checkpoint是put-back J train0/20000，不重传/转换/预热。

只需紧凑本task receipt/report，列清确认项与任何实际不一致。GPU0空闲可作只读快照，但仍由运行者执行前再核实。无需运行测试（Manager复跑），不需要源码worktree，无长进程，无需另外创建工具框架。完成后发布report并结束turn，由Manager决定是否运行3action+5probe有界实验。
