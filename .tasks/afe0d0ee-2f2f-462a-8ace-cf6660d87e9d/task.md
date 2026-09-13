# P0诊断记录接口独立审查：行为等价、RNG与证据完整性

## 当前执行：已确认四项问题的增量复审

源task8968b7f5新报告 `1ed55ee703ad7bd0bc3c2a37dc850121b59832c5` 已发布，以下新冻结提交取代旧交付作为本轮审查对象：OpenPI `cb861d3824a46d9c243be7ff69159bcec17a0ac7` → `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`；robot-bridge `a2c7f80b99556db2147c85ca9f625ffb840b276a` → `fa62a9febc8fab9098994d0cb8e1894a0590b7e8`。保留你已有独立review workspace，不新建重复树；核对clean后把本任务review分支快进至相应候选，再读新report及代码。

Manager此前已接受四项发现：v1 execute non-ok后record过早关闭、legacy non-ok候选缺record ID形成悬挂、cap在复制/传输后才检查、空complete sidecar可伪装recorded。逐项独立复核真实run_iteration失败/重试/supersede/reset/terminal链，证据未知actual K保持null，不改变动作或默认RNG。检查源新增preflight在host/device copy、msgpack和NPZ之前生效，极小预算+1024²RGB测试须真正经过Policy/codec/recorder链而非只测serializer；容量不足仍不能改变S sampler语义。检查必需schema、missing sampling key以及伪造recorded的校验拒绝。

作者声称OpenPI6、bridge35 CPU通过，synthetic17数组recorded；这不是独立PASS。此前4个read-only transform failures如仍出现，需保留准确旧基线复现来源，不笼统归为环境或新代码错误。检查变更包含的格式化是否隐藏了默认路径行为变动。checkpoint强身份仍由独立run-level权重manifest提供，本任务不扩展逐query权重哈希。

给出精确commits、独立验证和剩余限制、是否准入最小受控GPU验收；不得运行GPU/正式eval/训练或改作者树。HF task0acf仍独立，不把它的未提交修复混入本review。发现实质问题即时报告Manager裁决；完成后publish report并正常结束，无需活跃等待。

使用 gpt-5.6-terra/max 独立审查，Manager 亲自裁决，不改变科学设计。阅读 AGENTS 与本 task 已捕获的源要求、report 和准确交付，mam workspace add 分别从 OpenPI cb861d3824a46d9c243be7ff69159bcec17a0ac7 / robot-bridge a2c7f80b99556db2147c85ca9f625ffb840b276a 创建独立 review worktree。基线分别 a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 / f9626636c4776d8eb15f9c556775cb2d12c000e5，审查这两个精确 diff，不混入高频 owner 未提交源码。

重点核验：默认关闭是否完全保持现有接口/采样/RNG；开启选中 query 时真实 Policy transform→model→output 路径是否仍动作/状态和最终RNG相等；S details 与原三值API的真实model路径一致；J/T raw坐标不冒称logits；序列/explicit noise/reset；-inf原始数组与严格finite JSON；有界选择/容量、异步设备copy时序、写失败不影响动作但证据缺失可见；记录的参数/input/checkpoint/code/episode/seed/query以及NPZ与JSON关联足以复核，实际K/pending/cancelled/terminal不能伪造；array/namespace是否可以互相覆盖或报告错误完成。报告 I/O 插入动作dispatch之前的实际影响，不要求证明物理实时轨迹等价。

独立运行有意义的窄CPU tests和dry-run，包括必要反例；源码审查和行为覆盖分开陈述，不能仅复述作者16/66计数。不得改作者tree、运行GPU/正式rollout/训练、安装生产或把code PASS写成GPU验收。给出P1/P2精确文件行和触发条件；发现bug及时告诉Manager，由作者修，除测试证据外不代写功能。完成后发布report，PASS仅意味着可进入最小受控GPU验收。与高频任务0acf独立并行，这份logger不是该任务CPU开发的等待前置。

Review source delivery (source TASK-ID: 8968b7f5-74f7-44db-ad0b-058d3fd556ca):
{
  "task": "8968b7f5-74f7-44db-ad0b-058d3fd556ca",
  "commits": {
    "openpi": "cb861d3824a46d9c243be7ff69159bcec17a0ac7",
    "robot-bridge": "a2c7f80b99556db2147c85ca9f625ffb840b276a"
  }
}

Source task requirements:

# P0诊断记录接口：状态原始输出、动作和RNG的无行为改动采集

## 目标与职责
你使用 gpt-5.6-terra / max，负责实现和验证。Manager 负责论文主张、实验设计和最终裁决。先读 MAM AGENTS、README、.local/README，再 mam task show 本 TASK-ID 和相关库 AGENTS、开发/环境说明。原审计任务 f987cfb5 已归档，其交付现保存于 /root/Documents/task-state-vla-paper/docs/audits/20260913-trace-inventory/；不要使用已删除的旧 workspace。

现有日志缺少原始状态输出、动作与 RNG，无法据此进行同一输入/随机数的状态敏感性诊断。实现默认关闭、显式选择 episode/query 的最小记录接口，提供后续复现所需证据。本次仅代码、CPU 验证和 dry-run 方案；不开展新 GPU rollout、正式评测或训练，不部署到运行中的 C 集群 runtime，不实现状态干预。

## 冻结基线与范围
通过 mam workspace add 建立独立 worktree：OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；robot-bridge f9626636c4776d8eb15f9c556775cb2d12c000e5。必要的启动参数贯通优先在两库完成；确需 RMBench 修改时先报告具体原因并固定既有正式 r3 baseline，不能隐式使用其他开发树。不要修改原运行树、模型、数据和正式结果。

优先沿既有 policy/scheduler trace 路径添加窄接口，不建立通用日志框架。限制记录数量、数组体积和存储范围；完整输入可采用有校验值的独立文件引用，不能仅存无法复现的摘要。

## 记录合同
每次选中 query 记录版本化 schema、checkpoint 与代码身份、episode/env seed/query 链接，实际推理输入（图像、机器人状态、token、memory；区分变换前/后，保证可复现），及下列证据：
- J/T：联合生成的原始 memory 坐标和解码结果，不能称为分类 logits。S：真实 key_state_logits、最终选中的 IDs，以及实际用于 condition action 的状态。
- 原始完整 action chunk、输出变换后的 robot actions，shape/dtype/单位；scheduler 的动作下发/变换关联需说明覆盖到哪一层，未观测的 controller 内部量不作已记录声明。
- policy RNG split 前、实际 sampling key、split 后状态，以及调用方显式提供的 noise（若存在）。不能为了记录额外 split 或生成新 noise。对未显式供给的采样内部噪声，保存足以重现的 key/算法身份，不虚构直接观测。
- scheduler cache 前后、消费的 memory 行、accepted/discarded/terminal progress、planned K 和有观测支持的 actual K。未知为 null；尤其 S 旧 trace 的 actual_k=0 是未填充，不等于未执行。
- wall/monotonic timestamp；已有 infer timing 与新增 logger 开销分开，说明异步设备执行下时间含义，不改变默认同步行为。

记录不允许改变 input、decoder、采样 RNG、数组内容或执行策略。启用记录会有可测 I/O 开销，不声称物理实时轨迹完全等价；默认关闭时维持既有协议/输出，不添加必需字段。读写失败策略明确且有测试，诊断缺失需显式可见，不能悄悄伪造完整证据。S padded logits 含 -inf，JSON 必须严格 finite，原始数组可用支持非有限值的格式并在元数据标注。文件哈希、episode/query/序号跨文件关联可校验。

## 验收和交付
提供最小 CPU tests，验证相同实际输入与相同初始 RNG 下 logging on/off 的动作/状态输出及最终 RNG 相等；多 query、J/T 与 S 路径、显式 noise、默认关闭、写入失败和 -inf roundtrip/严格 JSON、序号文件链接覆盖根据实现组织为有意义的测试。mock sample 必须保留真实 policy 的输入变换/RNG split/输出变换调用链；不能仅测试 serializer 后声称已验证 policy 行为。
发布 report，包含干净 commit、完整 diff 范围、验证命令/结果、示例记录和校验脚本、存储/开销界限、后续最小 GPU smoke 方案与尚未验证的界限。短 CPU smoke 无需登记 job，任何预计超过 30 分钟的程序按 MAM 登记。完成可执行工作后正常结束 turn，不轮询。Manager review 之后才决定 GPU 验收和诊断实验。

Source report:

# P0 选中 query 诊断记录接口：完成报告

## 交付

- OpenPI worktree：`/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/openpi`
  - 冻结基线：`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`
  - 交付 commit：`cb861d3824a46d9c243be7ff69159bcec17a0ac7` (`Add opt-in selected-query policy diagnostics`)
- robot-bridge worktree：`/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/robot-bridge`
  - 冻结基线：`f9626636c4776d8eb15f9c556775cb2d12c000e5`
  - 交付 commit：`a2c7f80b99556db2147c85ca9f625ffb840b276a` (`Persist selected-query diagnostic records`)

两个 worktree 均已在各自 `task/8968b7f5-74f7-44db-ad0b-058d3fd556ca` 分支干净提交。

## 实现范围

OpenPI 的 `Policy.infer` 新增仅由
`__openpi_diagnostic_context__` 启用的 sidecar；该字段在任何输入 transform 前移除，默认
请求和响应不增加字段、不写文件。选中调用记录变换前输入、batched transform 后输入、
`Observation.from_dict` 后传入 sampler 的输入（包括图像 uint8 到归一化 float 的变化）、
完整 raw action chunk、output transform 后输出、显式 noise，以及 JAX split 前 key、实际
sampling key 和 split 后 key。日志快照不额外 split RNG、生成 noise、调用 decoder 或改变
transform；捕获失败会以 `capture_failed` sidecar 明示，保持动作和最终 RNG 路径不变。

`Pi0.sample_actions_with_key_state_details` 在不改变既有三值普通 wire 的情况下，提供选中
诊断所需的 decoder selected IDs、实际用于 action condition 的 IDs 和真实 logits。J/T 的
tail 记录为连续 `raw_joint_memory_coordinates_before_output_transform`，并显式注明不是
classification logits；S 记录含 `-inf` padding 的真实 key-state logits、selected IDs 和
action-condition IDs。数组 descriptor 提供 dtype/shape；通用 policy 无法如实声明物理单位时
写为 `null`，RMBench scheduler 对最终 14 维 arms qpos target slice 另行声明单位约定。

robot-bridge 新增窄的 schema v1 `QueryDiagnosticRecorder`，只接受严格的
`params.diagnostic_trace` 配置。每个选中 query 写 strict-finite JSON 与 NPZ：数组、bytes
和非有限浮点外置，JSON 引用包含 key/dtype/shape/nonfinite；校验器核对 SHA-256、JSON 文件名、
`query.record_id` 与 NPZ 文件名的跨文件关联。首次 JSON/NPZ 发布使用同目录 hard-link，避免
并发 recorder 覆盖另一方的初始证据；同一记录的有限 lifecycle 更新使用 atomic replacement。
写入失败、数组上限、缺 policy response、sidecar link mismatch 都会留下显式状态或 recorder
status，不中断 policy/scheduler 动作路径。

`OpenPiSimulationScheduler` 将选中 context 注入 policy request，关联 policy sidecar、output
action chunk 与实际 `execute` request，并持续记录 cache、accepted/discarded/terminal、planned K、
已消费的 memory rows 与有 controller execution-progress 支持的 actual K。S 的
query-selected feedback 将旧 trace 的初始化 `actual_k=0` 规范为
`not_recorded_for_query_selected_feedback` / `value: null`，不声称执行零行。benchmark runner
把已接受 episode/seed 仅作为诊断构造参数传入 scheduler，未发起第二次 reset。

新增文档与入口：

- `docs/reference/query-diagnostic.md`
- `scripts/query_diagnostic_dry_run.py`
- `scripts/validate_query_diagnostic.py`

## CPU 验证

以下命令均在对应独立 worktree 完成，未启动 GPU rollout、训练、评测、部署或真机/仿真控制。

```bash
# openpi
JAX_PLATFORMS=cpu .venv/bin/pytest -q \
  src/openpi/policies/policy_diagnostic_test.py \
  src/openpi/training/memory_data_test.py \
  src/openpi/models/pi0_memory_test.py
# 16 passed

.venv/bin/ruff check src/openpi/policies/policy.py \
  src/openpi/policies/policy_diagnostic_test.py src/openpi/models/pi0.py
.venv/bin/python -m compileall -q src/openpi/policies/policy.py \
  src/openpi/policies/policy_diagnostic_test.py src/openpi/models/pi0.py
.venv/bin/python scripts/worktree_env_smoke.py
# 均通过
```

```bash
# robot-bridge
PYTHONPATH=/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/openpi/packages/openpi-client/src \
  .venv/bin/pytest -q \
  tests/scheduler/test_query_diagnostic.py \
  tests/scheduler/test_openpi_simulation.py \
  tests/scheduler/test_memory_v1_schedulers.py \
  tests/scheduler/test_memory_context.py \
  tests/scripts/test_run_scheduler.py \
  tests/benchmark/test_runner.py
# 66 passed

.venv/bin/ruff check --ignore EXE001 \
  robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py \
  robot_bridge/scheduler/memory_context.py robot_bridge/benchmark/runner.py \
  scripts/run_scheduler.py scripts/query_diagnostic_dry_run.py \
  scripts/validate_query_diagnostic.py tests/scheduler/test_query_diagnostic.py \
  tests/scripts/test_run_scheduler.py tests/benchmark/test_runner.py
.venv/bin/python -m compileall -q robot_bridge/scheduler/query_diagnostic.py \
  robot_bridge/scheduler/openpi_simulation.py robot_bridge/scheduler/memory_context.py \
  robot_bridge/benchmark/runner.py scripts/run_scheduler.py \
  scripts/query_diagnostic_dry_run.py scripts/validate_query_diagnostic.py
.venv/bin/python scripts/worktree_env_smoke.py
# 均通过；EXE001 仅忽略已有 run_scheduler.py shebang 非 executable mode
```

额外完成 OpenPI msgpack 与 bridge transport codec 的含 `-inf` logits round trip；结果通过。
新鲜 CPU dry-run 写入并校验了一条合成 S 记录，返回 `status=recorded`、`array_count=15`；
临时目录已删除：

```bash
.venv/bin/python scripts/query_diagnostic_dry_run.py --directory "$OUT"
.venv/bin/python scripts/validate_query_diagnostic.py "$OUT"/records/*.json
```

Policy 测试保留真实 Policy transform、batch、RNG split 与 output-transform 调用链，覆盖默认关闭、
J/T、S、显式 noise、`-inf`、image canonicalization 和 capture-failure 不干扰。Bridge 测试覆盖
多 query、严格 JSON/NPZ、hash/link、array cap、写失败、初始发布 race 不覆盖、J/T progress、S
unknown actual K，以及 runner identity 不触发 reset。

## 存储、时间与 I/O 边界

默认完全关闭。开启后必须显式选择 episode/query；`max_records` 默认 16、最大 64，
`max_array_bytes` 每条默认 64 MiB、最大 512 MiB。未压缩数组上界因此默认 1 GiB、极限 32 GiB；
NPZ 压缩、JSON 和文件系统开销不计入此界限。已存在的同名 evidence 不会被新 recorder 覆盖。

`model_infer_ms` 只覆盖 policy sampling；`diagnostic_capture_ms` 单独覆盖 sidecar snapshot/
构造，scheduler status 单独暴露最近 JSON、NPZ 与总写入耗时。选中 JSON/NPZ 是 policy response
后、execute dispatch 前的同步 I/O，会增加该次 dispatch 延迟；默认路径不执行这些操作。JAX
设备执行可能异步，因此 wall/monotonic、本地 infer timing 和写入 timing 只描述本地编排，不能
解释为 kernel、controller 或物理动作完成时刻。

记录止于 policy output transform 和 scheduler 形成的 `execute` request。未记录或验证
controller 内部排队、TOPP path、底层 SDK 命令、物理 tick、相机采集内部状态，也不证明启用记录
与关闭记录的物理实时轨迹逐时刻完全等价。

## 后续最小 GPU smoke（需 Manager 另行批准）

1. 在冻结 checkpoint 与本次两个 commit 上准备专用 scheduler YAML，使用空的诊断目录，选择一个
   accepted episode、`query_ids: [1]`、`max_records: 1` 和 64 MiB cap。
2. 只运行一个受控 simulation query，不开展正式评测；保存 scheduler status 和 record/NPZ，执行
   `scripts/validate_query_diagnostic.py`。
3. 对 policy 层使用相同输入、初始 key 和显式 noise 做 logging off/on 配对检查，比较 actions、
   state 与最终 RNG；再检查 scheduler record 的 checkpoint/source identity、episode/seed/query、
   J/T 或 S evidence 与 execute slice。
4. 单独报告 I/O 延迟，不把该 smoke 外推为 controller/TOPP/physical-tick 的验证或正式实验结果。
