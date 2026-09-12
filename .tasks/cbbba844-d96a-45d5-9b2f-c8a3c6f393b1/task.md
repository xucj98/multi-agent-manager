# U辅助监督对照：6个20k训练

## 研究目的与既定设计
读取/root/Documents/task-state-vla-paper/docs/EXPERIMENT_PLAN_20260910.zh-CN.md，执行已计划U组：rearrange_blocks和put_back_block，各seed0/1/2。检验性能收益来自递推记忆输入还是仅来自额外状态监督。与各任务Q2/B full per-frame t+j+1基线保持同形状、同字段、同输出目标、loss/mask/归约、norm、数据、初始化及采样；唯一处理为训练和部署memory输入始终为字段initial，不消费预测反馈。仍训练原memory输出及状态损失。不能只在推理清空输入，也不能变成no-memory网络。保留假设可被推翻的表述，不预填成绩。

## 工作与资源
用本任务独立OpenPI及需要的robot-bridge/RMBench worktree，读各AGENTS；不要修改现有活跃训练树。先核对已完成/运行训练，确保U对照未重复。复用已验收demo_clean_state转换、base和norm，不重转数据。以已验收新schema训练实现为基线，优先使用现有schema/config表示initial；若能力未接入，最小补充train和memory context一致路径，OpenPI和bridge两份memory_config保持语义一致，不引入跨库依赖。明确实际参考基线commit/config及逐项差异。

授权资源：本机GPU1/7，wuwen-1 GPU4/5/6/7。启动前复查实际空闲和进程归属，已有占用不抢。规划本机1/7为rearrange seed0/1，wuwen-1 GPU4为rearrange seed2、GPU5/6/7为put-back seed0/1/2。每卡单训练，bs32、20k、H50/K30，最终只存一个20k BF16 checkpoint及必要资产/metadata，独立非现有路径。源数据必须demo_clean_state。

## 开跑门禁
先完成真实训练sample/模型loss/Context反馈的CPU验收，证明memory输入全部initial且GT memory targets、权重、robot输入输出未被误改；reset/takeover/offline/live均不消费反馈。必要50step训练保存恢复smoke用本机GPU1，复用合理已有验证但不能跳过新行为；清理自有smoke产物，提交干净commit。把具体配置、diff、测试和smoke提交Manager，独立review通过后才启动6个正式训练。不要因卡空闲直接跑未review的新语义。

## 台账及交接
在RMBench/experiments/memory_chunk_20260910新增独立U组说明（避免与e690主台账写冲突），先写研究问题、变量、预期结论、每run train/ckpt及计划eval路径。正式启动后登记mam job，检查初始有限loss与GPU映射，完成后验收最终checkpoint、资源释放和训练job归档，给e690评估负责人可评清单。评估用C集群和smoke2→100既定协议，你不重复启动eval。完整任务要求及报告统一MAM .tasks，交付commit、路径、测试、运行job。事件等待用mam wait；不要无变化轮询/心跳/每次超时写report；实际工作完成后结束turn。

## Manager正式训练准入
独立review f6293543通过，Manager验收。现在立即按既定GPU映射和唯一exp_name启动6条20k：本机1/7为rearrange seed0/1，wuwen-1 GPU4为rearrange seed2、5/6/7为put-back seed0/1/2。启动前复查卡空闲；冻结OpenPI6266bd8bbfa5f3e451f7253c476d1108e1ff5e1e，bs32/20k/BF16 final only，源schema与review一致。无需再重复smoke/CPU或等待其他评估结果。
逐条mam job add登记真实进程，初始有限loss和实际设备映射验收后报告6个job/路径与预计完成；更新U台账运行状态。若某卡被外部占用，只阻塞该条，其余独立开跑。持续以mam wait完成事件监控，结束后验收产物交e690评估；不得把启动成功写成训练完成。

## 启动验收后的等待交接确认
Manager已验收6条实际启动/step100/设备映射，当前无需新检查或重复报告。仍由你负责这6条训练停止后的产物验证和eval交接；保持mam wait实际await，等待工具返回事件后处理，不是在后台启动wait后直接结束turn。无变化不汇报、不刷新报告，固定超时后直接重新wait。只有任务真实完成或Manager明确交接时才结束turn。


## MAM proactive wake is installed (2026-09-12 18:35 CST)

The installed version now passed all191 source tests, optional wait compatibility, API compatibility and the isolated six-turn actual delivery acceptance. The production per-project service is healthy and bound to the Manager. This section supersedes all earlier requirements to remain active solely for monitoring or to poll hourly.

Finish currently executable work and publish actual results/status, then end turn normally while registered long jobs continue. MAM wakes a dormant executor for any stopped unarchived job, even when other jobs are running. Handle results/cleanup/archive according to this task, and end again when no immediate work remains. A running-only task does not need a standing active turn. Do not stop experiments or archive running training/eval jobs merely to end your turn. Manager receives completed/no-job task follow-up after review routing.

Optional `mam wait`, `mam wait list`, and `mam wait stop` are retained for a concrete need to wait within a turn. Do not produce unchanged waiting updates or start a custom loop to keep the turn alive. Existing experiment protocol, rollout checks, artifact paths and resource authorizations are unchanged. If a queued next run can be started now, continue that work before ending; automatic wake does not replace executing the queue.


## 当前Manager执行者交接（2026-09-13）
Manager 01a09657-e0f3-7352-b726-aba5bbd5d498 将用 mam task rebind 将本任务交给当前对话新建的 terra/max 执行者。以 mam task status 的当前 agent 为执行权限依据；旧执行者若发现已换绑，停止执行本任务，不再写workspace/report或处理job。新执行者换绑前仅只读准备并结束turn，待Manager明确接续消息后开始工作。换绑后直接继承原TASK-ID、全部现有workspace/worktree/分支/已发布报告与运行job，不再次workspace add，不复制或重启/重复登记job。既有任务目标、数据与评估协议、冻结runtime、独立review门禁和资源授权均不变。完成可执行事项正常结束turn，由MAM唤醒；不得高频轮询。
