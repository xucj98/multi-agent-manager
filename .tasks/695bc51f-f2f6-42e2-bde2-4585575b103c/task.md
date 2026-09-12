# put-back B 基线配置及训练准备

目标：既定论文 B 组中 put-back 目前只有 full三seed，补 serial lag30 和 no-memory seed0，回答同骨干能力比较。两项不依赖Q2评估或C环境验收。你负责最小配置补齐、验证和后续获Manager放行后的训练；不改变模型/loader/schema算法。

先读MAM入口，用mam workspace add从OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 建本task独立worktree并读库AGENTS。现有rearrange serial/no-memory和put-back full均已有实际20k训练；按现有配置factory增加put-back serial_lag30/no_memory注册（若已有等价配置则复用，勿重复）。沿用已验收put-back demo_clean_state数据、sidecar及专用robot norm，不使用rearrange norm或demo_clean。

两条路径需实际loader核对batch/机器人14D、memory字段/serial token监督和条件/no-memory robot-only、目标与padding mask、norm及数据来源，确认相对rearrange既有基线只变任务数据/字段资产。CPU配置样本验收后提交小改交Manager，安排独立review。可用本机GPU6/7各做必要50step训练+BF16保存+checkpoint-only恢复（同类路径已有验收则聚焦本任务新配置，不重跑全套旧测试），记录有效updates/有限loss/恢复shape；不得动GPU0/1/2–5或wuwen-1。启动前查实际显存，碰到他人占用等待并汇报。

正式计划：GPU6 serial seed0，GPU7 no-memory seed0；单卡bs32、20k、H50/K30、相同pi05_base初始化、仅最终20000 BF16模型及metadata/assets。已有run禁止混写，失败retry新目录。正式开跑前提交配置commit和smoke证据给Manager，Manager快速验收后即放行，不等C。冻结源码，使用独立exp_name/可靠detach/python -u -B，登记mam job，确认初始updates/loss。评估另由C验收后安排。

report记录研究目的、实际命令/commit、数据/norm和结果路径、完成与缺口。正式训练如放行则按小时监控，完成后核实权重/metadata完整、退出资源释放并归档job。清理本任务smoke临时产物，保留正式checkpoint及待Manager归档worktree。不创建subagent，不改MAM，不修改他人运行树。

## Manager放行：put-back no-memory seed0
独立review15254a5f配置/真实CPU样本PASS，作者GPU7已完成50updates、有限loss、BF16完整保存与checkpoint-only恢复actions[50,14]。Manager已核对报告及实际保存日志，现正式放行GPU7 no-memory seed0的20k训练。沿a7f3e07冻结树、单卡bs32/20k/相同base及data/norm、最终BF16模型及metadata，独立exp_name不覆盖。立即重新确认GPU7空闲后启动、登记job并验证有效updates/有限loss，不等C或serial。先保留门禁简报到正式run artifacts再清理自身smoke临时checkpoint。serial配置review也PASS，但其GPU smoke尚未完成，仍等GPU6空闲，不碰其他占用。

## 15:46资源更新：按实际空闲卡启动
GPU0/1/6/7当前均有外部占用，2–5为本项目四路训练。此前指定6/7改为本机0/1/6/7中任一实际空闲卡（启动前显存/利用率确认，不因为本VM看不到PID就判为空闲）。不触碰他人作业，不使用wuwen-1。下一张空闲卡优先已放行no-memory正式20k；serial在另一张空闲卡做自身50step/保存恢复后交证据放行。约30分钟核对一次可用性即可，不持续快速轮询、不创建无用长等待job。资源未空闲时阶段报告即可，Manager按时间唤醒。

## Manager放行：put-back serial seed0
独立配置/CPU review15254a5f PASS；现GPU6实际50updates、完整BF16保存、checkpoint-only gate恢复56leaf并返回actions[50,14]/memory_prediction_ids[1,2]均通过。Manager已核对报告及gate日志，正式放行serial seed0的20k：沿a7f3e07冻结版本、已定base/data/norm/bs32/20k、独立exp_name、不覆盖。在本机0/1/6/7任一实际空闲卡启动（优先刚释放的6），立即登记job并确认有效updates/loss，不等C。报告简述gate初次失败与retry1差异，保留门禁必要证据，勿把初次失败隐去。两个正式run按小时监控；不修改活跃源码。

## 后续已授权队列：补齐B组put-back三个训练seed
为避免已验收模型开跑后再临时准备下一批，现同步排入既定B组的四项：put-back serial_lag30 seed1/2、put-back no-memory seed1/2。同a7f3e07配置/数据/norm/base/bs32/20k，仅seed和唯一exp_name改变；原任务每类seed0不重复。先准备准确命令与各独立目录写report，标为queued，不能写已启动。
首两项seed0正常更新后，以上四项可按本机实际释放的GPU直接依次启动：serial seed1、no-memory seed1、serial seed2、no-memory seed2；本机0–7均可，但先检查本项目其他task登记与实际显存，禁止抢占/终止任何既有作业，2–5当前7ae任务训练需等其明确结束。wuwen-1仍不使用。已验收相同路径无需每个seed重复50step；正常入口检查后启动登记MAM与updates/loss证据。最多一GPU一训练，不为队列持卡、不改源码，失败报告。若整机无空卡按约30分钟核对并报告，Manager也协调。此为原72训练预算中的B组既定重复，不依赖C验收或seed0评估成绩。完成后每个模型独立恢复/留痕/台账/资源清理照原协议。

## 最新资源授权：wuwen-1重新开放
用户刚确认 wuwen-1 空闲，可继续安排训练。本节覆盖此前所有“不得使用wuwen-1”的资源限制。先核对现有本机seed0及任何后来已启动的seed1/2，避免重复；然后ssh wuwen-1检查真实GPU显存/利用率，优先把仍queued的 put-back serial_lag30 seed1、no_memory seed1、serial_lag30 seed2、no_memory seed2四组已授权20k实验放到空闲GPU，每卡一个。与本机共享/mnt/public，复用本task已冻结a7f3e07 worktree/环境/data/norm。bs32/20k、仅最终BF1620000、demo_clean_state、唯一目录、相同base协议不变。无需重复已验收的seed-only smoke，不覆盖已有run。
启动后在本机MAM登记remote host/PID/身份，核实真实updates与有限loss，更新本任务报告及准确训练路径/研究目的。不得修改任何活跃运行源码/杀他人GPU。四项全已启动则不擅自扩展新的实验清单，汇报可用资源等Manager排期。
不要按小时/分钟让模型反复巡检；当前MAM新版仍在验收，暂时用普通进程检查及阶段报告，完成启动/检查后结束本轮供Manager接手，不能把繁忙监控转成大量模型请求。此为实质恢复训练安排，不等待MAM或C环境验收。

## Manager待办清理与恢复责任
恢复运行期责任。先只读核对现有本机与wuwen-1六路训练，已停止则验收20k产物/更新台账/归档job，尚运行则调用已安装新版mam wait保持active直到停止事件。不要小时级模型轮询，不新开重复训练；此前四项已开齐。使用原worktree，勿重建。

## 完成训练后的评估交接
用户要求完成训练及时安排eval并更新实验台账。请核对各run实际结束状态；完成后验证最终20k checkpoint完整/可恢复及metadata、归档已处理训练job，并在report给出明确可评模型清单（config/schema/seed/commit/绝对checkpoint路径、研究目的、预期结论）。通过任务报告交给e6908de7评估队列，勿自行重复启动eval。仍在训练的继续保留真实状态和完成事件监控。无需为没有变化的等待窗口改报告或发心跳；任务全部交付后结束turn，不为已完成事项持续wait。


## MAM proactive wake is installed (2026-09-12 18:35 CST)

The installed version now passed all191 source tests, optional wait compatibility, API compatibility and the isolated six-turn actual delivery acceptance. The production per-project service is healthy and bound to the Manager. This section supersedes all earlier requirements to remain active solely for monitoring or to poll hourly.

Finish currently executable work and publish actual results/status, then end turn normally while registered long jobs continue. MAM wakes a dormant executor for any stopped unarchived job, even when other jobs are running. Handle results/cleanup/archive according to this task, and end again when no immediate work remains. A running-only task does not need a standing active turn. Do not stop experiments or archive running training/eval jobs merely to end your turn. Manager receives completed/no-job task follow-up after review routing.

Optional `mam wait`, `mam wait list`, and `mam wait stop` are retained for a concrete need to wait within a turn. Do not produce unchanged waiting updates or start a custom loop to keep the turn alive. Existing experiment protocol, rollout checks, artifact paths and resource authorizations are unchanged. If a queued next run can be started now, continue that work before ending; automatic wake does not replace executing the queue.

## Final archive cleanup

Manager accepted all six final models and verified all six stable gate logs. Archival is blocked by ignored transient caches in your OpenPI worktree: .pytest_cache, generated .ruff_cache entries, and source/client __pycache__ directories. Remove only your generated temporary caches, preserve environment/shared links and tracked files, and publish a concise cleanup confirmation. Manager already removed the extra workspace-root put_back_final_gate.py only after exact comparison with your stable saved copy; stable evidence remains. Do not repeat training or model verification. End turn after cleanup; Manager will retry archive. Code retained as codex/put-back-memory-baselines at a7f3e07. No new diagnosis work belongs to this task.
