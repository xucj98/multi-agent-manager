# 现有状态—动作—事件诊断材料与验证集审计

使用gpt-5.6-terra/max，只做辅助事实调查与具体工程准备；科学解释/实验选择由Manager完成。读MAM AGENTS/README/.local，mam task show本TASK-ID。论文repo=/root/Documents/task-state-vla-paper，新结果快照docs/analysis/accepted_results_20260913.json；业务repo位于/mnt/public/xcj/Projects/{RMBench,openpi,robot-bridge}，C集群共享根/mnt/public/xcj/Projects/state-vla，可SSH wuwen-4090-{1,2,3}只读；不要影响evaluation_owner任何运行tree/job。

## 有界目标
1. 基于上述快照所列原始路径，核查put-back J/T 6模型eval0及rearrange S 3模型已有记录能否对齐：scene ID/env seed/实际初态信息、checkpoint/代码身份、policy RNG、query时间、实际K、raw logits/解码字段/锁存与动作条件、按钮深度/press事件、动作方向、失败类型。输出字段“已存在/可以导出/未记录”的精确表和少量证据，不从终态分类编造机制。
2. 每个模型按episode ID升序，在success、完全未按、浅按不足、其他失败各选最多2个已存在样本（无样本如实记0），定位已有trace路径与字段，避免只挑好看的视频。只检查现有文件；不要开GPU rollout、训练或下载大视频。
3. 核查两个任务是否有独立于训练50集的diagnostic demonstration episodes，给episode IDs/数据来源；同一episode不同帧不算独立验证。若没有，报告确切缺口和最小准备工程，不自行生成新的训练/验证数据。
4. 论文复现所需现有配置：N/J/S/T输入/输出/损失类型与系数、真实控制频率与动作参数化、H/K物理时长、终止/超时、任务schema与acquisition/retention/decoder、训练/评估隔离和场景重试规则。只据冻结checkpoint metadata及确切code版本引用，不猜。J/T的差异要与已接受mask合同一致。
5. 交付一份小的machine-readable索引（model/run/episode ID/env seed/原始路径/hash/available fields）和中文audit.md。若必须增加只读日志才能做P0，提出最小hook位置与输出合同供Manager裁决，不改生产。无需复现所有历史结果。

将成果写本任务独立workspace并在MAM report发布；没有修改业务代码则不需建业务worktree，如需实现先报告再按mam workspace流程。不得修改论文正文/科学设计、不能独立宣布瓶颈或改进结论。不等待长进程/高频轮询；当前可做完成后结束。

## Manager 初审后事实修正（2026-09-13）
继续只读审计，修订并发布audit/report：
1. J/T表的“训练只在episode first frame读reference offset0”疑似把normal input和first-frame override颠倒。沿冻结config与实际输入构造函数核实：普通query训练当前reference、首帧initial、推理cache；给commit/文件/行。
2. “完成但未按”统一改成“未记录有效按压（终态标签）”，明确不表示整个任务完成；索引complete_no_press为机械分类别名，不额外推出动作机制。
3. 沿真实compute_loss/reduction确认Memory-v1是否实际使用key_state_loss_weight，区分遗留metadata与有效权重，列出N/J/S/T各项有效系数及分母。不要仅把保存的0.1/1.0当实际不同权重。
4. 给actual K、qpos/TOPP时间与RNG等关键判断的确切冻结代码路径/commit定位。无需扩大1500集重复扫描；只补事实和来源。仍不实现hook、不训练/rollout、不修改论文，科学判断由Manager完成。
