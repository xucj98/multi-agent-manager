# Review Memory v1 checkpoint 评测 CPU 准备

Review fixed source delivery:
{
  "task": "e6908de7-4b02-465a-987b-a19eba7a315a",
  "task_revision": "0d304cc88fcd38b3cdd443e44126ac7926954faa",
  "report_revision": "e212beff92c34e9f88baba4ff59d1da3097ddaae",
  "commits": {
    "RMBench": "737890494d38486c6335feed6fe55f550b271234",
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

10:23 Manager接受498cc4c所列公共接口缺口与必要适配范围，但正式审计输入也应使用本任务RMBench/.local/memory_schema_eval下的临时目录，不能写入<checkpoint>/eval_inputs。原因是评测需可读取不允许写入的checkpoint，同一模型也会被多个实验/工作区使用；评测配置归执行run，其已有config_source继承已验证可以保留输入快照。请统一技术/正式临时存放机制，继续通过既有recorder复制到run，保持checkpoint所有文件不变，说明run完成后清理路径；只做这一处小修和相应CPU验证，不扩大runner框架或新造持久缓存。若公共接口确有必须写checkpoint的约束，先给具体代码证据。正式结果仍只在RMBench/eval_result/<group>/<run>。

先提交CPU准备commit并发布简短report，注明task_revision、三库实际SHA/workspace、命令dry-run与metadata检查、GPU待办和预计耗时。Manager验收后分配GPU进行新schema必要smoke或正式模型评测；未分配前不占本机GPU0/1或远端八卡，它们已有任务。超过1小时的正式进程用mam job add登记。

任务自己的smoke和临时文件自行清理，正式产物留共享主repo。正式运行期间冻结所有被调用worktree；结束、处理job并完成交付后由Manager归档环境/分支。

Source report:

task_revision: 0d304cc88fcd38b3cdd443e44126ac7926954faa

完成本次小修：

- RMBench 最终 HEAD：737890494d38486c6335feed6fe55f550b271234（基于 CPU 准备提交 498cc4c49e8669dab822e55a2dd060a5e1c68d98）。
- technical、常规 smoke 和 formal 的 input_audit.json / input_manifest.json 统一生成在本任务 RMBench worktree 的 `.local/memory_schema_eval/inputs/<variant>--<resolved-checkpoint-path-hash>/`。checkpoint 不再写入 `eval_inputs` 或任何 sidecar；同一 checkpoint 可由多个实验组或 worktree 只读复用。
- 不新增公共 API 或 runner。BenchmarkRunner 既有 `--source-root` / `config_source` 已可读取该目录，RMBench recorder 既有 metadata inheritance 将两个输入文件复制到正式 run 的 `checkpoint_metadata/lineage/config_source/`。
- README 已说明：technical 结论记录后删除其 local 输入与技术结果；20k local 输入保留到匹配 formal 完成并确认继承副本后删除。它们不是持久缓存，也不在 eval_result 下创建输入目录。

CPU 验证（未加载模型、未启动仿真或 GPU）：

- 对保留 d10 full 50-step checkpoint 执行 `--technical-smoke --prepare-audit`：metadata 经 `_runtime_metadata -> MemoryContext`，得到 joint_dense、H50/K30、padded action 32、demo_clean_state 和 chunk_completed/last_executed；audit 落在新的 worktree-local 路径。
- Bridge `verify_audited_checkpoint` 验证 27 个 params/assets 文件、`verify_audited_metadata` 验证 29 个 metadata 文件均通过；checkpoint 下确认没有 `eval_inputs`。
- 使用既有 `inherit_metadata` 验证 `config_source` 复制 `input_audit.json` 与 `input_manifest.json` 到 `checkpoint_metadata/lineage/config_source/`。
- technical dry-run 和一个仅在 /tmp 构造、结束即删除的 canonical 20k checkpoint 的 formal dry-run，均传递 worktree-local `Audit` source root；未执行任何服务或 rollout。
- AST/YAML、`git diff --check` 通过。两类 local audit、/tmp canonical checkpoint、/tmp 输出和本任务 bytecode 均已清理。

固定工作区与依赖：

- RMBench：`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench`，`task/e6908de7-4b02-465a-987b-a19eba7a315a`，737890494d38486c6335feed6fe55f550b271234，干净。
- robot-bridge：同级 `robot-bridge`，8ea6078543a875b5ae223df16891cdc1fe975c66，干净。
- openpi：同级 `openpi`，a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，干净。

没有 MAM job 或 GPU 进程。GPU 授权后仍按既有规则：完成 20k checkpoint 先 prepare-audit、匹配两集 smoke，再用同 checkpoint 的 smoke 启动 formal；超过一小时的正式任务立即登记 MAM job。
