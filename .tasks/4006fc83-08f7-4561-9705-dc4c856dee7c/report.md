# 高频状态 / replan 合同级独立审查

审查任务要求 revision 为 `491ac82ef2c65bd8a64ecb12f5452bf9e08cdaa6`；本轮读取的源任务算法合同为
`7009b32ca379c4d188e631775c638ebeafae2498`，评测任务合同为
`289f4cf59886d414514d6bd02f57add54df39631`。基线对象是 OpenPI
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 与 robot-bridge
`f9626636c4776d8eb15f9c556775cb2d12c000e5`。

## 本轮结论

**合同级条件准入；没有 code PASS。** 本轮仅核对冻结算法合同和既有实现接口。源 owner 尚未交付干净的实现 commit / report；审查期间其 worktree 出现未提交的 `src/openpi/models/pi0.py` 编辑，故不把它当作可复审代码快照，也没有运行实现测试、GPU、仿真或正式评测。

J 的绝对时刻合同正确：对于动作计划起点 `a`，J row `j` 的 target 是
`a+j+1`；在已实际完成到 `u` 时，最近 forecast source 为 `s`，应读取
`row(u-s-1)` 作为 target 恰为 `u` 的 `m_u`。因此 old `Z_a[d:d+3]` 与 fresh
`Z_u[0:3]`（`d=u-a`）同为 `u+1..u+3`；`u=a+25` 时 source `a+25` 的 row 4 供
`a+30` 的下一 action infer 使用。不能写成 `d-1`，也不能把 J row 0 当 current
state。phase window 的三行比较、`d >= 10 && d < 30` 与 replan 后重新定义 `a` 均应由
CPU 测试逐项断言。

J HF-event 的比较可以作为“以新观测、递归 cache 和固定独立采样得到的两份 forecast 的
不一致”触发 replan；它不是对观测物理状态误差的测量，也不能把触发次数解释为物理异常次数。
HF-event 对 HF-fixed 的差异只能归因于该 re-observation-triggered replan 策略。源合同已要求
将此限定写入留痕和结果说明；K10 periodic 不可被表述为与 event 臂严格平均调用数匹配的对照。

## 代码准入 P1

1. **隔离标准 pending feedback。** 既有 `MemoryContext.accept()` 为 J action chunk 保存 pending，
   `observe()` 随后按全局 `execution_progress.completed` 结清它。若 rolling 沿用该 pending，正常
   `a+30` 会用旧 `Z_a` row 29 覆盖最近 monitor forecast；若在 `u` clear 原后缀，下一新计划的
   completed 还会把已取消的旧 rows 误认完成。高频 J 必须以 plan ID、source 和实际 prefix 绑定自己的
   生命周期，并在正确时点隔离/废弃旧 pending；probe 不得伪造 accept 或 completion evidence。

2. **动作与 probe RNG 必须真隔离。** 当前 `Policy.infer()` 对每次调用都 split 内部 `self._rng`，
   bridge backend/server 也只有普通 `infer`。普通 probe 会推进动作 RNG；即使传入 noise，现有实现仍会
   split。新 wire 必须保证 probe 不改变动作 RNG，并用 baseline/shadow 同 checkpoint、同输入的逐 action
   输出和 RNG identity 证明。

3. **进度异常不能跨越。** duplicate、stale、invalid 和 gap observation 必须在 probe 前短路，既不消耗
   probe RNG、也不替换 forecast，并打断连续偏差计数。`high@5 → invalid@10 → high@15` 不得触发；清队列后
   新 plan 也不得结清旧 pending。

4. **观测副作用要与 baseline 对齐。** RMBench 在录视频时 `get_obs_for_policy()` 走 `get_obs()`；若
   `crazy_random_light` 启用，额外 render 会重采样灯光并消费全局 NumPy RNG。源合同已冻结派生高频配置为
   `random_light=false`、`crazy_random_light_rate=0`，并要求核对原 baseline；条件不一致时应补同条件
   baseline，不能静默复用旧成绩。shadow 检查须覆盖 video 和 no-video。

## 已做的只读核对

- 读取了源、评测和时间尺度审计任务的已发布合同，以及 OpenPI memory YAML、policy RNG 路径、
  robot-bridge simulation scheduler / `MemoryContext` / RMBench worker 的 queue、drain 与 observation 路径。
- 核实 J `t+1` YAML、S query-current / lag30 YAML 和 T per-field target 差异；T 本轮仍应拒绝进入
  rolling / frame-deviation。
- 未修改作者或生产 worktree，未运行 GPU、训练、rollout、正式评测、部署或服务。

Manager 已将上述 P1 合同补充发布给源 owner。收到其明确干净 commit 后，本 reviewer 将对精确 diff 做
独立代码复审；届时才判断 CPU smoke 准入，且不会将其表述为正式评测完成。
