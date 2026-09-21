# 独立科学裁决：接管后的论文与 HF 证据边界

TASK-ID：`959d76e3-aa68-4e74-af29-33e9a21b24e3`  
AGENT/CODEX_THREAD_ID：`01a0c410-945c-7920-b76a-efee33a64bca`  
独立审计 workspace：`/mnt/public/xcj/Projects/workspace/959d76e3-aa68-4e74-af29-33e9a21b24e3/RMBench`，基线 `eb0546a04c857f2ad325d0dc322211ff1f82c393`。

本轮只读。没有启动训练、评测或长进程，没有终止进程，没有改动论文、RMBench 或既有任务，也没有重复遍历原始 rollout。已读论文 TeX/PDF、`docs/EXPERIMENT_PLAN.zh-CN.md`、`RESEARCH_POSITIONING.zh-CN.md`、`RESULT_ANALYSIS_AND_FOLLOWUPS.zh-CN.md`、`STATE_PREDICTION_FREQUENCY.zh-CN.md`、`RESEARCH_DECISIONS_FROM_SESSIONS.zh-CN.md`、`docs/reviews/20260915-plan-independent-review.zh-CN.md`、既有科学审稿 `cba8b004-166c-4d24-b0e0-0b4b819f6cbc`，以及接管交接材料 `docs/handoff/20260921/`。

## 裁决

当前证据可以支持一条收缩后的描述性结论：**同一 J checkpoint、固定 K=30 下，状态刷新与事件重规划的部署效果依赖任务、评测 cohort 和执行轨迹；fixed 高频刷新不是普遍收益，event 结果也不能作为跨 runtime 的稳健算法改善。** 它暂时不能支持“高频状态更新提高成功率”“event 触发策略普遍有效”，也不能识别收益或损失来自状态预测、缓存递推、动作重规划、GPU/运行时数值或初始条件中的哪一个。

这不是对工程结果有效性的否定。它是对推断单位的限制：18 批的结果足以更新台账和论文中的观察，但不足以把 300 个 episode 的简单 bootstrap 当成跨运行时的独立证据。

## 证据身份与最新数字

`/root/Documents/task-state-vla-paper/docs/handoff/20260921/manager_hf_raw_recomputation.json` 的 `scope` 明确写着：这是 Manager 对 18 批的 outcome、seed、preflight identity 只读复算，**不是全部 source/video/rolling 的最终验收**。因此下表可作为已核对的数值记录；正式完成状态仍应逐 lane 引用相应 terminal/rolling receipt，不能只引用这一个 JSON。

| task / arm | eval0 | eval1 | eval2 | 300 集描述合计 |
| --- | ---: | ---: | ---: | ---: |
| put-back matched baseline | 100 | 73 | 61 | 234/300 |
| put-back HF-fixed | 49 | 100 | 82 | 231/300 |
| put-back HF-event | 100 | 77 | 100 | 277/300 |
| rearrange matched baseline | 86 | 81 | 87 | 254/300 |
| rearrange HF-fixed | 90 | 91 | 87 | 268/300 |
| rearrange HF-event | 84 | 88 | 86 | 258/300 |

按 pooled 描述值，rearrange fixed-baseline 为 `+14 pp`、event-baseline 为 `+4 pp`、event-fixed 为 `-10 pp`；put-back 分别为 `-3 pp`、`+43 pp`、`+46 pp`。这些差值不能独立解释为算法效应，因为同一任务内的 cohort 方向反转：put-back fixed-baseline 为 `-51/+27/+21 pp`，event-baseline 为 `0/+4/+39 pp`；rearrange fixed-baseline 为 `+4/+10/0 pp`，event-baseline 为 `-2/+7/-1 pp`。put-back event 的触发 episode 数为 `20/50/79`，与成功率没有单调关系，不能把触发次数当作中介或成功代理。

pair 记录也应保留为条件描述，而不是独立显著性证据：rearrange fixed 对 baseline 的仅 A 成功/仅 B 成功为 `37/23`，event 对 baseline 为 `27/23`；put-back 对应为 `48/51` 和 `66/23`。这些配对共享 seed，但不自动共享完整运行环境身份或独立轨迹。

## 关键混杂与有效信息量

1. **评测 cohort 与 GPU/lane 完全绑定。** eval0、eval1、eval2 是不相交的环境 seed cohort，并各自固定到一条 GPU/lane。没有把同一 cohort 随机交叉到不同 runtime/GPU，也没有把硬件作为重复因素。因此 `100/73/61` 这种跨 cohort 大幅差异可能包含初始场景、GPU/编译/数值、进程顺序或其他 lane 状态；不能用 episode bootstrap 把它压成一个跨 runtime 95% 区间。

2. **put-back 的 300 集不是 300 条独立轨迹。** Manager 复算显示，每个 `arm × eval × origin_mat` 组的结果和 episode length 完全相同，只有四类重复轨迹；同一 cohort 中的 100 个 seed 只是四种 origin 类别的重复计数。因而每个 arm/eval 的主要行为信息量接近四个 trajectory cells，而不是 100 个独立 Bernoulli 样本；300 集成功率仍可作为 benchmark 描述分母，但不能作为独立试验数。

3. **put-back 的匹配强度需要分层表述。** `manager_hf_preflight_comparison.json` 核对到三臂按 seed 的 `origin` 和 `initial_block_pose` 均相同（每组 100/100），这支持同 cohort 内的局部配对。可是完整 preflight identity 在 put-back 臂间不相等，差异集中在 `expert final_block_pose`；最大差异约为位置 `0.00121`、另一位置轴 `0.00047`、四元数 `q3≈0.0127`（具体逐项见该 JSON）。在确认该字段只属于不参与策略/终止判定的专家元数据之前，不能写成“完整初始条件完全相同”；更准确的措辞是“初始 block pose/origin 已匹配，full preflight identity 仍有未裁决差异”。

4. **重复轨迹使 cohort 方向反转更值得重视。** put-back 的 fixed 在 eval0 使 front/right 两类全部失败，eval1 全部四类成功，eval2 只使 right 失败；event 的变化也由少数 origin cells 决定。这个结构不是普通抽样噪声的外观，更像确定性策略、场景类和运行时组合的交互。应报告 `eval × origin × arm` 的 cell 表和 length，而不是只报告 300 集总数。

5. **已有 rolling 工程审计不等于科学机制验证。** 它能证明 probe、cache、消费时刻和 trigger→clear→replan 的记录合同，但 J 的 forecast 仍是从 query 起点预测未来状态，不是已发生的物理事件。event 的成功或失败不能被写成“状态估计正确”或“触发修复了按钮接触”。

## 对核心主张的判断

- **紧凑状态可能支持动作执行：部分支持。** J 在若干任务/模型上的高成功率和既有历史结果支持“有用的实例”，不支持状态充分性、训练稳定性或任意任务泛化。
- **J/T 目标分配有稳定赢家：不支持。** put-back 三个完整训练模型的 `T-J` 为 `-1.0/+6.3/+3.3 pp`，描述均值仅 `+2.9 pp`，小于已观察模型间差异；S/J/N/T 仍是整套协议混杂，不能归因于单一时间监督机制。
- **fixed 高频刷新普遍改善：不支持。** rearrange 的 pooled 小幅上升在 put-back 不复现，且 put-back cohort 内方向反转。若保留结果，主张应收缩为“固定 checkpoint 的任务/cohort 条件性部署反应”。
- **event 触发重规划改善：尚不支持稳健因果结论。** put-back pooled `+43 pp` 很醒目，但由三个 cohort 的不同 cell 组合产生；rearrange 仅 `+4 pp`，event 还低于 fixed。触发数 `20/50/79` 也不解释该差异。
- **按钮失败由错误状态预测造成：不支持。** 现有审计只显示预测进度可以在没有有效按压时进入下一次 policy 输入；它没有证明动作网络使用该字段、字段错误先于物理失败，或接触控制是唯一瓶颈。
- **视觉历史 V 与显式状态的比较：当前无证据。** V 在首个 update 已出现单卡 OOM，双卡首次 update 仍 OOM，9 个模型尚未产生 checkpoint。V 是工程阻塞，不应被写成负科学结果，也不能继续作为已经可交付的主比较。

## 最小计划调整（不启动实验）

1. **先冻结分析口径。** 将 18 批标成“数值已由 Manager 复算；逐 lane 终审状态另引 receipt”，补一张 `arm × eval × context/origin` 表，列出 `n`、success、episode length、trigger、GPU/lane、runtime commit、preflight hash 和 arm 顺序。put-back 的 bootstrap/显著性区间改为不报告，或明确只对四类 cell 做 cluster-level 描述；不能把重复 seed 当独立轨迹。

2. **做现有证据的只读一致性核查。** 确认 `expert final_block_pose` 是否进入 policy input、success 判定、终态或仅是 preflight 记录；核对三臂的 runtime/compiler/GPU、进程顺序、action/probe RNG 和完整初始状态。若不能证明其无关，保留“full preflight identity 未匹配”的限制。这个核查不需要重跑模型。

3. **HF/LR 优先级降级。** cba8b004 建议的 LR 仍是概念上正确的区分（fixed 的中间递推 versus 边界前刷新），但在当前 fixed/event 的 cohort/lane 异质性未解释前，不应把 LR 或更多 HF 批次列为 P0，也不应追跑到显著。若将来仍把“中间递推”作为主问题，先用 lane/arm 交叉和完整 identity gate 重新设计，再决定是否做 LR。

4. **cover 独立确认暂缓。** handoff 的 wave1 复算中 `cover_blocks N train0 eval0=0/100`，且失败为 `unspecified_failure`；这不是科学 null，先查 adapter/schema/终态记录。未完成该诊断前，不启动 cba8b004 建议的 cover baseline/fixed/LR 三臂，也不因零结果换任务。

5. **V 设为工程准入门。** 双卡 OOM 后暂停 9 个 V 训练；先固定完整 18-slot 输入、global batch32、reset/mask/cache 合同和实际显存/吞吐验收。不能逐任务缩图或减 batch 后把 V 混入主表；在 V 无 checkpoint 前，论文只保留“计划比较”，不写显式状态优于视觉历史。

6. **保留低风险主线，收缩推断。** 九任务 N/S/J 覆盖、已有 checkpoint 的三 eval 补齐和 J/T/JE/C 合同审计可继续按资源计划进行，但所有单 train seed 结果均标为 checkpoint-conditional；JC/SF、全面 K/row 网格、额外按钮字段训练继续后置。新增 training seed 不应因为 HF pooled 差异而自动扩展。

如果未来必须获得跨 runtime 的部署结论，最小设计不是同一 lane 再增加 episode，而是把 arm、GPU/runtime 和 cohort 做交叉或随机化，且每个条件只保留去重后的独立初始轨迹；先证明完整 preflight identity，再按 trajectory-cell 做配对分析。这是后续准入条件，不是本轮授权。

## 交接结论

论文应把当前 HF 结果从“频率干预尚未完成”更新为“第一层两任务三臂部署结果已获得，但跨 cohort/lane 的解释仍未闭合”。可发表的当前表述是任务和 cohort 条件性的部署反应及其证据边界；不可发表的表述包括高频更新普遍提升、event 触发普遍有效、300 episode bootstrap 证明稳健性、或把 forecast 当成物理完成状态。

本报告没有代码 commit；仅发布本任务的科学审计简报。
