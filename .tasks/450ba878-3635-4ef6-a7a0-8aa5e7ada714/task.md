# Review Memory v1 checkpoint 评测 CPU 准备

Review fixed source delivery:
{
  "task": "e6908de7-4b02-465a-987b-a19eba7a315a",
  "task_revision": "6ea71195b6189b83739e487b4a641bb3fdd404c8",
  "report_revision": "268aceb515f6aa969bc0214b5de3ed86f17a2ce2",
  "commits": {
    "RMBench": "498cc4c49e8669dab822e55a2dd060a5e1c68d98",
    "robot-bridge": "8ea6078543a875b5ae223df16891cdc1fe975c66",
    "openpi": "a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4"
  }
}

Source task:

# Memory v1 新 checkpoint 评测准备

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

先提交CPU准备commit并发布简短report，注明task_revision、三库实际SHA/workspace、命令dry-run与metadata检查、GPU待办和预计耗时。Manager验收后分配GPU进行新schema必要smoke或正式模型评测；未分配前不占本机GPU0/1或远端八卡，它们已有任务。超过1小时的正式进程用mam job add登记。

任务自己的smoke和临时文件自行清理，正式产物留共享主repo。正式运行期间冻结所有被调用worktree；结束、处理job并完成交付后由Manager归档环境/分支。

Source report:

task_revision: 6ea71195b6189b83739e487b4a641bb3fdd404c8

完成：

- RMBench 已提交 CPU 准备版本：498cc4c49e8669dab822e55a2dd060a5e1c68d98（“准备 Memory v1 checkpoint 评测适配器”）。
- 交付仅在 RMBench 的 experiments/memory_chunk_20260910：
  - commands/run_memory_schema_eval.py
  - configs/memory_schema_eval.yaml
  - README_memory_schema.zh-CN.md
- 删除了未提交的 drawer wrapper；README 直接给出既有 robot-bridge/scripts/launch/drawer_offline.py 的两个旧模型、固定五集、输入和输出命令。
- 入口只保留 checkpoint metadata/schema → input audit → derived static manifest 的窄适配。它不管理子进程、GPU 探测、detach、队列日志、结果 recorder 或自定义 smoke 校验；这些均复用 BenchmarkRunner/RMBench recorder。
- technical-smoke 必须是 leaf 50、mode=smoke、run-name 以 technical_ 开头，runner 仍固定两条 accepted rollout（video on/off），manifest 记录 evaluation_kind=technical_smoke。常规 smoke/formal 即使 dry-run 也只接受 config/exp_name/20000；formal 只转交 --smoke-run 给既有 runner 的 validate_smoke_run 和握手后 assert_smoke_compatible。
- 已将本 task OpenPI 分支从 929e398682feb78a043d7252bfe72204e710cc2d fast-forward 到 a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；未重建环境。配置与说明同步该固定 SHA，bridge 仍固定 8ea6078543a875b5ae223df16891cdc1fe975c66。
- 公共接口缺口已核实：BenchmarkRunner 只消费静态 manifest，provenance 模块只验证逐文件 evidence，均没有 checkpoint→audit/manifest 生产 API；因此未修改 bridge，而由本实验组构造必要输入。
- 另发现 bridge 对完整 checkpoint/metadata 作逐文件集合验证。把 audit 写入 metadata 子树会让 evidence 自引用并必然失败，故完成 checkpoint 的不可变 sidecar 放在 <checkpoint>/eval_inputs/memory_chunk_20260910/<variant>/；通过 run.config_source 由 recorder 继承至结果的 checkpoint_metadata/lineage/config_source/。这保留既有 metadata 留痕，不在 eval_result 创建输入缓存。

workspace、实际版本：

- RMBench：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench
  - task/e6908de7-4b02-465a-987b-a19eba7a315a，498cc4c49e8669dab822e55a2dd060a5e1c68d98，干净。
- robot-bridge：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/robot-bridge
  - task/e6908de7-4b02-465a-987b-a19eba7a315a，8ea6078543a875b5ae223df16891cdc1fe975c66，干净。
- openpi：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/openpi
  - task/e6908de7-4b02-465a-987b-a19eba7a315a，a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，干净；MAM 登记的 base 仍显示初始 929e398，实际 checkout 已按发布要求快进。

CPU 验证：

- 在 a869498 上以 JAX_PLATFORMS=cpu 对两个保留 d10/50 checkpoint 重跑入口 dry-run：
  - full：joint_dense、H50/K30、padded action 32、phase/empty_mat_side/button_press_status、chunk_completed/last_executed、demo_clean_state，metadata 经 _runtime_metadata → MemoryContext。
  - serial：serial_token、同一 H50/K30/32 与字段、query_selected/query、demo_clean_state，metadata 经相同真实路径进入 MemoryContext。
- 将 full checkpoint 传给 serial variant 被 schema 不匹配拒绝；未带 --technical-smoke 的 step 50 被 20k 门拒绝；technical-smoke + formal 被 CLI 拒绝。
- 对真实 d10 technical audit，bridge verify_audited_checkpoint（params/assets）和 verify_audited_metadata（metadata）均通过；derived manifest 标记 technical smoke。还以临时 mock completed checkpoint 验证最终 checkpoint sidecar 不改变 metadata evidence 集合，并可同时通过两种 bridge verifier。
- RMBench recorder.inherit_metadata 已验证可将 config_source 的 input_audit.json 与 input_manifest.json 复制进 checkpoint_metadata/lineage/config_source。
- AST/YAML、git diff --check、bridge benchmark/drawer --help 均通过；入口 help 不含 --detach 或 --check-smoke。
- 没有加载模型、启动仿真或 GPU 进程；MAM jobs 为空。技术审计 .local/memory_schema_eval/technical_inputs、测试临时目录与 /tmp 输出均已清理，未写入 eval_result。

行数与边界：

- 入口为 256 个物理行、230 个非空非注释行，AST 计 170 个语句。约 150 的目标按可执行逻辑只超 20 个语句；保留的增量是六项 metadata/schema 断言、params/assets 与 metadata 两个不同 scope 的逐文件 evidence、不可变 write-once sidecar、派生 manifest，以及调用既有 runner 所必需的服务命令接线。没有通过压缩排版或新增平行 runner 达到表面行数。

未完成与 GPU 后续：

- 当前没有 GPU 授权；未执行 technical smoke、20k 常规 smoke、100 episode formal 或 drawer offline 回归。
- 获授权后先为每个完成 20k checkpoint 执行 --prepare-audit，再执行匹配的两集 smoke；确认 runner 产物后同 checkpoint/formal 使用该 smoke。technical 50 结果只用于新 wire 验证，检查后清理技术结果与 .local 输入。
- 正式 100 episode 需在干净 commit 上由单卡串行运行，启动后立刻 mam job add 登记。入口配置每 episode timeout 为 3600 秒：两集 smoke 的硬上限约 2 小时加启动，正式 100 的实际时间应以 smoke 实测 wall time 乘 50 后再向 Manager 报告，CPU 准备不能可靠给出更窄估计。
- drawer 使用 README 的既有 direct command；其没有 CPU dry-run，GPU 分配后才能运行。

