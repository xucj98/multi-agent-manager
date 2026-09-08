task_revision: 4e4b04bad1c464020506ababdf9d3fb12a8fcabf

# 场景与时序审阅

审阅对象仅为 `git show 2196483:docs/design/shared-memory-schema-and-scheduler.zh-CN.md`，代码取证基线为 OpenPI `71c80db`、robot-bridge `0095a3f`。审阅期间业务仓库中的该文档已有未提交改写；本报告没有采用那些改写，也没有修改业务代码、创建 worktree、环境或作业。

方向可行：schema 只描述语义/初始状态，表示配置承担编码、loss 与布局；scheduler 持有 context，policy 保持可 reset 且无 session；保留 `get_obs(wait_condition)`、action chunk、UDP takeover 路径。这些边界应保留。

在进入第 10 节的实现前，需要先补齐下列四个阻断项。它们都能在现有时序中造成错误 context 或无效训练，不能靠后续 smoke 兜底。

## 四个场景

| 场景 | 转换 → 训练 → checkpoint | infer → feedback → offline/UI | 结论 |
| --- | --- | --- | --- |
| wash-cup 单 phase，空白/label 6 | `phase` 是 enum；label 6 整集删除，空白帧的 memory target 应无效而物理 action 仍有效；checkpoint 固化 schema/表示/映射。 | full 应按已执行 policy step 更新，serial 按 query 更新；UI 只显示/修改语义 phase。 | 缺口：现有 ARX transform 会从 memory 无效推导 robot loss 无效，且草案未定义空白帧的因果 input context。见阻断 2。 |
| drawer 两字段 | 两字段应是各自的 enum/valid 数据，full 是 raw dense context，serial 是 `int32[2]`；同一快照部署。 | 人工设 `drawer_target` 或锁 `completed_layers` 时，另一字段和任何连续 raw segment 必须保持；旧预测不得回写新 patch。 | 缺口：草案只规定输入 override，不规定预测反馈的字段级 merge。见阻断 3。 |
| RMBench 多字段、异步/部分执行/takeover | full 输出每个 action-step 的 context，serial 输出一个 query context；训练 target 必须带原始 policy index。 | full 在下一次执行完成观测中取最后真实执行的 tail；serial 在 action chunk 被接受时 commit，并记录 query/执行位置。takeover 清队列后不能误提 full pending。 | 缺口：通用 scheduler 没有把 accepted chunk 与执行位置关联的协议。见阻断 1。 |
| 连续 position/rotation，initial=null | position/rotation 是 `float32` 物理量；未知不能落成物理零点；连续 serial 保持未启用。checkpoint 记录表示的 unknown、归一化和输出规则。 | full raw vector 可原样反馈，UI 显示 unknown；评价 position 用物理单位，rotation 用等价的角度误差。 | 缺口：草案没有训练行的 known/target 语义，也没有 quaternion 的等价/投影规则。见阻断 2。 |

所有场景的普通 replay 都必须将真值留给 evaluator；目前 legacy offline 默认可把 dataset phase/master 送入模型，故另有阻断 4。

## 阻断 1：full 的“执行完成”没有可实现的事件契约

所在：草案 §6（反馈时点，特别是“最后已执行动作索引”）和 §7（`stage/commit`）。

失败场景：真机非阻塞 chunk 已被 `execute` 接受，随后只执行其中 3/15 步就发生 takeover/clear；若 full 直接保存 `actions[0]` 或最后预测 tail，会把未执行动作的 memory 当成当前 context。插值还会令控制步号与 policy action index 不同。

取证：`SchedulerBase.run_iteration()` 在 action RPC 成功后立即调用 `after_execute(act_req)`，不把 response 或执行进度传给 hook；基础 controller 的 execute response 只有 queued 数量。现有 `OpenPiScheduler` 和 `OpenPiOfflineScheduler` 都在 accepted 时取 `actions[0]`。反例是 `OpenPiSimulationScheduler`：它保存整段 tails，等下次 `get_obs` 的 `logical_step` 前进后才选择 `tails[executed - 1]`。

最小修正：在表示配置中把反馈描述写成可校验记录，而不只是文字：`cadence`、原始 policy indices、chunk/query id、epoch、每个 context 对应的 action index、commit evidence 与部分执行规则。`stage` 保存该记录；下一次 `get_obs` 返回 controller 的已执行 policy 位置（或等价的 chunk-id + 已执行数），`commit` 据此选择 full context。`clear_actions`、reset 和 takeover 必须使对应 pending 失效。serial 仍可在 accepted 时提交，但日志必须带 query id、accepted chunk 与执行位置，明确其不是逐步物理状态。无需新增 server 插件体系。

验收：15-step chunk 只执行 3 步、执行 0 步后 clear、插值、RPC 失败、reset 和 takeover 六例中，full 只提交正确的原始 policy tail；serial 的 accepted-query 行为固定且可回放。

## 阻断 2：空白、unknown、连续字段与 loss 的数据契约不完整

所在：草案 §2 的 `initial: null`、§4 的 `memory_valid`/独立监督及 §10 的梯度验收。

失败场景 A（wash-cup）：一个 15-step horizon 在第 4 步遇到标注空白。草案要求保留物理 action 监督，但当前 `ArxSm2smInputs` 以 `all(memory_valid)` 调 `_causal_robot_action_valid`，会从首个无效 memory 起把 robot action mask 置 false；当前 JAX `Pi0.compute_loss` 又直接对所有维度取均值，未消费 `action_loss_mask`，其定义的 key-state CE 也未在该 loss 路径合并。只改 §4 所说的 JAX loss 仍不足以满足“action 有效、memory 无效”。

失败场景 B（position/rotation）：`initial=null` 若在 LeRobot 只写数值占位和 `memory_valid=false`，模型无法区分未知 position 与真实 `[0,0,0]`；quaternion `q` 与 `-q` 是同一姿态，却会作为不同数值 target/反馈被 MSE 和 UI 当作跳变。

最小修正：这是表示/transform/evaluator 的职责，不放回 schema。

- 训练数据明确分开物理 action 的可用性、每个 memory target 的 valid，以及每个 memory input 是否 known；空白 target 不得从未来标签回填。full 的 action-dimension mask 用各自的 valid，serial CE 用字段 mask；物理 action mask 不能由 memory valid 推导。
- 为未知连续输入定义数值编码加 known 通道（或等价的 representation-owned code），并规定 target/loss/统计量只在哪些 valid/known 元素生效。向量先整体 valid 即可。
- 在 rotation 的表示配置与 evaluator 中规定单位化、`q/-q` canonicalization 或等价角度误差；schema 继续只保留 frame、unit、`quaternion_xyzw` 这类物理语义。
- 定义 loss 的分母和全无效行为：无效 memory 不给该 head 梯度、不产生 NaN；物理 action 仍有梯度；有效 full memory tail 与 serial CE 各自有非零梯度和独立日志。

验收：构造一个 blank phase、一个 unknown position、一个 `q/-q` 对以及全 memory-invalid batch；逐项断言 mask、loss 分母、head gradient 和 physical action gradient。

## 阻断 3：字段级人工 patch/lock 无法保证保留其他 raw context

所在：草案 §6 的 `overrides`、§7 的 `MemoryContext` 生命周期、§8 的多字段 UI。

失败场景：operator 修改 `drawer_target`，并锁住 `completed_layers`；同一 full-state context 还含连续 position/rotation。下一次模型响应是整个 dense context。若 `commit` 直接替换 raw vector，锁和人工值被旧预测覆盖；若 scheduler 先 decode 后重编码整个 vector，则未修改的连续值会被量化、归一化往返或丢失 unknown 标志。现有单字段 `OpenPiScheduler` 正是整段 `_dense_memory` 替换，不能作为多字段实现的默认行为。

最小修正：让 model adapter（而非 schema 或 scheduler）提供一次字段 patch 和一次反馈 merge：输入为旧 raw context、语义 overrides、field locks 与预测 raw context；输出为新的 raw context 及同源 semantic values。scheduler 只保存 adapter 返回的 raw result、字段锁和 epoch。`set_memory` 必须使旧 epoch chunk 无效；lock 仅屏蔽本字段的预测 merge。该协议足以由现有 `control_actions` 同时供键盘和 UI 使用，不需要抽象注册表。

验收：对两个 drawer 字段和一个连续 vector，分别一次性修改、持续 lock、inference 中途修改；断言未修改 raw segment 不变，锁字段不被反馈覆盖，旧 epoch 的 action/context 均不提交。

## 阻断 4：offline 的“真值只给 evaluator”缺少强制运行模式

所在：草案 §8。

失败场景：普通 drawer/wash replay 误沿用 legacy `openpi_offline` 配置。其 `master_source`、`phase_source` 默认是 `dataset`，controller 会把 GT phase/master 放入 `get_obs`，scheduler 再写入 policy input；此时 memory 指标和 action 误差都不是自回归部署结果，且无显式 oracle 标记。

最小修正：新转换 replay 的普通模式固定为 model-owned context：reader 只向 scheduler 提供物理 observation/执行进度，真值与 valid 只留在 evaluator record。oracle 只能走显式实验路径，并在 infer metadata、result manifest 和 UI 状态写 `oracle=true`。历史 drawer 原始 reader 可以保留为验收 adapter，但 dataset context 不得成为普通 inference 的默认值。

验收：将 evaluator 的 memory 真值替换为随机值，普通 infer request 的 bytes 和 prediction 必须不变；oracle run 必须因标记/输入不同而可识别；两类结果不得混合汇总。

## 可简化的实现边界

- `MemoryContext` 不必发展为通用插件。保留四个生命周期动作即可，但其 pending record 与 adapter merge 的输入/输出必须具体化。
- 沿用仿真已有的 `logical_step` 作为 full 反馈的回归样例；真机只需提供等价执行位置，不要求两端 server 建立共用扩展框架。
- 旧 full 连续 tail 只做 representation 规定的处理，绝不因统一 schema 走 argmax；分类投影仅作用于对应分类字段。

## 需要用户确认的实验语义

wash-cup 的空白标注除“target mask=false、物理 action 保留”外，还需确定该帧的因果 input：

1. 保持最近一次已知 phase（首帧用 `pick_cup`），不从未来标签补值；或
2. 从空白开始输入 explicit unknown，直到下一次已知标注。

这会改变 full/serial 的训练分布和离线解释，不能由工程默认决定。另应将“serial query 已 accepted、随后 action 被 takeover 清队列”明确写成保留该 query context 或回滚；草案倾向 accepted 即提交，但需在回归样例中固定。

## 交付与验证

完成：固定草案的只读设计审阅、四场景推演和定点源码取证。

未完成：未修改业务代码、未运行测试/GPU/训练；待 Manager 裁决以上阻断项和两项实验语义。

workspace、各库交付 commit：按任务限制未创建 workspace/worktree；无业务库提交。

验证结果与成果位置：报告在本文件；取证包括 `robot_bridge/scheduler/{base,openpi,openpi_offline,openpi_simulation}.py`、`robot_bridge/robot/controllers/{base,x2robot_offline}.py`、OpenPI `models/pi0.py` 和 `policies/arx_policy.py` 的固定提交内容。

## 第二轮最终定向复核（c4d5b35）

本轮只复核 `robot-bridge` `c4d5b3590a84670ad5cf8dcfa21d0263e5441abf` 的设计文本、任务中给出的 drawer/RMBench 时间关系，以及字段锁定契约；未重复数据扫描、源码/训练 target 取证，也未创建 worktree、环境或运行训练。

§6 新增的常规索引公式成立：若 query `t` 的第 `i` 个逐帧输出表示 `m[t + target_offset + i]`，下一 query 需要 `m[t′ - input_lag]`，则 `i=t′-input_lag-t-target_offset`。因此 drawer 的 `input_lag=15,target_offset=0,t′=t+15` 取 `i=0`；RMBench 的 `input_lag=0,target_offset=1,t′=t+k` 取 `i=k-1`。这正确地把 accepted-first 改为仅在训练时间关系对齐时可用，而不是默认正确。

| 路径 | 最终文案复核 |
|---|---|
| drawer full-state 常规区间 | 通过：15 帧 query 间隔时首个 context 与训练输入对齐。 |
| RMBench full-state | 通过：`k` 个已执行 policy step 对应第 `k-1` 个 context。 |
| serial-soft | 通过：选择由该模型的 query lag/offset 决定，接受事件与物理完成分开记录。 |

### 阻断：强制覆盖区间和部分执行仍没有唯一的选取规则

所在：§6 第 139–154 行、§7 第 171 行。

`input_lag` 是固定表示参数，但 drawer 表已说明部分 execution 区间强制覆盖输入。这些 query 的有效输入时刻不一定是 `t-input_lag`；当前文字只说“不能据此保证一致”，没有说明 scheduler 应使用哪个输入坐标或无匹配时如何处理。与此同时，§7 无条件规定“部分执行以 controller 已报告的执行位置为准”。例如正常 drawer query 从 `t` 到 `t+15`，但实际只执行 `k<15` 步时，§6 公式要求为下一次训练式输入选择 `i=0`，§7 又可能要求按 `k` 选择，真机还没有新增进度回执来消除该歧义。实现者可能错误回灌第 `k-1` 个 context，或在强制覆盖区间继续沿用首个 context。

最小修正文案可替换 §7 的部分执行句，并补在 §6 表后：

> 对强制覆盖输入区间，表示元数据须记录该 query 的有效 input frame（或 effective input_lag）；选择公式使用该值。无匹配输出时丢弃 pending 并重新 query，不取首项或 clamp。仅 `execution-position` 策略按 controller 已报告的执行位置选择（如 RMBench）；`training-lag` 策略按 §6 的 query 坐标和有效输入坐标选择，部分执行位置不得覆盖该选择。

锁定字段的主契约可行：`locked_fields ⊆ overrides`，adapter 只编码锁定字段并从同一 raw context 解码 UI values，故不会对未锁定连续段做 scheduler 侧重编码。为避免一次性 override 消费后被误解为解除锁，建议在 §7 `prepare()` 说明一件实现细节：锁定时快照当前语义值，并在每轮 `prepare()` 将每个持久锁值重新写入请求 `overrides`；只有非锁定的一次性 override 在同 epoch 首次反馈提交后消费，解锁才移除该持久值。这不需要额外 RPC 或 raw merge。

wash-cup 仍只待用户确认标注空白区间的 input/serial-conditioning 处理；标签筛选规则和“172 集”计数未在本轮重新调查。

## 本轮交付与验证

完成：对最终文案的公式、三种反馈路径和锁定契约做了定向复核，并给出一项可直接落文档的阻断修正。

未完成：未修改业务代码或设计草案，未运行测试、GPU 或训练；强制覆盖区间的有效输入坐标与部分执行策略需先按上述文本固定，空白区间处理仍待用户确认。

workspace、各库交付 commit：按任务限制未创建 workspace/worktree；无业务库提交。

验证结果与成果位置：本报告；审阅对象为固定 commit `c4d5b3590a84670ad5cf8dcfa21d0263e5441abf` 的 `docs/design/shared-memory-schema-and-scheduler.zh-CN.md`。
