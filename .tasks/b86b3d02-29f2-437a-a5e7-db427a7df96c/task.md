# 通用 schema offline 验收路径

## 目标
让新wash-cup单phase full/serial与旧drawer双字段通过同一套offline代码及memory配置工作；差别来自配置，不能另写wash专用推理/反馈/GT算法。只修公共offline接口，不改变正在训练的源码/进程或仿真已验收路径。Manager希望本机07:27左右新模型结束后即可安排offline，先给简短范围和预计耗时，再实现。

## 工作区与代码基线
在本任务独立workspace创建robot-bridge worktree，base bd30069ffc0b773de13f98f53753566711960858。如需读/改openpi，创建其独立worktree，base a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。先读MAM入口与本地说明、目标库AGENTS及robot-bridge/docs/design/conventions.md。不要改其他agent运行中的worktree。MAM主根 /mnt/public/xcj/Projects/multi-agent-manager，任务/报告发布project/state-vla；不要修改MAM工具。

## 已有证据与输入
先读任务e6908de7-4b02-465a-987b-a19eba7a315a最新报告（9e975497），及其RMBench/experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md在3e69b1e提交中的队列/真实路径。旧bridge8ea脚本scripts/launch/drawer_offline.py限制旧5ep、H30/K15、固定checkpoint根；scheduler/openpi_offline.py和controllers/x2robot_offline.py的memory指标仍旧格式。请基于新base确认具体适用位置，不机械改行号。
wash训练owner ad6bb77e-3892-4730-ae1a-7d9cd99a5728最新task/report：两20k checkpoint目录、v3 source-frame-aligned全部172ep，固定LeRobot index0–4，S2M单phase，H50/K30。使用已固定的5集，不拆分训练验证集，不重选数据。旧drawer两个模型与5ep[1,22,23,24,26]已有已验收结果，保持原配置行为。

## 实施边界
- 在既有offline启动/manifest入口用配置指定episode、H/K、checkpoint根，保留process/exit/metadata管理，不复制launcher、不另建调度器。
- 复用checkpoint的memory_config、现有MemoryContext，以及共享样本目标/时间和mask逻辑；训练/推理/offline不能各自重新定义offset。full逐帧(t+j+1)、重复终点和serial当前query语义按配置；S2M机器人action对齐沿既有action_at_row/offset0，不重复移位。
- memory预测、可用性mask及GT接入现有offline评估产物，支持单/多字段。GT仅用于评估，不注入policy输入/反馈。不要把action-only跑通冒称memory offline已验收。
- 保留真机wait-condition get_obs、execute/takeover/reset和已有反馈机制，不扩展session或plugin架构。
- 产物留RMBench/eval_result/memory_chunk_20260910/<run>，逐步保留命令/commit/config及转换/训练metadata；不要复制源码或改checkpoint原件。

## 验收与交付
本轮不占GPU。做有意义的CPU边界测试：相同配置目标与训练样本时序一致、mask缺失正确、单/双字段与不同H/K，旧drawer配置不变；真实5ep输入/文件映射与命令dry-run。不要重复全量转换或旧模型测试。若必须改变算法或需大量重构，先提出具体证据/最小方案供Manager裁决。提交代码和简短报告，列文件/commit、测试、剩余GPU验收及可复制命令。清理自己的临时文件，保留workspace供Manager安排空白独立review；不要自己充当独立review或再建review任务，不自行合并部署。

## 9月11日07:22 Manager裁定：独立review修复
读取review任务65a3c29f-08c0-4025-8c29-c4567b26f775的report草稿/发布稿。接受P1：实际policy源码clean门禁与顶层留痕不能来自checkpoint root alias；须绑定--policy-python实际导入的OpenPI源码，且和served_metadata现有provenance校验。用最小CPU探针解析模块根/commit及解释器；复用现有git检查与served字段，不另造依赖快照或provenance框架。探针不加载模型/不占GPU。任意实际源码dirty或握手不符必须在episode执行前拒绝并正确回收服务。
接受P2：dataset与expected_policy_metadata/expected_execution_rows同时出现时，冲突明确报错；新wash manifest删除重复时间字段，只保留一个来源。支持旧drawer现有manifest，不改变其有效参数。
范围收敛：删除当前输入未用的--replay任意选节；保留必要的OpenPI/RMBench root映射及旧格式适配，不为了删行数重写整个launcher。不要增加新的通用配置格式。已有memory指标算法CPU review通过，除具体错误外不改controller/scheduler。
更正报告计数：5525是逻辑执行行/模型，K30对应各集41/51/24/38/33次infer，共187次/模型；此前报告的5525 query不可当成实际infer次数。正式GPU最终按实际日志验证。
提交小修并发布report，给出新增失败保护的定向CPU测试及新commit。目标20分钟，若需要扩大范围先说明。仍不占GPU；Manager交原独立reviewer复查后分配wash offline。本任务实现完成后允许继续负责本代码的GPU offline，但必须等Manager明确授权与checkpoint通过。

## 07:36 wash正式offline排期（以独立复查通过为前提）
训练owner ad6bb77e已发布两20000的CPU完整参数、真实GPU checkpoint-only恢复及进程释放验收，GPU2/3于07:30各1MiB/0%。独立review65a3对fda269c1通过且Manager告知后，授权本任务使用本机GPU2串行执行full/serial两个模型固定5ep；GPU3暂不使用，不跨wuwen-1。启动前核对显存、独立端口，复用已有两库环境和入口，固定干净源码。
统一正式输出目录RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep，launcher内模型子目录wash_full/wash_serial属于同一run的分项产物。先dry-run确认两个真实checkpoint可用。完整执行各5ep[0..4]，不用新smoke模型代替，检查真实action/memory GT/pred/mask、实际infer次数（预计187/模型）与执行行5525/模型、每集退出和资源释放。读取GT仅评分。若失败保留具体首因和已生成产物，不覆盖同目录掩盖失败；恢复方案先报告。
记录实际命令、源码与解释器、checkpoint/转换/训练metadata完整继承。若预计超1小时按mam登记job；可以按合理估算短任务无需强行登记。完成发布简报提供两模型每集动作误差/phase指标（含有效样本数）及产物路径；offline不是闭环成功率。随后Manager安排结果文档整合与统一台账更新，不把本次接口通过称作scheduler原始架构重构已完成。

## 07:45 今日优先真机验证；修复真实metadata接线
用户决定今天不做架构重构，优先wash-cup真机实验，明天再讨论统一架构。接受首次失败原因定位，允许最小修复：新memory_config协议中execution.rows为有效K来源；不要机械把dataset query_stride与execution.rows混为概念，明确launcher校验的是实际运行K及模型输入数据频率/H。对于legacy沿原metadata query_stride规则，显式字段与schema定义同一运行量时拒绝冲突。使用首次真实served_metadata作为回归输入，确认该缺失字段情况被覆盖，不另增配置格式。只修改launcher及必要测试，不扩展scheduler重构。
提交小修并发布report，Manager/独立真机路径验收任务定向复核后启动GPU2重试；新run名wash_memory_v1_20k_offline5ep_retry1，不覆盖失败目录。失败目录最终保留必要首因与命令到工作报告/正式留痕后清理无用临时产物，不能当作正式成功结果。今天的最终交付除每集指标，还需给真机人员明确模型/代码路径与已知限制，不声称未实际验证的真机效果。

## 08:12 retry1类型错误裁定与集成门禁
接受retry1根因。允许最小offline接线修复，优先把memory预测/索引作为offline评估信息妥善传递，避免通用机器人float32动作转换吞掉整数类型。不要在通用server或controller base引入模型专用memory字段分支，也不要全局改变既有机器人动作float32契约；可用offline controller局部handle_execute适配或现成评估请求字段实现，选择最小方案。写集允许本任务offline scheduler/controller及必要测试；确需改base先报具体不可替代原因。禁止通过float→int截断来掩盖错误输入。
这次必须补真实WebSocket/codec→RobotServer→handle_execute→offline controller的CPU集成验证，运行完整fake-policy一集full和serial，核对integer IDs/rows、query标量、实际drain行/GT/mask/反馈，检查末尾/reset。不要再次只测直接execute或孤立helper。CPU用确定性fake预测即可，不加载模型；保留既有legacy drawer/action转换契约。先在这条真实RPC路径找出后续同类错误再交付，不让每次GPU试跑只暴露下一个可CPU捕获的接口错误。
提交小修和定向集成结果给Manager，独立4296391复查。GPU2重试run为wash_memory_v1_20k_offline5ep_retry2，待准入后才跑，保留前次错误原始证据，最终清理重复失败临时目录按既定要求。全程今天只保证wash功能，不做架构重构。

## 08:40 RPC 独立验收后准入
Helmholtz已独立复核dd0914b170fe5d227f24d36b07d90c0e422b7e58，实际RPC full/serial各两集27 passed。Manager准入：固定该bridge commit和OpenPI a869498f，以GPU2执行两模型各5ep offline，输出新目录wash_memory_v1_20k_offline5ep_retry2。仍先检查卡/端口19580/19582、干净源码与握手；同一GPU顺序跑full后serial，完成后核对执行行/推理次数/指标、进程退出及释放。预计超1小时则登记mam job；失败先定位，不反复盲重试。此准入不代表真机验证通过。

## 正式结果收尾
Manager接受retry2运行与释放证据。请在同task创建RMBench worktree（基于其当前xcj-dev），阅读实验规范，仅更新experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md和必要README链接：记录wash两20k训练完成、实际训练/成功offline路径、两模型5ep指标及full逐行/serial逐query不可直接比较、训练内回放而非泛化或闭环成功率。不要更新其他正在跑的sim结果或修改其源树。
失败重试的根因/命令/commit保留为简洁Git实验记录；诊断已完成的前两次失败临时目录可清理，确认不删原数据/正式retry2及共享模型。报告区分成功运行事实和历史失败，不再把已归档workspace当未来部署入口。完成提交、发布report并清理本task各worktree临时缓存，供Manager合并归档。
